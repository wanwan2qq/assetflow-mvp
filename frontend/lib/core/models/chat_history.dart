import 'package:json_annotation/json_annotation.dart';

part 'chat_history.g.dart';

@JsonSerializable()
class ChatHistoryResponse {
  final List<ChatHistoryMessage> messages;
  final int total;

  ChatHistoryResponse({
    required this.messages,
    required this.total,
  });

  factory ChatHistoryResponse.fromJson(Map<String, dynamic> json) =>
      _$ChatHistoryResponseFromJson(json);

  Map<String, dynamic> toJson() => _$ChatHistoryResponseToJson(this);
}

@JsonSerializable()
class ChatHistoryMessage {
  final int id;
  final String role;
  final String content;
  @JsonKey(name: 'meta_data')
  final Map<String, dynamic>? metaData;
  final String timestamp;

  ChatHistoryMessage({
    required this.id,
    required this.role,
    required this.content,
    this.metaData,
    required this.timestamp,
  });

  factory ChatHistoryMessage.fromJson(Map<String, dynamic> json) =>
      _$ChatHistoryMessageFromJson(json);

  Map<String, dynamic> toJson() => _$ChatHistoryMessageToJson(this);

  bool get isUser => role == 'user';
  bool get isAI => role == 'ai';

  DateTime get parsedTimestamp => DateTime.parse(timestamp);

  List<WidgetData>? get widgets {
    if (metaData == null || metaData!['widgets'] == null) return null;
    
    final widgetsList = metaData!['widgets'] as List<dynamic>;
    return widgetsList
        .map((w) => WidgetData.fromJson(w as Map<String, dynamic>))
        .toList();
  }
}

@JsonSerializable()
class WidgetData {
  @JsonKey(name: 'widget_type')
  final String widgetType;
  final Map<String, dynamic> data;

  WidgetData({
    required this.widgetType,
    required this.data,
  });

  factory WidgetData.fromJson(Map<String, dynamic> json) =>
      _$WidgetDataFromJson(json);

  Map<String, dynamic> toJson() => _$WidgetDataToJson(this);
}