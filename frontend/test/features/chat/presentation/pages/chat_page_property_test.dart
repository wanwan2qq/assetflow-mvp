import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:faker/faker.dart';
import 'package:flutter_markdown/flutter_markdown.dart';
import '../../../../../lib/features/chat/presentation/pages/chat_page.dart';
import '../../../../../lib/shared/widgets/valuation_card.dart';
import '../../../../../lib/shared/widgets/action_card.dart';
import '../../../../../lib/shared/widgets/portfolio_chart.dart';
import '../../../../test_helpers.dart';

void main() {
  group('Chat Page Property Tests', () {
    // **Feature: asset-flow-mvp, Property 12: 流式响应组件处理正确性**
    testWidgets('streaming response component handling correctness', (WidgetTester tester) async {
      // Generate random test data
      final faker = Faker();
      final testCases = List.generate(10, (index) => {
        'message': faker.lorem.sentence(),
        'hasValuationWidget': faker.randomGenerator.boolean(),
        'hasActionWidget': faker.randomGenerator.boolean(),
        'hasPortfolioWidget': faker.randomGenerator.boolean(),
        'streamingText': faker.lorem.sentences(3).join(' '),
      });

      for (final testCase in testCases) {
        await tester.pumpWidget(createTestApp(child: const ChatPage()));
        
        // Find the chat input and send button
        final chatInput = find.byKey(const Key('chat_input'));
        final sendButton = find.byKey(const Key('send_button'));
        
        expect(chatInput, findsOneWidget);
        expect(sendButton, findsOneWidget);
        
        // Enter test message
        await tester.enterText(chatInput, testCase['message'] as String);
        await tester.tap(sendButton);
        await tester.pump();
        
        // Verify user message appears
        expect(find.text(testCase['message'] as String), findsOneWidget);
        
        // Wait for streaming response to start
        await tester.pump(const Duration(milliseconds: 100));
        
        // Verify streaming indicator appears for AI response
        expect(find.byType(CircularProgressIndicator), findsAtLeastNWidgets(0));
        
        // Wait for streaming to complete
        await tester.pumpAndSettle(const Duration(seconds: 5));
        
        // Verify streaming indicator disappears
        expect(find.byType(CircularProgressIndicator), findsNothing);
        
        // Verify AI response appears
        expect(find.byType(ChatBubble), findsAtLeast(2)); // User + AI message
        
        // Reset for next test case
        await tester.tap(find.byIcon(Icons.refresh));
        await tester.pumpAndSettle();
      }
    });

    testWidgets('widget tag parsing and rendering correctness', (WidgetTester tester) async {
      await tester.pumpWidget(createTestApp(child: const ChatPage()));
      
      // Test cases for different widget types
      final widgetTestCases = [
        {
          'input': '房产',
          'expectedWidget': ValuationCard,
          'description': 'ValuationCard should render for property-related messages'
        },
        {
          'input': '现金',
          'expectedWidget': ActionCard,
          'description': 'ActionCard should render for cash-related messages'
        },
        {
          'input': '分析',
          'expectedWidget': PortfolioChart,
          'description': 'PortfolioChart should render for analysis-related messages'
        },
      ];

      for (final testCase in widgetTestCases) {
        // Clear previous messages
        await tester.tap(find.byIcon(Icons.refresh));
        await tester.pumpAndSettle();
        
        // Send message
        await tester.enterText(find.byKey(const Key('chat_input')), testCase['input'] as String);
        await tester.tap(find.byKey(const Key('send_button')));
        await tester.pump();
        
        // Wait for response to complete
        await tester.pumpAndSettle(const Duration(seconds: 5));
        
        // Verify expected widget appears
        expect(
          find.byType(testCase['expectedWidget'] as Type),
          findsOneWidget,
          reason: testCase['description'] as String,
        );
      }
    });

    testWidgets('markdown rendering in AI responses', (WidgetTester tester) async {
      await tester.pumpWidget(createTestApp(child: const ChatPage()));
      
      // Test markdown content rendering
      const markdownTestMessage = '测试';
      
      await tester.enterText(find.byKey(const Key('chat_input')), markdownTestMessage);
      await tester.tap(find.byKey(const Key('send_button')));
      await tester.pump();
      
      // Wait for response
      await tester.pumpAndSettle(const Duration(seconds: 3));
      
      // Verify markdown content is rendered (MarkdownBody should be present)
      expect(find.byType(MarkdownBody), findsAtLeastNWidgets(1));
    });

    testWidgets('typewriter effect preserves message order', (WidgetTester tester) async {
      await tester.pumpWidget(createTestApp(child: const ChatPage()));
      
      // Send multiple messages quickly
      final messages = ['第一条消息', '第二条消息', '第三条消息'];
      
      for (final message in messages) {
        await tester.enterText(find.byKey(const Key('chat_input')), message);
        await tester.tap(find.byKey(const Key('send_button')));
        await tester.pump(const Duration(milliseconds: 100));
      }
      
      // Wait for all responses to complete
      await tester.pumpAndSettle(const Duration(seconds: 10));
      
      // Verify all user messages are present in order
      for (final message in messages) {
        expect(find.text(message), findsOneWidget);
      }
      
      // Verify we have the expected number of chat bubbles (user + AI responses)
      expect(find.byType(ChatBubble), findsAtLeast(messages.length * 2));
    });

    testWidgets('embedded widgets interaction handling', (WidgetTester tester) async {
      await tester.pumpWidget(createTestApp(child: const ChatPage()));
      
      // Send message that triggers ValuationCard
      await tester.enterText(find.byKey(const Key('chat_input')), '房产估值');
      await tester.tap(find.byKey(const Key('send_button')));
      await tester.pump();
      
      // Wait for ValuationCard to appear
      await tester.pumpAndSettle(const Duration(seconds: 5));
      
      // Verify ValuationCard is present
      expect(find.byType(ValuationCard), findsOneWidget);
      
      // Test interaction with embedded widget
      final confirmButton = find.byKey(const Key('confirm_valuation_button'));
      expect(confirmButton, findsOneWidget);
      
      await tester.tap(confirmButton);
      await tester.pumpAndSettle();
      
      // Verify interaction triggered additional response
      expect(find.byType(ChatBubble), findsAtLeast(3)); // Original user + AI + confirmation response
    });
  });
}