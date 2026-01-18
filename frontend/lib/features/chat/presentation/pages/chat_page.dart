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
import '../../../../shared/widgets/valuation_card.dart';
import '../../../../shared/widgets/action_card.dart';
import '../../../../shared/widgets/portfolio_chart.dart';

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
  
  // Grace period for error display to prevent flashing during page loads/tab switches
  Timer? _connectionTimer;
  bool _showConnectionError = false;

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
      
      // Start grace period timer if initially disconnected
      if (webSocketService.connectionState == WebSocketConnectionState.disconnected ||
          webSocketService.connectionState == WebSocketConnectionState.error) {
        _startConnectionErrorTimer();
      }
      
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
              onConfirm: () {
                _sendMessage('确认估值 ${(data['price'] as num?)?.toDouble() ?? 0}');
              },
              onEdit: () {
                _sendMessage('我想调整估值');
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
    _connectionTimer?.cancel(); // Cancel grace period timer
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
          
          // Handle grace period for error display
          if (state == WebSocketConnectionState.connected || 
              state == WebSocketConnectionState.connecting) {
            // Immediately hide error banner and cancel timer
            _connectionTimer?.cancel();
            setState(() {
              _currentConnectionState = state;
              _showConnectionError = false;
              _isConnecting = state == WebSocketConnectionState.connecting;
            });
          } else if (state == WebSocketConnectionState.disconnected || 
                     state == WebSocketConnectionState.error) {
            // Update state but don't show error immediately - start grace period
            setState(() {
              _currentConnectionState = state;
              _isConnecting = false;
            });
            _startConnectionErrorTimer();
          } else if (state == WebSocketConnectionState.reconnecting) {
            // Reconnecting - hide error but keep state updated
            _connectionTimer?.cancel();
            setState(() {
              _currentConnectionState = state;
              _showConnectionError = false;
              _isConnecting = true;
            });
          }
          
          // Show snackbar notifications only for errors/issues (success is silent)
          if (state == WebSocketConnectionState.error) {
            _showConnectionStatus('连接失败，正在重试...', isError: true);
          } else if (state == WebSocketConnectionState.reconnecting) {
            _showConnectionStatus('正在重新连接...', isError: false);
          }
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
          _showConnectionStatus('消息接收错误: $error', isError: true);
        },
      );
      
      print('🚀 Attempting WebSocket connection...');
      await webSocketService.connect(userId, token);
      print('✅ WebSocket connection initiated');
      
    } catch (error) {
      print('❌ WebSocket connection failed: $error');
      _showConnectionStatus('连接失败: $error', isError: true);
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
          _showConnectionStatus('AI错误: $content', isError: true);
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
        _showConnectionStatus('消息包含特殊字符，已自动处理', isError: false);
        
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
    final widgets = <Widget>[];
    
    if (text.contains('<WIDGET:VALUATION_CARD>')) {
      widgets.add(
        ValuationCard(
          propertyName: '北京天通苑',
          estimatedValue: 4500000,
          pricePerSqm: '3.8万/平',
          onConfirm: () {
            _sendMessage('确认估值 450万');
          },
          onEdit: () {
            _sendMessage('我想调整估值');
          },
        ),
      );
    }
    
    if (text.contains('<WIDGET:ACTION_CARD>')) {
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
    
    if (text.contains('<WIDGET:PORTFOLIO_CHART>')) {
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
    
    return widgets.isNotEmpty ? widgets : null;
  }

  void _showConnectionStatus(String message, {required bool isError}) {
    if (!mounted) return;
    
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: isError ? Colors.red : Colors.green,
        duration: Duration(seconds: isError ? 4 : 2),
      ),
    );
  }

  void _startConnectionErrorTimer() {
    // Cancel any existing timer
    _connectionTimer?.cancel();
    
    // Start 3-second grace period before showing error
    _connectionTimer = Timer(const Duration(seconds: 3), () {
      if (mounted && 
          (_currentConnectionState == WebSocketConnectionState.disconnected ||
           _currentConnectionState == WebSocketConnectionState.error)) {
        setState(() {
          _showConnectionError = true;
        });
      }
    });
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
          connectionState == WebSocketConnectionState.disconnected) {
        print('🔌 Initial WebSocket connection needed');
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
        // User is logged in with a valid token - connect WebSocket only if not already connected
        if (currentState == WebSocketConnectionState.disconnected) {
          print('✅ User logged in, connecting WebSocket...');
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
    
    return Scaffold(
          appBar: AppBar(
            title: const Text('AI 资产顾问'),
            actions: [
              // Connection status indicator - only show on failure
              if (_shouldShowConnectionStatus(connectionState))
                Container(
                  margin: const EdgeInsets.only(right: 8),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        _getConnectionIcon(connectionState),
                        color: _getConnectionColor(connectionState),
                        size: 16,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        _getConnectionText(connectionState),
                        style: TextStyle(
                          fontSize: 12,
                          color: _getConnectionColor(connectionState),
                        ),
                      ),
                    ],
                  ),
                ),
              IconButton(
                icon: const Icon(Icons.refresh),
                onPressed: () async {
                  final webSocketService = ref.read(webSocketServiceProvider);
                  if (webSocketService.connectionState == WebSocketConnectionState.error) {
                    await webSocketService.reconnect();
                  } else {
                    setState(() {
                      _messages.clear();
                    });
                  }
                },
              ),
            ],
          ),
      body: Column(
        children: [
          // Connection error/failure banner - only show after grace period
          if (_showConnectionError && 
              (connectionState == WebSocketConnectionState.error ||
               connectionState == WebSocketConnectionState.disconnected))
            Container(
              width: double.infinity,
              margin: const EdgeInsets.all(16),
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.red.shade50,
                border: Border.all(color: Colors.red.shade200),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.error, color: Colors.red.shade600, size: 20),
                      const SizedBox(width: 8),
                      Text(
                        connectionState == WebSocketConnectionState.error 
                            ? '连接失败' 
                            : '连接已断开',
                        style: TextStyle(
                          color: Colors.red.shade600,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    connectionState == WebSocketConnectionState.error
                        ? 'Token可能已过期，请重新登录后再试'
                        : '网络连接已断开，请检查网络或重试',
                    style: TextStyle(color: Colors.red.shade700),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      if (connectionState == WebSocketConnectionState.error)
                        ElevatedButton.icon(
                          onPressed: () {
                            // 导航到登录页面
                            Navigator.of(context).pushReplacementNamed('/login');
                          },
                          icon: const Icon(Icons.login, size: 16),
                          label: const Text('重新登录'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: Colors.red.shade600,
                            foregroundColor: Colors.white,
                          ),
                        ),
                      if (connectionState == WebSocketConnectionState.error)
                        const SizedBox(width: 8),
                      TextButton.icon(
                        onPressed: () async {
                          final webSocketService = ref.read(webSocketServiceProvider);
                          await webSocketService.reconnect();
                        },
                        icon: const Icon(Icons.refresh, size: 16),
                        label: const Text('重试连接'),
                      ),
                    ],
                  ),
                ],
              ),
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
                      hintText: connectionState == WebSocketConnectionState.connected 
                          ? '输入您的资产信息...' 
                          : '等待连接...',
                      border: const OutlineInputBorder(),
                      enabled: connectionState == WebSocketConnectionState.connected,
                    ),
                    maxLines: null,
                    onSubmitted: (_) => _sendMessage(),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  key: const Key('send_button'),
                  onPressed: connectionState == WebSocketConnectionState.connected ? _sendMessage : null,
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

  bool _shouldShowConnectionStatus(WebSocketConnectionState state) {
    // Only show connection status when there's an actual failure AND grace period has passed
    // Hide during normal connecting/connected states to keep UI clean
    if (!_showConnectionError) {
      return false; // Grace period not elapsed yet
    }
    
    switch (state) {
      case WebSocketConnectionState.error:
        return true; // Authentication or connection error
      case WebSocketConnectionState.disconnected:
        return true; // Connection dropped
      case WebSocketConnectionState.connected:
      case WebSocketConnectionState.connecting:
      case WebSocketConnectionState.reconnecting:
        return false; // Hide during normal operation
    }
  }

  IconData _getConnectionIcon(WebSocketConnectionState state) {
    switch (state) {
      case WebSocketConnectionState.connected:
        return Icons.wifi;
      case WebSocketConnectionState.connecting:
      case WebSocketConnectionState.reconnecting:
        return Icons.wifi_off;
      case WebSocketConnectionState.error:
        return Icons.error;
      case WebSocketConnectionState.disconnected:
        return Icons.wifi_off;
    }
  }

  Color _getConnectionColor(WebSocketConnectionState state) {
    switch (state) {
      case WebSocketConnectionState.connected:
        return Colors.green;
      case WebSocketConnectionState.connecting:
      case WebSocketConnectionState.reconnecting:
        return Colors.orange;
      case WebSocketConnectionState.error:
        return Colors.red;
      case WebSocketConnectionState.disconnected:
        return Colors.grey;
    }
  }

  String _getConnectionText(WebSocketConnectionState state) {
    switch (state) {
      case WebSocketConnectionState.connected:
        return '已连接';
      case WebSocketConnectionState.connecting:
        return '连接中';
      case WebSocketConnectionState.reconnecting:
        return '重连中';
      case WebSocketConnectionState.error:
        return '连接失败';
      case WebSocketConnectionState.disconnected:
        return '连接已断开'; // More clearly indicates a failure/dropped connection
    }
  }

  Future<void> _sendMessage([String? text]) async {
    final messageText = text ?? _messageController.text.trim();
    if (messageText.isEmpty) return;

    final webSocketService = ref.read(webSocketServiceProvider);
    if (!webSocketService.isConnected) {
      print('❌ WebSocket not connected, cannot send message');
      _showConnectionStatus('未连接到服务器，无法发送消息', isError: true);
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
      _showConnectionStatus('发送消息失败: $error', isError: true);
      
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
      selectable: true,
    );
  }
}