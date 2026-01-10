import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import '../../../lib/shared/widgets/action_card.dart';

void main() {
  group('ActionCard Tests', () {
    testWidgets('should render insurance card correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ActionCard(
              type: ActionCardType.insurance,
              title: '保险保障建议',
              description: '建议配置重疾险和意外险',
              provider: '平安保险',
              contactInfo: '400-123-4567',
            ),
          ),
        ),
      );

      expect(find.text('保险保障建议'), findsOneWidget);
      expect(find.text('建议配置重疾险和意外险'), findsOneWidget);
      expect(find.text('平安保险'), findsOneWidget);
      expect(find.text('400-123-4567'), findsOneWidget);
      expect(find.byIcon(Icons.security), findsOneWidget);
    });

    testWidgets('should render broker card correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ActionCard(
              type: ActionCardType.broker,
              title: '理财顾问推荐',
              description: '专业理财师为您定制投资方案',
              provider: '招商银行',
              contactInfo: '张经理 138-0013-8000',
            ),
          ),
        ),
      );

      expect(find.text('理财顾问推荐'), findsOneWidget);
      expect(find.text('专业理财师为您定制投资方案'), findsOneWidget);
      expect(find.text('招商银行'), findsOneWidget);
      expect(find.text('张经理 138-0013-8000'), findsOneWidget);
      expect(find.byIcon(Icons.person_outline), findsOneWidget);
    });

    testWidgets('should render investment card correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ActionCard(
              type: ActionCardType.investment,
              title: '投资产品推荐',
              description: '稳健型基金组合，年化收益6-8%',
              provider: '天天基金',
              contactInfo: 'www.1234567.com.cn',
            ),
          ),
        ),
      );

      expect(find.text('投资产品推荐'), findsOneWidget);
      expect(find.text('稳健型基金组合，年化收益6-8%'), findsOneWidget);
      expect(find.text('天天基金'), findsOneWidget);
      expect(find.text('www.1234567.com.cn'), findsOneWidget);
      expect(find.byIcon(Icons.trending_up), findsOneWidget);
    });

    testWidgets('should render warning card correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ActionCard(
              type: ActionCardType.warning,
              title: '流动性风险警告',
              description: '您的现金储备不足，建议增加流动资金',
            ),
          ),
        ),
      );

      expect(find.text('流动性风险警告'), findsOneWidget);
      expect(find.text('您的现金储备不足，建议增加流动资金'), findsOneWidget);
      expect(find.byIcon(Icons.warning), findsOneWidget);
    });

    testWidgets('should handle tap events correctly', (tester) async {
      bool tapped = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ActionCard(
              type: ActionCardType.insurance,
              title: '保险保障建议',
              description: '建议配置重疾险和意外险',
              onTap: () => tapped = true,
            ),
          ),
        ),
      );

      await tester.tap(find.byType(ActionCard));
      await tester.pumpAndSettle();

      expect(tapped, isTrue);
    });

    testWidgets('should show chevron icon when onTap is provided', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ActionCard(
              type: ActionCardType.insurance,
              title: '保险保障建议',
              description: '建议配置重疾险和意外险',
              onTap: () {},
            ),
          ),
        ),
      );

      expect(find.byIcon(Icons.chevron_right), findsOneWidget);
    });

    testWidgets('should not show chevron icon when onTap is null', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ActionCard(
              type: ActionCardType.insurance,
              title: '保险保障建议',
              description: '建议配置重疾险和意外险',
            ),
          ),
        ),
      );

      expect(find.byIcon(Icons.chevron_right), findsNothing);
    });

    testWidgets('should not show provider and contact info when null', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ActionCard(
              type: ActionCardType.warning,
              title: '风险警告',
              description: '这是一个风险警告',
            ),
          ),
        ),
      );

      expect(find.byIcon(Icons.business), findsNothing);
      expect(find.byIcon(Icons.contact_phone), findsNothing);
    });

    testWidgets('should use correct colors for different card types', (tester) async {
      // Test insurance card color
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ActionCard(
              type: ActionCardType.insurance,
              title: '保险',
              description: '描述',
            ),
          ),
        ),
      );

      final insuranceIcon = tester.widget<Icon>(find.byIcon(Icons.security));
      expect(insuranceIcon.color, equals(Colors.blue));

      // Test broker card color
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ActionCard(
              type: ActionCardType.broker,
              title: '理财师',
              description: '描述',
            ),
          ),
        ),
      );

      final brokerIcon = tester.widget<Icon>(find.byIcon(Icons.person_outline));
      expect(brokerIcon.color, equals(Colors.green));

      // Test investment card color
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ActionCard(
              type: ActionCardType.investment,
              title: '投资',
              description: '描述',
            ),
          ),
        ),
      );

      final investmentIcon = tester.widget<Icon>(find.byIcon(Icons.trending_up));
      expect(investmentIcon.color, equals(Colors.orange));

      // Test warning card color
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ActionCard(
              type: ActionCardType.warning,
              title: '警告',
              description: '描述',
            ),
          ),
        ),
      );

      final warningIcon = tester.widget<Icon>(find.byIcon(Icons.warning));
      expect(warningIcon.color, equals(Colors.red));
    });
  });
}