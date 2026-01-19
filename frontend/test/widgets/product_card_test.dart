import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import '../../lib/shared/widgets/product_card.dart';

void main() {
  group('ProductCard Widget Tests', () {
    testWidgets('ProductCard displays basic information correctly', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ProductCard(
              name: '余额宝',
              provider: '天弘基金',
              category: 'investment',
              description: '低风险货币基金，随存随取',
              price: '1元起投',
              roi: '年化收益约2.5%',
              priority: 'high',
              reason: '提高资产流动性',
            ),
          ),
        ),
      );

      // Verify product information is displayed
      expect(find.text('余额宝'), findsOneWidget);
      expect(find.text('天弘基金'), findsOneWidget);
      expect(find.text('低风险货币基金，随存随取'), findsOneWidget);
      expect(find.text('1元起投'), findsOneWidget);
      expect(find.text('年化收益约2.5%'), findsOneWidget);
      expect(find.text('提高资产流动性'), findsOneWidget);
    });

    testWidgets('ProductCard shows high priority badge', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ProductCard(
              name: '推荐产品',
              provider: '服务商',
              category: 'insurance',
              description: '高优先级产品',
              priority: 'high',
            ),
          ),
        ),
      );

      // Verify high priority badge is shown
      expect(find.text('推荐'), findsOneWidget);
    });

    testWidgets('ProductCard shows correct icons for different categories', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Column(
              children: const [
                ProductCard(
                  name: '保险产品',
                  provider: '保险公司',
                  category: 'insurance',
                  description: '保险产品描述',
                ),
                ProductCard(
                  name: '投资产品',
                  provider: '投资公司',
                  category: 'investment',
                  description: '投资产品描述',
                ),
                ProductCard(
                  name: '经纪服务',
                  provider: '经纪公司',
                  category: 'broker',
                  description: '经纪服务描述',
                ),
              ],
            ),
          ),
        ),
      );

      // Verify different category icons are rendered
      expect(find.byIcon(Icons.security), findsOneWidget); // insurance
      expect(find.byIcon(Icons.trending_up), findsOneWidget); // investment
      expect(find.byIcon(Icons.person_outline), findsOneWidget); // broker
    });

    testWidgets('ProductCard shows action buttons when links provided', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ProductCard(
              name: '测试产品',
              provider: '测试服务商',
              category: 'investment',
              description: '测试描述',
              buyNowLink: 'https://example.com',
              contactInfo: const {
                'phone': '400-123-4567',
                'website': 'https://example.com'
              },
            ),
          ),
        ),
      );

      // Verify action buttons are shown
      expect(find.text('联系咨询'), findsOneWidget);
      expect(find.text('立即购买'), findsOneWidget);
    });

    testWidgets('ProductCard handles tap callbacks', (WidgetTester tester) async {
      bool tapped = false;
      bool contacted = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ProductCard(
              name: '测试产品',
              provider: '测试服务商',
              category: 'investment',
              description: '测试描述',
              contactInfo: const {'phone': '400-123-4567'},
              onTap: () => tapped = true,
              onContact: () => contacted = true,
            ),
          ),
        ),
      );

      // Test main tap
      await tester.tap(find.byType(ProductCard));
      await tester.pump();
      expect(tapped, isTrue);

      // Test contact button tap
      await tester.tap(find.text('联系咨询'));
      await tester.pump();
      expect(contacted, isTrue);
    });

    testWidgets('ProductCard displays reason in highlighted box', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: ProductCard(
              name: '测试产品',
              provider: '测试服务商',
              category: 'investment',
              description: '测试描述',
              reason: '基于您的风险分析推荐',
            ),
          ),
        ),
      );

      // Verify reason is displayed
      expect(find.text('基于您的风险分析推荐'), findsOneWidget);
      
      // Verify lightbulb icon is shown with reason
      expect(find.byIcon(Icons.lightbulb_outline), findsOneWidget);
    });
  });
}