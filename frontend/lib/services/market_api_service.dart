import 'dart:convert';

import 'package:http/http.dart' as http;

import '../constants/api_constants.dart';
import '../models/recommendations_response.dart';
import '../models/stock_detail.dart';
import 'market_api.dart';

class MarketApiService implements MarketApi {
  MarketApiService({http.Client? httpClient})
    : _httpClient = httpClient ?? http.Client();

  final http.Client _httpClient;

  @override
  Future<RecommendationsResponse> fetchRecommendations({String group = 'all'}) async {
    final uri = Uri.parse('$baseUrl/recommendations').replace(
      queryParameters: group == 'all' ? null : <String, String>{'group': group},
    );

    final response = await _httpClient.get(uri);
    final json = _readJson(response);
    return RecommendationsResponse.fromJson(json);
  }

  @override
  Future<StockDetail> fetchStockDetail(String symbol) async {
    final response = await _httpClient.get(
      Uri.parse('$baseUrl/stocks/$symbol'),
    );
    final json = _readJson(response);
    return StockDetail.fromJson(json);
  }

  Map<String, dynamic> _readJson(http.Response response) {
    final body = utf8.decode(response.bodyBytes);

    if (response.statusCode < 200 || response.statusCode >= 300) {
      throw Exception(body.isEmpty ? 'Request failed.' : body);
    }

    final decoded = jsonDecode(body);
    if (decoded is! Map<String, dynamic>) {
      throw const FormatException('Invalid response format.');
    }

    return decoded;
  }
}

