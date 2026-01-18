import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:device_info_plus/device_info_plus.dart';
import 'package:dio/dio.dart';
import 'dart:io';
import '../../../../core/providers/auth_provider.dart';
import '../../../../core/services/error_handling_service.dart';

class LoginPage extends ConsumerStatefulWidget {
  const LoginPage({super.key});

  @override
  ConsumerState<LoginPage> createState() => _LoginPageState();
}

class _LoginPageState extends ConsumerState<LoginPage> {
  final _phoneController = TextEditingController();
  final _codeController = TextEditingController();
  bool _codeSent = false;
  bool _isLoading = false;
  bool _isSendingCode = false;
  late final ErrorHandlingService _errorService;

  @override
  void initState() {
    super.initState();
    _errorService = ref.read(errorHandlingServiceProvider.notifier);
  }

  @override
  void dispose() {
    _phoneController.dispose();
    _codeController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('登录 AssetFlow'),
      ),
      body: Padding(
        padding: const EdgeInsets.all(24.0),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            const Icon(
              Icons.account_balance_wallet,
              size: 80,
              color: Colors.blue,
            ),
            const SizedBox(height: 32),
            const Text(
              'AssetFlow',
              style: TextStyle(
                fontSize: 32,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'AI 原生家庭资产配置顾问',
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey,
              ),
            ),
            const SizedBox(height: 48),
            TextField(
              key: const Key('phone_input'),
              controller: _phoneController,
              decoration: const InputDecoration(
                labelText: '手机号',
                prefixIcon: Icon(Icons.phone),
              ),
              keyboardType: TextInputType.phone,
            ),
            const SizedBox(height: 16),
            if (_codeSent) ...[
              TextField(
                controller: _codeController,
                decoration: const InputDecoration(
                  labelText: '验证码',
                  prefixIcon: Icon(Icons.security),
                ),
                keyboardType: TextInputType.number,
              ),
              const SizedBox(height: 16),
            ],
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                key: Key(_codeSent ? 'login_button' : 'send_code_button'),
                onPressed: (_codeSent ? _isLoading : _isSendingCode) ? null : (_codeSent ? _login : _sendCode),
                child: (_codeSent ? _isLoading : _isSendingCode)
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : Text(_codeSent ? '登录' : '发送验证码'),
              ),
            ),
            const SizedBox(height: 16),
            TextButton(
              onPressed: _isLoading ? null : _anonymousLogin,
              child: _isLoading 
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Text('匿名体验'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _sendCode() async {
    if (_phoneController.text.isEmpty) {
      _errorService.showWarning(context, '请输入手机号');
      return;
    }

    // 简单的手机号格式验证
    if (!RegExp(r'^1[3-9]\d{9}$').hasMatch(_phoneController.text)) {
      _errorService.showWarning(context, '请输入正确的手机号格式');
      return;
    }

    setState(() {
      _isSendingCode = true;
    });

    try {
      await ref.read(authStateProvider.notifier).sendVerificationCode(_phoneController.text);
      
      setState(() {
        _codeSent = true;
      });
      
      if (mounted) {
        _errorService.showSuccess(context, '验证码已发送，请查看后端控制台');
      }
    } catch (error) {
      if (mounted) {
        if (error is DioException) {
          // 使用错误处理服务来处理Dio异常
          _errorService.handleDioError(
            context, 
            error,
            onRetry: () => _sendCode(), // 提供重试功能
          );
        } else {
          // 处理其他类型的错误
          final apiError = ApiError(
            message: error.toString(),
            code: ErrorCode.internalServerError,
          );
          _errorService.handleApiError(
            context, 
            apiError,
            onRetry: () => _sendCode(),
          );
        }
      }
    } finally {
      if (mounted) {
        setState(() {
          _isSendingCode = false;
        });
      }
    }
  }

  Future<void> _login() async {
    if (_codeController.text.isEmpty) {
      _errorService.showWarning(context, '请输入验证码');
      return;
    }

    // 简单的验证码格式验证
    if (_codeController.text.length != 6 || !RegExp(r'^\d{6}$').hasMatch(_codeController.text)) {
      _errorService.showWarning(context, '验证码应为6位数字');
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      await ref.read(authStateProvider.notifier).login(
        _phoneController.text,
        _codeController.text,
      );
      
      // 登录成功，直接跳转
      if (mounted) {
        context.go('/chat');
      }
    } catch (error) {
      if (mounted) {
        if (error is DioException) {
          _errorService.handleDioError(
            context, 
            error,
            onRetry: () => _login(),
          );
        } else {
          final apiError = ApiError(
            message: error.toString(),
            code: ErrorCode.authInvalidCredentials,
          );
          _errorService.handleApiError(
            context, 
            apiError,
            onRetry: () => _login(),
          );
        }
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _anonymousLogin() async {
    setState(() {
      _isLoading = true;
    });

    try {
      // 获取设备ID
      final deviceInfo = DeviceInfoPlugin();
      String deviceId;
      
      if (Platform.isAndroid) {
        final androidInfo = await deviceInfo.androidInfo;
        deviceId = androidInfo.id;
      } else if (Platform.isIOS) {
        final iosInfo = await deviceInfo.iosInfo;
        deviceId = iosInfo.identifierForVendor ?? 'unknown_ios_device';
      } else {
        deviceId = 'unknown_device_${DateTime.now().millisecondsSinceEpoch}';
      }

      // 执行匿名登录
      await ref.read(authStateProvider.notifier).loginAnonymously(deviceId);
      
      // 检查登录状态
      final authState = ref.read(authStateProvider);
      if (authState.hasValue && authState.value != null) {
        if (mounted) {
          context.go('/chat');
        }
      } else {
        throw Exception('匿名登录失败');
      }
    } catch (error) {
      if (mounted) {
        if (error is DioException) {
          _errorService.handleDioError(
            context, 
            error,
            onRetry: () => _anonymousLogin(),
          );
        } else {
          final apiError = ApiError(
            message: error.toString(),
            code: ErrorCode.authInvalidCredentials,
          );
          _errorService.handleApiError(
            context, 
            apiError,
            onRetry: () => _anonymousLogin(),
          );
        }
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }
}