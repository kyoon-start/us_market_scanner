import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

class FavoritesStore {
  FavoritesStore._();

  static final FavoritesStore instance = FavoritesStore._();
  static const String _storageKey = 'favorite_symbols';

  final ValueNotifier<Set<String>> favorites = ValueNotifier<Set<String>>(<String>{});

  bool _loaded = false;

  bool contains(String symbol) {
    return favorites.value.contains(symbol.toUpperCase());
  }

  Future<void> ensureLoaded() async {
    if (_loaded) {
      return;
    }

    final preferences = await SharedPreferences.getInstance();
    final storedSymbols = preferences.getStringList(_storageKey) ?? <String>[];
    favorites.value = storedSymbols.map((symbol) => symbol.toUpperCase()).toSet();
    _loaded = true;
  }

  Future<void> toggle(String symbol) async {
    await ensureLoaded();

    final normalizedSymbol = symbol.toUpperCase();
    final nextFavorites = Set<String>.from(favorites.value);
    if (!nextFavorites.add(normalizedSymbol)) {
      nextFavorites.remove(normalizedSymbol);
    }

    favorites.value = nextFavorites;
    final preferences = await SharedPreferences.getInstance();
    await preferences.setStringList(_storageKey, nextFavorites.toList()..sort());
  }
}

