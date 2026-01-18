import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/providers/auth_provider.dart';

class ProfilePage extends ConsumerWidget {
  const ProfilePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('个人中心'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _buildUserInfo(context, ref),
          const SizedBox(height: 16),
          _buildSettingsSection(context, ref),
          const SizedBox(height: 16),
          _buildAboutSection(context, ref),
        ],
      ),
    );
  }

  Widget _buildUserInfo(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authStateProvider);
    final token = ref.watch(authTokenProvider);
    
    // 添加调试信息
    print('🔍 个人中心 - AuthState: ${authState.toString()}');
    token.when(
      data: (tokenValue) => print('🔍 个人中心 - Token: ${tokenValue?.substring(0, 20) ?? 'null'}...'),
      loading: () => print('🔍 个人中心 - Token: loading...'),
      error: (error, stack) => print('🔍 个人中心 - Token error: $error'),
    );
    
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            const CircleAvatar(
              radius: 30,
              child: Icon(Icons.person, size: 30),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    authState.when(
                      data: (user) {
                        if (user == null) return '未登录';
                        // 检查是否为匿名用户（手机号以1开头且为11位数字，但没有真实手机号特征）
                        if (user.deviceId != null && user.phone.startsWith('1') && user.phone.length == 11) {
                          // 进一步检查是否为生成的匿名手机号
                          try {
                            int.parse(user.phone);
                            return '匿名用户';
                          } catch (e) {
                            return user.phone;
                          }
                        }
                        return user.phone;
                      },
                      loading: () => '加载中...',
                      error: (_, __) => '未登录',
                    ),
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 4),
                  Text(
                    authState.when(
                      data: (user) {
                        if (user == null) return '请先登录';
                        if (user.deviceId != null && user.phone.startsWith('1') && user.phone.length == 11) {
                          try {
                            int.parse(user.phone);
                            return '点击绑定手机号';
                          } catch (e) {
                            return '已绑定手机号';
                          }
                        }
                        return '已绑定手机号';
                      },
                      loading: () => '加载中...',
                      error: (_, __) => '请先登录',
                    ),
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: Colors.grey,
                    ),
                  ),
                ],
              ),
            ),
            IconButton(
              onPressed: () {
                final user = authState.value;
                if (user != null && user.deviceId != null) {
                  // 匿名用户，显示绑定手机号选项
                  _showBindPhoneDialog(context, ref);
                } else {
                  // 已登录用户，编辑个人信息
                  // TODO: Navigate to profile edit
                }
              },
              icon: const Icon(Icons.edit),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSettingsSection(BuildContext context, WidgetRef ref) {
    return Card(
      child: Column(
        children: [
          ListTile(
            leading: const Icon(Icons.notifications),
            title: const Text('通知设置'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {
              // TODO: Navigate to notification settings
            },
          ),
          const Divider(height: 1),
          ListTile(
            leading: const Icon(Icons.security),
            title: const Text('隐私设置'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {
              // TODO: Navigate to privacy settings
            },
          ),
          const Divider(height: 1),
          ListTile(
            leading: const Icon(Icons.language),
            title: const Text('语言设置'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {
              // TODO: Navigate to language settings
            },
          ),
        ],
      ),
    );
  }

  Widget _buildAboutSection(BuildContext context, WidgetRef ref) {
    return Card(
      child: Column(
        children: [
          ListTile(
            leading: const Icon(Icons.help),
            title: const Text('帮助中心'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {
              // TODO: Navigate to help center
            },
          ),
          const Divider(height: 1),
          ListTile(
            leading: const Icon(Icons.info),
            title: const Text('关于我们'),
            trailing: const Icon(Icons.chevron_right),
            onTap: () {
              // TODO: Navigate to about page
            },
          ),
          const Divider(height: 1),
          ListTile(
            leading: const Icon(Icons.logout),
            title: const Text('退出登录'),
            onTap: () {
              ref.read(authStateProvider.notifier).logout();
              context.go('/login');
            },
          ),
        ],
      ),
    );
  }

  void _showBindPhoneDialog(BuildContext context, WidgetRef ref) {
    final phoneController = TextEditingController();
    final codeController = TextEditingController();
    bool codeSent = false;
    bool isLoading = false;

    showDialog(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setState) => AlertDialog(
          title: const Text('绑定手机号'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: phoneController,
                decoration: const InputDecoration(
                  labelText: '手机号',
                  prefixIcon: Icon(Icons.phone),
                ),
                keyboardType: TextInputType.phone,
              ),
              const SizedBox(height: 16),
              if (codeSent) ...[
                TextField(
                  controller: codeController,
                  decoration: const InputDecoration(
                    labelText: '验证码',
                    prefixIcon: Icon(Icons.security),
                  ),
                  keyboardType: TextInputType.number,
                ),
                const SizedBox(height: 16),
              ],
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.of(context).pop(),
              child: const Text('取消'),
            ),
            if (!codeSent)
              ElevatedButton(
                onPressed: isLoading ? null : () async {
                  if (phoneController.text.isEmpty) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('请输入手机号')),
                    );
                    return;
                  }

                  setState(() => isLoading = true);
                  try {
                    await ref.read(authStateProvider.notifier).sendVerificationCode(phoneController.text);
                    setState(() => codeSent = true);
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('验证码已发送，请查看后端控制台')),
                    );
                  } catch (error) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('发送验证码失败: $error')),
                    );
                  } finally {
                    setState(() => isLoading = false);
                  }
                },
                child: isLoading 
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Text('发送验证码'),
              )
            else
              ElevatedButton(
                onPressed: isLoading ? null : () async {
                  if (codeController.text.isEmpty) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('请输入验证码')),
                    );
                    return;
                  }

                  setState(() => isLoading = true);
                  try {
                    // TODO: 实现绑定手机号功能
                    await ref.read(authStateProvider.notifier).bindPhone(
                      phoneController.text,
                      codeController.text,
                    );
                    Navigator.of(context).pop();
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('手机号绑定成功')),
                    );
                  } catch (error) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(content: Text('绑定失败: $error')),
                    );
                  } finally {
                    setState(() => isLoading = false);
                  }
                },
                child: isLoading 
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                    : const Text('绑定'),
              ),
          ],
        ),
      ),
    );
  }
}