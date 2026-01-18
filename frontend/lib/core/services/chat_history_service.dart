import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../models/chat_history.dart';
import 'api_service.dart';

part 'chat_history_service.g.dart';

@riverpod
class ChatHistoryService extends _$ChatHistoryService {
  @override
  FutureOr<ChatHistoryResponse?> build() {
    return null;
  }

  Future<ChatHistoryResponse> loadChatHistory({int limit = 50}) async {
    final apiService = ref.read(apiServiceProvider);
    
    try {
      final response = await apiService.getChatHistory(limit: limit);
      final chatHistory = ChatHistoryResponse.fromJson(response.data);
      
      // Update the state with the loaded history
      state = AsyncValue.data(chatHistory);
      
      return chatHistory;
    } catch (error, stackTrace) {
      state = AsyncValue.error(error, stackTrace);
      rethrow;
    }
  }

  void clearHistory() {
    state = const AsyncValue.data(null);
  }
}