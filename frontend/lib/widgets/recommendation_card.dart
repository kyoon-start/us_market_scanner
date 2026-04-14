import 'package:flutter/material.dart';

import '../models/recommendation_item.dart';

class RecommendationCard extends StatelessWidget {
  const RecommendationCard({
    super.key,
    required this.item,
    required this.onTap,
    required this.onFavoriteToggle,
    required this.isFavorite,
    required this.strategyLabel,
    required this.accentColor,
  });

  final RecommendationItem item;
  final VoidCallback onTap;
  final VoidCallback onFavoriteToggle;
  final bool isFavorite;
  final String strategyLabel;
  final Color accentColor;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final probabilityText = _formatProbability(item.probability);
    final scoreBadge = _scoreBadgeStyle(item.score);
    final reasonPreview = item.reasons.isEmpty
        ? 'No signal summary available.'
        : item.reasons.first;

    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: <Widget>[
              Container(
                height: 4,
                decoration: BoxDecoration(
                  color: accentColor.withValues(alpha: 0.9),
                  borderRadius: BorderRadius.circular(999),
                ),
              ),
              const SizedBox(height: 14),
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: <Widget>[
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: <Widget>[
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                          decoration: BoxDecoration(
                            color: accentColor.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(999),
                          ),
                          child: Text(
                            strategyLabel,
                            style: TextStyle(
                              color: accentColor,
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ),
                        const SizedBox(height: 12),
                        Text(
                          item.symbol,
                          style: theme.textTheme.titleLarge?.copyWith(
                            fontSize: 24,
                            fontWeight: FontWeight.w900,
                            letterSpacing: -0.6,
                          ),
                        ),
                      ],
                    ),
                  ),
                  IconButton.filledTonal(
                    onPressed: onFavoriteToggle,
                    icon: Icon(isFavorite ? Icons.bookmark : Icons.bookmark_border),
                    color: isFavorite ? const Color(0xFFB45309) : const Color(0xFF475569),
                  ),
                ],
              ),
              const SizedBox(height: 14),
              Wrap(
                spacing: 10,
                runSpacing: 10,
                children: <Widget>[
                  _StatPill(
                    label: 'Score',
                    value: item.score.toString(),
                    background: scoreBadge.background,
                    foreground: scoreBadge.foreground,
                  ),
                  _StatPill(
                    label: 'Probability',
                    value: probabilityText,
                    background: const Color(0xFFE0F2FE),
                    foreground: const Color(0xFF075985),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: const Color(0xFFF8FAFC),
                  borderRadius: BorderRadius.circular(18),
                ),
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
                        reasonPreview,
                        maxLines: 2,
                        overflow: TextOverflow.ellipsis,
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: const Color(0xFF334155),
                          height: 1.35,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              if (item.reasons.length > 1) ...<Widget>[
                const SizedBox(height: 10),
                Text(
                  '+${item.reasons.length - 1} more reasons',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: const Color(0xFF64748B),
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  String _formatProbability(double? value) {
    if (value == null) {
      return 'n/a';
    }

    return '${(value * 100).toStringAsFixed(0)}%';
  }

  _BadgeStyle _scoreBadgeStyle(int score) {
    if (score >= 70) {
      return const _BadgeStyle(
        background: Color(0xFFDCFCE7),
        foreground: Color(0xFF166534),
      );
    }

    if (score >= 40) {
      return const _BadgeStyle(
        background: Color(0xFFFFEDD5),
        foreground: Color(0xFF9A3412),
      );
    }

    return const _BadgeStyle(
      background: Color(0xFFE5E7EB),
      foreground: Color(0xFF374151),
    );
  }
}

class _StatPill extends StatelessWidget {
  const _StatPill({
    required this.label,
    required this.value,
    required this.background,
    required this.foreground,
  });

  final String label;
  final String value;
  final Color background;
  final Color foreground;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: background,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: <Widget>[
          Text(
            '$label ',
            style: TextStyle(color: foreground.withValues(alpha: 0.8)),
          ),
          Text(
            value,
            style: TextStyle(color: foreground, fontWeight: FontWeight.w800),
          ),
        ],
      ),
    );
  }
}

class _BadgeStyle {
  const _BadgeStyle({required this.background, required this.foreground});

  final Color background;
  final Color foreground;
}

