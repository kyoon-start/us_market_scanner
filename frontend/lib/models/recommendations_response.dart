import 'recommendation_item.dart';

class RecommendationsResponse {
  const RecommendationsResponse({required this.swing, required this.longTerm});

  factory RecommendationsResponse.fromJson(Map<String, dynamic> json) {
    return RecommendationsResponse(
      swing:
          ((json['swing'] as List<dynamic>?) ?? <dynamic>[])
              .map(
                (item) =>
                    RecommendationItem.fromJson(item as Map<String, dynamic>),
              )
              .toList(),
      longTerm:
          ((json['long'] as List<dynamic>?) ?? <dynamic>[])
              .map(
                (item) =>
                    RecommendationItem.fromJson(item as Map<String, dynamic>),
              )
              .toList(),
    );
  }

  final List<RecommendationItem> swing;
  final List<RecommendationItem> longTerm;
}
