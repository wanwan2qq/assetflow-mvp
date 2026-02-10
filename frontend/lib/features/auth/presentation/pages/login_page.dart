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
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return Scaffold(
      backgroundColor: isDark ? const Color(0xFF121212) : Colors.grey[50],
      body: Stack(
        children: [
          // Background Gradient decoration
          Positioned(
            top: -100,
            right: -100,
            child: Container(
              width: 300,
              height: 300,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: RadialGradient(
                  colors: [
                    const Color(0xFF00695C).withOpacity(isDark ? 0.2 : 0.1),
                    Colors.transparent,
                  ],
                ),
              ),
            ),
          ),
          SafeArea(
            child: Center(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(horizontal: 24.0),
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    const SizedBox(height: 40),
                    _buildHeroSection(isDark),
                    const SizedBox(height: 48),
                    _buildInputForm(isDark),
                    const SizedBox(height: 24),
                    _buildAnonymousTrial(isDark),
                    const SizedBox(height: 60),
                    _buildFooter(isDark),
                    const SizedBox(height: 20),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildHeroSection(bool isDark) {
    return Column(
      children: [
        Container(
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF00695C).withOpacity(0.2),
                blurRadius: 20,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          child: const Icon(
            Icons.account_balance_wallet,
            size: 80,
            color: Color(0xFF00695C),
          ),
        ),
        const SizedBox(height: 32),
        Text(
          'inW',
          style: Theme.of(context).textTheme.displaySmall?.copyWith(
            fontWeight: FontWeight.bold,
            color: isDark ? const Color(0xFFEEEEEE) : const Color(0xFF121212),
          ),
        ),
        const SizedBox(height: 8),
        Text(
          'AI 原生家庭资产配置顾问',
          style: Theme.of(context).textTheme.bodyLarge?.copyWith(
            color: isDark ? Colors.grey[400] : Colors.grey[600],
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }

  Widget _buildInputForm(bool isDark) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF1E1E1E) : Colors.white,
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          if (!isDark)
            BoxShadow(
              color: Colors.black.withOpacity(0.05),
              blurRadius: 20,
              offset: const Offset(0, 10),
            ),
        ],
      ),
      child: Column(
        children: [
          _buildTextField(
            controller: _phoneController,
            label: '请输入手机号',
            icon: Icons.phone_android,
            prefixText: '+86',
            isDark: isDark,
          ),
          if (_codeSent) ...[
            const SizedBox(height: 16),
            _buildTextField(
              controller: _codeController,
              label: '请输入验证码',
              icon: Icons.security,
              isDark: isDark,
              isNumber: true,
            ),
          ],
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            height: 50,
            child: FilledButton(
              onPressed: (_codeSent ? _isLoading : _isSendingCode) ? null : (_codeSent ? _login : _sendCode),
              style: FilledButton.styleFrom(
                backgroundColor: const Color(0xFF00695C),
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
                elevation: 0,
              ),
              child: (_codeSent ? _isLoading : _isSendingCode)
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : Text(
                      _codeSent ? '进入 inW' : '发送验证码',
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildTextField({
    required TextEditingController controller,
    required String label,
    required IconData icon,
    String? prefixText,
    required bool isDark,
    bool isNumber = false,
  }) {
    return TextField(
      controller: controller,
      keyboardType: isNumber ? TextInputType.number : TextInputType.phone,
      style: TextStyle(
        color: isDark ? Colors.white : Colors.black87,
      ),
      decoration: InputDecoration(
        filled: true,
        fillColor: isDark ? const Color(0xFF2C2C2C) : Colors.grey[50],
        prefixIcon: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(width: 12),
            Icon(icon, color: const Color(0xFF00695C)),
            if (prefixText != null) ...[
              const SizedBox(width: 8),
              Container(
                width: 1,
                height: 16,
                color: isDark ? Colors.grey[700] : Colors.grey[400],
              ),
              const SizedBox(width: 8),
              Text(
                prefixText,
                style: TextStyle(
                  color: isDark ? Colors.grey[400] : Colors.grey[600],
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(width: 4), // Reduced spacing
            ] else ...[
               const SizedBox(width: 12),
            ],
          ],
        ),
        hintText: label,
        hintStyle: TextStyle(
          color: isDark ? Colors.grey[600] : Colors.grey[400],
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      ),
    );
  }

  Widget _buildAnonymousTrial(bool isDark) {
    return TextButton(
      onPressed: _isLoading ? null : _anonymousLogin,
      child: Text(
        '匿名体验',
        style: TextStyle(
          color: isDark ? Colors.grey[400] : Colors.grey[600],
          fontSize: 14,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }
  
  Widget _buildFooter(bool isDark) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Icon(Icons.shield_outlined, size: 14, color: isDark ? Colors.grey[600] : Colors.grey[400]),
        const SizedBox(width: 4),
        Text(
          '银行级安全保障 · 本地数据存储',
          style: TextStyle(
            color: isDark ? Colors.grey[600] : Colors.grey[400],
            fontSize: 12,
          ),
        ),
      ],
    );
  }

  void _showToast(String message, {bool isError = false, bool isSuccess = false}) {
    if (!mounted) return;
    
    ScaffoldMessenger.of(context).clearSnackBars();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Row(
          children: [
            Icon(
              isError ? Icons.cancel : (isSuccess ? Icons.check_circle : Icons.info),
              color: isError ? Colors.redAccent : (isSuccess ? Colors.greenAccent : Colors.white),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                message,
                style: const TextStyle(
                  color: Colors.white,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          ],
        ),
        behavior: SnackBarBehavior.floating,
        backgroundColor: const Color(0xFF323232).withOpacity(0.95),
        margin: const EdgeInsets.all(16),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(12),
        ),
        elevation: 4,
        duration: const Duration(seconds: 3),
      ),
    );
  }

  Future<void> _sendCode() async {
    if (_phoneController.text.isEmpty) {
      _showToast('请输入手机号', isError: true);
      return;
    }

    // 简单的手机号格式验证
    if (!RegExp(r'^1[3-9]\d{9}$').hasMatch(_phoneController.text)) {
      _showToast('请输入正确的手机号格式', isError: true);
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
      
      _showToast('验证码已发送', isSuccess: true);
    } catch (error) {
       _showToast('网络错误，请稍后重试', isError: true);
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
      _showToast('请输入验证码', isError: true);
      return;
    }

    if (_codeController.text.length != 6 || !RegExp(r'^\d{6}$').hasMatch(_codeController.text)) {
      _showToast('验证码应为6位数字', isError: true);
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
      
      if (mounted) {
        context.go('/chat');
      }
    } catch (error) {
      _showToast('登录失败，请检查验证码或网络', isError: true);
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

      await ref.read(authStateProvider.notifier).loginAnonymously(deviceId);
      
      final authState = ref.read(authStateProvider);
      if (authState.hasValue && authState.value != null) {
        if (mounted) {
          context.go('/chat');
        }
      } else {
        throw Exception('匿名登录失败');
      }
    } catch (error) {
      _showToast('匿名登录失败，请稍后重试', isError: true);
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }
}