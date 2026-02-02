"""
Conversation Orchestrator - 聊天消息处理的主入口

本模块负责协调各类服务以处理用户的聊天请求：
1. 上下文加载与管理 (Context Loading)
2. 调用 LLM 生成回复 (LLM Interaction)
3. UI 组件的生成与注入 (UI Injection)
4. 后台任务的触发 (Background Tasks: System 2)

数据流向 (High Level Data Flow):
User -> WebSocket -> ChatAgent (Facade) -> ConversationOrchestrator
    -> Step 1: ContextManager (获取历史/画像/资产)
    -> Step 2: IntentClassifier (意图识别)
    -> Step 3: RAGEngine (如果需要，检索知识) + MemoryService (检索相关记忆)
    -> Step 4: LLMProvider (流式生成回复)
    -> Step 5: UIComponentInjector (注入前端组件)
    -> Step 6: Background Pipeline (异步执行信息提取、分析、存储)

设计模式:
- 协调者模式 (Orchestrator Pattern): 作为指挥中心，不处理具体业务，而是调度其他服务。
- 依赖注入 (Dependency Injection): 通过构造函数注入核心依赖，提高可测试性。
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from datetime import datetime
import time
from typing import Any

from app.core.config import get_settings
from app.core.prompt_manager import prompt_manager
from app.models.context import ConversationContext
from app.models.intent import IntentType
from app.models.knowledge import KnowledgeChunk
from app.services.context_manager import ContextManager
from app.services.llm_caller import LLMProvider
from app.services.ui_component_injector import get_ui_component_injector
from app.services.ui_tools import ShowValuationCard, ShowActionPlan, ShowPortfolioChart, ShowActionCard

logger = logging.getLogger(__name__)


class ConversationOrchestrator:
    """
    对话编排器 (Conversation Orchestrator).
    
    这是系统的核心调度类，取代了原有的单体 `ChatAgent`。它的职责是协调各个专职服务协同工作。
    
    职责:
        1. 维护对话上下文 (Context)
        2. 构建 Prompt 并调用 LLM
        3. 处理 LLM 的工具调用，生成 UI 组件
        4. 全异步触发后台深度分析任务 (Information Extraction, Insight Analysis, etc.)
    
    并发说明:
        - 主流程 `process_message` 是异步的 (async)，但为了保证用户体验，
          所有重型任务 (如信息提取、写入数据库) 均通过 `asyncio.create_task` 
          放入后台执行 (Fire-and-Forget)，不阻塞用户接收首个 Token。
    """
    
    def __init__(
        self,
        llm_provider: LLMProvider,
        context_manager: ContextManager
    ):
        """
        初始化编排器。
        
        采用依赖注入模式，传入核心服务的实例。
        
        Args:
            llm_provider (LLMProvider): LLM 服务提供者，负责与模型交互 (支持 DeepSeek, OpenAI 等)。
            context_manager (ContextManager): 上下文管理器，负责加载和缓存用户状态。
        """
        self.llm_provider = llm_provider
        self.context_manager = context_manager
        
        # UI 注入器 (负责生成前端组件)
        self.ui_injector = get_ui_component_injector()
        
        # Phase 1: 意图分类器 (懒加载以避免循环依赖)
        from app.services.intent_classifier import get_intent_classifier
        self.intent_classifier = get_intent_classifier()
        
        # Phase 1: 记忆服务 (负责 Long-term Memory 检索)
        from app.services.memory_service import get_memory_service
        self.memory_service = get_memory_service()

        # Phase 2: Services for Synchronous Extraction
        from app.services.information_extraction import InformationExtractor
        self.information_extractor = InformationExtractor()
        
        from app.services.asset_extraction_service import AssetExtractionService
        self.asset_extraction_service = AssetExtractionService()

        from app.services.property_valuation import get_property_valuation_service
        self.valuation_service = get_property_valuation_service()
        
        logger.info("✅ ConversationOrchestrator initialized (编排器初始化完成)")

    
    async def process_message(
        self, 
        user_id: int, 
        message: str
    ) -> AsyncIterator[str]:
        """
        处理用户消息的主入口方法。
        
        作为 WebSocket Handler 的直接下游，负责编排整个响应流程。
        
        流程概览:
        1. Context: 加载用户上下文 (缓存优先，数据库兜底)
        2. Classification: 识别用户意图 (决定是否触发 RAG)
        3. History: 立即保存用户消息 (确保断线不丢记录)
        4. RAG & Memory: 根据意图检索知识库和长期记忆
        5. Prompt: 构建 System Prompt (包含画像、资产、知识、记忆)
        6. LLM: 流式生成文本回复，并监听 Tool Calls
        7. UI: 根据 Tool Calls 或正则规则生成前端组件
        8. Background: 启动 Fire-and-Forget 后台任务 (分析、提取、甚至写入)
        
        Args:
            user_id: 用户 ID
            message: 用户发送的文本消息
            
        Yields:
            str: 文本流 (chunks) 或 UI 组件标记 (<WIDGET... />)
        """
        # Import here to avoid circular imports
        from app.services.chat_history_service import get_chat_history_service
        
        chat_history_service = get_chat_history_service()
        
        # Save user message moved to after intent classification (Step 1.6)
        
        try:
            # =========================================================================
            # Phase 1: 上下文加载与意图识别 (Context Loading & Intent)
            # =========================================================================
            
            # Step 1: 加载上下文
            # ContextManager 会优先查 Redis，未命中则查 DB 并重建缓存
            context = await self.context_manager.get_context(user_id)
            
            # Step 1.5: 意图分类 (Intent Classification)
            # 使用最近 10 条历史记录辅助分类，以理解上下文 (如 "它多少钱" 指代的是上文的资产)
            from app.models.chat import ChatMessage
            # context.conversation_history is list of dicts: {'role': '...', 'content': '...', ...}
            history_objs = [
                ChatMessage(role=msg["role"], content=msg["content"]) 
                for msg in context.conversation_history[-10:] # Last 10 messages
            ]
            
            intent_result = await self.intent_classifier.classify(message, history_objs)
            logger.info(f"[Workflow:AssetCollection] Step 1: Intent detected: {intent_result.intent_type} (conf={intent_result.confidence})")
            
            # Step 1.6: 保存用户消息
            # 立即持久化，确保即使后续崩溃，用户的输入也被记录
            try:
                # Use json.loads(json()) to ensure Enums are serialized to strings
                await chat_history_service.save_user_message(
                    user_id, 
                    message,
                    meta_data={"intent": intent_result.model_dump(mode='json')}
                )
            except Exception as e:
                logger.error(f"Failed to save user message: {e}")
            
            # Step 2: 更新内存上下文
            context.add_message("user", message)
            self.context_manager.update_in_memory(user_id, context)

            # [Plan B] Step 2.5: 同步提取与估值 (Synchronous Extraction)
            # 在 LLM 思考前，先处理数据
            sync_result = {}
            if intent_result.intent_type in [IntentType.INFO_COLLECTION, IntentType.ACTION_REQUEST]:
                # Need chat_message_id for lineage, assuming save_user_message returns ID or we re-query
                # For simplicity, we pass a dummy ID or fetch latest. 
                # Optimization: save_user_message typically returns the object. 
                # Let's assume we can proceed without strict ID or fetch it if vital.
                # Actually, for this MVP refactor, we pass 0 if not easily available, or fix save_user_message later.
                msg_id = 0 
                sync_result = await self._synchronous_extraction_pipeline(
                    message, user_id, intent_result.intent_type, msg_id
                )
                
                # 如果有新资产入库，强制刷新 Context 中的 extracted_assets
                if sync_result.get("new_assets"):
                    logger.info(f"[Workflow:AssetCollection] Step 3: Refreshing context assets after extraction")
                    # Re-fetch assets to ensure context is up-to-date
                    # This is slightly expensive but guarantees consistency
                    fresh_assets = await self.asset_extraction_service.get_user_assets(user_id)
                    context.extracted_assets = fresh_assets
                    self.context_manager.update_in_memory(user_id, context) # Sync back

            
            # =========================================================================
            # Phase 2: 知识增强与记忆检索 (RAG & Memory Retrieval)
            # =========================================================================
            
            # Step 3: RAG 增强 (意图门控 Intent-Gated)
            rag_context, rag_sources = None, []
            
            # 仅在 "政策咨询" 或 "顾问建议" 类意图触发 RAG
            # 避免 "我赚了50万" 这种信息录入类文本触发无关的检索
            should_rag = intent_result.intent_type in [IntentType.POLICY_QUERY, IntentType.ADVISORY]
            
            if should_rag:
                rag_context, rag_sources = await self._augment_with_rag(message, context)
            else:
                logger.info(f"⏭️ Skipping RAG for intent: {intent_result.intent_type}")
            
            # Step 3.5: 长期记忆召回 (Memory Recall)
            # 检索向量数据库中的相关记忆片段 (如用户之前的偏好、家庭情况)
            # ACTION_REQUEST 通常无需历史记忆，直接执行
            relevant_memories = []
            if intent_result.intent_type != IntentType.ACTION_REQUEST:
                relevant_memories = await self.memory_service.retrieve_relevant(user_id, message, limit=3, similarity_threshold=0.6)
            
            memory_context = ""
            if relevant_memories:
                # Fix: Use dictionary access m["content"] instead of object access m.text
                memory_list = "\n".join([f"- {m['content']}" for m in relevant_memories])
                # Format clearly for LLM
                memory_context = f"\n\n## 🧠 用户相关记忆 (Long-term Memory)\n{memory_list}\n"
                logger.info(f"🧠 Retrieved {len(relevant_memories)} relevant memories")

            # =========================================================================
            # Phase 3: Prompt 构建与 LLM 执行 (Prompt & LLM Execution)
            # =========================================================================

            # Step 4: 构建 System Prompt
            if rag_context:
                # 使用 RAG 增强后的 Prompt (包含知识片段)
                system_prompt = rag_context
            else:
                # 使用标准 Prompt
                system_prompt = prompt_manager.render("chat", "agent_system", "system_instruction")

            # 注入意图特定指令 (Intent-Specific Instructions)
            # 确保 Agent 在不同场景下 (如闲聊 vs 严谨咨询) 表现出正确的人设
            try:
                intent_key = intent_result.intent_type.value
                # Assuming intent_instructions.yaml exists in chat folder
                intent_instruction = prompt_manager.render(
                    category="chat",
                    filename="intent_instructions",
                    key=intent_key
                )
                if intent_instruction:
                    system_prompt += f"\n\n{intent_instruction}"
                    logger.debug(f"🎯 Injected intent instruction for: {intent_key}")
            except Exception as e:
                # Non-critical, just log warning
                logger.warning(f"Note: Could not load intent instruction: {e}")

            # 注入长期记忆
            if memory_context:
                system_prompt += memory_context
                
            # Step 4.5: 即时生成行动方案 (Generative Plan on Demand)
            # 如果用户明确索要方案，立即调用 ActionReasoner 生成，并将摘要注入 Prompt
            has_plan, plan_instruction = await self._generate_plan_if_requested(message, user_id, context)
            
            # If we generated a plan, instruct LLM to be brief and NOT output text details
            if has_plan:
                system_prompt += plan_instruction
            
            # DEBUG: 打印完整上下文信息 (DEBUG: Log full context information)
            logger.info("============== DEBUG LLM CONTEXT START ==============")
            logger.info(f"RAG Context: {rag_context if rag_context else 'None'}")
            logger.info(f"Memory Context: {memory_context if memory_context else 'None'}")
            logger.info(f"Plan Instruction: {plan_instruction if has_plan else 'None'}")
            # Context object might be complex, logging key attributes
            logger.info(f"ConversationContext: {context}") 
            logger.info("============== DEBUG LLM CONTEXT END ==============")

            messages = self._build_messages(context)
            
            # DEBUG: 打印最终构建的消息列表
            logger.info("============== DEBUG MESSAGES START ==============")
            import json
            try:
                # Attempt to pretty print JSON if possible, otherwise raw string
                logger.info(json.dumps(messages, ensure_ascii=False, indent=2))
            except Exception:
                logger.info(messages)
            logger.info("============== DEBUG MESSAGES END ==============")
            
            # 准备 UI 工具列表 (Phase 3)
            # [DISABLED] 暂时禁用 AI 工具调用，回归纯文本模式
            # ui_tools = [ShowValuationCard, ShowActionPlan, ShowPortfolioChart, ShowActionCard]
            ui_tools = None
            
            full_response = ""
            tool_calls = []
            
            # 执行 LLM 流式生成
            async for chunk in self.llm_provider.generate_stream(messages, system_prompt, tools=ui_tools):
                if isinstance(chunk, str):
                    # 文本流: 立即 Yield 给前端，实现打字机效果 (System 1 极速响应)
                    full_response += chunk
                    yield chunk
                # [DISABLED] 禁用工具调用处理
                # elif isinstance(chunk, dict) and "name" in chunk:
                #     # 工具调用: 暂存，待文本生成完毕后统一处理
                #     logger.info(f"🛠️ Received Tool Call: {chunk['name']}")
                #     tool_calls.append(chunk)

            # Step 5: 更新 AI 回复到上下文
            context.add_message("assistant", full_response)
            self.context_manager.update_in_memory(user_id, context)
            
            # =========================================================================
            # Phase 4: UI 组件注入 (UI Component Injection)
            # =========================================================================
            
            # Step 6: 生成并注入 UI 组件
            enhanced_response = full_response
            ui_components = []
            
            # A. 优先处理 LLM 的显式工具调用 (Explicit Tool Calls)
            if tool_calls:
                for tool_call in tool_calls:
                     widgets = await self.ui_injector.generate_widgets_from_tool(
                         tool_call, context, user_id
                     )
                     ui_components.extend(widgets)
                
                # 将生成的组件追加到响应末尾
                if ui_components:
                    import json
                    widgets_str = ""
                    for comp in ui_components:
                        c_type = comp["type"]
                        c_data_json = json.dumps(comp["data"], ensure_ascii=False, default=str)
                        c_data_escaped = c_data_json.replace('"', '&quot;')
                        widgets_str += f'\n\n<WIDGET:{c_type} data="{c_data_escaped}" />'
                    
                    enhanced_response = full_response + widgets_str
                    # 再次 Yield 组件部分
                    yield widgets_str
                else:
                    # 容错处理: LLM 调用了工具但某些原因未生成组件 (可能是数据不足)
                    # 如果文本也是空的，这是一个严重的 "空响应" bug，需要给出兜底回复
                    if not full_response.strip():
                        # Determine specific fallback based on what tool was attempted
                        failed_tools = [t.get("name") for t in tool_calls]
                        
                        if "ShowPortfolioChart" in failed_tools:
                            fallback_text = "为了给您更准确的资产配置建议，我需要您至少提供两类资产信息（例如房产+存款）。请继续补充信息哦！💡"
                        elif "ShowValuationCard" in failed_tools:
                            fallback_text = "收到，已记录您的房产信息。正在后台同步最新市场数据，请稍等片刻后再查看估值卡片 🏠"
                        elif "ShowActionPlan" in failed_tools:
                            fallback_text = "已收到您的请求。目前信息尚不足以生成完整的行动方案，建议您先补充一下家庭财务状况。"
                        else:
                            # Default fallback
                            fallback_text = "已收到您的信息。正在结合现有资产进行综合分析，请稍候..."
                            
                        logger.warning(f"⚠️ LLM called tools {failed_tools} but no widgets generated. Injecting smart fallback: {fallback_text}")
                        enhanced_response = fallback_text
                        yield fallback_text
                    else:
                        enhanced_response = full_response
            
            # B. 降级策略: 如果没有 Tool Call，尝试正则匹配 (Legacy/Supplemental)
            # B. 降级策略: 如果没有 Tool Call，尝试正则匹配 (Legacy/Supplemental)
            # [DISABLED] 暂时禁用正则匹配注入，确保纯文本输出
            else:
                pass
                # enhanced_response, legacy_components = await self.ui_injector.extract_and_inject(
                #     full_response, context, user_id
                # )
                # if enhanced_response != full_response:
                #     # Yield 追加的部分
                #     yield enhanced_response[len(full_response):]
                #     ui_components = legacy_components

            # [Plan B] Deterministic UI Injection
            # 如果同步提取阶段明确要求显示某些组件 (如 估值卡片)，直接追加
            if sync_result.get("triggered_widgets"):
                logger.info(f"🧩 [SYNC_UI] Injecting deterministic widgets: {sync_result['triggered_widgets']}")
                widget_str_buffer = ""
                
                for w_name in sync_result['triggered_widgets']:
                    if w_name == "ShowValuationCard":
                        # Find the newly added real estate asset(s)
                        for new_asset in sync_result.get("new_assets", []):
                            if new_asset.asset_type == "real_estate":
                                # Generate widget markup
                                # For simplicity, construct raw data manually or use UIInjector helper if possible
                                # Assuming simplified construction for MVP
                                # Need to format data as assumed by frontend: { "asset_id": ... }
                                
                                w_data = {"asset_id": new_asset.id}
                                import json
                                c_data_json = json.dumps(w_data, ensure_ascii=False)
                                c_data_escaped = c_data_json.replace('"', '&quot;')
                                widget_xml = f'\n\n<WIDGET:VALUATION_CARD data="{c_data_escaped}" />'
                                
                                widget_str_buffer += widget_xml
                                ui_components.append({"type": "VALUATION_CARD", "data": w_data})
                
                if widget_str_buffer:
                    full_response += widget_str_buffer
                    enhanced_response = full_response # Update final
                    yield widget_str_buffer # Stream to user

            
            # Step 7: 保存最终的 AI 消息 (含组件标记)
            try:
                await chat_history_service.save_ai_message(user_id, enhanced_response)
            except Exception as e:
                logger.error(f"Failed to save AI message: {e}")
            
            # =========================================================================
            # Phase 5: 后台处理 (Background Pipeline)
            # =========================================================================
            
            # Step 8: 触发后台流水线 (Fire-and-Forget)
            # 关键设计: 使用 asyncio.create_task 而不 await
            # 确保用户无需等待繁重的信息提取和分析任务完成
            asyncio.create_task(
                self._background_extraction_pipeline(message, user_id, context)
            )
            
            logger.info(f"✅ Message processed for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            yield f"抱歉，处理您的消息时出现了错误：{str(e)}"

    async def _synchronous_extraction_pipeline(
        self,
        message: str,
        user_id: int,
        intent: IntentType,
        chat_message_id: int
    ) -> dict[str, Any]:
        """
        [Plan B] 同步提取流水线: 在 LLM 生成回复前，先提取数据、存库并估值。
        
        Returns:
            dict: {
                "new_assets": list[UserAsset], # 新入库的资产对象
                "updated_valuations": list[float], # 对应的估值
                "triggered_widgets": list[str] # 建议触发的 UI 组件类型 (e.g. 'ShowValuationCard')
            }
        """
        # 仅在信息更新/收集类意图下运行，避免不必要的延迟
        if intent not in [IntentType.INFO_COLLECTION, IntentType.ACTION_REQUEST]:
            return {}

        logger.info(f"[Workflow:AssetCollection] Step 2: Starting synchronous extraction for user {user_id}")
        start_time = time.time()
        
        result = {
            "new_assets": [],
            "updated_valuations": [],
            "triggered_widgets": []
        }

        try:
            # 1. 提取实体 (Use InformationExtractor)
            logger.info(f"[Workflow:AssetCollection] Step 2.1: Calling LLM for extraction")
            assets, profile, validation = await self.information_extractor.extract_information_from_conversation(message)
            
            if not assets:
                logger.info("[Workflow:AssetCollection] Step 2.1: No assets extracted by LLM.")
                return result

            logger.info(f"[Workflow:AssetCollection] Step 2.1: Extracted {len(assets)} assets")

            # 2. 存入数据库 (Use AssetExtractionService)
            # This handles duplicate detection and updates
            logger.info(f"[Workflow:AssetCollection] Step 2.2: Persisting assets to DB")
            stored_assets = await self.asset_extraction_service.store_extracted_assets(user_id, assets)
            result["new_assets"] = stored_assets
            logger.info(f"[Workflow:AssetCollection] Step 2.2: DB Persistence complete. stored_assets count: {len(stored_assets)}")
            
            # 3. 触发估值 logic
            from app.models.user import AssetType as UserAssetType
            # from app.services.asset_service import AssetService
            # asset_service = AssetService()
            
            for asset in stored_assets:
                # Check if it is real estate
                if asset.asset_type == UserAssetType.REAL_ESTATE:
                    logger.info(f"[Workflow:AssetCollection] Step 2.3: Triggering valuation for asset {asset.id}")
                    # Extract location/name and area from extra_data or name
                    # [Fix] Use location from extra_data if available, otherwise fallback to name
                    location = asset.extra_data.get("location") if asset.extra_data else None
                    if not location:
                        location = asset.name
                    
                    area = asset.extra_data.get("area", 0) if asset.extra_data else 0
                    
                    valuation = await self.valuation_service.get_market_value(
                        location=location,
                        area=float(area)
                    )
                    
                    if valuation:
                         # Update asset value using AssetExtractionService
                         await self.asset_extraction_service.update_asset_value(
                             asset_id=asset.id,
                             new_value=valuation.value
                         )
                         
                         asset.value = valuation.value
                         result["updated_valuations"].append(valuation.value)
                         result["triggered_widgets"].append("ShowValuationCard")

            logger.info(f"[Workflow:AssetCollection] Step 2: Pipeline finished in {time.time() - start_time:.2f}s. New assets: {len(result['new_assets'])}")
            return result

        except Exception as e:
            logger.error(f"❌ [SYNC_EXTRACT] Failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return result

    async def _save_and_value_assets(self, user_id: int, extracted_data: list[Any], chat_message_id: int) -> dict:
        """辅助方法: 存库并触发估值"""
        res = {"new_assets": [], "updated_valuations": [], "triggered_widgets": []}
        
        from app.services.asset_service import AssetService
        asset_service = AssetService() # Should be injected, but for now instantiate
        
        for item in extracted_data:
            # 1. 保存到 UserAsset
            # 模拟 Entity -> Model 的转换逻辑
            # 这里简化处理，假设 item 已经是结构化数据
            try:
                # 识别资产类型
                asset_type = item.type # e.g. "real_estate"
                
                # Check duplication / Update logic? 
                # For Plan B, we assume "add or update"
                # Using a simplified upsert logic for now
                
                saved_asset = await asset_service.create_or_update_asset(
                    user_id=user_id,
                    asset_data=item, 
                    source_message_id=chat_message_id
                )
                
                if saved_asset:
                    res["new_assets"].append(saved_asset)
                    
                    # 2. 如果是房产，立即触发估值
                    if saved_asset.asset_type == "real_estate":
                        logger.info(f"🏠 [SYNC_VALUATION] Triggering valuation for asset {saved_asset.id}")
                        from app.services.valuation_service import ValuationService
                        val_service = ValuationService()
                        valuation = await val_service.assess_asset_value(saved_asset.id)
                        
                        if valuation:
                            # 更新资产价值
                            await asset_service.update_asset_value(saved_asset.id, valuation.total_value)
                            saved_asset.value = valuation.total_value # Update local object
                            res["updated_valuations"].append(valuation.total_value)
                            res["triggered_widgets"].append("ShowValuationCard")
                            
            except Exception as e:
                logger.error(f"Error saving asset item: {e}")
                continue
                
        return res

    async def _generate_plan_if_requested(
        self,
        message: str,
        user_id: int,
        context: ConversationContext
    ) -> tuple[bool, str]:
        """
        检查用户是否请求生成方案，如果是则立即生成。
        
        System 1 (快速响应) 检测到意图后，立即触发 System 2 (ActionReasoner) 生成方案，
        并将生成结果的摘要注入到本次 LLM 的 Prompt 中，实现即问即答。
        
        Returns:
            (has_plan, prompt_instruction_to_append): 是否生成了方案，以及需要追加的 Prompt 指令
        """
        plan_keywords = [
            # 常见表达
            "生成方案", "行动方案", "理财计划", "看看我的方案", "我的方案", "generate plan",
            # 保障/保险类
            "保障方案", "家庭保障", "财富保障", "保险方案",
            # 投资/增值类
            "投资方案", "增值方案", "财富增值",
            # 规划类
            "规划方案", "做个方案", "制定方案", "给我一个方案",
            # 债务类
            "负债优化", "债务方案",
            # 房产类
            "房产方案", "房产规划"
        ]
        is_request = any(k in message for k in plan_keywords)
        
        if is_request:
            logger.info(f"⚡️ [ORCHESTRATOR] Detected plan request from user {user_id}")
            try:
                from app.services.action_reasoner import get_action_reasoner
                action_reasoner = get_action_reasoner()
                
                # 推断关注领域 (Focus Area)
                from app.models.action_plan import ActionCategory
                
                focus_area = None
                if any(k in message for k in ["保障", "保险", "重疾", "医疗"]):
                    focus_area = ActionCategory.WEALTH_PROTECTION
                elif any(k in message for k in ["投资", "增值", "理财", "股票", "基金"]):
                    focus_area = ActionCategory.WEALTH_GROWTH
                elif any(k in message for k in ["房产", "买房", "置换", "贷款"]):
                    focus_area = ActionCategory.REAL_ESTATE
                elif any(k in message for k in ["负债", "债务", "还款"]):
                    focus_area = ActionCategory.DEBT_OPTIMIZATION
                elif any(k in message for k in ["教育", "养老", "税务", "退休"]):
                    focus_area = ActionCategory.LIFE_PLANNING

                # 检查 "强制刷新" 意图
                force_keywords = ["重新生成", "重新制定", "覆盖", "强制", "新方案", "不够好", "不满意", "force"]
                should_force_new = any(k in message for k in force_keywords)
                
                # 如果用户要求重新生成，则不检查既有方案 (check_existing=False)
                check_existing = not should_force_new
                
                plans, status = await action_reasoner.generate_plan(
                    user_id, 
                    focus_area=focus_area, 
                    check_existing=check_existing
                )
                
                if plans:
                    logger.info(f"✅ [ORCHESTRATOR] Plan request handled: {len(plans)} plan(s), status={status}")
                    
                    if status in ["existing_active", "existing_pending"]:
                        instruction = "\n\n【重要指令】检测到用户请求方案，但系统中已存在一份相关的活跃方案。请告知用户：'检测到您目前已有一份正在执行(或待采纳)的同类行动方案（见下方卡片）。您是想继续查看这份方案，还是希望我基于最新情况为您重新生成一份？' (引导用户查看下方卡片)"
                    else:
                        instruction = "\n\n【重要指令】检测到用户请求行动方案，系统已为你生成了可视化的「行动方案卡片」(ActionPlanCard)。请务必简短回复，只需引导用户查看下方的卡片即可。严禁在回复中以文本形式输出具体的方案步骤或JSON数据，严禁重复输出方案内容。请只回复类似这样的内容：'我已根据您的资产状况，为您制定了如下行动方案，请查看下方卡片。'"
                        
                    return True, instruction
                    
            except Exception as e:
                logger.error(f"❌ Failed to generate plan on demand: {e}")
        
        return False, ""
    
    def _get_system_prompt(self, context: ConversationContext) -> str:
        """根据上下文获取 System Prompt (优先从 YAML 加载)."""
        try:
            return prompt_manager.render(
                category="chat",
                filename="agent_system",
                key="system_instruction"
            )
        except Exception as e:
            logger.warning(f"Failed to load prompt from YAML: {e}")
            return self._get_default_system_prompt()
    
    def _get_default_system_prompt(self) -> str:
        """获取默认 System Prompt (当 YAML 加载失败时)."""
        return """你是AssetFlow的首席资产配置专家，一位温暖、专业、值得信赖的财务顾问。

你的核心职责：
1. 通过对话了解用户的资产状况和财务目标
2. 基于标准普尔四象限模型提供专业的资产配置建议
3. 用温暖和同理心回应用户的财务焦虑

对话原则：
- 每次只问一个问题，不要连续追问
- 先认可用户分享的信息，再引导下一步
- 用emoji增加亲和力，但不要过度使用

严格遵守：
- 不要在回复中包含<Thought>标签，这是内部思考过程
- 不要重复询问用户已经回答过的问题"""
    
    # =========================================================================
    # RAG Augmentation Methods
    # =========================================================================
    
    # Keywords that trigger RAG retrieval for policy-related questions
    RAG_TRIGGER_KEYWORDS = [
        # 购房政策
        "政策", "限购", "购房资格", "买房条件", "购房条件",
        # 公积金
        "公积金", "住房公积金", "公积金贷款", "公积金提取",
        # 贷款
        "首付", "贷款", "房贷", "利率", "还款", "月供", "商贷", "组合贷",
        # 税费
        "税费", "契税", "个税", "增值税", "印花税",
        # 其他政策
        "户口", "社保", "纳税", "限售", "摇号", "积分", "人才"
    ]
    
    def _should_use_rag(self, message: str) -> bool:
        """
        判断用户消息是否需要触发 RAG 检索。
        
        仅对购房、贷款、政策等专业问题触发检索，普通闲聊或信息录入不触发。
        """
        settings = get_settings()
        if not settings.ENABLE_RAG_AUGMENTATION:
            return False
        
        # 检查触发词 (Keyword Match)
        message_lower = message.lower()
        for keyword in self.RAG_TRIGGER_KEYWORDS:
            if keyword in message_lower:
                logger.debug(f"🔍 [RAG] Triggered by keyword: {keyword}")
                return True
        
        # 检查问题模式 (Question Pattern Match)
        question_patterns = ["怎么", "如何", "可以", "能不能", "什么", "多少", "哪些", "需要", "条件"]
        property_keywords = ["房", "买", "购", "住", "置业"]
        
        has_question = any(p in message for p in question_patterns)
        has_property = any(k in message for k in property_keywords)
        
        if has_question and has_property:
            logger.debug(f"🔍 [RAG] Triggered by property question pattern")
            return True
        
        return False
    
    async def _augment_with_rag(
        self, 
        message: str, 
        context: ConversationContext
    ) -> tuple[str | None, list[KnowledgeChunk]]:
        """
        使用 RAG 增强 System Prompt。
        
        Returns:
            (augmented_system_prompt, sources): 如果检索成功返回增强后的 Prompt 和来源，否则返回 (None, [])
        """
        # 二次检查 (虽然上层已做意图过滤，这里做双重保险)
        if not self._should_use_rag(message):
            logger.debug(f"🔍 [RAG] Skipped - no trigger keywords found")
            return None, []
        
        try:
            from app.services.rag_engine import get_rag_engine
            
            settings = get_settings()
            rag_engine = get_rag_engine()
            
            # 构建检索上下文 (Contextual Retrieval)
            user_context = {}
            if context.user_profile:
                user_context["profile"] = context.user_profile
                user_context["city"] = context.user_profile.get("city", "")
            
            # 执行检索
            logger.info(f"🔍 [RAG] Querying knowledge base for: {message[:50]}...")
            rag_response = await rag_engine.query(
                question=message,
                user_context=user_context,
                top_k=settings.RAG_TOP_K
            )
            
            # 检查置信度阈值 (Confidence Check)
            if rag_response.confidence < settings.RAG_CONFIDENCE_THRESHOLD:
                logger.info(f"🔍 [RAG] Low confidence ({rag_response.confidence:.2f}), using fallback")
                return None, []
            
            # 记录来源于日志
            source_count = len(rag_response.sources)
            logger.info(f"🔍 [RAG] Retrieved {source_count} sources, confidence={rag_response.confidence:.2f}")
            
            # 构建增强后的 System Prompt
            augmented_prompt = self._build_rag_augmented_prompt(
                message=message,
                knowledge_chunks=rag_response.sources,
                rules_applied=rag_response.rules_applied
            )
            
            return augmented_prompt, rag_response.sources
            
        except Exception as e:
            logger.error(f"❌ [RAG] Augmentation failed: {e}")
            return None, []
    
    def _build_rag_augmented_prompt(
        self,
        message: str,
        knowledge_chunks: list[KnowledgeChunk],
        rules_applied: list | None = None
    ) -> str:
        """
        构建包含检索知识的 System Prompt。
        """
        # 格式化知识片段
        if knowledge_chunks:
            knowledge_parts = []
            for chunk in knowledge_chunks:
                source_info = f"(来源: {chunk.source})" if chunk.source else ""
                knowledge_parts.append(
                    f"【{chunk.category}】{chunk.title} {source_info}\n{chunk.content}"
                )
            knowledge_context = "\n\n".join(knowledge_parts)
        else:
            knowledge_context = "无相关参考知识"
        
        # 格式化政策约束 (Rule Constraints)
        if rules_applied:
            rule_constraints = "\n".join([
                f"- {r.constraint_text}" 
                for r in rules_applied 
                if hasattr(r, 'constraint_text')
            ])
        else:
            rule_constraints = "无特殊政策约束"
        
        # 尝试渲染模板
        try:
            return prompt_manager.render(
                category="rag",
                filename="knowledge_query",
                key="system_instruction",
                knowledge_context=knowledge_context,
                rule_constraints=rule_constraints,
                question=message
            )
        except Exception as e:
            logger.warning(f"Failed to render RAG prompt template: {e}")
            # Fallback prompt (硬编码兜底)
            return f"""你是一位专业的购房顾问和资产配置专家。请基于以下参考知识回答用户问题。

## 参考知识
{knowledge_context}

## 政策约束
{rule_constraints}

## 用户问题
{message}

## 回答要求
1. **优先使用参考知识**中的信息，确保回答准确
2. **政策约束是硬性规定**，必须遵守
3. 如果知识不足以完整回答，请明确说明
4. 引用具体政策时标注来源
5. 语气亲切专业"""
    
    def _build_messages(self, context: ConversationContext) -> list[dict[str, str]]:
        """
        构建发送给 LLM 的消息列表。
        
        包含:
        - 近期的对话历史
        - 用户画像摘要 (System Prompt 未必能包含所有细节)
        - 资产摘要
        """
        messages = []
        
        # 将上下文摘要作为第一条用户消息注入 (Context Injection)
        context_summary = self._build_context_summary(context)
        if context_summary:
            messages.append({
                "role": "user",
                "content": f"[系统信息] {context_summary}"
            })
            messages.append({
                "role": "assistant", 
                "content": "我已了解您的情况，请继续。"
            })
        
        # 添加近期对话历史
        for msg in context.get_recent_messages(10):
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        return messages
    
    def _build_context_summary(self, context: ConversationContext) -> str:
        """构建上下文摘要字符串 (用于注入 Prompt)."""
        parts = []
        
        # 用户画像 - 包含所有已收集字段，避免 LLM 重复询问
        if context.user_profile:
            profile_parts = []
            if context.user_profile.get("age_range") and context.user_profile.get("age_range") != "unknown":
                profile_parts.append(f"年龄: {context.user_profile['age_range']}")
            if context.user_profile.get("family_structure") and context.user_profile.get("family_structure") != "unknown":
                profile_parts.append(f"家庭: {context.user_profile['family_structure']}")
            if context.user_profile.get("occupation"):
                profile_parts.append(f"职业: {context.user_profile['occupation']}")
            # 收入范围
            if context.user_profile.get("income_range"):
                profile_parts.append(f"收入: {context.user_profile['income_range']}")
            # 日常支出 (不含房贷)
            if context.user_profile.get("monthly_expense"):
                base_expense = context.user_profile['monthly_expense']
                # 计算房产月供总和
                total_mortgage = sum(
                    re.get("monthly_payment", 0) 
                    for re in (context.real_estate_assets or [])
                )
                if total_mortgage > 0:
                    total_expense = base_expense + total_mortgage
                    profile_parts.append(f"日常支出: {base_expense:.0f}元(不含房贷)")
                    profile_parts.append(f"总月支出: {total_expense:.0f}元(含{total_mortgage:.0f}元月供)")
                else:
                    profile_parts.append(f"月支出: {base_expense:.0f}元")
            # 风险偏好
            if context.user_profile.get("risk_preference") and context.user_profile.get("risk_preference") not in ["unknown", "UNKNOWN"]:
                risk_map = {"CONSERVATIVE": "保守型", "MODERATE": "稳健型", "AGGRESSIVE": "激进型"}
                risk_display = risk_map.get(context.user_profile['risk_preference'], context.user_profile['risk_preference'])
                profile_parts.append(f"风险偏好: {risk_display}")
            if profile_parts:
                parts.append("用户已告知信息: " + ", ".join(profile_parts))
        
        # 资产摘要 (通用)
        if context.extracted_assets:
            asset_summary = []
            for asset in context.extracted_assets[:20]:  # Limit increased from 5 to 20
                name = asset.get("name", "未知")
                value = asset.get("value", 0)
                asset_type = asset.get("type", "other")
                asset_summary.append(f"{name}({asset_type}): {value:,.0f}元")
            if asset_summary:
                parts.append("已知资产: " + "; ".join(asset_summary))
        
        # 房产详细摘要 (包含贷款信息)
        if context.real_estate_assets:
            re_summary = []
            for re in context.real_estate_assets[:10]:  # Limit increased from 3 to 10
                name = re.get("name", "房产")
                city = re.get("city", "")
                area = re.get("area", 0)
                value = re.get("current_value", 0)
                loan_balance = re.get("loan_balance", 0)
                monthly_payment = re.get("monthly_payment", 0)
                
                re_info = f"{city}{name}({area}平米, 估值{value/10000:.0f}万)"
                
                # 添加贷款信息
                if loan_balance > 0:
                    re_info += f", 贷款余额{loan_balance/10000:.0f}万"
                if monthly_payment > 0:
                    re_info += f", 月供{monthly_payment:.0f}元"
                
                re_summary.append(re_info)
            
            if re_summary:
                parts.append("房产详情: " + "; ".join(re_summary))
        
        return " | ".join(parts) if parts else ""
    
    async def _background_extraction_pipeline(
        self, 
        message: str, 
        user_id: int, 
        context: ConversationContext
    ) -> None:
        """
        后台提取流水线 (Fire-and-Forget)。
        
        在响应发送给用户后异步运行，不阻塞主线程。
        
        任务列表:
        1. Information Extraction: 使用 LLM 提取资产、画像
        2. Context Refresh: 提取后使得缓存失效，强制下次从 DB 重新加载
        3. Insight Analysis: 心理画像与风险偏好分析
        4. ActionReasoner: 如果满足条件，尝试生成行动方案
        5. RealEstateAsset Sync: 详细房产数据与贷款信息同步
        6. FamilyProfile Update: 更新家庭成员图谱
        """
        try:
            logger.info(f"🔄 Background extraction pipeline started for user {user_id}")
            
            # Step 1: 信息提取 (Information Extraction)
            extraction_result = await self._trigger_information_extraction(message, user_id, context)
            
            # Step 2: 刷新上下文缓存 (Context Refresh)
            await self.context_manager.invalidate(user_id)
            
            # Step 3: 洞察分析 (Insight Analysis)
            # 每 N 轮对话触发一次
            await self._trigger_insight_analysis(user_id, context)
            
            # Step 4: 自动生成行动方案 (Action Plan Generation)
            await self._trigger_action_plan_generation(user_id, context)
            
            # Step 5: 房产数据同步 (Real Estate Sync)
            # 将提取到的 liability 和 asset 映射到 detailed real_estate_asset 表
            if extraction_result:
                assets = extraction_result.get("assets", [])
                logger.info(f"🏠 [DEBUG] extraction_result has {len(assets)} assets: {[a.get('type') for a in assets]}")
                await self._trigger_real_estate_sync(user_id, extraction_result)
            
            # Step 6: 家庭画像更新 (Family Profile)
            if extraction_result:
                await self._trigger_family_profile_update(user_id, extraction_result)
            
            logger.info(f"🎉 Background extraction pipeline completed for user {user_id}")
            
        except Exception as e:
            logger.error(f"❌ Background extraction pipeline failed: {e}")
    
    async def _trigger_information_extraction(
        self, 
        message: str, 
        user_id: int, 
        context: ConversationContext
    ) -> dict | None:
        """触发基于 LLM 的信息提取 (Information Extraction)."""
        try:
            from app.services.information_extraction import get_information_extractor, extract_information
            from app.services.asset_extraction_service import asset_extraction_service
            
            # 构建提取所需的近期历史
            recent_messages = context.get_recent_messages(5)
            
            # 使用 extract_information (Phase 2 标准接口)
            extraction_result = await extract_information(
                user_message=message,
                current_history=recent_messages
            )
            
            # 记录数据流向日志
            assets_count = len(extraction_result.get("assets", []))
            has_profile = bool(extraction_result.get("risk_profile"))
            logger.info(f"📥 [EXTRACT] user={user_id} assets={assets_count} profile={has_profile}")
            
            # data persistence 如果提取到了有效信息
            if extraction_result and (
                extraction_result.get("assets") or 
                extraction_result.get("risk_profile")
            ):
                success = await asset_extraction_service.update_user_state(user_id, extraction_result)
                logger.info(f"💾 [PERSIST] user={user_id} success={success}")
                

                
                logger.info(f"✅ Information extraction completed for user {user_id}")
                return extraction_result
            else:
                logger.debug(f"ℹ️ No new information extracted for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Information extraction failed: {e}")
            return None
    
    async def _trigger_insight_analysis(
        self, 
        user_id: int, 
        context: ConversationContext
    ) -> None:
        """触发深度洞察分析 (System 2: Insight Analysis)."""
        try:
            message_count = len(context.conversation_history)
            
            # 频率控制:
            # - 至少 2 条消息后
            # - 每 2 轮对话触发一次
            if message_count < 2 or message_count % 2 != 0:
                logger.debug(f"Skipping insight analysis: message_count={message_count}")
                return
            
            from app.services.insight_service import get_insight_service
            
            insight_service = get_insight_service()
            analysis_result = await insight_service.analyze_user_psychology(user_id)
            
            # Log the analysis result for debugging
            if analysis_result.get("skipped"):
                logger.info(f"ℹ️ Insight analysis skipped for user {user_id}: {analysis_result.get('reason')}")
            else:
                logger.info(f"✅ Insight analysis completed for user {user_id}")
            
            
        except Exception as e:
            logger.error(f"❌ Insight analysis failed: {e}")
    
    async def _trigger_action_plan_generation(
        self, 
        user_id: int, 
        context: ConversationContext
    ) -> None:
        """
        Phase 4: Trigger ActionReasoner to generate action plans.
        
        Only generates plans when:
        - Feature flag is enabled
        - Auto-generation is enabled
        - Sufficient context is available (at least 5 messages)
        """
        try:
            from app.core.config import get_settings
            
            settings = get_settings()
            
            # Check feature flags
            if not settings.ENABLE_ACTION_REASONER:
                return
            
            if not getattr(settings, 'ACTION_PLAN_AUTO_GENERATE', False):
                logger.debug("ActionReasoner auto-generate disabled")
                return
            
            # Only generate after sufficient conversation
            message_count = len(context.conversation_history)
            if message_count < 5:
                return
            
            # Only trigger every 5 turns to avoid spam
            if message_count % 5 != 0:
                return
            
            from app.services.action_reasoner import get_action_reasoner
            
            action_reasoner = get_action_reasoner()
            plans, status = await action_reasoner.generate_plan(user_id, check_existing=True)
            
            if plans:
                logger.info(f"🎯 [ACTION_REASONER] Background generation: {len(plans)} plan(s), status={status}")
            
        except Exception as e:
            logger.error(f"❌ ActionReasoner failed: {e}")
    

    async def _trigger_real_estate_sync(
        self, 
        user_id: int, 
        extraction_result: dict
    ) -> None:
        """
        同步提取的房产资产到详细表 (RealEstateAsset).
        
        该表为以下核心功能提供结构化数据支持：
        - RealEstateEngine (房产深度分析)
        - SwapSimulator (置换模拟)
        - PropertyValuation (估值服务)
        
        流程:
        1. 遍历提取到的 real_estate 类型资产
        2. 基于名称/地点/面积进行模糊匹配，判断是更新还是新建
        3. 遍历提取到的 liability (负债) 类型资产
        4. 尝试根据名称匹配到对应的房产，补充贷款余额和月供信息
        """
        try:
            from app.models.real_estate import RealEstateAsset
            from app.core.database import get_db_session
            from sqlmodel import select
            from datetime import datetime
            
            assets = extraction_result.get("assets", [])
            real_estate_assets = [a for a in assets if a.get("type") == "real_estate"]
            liability_assets = [a for a in assets if a.get("type") == "liability"]
            
            # 双重空校验 (只有两边都为空才跳过)
            if not real_estate_assets and not liability_assets:
                logger.debug("No real estate or liability assets to sync")
                return
            
            logger.info(f"🏠 [SYNC] Processing {len(real_estate_assets)} real estate, {len(liability_assets)} liability assets")
            
            async for session in get_db_session():
                for asset in real_estate_assets:
                    name = asset.get("name", "未命名房产")
                    amount = asset.get("amount", 0)
                    # 注意: location 和 area 是顶级字段，不在 metadata 中
                    location = asset.get("location", "")
                    area = asset.get("area", 0)
                    metadata = asset.get("metadata", {})
                    
                    logger.info(f"🏠 [DEBUG] Processing asset: name={name}, amount={amount}, location={location}, area={area}")
                    
                    # 解析城市 (Location Parsing)
                    city = "未知"
                    if location and "市" in location:
                        city = location.split("市")[0] + "市"
                    elif location:
                        city = location
                    
                    # 检查是否存在相似房产 (Fuzzy Matching)
                    # 获取该用户所有房产进行内存比对 (避免频繁 DB 查询)
                    stmt = select(RealEstateAsset).where(RealEstateAsset.user_id == user_id)
                    result = await session.execute(stmt)
                    user_properties = result.scalars().all()
                    
                    existing = self._find_matching_property(
                        candidates=user_properties,
                        name=name,
                        location=location,
                        area=area
                    )
                    
                    if existing:
                        # 更新现有房产
                        if amount > 0:
                            existing.current_value = amount
                        if area and area > 0:
                            existing.area = area
                        existing.value_source = "extraction"
                        existing.value_updated_at = datetime.utcnow()
                        logger.info(f"🏠 Updated RealEstateAsset: {name} for user {user_id}")
                    else:
                        # Calculate estimated value if not provided
                        current_value = amount
                        value_source = "extraction"
                        
                        if current_value <= 0:
                            try:
                                from app.services.property_valuation import get_property_valuation_service
                                valuation_service = get_property_valuation_service()
                                
                                # Use Tier 2/3 valuation
                                valuation = await valuation_service.get_market_value(
                                    location=f"{city}{location}",
                                    area=area if area and area > 0 else 100,
                                    property_type="residential"
                                )
                                current_value = valuation.value
                                value_source = f"auto_{valuation.source}"
                                logger.info(f"🏠 Auto-valued property: {current_value} (source={value_source})")
                            except Exception as e:
                                logger.warning(f"Failed to auto-value property: {e}")
                                current_value = 0 # Default to 0 if valuation fails (better than fake 1M)
                        
                        # 创建新房产 (使用字符串值而非 Enum 对象，避免序列化问题)
                        new_property = RealEstateAsset(
                            user_id=user_id,
                            name=name,
                            property_type="residential",  # Use string value
                            usage="self_occupied",        # Use string value
                            city=city,
                            area=area if area and area > 0 else 100,  # Default 100 sqm if not provided
                            current_value=current_value,
                            value_source=value_source,
                            loan_type="none",             # Use string value
                        )
                        session.add(new_property)
                        logger.info(f"🏠 Created RealEstateAsset: {name} for user {user_id}")
                
                # 处理 LIABILITY 资产 (主要是房贷) 以更新贷款信息
                liability_assets = [a for a in assets if a.get("type") == "liability"]
                logger.info(f"🏦 [DEBUG] Found {len(liability_assets)} LIABILITY assets: {liability_assets}")
                
                for liability in liability_assets:
                    liability_name = liability.get("name", "")
                    loan_amount = liability.get("amount", 0)
                    metadata = liability.get("metadata", {})
                    monthly_payment = metadata.get("monthly_payment", 0)
                    
                    logger.info(f"🏦 [DEBUG] Liability raw data: {liability}")
                    logger.info(f"🏦 [DEBUG] Checking mortgage keywords in '{liability_name}'")
                    
                    # 校验是否为房贷 (关键字过滤)
                    if not any(keyword in liability_name for keyword in ["房贷", "房产", "住房贷款", "按揭", "贷款"]):
                        logger.info(f"🏦 [DEBUG] Skipping - not a mortgage: {liability_name}")
                        continue
                    
                    logger.info(f"🏦 [DEBUG] Processing mortgage: name={liability_name}, loan={loan_amount}, monthly={monthly_payment}")
                    
                    # Find the corresponding RealEstateAsset to update
                    # Try to match by city name in the liability name
                    re_stmt = select(RealEstateAsset).where(RealEstateAsset.user_id == user_id)
                    re_result = await session.execute(re_stmt)
                    user_properties = re_result.scalars().all()
                    
                    matched_property = None
                    for prop in user_properties:
                        # Match by city name in liability name
                        if prop.city and prop.city in liability_name:
                            matched_property = prop
                            break
                        # Match by property name in liability name
                        if prop.name and prop.name in liability_name:
                            matched_property = prop
                            break
                    
                    # If no match found, update the first/most recent property
                    if not matched_property and user_properties:
                        matched_property = user_properties[0]
                    
                    if matched_property:
                        if loan_amount > 0:
                            matched_property.loan_balance = loan_amount
                            matched_property.loan_type = "commercial"  # Default to commercial loan
                        if monthly_payment > 0:
                            matched_property.monthly_payment = monthly_payment
                        matched_property.value_updated_at = datetime.utcnow()
                        logger.info(f"🏦 Updated loan info for {matched_property.name}: balance={loan_amount}, monthly={monthly_payment}")
                
                await session.commit()
                break
            
            logger.info(f"🏠 [REAL_ESTATE_SYNC] user={user_id} synced={len(real_estate_assets)} properties")
            
        except Exception as e:
            logger.error(f"❌ Failed to sync real estate assets for user {user_id}: {e}")

    async def _trigger_family_profile_update(
        self, 
        user_id: int, 
        extraction_result: dict
    ) -> None:
        """
        根据提取的用户画像更新家庭档案 (FamilyProfile).
        
        创建家庭成员图谱和生命周期事件。
        该数据将直接用于 ActionReasoner 的财务规划建议。
        """
        try:
            from app.services.family_profile import get_family_profile_service
            from app.core.config import get_settings
            
            settings = get_settings()
            if not settings.ENABLE_FAMILY_PROFILE:
                logger.debug("FamilyProfile disabled by feature flag")
                return
            
            risk_profile = extraction_result.get("risk_profile", {})
            family_structure = risk_profile.get("family_structure")
            
            # 仅在有家庭结构信息时更新
            if not family_structure or family_structure == "unknown":
                return
            
            family_service = get_family_profile_service()
            
            # 从画像数据中解析家庭成员
            family_info = await family_service.extract_family_info_from_profile(risk_profile)
            
            # 解析收入范围字符串为数值 (e.g., "48万" -> 480000)
            total_income = None
            income_str = risk_profile.get("income_range", "")
            if income_str:
                try:
                    import re
                    # Extract number and unit from strings like "48万", "年收入50万", "500000"
                    match = re.search(r'(\d+(?:\.\d+)?)\s*万?', str(income_str))
                    if match:
                        value = float(match.group(1))
                        if '万' in str(income_str):
                            value *= 10000
                        total_income = value
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse income_range: {income_str}")
                    total_income = None
            
            # 解析日常支出
            # 注意: 此时的 monthly_expense 已剥离房贷，仅代表日常开销
            total_expenses = risk_profile.get("monthly_expense")
            if total_expenses is not None:
                try:
                    total_expenses = float(total_expenses)
                except (ValueError, TypeError):
                    total_expenses = None
            
            # 更新 FamilyProfile
            await family_service.create_or_update_profile(
                user_id=user_id,
                members=family_info.get("members"),
                lifecycle_events=family_info.get("lifecycle_events"),
                total_income=total_income,
                total_expenses=total_expenses
            )
            
            members_count = len(family_info.get("members", []))
            events_count = len(family_info.get("lifecycle_events", []))
            logger.info(f"👨‍👩‍👧 [FAMILY_PROFILE] user={user_id} members={members_count} events={events_count}")
            
        except Exception as e:
            logger.error(f"❌ Failed to update family profile for user {user_id}: {e}")



    def _find_matching_property(
        self,
        candidates: list[Any],
        name: str,
        location: str | None,
        area: float | None
    ) -> Any | None:
        """通过模糊逻辑查找匹配的房产 (需与 AssetExtractionService 保持一致)."""
        # Normalize extracted data
        ext_loc_norm = location.replace(" ", "").lower() if location else ""
        ext_name_norm = name.replace(" ", "").lower()
        
        for prop in candidates:
            # Normalize property data
            prop_loc = f"{prop.city or ''}{prop.district or ''}{prop.address or ''}"
            prop_loc_norm = prop_loc.replace(" ", "").lower()
            prop_name_norm = prop.name.replace(" ", "").lower()
            
            # MATCH 1: Location overlap (地点重叠 - 强信号)
            if ext_loc_norm and prop_loc_norm:
                if ext_loc_norm in prop_loc_norm or prop_loc_norm in ext_loc_norm:
                    logger.info(f"🏠 [SYNC] Matched by location overlap: '{location}' ~ '{prop_loc}'")
                    return prop

            # MATCH 2: Name overlap (名称重叠)
            if ext_name_norm in prop_name_norm or prop_name_norm in ext_name_norm:
                 logger.info(f"🏠 [SYNC] Matched by name overlap: '{name}' ~ '{prop.name}'")
                 return prop
                 
            # MATCH 3: Cross-field overlap (交叉字段重叠)
            if ext_loc_norm and prop_name_norm:
                 if ext_loc_norm in prop_name_norm or prop_name_norm in ext_loc_norm:
                     logger.info(f"🏠 [SYNC] Matched by cross-field: '{location}' ~ '{prop.name}'")
                     return prop
                     
            if ext_name_norm and prop_loc_norm:
                if ext_name_norm in prop_loc_norm or prop_loc_norm in ext_name_norm:
                    logger.info(f"🏠 [SYNC] Matched by cross-field: '{name}' ~ '{prop_loc}'")
                    return prop
            
            # MATCH 4: Area exact match (面积精确匹配 - 辅助验证)
            if area and prop.area:
                if abs(area - prop.area) < 5:
                    logger.info(f"🏠 [SYNC] Matched by area: {area} ~ {prop.area}")
                    return prop
            
            # MATCH 5: Fuzzy name check (模糊名称检查)
            if self._is_name_similar(name, prop.name):
                logger.info(f"🏠 [SYNC] Matched by fuzzy name: '{name}' ~ '{prop.name}'")
                return prop
                
        return None

    def _is_name_similar(self, name1: str, name2: str) -> bool:
        """使用 Jaccard 指数检查单词相似度。"""
        import re
        # Normalize
        n1 = name1.lower().replace(" ", "")
        n2 = name2.lower().replace(" ", "")
        
        # 子串匹配快捷方式
        if n1 in n2 or n2 in n1:
            return True
            
        # 分词
        words1 = set(re.findall(r'[\w]+', name1.lower()))
        words2 = set(re.findall(r'[\w]+', name2.lower()))
        
        # 移除单字
        words1 = {w for w in words1 if len(w) > 1}
        words2 = {w for w in words2 if len(w) > 1}
        
        if not words1 or not words2:
            return False
            
        intersection = words1 & words2
        union = words1 | words2
        
        if not union:
            return False
            
        similarity = len(intersection) / len(union)
        return similarity > 0.5


# Singleton instance
_orchestrator: ConversationOrchestrator | None = None


def get_conversation_orchestrator() -> ConversationOrchestrator:
    """获取或创建 ConversationOrchestrator 单例实例。"""
    global _orchestrator
    if _orchestrator is None:
        from app.core.dependencies import get_llm_provider, get_context_manager
        
        _orchestrator = ConversationOrchestrator(
            llm_provider=get_llm_provider(),
            context_manager=get_context_manager()
        )
    return _orchestrator
