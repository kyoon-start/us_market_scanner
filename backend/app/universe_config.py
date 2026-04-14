"""Dedicated configuration for the recommendation stock universe."""

from __future__ import annotations

import logging


logger = logging.getLogger(__name__)

SUPPORTED_UNIVERSE_SIZES = (100, 200, 500)
DEFAULT_UNIVERSE_SIZE = 100
MAX_DEFAULT_UNIVERSE_SIZE = max(SUPPORTED_UNIVERSE_SIZES)


def _dedupe_symbols(symbols: list[str]) -> list[str]:
    """Return uppercase symbols in stable order without duplicates."""
    seen: set[str] = set()
    normalized_symbols: list[str] = []
    for symbol in symbols:
        normalized = symbol.strip().upper()
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        normalized_symbols.append(normalized)
    return normalized_symbols


US_RECOMMENDATION_UNIVERSE = _dedupe_symbols([
    "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "GOOG", "TSLA", "BRK-B", "JPM",
    "V", "LLY", "AVGO", "XOM", "UNH", "MA", "COST", "JNJ", "WMT", "PG",
    "HD", "MRK", "BAC", "ABBV", "CVX", "KO", "CRM", "AMD", "NFLX", "PEP",
    "ADBE", "TMO", "LIN", "ACN", "MCD", "CSCO", "ORCL", "ABT", "DHR", "WFC",
    "DIS", "PM", "TXN", "VZ", "INTU", "AMGN", "QCOM", "CAT", "IBM", "GE",
    "SPGI", "NOW", "ISRG", "INTC", "AXP", "UNP", "MS", "GS", "BKNG", "RTX",
    "BLK", "SYK", "SCHW", "BA", "AMAT", "LMT", "TJX", "LOW", "PGR", "DE",
    "MDT", "ADP", "COP", "PLD", "MMC", "VRTX", "ELV", "CB", "ADI", "MU",
    "PANW", "C", "ETN", "GILD", "MDLZ", "TMUS", "ADSK", "ZTS", "REGN", "MO",
    "CI", "SO", "DUK", "USB", "T", "CME", "PYPL", "CL", "NKE", "MMM",
    "WM", "SHW", "APD", "SLB", "EOG", "EQIX", "SNPS", "CDNS", "AON", "ICE",
    "MCK", "ITW", "FDX", "EMR", "PH", "CMG", "HCA", "MAR", "PSX", "KLAC",
    "AEP", "CSX", "PNC", "AJG", "GD", "NSC", "EW", "ROP", "TT", "FCX",
    "GM", "PCAR", "F", "NXPI", "MPC", "TGT", "OXY", "SRE", "NOC", "DLR",
    "BDX", "WELL", "BK", "TRV", "AFL", "CTAS", "PAYX", "AMP", "AZO", "ROST",
    "PSA", "TEL", "JCI", "MSI", "AIG", "CPRT", "O", "KMB", "ALL", "D",
    "MET", "FAST", "FIS", "KVUE", "KMI", "CCI", "A", "DHI", "MSCI", "AME",
    "MNST", "XEL", "IDXX", "LRCX", "HLT", "SYY", "PRU", "EXC", "CHTR", "CTVA",
    "IQV", "YUM", "EA", "ODFL", "CARR", "RSG", "PEG", "PCG", "DAL", "TTWO",
    "STZ", "HIG", "DD", "OTIS", "VRSK", "DXCM", "VMC", "KDP", "NEM", "HSY",
    "CSGP", "WAB", "ECL", "ED", "FANG", "BIIB", "ANET", "BKR", "CDW", "XYL",
    "LULU", "PPG", "MTD", "LYB", "PHM", "GIS", "ROK", "IR", "WEC", "AVB",
    "ON", "WTW", "VICI", "SBAC", "FITB", "LEN", "EBAY", "RMD", "CAH", "ABC",
    "DFS", "NUE", "ZBH", "KEYS", "PPL", "AWK", "HUM", "CMI", "CHD", "EIX",
    "DTE", "TRGP", "GWW", "ADM", "FTNT", "GLW", "TSCO", "TROW", "HBAN", "MPWR",
    "DOW", "EXPE", "VRSN", "ALGN", "ACGL", "BRO", "PTC", "HPE", "NDAQ", "PFG",
    "EFX", "IFF", "CTSH", "EXR", "ESS", "FTV", "INVH", "HES", "FE", "CNC",
    "MKC", "STT", "RF", "CMS", "AEE", "EQR", "MOH", "MTB", "WY", "APTV",
    "TDG", "WST", "MLM", "ETR", "CHRW", "AIZ", "PWR", "CNP", "STE", "DGX",
    "DOV", "UAL", "COF", "COR", "NTRS", "VTR", "WAT", "PKG", "IP", "LYV",
    "TER", "HOLX", "LVS", "BALL", "TSN", "DRI", "CBOE", "LH", "MAS", "CFG",
    "MAA", "FICO", "NVR", "ULTA", "VTRS", "ARE", "JBHT", "OMC", "J", "DPZ",
    "L", "SYF", "TXT", "SWK", "FSLR", "AES", "CE", "BAX", "CPB", "BBY",
    "PODD", "GEN", "TRMB", "FDS", "TYL", "JKHY", "RJF", "LDOS", "IEX", "CLX",
    "HRL", "PEAK", "DG", "MGM", "MRNA", "SMCI", "ONON", "HUBB", "NRG", "LHX",
    "SWKS", "COO", "CAG", "KHC", "EPAM", "MOS", "CF", "JBL", "AKAM", "DOC",
    "BBWI", "CINF", "NDSN", "LNT", "NWSA", "NWS", "RVTY", "ENPH", "GNRC", "FMC",
    "EVRG", "NI", "AAL", "MRO", "APA", "BEN", "FOX", "FOXA", "HAS", "MHK",
    "INCY", "REG", "K", "PARA", "SJM", "UDR", "WRB", "CPT", "POOL", "MKTX",
    "FFIV", "ALB", "ATO", "PNR", "TPR", "RL", "WHR", "JNPR", "VFC", "XRAY",
    "BXP", "HSIC", "TECH", "WBA", "NCLH", "RCL", "CCL", "ETSY", "DOCU", "SNOW",
    "TEAM", "NET", "CRWD", "ZS", "DDOG", "OKTA", "MDB", "HUBS", "SHOP", "SQ",
    "AFRM", "COIN", "UBER", "LYFT", "ABNB", "DASH", "SPOT", "ROKU", "TTD", "APP",
    "PLTR", "ARM", "MRVL", "MCHP", "QRVO", "LPLA", "CAVA", "DKNG", "PINS", "SNAP",
    "HOOD", "BILL", "SOFI", "DUOL", "CELH", "ELF", "DECK", "ANSS", "MANH", "PAYC",
    "PAYCOM", "PCOR", "WDAY", "GFS", "INTA", "CVNA", "KKR", "BX", "OWL", "CG",
    "ARES", "CPNG", "FI", "GPN", "FLT", "BR", "VEEV", "TOST", "PATH", "ESTC",
    "NEE", "SBUX", "ORLY", "MELI", "CEG", "HWM", "CRH", "FERG", "PDD", "BURL",
    "WYNN", "CZR", "MTCH", "EXAS", "NTRA", "VRT", "RPM", "URI", "ZBRA", "UHS",
    "AOS", "HST", "RHI", "BIO", "LII", "KIM", "GLPI", "LUV", "MUSA", "TPX",
    "KEX", "WSM",
])

FALLBACK_SYMBOLS = US_RECOMMENDATION_UNIVERSE[:20]

SYMBOL_GROUPS = {
    "all": US_RECOMMENDATION_UNIVERSE,
    "big-tech": [
        "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "GOOG", "TSLA", "NFLX", "AMD",
        "ADBE", "ORCL", "CSCO", "QCOM", "INTC", "CRM", "NOW", "SNOW", "PLTR", "PANW",
    ],
    "semiconductors": [
        "NVDA", "AMD", "AVGO", "QCOM", "INTC", "AMAT", "ADI", "MU", "TXN", "KLAC",
        "LRCX", "NXPI", "ON", "MRVL", "MCHP", "QRVO", "SWKS", "MPWR", "GFS", "ARM",
    ],
    "finance": [
        "JPM", "BAC", "WFC", "MS", "GS", "V", "MA", "AXP", "BLK", "CME",
        "SCHW", "USB", "C", "PNC", "BK", "AIG", "PGR", "COF", "MCO", "SPGI",
    ],
    "defensive": [
        "JNJ", "PG", "KO", "PEP", "WMT", "COST", "MRK", "ABBV", "MCD", "WM",
        "DUK", "SO", "CL", "KMB", "GIS", "HSY", "MDLZ", "SJM", "CPB", "KHC",
    ],
}


def _normalize_universe_size(universe_size: int | None) -> int:
    """Return a supported universe size, falling back safely when needed."""
    if universe_size in SUPPORTED_UNIVERSE_SIZES:
        return universe_size

    if universe_size is not None:
        logger.warning(
            "Unsupported universe size '%s', using default size %d instead",
            universe_size,
            DEFAULT_UNIVERSE_SIZE,
        )
    return DEFAULT_UNIVERSE_SIZE


def get_default_symbols(universe_size: int | None = None) -> list[str]:
    """Return the default recommendation universe capped to a supported size."""
    normalized_size = _normalize_universe_size(universe_size)
    try:
        if not US_RECOMMENDATION_UNIVERSE:
            raise ValueError("Configured stock universe is empty.")

        limited_symbols = US_RECOMMENDATION_UNIVERSE[:normalized_size]
        logger.info(
            "Loaded stock recommendation universe with %d symbols (requested size %d)",
            len(limited_symbols),
            normalized_size,
        )
        return limited_symbols
    except Exception:
        logger.exception("Falling back to the backup stock universe")
        return FALLBACK_SYMBOLS[:normalized_size]


def get_symbols_for_group(group: str | None, universe_size: int | None = None) -> list[str]:
    """Return a curated symbol subset for the requested group."""
    normalized_size = _normalize_universe_size(universe_size)
    if not group:
        return get_default_symbols(normalized_size)

    normalized_group = group.strip().lower()
    selected_symbols = SYMBOL_GROUPS.get(normalized_group)
    if not selected_symbols:
        logger.warning("Unknown symbol group '%s', using defaults instead", normalized_group)
        return get_default_symbols(normalized_size)

    return _dedupe_symbols(selected_symbols)[:normalized_size]


