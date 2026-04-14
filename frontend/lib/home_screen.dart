import 'package:flutter/material.dart';

import 'models/recommendation_item.dart';
import 'models/recommendations_response.dart';
import 'screens/stock_detail_screen.dart';
import 'services/favorites_store.dart';
import 'services/market_api.dart';
import 'widgets/error_state.dart';
import 'widgets/recommendation_card.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key, required this.api});

  final MarketApi api;

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final FavoritesStore _favoritesStore = FavoritesStore.instance;
  final Map<String, RecommendationsResponse> _responseCache =
      <String, RecommendationsResponse>{};

  late Future<RecommendationsResponse> _future;
  MarketGroup _selectedGroup = MarketGroup.values.first;

  @override
  void initState() {
    super.initState();
    _future = _loadRecommendations();
    _favoritesStore.ensureLoaded();
  }

  Future<RecommendationsResponse> _loadRecommendations({
    bool forceRefresh = false,
  }) {
    if (!forceRefresh) {
      final cached = _responseCache[_selectedGroup.id];
      if (cached != null) {
        return Future<RecommendationsResponse>.value(cached);
      }
    }

    final future = widget.api
        .fetchRecommendations(group: _selectedGroup.id)
        .then((response) {
          _responseCache[_selectedGroup.id] = response;
          return response;
        });
    return future;
  }

  void _changeGroup(MarketGroup group) {
    if (_selectedGroup == group) {
      return;
    }

    setState(() {
      _selectedGroup = group;
      _future = _loadRecommendations();
    });
  }

  void _retry({bool forceRefresh = false}) {
    setState(() {
      if (forceRefresh) {
        _responseCache.remove(_selectedGroup.id);
      }
      _future = _loadRecommendations(forceRefresh: forceRefresh);
    });
  }

  Future<void> _toggleFavorite(String symbol) {
    return _favoritesStore.toggle(symbol);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: <Widget>[
            Text(
              'US Market Scanner',
              style: theme.textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.w800,
              ),
            ),
            Text(
              '추천 종목, 관심종목, 상세 시그널 한 번에 보기',
              style: theme.textTheme.bodySmall?.copyWith(
                color: const Color(0xFF64748B),
              ),
            ),
          ],
        ),
        actions: <Widget>[
          IconButton(
            onPressed: () => _retry(forceRefresh: true),
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: FutureBuilder<RecommendationsResponse>(
        future: _future,
        builder: (
          BuildContext context,
          AsyncSnapshot<RecommendationsResponse> snapshot,
        ) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const Center(child: CircularProgressIndicator());
          }

          if (snapshot.hasError) {
            return ErrorState(
              message: snapshot.error.toString(),
              onRetry: () => _retry(forceRefresh: true),
            );
          }

          final data = snapshot.data;
          if (data == null) {
            return ErrorState(
              message: 'No data received.',
              onRetry: () => _retry(forceRefresh: true),
            );
          }

          return ValueListenableBuilder<Set<String>>(
            valueListenable: _favoritesStore.favorites,
            builder:
                (
                  BuildContext context,
                  Set<String> favorites,
                  Widget? child,
                ) {
                  final watchlistItems = _buildWatchlistItems(data, favorites);

                  return RefreshIndicator(
                    onRefresh: () async {
                      _retry(forceRefresh: true);
                      await _future;
                    },
                    child: ListView(
                      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
                      children: <Widget>[
                        _HeroBanner(
                          selectedGroup: _selectedGroup,
                          favoriteCount: favorites.length,
                        ),
                        const SizedBox(height: 16),
                        SizedBox(
                          height: 44,
                          child: ListView.separated(
                            scrollDirection: Axis.horizontal,
                            itemBuilder: (BuildContext context, int index) {
                              final group = MarketGroup.values[index];
                              return ChoiceChip(
                                label: Text(group.label),
                                selected: group == _selectedGroup,
                                onSelected: (_) => _changeGroup(group),
                              );
                            },
                            separatorBuilder:
                                (BuildContext context, int index) =>
                                    const SizedBox(width: 10),
                            itemCount: MarketGroup.values.length,
                          ),
                        ),
                        const SizedBox(height: 20),
                        if (watchlistItems.isNotEmpty) ...<Widget>[
                          _Section(
                            title: '관심종목',
                            subtitle: '저장한 종목을 현재 추천 결과와 함께 빠르게 다시 확인합니다.',
                            items: watchlistItems,
                            favorites: favorites,
                            onFavoriteToggle: _toggleFavorite,
                            api: widget.api,
                            accentColor: const Color(0xFFB45309),
                            strategyLabel: 'Watchlist',
                          ),
                          const SizedBox(height: 20),
                        ],
                        _Section(
                          title: 'Swing Best 3',
                          subtitle: '단기 모멘텀과 패턴 점수를 중심으로 정리했습니다.',
                          items: data.swing,
                          favorites: favorites,
                          onFavoriteToggle: _toggleFavorite,
                          api: widget.api,
                          accentColor: const Color(0xFF0F766E),
                          strategyLabel: 'Swing',
                        ),
                        const SizedBox(height: 20),
                        _Section(
                          title: 'Long-term Best 3',
                          subtitle: '추세 정렬과 장기 우상향 조건을 중심으로 골랐습니다.',
                          items: data.longTerm,
                          favorites: favorites,
                          onFavoriteToggle: _toggleFavorite,
                          api: widget.api,
                          accentColor: const Color(0xFF1D4ED8),
                          strategyLabel: 'Long-term',
                        ),
                      ],
                    ),
                  );
                },
          );
        },
      ),
    );
  }

  List<RecommendationItem> _buildWatchlistItems(
    RecommendationsResponse data,
    Set<String> favorites,
  ) {
    final deduplicated = <String, RecommendationItem>{};
    for (final item in <RecommendationItem>[...data.swing, ...data.longTerm]) {
      if (favorites.contains(item.symbol)) {
        deduplicated[item.symbol] = item;
      }
    }

    final items = deduplicated.values.toList();
    items.sort((left, right) => right.score.compareTo(left.score));
    return items;
  }
}

class _HeroBanner extends StatelessWidget {
  const _HeroBanner({required this.selectedGroup, required this.favoriteCount});

  final MarketGroup selectedGroup;
  final int favoriteCount;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(28),
        gradient: const LinearGradient(
          colors: <Color>[Color(0xFF0F766E), Color(0xFF0F172A)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            '${selectedGroup.label} universe',
            style: theme.textTheme.titleLarge?.copyWith(
              color: Colors.white,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '추천 카드에서 바로 저장하고, 상세 화면에서 최근 가격 흐름과 근거를 함께 확인할 수 있습니다.',
            style: theme.textTheme.bodyMedium?.copyWith(
              color: Colors.white.withValues(alpha: 0.86),
              height: 1.4,
            ),
          ),
          const SizedBox(height: 16),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: <Widget>[
              _BannerPill(label: 'Group', value: selectedGroup.label),
              _BannerPill(label: 'Saved', value: '$favoriteCount symbols'),
            ],
          ),
        ],
      ),
    );
  }
}

class _BannerPill extends StatelessWidget {
  const _BannerPill({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(18),
      ),
      child: Text(
        '$label  $value',
        style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w700),
      ),
    );
  }
}

class _Section extends StatelessWidget {
  const _Section({
    required this.title,
    required this.subtitle,
    required this.items,
    required this.favorites,
    required this.onFavoriteToggle,
    required this.api,
    required this.accentColor,
    required this.strategyLabel,
  });

  final String title;
  final String subtitle;
  final List<RecommendationItem> items;
  final Set<String> favorites;
  final Future<void> Function(String symbol) onFavoriteToggle;
  final MarketApi api;
  final Color accentColor;
  final String strategyLabel;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: <Widget>[
        Text(
          title,
          style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.w800),
        ),
        const SizedBox(height: 6),
        Text(
          subtitle,
          style: theme.textTheme.bodyMedium?.copyWith(
            color: const Color(0xFF64748B),
          ),
        ),
        const SizedBox(height: 12),
        if (items.isEmpty)
          const Card(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Text('No recommendations available.'),
            ),
          ),
        ...items.map(
          (item) => Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: RecommendationCard(
              item: item,
              isFavorite: favorites.contains(item.symbol),
              onFavoriteToggle: () => onFavoriteToggle(item.symbol),
              strategyLabel: strategyLabel,
              accentColor: accentColor,
              onTap: () {
                Navigator.of(context).push(
                  MaterialPageRoute<void>(
                    builder:
                        (BuildContext context) =>
                            StockDetailScreen(symbol: item.symbol, api: api),
                  ),
                );
              },
            ),
          ),
        ),
      ],
    );
  }
}

enum MarketGroup {
  all('all', 'All'),
  bigTech('big-tech', 'Big Tech'),
  semiconductors('semiconductors', 'Semis'),
  finance('finance', 'Finance'),
  defensive('defensive', 'Defensive');

  const MarketGroup(this.id, this.label);

  final String id;
  final String label;
}

