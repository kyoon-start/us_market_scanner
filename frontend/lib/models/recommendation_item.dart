class RecommendationItem {
  const RecommendationItem({
    required this.symbol,
    required this.score,
    required this.probability,
    required this.reasons,
  });

  factory RecommendationItem.fromJson(Map<String, dynamic> json) {
    return RecommendationItem(
      symbol: json['symbol'] as String? ?? '',
      score: (json['score'] as num?)?.toInt() ?? 0,
      probability: (json['probability'] as num?)?.toDouble(),
      reasons:
          ((json['reason'] as List<dynamic>?) ?? <dynamic>[])
              .map((item) => item.toString())
              .toList(),
    );
  }

  final String symbol;
  final int score;
  final double? probability;
  final List<String> reasons;
}
