import 'package:flutter/material.dart';

import '../models/stock_detail.dart';
import '../services/favorites_store.dart';
import '../services/market_api.dart';

class StockDetailScreen extends StatefulWidget {
  const StockDetailScreen({super.key, required this.symbol, required this.api});

  final String symbol;
  final MarketApi api;

  @override
  State<StockDetailScreen> createState() => _StockDetailScreenState();
}

class _StockDetailScreenState extends State<StockDetailScreen> {
  final FavoritesStore _favoritesStore = FavoritesStore.instance;
  late Future<StockDetail> _future;

  @override
  void initState() {
    super.initState();
    _future = widget.api.fetchStockDetail(widget.symbol);
    _favoritesStore.ensureLoaded();
  }

  void _retry() {
    setState(() {
      _future = widget.api.fetchStockDetail(widget.symbol);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.symbol)),
      body: FutureBuilder<StockDetail>(
        future: _future,
        builder: (BuildContext context, AsyncSnapshot<StockDetail> snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return _DetailLoadingState(symbol: widget.symbol);
          }

          if (snapshot.hasError) {
            return _DetailErrorState(
              symbol: widget.symbol,
              message: snapshot.error.toString(),
              onRetry: _retry,
            );
          }

          final detail = snapshot.data;
          if (detail == null) {
            return _DetailErrorState(
              symbol: widget.symbol,
              message: 'No stock detail data was returned.',
              onRetry: _retry,
            );
          }

          return ValueListenableBuilder<Set<String>>(
            valueListenable: _favoritesStore.favorites,
            builder: (
              BuildContext context,
              Set<String> favorites,
              Widget? child,
            ) {
              final isFavorite = favorites.contains(detail.symbol);

              return ListView(
                padding: const EdgeInsets.fromLTRB(16, 12, 16, 24),
                children: <Widget>[
                  _DetailHeroCard(
                    detail: detail,
                    isFavorite: isFavorite,
                    onFavoriteToggle:
                        () => _favoritesStore.toggle(detail.symbol),
                  ),
                  const SizedBox(height: 20),
                  const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 4),
                    child: Text(
                      'Analysis',
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.w700,
                        color: Color(0xFF0F172A),
                      ),
                    ),
                  ),
                  const SizedBox(height: 12),
                  _AnalysisCard(
                    title: 'Swing Analysis',
                    subtitle:
                        'Shorter-term setup quality based on the latest signal mix.',
                    score: detail.swingScore,
                    probability: detail.swingProbability,
                    reasons: detail.swingReasons,
                    accentColor: const Color(0xFF0F766E),
                  ),
                  const SizedBox(height: 16),
                  _AnalysisCard(
                    title: 'Long-term Analysis',
                    subtitle:
                        'Broader trend confirmation and longer-horizon context.',
                    score: detail.longTermScore,
                    probability: detail.longTermProbability,
                    reasons: detail.longTermReasons,
                    accentColor: const Color(0xFF1D4ED8),
                  ),
                ],
              );
            },
          );
        },
      ),
    );
  }
}

class _DetailHeroCard extends StatelessWidget {
  const _DetailHeroCard({
    required this.detail,
    required this.isFavorite,
    required this.onFavoriteToggle,
  });

  final StockDetail detail;
  final bool isFavorite;
  final VoidCallback onFavoriteToggle;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(24),
        gradient: const LinearGradient(
          colors: <Color>[Color(0xFF0F172A), Color(0xFF1E3A8A)],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        boxShadow: const <BoxShadow>[
          BoxShadow(
            color: Color(0x140F172A),
            blurRadius: 24,
            offset: Offset(0, 10),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: <Widget>[
                    Text(
                      'Symbol',
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: Colors.white.withValues(alpha: 0.72),
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      detail.symbol,
                      style: theme.textTheme.headlineMedium?.copyWith(
                        color: Colors.white,
                        fontWeight: FontWeight.w800,
                        letterSpacing: -0.5,
                      ),
                    ),
                    const SizedBox(height: 20),
                    Text(
                      'Latest Close',
                      style: theme.textTheme.bodyMedium?.copyWith(
                        color: Colors.white.withValues(alpha: 0.72),
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      '\$${detail.latestClosePrice.toStringAsFixed(2)}',
                      style: theme.textTheme.displaySmall?.copyWith(
                        color: Colors.white,
                        fontWeight: FontWeight.w800,
                        letterSpacing: -1,
                      ),
                    ),
                  ],
                ),
              ),
              IconButton.filled(
                onPressed: onFavoriteToggle,
                style: IconButton.styleFrom(
                  backgroundColor: Colors.white.withValues(alpha: 0.14),
                  foregroundColor: Colors.white,
                ),
                icon: Icon(isFavorite ? Icons.bookmark : Icons.bookmark_border),
              ),
            ],
          ),
          const SizedBox(height: 20),
          Row(
            children: <Widget>[
              Expanded(
                child: _HeroMetricChip(
                  label: 'Swing Score',
                  value: detail.swingScore.toString(),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _HeroMetricChip(
                  label: 'Long-term Score',
                  value: detail.longTermScore.toString(),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _HeroMetricChip extends StatelessWidget {
  const _HeroMetricChip({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.white.withValues(alpha: 0.14)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            label,
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w500,
              color: Colors.white70,
            ),
          ),
          const SizedBox(height: 4),
          Text(
            value,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w800,
              color: Colors.white,
            ),
          ),
        ],
      ),
    );
  }
}

class _AnalysisCard extends StatelessWidget {
  const _AnalysisCard({
    required this.title,
    required this.subtitle,
    required this.score,
    required this.probability,
    required this.reasons,
    required this.accentColor,
  });

  final String title;
  final String subtitle;
  final int score;
  final double? probability;
  final List<String> reasons;
  final Color accentColor;

  @override
  Widget build(BuildContext context) {
    final scoreTheme = _scoreTheme(score, accentColor);

    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: const Color(0xFFE2E8F0)),
        boxShadow: const <BoxShadow>[
          BoxShadow(
            color: Color(0x0F0F172A),
            blurRadius: 18,
            offset: Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            title,
            style: const TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w700,
              color: Color(0xFF0F172A),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            subtitle,
            style: const TextStyle(
              fontSize: 14,
              height: 1.45,
              color: Color(0xFF475569),
            ),
          ),
          const SizedBox(height: 18),
          Row(
            children: <Widget>[
              Expanded(
                child: _MetricTile(
                  label: 'Score',
                  value: score.toString(),
                  foregroundColor: scoreTheme.foreground,
                  backgroundColor: scoreTheme.background,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _MetricTile(
                  label: 'Probability',
                  value: _formatProbability(probability),
                  foregroundColor: const Color(0xFF0F172A),
                  backgroundColor: const Color(0xFFF8FAFC),
                ),
              ),
            ],
          ),
          const SizedBox(height: 18),
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: const Color(0xFFF8FAFC),
              borderRadius: BorderRadius.circular(16),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                const Text(
                  'Reasons',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                    color: Color(0xFF0F172A),
                  ),
                ),
                const SizedBox(height: 12),
                ..._buildReasons(reasons, accentColor),
              ],
            ),
          ),
        ],
      ),
    );
  }

  List<Widget> _buildReasons(List<String> reasons, Color accentColor) {
    if (reasons.isEmpty) {
      return const <Widget>[
        Text(
          'No reasons available.',
          style: TextStyle(
            fontSize: 14,
            height: 1.45,
            color: Color(0xFF64748B),
          ),
        ),
      ];
    }

    return reasons
        .map(
          (String reason) => Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: <Widget>[
                Container(
                  width: 8,
                  height: 8,
                  margin: const EdgeInsets.only(top: 6),
                  decoration: BoxDecoration(
                    color: accentColor,
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    reason,
                    style: const TextStyle(
                      fontSize: 14,
                      height: 1.45,
                      color: Color(0xFF334155),
                    ),
                  ),
                ),
              ],
            ),
          ),
        )
        .toList();
  }

  _ScoreTheme _scoreTheme(int score, Color accentColor) {
    if (score >= 70) {
      return const _ScoreTheme(
        background: Color(0xFFDCFCE7),
        foreground: Color(0xFF166534),
      );
    }
    if (score >= 40) {
      return _ScoreTheme(
        background: const Color(0xFFDBEAFE),
        foreground: accentColor,
      );
    }
    return const _ScoreTheme(
      background: Color(0xFFF1F5F9),
      foreground: Color(0xFF475569),
    );
  }
}

class _MetricTile extends StatelessWidget {
  const _MetricTile({
    required this.label,
    required this.value,
    required this.foregroundColor,
    required this.backgroundColor,
  });

  final String label;
  final String value;
  final Color foregroundColor;
  final Color backgroundColor;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: <Widget>[
          Text(
            label,
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: Color(0xFF64748B),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            value,
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.w800,
              color: foregroundColor,
              letterSpacing: -0.5,
            ),
          ),
        ],
      ),
    );
  }
}

class _DetailLoadingState extends StatelessWidget {
  const _DetailLoadingState({required this.symbol});

  final String symbol;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: <Widget>[
            const SizedBox(
              width: 28,
              height: 28,
              child: CircularProgressIndicator(strokeWidth: 2.6),
            ),
            const SizedBox(height: 18),
            Text(
              'Loading $symbol details',
              style: const TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w700,
                color: Color(0xFF0F172A),
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Fetching the latest close price and analysis.',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 14,
                height: 1.45,
                color: Color(0xFF64748B),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _DetailErrorState extends StatelessWidget {
  const _DetailErrorState({
    required this.symbol,
    required this.message,
    required this.onRetry,
  });

  final String symbol;
  final String message;
  final VoidCallback onRetry;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Container(
          constraints: const BoxConstraints(maxWidth: 420),
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: const Color(0xFFE2E8F0)),
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: <Widget>[
              Container(
                width: 52,
                height: 52,
                decoration: const BoxDecoration(
                  color: Color(0xFFFEE2E2),
                  shape: BoxShape.circle,
                ),
                child: const Icon(
                  Icons.error_outline,
                  color: Color(0xFFB91C1C),
                ),
              ),
              const SizedBox(height: 16),
              Text(
                'Unable to load $symbol',
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                  color: Color(0xFF0F172A),
                ),
              ),
              const SizedBox(height: 8),
              Text(
                message,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontSize: 14,
                  height: 1.45,
                  color: Color(0xFF64748B),
                ),
              ),
              const SizedBox(height: 18),
              FilledButton.icon(
                onPressed: onRetry,
                icon: const Icon(Icons.refresh),
                label: const Text('Retry'),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _ScoreTheme {
  const _ScoreTheme({required this.background, required this.foreground});

  final Color background;
  final Color foreground;
}

String _formatProbability(double? value) {
  if (value == null) {
    return 'N/A';
  }

  return '${(value * 100).toStringAsFixed(0)}%';
}
