import 'dart:ui';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../../../core/providers/auth_provider.dart';
import '../../../../core/providers/theme_provider.dart';

class ProfilePage extends ConsumerWidget {
  const ProfilePage({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    // Premium Fintech Theme Strategy:
    // Light Mode: Colors.grey[50]
    // Dark Mode: Deep Dark (0xFF121212)
    final scaffoldBg = isDark ? const Color(0xFF121212) : Colors.grey[50];

    return Scaffold(
      backgroundColor: scaffoldBg,
      body: SingleChildScrollView(
        child: Column(
          children: [
            _buildHeader(context, ref),
            const SizedBox(height: 24),
            _buildDataSecuritySection(context, ref),
            const SizedBox(height: 24),
            _buildSettingsSection(context, ref),
            const SizedBox(height: 24),
            _buildAboutSection(context, ref),
            const SizedBox(height: 40),
            _buildDangerZone(context, ref),
            const SizedBox(height: 60), // Bottom padding
          ],
        ),
      ),
    );
  }

  Widget _buildHeader(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authStateProvider);
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        // Brand Gradient (Deep Teal) - Matching Wealth Page Hero
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: isDark
              ? [const Color(0xFF004D40), const Color(0xFF00695C)]
              : [theme.colorScheme.primary, Color.lerp(theme.colorScheme.primary, Colors.black, 0.2)!],
        ),
        boxShadow: [
          BoxShadow(
            color: theme.colorScheme.primary.withOpacity(0.3),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
        borderRadius: const BorderRadius.only(
          bottomLeft: Radius.circular(32),
          bottomRight: Radius.circular(32),
        ),
      ),
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(24, 16, 24, 32),
          child: Column(
            children: [
              // Custom AppBar visual
              Padding(
                padding: const EdgeInsets.only(bottom: 24),
                child: Text(
                  '我的',
                  style: theme.textTheme.titleMedium?.copyWith(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              
              InkWell(
                onTap: () => _handleProfileTap(context, ref),
                borderRadius: BorderRadius.circular(16),
                child: Padding(
                  padding: const EdgeInsets.all(8.0),
                  child: Row(
                    children: [
                      // Avatar with White Boarder
                      Container(
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          border: Border.all(color: Colors.white, width: 2),
                          boxShadow: [
                             BoxShadow(
                               color: Colors.black.withOpacity(0.1), 
                               blurRadius: 8, 
                               offset: const Offset(0, 4)
                             ),
                          ],
                        ),
                        child: CircleAvatar(
                          radius: 36,
                          backgroundColor: Colors.white,
                          child: Icon(Icons.person, size: 40, color: theme.colorScheme.primary),
                        ),
                      ),
                      const SizedBox(width: 20),
                      
                      // User Info
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              authState.when(
                                data: (user) {
                                  if (user == null) return '未登录';
                                  if (user.deviceId != null && user.phone.startsWith('1') && user.phone.length == 11) {
                                    try {
                                      int.parse(user.phone);
                                      return '匿名用户';
                                    } catch (_) {
                                      return user.phone;
                                    }
                                  }
                                  return user.phone;
                                },
                                loading: () => '加载中...',
                                error: (_, __) => '未登录',
                              ),
                              style: theme.textTheme.titleLarge?.copyWith(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            const SizedBox(height: 8),
                            
                            // Tag & Badge Row
                            Row(
                              children: [
                                // Gold/Amber Glassmorphism Pill
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                  decoration: BoxDecoration(
                                    color: Colors.amber.withOpacity(0.2),
                                    borderRadius: BorderRadius.circular(20),
                                    border: Border.all(color: Colors.amber.withOpacity(0.3), width: 1),
                                  ),
                                  child: Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      const Icon(Icons.stars_rounded, color: Colors.amber, size: 14),
                                      const SizedBox(width: 4),
                                      Text(
                                        '财富管家',
                                        style: theme.textTheme.labelSmall?.copyWith(
                                          color: Colors.white,
                                          fontWeight: FontWeight.w600,
                                        ),
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                      
                      Icon(Icons.chevron_right, color: Colors.white.withOpacity(0.7)),
                    ],
                  ),
                ),
              ),

              const SizedBox(height: 24),

              // Stats Row (Joined Days)
              authState.when(
                data: (user) {
                  if (user == null) return const SizedBox.shrink();
                  final daysJoined = DateTime.now().difference(user.createdAt).inDays + 1;
                  return Row(
                    children: [
                      Icon(Icons.calendar_today_rounded, size: 14, color: Colors.white.withOpacity(0.6)),
                      const SizedBox(width: 6),
                      Text(
                        '已加入 $daysJoined 天',
                        style: TextStyle(
                          color: Colors.white.withOpacity(0.8),
                          fontSize: 12,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  );
                },
                loading: () => const SizedBox.shrink(),
                error: (_, __) => const SizedBox.shrink(),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _handleProfileTap(BuildContext context, WidgetRef ref) {
    final user = ref.read(authStateProvider).value;
    if (user != null) {
      if (user.deviceId != null && user.phone.startsWith('1') && user.phone.length == 11) {
        try {
          int.parse(user.phone);
          _showBindPhoneDialog(context, ref);
        } catch (_) {
          // Real phone, navigate to edit
        }
      } else {
        // Real user, navigate to edit
      }
    }
  }

  Widget _buildSectionHeader(BuildContext context, String title) {
    return Padding(
      padding: const EdgeInsets.only(left: 24, bottom: 8),
      child: Text(
        title.toUpperCase(),
        style: TextStyle(
          color: Theme.of(context).brightness == Brightness.dark ? Colors.grey[400] : Colors.grey[600],
          fontSize: 12,
          fontWeight: FontWeight.bold,
          letterSpacing: 0.5,
        ),
      ),
    );
  }

  Widget _buildCard(BuildContext context, List<Widget> children) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF1E1E1E) : Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: children.asMap().entries.map((entry) {
          final index = entry.key;
          final widget = entry.value;
          return Column(
            children: [
              widget,
              if (index != children.length - 1)
                Divider(
                  height: 1, 
                  indent: 60, // Align with text start (Icon size 28 + padding)
                  endIndent: 16,
                  color: isDark ? Colors.white.withOpacity(0.08) : Colors.grey.withOpacity(0.1),
                ),
            ],
          );
        }).toList(),
      ),
    );
  }

  Widget _buildIconTile(BuildContext context, {
    required IconData icon,
    required Color color,
    required String title,
    String? subtitle,
    Widget? trailing,
    VoidCallback? onTap,
    bool isDestructive = false,
  }) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      leading: Container(
        width: 32,
        height: 32,
        decoration: BoxDecoration(
          color: color.withOpacity(isDark ? 0.2 : 0.1),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Icon(icon, color: color, size: 18),
      ),
      title: Text(
        title,
        style: TextStyle(
          color: isDestructive ? Colors.red : (isDark ? Colors.white : Colors.black87),
          fontWeight: FontWeight.w500,
          fontSize: 15,
        ),
      ),
      subtitle: subtitle != null ? Text(subtitle, style: const TextStyle(fontSize: 12)) : null,
      trailing: trailing ?? Icon(Icons.chevron_right_rounded, size: 20, color: Colors.grey.withOpacity(0.6)),
      onTap: onTap,
    );
  }

  Widget _buildDataSecuritySection(BuildContext context, WidgetRef ref) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildSectionHeader(context, 'Data & Security'),
        _buildCard(context, [
          _buildIconTile(
            context,
            icon: Icons.cloud_sync_rounded,
            color: Colors.indigo,
            title: '备份与恢复',
            onTap: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('功能开发中：iCloud/本地备份')),
              );
            },
          ),
          _buildIconTile(
            context,
            icon: Icons.file_download_rounded,
            color: Colors.green,
            title: '导出数据',
            onTap: () {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('功能开发中：导出为 Excel/CSV')),
              );
            },
          ),
          // Custom SwitchTile needed for alignment match
          _buildSwitchTile(
            context,
            icon: Icons.face_rounded,
            color: Colors.purple,
            title: '生物识别锁定',
            value: false, // TODO: Connect to local storage
            onChanged: (val) {
               ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('功能开发中：FaceID/TouchID 锁定')),
              );
            }
          ),
        ]),
      ],
    );
  }

  Widget _buildSwitchTile(BuildContext context, {
    required IconData icon,
    required Color color,
    required String title,
    required bool value,
    required ValueChanged<bool> onChanged,
  }) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final theme = Theme.of(context);

    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
      leading: Container(
        width: 32,
        height: 32,
        decoration: BoxDecoration(
          color: color.withOpacity(isDark ? 0.2 : 0.1),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Icon(icon, color: color, size: 18),
      ),
      title: Text(
        title,
        style: TextStyle(
          color: isDark ? Colors.white : Colors.black87,
          fontWeight: FontWeight.w500,
          fontSize: 15,
        ),
      ),
      trailing: Switch.adaptive(
        value: value, 
        onChanged: onChanged,
        activeColor: theme.colorScheme.primary,
      ),
    );
  }

  Widget _buildSettingsSection(BuildContext context, WidgetRef ref) {
    final themeMode = ref.watch(themeModeProvider);
    
    String getThemeText(ThemeMode mode) {
      switch (mode) {
        case ThemeMode.system: return '自动';
        case ThemeMode.light: return '浅色';
        case ThemeMode.dark: return '深色';
      }
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildSectionHeader(context, 'Personalization'),
        _buildCard(context, [
          _buildIconTile(
            context,
            icon: Icons.dark_mode_rounded,
            color: Colors.deepPurple,
            title: '深色模式',
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(getThemeText(themeMode), style: const TextStyle(color: Colors.grey, fontSize: 13)),
                const SizedBox(width: 4),
                const Icon(Icons.chevron_right_rounded, size: 20, color: Colors.grey),
              ],
            ),
            onTap: () => _showThemeSelectionDialog(context, ref),
          ),
           _buildIconTile(
            context,
            icon: Icons.currency_yen_rounded,
            color: Colors.teal,
            title: '主货币单位',
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text('CNY', style: TextStyle(color: Colors.grey, fontSize: 13)),
                const SizedBox(width: 4),
                const Icon(Icons.chevron_right_rounded, size: 20, color: Colors.grey),
              ],
            ),
            onTap: () {},
          ),
          _buildSwitchTile(
            context,
            icon: Icons.notifications_active_rounded,
            color: Colors.redAccent,
            title: '消息通知',
            value: true,
            onChanged: (val) {},
          ),
        ]),
      ],
    );
  }

  Widget _buildAboutSection(BuildContext context, WidgetRef ref) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildSectionHeader(context, 'About'),
        _buildCard(context, [
          _buildIconTile(
            context,
            icon: Icons.help_center_rounded,
            color: Colors.orange,
            title: '帮助与反馈',
            onTap: () {},
          ),
          _buildIconTile(
            context,
            icon: Icons.info_rounded,
            color: Colors.blueGrey,
            title: '关于 AssetFlow',
            subtitle: 'v1.0.0',
            onTap: () {},
          ),
        ]),
      ],
    );
  }

  Widget _buildDangerZone(BuildContext context, WidgetRef ref) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 24.0),
          child: SizedBox(
            width: double.infinity,
            child: OutlinedButton(
              onPressed: () => _showClearDataDialog(context),
              style: OutlinedButton.styleFrom(
                side: BorderSide(color: Colors.red.withOpacity(0.5)),
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                backgroundColor: Colors.red.withOpacity(0.05),
              ),
              child: const Text(
                '重制应用数据 (Danger Zone)',
                style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold),
              ),
            ),
          ),
        ),
        const SizedBox(height: 16),
        TextButton(
          onPressed: () {
            ref.read(authStateProvider.notifier).logout();
            context.go('/login');
          },
          child: const Text('退出登录', style: TextStyle(color: Colors.grey)),
        ),
      ],
    );
  }

  // --- Dialogs ---
  
  void _showClearDataDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('⚠️ 警告'),
        content: const Text(
          '确定要清空所有数据吗？\n此操作不可恢复，所有资产、流水和设置都将丢失。',
          style: TextStyle(color: Colors.red),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('取消'),
          ),
          TextButton(
            onPressed: () {
              Navigator.of(context).pop();
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('数据已清空 (Mock)')),
              );
            },
            child: const Text('确认清空', style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }
  
  void _showThemeSelectionDialog(BuildContext context, WidgetRef ref) {
    showModalBottomSheet(
      context: context,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const SizedBox(height: 12),
            Container(
              width: 40, height: 4, 
              decoration: BoxDecoration(color: Colors.grey[300], borderRadius: BorderRadius.circular(2)),
            ),
            const SizedBox(height: 20),
            ListTile(
              leading: const Icon(Icons.brightness_auto),
              title: const Text('跟随系统'),
              onTap: () {
                ref.read(themeModeProvider.notifier).setTheme(ThemeMode.system);
                Navigator.pop(context);
              },
            ),
            ListTile(
              leading: const Icon(Icons.light_mode),
              title: const Text('浅色模式'),
              onTap: () {
                ref.read(themeModeProvider.notifier).setTheme(ThemeMode.light);
                Navigator.pop(context);
              },
            ),
            ListTile(
              leading: const Icon(Icons.dark_mode),
              title: const Text('深色模式'),
              onTap: () {
                ref.read(themeModeProvider.notifier).setTheme(ThemeMode.dark);
                Navigator.pop(context);
              },
            ),
            const SizedBox(height: 20),
          ],
        ),
      ),
    );
  }

  void _showBindPhoneDialog(BuildContext context, WidgetRef ref) {
    final phoneController = TextEditingController();
    final codeController = TextEditingController();
    
    showDialog(
      context: context,
      builder: (context) {
        bool codeSent = false;
        bool isLoading = false;
        
        return StatefulBuilder(
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
                    if (phoneController.text.isEmpty) return;
                    setState(() => isLoading = true);
                    try {
                      await ref.read(authStateProvider.notifier).sendVerificationCode(phoneController.text);
                      setState(() => codeSent = true);
                    } catch (e) {
                      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
                    } finally {
                      setState(() => isLoading = false);
                    }
                  },
                  child: isLoading ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)) : const Text('发送验证码'),
                )
              else
                ElevatedButton(
                  onPressed: isLoading ? null : () async {
                    if (codeController.text.isEmpty) return;
                    setState(() => isLoading = true);
                    try {
                      await ref.read(authStateProvider.notifier).bindPhone(phoneController.text, codeController.text);
                      Navigator.of(context).pop();
                    } catch (e) {
                      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('$e')));
                    } finally {
                      setState(() => isLoading = false);
                    }
                  },
                  child: isLoading ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2)) : const Text('绑定'),
                ),
            ],
          ),
        );
      },
    );
  }
}