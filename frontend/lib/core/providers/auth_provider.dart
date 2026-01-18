import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../models/user.dart';
import '../services/api_service.dart';
import '../services/token_storage_service.dart';

part 'auth_provider.g.dart';

@riverpod
class AuthState extends _$AuthState {
  @override
  AsyncValue<User?> build() {
    // 异步初始化认证状态
    _initializeAuthState();
    return const AsyncValue.loading();
  }
  
  /// 异步初始化认证状态
  Future<void> _initializeAuthState() async {
    try {
      print('🔄 初始化认证状态...');
      
      // 从持久化存储中恢复认证数据
      final tokenStorage = TokenStorageService.instance;
      final hasAuthData = await tokenStorage.hasAuthData();
      
      if (hasAuthData) {
        final token = await tokenStorage.getToken();
        final user = await tokenStorage.getUser();
        
        if (token != null && user != null) {
          print('✅ 从存储中恢复登录状态');
          print('   用户: ${user.phone}');
          print('   Token: ${token.substring(0, 20)}...');
          
          // 更新内存中的状态（保持向后兼容）
          _currentToken = token;
          _currentUser = user;
          
          state = AsyncValue.data(user);
          return;
        }
      }
      
      print('ℹ️ 没有存储的认证数据，用户未登录');
      state = const AsyncValue.data(null);
      
    } catch (e) {
      print('❌ 初始化认证状态失败: $e');
      state = AsyncValue.error(e, StackTrace.current);
    }
  }

  Future<void> sendVerificationCode(String phone) async {
    try {
      final apiService = ref.read(apiServiceProvider);
      
      // 调用后端发送验证码API
      final response = await apiService.sendSms(phone);
      
      if (response.statusCode != 200) {
        throw Exception('发送验证码失败');
      }
    } catch (error) {
      rethrow;
    }
  }

  Future<void> login(String phone, String verificationCode) async {
    state = const AsyncValue.loading();
    
    try {
      // 强制清除所有旧的认证信息
      _clearToken();
      
      print('🔐 开始登录: $phone');
      print('🗑️ 已清除旧的认证信息');
      
      // 调用后端登录API
      final apiService = ref.read(apiServiceProvider);
      final response = await apiService.loginWithPhone(phone, verificationCode);
      
      print('📡 登录响应状态码: ${response.statusCode}');
      print('📡 登录响应数据: ${response.data}');
      
      if (response.statusCode == 200) {
        final authData = response.data;
        final user = User(
          id: authData['user_id'],
          phone: authData['phone'],
          createdAt: DateTime.now(),
        );
        
        print('👤 创建用户对象: ${user.toString()}');
        print('🆔 用户ID: ${user.id}');
        print('📱 手机号: ${user.phone}');
        
        // 存储token和用户信息到持久化存储
        final tokenStorage = TokenStorageService.instance;
        await tokenStorage.storeAuthData(authData['access_token'], user);
        
        // 同时更新内存中的状态（保持向后兼容）
        _storeToken(authData['access_token']);
        _currentUser = user;
        
        print('🔑 Token已存储到持久化存储和内存');
        
        // 强制触发状态更新
        state = AsyncValue.data(user);
        print('✅ 登录状态已更新');
        
        // 验证新token和用户信息是否正确存储
        print('🔍 验证: 当前token前缀: ${_currentToken?.substring(0, 20)}...');
        print('🔍 验证: 当前用户ID: ${_currentUser?.id}');
        print('🔍 验证: 当前手机号: ${_currentUser?.phone}');
        
        // 额外的状态刷新，确保所有监听器都能收到更新
        await Future.delayed(const Duration(milliseconds: 100));
        state = AsyncValue.data(user);
        print('🔄 状态已二次刷新确保更新');
        
      } else {
        throw Exception('登录失败: HTTP ${response.statusCode}');
      }
    } catch (error, stackTrace) {
      print('❌ 登录异常: $error');
      print('📍 堆栈跟踪: $stackTrace');
      state = AsyncValue.error(error, stackTrace);
    }
  }

  Future<void> loginAnonymously(String deviceId) async {
    state = const AsyncValue.loading();
    
    try {
      final apiService = ref.read(apiServiceProvider);
      
      // 调用后端匿名登录API
      final response = await apiService.loginWithDevice(deviceId);
      
      if (response.statusCode == 200) {
        final authData = response.data;
        final user = User(
          id: authData['user_id'],
          phone: authData['phone'],
          deviceId: deviceId,
          createdAt: DateTime.now(),
        );
        
        // 存储token和用户信息
        _storeToken(authData['access_token']);
        _currentUser = user;
        
        state = AsyncValue.data(user);
      } else {
        throw Exception('匿名登录失败');
      }
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
    }
  }

  Future<void> bindPhone(String phone, String verificationCode) async {
    try {
      
      print('🔗 开始绑定手机号: $phone');
      
      // 调用后端绑定手机号API
      final apiService = ref.read(apiServiceProvider);
      final response = await apiService.bindPhone(phone, verificationCode);
      
      print('📡 绑定响应状态码: ${response.statusCode}');
      print('📡 绑定响应数据: ${response.data}');
      
      if (response.statusCode == 200) {
        final authData = response.data;
        final user = User(
          id: authData['user_id'],
          phone: authData['phone'],
          deviceId: authData['device_id'],
          createdAt: DateTime.now(),
        );
        
        print('👤 更新用户对象: ${user.toString()}');
        
        // 更新token和用户信息
        _storeToken(authData['access_token']);
        _currentUser = user;
        print('🔑 Token已更新');
        
        state = AsyncValue.data(user);
        print('✅ 绑定状态已更新');
      } else {
        throw Exception('绑定失败: HTTP ${response.statusCode}');
      }
    } catch (error, stackTrace) {
      print('❌ 绑定异常: $error');
      rethrow;
    }
  }

  Future<void> logout() async {
    print('🚪 开始登出...');
    
    // 清除持久化存储
    final tokenStorage = TokenStorageService.instance;
    await tokenStorage.clearAuthData();
    
    // 清除内存状态
    _clearToken();
    _currentUser = null;
    state = const AsyncValue.data(null);
    
    print('✅ 登出完成');
  }
  
  void _storeToken(String token) {
    // 存储到内存（保持向后兼容）
    _currentToken = token;
    print('🔑 Token已更新到内存: ${token.substring(0, 20)}...');
  }
  
  void _clearToken() {
    print('🗑️ 清除内存中的Token和用户信息');
    _currentToken = null;
    _currentUser = null;
    
    // 强制触发provider更新
    state = const AsyncValue.data(null);
  }
  
  // 调试方法：检查当前token状态
  void debugTokenState() {
    print('=== Token调试信息 ===');
    print('当前token: ${_currentToken?.substring(0, 30)}...' ?? 'null');
    print('当前用户: ${_currentUser?.toString() ?? 'null'}');
    print('Token长度: ${_currentToken?.length ?? 0}');
    
    if (_currentToken != null) {
      // 检查token格式
      final parts = _currentToken!.split('.');
      print('JWT格式: ${parts.length == 3 ? '有效' : '无效'} (${parts.length}部分)');
      
      // 检查token是否过期（简单检查）
      try {
        final payload = parts[1];
        // 这里可以添加更详细的token解析，但现在只是基本检查
        print('Token payload长度: ${payload.length}');
      } catch (e) {
        print('Token解析错误: $e');
      }
    }
    print('==================');
  }
  
  // 强制刷新token的方法（用于调试）
  void forceTokenRefresh() {
    print('🔄 强制刷新token状态...');
    final currentState = state;
    if (currentState.value != null) {
      // 触发状态更新，这会通知所有监听器
      state = AsyncValue.data(currentState.value);
      print('✅ Token状态已刷新');
    }
  }
}

// 临时存储token和用户信息的变量，实际应该使用secure storage
String? _currentToken;
User? _currentUser;

// 导出token访问器供其他模块使用
String? getCurrentToken() => _currentToken;
User? getCurrentUser() => _currentUser;

@riverpod
Future<String?> authToken(AuthTokenRef ref) async {
  // 优先从内存获取（快速访问）
  if (_currentToken != null) {
    return _currentToken;
  }
  
  // 从持久化存储获取
  final tokenStorage = TokenStorageService.instance;
  final token = await tokenStorage.getToken();
  
  // 同步到内存中
  if (token != null) {
    _currentToken = token;
  }
  
  return token;
}

@riverpod
bool isAuthenticated(IsAuthenticatedRef ref) {
  final authState = ref.watch(authStateProvider);
  return authState.when(
    data: (user) => user != null,
    loading: () => false,
    error: (_, __) => false,
  );
}