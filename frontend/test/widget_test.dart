import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'package:frontend/models/recommendations_response.dart';
import 'package:frontend/models/stock_detail.dart';
import 'package:frontend/root/app_shell.dart';
import 'package:frontend/screens/stock_detail_screen.dart';
import 'package:frontend/services/market_api.dart';

class FakeMarketApi implements MarketApi {
  @override
  Future<RecommendationsResponse> fetchRecommendations({
    String group = 'all',
  }) async {
    return RecommendationsResponse.fromJson(<String, dynamic>{
      'swing': <Map<String, dynamic>>[
        <String, dynamic>{
          'symbol': 'AAPL',
          'score': 95,
          'probability': 0.82,
          'reason': <String>['Strong momentum'],
        },
      ],
      'long': <Map<String, dynamic>>[
        <String, dynamic>{
          'symbol': 'MSFT',
          'score': 90,
          'probability': 0.78,
          'reason': <String>['Healthy trend'],
        },
      ],
    });
  }

  @override
  Future<StockDetail> fetchStockDetail(String symbol) async {
    return StockDetail.fromJson(<String, dynamic>{
      'symbol': symbol,
      'latest_close_price': 123.45,
      'swing_score': 88,
      'swing_probability': 0.75,
      'swing_reasons': <String>['Momentum'],
      'long_term_score': 91,
      'long_term_probability': 0.8,
      'long_term_reasons': <String>['Trend'],
      'price_history': <Map<String, dynamic>>[
        <String, dynamic>{'date': '2026-03-01', 'close': 120.0},
        <String, dynamic>{'date': '2026-03-31', 'close': 123.45},
      ],
    });
  }
}

void main() {
  testWidgets('home screen shows recommendation sections', (
    WidgetTester tester,
  ) async {
    SharedPreferences.setMockInitialValues(<String, Object>{});

    await tester.pumpWidget(USMarketScannerApp(api: FakeMarketApi()));
    await tester.pumpAndSettle();

    expect(find.text('US Market Scanner'), findsOneWidget);
    expect(find.text('Swing Best 3'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('Long-term Best 3'),
      300,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('Long-term Best 3'), findsOneWidget);
    expect(find.text('AAPL'), findsOneWidget);
    expect(find.text('MSFT'), findsOneWidget);
  });

  testWidgets('stock detail screen shows refined analysis cards', (
    WidgetTester tester,
  ) async {
    SharedPreferences.setMockInitialValues(<String, Object>{});

    await tester.pumpWidget(
      MaterialApp(
        home: StockDetailScreen(symbol: 'AAPL', api: FakeMarketApi()),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Symbol'), findsOneWidget);
    expect(find.text('Latest Close'), findsOneWidget);
    expect(find.text('\$123.45'), findsOneWidget);
    expect(find.text('Swing Analysis'), findsOneWidget);
    await tester.scrollUntilVisible(
      find.text('Long-term Analysis'),
      300,
      scrollable: find.byType(Scrollable).first,
    );
    expect(find.text('Long-term Analysis'), findsOneWidget);
    expect(find.text('Probability'), findsNWidgets(2));
    expect(find.text('Reasons'), findsNWidgets(2));
    expect(find.text('Momentum'), findsOneWidget);
    expect(find.text('Trend'), findsOneWidget);
  });
}
