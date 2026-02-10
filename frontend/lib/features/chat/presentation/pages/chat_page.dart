import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../../../../core/services/websocket_service.dart';
import '../../../../core/providers/auth_provider.dart';
import '../../../../core/services/chat_history_service.dart';
import '../../../../core/models/chat_history.dart';
import '../../../../core/models/asset.dart';
import '../../../../core/models/user.dart';
import '../../../../shared/widgets/action_card.dart';
import '../../../../shared/widgets/portfolio_chart.dart';
import '../../../../shared/widgets/product_card.dart';
import '../../../../shared/widgets/action_plan_card.dart';
import '../../../../core/models/action_plan.dart';
import '../../services/card_action_handler.dart';
import '../widgets/fact_sheet_drawer.dart';
import '../widgets/chat_asset_card.dart';

// STATE PRESERVATION NOTES:
// 1. This page uses AutomaticKeepAliveClientMixin to preserve state when switching tabs
// 2. The app uses go_router with ShellRoute, which provides basic state preservation
// 3. The ListView uses reverse: true to naturally show latest messages at bottom without
//    manual scrolling, eliminating visual jumps and lag
// 4. Messages are displayed with inverted index to show newest at bottom when reversed

class ChatPage extends ConsumerStatefulWidget {
  const ChatPage({super.key});

  @override
  ConsumerState<ChatPage> createState() => _ChatPageState();
}

class _ChatPageState extends ConsumerState<ChatPage> with AutomaticKeepAliveClientMixin {
  final _messageController = TextEditingController();
  final _scrollController = ScrollController();
  final List<ChatMessage> _messages = [];
  StreamSubscription<String>? _messageSubscription;
  StreamSubscription<WebSocketConnectionState>? _connectionSubscription;
  bool _isConnecting = false;
  
  // Add a state variable to track connection state for UI updates
  WebSocketConnectionState _currentConnectionState = WebSocketConnectionState.disconnected;
  
  @override
  bool get wantKeepAlive => true;

  @override
  void initState() {
    super.initState();
    // Initialize connection state from WebSocket service
    WidgetsBinding.instance.addPostFrameCallback((_) {
      final webSocketService = ref.read(webSocketServiceProvider);
      setState(() {
        _currentConnectionState = webSocketService.connectionState;
      });
      
      // Load chat history when the page initializes
      _loadChatHistory();
    });
  }

  Future<void> _loadChatHistory() async {
    try {
      final chatHistoryService = ref.read(chatHistoryServiceProvider.notifier);
      final history = await chatHistoryService.loadChatHistory(limit: 50);
      
      // Convert history messages to ChatMessage objects
      final historyMessages = history.messages.map((historyMsg) {
        // Parse widgets from meta_data if available
        List<Widget>? widgets;
        if (historyMsg.widgets != null && historyMsg.widgets!.isNotEmpty) {
          widgets = _parseWidgetsFromMetaData(historyMsg.widgets!);
        }
        
        // Also parse widgets from text content (new method)
        // If there are embedded <WIDGET...> tags, parse them
        final textWidgets = _parseEmbeddedWidgets(historyMsg.content);
        if (textWidgets != null) {
          widgets = [...?widgets, ...textWidgets];
        }
        
        return ChatMessage(
          text: historyMsg.content,
          isUser: historyMsg.isUser,
          timestamp: historyMsg.parsedTimestamp,
          isStreaming: false,
          embeddedWidgets: widgets,
        );
      }).toList();
      
      // Add history messages to the chat
      setState(() {
        _messages.clear();
        _messages.addAll(historyMessages);
      });
      
      // No need to scroll - reverse: true will naturally show latest messages
      print('✅ Loaded ${historyMessages.length} messages from chat history');
      
    } catch (error) {
      print('❌ Failed to load chat history: $error');
      // Don't show error to user for history loading failure
      // Just continue with empty chat
    }
  }

  List<Widget>? _parseWidgetsFromMetaData(List<WidgetData> widgetDataList) {
    final widgets = <Widget>[];
    
    for (final widgetData in widgetDataList) {
      switch (widgetData.widgetType) {
        case 'VALUATION_CARD':
          final data = widgetData.data;
          widgets.add(
            ChatAssetCard(
              data: {
                ...data,
                'name': data['location'] ?? '房产',
                'value': data['price'],
                'unit_price': data['area'] != null 
                    ? '${((data['price'] as num?) ?? 0) ~/ (data['area'] as num? ?? 1) / 10000}万/平'
                    : '未知',
                'type': 'real_estate',
              },
              onConfirm: () async {
                await ref.read(cardActionHandlerProvider).handleAction(
                  context,
                  actionType: 'confirm_valuation',
                  data: data,
                  onSendUserMessage: _sendMessage,
                  onUpdateUi: () => _loadChatHistory(),
                );
              },
              onModify: () async {
                await ref.read(cardActionHandlerProvider).handleAction(
                  context,
                  actionType: 'edit_valuation',
                  data: data,
                  onSendUserMessage: _sendMessage,
                  onUpdateUi: () => _loadChatHistory(),
                );
              },
            ),
          );
          break;
          
        case 'ACTION_CARD':
          final data = widgetData.data;
          widgets.add(
            ActionCard(
              type: _parseActionCardType(data['type'] as String?),
              title: data['title'] as String? ?? '操作建议',
              description: data['description'] as String? ?? '',
              onTap: () {
                _sendMessage('告诉我更多关于${data['title'] ?? '这个建议'}的信息');
              },
            ),
          );
          break;
          
        case 'PORTFOLIO_CHART':
          final data = widgetData.data;
          final assets = (data['assets'] as List<dynamic>?)?.map((assetData) {
            return UserAsset(
              id: assetData['id'] ?? 0,
              userId: assetData['userId'] ?? 0,
              assetType: _parseAssetType(assetData['assetType'] as String?),
              name: assetData['name'] ?? '未知资产',
              value: (assetData['value'] as num?)?.toDouble() ?? 0,
              isConfirmed: assetData['isConfirmed'] ?? false,
              createdAt: DateTime.now(),
              updatedAt: DateTime.now(),
            );
          }).toList() ?? [];
          
          widgets.add(
            PortfolioChart(
              assets: assets,
              title: data['title'] as String? ?? '资产配置分析',
              onTap: () {
                _sendMessage('请详细解释我的资产配置');
              },
            ),
          );
          break;
          
        case 'ASSET_CARD':
          final data = widgetData.data;
          widgets.add(
            ChatAssetCard(
              data: data,
              onConfirm: () async {
                 await ref.read(cardActionHandlerProvider).handleAction(
                  context,
                  actionType: 'confirm_asset',
                  data: data,
                  onSendUserMessage: _sendMessage,
                  onUpdateUi: () => _loadChatHistory(),
                );
              },
              onModify: () async {
                 await ref.read(cardActionHandlerProvider).handleAction(
                  context,
                  actionType: 'edit_asset',
                  data: data,
                  onSendUserMessage: _sendMessage,
                  onUpdateUi: () => _loadChatHistory(),
                );
              },
            ),
          );
          break;

        case 'PRODUCT_CARD':
          final data = widgetData.data;
          widgets.add(
            ProductCard(
              name: data['name'] as String? ?? '推荐产品',
              provider: data['provider'] as String? ?? '未知服务商',
              category: data['category'] as String? ?? 'general',
              description: data['description'] as String? ?? '',
              price: data['price'] as String?,
              roi: data['roi'] as String?,
              buyNowLink: data['buy_now_link'] as String?,
              contactInfo: data['contact_info'] as Map<String, dynamic>?,
              priority: data['priority'] as String? ?? 'medium',
              reason: data['reason'] as String?,
              onTap: () {
                ref.read(cardActionHandlerProvider).handleAction(
                  context,
                  actionType: 'send_message',
                  data: {'message': '我对${data['name'] ?? '这个产品'}感兴趣，请提供更多信息'},
                  onSendUserMessage: _sendMessage,
                );
              },
              onContact: () {
                ref.read(cardActionHandlerProvider).handleAction(
                  context,
                  actionType: 'contact_product',
                  data: data,
                  onSendUserMessage: _sendMessage,
                );
              },
            ),
          );
          break;
          
        case 'ACTION_PLAN_CARD':
          final data = widgetData.data;
          try {
            final plan = ActionPlan.fromJson(data);
            widgets.add(
              ActionPlanCard(
                plan: plan,
              ),
            );
          } catch (e) {
            print('❌ Error parsing ActionPlan from history: $e');
          }
          break;
      }
    }
    
    return widgets.isNotEmpty ? widgets : null;
  }

  ActionCardType _parseActionCardType(String? type) {
    switch (type) {
      case 'warning':
        return ActionCardType.warning;
      case 'insurance':
        return ActionCardType.insurance;
      case 'broker':
        return ActionCardType.broker;
      case 'investment':
        return ActionCardType.investment;
      default:
        return ActionCardType.warning;
    }
  }

  AssetType _parseAssetType(String? type) {
    switch (type) {
      case 'real_estate':
        return AssetType.realEstate;
      case 'cash':
        return AssetType.cash;
      case 'investment':
        return AssetType.investment;
      case 'insurance':
        return AssetType.insurance;
      default:
        return AssetType.cash;
    }
  }

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    _messageSubscription?.cancel();
    _connectionSubscription?.cancel();

    super.dispose();
  }

  Future<void> _connectWebSocket(int userId, String token) async {
    final webSocketService = ref.read(webSocketServiceProvider);
    
    // Check if already connected or connecting
    if (_isConnecting) {
      return;
    }
    
    if (webSocketService.isConnected) {
      return;
    }
    
    print('🔌 Connecting WebSocket for user $userId with token ${token.substring(0, 20)}...');
    
    setState(() {
      _isConnecting = true;
    });

    try {
      // Disconnect existing connection first if any
      if (webSocketService.connectionState != WebSocketConnectionState.disconnected) {
        await webSocketService.disconnect();
        await Future.delayed(const Duration(milliseconds: 500));
      }
      
      // Listen to connection state changes
      _connectionSubscription?.cancel();
      _connectionSubscription = webSocketService.connectionStateStream.listen(
        (state) {
          if (mounted) {
            setState(() {
              _currentConnectionState = state;
              _isConnecting = state == WebSocketConnectionState.connecting || 
                              state == WebSocketConnectionState.reconnecting;
            });
          }
        },
      );
      
      // Listen to incoming messages
      _messageSubscription?.cancel();
      _messageSubscription = webSocketService.messageStream.listen(
        (message) {
          _handleIncomingMessage(message);
        },
        onError: (error) {
          // Error handled by connection state stream, just log if needed
          print('WebSocket message stream error: $error');
        },
      );
      
      await webSocketService.connect(userId, token);
      
    } catch (error) {
      print('❌ WebSocket connection failed: $error');
      // Error is handled by connection state stream
    } finally {
      if (mounted) {
        setState(() {
          _isConnecting = false;
        });
      }
    }
  }

  void _handleIncomingMessage(String message) {
    try {
      // Validate UTF-8 encoding first
      try {
        message.codeUnits; // This will throw if there are invalid UTF-8 sequences
      } catch (e) {
        // Try to clean the message by replacing invalid characters
        message = String.fromCharCodes(
          message.runes.where((rune) => rune != 0xFFFD).toList()
        );
      }
      
      // Parse JSON message from backend
      final messageData = json.decode(message);
      final messageType = messageData['type'] as String?;
      final content = messageData['content'] as String? ?? '';
      
      if (content.isEmpty && messageType != 'typing') return;
      
      switch (messageType) {
        case 'system':
          // Welcome message - add as AI message
          setState(() {
            _messages.add(ChatMessage(
              text: content,
              isUser: false,
              timestamp: DateTime.now(),
              isStreaming: false,
            ));
          });
          break;
          
        case 'typing':
          // Show typing indicator
          setState(() {
            _messages.add(ChatMessage(
              text: content,
              isUser: false,
              timestamp: DateTime.now(),
              isStreaming: true,
            ));
          });
          break;
          
        case 'chunk':
          // Handle streaming response chunks
          if (_messages.isNotEmpty && _messages.last.isStreaming && !_messages.last.isUser) {
            // Update the last streaming message
            setState(() {
              final lastIndex = _messages.length - 1;
              _messages[lastIndex] = _messages[lastIndex].copyWith(
                text: _messages[lastIndex].text + content,
              );
            });
          } else {
            // Start a new AI message
            setState(() {
              _messages.add(ChatMessage(
                text: content,
                isUser: false,
                timestamp: DateTime.now(),
                isStreaming: true,
              ));
            });
          }
          break;
          
        case 'complete':
          // Complete message received - finalize streaming message
          if (_messages.isNotEmpty && _messages.last.isStreaming && !_messages.last.isUser) {
            setState(() {
              final lastIndex = _messages.length - 1;
              // Don't add content again - just mark as complete and parse widgets
              final currentText = _messages[lastIndex].text;
              final widgets = _parseEmbeddedWidgets(currentText);
              
              _messages[lastIndex] = _messages[lastIndex].copyWith(
                text: currentText, // Keep existing text from chunks
                isStreaming: false,
                embeddedWidgets: widgets,
              );
            });
          } else {
            // Add complete message (fallback case)
            final widgets = _parseEmbeddedWidgets(content);
            setState(() {
              _messages.add(ChatMessage(
                text: content,
                isUser: false,
                timestamp: DateTime.now(),
                isStreaming: false,
                embeddedWidgets: widgets,
              ));
            });
          }
          break;
          
        case 'error':
          // Handle error messages
          print('❌ AI Error: $content');
          break;
          
        default:
          // Fallback for unknown message types
          setState(() {
            _messages.add(ChatMessage(
              text: content,
              isUser: false,
              timestamp: DateTime.now(),
              isStreaming: false,
            ));
          });
      }
      
    } catch (e) {
      // Check if this is a UTF-8 encoding error
      if (e.toString().contains('UTF-8') || e.toString().contains('REPLACEMENT CHARACTER')) {
        // Try to extract readable content
        try {
          final cleanMessage = message.replaceAll(RegExp(r'[^\x20-\x7E\u4e00-\u9fff]'), '');
          if (cleanMessage.trim().isNotEmpty) {
            setState(() {
              _messages.add(ChatMessage(
                text: '消息已处理: $cleanMessage',
                isUser: false,
                timestamp: DateTime.now(),
                isStreaming: false,
              ));
            });
          }
        } catch (cleanError) {
          print('Failed to clean message: $cleanError');
        }
        return;
      }
      
      // Only add as message if it's not empty and looks like actual content
      if (message.trim().isNotEmpty && !message.startsWith('{')) {
        setState(() {
          _messages.add(ChatMessage(
            text: message,
            isUser: false,
            timestamp: DateTime.now(),
            isStreaming: false,
          ));
        });
      }
    }
  }

  List<Widget>? _parseEmbeddedWidgets(String text) {
    if (!text.contains('<WIDGET:')) {
      return null;
    }
    
    final widgets = <Widget>[];
    
    // Parse VALUATION_CARD with JSON data
    if (text.contains('<WIDGET:VALUATION_CARD')) {
      final matches = RegExp(r'<WIDGET:VALUATION_CARD data="([^"]*)"').allMatches(text);
      for (final match in matches) {
        try {
          var jsonStr = match.group(1) ?? '{}';
          jsonStr = jsonStr.replaceAll('&quot;', '"');
          if (!jsonStr.contains('"') && jsonStr.contains("'")) {
             jsonStr = jsonStr.replaceAll("'", '"');
             jsonStr = jsonStr.replaceAllMapped(
               RegExp(r'([{,]\s*)([a-zA-Z0-9_]+)(\s*:)'), 
               (m) => '${m[1]}"${m[2]}"${m[3]}'
             );
          }
          
          final data = json.decode(jsonStr) as Map<String, dynamic>;
          final estimatedValue = (data['price'] as num?)?.toDouble() ?? 0;
          
          if (estimatedValue <= 0 && data['id'] == null) continue;

          widgets.add(
            ChatAssetCard(
              data: {
                ...data,
                'name': data['location'] ?? '房产',
                'value': estimatedValue,
                'unit_price': data['area'] != null && data['area'] > 0
                    ? '${((data['price_per_sqm'] as num?) ?? estimatedValue / (data['area'] as num)).toStringAsFixed(0)}元/平'
                    : '未知',
                'type': 'real_estate',
              },
              onConfirm: () async {
                await ref.read(cardActionHandlerProvider).handleAction(
                  context,
                  actionType: 'confirm_valuation',
                  data: data,
                  onSendUserMessage: _sendMessage,
                  onUpdateUi: () => _loadChatHistory(),
                );
              },
              onModify: () async {
                await ref.read(cardActionHandlerProvider).handleAction(
                  context,
                  actionType: 'edit_valuation',
                  data: data,
                  onSendUserMessage: _sendMessage,
                  onUpdateUi: () => _loadChatHistory(),
                );
              },
            ),
          );
        } catch (e) {
          print('❌ DEBUG: Error parsing VALUATION_CARD data: $e');
        }
      } 
    }
    
    // Parse ACTION_CARD with JSON data
    if (text.contains('<WIDGET:ACTION_CARD')) {
      final matches = RegExp(r'<WIDGET:ACTION_CARD data="([^"]*)"').allMatches(text);
      for (final match in matches) {
        try {
          final jsonStr = match.group(1)?.replaceAll('&quot;', '"') ?? '{}';
          final data = json.decode(jsonStr) as Map<String, dynamic>;
          widgets.add(
            ActionCard(
              type: _parseActionCardType(data['type'] as String?),
              title: data['title'] as String? ?? '操作建议',
              description: data['description'] as String? ?? '',
              onTap: () {
                _sendMessage('告诉我更多关于${data['title'] ?? '这个建议'}的信息');
              },
            ),
          );
        } catch (e) {
          print('❌ DEBUG: Error parsing ACTION_CARD data: $e');
        }
      }
    }

    // Parse PORTFOLIO_CHART
    if (text.contains('<WIDGET:PORTFOLIO_CHART')) {
      final match = RegExp(r'<WIDGET:PORTFOLIO_CHART data="([^"]*)"').firstMatch(text);
      if (match != null) {
        try {
          final jsonStr = match.group(1)?.replaceAll('&quot;', '"') ?? '{}';
          final data = json.decode(jsonStr) as Map<String, dynamic>;
          
          final assets = (data['assets'] as List<dynamic>?)?.map((assetData) {
            return UserAsset(
              id: assetData['id'] ?? 0,
              userId: assetData['userId'] ?? 0,
              assetType: _parseAssetType(assetData['assetType'] as String?),
              name: assetData['name'] ?? '未知资产',
              value: (assetData['value'] as num?)?.toDouble() ?? 0,
              isConfirmed: assetData['isConfirmed'] ?? false,
              createdAt: DateTime.now(),
              updatedAt: DateTime.now(),
            );
          }).toList() ?? [];
          
          widgets.add(
            PortfolioChart(
              assets: assets,
              title: data['title'] as String? ?? '资产配置分析',
              onTap: () {
                _sendMessage('请详细解释我的资产配置');
              },
            ),
          );
        } catch (e) {
           print('❌ DEBUG: Error parsing PORTFOLIO_CHART data: $e');
        }
      }
    }
    
    // Parse ASSET_CARD with JSON data
    if (text.contains('<WIDGET:ASSET_CARD')) {
      final match = RegExp(r'<WIDGET:ASSET_CARD data="([^"]*)"').firstMatch(text);
      if (match != null) {
        try {
          final jsonStr = match.group(1)?.replaceAll('&quot;', '"') ?? '{}';
          final data = json.decode(jsonStr) as Map<String, dynamic>;
          
          widgets.add(
            ChatAssetCard(
              data: data,
              onConfirm: () async {
                await ref.read(cardActionHandlerProvider).handleAction(
                  context,
                  actionType: 'confirm_asset',
                  data: data,
                  onSendUserMessage: _sendMessage,
                  onUpdateUi: () => _loadChatHistory(),
                );
              },
              onModify: () async {
                await ref.read(cardActionHandlerProvider).handleAction(
                  context,
                  actionType: 'edit_asset',
                  data: data,
                  onSendUserMessage: _sendMessage,
                  onUpdateUi: () => _loadChatHistory(),
                );
              },
            ),
          );
        } catch (e) {
          print('❌ DEBUG: Error parsing ASSET_CARD data: $e');
        }
      }
    }

    return widgets.isNotEmpty ? widgets : null;
  }

  @override
  Widget build(BuildContext context) {
    super.build(context);
    
    final webSocketService = ref.watch(webSocketServiceProvider);
    final connectionState = _currentConnectionState;
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    // ... (Auth checks remain same) ...
     WidgetsBinding.instance.addPostFrameCallback((_) async {
      final authState = ref.read(authStateProvider);
      final token = await ref.read(authTokenProvider.future);
      if (authState.value != null && 
          token != null && 
          (connectionState == WebSocketConnectionState.disconnected || 
           connectionState == WebSocketConnectionState.error)) {
        _connectWebSocket(authState.value!.id, token);
      }
    });

    // ... (Listeners remain same) ...
    ref.listen<AsyncValue<User?>>(authStateProvider, (previous, next) async {
      final token = await ref.read(authTokenProvider.future);
      final currentState = webSocketService.connectionState;
      if (next.value != null && token != null) {
        if (currentState == WebSocketConnectionState.disconnected || 
            currentState == WebSocketConnectionState.error) {
          WidgetsBinding.instance.addPostFrameCallback((_) {
            _connectWebSocket(next.value!.id, token);
          });
        }
      } else {
        WidgetsBinding.instance.addPostFrameCallback((_) {
          webSocketService.disconnect();
        });
      }
    });

    ref.listen(authTokenProvider, (previous, next) {
       final authState = ref.read(authStateProvider);
       final nextToken = next.whenOrNull(data: (t) => t);
       final previousToken = previous?.whenOrNull(data: (t) => t);
       
       if (authState.value != null && nextToken != null && previousToken != nextToken && previousToken != null) {
         WidgetsBinding.instance.addPostFrameCallback((_) {
           _connectWebSocket(authState.value!.id, nextToken);
         });
       }
    });
    
    return Scaffold(
      backgroundColor: isDark ? const Color(0xFF121212) : Colors.grey[50], // Theme Requirement 1
      endDrawer: const FactSheetDrawer(),
      appBar: AppBar(
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              'inW Assistant', // Theme Requirement 1.1
              style: TextStyle(fontWeight: FontWeight.bold),
            ),
            if (_currentConnectionState == WebSocketConnectionState.connected) ...[
              const SizedBox(width: 8),
              Container(
                width: 8,
                height: 8,
                decoration: const BoxDecoration(
                  color: Colors.green, // Theme Requirement 1.2
                  shape: BoxShape.circle,
                ),
              ),
            ],
          ],
        ),
        centerTitle: true,
        backgroundColor: Colors.transparent,
        elevation: 0,
        actions: [
          IconButton(
            icon: const Icon(Icons.delete_outline), // Theme Requirement 1.3
            tooltip: '清除对话',
            onPressed: () {
              setState(() {
                _messages.clear();
              });
              // Optionally call service to clear history
            },
          ),
          Builder(
            builder: (context) => IconButton(
              icon: const Icon(Icons.folder_shared_outlined),
              tooltip: '档案',
              onPressed: () => Scaffold.of(context).openEndDrawer(),
            ),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              reverse: true,
              controller: _scrollController,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final message = _messages[_messages.length - 1 - index];
                return ChatBubble(message: message);
              },
            ),
          ),
          
          // Input Area - Theme Requirement 4
          Container(
            decoration: BoxDecoration(
              color: isDark ? const Color(0xFF1E1E1E) : Colors.white,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.05),
                  blurRadius: 10,
                  offset: const Offset(0, -2),
                ),
              ],
            ),
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 24), // Extra bottom padding for safe area
            child: SafeArea( // Using SafeArea inside container
              top: false,
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Chips moved inside (technically above input but inside container)
                  SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    padding: const EdgeInsets.only(bottom: 12),
                    child: Row(
                      children: [
                        _buildActionChip(context, '评估风险', Icons.show_chart),
                        const SizedBox(width: 8),
                        _buildActionChip(context, '投资建议', Icons.lightbulb_outline),
                        const SizedBox(width: 8),
                        _buildActionChip(context, '资产体检', Icons.health_and_safety_outlined),
                      ],
                    ),
                  ),
                  
                  Row(
                    children: [
                      Expanded(
                        child: Container(
                          decoration: BoxDecoration(
                            color: isDark ? Colors.black12 : Colors.grey[200],
                            borderRadius: BorderRadius.circular(30),
                          ),
                          child: TextField(
                             key: const Key('chat_input'),
                             controller: _messageController,
                             decoration: InputDecoration(
                               hintText: _currentConnectionState == WebSocketConnectionState.connected 
                                   ? '输入消息...' 
                                   : '等待连接...',
                               hintStyle: TextStyle(
                                 color: isDark ? Colors.grey[600] : Colors.grey[500],
                                 fontSize: 14,
                               ),
                               border: InputBorder.none,
                               contentPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                               isDense: true,
                               enabled: _currentConnectionState == WebSocketConnectionState.connected,
                             ),
                             maxLines: 5,
                             minLines: 1,
                             style: TextStyle(
                               color: isDark ? Colors.white : Colors.black87,
                             ),
                             textInputAction: TextInputAction.send,
                             onSubmitted: (_) => _sendMessage(),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Container(
                        decoration: BoxDecoration(
                           color: const Color(0xFF00695C), // Brand Teal
                           shape: BoxShape.circle,
                        ),
                        child: IconButton(
                          key: const Key('send_button'),
                          onPressed: _currentConnectionState == WebSocketConnectionState.connected 
                              ? () => _sendMessage() 
                              : null,
                          icon: _isConnecting 
                              ? const SizedBox(
                                  width: 20,
                                  height: 20,
                                  child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                                )
                              : const Icon(
                                  Icons.arrow_upward,
                                  color: Colors.white,
                                  size: 20,
                                ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
  
  Widget _buildActionChip(BuildContext context, String label, IconData icon) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return ActionChip(
      label: Text(label),
      onPressed: () => _sendMessage(label),
      avatar: Icon(icon, size: 16, color: const Color(0xFF00695C)),
      backgroundColor: isDark ? const Color(0xFF2C2C2C) : Colors.white,
      side: BorderSide(color: const Color(0xFF00695C).withValues(alpha: 0.2)),
      labelStyle: TextStyle(
        color: isDark ? Colors.grey[300] : const Color(0xFF00695C),
        fontSize: 12,
        fontWeight: FontWeight.w500,
      ),
      padding: EdgeInsets.zero,
      visualDensity: VisualDensity.compact,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
    );
  }

  Future<void> _sendMessage([String? text]) async {
    final messageText = text ?? _messageController.text.trim();
    if (messageText.isEmpty) return;

    final webSocketService = ref.read(webSocketServiceProvider);
    if (!webSocketService.isConnected) {
      print('❌ WebSocket not connected, cannot send message');
      return;
    }

    setState(() {
      _messages.add(ChatMessage(
        text: messageText,
        isUser: true,
        timestamp: DateTime.now(),
      ));
      if (text == null) {
        _messageController.clear();
      }
    });

    try {
      final messageJson = {
        'content': messageText,
        'timestamp': DateTime.now().toIso8601String(),
      };
      
      final jsonString = json.encode(messageJson);
      await webSocketService.sendMessage(jsonString);
      
    } catch (error) {
      print('❌ Failed to send message: $error');
      if (error.toString().contains('not connected')) {
        setState(() {
          if (_messages.isNotEmpty && _messages.last.isUser) {
            _messages.removeLast();
          }
        });
      }
    }
  }
}

class ChatMessage {
  final String text;
  final bool isUser;
  final DateTime timestamp;
  final bool isStreaming;
  final List<Widget>? embeddedWidgets;

  ChatMessage({
    required this.text,
    required this.isUser,
    required this.timestamp,
    this.isStreaming = false,
    this.embeddedWidgets,
  });

  ChatMessage copyWith({
    String? text,
    bool? isUser,
    DateTime? timestamp,
    bool? isStreaming,
    List<Widget>? embeddedWidgets,
  }) {
    return ChatMessage(
      text: text ?? this.text,
      isUser: isUser ?? this.isUser,
      timestamp: timestamp ?? this.timestamp,
      isStreaming: isStreaming ?? this.isStreaming,
      embeddedWidgets: embeddedWidgets ?? this.embeddedWidgets,
    );
  }
}

class ChatBubble extends StatelessWidget {
  final ChatMessage message;

  const ChatBubble({
    super.key,
    required this.message,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8.0),
      child: Column(
        crossAxisAlignment: message.isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: message.isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (!message.isUser) ...[
                // AI Avatar
                Container(
                  width: 32,
                  height: 32,
                  decoration: const BoxDecoration(
                    gradient: LinearGradient(
                      colors: [Color(0xFF00695C), Color(0xFF00897B)],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(Icons.auto_awesome, color: Colors.white, size: 16),
                ),
                const SizedBox(width: 8),
              ],
              
              Flexible(
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    color: message.isUser
                        ? const Color(0xFF00695C) // Brand Teal for User
                        : (isDark ? const Color(0xFF2C2C2C) : Colors.white), // Theme Req 2
                    borderRadius: BorderRadius.only(
                      topLeft: const Radius.circular(16),
                      topRight: const Radius.circular(16),
                      bottomLeft: Radius.circular(message.isUser ? 16 : 4),
                      bottomRight: Radius.circular(message.isUser ? 4 : 16),
                    ),
                    boxShadow: message.isUser ? [] : [
                      BoxShadow(
                        color: Colors.black.withValues(alpha: 0.05),
                        blurRadius: 4,
                        offset: const Offset(0, 1),
                      ),
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      if (message.isUser)
                        Text(
                          message.text,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 15,
                            height: 1.4,
                          ),
                        )
                      else
                        _buildAIMessageContent(context),
                        
                      if (message.isStreaming)
                        Padding(
                          padding: const EdgeInsets.only(top: 8),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                               SizedBox(
                                width: 12,
                                height: 12,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  valueColor: AlwaysStoppedAnimation<Color>(
                                    message.isUser ? Colors.white70 : const Color(0xFF00695C),
                                  ),
                                ),
                              ),
                              const SizedBox(width: 6),
                              Text(
                                'Thinking...',
                                style: TextStyle(
                                  color: message.isUser 
                                      ? Colors.white.withValues(alpha: 0.7) 
                                      : Colors.grey[500],
                                  fontSize: 10,
                                ),
                              ),
                            ],
                          ),
                        ),
                    ],
                  ),
                ),
              ),
              
              if (message.isUser) ...[
                 const SizedBox(width: 8),
                 // User Avatar
                 Container(
                   width: 32,
                   height: 32,
                   decoration: BoxDecoration(
                     color: isDark ? Colors.grey[800] : Colors.grey[300],
                     shape: BoxShape.circle,
                   ),
                   child: Icon(
                     Icons.person,
                     color: isDark ? Colors.grey[400] : Colors.white, 
                     size: 20
                    ),
                 ),
              ],
            ],
          ),
          
          // Render embedded widgets below the message bubble
          if (message.embeddedWidgets != null && message.embeddedWidgets!.isNotEmpty)
            Padding(
               padding: EdgeInsets.only(
                 left: message.isUser ? 0 : 40, 
                 right: message.isUser ? 40 : 0, 
                 top: 8
               ),
               child: Column(
                 crossAxisAlignment: message.isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
                 children: message.embeddedWidgets!.map((widget) => 
                   Padding(
                     padding: const EdgeInsets.only(bottom: 8),
                     child: widget, 
                   ),
                 ).toList(),
               ),
            ),
        ],
      ),
    );
  }

  Widget _buildAIMessageContent(BuildContext context) {
    // Remove widget tags from display text
    String displayText = message.text.replaceAll(RegExp(r'<WIDGET:[^>]+>'), '');
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    if (displayText.trim().isEmpty && message.isStreaming) {
      return const SizedBox.shrink();
    }
    
    // Use markdown rendering for AI messages
    return MarkdownBody(
      data: displayText,
      styleSheet: MarkdownStyleSheet(
        p: TextStyle(
          color: isDark ? Colors.grey[300] : Colors.grey[800],
          fontSize: 15,
          height: 1.5,
        ),
        strong: TextStyle(
          color: isDark ? Colors.white : Colors.black,
          fontWeight: FontWeight.w600,
        ),
        em: TextStyle(
          color: isDark ? Colors.grey[400] : Colors.grey[700],
          fontStyle: FontStyle.italic,
        ),
        code: TextStyle(
          backgroundColor: isDark ? Colors.grey[800] : Colors.grey[100],
          color: const Color(0xFF00695C),
          fontFamily: 'monospace',
          fontSize: 13,
        ),
        blockquote: TextStyle(
          color: isDark ? Colors.grey[500] : Colors.grey[600],
          fontStyle: FontStyle.italic,
          decoration: TextDecoration.none, // Remove underline if any
        ),
        blockquoteDecoration: BoxDecoration(
          border: Border(left: BorderSide(color: const Color(0xFF00695C), width: 3)),
        ),
      ),
      selectable: false,
    );
  }
}