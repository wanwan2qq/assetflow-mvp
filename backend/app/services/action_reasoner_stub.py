
    async def refine_plan(
        self,
        plan_id: int,
        feedback: str
    ) -> ActionPlan | None:
        """根据用户反馈调整计划"""
        try:
            async for session in get_db_session():
                # 1. 获取原计划
                stmt = select(ActionPlan).where(ActionPlan.id == plan_id)
                result = await session.execute(stmt)
                plan = result.scalar_one_or_none()
                
                if not plan or plan.status != "pending":
                    logger.warning(f"Plan {plan_id} not found or not pending")
                    return None
                
                # 2. 调用 LLM 调整
                new_plan_data = await self._refine_plan_with_llm(plan, feedback)
                
                if new_plan_data:
                    # 3. 更新现有计划
                    plan.summary = new_plan_data.get("summary", plan.summary)
                    plan.original_steps_snapshot = new_plan_data.get("steps", plan.original_steps_snapshot)
                    plan.expected_benefits = new_plan_data.get("expected_benefits", plan.expected_benefits)
                    plan.potential_risks = new_plan_data.get("potential_risks", plan.potential_risks)
                    plan.updated_at = datetime.utcnow()
                    
                    session.add(plan)
                    await session.commit()
                    await session.refresh(plan)
                    
                    logger.info(f"✅ [ACTION_REASONER] Refined plan {plan_id}")
                    return plan
                    
            return None
            
        except Exception as e:
            logger.error(f"Error refining plan: {e}")
            return None

    async def _refine_plan_with_llm(self, plan: ActionPlan, feedback: str) -> dict | None:
        """调用 LLM 根据反馈修改计划 JSON"""
        try:
            from app.core.dependencies import get_llm_provider
            llm_provider = get_llm_provider()
            
            current_json = {
                "title": plan.title,
                "summary": plan.summary,
                "steps": plan.original_steps_snapshot,
                "expected_benefits": plan.expected_benefits,
                "potential_risks": plan.potential_risks
            }
            
            prompt = f"""你是一位专业的财务顾问。用户希望调整以下行动方案。

当前方案 (JSON):
{json.dumps(current_json, ensure_ascii=False, indent=2)}

用户反馈: "{feedback}"

请根据反馈修改方案。保持 JSON 结构不变（title, summary, steps, expected_benefits, potential_risks）。
仅返回修改后的 JSON。"""

            messages = [{"role": "user", "content": prompt}]
            
            response = ""
            async for chunk in llm_provider.generate_stream(messages, "您是一个JSON生成助手。"):
                response += chunk
                
            # 解析 JSON
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
                
            return None
            
        except Exception as e:
            logger.error(f"Error refining plan with LLM: {e}")
            return None
