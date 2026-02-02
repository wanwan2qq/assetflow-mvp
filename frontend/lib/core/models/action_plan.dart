import 'package:flutter/material.dart';

enum ActionPriority {
  high,
  medium,
  low,
}

enum ActionCategory {
  wealthProtection,
  wealthGrowth,
  realEstate,
  lifePlanning,
  debtOptimization,
  other,
}

class ActionStep {
  final int? id;
  final int stepNumber;
  final String action;
  final String description;
  final String expectedOutcome;
  final String timeline;
  final String status;
  final String? userNotes;
  final DateTime? completedAt;

  ActionStep({
    this.id,
    required this.stepNumber,
    required this.action,
    this.description = '',
    this.expectedOutcome = '',
    required this.timeline,
    this.status = 'pending',
    this.userNotes,
    this.completedAt,
  });

  factory ActionStep.fromJson(Map<String, dynamic> json) {
    return ActionStep(
      id: json['id'] as int?,
      stepNumber: json['step_number'] as int? ?? 0,
      action: json['action'] as String? ?? json['title'] as String? ?? '',
      description: json['description'] as String? ?? '',
      expectedOutcome: json['expected_outcome'] as String? ?? '',
      timeline: json['timeline'] as String? ?? '',
      status: json['status'] as String? ?? 'pending',
      userNotes: json['user_notes'] as String?,
      completedAt: json['completed_at'] != null 
          ? DateTime.tryParse(json['completed_at'] as String) 
          : null,
    );
  }

  ActionStep copyWith({
    int? id,
    int? stepNumber,
    String? action,
    String? description,
    String? expectedOutcome,
    String? timeline,
    String? status,
    String? userNotes,
    DateTime? completedAt,
  }) {
    return ActionStep(
      id: id ?? this.id,
      stepNumber: stepNumber ?? this.stepNumber,
      action: action ?? this.action,
      description: description ?? this.description,
      expectedOutcome: expectedOutcome ?? this.expectedOutcome,
      timeline: timeline ?? this.timeline,
      status: status ?? this.status,
      userNotes: userNotes ?? this.userNotes,
      completedAt: completedAt ?? this.completedAt,
    );
  }
}

class ActionPlan {
  final int? id;
  final String title;
  final ActionCategory category;
  final ActionPriority priority;
  final String summary;
  final List<ActionStep> steps;
  final List<String> expectedBenefits;
  final List<String> potentialRisks;
  final double confidence;
  final String status; // pending, in_progress, completed, dismissed
  final DateTime createdAt;
  final DateTime? adoptedAt;
  final DateTime? completedAt;

  ActionPlan({
    this.id,
    required this.title,
    required this.category,
    required this.priority,
    required this.summary,
    required this.steps,
    this.expectedBenefits = const [],
    this.potentialRisks = const [],
    this.confidence = 0.5,
    this.status = 'pending',
    required this.createdAt,
    this.adoptedAt,
    this.completedAt,
  });

  factory ActionPlan.fromJson(Map<String, dynamic> json) {
    // Handle steps: prioritize 'steps_list' (if returned) -> 'original_steps_snapshot' -> 'steps' (legacy)
    List<dynamic>? stepsData;
    if (json['steps_list'] != null) {
      stepsData = json['steps_list'] as List<dynamic>;
    } else if (json['original_steps_snapshot'] != null) {
      stepsData = json['original_steps_snapshot'] as List<dynamic>;
    } else if (json['steps'] != null) {
      stepsData = json['steps'] as List<dynamic>;
    }

    return ActionPlan(
      id: json['id'] as int?,
      title: json['title'] as String? ?? '未命名方案',
      category: _parseCategory(json['category'] as String?),
      priority: _parsePriority(json['priority'] as String?),
      summary: json['summary'] as String? ?? '',
      steps: stepsData
              ?.map((e) => ActionStep.fromJson(e as Map<String, dynamic>))
              .toList() ??
          [],
      expectedBenefits: (json['expected_benefits'] as List<dynamic>?)?.cast<String>() ?? [],
      potentialRisks: (json['potential_risks'] as List<dynamic>?)?.cast<String>() ?? [],
      confidence: (json['confidence'] as num?)?.toDouble() ?? 0.5,
      status: json['status'] as String? ?? 'pending',
      createdAt: DateTime.tryParse(json['created_at'] as String? ?? '') ?? DateTime.now(),
      adoptedAt: json['adopted_at'] != null 
          ? DateTime.tryParse(json['adopted_at'] as String) 
          : null,
      completedAt: json['completed_at'] != null 
          ? DateTime.tryParse(json['completed_at'] as String) 
          : null,
    );
  }

  ActionPlan copyWith({
    int? id,
    String? title,
    ActionCategory? category,
    ActionPriority? priority,
    String? summary,
    List<ActionStep>? steps,
    List<String>? expectedBenefits,
    List<String>? potentialRisks,
    double? confidence,
    String? status,
    DateTime? createdAt,
    DateTime? adoptedAt,
    DateTime? completedAt,
  }) {
    return ActionPlan(
      id: id ?? this.id,
      title: title ?? this.title,
      category: category ?? this.category,
      priority: priority ?? this.priority,
      summary: summary ?? this.summary,
      steps: steps ?? this.steps,
      expectedBenefits: expectedBenefits ?? this.expectedBenefits,
      potentialRisks: potentialRisks ?? this.potentialRisks,
      confidence: confidence ?? this.confidence,
      status: status ?? this.status,
      createdAt: createdAt ?? this.createdAt,
      adoptedAt: adoptedAt ?? this.adoptedAt,
      completedAt: completedAt ?? this.completedAt,
    );
  }

  static ActionCategory _parseCategory(String? category) {
    switch (category?.toLowerCase()) {
      case 'wealth_protection':
        return ActionCategory.wealthProtection;
      case 'wealth_growth':
        return ActionCategory.wealthGrowth;
      case 'real_estate':
        return ActionCategory.realEstate;
      case 'life_planning':
        return ActionCategory.lifePlanning;
      case 'debt_optimization':
        return ActionCategory.debtOptimization;
      // Legacy mapping
      case 'insurance':
      case 'emergency_fund':
        return ActionCategory.wealthProtection;
      case 'asset_allocation':
      case 'investment':
        return ActionCategory.wealthGrowth;
      case 'education':
      case 'retirement':
      case 'tax_planning':
        return ActionCategory.lifePlanning;
      case 'debt_management':
        return ActionCategory.debtOptimization;
      default:
        return ActionCategory.other;
    }
  }

  static ActionPriority _parsePriority(String? priority) {
    switch (priority?.toLowerCase()) {
      case 'high':
        return ActionPriority.high;
      case 'medium':
        return ActionPriority.medium;
      case 'low':
        return ActionPriority.low;
      default:
        return ActionPriority.medium;
    }
  }

  Color get priorityColor {
    switch (priority) {
      case ActionPriority.high:
        return Colors.red;
      case ActionPriority.medium:
        return Colors.orange;
      case ActionPriority.low:
        return Colors.green;
    }
  }

  String get priorityLabel {
    switch (priority) {
      case ActionPriority.high:
        return '高优先级';
      case ActionPriority.medium:
        return '中优先级';
      case ActionPriority.low:
        return '长期规划';
    }
  }
  
  String get categoryLabel {
    switch (category) {
      case ActionCategory.wealthProtection:
        return '财富保障';
      case ActionCategory.wealthGrowth:
        return '财富增值';
      case ActionCategory.realEstate:
        return '房产规划';
      case ActionCategory.lifePlanning:
        return '人生规划';
      case ActionCategory.debtOptimization:
        return '负债优化';
      case ActionCategory.other:
        return '其他';
    }
  }
}
