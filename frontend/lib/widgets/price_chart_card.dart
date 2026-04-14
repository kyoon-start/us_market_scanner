import 'dart:math' as math;

import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';

import '../models/stock_detail.dart';

class PriceChartCard extends StatelessWidget {
  const PriceChartCard({super.key, required this.priceHistory});

  final List<StockPricePoint> priceHistory;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final points = priceHistory.length > 30
        ? priceHistory.sublist(priceHistory.length - 30)
        : priceHistory;

    if (points.length < 2) {
      return const SizedBox.shrink();
    }

    final minPrice = points.map((point) => point.close).reduce(math.min);
    final maxPrice = points.map((point) => point.close).reduce(math.max);
    final range = maxPrice - minPrice;
    final paddedMin = range == 0 ? minPrice - 1 : minPrice - (range * 0.08);
    final paddedMax = range == 0 ? maxPrice + 1 : maxPrice + (range * 0.08);
    final isPositive = points.last.close >= points.first.close;
    final lineColor = isPositive
        ? const Color(0xFF059669)
        : const Color(0xFFDC2626);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              'Price Trend',
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              'Last ${points.length} trading days',
              style: theme.textTheme.bodySmall?.copyWith(
                color: const Color(0xFF64748B),
              ),
            ),
            const SizedBox(height: 16),
            SizedBox(
              height: 180,
              child: LineChart(
                LineChartData(
                  minX: 0,
                  maxX: (points.length - 1).toDouble(),
                  minY: paddedMin,
                  maxY: paddedMax,
                  gridData: FlGridData(
                    show: true,
                    drawVerticalLine: false,
                    horizontalInterval: (paddedMax - paddedMin) / 3,
                    getDrawingHorizontalLine: (double value) {
                      return const FlLine(
                        color: Color(0xFFE2E8F0),
                        strokeWidth: 1,
                      );
                    },
                  ),
                  borderData: FlBorderData(show: false),
                  titlesData: const FlTitlesData(
                    topTitles: AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                    rightTitles: AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                    leftTitles: AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                    bottomTitles: AxisTitles(
                      sideTitles: SideTitles(showTitles: false),
                    ),
                  ),
                  lineTouchData: const LineTouchData(enabled: false),
                  lineBarsData: <LineChartBarData>[
                    LineChartBarData(
                      isCurved: true,
                      color: lineColor,
                      barWidth: 3,
                      isStrokeCapRound: true,
                      dotData: const FlDotData(show: false),
                      belowBarData: BarAreaData(
                        show: true,
                        gradient: LinearGradient(
                          begin: Alignment.topCenter,
                          end: Alignment.bottomCenter,
                          colors: <Color>[
                            lineColor.withValues(alpha: 0.22),
                            lineColor.withValues(alpha: 0.02),
                          ],
                        ),
                      ),
                      spots: List<FlSpot>.generate(
                        points.length,
                        (int index) => FlSpot(
                          index.toDouble(),
                          points[index].close,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            Row(
              children: <Widget>[
                Text(
                  points.first.date,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: const Color(0xFF64748B),
                  ),
                ),
                const Spacer(),
                Text(
                  points.last.date,
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: const Color(0xFF64748B),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
