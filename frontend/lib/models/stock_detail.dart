class StockPricePoint {
  const StockPricePoint({required this.date, required this.close});

  factory StockPricePoint.fromJson(Map<String, dynamic> json) {
    return StockPricePoint(
      date: json['date'] as String? ?? '',
      close: (json['close'] as num?)?.toDouble() ?? 0,
    );
  }

  final String date;
  final double close;
}

class StockDetail {
  const StockDetail({
    required this.symbol,
    required this.latestClosePrice,
    required this.swingScore,
    required this.swingProbability,
    required this.swingReasons,
    required this.longTermScore,
    required this.longTermProbability,
    required this.longTermReasons,
    required this.priceHistory,
  });

  factory StockDetail.fromJson(Map<String, dynamic> json) {
    return StockDetail(
      symbol: json['symbol'] as String? ?? '',
      latestClosePrice: (json['latest_close_price'] as num?)?.toDouble() ?? 0,
      swingScore: (json['swing_score'] as num?)?.toInt() ?? 0,
      swingProbability: (json['swing_probability'] as num?)?.toDouble(),
      swingReasons:
          ((json['swing_reasons'] as List<dynamic>?) ?? <dynamic>[])
              .map((item) => item.toString())
              .toList(),
      longTermScore: (json['long_term_score'] as num?)?.toInt() ?? 0,
      longTermProbability: (json['long_term_probability'] as num?)?.toDouble(),
      longTermReasons:
          ((json['long_term_reasons'] as List<dynamic>?) ?? <dynamic>[])
              .map((item) => item.toString())
              .toList(),
      priceHistory:
          ((json['price_history'] as List<dynamic>?) ?? <dynamic>[])
              .map((item) => StockPricePoint.fromJson(item as Map<String, dynamic>))
              .toList(),
    );
  }

  final String symbol;
  final double latestClosePrice;
  final int swingScore;
  final double? swingProbability;
  final List<String> swingReasons;
  final int longTermScore;
  final double? longTermProbability;
  final List<String> longTermReasons;
  final List<StockPricePoint> priceHistory;
}

