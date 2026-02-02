import 'package:dio/dio.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import '../models/action_plan.dart';
import 'api_service.dart';

part 'action_plan_service.g.dart';

class ActionPlanService {
  final Dio _dio;
  
  ActionPlanService(this._dio);
  
  Future<List<ActionPlan>> getPlans({String? status, String? category}) async {
    try {
      final response = await _dio.get('/api/v1/plans', queryParameters: {
          if (status != null) 'status': status,
          if (category != null) 'category': category,
      });
      return (response.data as List).map((e) => ActionPlan.fromJson(e)).toList();
    } catch (e) {
      print('❌ Error getting plans: $e');
      return [];
    }
  }
  
  Future<Map<String, dynamic>> getStats() async {
    try {
      final response = await _dio.get('/api/v1/plans/stats');
      return response.data as Map<String, dynamic>;
    } catch (e) {
        print('❌ Error getting plan stats: $e');
        return {};
    }
  }

  Future<ActionPlan?> getPlan(int id) async {
    try {
      final response = await _dio.get('/api/v1/plans/$id');
      return ActionPlan.fromJson(response.data);
    } catch (e) {
      print('❌ Error getting plan: $e');
      return null;
    }
  }
  
  Future<ActionPlan?> adoptPlan(int id) async {
    try {
      final response = await _dio.post('/api/v1/plans/$id/adopt');
      return ActionPlan.fromJson(response.data);
    } catch (e) {
      print('❌ Error adopting plan: $e');
      return null;
    }
  }
  
  Future<bool> dismissPlan(int id, {String? reason}) async {
    try {
      await _dio.post('/api/v1/plans/$id/dismiss', data: {
        'reason': reason,
      });
      return true;
    } catch (e) {
      print('❌ Error dismissing plan: $e');
      return false;
    }
  }
  
  Future<bool> updateStepStatus(int planId, int stepId, String status, {String? notes}) async {
    try {
      await _dio.patch('/api/v1/plans/$planId/steps/$stepId', queryParameters: {
          'status': status,
          if (notes != null) 'notes': notes,
      });
      return true;
    } catch (e) {
      print('❌ Error updating step status: $e');
      return false;
    }
  }
}

@riverpod
ActionPlanService actionPlanService(ActionPlanServiceRef ref) {
    final dio = ref.watch(dioProvider);
    return ActionPlanService(dio);
}
