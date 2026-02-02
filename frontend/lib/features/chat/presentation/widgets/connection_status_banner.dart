import 'package:flutter/material.dart';
import '../../../../core/services/websocket_service.dart';

class ConnectionStatusBanner extends StatefulWidget {
  final WebSocketConnectionState connectionState;
  final String? errorMessage;

  const ConnectionStatusBanner({
    super.key,
    required this.connectionState,
    this.errorMessage,
  });

  @override
  State<ConnectionStatusBanner> createState() => _ConnectionStatusBannerState();
}

class _ConnectionStatusBannerState extends State<ConnectionStatusBanner> with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _heightFactor;
  
  bool _isVisible = false;
  Color _backgroundColor = Colors.grey;
  String _message = '';
  IconData _icon = Icons.info_outline;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    _heightFactor = CurvedAnimation(parent: _controller, curve: Curves.easeInOut);
    
    // Initial state update
    _updateState(widget.connectionState);
  }

  @override
  void didUpdateWidget(ConnectionStatusBanner oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.connectionState != widget.connectionState || 
        oldWidget.errorMessage != widget.errorMessage) {
      _updateState(widget.connectionState);
    }
  }

  void _updateState(WebSocketConnectionState state) {
    bool shouldShow = false;
    
    switch (state) {
      case WebSocketConnectionState.connecting:
        _backgroundColor = Colors.orange.shade400;
        _message = '正在连接...';
        _icon = Icons.cloud_sync;
        shouldShow = true;
        break;
        
      case WebSocketConnectionState.reconnecting:
        _backgroundColor = Colors.orange.shade600;
        _message = '网络断开，正在重连...';
        _icon = Icons.wifi_off_rounded;
        shouldShow = true;
        break;
        
      case WebSocketConnectionState.error:
        _backgroundColor = Colors.red.shade400;
        _message = widget.errorMessage ?? '连接失败，请检查网络';
        _icon = Icons.error_outline;
        shouldShow = true;
        break;
        
      case WebSocketConnectionState.connected:
        _backgroundColor = Colors.green.shade500;
        _message = '已连接';
        _icon = Icons.check_circle_outline;
        shouldShow = true;
        
        // Hide after delay
        Future.delayed(const Duration(seconds: 2), () {
          if (mounted && widget.connectionState == WebSocketConnectionState.connected) {
            _hide();
          }
        });
        break;
        
      case WebSocketConnectionState.disconnected:
        // Don't show anything for disconnected state (initial state)
        shouldShow = false;
        break;
    }

    if (shouldShow && !_isVisible) {
      _show();
    } else if (!shouldShow && _isVisible) {
      _hide();
    }
    
    // Force rebuild to update colors/text even if visibility doesn't change
    if (mounted) setState(() {});
  }

  void _show() {
    _isVisible = true;
    _controller.forward();
  }

  void _hide() {
    _isVisible = false;
    _controller.reverse();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return ClipRect(
          child: Align(
            heightFactor: _heightFactor.value,
            alignment: Alignment.topCenter,
            child: Container(
              width: double.infinity,
              color: _backgroundColor,
              padding: const EdgeInsets.symmetric(vertical: 4, horizontal: 16),
              child: SafeArea(
                bottom: false,
                top: false, // Assuming it's already below a SafeArea or AppBar
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(_icon, size: 14, color: Colors.white),
                    const SizedBox(width: 8),
                    Text(
                      _message,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 12,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    if (widget.connectionState == WebSocketConnectionState.connecting || 
                        widget.connectionState == WebSocketConnectionState.reconnecting) ...[
                      const SizedBox(width: 8),
                      const SizedBox(
                        width: 10,
                        height: 10,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}
