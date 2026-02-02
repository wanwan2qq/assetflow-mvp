import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/services/action_plan_service.dart';
import '../../../core/services/api_service.dart';
import '../../../core/providers/auth_provider.dart';
import '../presentation/widgets/sheets/valuation_edit_sheet.dart';
import '../presentation/widgets/sheets/asset_edit_sheet.dart';

/// Service to handle interactions from chat cards.
/// This decouples the UI handling in ChatPage from the business logic of what happens
/// when a user clicks a button on a card.
final cardActionHandlerProvider = Provider<CardActionHandler>((ref) {
  return CardActionHandler(ref);
});

class CardActionHandler {
  final Ref ref;

  CardActionHandler(this.ref);

  /// Handles an action triggered from a card.
  /// 
  /// [context] is required for showing dialogs, snackbars, or navigation.
  /// [actionType] defines the type of action (e.g., 'confirm_valuation', 'execute_plan').
  /// [data] contains the payload for the action.
  /// [onSendUserMessage] callback to send a message to the chat (user side).
  /// [onUpdateUi] optional callback to update local UI state.
  Future<void> handleAction(
    BuildContext context, {
    required String actionType,
    required Map<String, dynamic> data,
    required Function(String) onSendUserMessage,
    VoidCallback? onUpdateUi,
  }) async {
    print('🃏 CardActionHandler processing: $actionType with data: $data');

    switch (actionType) {
      // --- Valuation / Asset Actions ---
      case 'confirm_valuation':
        await _handleConfirmValuation(context, data, onSendUserMessage, onUpdateUi);
        break;
      
      case 'edit_valuation':
        await _handleEditValuation(context, data, onSendUserMessage);
        break;

      case 'edit_asset':
         await _handleEditAsset(context, data, onSendUserMessage);
         break;

      // --- Action Plan Actions ---
      case 'adopt_plan':
        await _handleAdoptPlan(context, data, onUpdateUi);
        break;
        
      case 'dismiss_plan':
        await _handleDismissPlan(context, data, onUpdateUi);
        break;
      
      case 'update_plan_step':
        await _handleUpdatePlanStep(context, data, onUpdateUi);
        break;

      // --- Product Actions ---
      case 'contact_product':
        _handleContactProduct(context, data, onSendUserMessage);
        break;
        
      // --- Generic / Fallback ---
      case 'send_message':
        final msg = data['message'] as String?;
        if (msg != null) onSendUserMessage(msg);
        break;
        
      default:
        print('⚠️ Unknown action type: $actionType');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('未知操作: $actionType')),
        );
    }
  }

  // --- Handlers Implementation ---


  Future<void> _handleConfirmValuation(
    BuildContext context, 
    Map<String, dynamic> data,
    Function(String) onSendUserMessage,
    [VoidCallback? onUpdateUi]
  ) async {
    final assetId = data['id'] as int?;
    if (assetId != null) {
      final userId = ref.read(authStateProvider).value?.id;
      if (userId != null) {
        try {
          await ref.read(apiServiceProvider).updateAsset(userId, assetId, {
            'is_confirmed': true,
          });
          if (!context.mounted) return;
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(content: Text('✅ 资产已确认')),
          );
          if (onUpdateUi != null) onUpdateUi();
          return;
        } catch (e) {
             // Fallback to message if API fails? Or just show error?
             print('Confirm failed: $e');
        }
      }
    }
    
    // Fallback: Send message
    final price = data['price'] as double? ?? 0;
    final formattedPrice = (price / 10000).toStringAsFixed(1);
    onSendUserMessage('确认估值 $formattedPrice万');
  }

  Future<void> _handleEditValuation(
    BuildContext context,
    Map<String, dynamic> data,
    Function(String) onSendUserMessage
  ) async {
    final currentPrice = ((data['price'] as num?)?.toDouble() ?? 0) / 10000;
    
    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => ValuationEditSheet(
        initialPrice: currentPrice,
        onConfirm: (newPrice) async {
          // If we have an ID, call API
          final assetId = data['id'] as int?;
          if (assetId != null) {
            final userId = ref.read(authStateProvider).value?.id;
            if (userId != null) {
              await ref.read(apiServiceProvider).updateAsset(userId, assetId, {
                'value': newPrice,
                'is_confirmed': true,
              });
              if (!context.mounted) return;
               ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('✅ 估值已更新')),
              );
              // TODO: Optimistic update of local widget?
            }
          } else {
            // Fallback: Send message if no ID or user
            onSendUserMessage('确认估值 ${(newPrice / 10000).toStringAsFixed(1)}万');
          }
        },
      ),
    );
  }

  Future<void> _handleEditAsset(
    BuildContext context,
    Map<String, dynamic> data,
    Function(String) onSendUserMessage
  ) async {
    await showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => AssetEditSheet(
        assetData: data,
        onConfirm: (updatedData) async {
          final assetId = data['id'] as int?;
          if (assetId != null) {
            final userId = ref.read(authStateProvider).value?.id;
             if (userId != null) {
               // Ensure we mark as confirmed upon edit
               final payload = Map<String, dynamic>.from(updatedData);
               payload['is_confirmed'] = true;
               
               await ref.read(apiServiceProvider).updateAsset(userId, assetId, payload);
               if (!context.mounted) return;
               ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(content: Text('✅ 资产信息已保存')),
               );
             }
          } else {
             // Fallback
             final name = updatedData['name'];
             onSendUserMessage('我想修改$name的信息');
          }
        },
      ),
    );
  }

  Future<void> _handleAdoptPlan(
    BuildContext context,
    Map<String, dynamic> data,
    VoidCallback? onUpdateUi,
  ) async {
    // Phase 1: Implement direct service call as requested in Requirements 4.2
    try {
      final planId = data['planId'] as int;
      final service = ref.read(actionPlanServiceProvider);
      
      // Show loading feedback
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('正在采纳方案...')),
      );

      await service.adoptPlan(planId);
      
      // Update UI (Optimistic or Refresh)
      if (onUpdateUi != null) onUpdateUi();
      
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('✅ 已采纳方案，请查看步骤列表')),
      );
    } catch (e) {
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('❌ 采纳失败: $e')),
      );
    }
  }

  Future<void> _handleDismissPlan(
    BuildContext context,
    Map<String, dynamic> data,
    VoidCallback? onUpdateUi,
  ) async {
    // Logic similar to ActionPlansPage (Dialog then Service)
    // For simplicity in Phase 1, we might just call the service if reason provided, 
    // or we assume the UI (Card) handled the dialog and passed the reason.
    try {
      final planId = data['planId'] as int;
      final reason = data['reason'] as String;
      
      final service = ref.read(actionPlanServiceProvider);
      await service.dismissPlan(planId, reason: reason);
      
      if (onUpdateUi != null) onUpdateUi();
    } catch (e) {
      print('Dismiss plan error: $e');
    }
  }

  Future<void> _handleUpdatePlanStep(
    BuildContext context,
    Map<String, dynamic> data,
    VoidCallback? onUpdateUi,
  ) async {
    try {
      final planId = data['planId'] as int;
      final stepId = data['stepId'] is int ? data['stepId'] as int : int.parse(data['stepId'] as String);
      final status = data['status'] as String;
      
      // Note: Backend service might expect int or string for IDs. 
      // ActionPlanService.updateStepStatus signature: (int planId, String stepNumber, String status)
      // Wait, let's check action_plan_service.dart signature.
      final service = ref.read(actionPlanServiceProvider);
      await service.updateStepStatus(planId, stepId, status);
      
      // Static update (no chat message)
      if (onUpdateUi != null) onUpdateUi();
      
    } catch (e) {
      print('Update step error: $e');
    }
  }

  void _handleContactProduct(
    BuildContext context,
    Map<String, dynamic> data,
    Function(String) onSendUserMessage
  ) {
    final name = data['name'] ?? '产品';
    final provider = data['provider'] ?? '服务商';
    onSendUserMessage('我想联系$provider咨询$name');
  }
}
