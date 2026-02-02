import 'dart:async';
import 'dart:convert';
import 'dart:math' as math;
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../widgets/connection_status_banner.dart';
import '../../../../core/services/websocket_service.dart';
import '../../../../core/providers/auth_provider.dart';
import '../../../../core/services/chat_history_service.dart';
import '../../../../core/models/chat_history.dart';
import '../../../../core/models/asset.dart';
import '../../../../core/models/user.dart';
import '../../../../shared/widgets/valuation_card.dart';
import '../../../../shared/widgets/action_card.dart';
import '../../../../shared/widgets/portfolio_chart.dart';
import '../../../../shared/widgets/asset_card.dart';
import '../../../../shared/widgets/product_card.dart';
import '../../../../shared/widgets/action_plan_card.dart';
import '../../../../core/models/action_plan.dart';
import '../../services/card_action_handler.dart';

// UTF-8 safe logging utility
String _safeLogString(String text, {int maxLength = 100}) {
  try {
    final truncated = text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    // Validate UTF-8 encoding
    truncated.codeUnits;
    return truncated;
  } catch (e) {
    return 'Text (${text.length} chars) - contains invalid UTF-8 characters';
  }
}

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
  String? _connectionErrorMessage;
  
  // Grace period for error display to prevent flashing during page loads/tab switches


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
            ValuationCard(
              propertyName: data['location'] ?? '房产',
              estimatedValue: (data['price'] as num?)?.toDouble() ?? 0,
              pricePerSqm: data['area'] != null 
                  ? '${((data['price'] as num?) ?? 0) ~/ (data['area'] as num? ?? 1) / 10000}万/平'
                  : '未知',
              onConfirm: () async {
                await ref.read(cardActionHandlerProvider).handleAction(
                  context,
                  actionType: 'confirm_valuation',
                  data: data,
                  onSendUserMessage: _sendMessage,
                  onUpdateUi: () => _loadChatHistory(),
                );
              },
              onEdit: () async {
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
            AssetCard(
              name: data['name'] as String? ?? '未知资产',
              value: (data['value'] as num?)?.toDouble() ?? 0,
              assetType: data['type'] as String? ?? 'unknown',
              riskLevel: data['risk_level'] as String?,
              tags: (data['tags'] as List<dynamic>?)?.cast<String>() ?? [],
              privacyMode: data['privacy_mode'] as bool? ?? false,
              onTap: () async {
                await ref.read(cardActionHandlerProvider).handleAction(
                  context,
                  actionType: 'send_message',
                  data: {'message': '告诉我更多关于${data['name'] ?? '这个资产'}的信息'},
                  onSendUserMessage: _sendMessage,
                );
              },
              onEdit: () async {
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
      print('⚠️ WebSocket connection already in progress, skipping...');
      return;
    }
    
    if (webSocketService.isConnected) {
      print('⚠️ WebSocket already connected, skipping...');
      return;
    }
    
    print('🔌 Connecting WebSocket for user $userId with token ${token.substring(0, 20)}...');
    
    setState(() {
      _isConnecting = true;
    });

    try {
      // Disconnect existing connection first if any
      if (webSocketService.connectionState != WebSocketConnectionState.disconnected) {
        print('🔄 Disconnecting existing WebSocket connection...');
        await webSocketService.disconnect();
        await Future.delayed(const Duration(milliseconds: 500));
      }
      
      // Listen to connection state changes
      _connectionSubscription?.cancel();
      _connectionSubscription = webSocketService.connectionStateStream.listen(
        (state) {
          print('🔗 WebSocket state changed to: $state');
          
          // Update state for UI
          if (mounted) {
            setState(() {
              _currentConnectionState = state;
              _isConnecting = state == WebSocketConnectionState.connecting || 
                              state == WebSocketConnectionState.reconnecting;
              // Clear error message on non-error states
              if (state != WebSocketConnectionState.error) {
                _connectionErrorMessage = null;
              }
            });
          }
          
          // Show snackbar notifications only for errors/issues (success is silent)
          // Removed manual snackbar - now handled by ConnectionStatusBanner
          // if (state == WebSocketConnectionState.error) {
          //   _showConnectionStatus('连接失败，正在重试...', isError: true);
          // } else if (state == WebSocketConnectionState.reconnecting) {
          //   _showConnectionStatus('正在重新连接...', isError: false);
          // }
        },
      );
      
      // Listen to incoming messages
      _messageSubscription?.cancel();
      _messageSubscription = webSocketService.messageStream.listen(
        (message) {
          print('📨 Received WebSocket message: ${_safeLogString(message)}');
          _handleIncomingMessage(message);
        },
        onError: (error) {
          print('❌ WebSocket message error: $error');
          // Update error message state
          if (mounted) {
            setState(() {
              _connectionErrorMessage = error.toString();
            });
          }
        },
      );
      
      print('🚀 Attempting WebSocket connection...');
      await webSocketService.connect(userId, token);
      print('✅ WebSocket connection initiated');
      
    } catch (error) {
      print('❌ WebSocket connection failed: $error');
      // Error is handled by connection state stream
    } finally {
      setState(() {
        _isConnecting = false;
      });
    }
  }

  void _scrollToBottom() {
    // Note: With reverse: true, we don't need manual scrolling
    // The list naturally starts at the bottom (latest messages)
    // This method is kept for potential future use (e.g., "scroll to bottom" button)
    if (_scrollController.hasClients) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _scrollController.animateTo(
          0, // In reverse mode, 0 is the bottom
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      });
    }
  }

  void _handleIncomingMessage(String message) {
    try {
      // Validate UTF-8 encoding first
      try {
        message.codeUnits; // This will throw if there are invalid UTF-8 sequences
      } catch (e) {
        print('⚠️ Invalid UTF-8 in message, attempting to clean: $e');
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
          // No need to scroll - reverse: true keeps latest at bottom
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
          // No need to scroll - reverse: true keeps latest at bottom
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
          // No need to scroll - reverse: true keeps latest at bottom
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
          // No need to scroll - reverse: true keeps latest at bottom
          break;
          
        case 'error':
          // Handle error messages
          print('❌ AI Error: $content');
          // _showConnectionStatus('AI错误: $content', isError: true);
          break;
          
        default:
          // Fallback for unknown message types
          print('⚠️ Unknown message type: $messageType');
          setState(() {
            _messages.add(ChatMessage(
              text: content,
              isUser: false,
              timestamp: DateTime.now(),
              isStreaming: false,
            ));
          });
          // No need to scroll - reverse: true keeps latest at bottom
      }
      
    } catch (e) {
      // If JSON parsing fails, treat as plain text (fallback)
      print('⚠️ Failed to parse message as JSON: $e');
      print('📄 Raw message: ${_safeLogString(message, maxLength: 200)}');
      
      // Check if this is a UTF-8 encoding error
      if (e.toString().contains('UTF-8') || e.toString().contains('REPLACEMENT CHARACTER')) {
        print('🔧 UTF-8 encoding issue detected, showing user-friendly error');
        // _showConnectionStatus('消息包含特殊字符，已自动处理', isError: false);
        
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
        // No need to scroll - reverse: true keeps latest at bottom
      }
    }
  }

  List<Widget>? _parseEmbeddedWidgets(String text) {
    print('🔍 DEBUG: Starting widget parsing');
    print('🔍 DEBUG: Message length: ${text.length}');
    print('🔍 DEBUG: Message preview: ${text.substring(0, math.min(200, text.length))}...');
    
    // Check for any widget tags
    if (text.contains('<WIDGET:')) {
      print('✅ DEBUG: Found WIDGET tags in message');
      
      // Count different widget types
      int valuationCount = '<WIDGET:VALUATION_CARD'.allMatches(text).length;
      int productCount = '<WIDGET:PRODUCT_CARD'.allMatches(text).length;
      int actionCount = '<WIDGET:ACTION_CARD'.allMatches(text).length;
      int portfolioCount = '<WIDGET:PORTFOLIO_CHART'.allMatches(text).length;

      int assetCount = '<WIDGET:ASSET_CARD'.allMatches(text).length;
      int actionPlanCount = '<WIDGET:ACTION_PLAN_CARD'.allMatches(text).length;
      
      print('🔍 DEBUG: Widget counts:');
      print('  VALUATION_CARD: $valuationCount');
      print('  PRODUCT_CARD: $productCount');
      print('  ACTION_CARD: $actionCount');
      print('  ACTION_PLAN_CARD: $actionPlanCount');
      print('  PORTFOLIO_CHART: $portfolioCount');
      print('  ASSET_CARD: $assetCount');
    } else {
      print('❌ DEBUG: No WIDGET tags found in message');
      return null;
    }
    
    final widgets = <Widget>[];
    
    // Parse VALUATION_CARD with JSON data
    if (text.contains('<WIDGET:VALUATION_CARD')) {
      print('🔍 DEBUG: Processing VALUATION_CARD');
      
      // Use distinct pattern to find all occurrences
      final matches = RegExp(r'<WIDGET:VALUATION_CARD data="([^"]*)"').allMatches(text);
      print('🔍 DEBUG: Found ${matches.length} VALUATION_CARD matches');
      
      for (final match in matches) {
        try {
          var jsonStr = match.group(1) ?? '{}';
          
          // ROBUSTNESS FIX: Handle LLM hallucinated JSON (single quotes, etc.)
          // 1. Unescape HTML entities
          jsonStr = jsonStr.replaceAll('&quot;', '"');
          
          // 2. If it looks like it uses single quotes, try to fix it
          if (!jsonStr.contains('"') && jsonStr.contains("'")) {
             print('⚠️ DEBUG: Detected single-quoted JSON, attempting fix');
             jsonStr = jsonStr.replaceAll("'", '"');
             // Note: This is a simple heuristic. For complex nested strings it might fail,
             // but it catches the common {key: 'value'} case.
             
             // 3. Handle unquoted keys (simple regex for basic keys)
             // Matches {key: or , key: and wraps key in quotes
             jsonStr = jsonStr.replaceAllMapped(
               RegExp(r'([{,]\s*)([a-zA-Z0-9_]+)(\s*:)'), 
               (m) => '${m[1]}"${m[2]}"${m[3]}'
             );
          }
          
          print('🔍 DEBUG: VALUATION_CARD JSON: ${jsonStr.substring(0, math.min(150, jsonStr.length))}...');
          final data = json.decode(jsonStr) as Map<String, dynamic>;
          
          final estimatedValue = (data['price'] as num?)?.toDouble() ?? 0;
          
          // heuristic to filter out broken/duplicate tags with 0 value
          if (estimatedValue <= 0 && data['id'] == null) {
             print('⚠️ DEBUG: Skipping invalid VALUATION_CARD (0 value, no ID)');
             continue;
          }

          widgets.add(
            ValuationCard(
              propertyName: data['location'] as String? ?? '房产',
              estimatedValue: estimatedValue,
              pricePerSqm: data['area'] != null && data['area'] > 0
                  ? '${((data['price_per_sqm'] as num?) ?? estimatedValue / (data['area'] as num)).toStringAsFixed(0)}元/平'
                  : '未知',
              status: data['status'] as String? ?? 'active',
              onConfirm: () async {
                await ref.read(cardActionHandlerProvider).handleAction(
                  context,
                  actionType: 'confirm_valuation',
                  data: data,
                  onSendUserMessage: _sendMessage,
                  onUpdateUi: () => _loadChatHistory(),
                );
              },
              onEdit: () async {
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
          print('✅ DEBUG: Successfully created VALUATION_CARD widget');
        } catch (e) {
          print('❌ DEBUG: Error parsing VALUATION_CARD data: $e');
          print('❌ DEBUG: JSON string: ${match.group(1)}');
          // Only add fallback if we really want to show broken widgets.
          // Better to skip broken ones if we expect a valid one later?
          // Let's show it but visually indicate error only in debug logs?
          // No, user sees "Parsing failed" card.
          // If we have multiple, maybe one is good.
          
          // Strategy: Try to parse. If fail, log it. 
          // If after checking ALL matches we found NO valid widgets, maybe add a fallback?
          // Or just add the error card so user knows something happened.
          widgets.add(
             ValuationCard(
              propertyName: '数据解析异常',
              estimatedValue: 0,
              pricePerSqm: '格式错误',
              onConfirm: () async => _sendMessage('确认估值'),
              onEdit: () async => _sendMessage('编辑估值'),
            ),
          );
        }
      } 
      
      // Check for simple tags ONLY if no data tags were found
      if (matches.isEmpty && text.contains('<WIDGET:VALUATION_CARD>')) {
        print('🔍 DEBUG: Found simple VALUATION_CARD tag');
        // Simple tag without data (legacy support)
        widgets.add(
          ValuationCard(
            propertyName: '房产估值',
            estimatedValue: 0,
            pricePerSqm: '待估价',
            onConfirm: () async {
              await ref.read(cardActionHandlerProvider).handleAction(
                context,
                actionType: 'confirm_valuation',
                data: {'price': 0},
                onSendUserMessage: _sendMessage,
                onUpdateUi: () => _loadChatHistory(),
              );
            },
            onEdit: () async {
              await ref.read(cardActionHandlerProvider).handleAction(
                context,
                actionType: 'edit_valuation',
                data: {'price': 0},
                onSendUserMessage: _sendMessage,
                onUpdateUi: () => _loadChatHistory(),
              );
            },
          ),
        );
      }
    }
    
    // Parse ACTION_CARD with JSON data - handle multiple cards
    if (text.contains('<WIDGET:ACTION_CARD')) {
      print('🔍 DEBUG: Processing ACTION_CARD');
      final matches = RegExp(r'<WIDGET:ACTION_CARD data="([^"]*)"').allMatches(text);
      print('🔍 DEBUG: Found ${matches.length} ACTION_CARD matches');
      
      for (final match in matches) {
        try {
          final jsonStr = match.group(1)
            ?.replaceAll('&quot;', '"')  // HTML entity decoding
            ?? '{}';
          print('🔍 DEBUG: ACTION_CARD JSON: ${jsonStr.substring(0, math.min(100, jsonStr.length))}...');
          
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
          print('✅ DEBUG: Successfully created ACTION_CARD widget: ${data['title']}');
        } catch (e) {
          print('❌ DEBUG: Error parsing ACTION_CARD data: $e');
          print('❌ DEBUG: Raw JSON string: ${match.group(1)}');
          // Fallback to simple action card
          widgets.add(
            ActionCard(
              type: ActionCardType.warning,
              title: '操作建议',
              description: '为您推荐的操作',
              onTap: () {
                _sendMessage('告诉我更多关于这个建议的信息');
              },
            ),
          );
        }
      }
      
      if (matches.isEmpty && text.contains('<WIDGET:ACTION_CARD>')) {
        print('🔍 DEBUG: Found simple ACTION_CARD tag');
        // Simple tag without data (legacy support)
        widgets.add(
          ActionCard(
            type: ActionCardType.warning,
            title: '流动性风险警告',
            description: '您的现金储备相对较低，建议增加应急资金至6个月支出',
            onTap: () {
              _sendMessage('告诉我更多关于流动性风险的信息');
            },
          ),
        );
      }
      }

    
    // Parse ACTION_PLAN_CARD with JSON data
    if (text.contains('<WIDGET:ACTION_PLAN_CARD')) {
      print('🔍 DEBUG: Processing ACTION_PLAN_CARD');
      final matches = RegExp(r'<WIDGET:ACTION_PLAN_CARD data="([^"]*)"').allMatches(text);
      print('🔍 DEBUG: Found ${matches.length} ACTION_PLAN_CARD matches');
      
      for (final match in matches) {
        try {
          final jsonStr = match.group(1)
            ?.replaceAll('&quot;', '"')  // HTML entity decoding
            ?? '{}';
          print('🔍 DEBUG: ACTION_PLAN_CARD JSON: ${jsonStr.substring(0, math.min(100, jsonStr.length))}...');
          
          final data = json.decode(jsonStr) as Map<String, dynamic>;
          final plan = ActionPlan.fromJson(data);
                    widgets.add(
              ActionPlanCard(
                plan: plan,
              ),
            );
          print('✅ DEBUG: Successfully created ACTION_PLAN_CARD widget: ${plan.title}');
        } catch (e) {
          print('❌ DEBUG: Error parsing ACTION_PLAN_CARD data: $e');
          print('❌ DEBUG: Raw JSON string: ${match.group(1)}');
        }
      }
    }
    
    // Parse PORTFOLIO_CHART with JSON data
    if (text.contains('<WIDGET:PORTFOLIO_CHART')) {
      print('🔍 DEBUG: Processing PORTFOLIO_CHART');
      final match = RegExp(r'<WIDGET:PORTFOLIO_CHART data="([^"]*)"').firstMatch(text);
      if (match != null) {
        try {
          final jsonStr = match.group(1)
            ?.replaceAll('&quot;', '"')  // HTML entity decoding
            ?? '{}';
          print('🔍 DEBUG: PORTFOLIO_CHART JSON: ${jsonStr.substring(0, math.min(100, jsonStr.length))}...');
          final data = json.decode(jsonStr) as Map<String, dynamic>;
          
          final assets = (data['assets'] as List<dynamic>?)?.map((assetData) {
            return UserAsset(
              id: assetData['id'] ?? 0,
              userId: assetData['userId'] ?? 0,
              assetType: _parseAssetType(assetData['type'] as String?),
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
          print('✅ DEBUG: Successfully created PORTFOLIO_CHART widget with ${assets.length} assets');
        } catch (e) {
          print('❌ DEBUG: Error parsing PORTFOLIO_CHART data: $e');
          print('❌ DEBUG: Raw JSON string: ${match.group(1)}');
          // Fallback to simple portfolio chart
          widgets.add(
            PortfolioChart(
              assets: [
                UserAsset(
                  id: 1,
                  userId: 1,
                  assetType: AssetType.realEstate,
                  name: '房产',
                  value: 4500000,
                  isConfirmed: true,
                  createdAt: DateTime.now(),
                  updatedAt: DateTime.now(),
                ),
                UserAsset(
                  id: 2,
                  userId: 1,
                  assetType: AssetType.cash,
                  name: '现金',
                  value: 800000,
                  isConfirmed: true,
                  createdAt: DateTime.now(),
                  updatedAt: DateTime.now(),
                ),
              ],
              title: '资产配置分析',
              onTap: () {
                _sendMessage('请详细解释我的资产配置');
              },
            ),
          );
        }
      } else if (text.contains('<WIDGET:PORTFOLIO_CHART>')) {
        print('🔍 DEBUG: Found simple PORTFOLIO_CHART tag');
        // Simple tag without data (legacy support)
        widgets.add(
          PortfolioChart(
            assets: [
              UserAsset(
                id: 1,
                userId: 1,
                assetType: AssetType.realEstate,
                name: '房产',
                value: 4500000,
                isConfirmed: true,
                createdAt: DateTime.now(),
                updatedAt: DateTime.now(),
              ),
              UserAsset(
                id: 2,
                userId: 1,
                assetType: AssetType.cash,
                name: '现金',
                value: 800000,
                isConfirmed: true,
                createdAt: DateTime.now(),
                updatedAt: DateTime.now(),
              ),
              UserAsset(
                id: 3,
                userId: 1,
                assetType: AssetType.investment,
                name: '投资',
                value: 500000,
                isConfirmed: true,
                createdAt: DateTime.now(),
                updatedAt: DateTime.now(),
              ),
              UserAsset(
                id: 4,
                userId: 1,
                assetType: AssetType.insurance,
                name: '保险',
                value: 200000,
                isConfirmed: true,
                createdAt: DateTime.now(),
                updatedAt: DateTime.now(),
              ),
            ],
            title: '您的资产配置分析',
            onTap: () {
              _sendMessage('请详细解释我的资产配置');
            },
          ),
        );
      }
    }
    
    // Parse ASSET_CARD with JSON data
    if (text.contains('<WIDGET:ASSET_CARD')) {
      print('🔍 DEBUG: Processing ASSET_CARD');
      final match = RegExp(r'<WIDGET:ASSET_CARD data="([^"]*)"').firstMatch(text);
      if (match != null) {
        try {
          final jsonStr = match.group(1)
            ?.replaceAll('&quot;', '"')  // HTML entity decoding
            ?? '{}';
          print('🔍 DEBUG: ASSET_CARD JSON: ${jsonStr.substring(0, math.min(100, jsonStr.length))}...');
          final data = json.decode(jsonStr) as Map<String, dynamic>;
          
          widgets.add(
            AssetCard(
              name: data['name'] as String? ?? '未知资产',
              value: (data['value'] as num?)?.toDouble() ?? 0,
              assetType: data['type'] as String? ?? 'unknown',
              riskLevel: data['risk_level'] as String?,
              tags: (data['tags'] as List<dynamic>?)?.cast<String>() ?? [],
              privacyMode: data['privacy_mode'] as bool? ?? false,
              status: data['status'] as String? ?? 'active',
              onTap: () async {
                await ref.read(cardActionHandlerProvider).handleAction(
                  context,
                  actionType: 'send_message',
                  data: {'message': '告诉我更多关于${data['name'] ?? '这个资产'}的信息'},
                  onSendUserMessage: _sendMessage,
                );
              },
              onEdit: () async {
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
          print('✅ DEBUG: Successfully created ASSET_CARD widget: ${data['name']}');
        } catch (e) {
          print('❌ DEBUG: Error parsing ASSET_CARD data: $e');
          print('❌ DEBUG: Raw JSON string: ${match.group(1)}');
          // Fallback to simple asset card
          widgets.add(
            AssetCard(
              name: '新增资产',
              value: 0,
              assetType: 'unknown',
              onTap: () async {
                await ref.read(cardActionHandlerProvider).handleAction(
                  context,
                  actionType: 'send_message',
                  data: {'message': '告诉我更多关于这个资产的信息'},
                  onSendUserMessage: _sendMessage,
                );
              },
            ),
          );
        }
      } else if (text.contains('<WIDGET:ASSET_CARD>')) {
        print('🔍 DEBUG: Found simple ASSET_CARD tag');
        // Simple tag without data
        widgets.add(
          AssetCard(
            name: '新增资产',
            value: 0,
            assetType: 'unknown',
            onTap: () async {
              await ref.read(cardActionHandlerProvider).handleAction(
                context,
                actionType: 'send_message',
                data: {'message': '告诉我更多关于这个资产的信息'},
                onSendUserMessage: _sendMessage,
              );
            },
          ),
        );
      }
    }

    // Parse PRODUCT_CARD with JSON data - handle multiple cards
    if (text.contains('<WIDGET:PRODUCT_CARD')) {
      print('🔍 DEBUG: Processing PRODUCT_CARD');
      
      // Try multiple regex patterns to handle different escaping levels
      final patterns = [
        RegExp(r'<WIDGET:PRODUCT_CARD data="([^"]*)"'),           // Normal escaping
        RegExp(r'<WIDGET:PRODUCT_CARD data=\\"([^\\"]*)\\""'),    // WebSocket escaping
        RegExp(r'<WIDGET:PRODUCT_CARD data=\\\"([^\\\"]*)\\\""'), // Double escaping
      ];
      
      int totalMatches = 0;
      for (int patternIndex = 0; patternIndex < patterns.length; patternIndex++) {
        final matches = patterns[patternIndex].allMatches(text);
        if (matches.isNotEmpty) {
          print('🔍 DEBUG: Pattern ${patternIndex + 1} found ${matches.length} PRODUCT_CARD matches');
          totalMatches += matches.length;
          
          for (final match in matches) {
            try {
              var jsonStr = match.group(1) ?? '{}';
              
              // Apply appropriate decoding based on pattern
              if (patternIndex == 0) {
                jsonStr = jsonStr
                  .replaceAll('&quot;', '"')  // HTML entity decoding
                  .replaceAll('\\"', '"');    // JSON escape decoding
              } else if (patternIndex == 1) {
                jsonStr = jsonStr
                  .replaceAll('\\&quot;', '"')  // WebSocket + HTML entity
                  .replaceAll('&quot;', '"')    // Remaining HTML entities
                  .replaceAll('\\"', '"');      // JSON escapes
              } else {
                jsonStr = jsonStr
                  .replaceAll('\\\\&quot;', '"')  // Double escaped HTML entities
                  .replaceAll('\\&quot;', '"')    // Single escaped HTML entities
                  .replaceAll('&quot;', '"')      // HTML entities
                  .replaceAll('\\"', '"');        // JSON escapes
              }
              
              print('🔍 DEBUG: PRODUCT_CARD JSON: ${jsonStr.substring(0, math.min(150, jsonStr.length))}...');
              
              final data = json.decode(jsonStr) as Map<String, dynamic>;
              
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
                    _sendMessage('我对${data['name'] ?? '这个产品'}感兴趣，请提供更多信息');
                  },
                  onContact: () {
                    _sendMessage('我想联系${data['provider'] ?? '服务商'}咨询${data['name'] ?? '这个产品'}');
                  },
                ),
              );
              print('✅ DEBUG: Successfully created PRODUCT_CARD widget: ${data['name']}');
            } catch (e) {
              print('❌ DEBUG: Error parsing PRODUCT_CARD data: $e');
              print('❌ DEBUG: Raw JSON string: ${match.group(1)}');
              // Fallback to simple product card
              widgets.add(
                ProductCard(
                  name: '推荐产品',
                  provider: '服务商',
                  category: 'general',
                  description: '为您推荐的产品',
                  onTap: () {
                    _sendMessage('我对这个产品感兴趣');
                  },
                ),
              );
            }
          }
          break; // Found matches with this pattern, no need to try others
        }
      }
      
      if (totalMatches == 0 && text.contains('<WIDGET:PRODUCT_CARD>')) {
        print('🔍 DEBUG: Found simple PRODUCT_CARD tag');
        // Simple tag without data
        widgets.add(
          ProductCard(
            name: '推荐产品',
            provider: '服务商',
            category: 'general',
            description: '为您推荐的产品',
            onTap: () {
              _sendMessage('我对这个产品感兴趣');
            },
          ),
        );
      }
    }
    
    print('🎯 DEBUG: Parsing completed');
    print('🎯 DEBUG: Generated ${widgets.length} widgets');
    for (int i = 0; i < widgets.length; i++) {
      print('  ${i + 1}. ${widgets[i].runtimeType}');
    }
    
    return widgets.isNotEmpty ? widgets : null;
  }



  @override
  Widget build(BuildContext context) {
    super.build(context); // Required for AutomaticKeepAliveClientMixin
    
    final webSocketService = ref.watch(webSocketServiceProvider);
    
    // Use the state variable that gets updated by the connection listener
    final connectionState = _currentConnectionState;
    
    // Check for initial connection when page loads
    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final authState = ref.read(authStateProvider);
      final token = await ref.read(authTokenProvider.future);
      
      print('🔍 Chat page loaded - Auth check:');
      print('   Auth state: ${authState.value?.phone ?? 'null'}');
      print('   User ID: ${authState.value?.id ?? 'null'}');
      print('   Token: ${token?.substring(0, 20) ?? 'null'}...');
      print('   WebSocket state: $connectionState');
      
      // Only connect if not already connected or connecting
      if (authState.value != null && 
          token != null && 
          (connectionState == WebSocketConnectionState.disconnected || 
           connectionState == WebSocketConnectionState.error)) {
        print('🔌 Initial WebSocket connection needed (State: $connectionState)');
        print('🆔 Using User ID: ${authState.value!.id}');
        _connectWebSocket(authState.value!.id, token);
      } else {
        print('⏭️ Skipping connection - already connected or connecting');
      }
    });
    
    // Watch for auth state changes and reconnect WebSocket when needed
    ref.listen<AsyncValue<User?>>(authStateProvider, (previous, next) async {
      final token = await ref.read(authTokenProvider.future);
      final currentState = webSocketService.connectionState;
      
      print('👤 Auth state changed:');
      print('   Previous: ${previous?.value?.phone ?? 'null'} (ID: ${previous?.value?.id ?? 'null'})');
      print('   Next: ${next.value?.phone ?? 'null'} (ID: ${next.value?.id ?? 'null'})');
      print('   Token: ${token?.substring(0, 20) ?? 'null'}...');
      print('   Current WebSocket state: $currentState');
      
      if (next.value != null && token != null) {
        // User is logged in with a valid token - connect WebSocket if disconnected or error
        if (currentState == WebSocketConnectionState.disconnected || 
            currentState == WebSocketConnectionState.error) {
          print('✅ User logged in, connecting WebSocket... (State: $currentState)');
          print('🆔 Using User ID: ${next.value!.id}');
          WidgetsBinding.instance.addPostFrameCallback((_) {
            _connectWebSocket(next.value!.id, token);
          });
        } else {
          print('⏭️ User logged in but WebSocket already connected/connecting');
        }
      } else {
        // User is not logged in - disconnect WebSocket
        print('❌ User not logged in, disconnecting WebSocket...');
        WidgetsBinding.instance.addPostFrameCallback((_) {
          webSocketService.disconnect();
        });
      }
    });
    
    // Also watch for token changes specifically
    ref.listen(authTokenProvider, (previous, next) {
      final authState = ref.read(authStateProvider);
      final currentState = webSocketService.connectionState;
      
      print('🔑 Token changed:');
      
      // Handle AsyncValue properly
      final previousToken = previous?.when(
        data: (token) => token,
        loading: () => null,
        error: (_, __) => null,
      );
      
      final nextToken = next?.when(
        data: (token) => token,
        loading: () => null,
        error: (_, __) => null,
      );
      
      print('   Previous: ${previousToken?.substring(0, 20) ?? 'null'}...');
      print('   Next: ${nextToken?.substring(0, 20) ?? 'null'}...');
      print('   Auth state: ${authState.value?.phone ?? 'null'}');
      print('   Current WebSocket state: $currentState');
      
      // Only reconnect if token actually changed and we have a valid user
      if (authState.value != null && 
          nextToken != null && 
          previousToken != nextToken &&
          previousToken != null) {  // Only reconnect if there was a previous token (token refresh scenario)
        print('🔄 Token changed, reconnecting WebSocket...');
        WidgetsBinding.instance.addPostFrameCallback((_) {
          _connectWebSocket(authState.value!.id, nextToken);
        });
      } else {
        print('⏭️ Token change ignored - no reconnection needed');
      }
    });
    
    // Determine which messages to show (streamed or full)
    // Note: handling both efficiently
    

    
    return Scaffold(
      backgroundColor: Theme.of(context).colorScheme.background,
      appBar: AppBar(
        title: Text(
          'AI 资产配置顾问',
          style: TextStyle(
            color: Theme.of(context).colorScheme.onSurface,
            fontSize: 18,
            fontWeight: FontWeight.w600,
          ),
        ),
        centerTitle: true,
        backgroundColor: Theme.of(context).colorScheme.surface,
        elevation: 0.5,
        iconTheme: IconThemeData(color: Theme.of(context).colorScheme.onSurface),
      ),
      body: Column(
        children: [
          // Connection Status Banner
          ConnectionStatusBanner(
            connectionState: _currentConnectionState,
            errorMessage: _connectionErrorMessage,
          ),
          
          Expanded(
            child: ListView.builder(
              reverse: true, // Show latest messages at bottom naturally
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                // Invert index to show newest at bottom when reversed
                final message = _messages[_messages.length - 1 - index];
                return ChatBubble(message: message);
              },
            ),
          ),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surface,
              border: Border(
                top: BorderSide(
                  color: Theme.of(context).dividerColor,
                ),
              ),
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    key: const Key('chat_input'),
                    controller: _messageController,
                    decoration: InputDecoration(
                      hintText: _currentConnectionState == WebSocketConnectionState.connected 
                          ? '输入您的资产信息...' 
                          : '等待连接...',
                      border: const OutlineInputBorder(),
                      enabled: _currentConnectionState == WebSocketConnectionState.connected,
                    ),
                    maxLines: null,
                    onSubmitted: (_) => _sendMessage(),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  key: const Key('send_button'),
                  onPressed: _currentConnectionState == WebSocketConnectionState.connected ? _sendMessage : null,
                  icon: _isConnecting 
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(strokeWidth: 2),
                        )
                      : const Icon(Icons.send),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }


    


  Future<void> _sendMessage([String? text]) async {
    final messageText = text ?? _messageController.text.trim();
    if (messageText.isEmpty) return;

    final webSocketService = ref.read(webSocketServiceProvider);
    if (!webSocketService.isConnected) {
      print('❌ WebSocket not connected, cannot send message');
      // Show error in banner logic (by setting state if needed, though usually automatic)
      return;
    }

    print('📤 Preparing to send message: "${_safeLogString(messageText, maxLength: 50)}"');

    // Add user message to chat
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

    print('✅ User message added to chat UI');

    // No need to scroll - reverse: true keeps latest at bottom

    // Send message via WebSocket with UTF-8 validation
    try {
      final messageJson = {
        'content': messageText,
        'timestamp': DateTime.now().toIso8601String(),
      };
      
      final jsonString = json.encode(messageJson);
      print('📡 Sending WebSocket message:$jsonString');
      
      // Validate UTF-8 encoding before sending
      try {
        jsonString.codeUnits; // This will throw if there are invalid UTF-8 sequences
      } catch (e) {
        print('⚠️ Invalid UTF-8 in outgoing message, cleaning: $e');
        // This shouldn't happen with user input, but just in case
        throw Exception('消息包含无效字符，请重新输入');
      }
      
      await webSocketService.sendMessage(jsonString);
      print('✅ Message sent successfully via WebSocket');
      
    } catch (error) {
      print('❌ Failed to send message: $error');
      // Error will be logged, and connection state might update if it's a network issue
      
      // 不要删除用户消息，让用户知道消息已发送但可能失败
      // 只在确认发送失败时才删除
      if (error.toString().contains('not connected')) {
        setState(() {
          if (_messages.isNotEmpty && _messages.last.isUser) {
            _messages.removeLast();
          }
        });
      }
    }
  }


  void _showEditValuationDialog({required double currentPrice, double? currentArea}) {
    final priceController = TextEditingController(text: currentPrice.toStringAsFixed(0));
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('调整房产估值'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text('请输入修正后的总价（万元）'),
            const SizedBox(height: 8),
            TextField(
              controller: priceController,
              keyboardType: TextInputType.number,
              decoration: const InputDecoration(
                suffixText: '万元',
                border: OutlineInputBorder(),
                hintText: '例如: 500',
              ),
              autofocus: true,
            ),
            if (currentArea != null) ...[
              const SizedBox(height: 16),
              Text(
                '注：当前面积 ${currentArea.toStringAsFixed(1)}平米',
                style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.grey),
              ),
            ],
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('取消'),
          ),
          ElevatedButton(
            onPressed: () {
              final newPrice = double.tryParse(priceController.text);
              if (newPrice != null && newPrice > 0) {
                Navigator.pop(context);
                _sendMessage('修正估值为: ${newPrice}万');
              } else {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('请输入有效的金额')),
                );
              }
            },
            child: const Text('确定'),
          ),
        ],
      ),
    );
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
    return Align(
      alignment: message.isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Column(
        crossAxisAlignment: message.isUser 
            ? CrossAxisAlignment.end 
            : CrossAxisAlignment.start,
        children: [
          Container(
            margin: const EdgeInsets.symmetric(vertical: 4),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            constraints: BoxConstraints(
              maxWidth: MediaQuery.of(context).size.width * 0.8,
            ),
            decoration: BoxDecoration(
              color: message.isUser
                  ? Theme.of(context).colorScheme.primary
                  : Theme.of(context).colorScheme.surfaceVariant,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (message.isUser)
                  Text(
                    message.text,
                    style: TextStyle(
                      color: Theme.of(context).colorScheme.onPrimary,
                    ),
                  )
                else
                  _buildAIMessageContent(context),
                if (message.isStreaming)
                  Padding(
                    padding: const EdgeInsets.only(top: 8),
                    child: SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation<Color>(
                          message.isUser
                              ? Theme.of(context).colorScheme.onPrimary
                              : Theme.of(context).colorScheme.primary,
                        ),
                      ),
                    ),
                  ),
              ],
            ),
          ),
          // Render embedded widgets below the message bubble
          if (message.embeddedWidgets != null && message.embeddedWidgets!.isNotEmpty)
            ...message.embeddedWidgets!.map((widget) => 
              Container(
                margin: const EdgeInsets.only(top: 8),
                constraints: BoxConstraints(
                  maxWidth: MediaQuery.of(context).size.width * 0.9,
                ),
                child: widget,
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildAIMessageContent(BuildContext context) {
    // Remove widget tags from display text
    String displayText = message.text.replaceAll(RegExp(r'<WIDGET:[^>]+>'), '');
    
    if (displayText.trim().isEmpty && message.isStreaming) {
      return const SizedBox.shrink();
    }
    
    // Use markdown rendering for AI messages
    return MarkdownBody(
      data: displayText,
      styleSheet: MarkdownStyleSheet(
        p: TextStyle(
          color: Theme.of(context).colorScheme.onSurfaceVariant,
          fontSize: 16,
        ),
        strong: TextStyle(
          color: Theme.of(context).colorScheme.onSurfaceVariant,
          fontWeight: FontWeight.bold,
        ),
        em: TextStyle(
          color: Theme.of(context).colorScheme.onSurfaceVariant,
          fontStyle: FontStyle.italic,
        ),
        code: TextStyle(
          backgroundColor: Theme.of(context).colorScheme.surface,
          color: Theme.of(context).colorScheme.primary,
          fontFamily: 'monospace',
        ),
        blockquote: TextStyle(
          color: Theme.of(context).colorScheme.onSurfaceVariant.withOpacity(0.8),
          fontStyle: FontStyle.italic,
        ),
      ),
      selectable: false, // Disabled to prevent scroll gesture conflicts
    );
  }
}