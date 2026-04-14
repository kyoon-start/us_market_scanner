import '../models/recommendations_response.dart';
import '../models/stock_detail.dart';

abstract class MarketApi {
  Future<RecommendationsResponse> fetchRecommendations({String group = 'all'});

  Future<StockDetail> fetchStockDetail(String symbol);
}

