"""Dedicated configuration for the recommendation stock universe."""

from __future__ import annotations

import logging

from .scanner_config import (
    DEFAULT_UNIVERSE_SIZE,
    FALLBACK_UNIVERSE_SIZE,
    MAX_DEFAULT_UNIVERSE_SIZE,
    SUPPORTED_UNIVERSE_SIZES,
    normalize_universe_size,
)


logger = logging.getLogger(__name__)


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
    "ACHC", "ACI", "ACIW", "ACM", "ACMR", "ACT", "ADMA", "ADNT", "ADT", "AEIS",
    "AER", "AEVA", "AGCO", "AGNC", "AGYS", "AI", "AIZN", "ALGM", "ALK", "ALKT",
    "ALLE", "ALNY", "ALRM", "ALSN", "ALTM", "AMCR", "AMCX", "AMED", "AMKR", "AMN",
    "AMR", "AMRC", "AMSC", "AMT", "AN", "ANF", "APPF", "AR", "ARCB", "ARCC",
    "ARDX", "ARIS", "ARLO", "AROC", "ARRY", "ARVN", "ASAN", "ASB", "ASO", "ATI",
    "ATKR", "ATMU", "ATRC", "ATRI", "ATRO", "ATUS", "AUB", "AVA", "AVAV", "AVDL",
    "AVNT", "AVTR", "AVY", "AX", "AXON", "AXSM", "AZEK", "AZPN", "AZTA", "BANC",
    "BAND", "BANF", "BANR", "BATRK", "BBIO", "BCC", "BCO", "BCPC", "BDC", "BE",
    "BEAM", "BEKE", "BENE", "BFAM", "BFH", "BGC", "BHF", "BHVN", "BIDU", "BIGC",
    "BIPC", "BJ", "BKH", "BKD", "BKI", "BKU", "BL", "BLD", "BLDR", "BLKB",
    "BLMN", "BLTE", "BLZE", "BMRN", "BMY", "BN", "BNS", "BOOT", "BORR", "BOX",
    "BRBR", "BRKR", "BRX", "BSAC", "BSY", "BTDR", "BTU", "BURL", "BV", "BWXT",
    "BYD", "BYND", "CABO", "CACI", "CADE", "CAH", "CALM", "CAR", "CARG", "CARS",
    "CAVA", "CBRL", "CBSH", "CBT", "CCCS", "CCJ", "CCOI", "CCS", "CDAY", "CDNA",
    "CDP", "CDRE", "CELC", "CENX", "CERT", "CEVA", "CGNX", "CHDN", "CHE", "CHEF",
    "CHGG", "CHPT", "CHWY", "CIEN", "CIVI", "CLBT", "CLF", "CLH", "CLSK", "CLS",
    "CMA", "CMC", "CMCSA", "CNO", "CNXC", "CNXN", "COHR", "COLB", "COMM", "COMP",
    "CON", "COOP", "COPA", "COTY", "CPAY", "CPRI", "CPRI", "CRDO", "CRI", "CRL",
    "CRS", "CRSP", "CRTO", "CRUS", "CRVL", "CSL", "CSWI", "CUBE", "CUBI", "CXM",
    "CYBR", "CYTK", "DAR", "DBX", "DCI", "DCI", "DCO", "DDI", "DDS", "DEI",
    "DINO", "DKS", "DLB", "DLTR", "DNLI", "DOCN", "DOLE", "DOOO", "DORM", "DOW",
    "DRS", "DSGR", "DSGX", "DVA", "DVN", "DXPE", "DY", "EAT", "EB", "EBC",
    "EBR", "ECPG", "EDR", "EEFT", "EGP", "EHC", "EHAB", "ELAN", "ELME", "ELS",
    "EME", "ENOV", "ENR", "ENV", "ENVA", "EPR", "EPRT", "EQH", "ERIE", "ESAB",
    "ESI", "ESLT", "ETSY", "ETWO", "EVH", "EVR", "EWBC", "EXEL", "EXLS", "EXP",
    "EXPO", "EXTR", "FAF", "FATE", "FBIN", "FBK", "FCFS", "FCN", "FCPT", "FCX",
    "FELE", "FER", "FHI", "FIGS", "FINV", "FIVE", "FLEX", "FLNC", "FLO", "FLR",
    "FND", "FNKO", "FOLD", "FORM", "FOUR", "FR", "FRHC", "FRPT", "FSV", "FTDR",
    "FTEC", "FTI", "FTI", "FTI", "FTOC", "FUBO", "FUL", "FUTU", "FYBR", "GATX",
    "GBDC", "GBX", "GDEN", "GDRX", "GEF", "GEO", "GERN", "GGAL", "GHC", "GH",
    "GIII", "GKOS", "GLBE", "GLNG", "GLOB", "GLPG", "GLPI", "GLXY", "GMAB", "GME",
    "GMED", "GMRE", "GNW", "GO", "GOEV", "GOLF", "GOSS", "GPK", "GRAB", "GRMN",
    "GRND", "GSHD", "GT", "GTES", "GTLB", "GTLS", "GXO", "HAE", "HAL", "HALO",
    "HASI", "HAYW", "HBI", "HBM", "HBT", "HCC", "HCI", "HIMS", "HLIO", "HLNE",
    "HLX", "HOG", "HOMB", "HOPE", "HOV", "HQY", "HR", "HRB", "HRMY", "HSII",
    "HUN", "HXL", "IART", "IBKR", "IBOC", "ICFI", "ICLR", "IDYA", "IESC", "IGMS",
    "IIPR", "IMVT", "INDB", "INFA", "INFN", "INGR", "INGR", "INMD", "INOD", "INSM",
    "INTAPP", "INVA", "IONS", "IOSP", "IPAR", "IPG", "IRDM", "IRM", "IRON", "IRT",
    "ITCI", "ITRI", "ITT", "JAMF", "JANX", "JBGS", "JBT", "JEF", "JHG", "JOBY",
    "JOE", "JWN", "KAI", "KAR", "KBR", "KC", "KD", "KFY", "KGC", "KKR", "KMX",
    "KNSL", "KNX", "KNTK", "KOD", "KR", "KRNT", "KRNY", "KRG", "KROS", "KRTX",
    "KTB", "KVYO", "LAD", "LAZ", "LB", "LBRDK", "LCII", "LCID", "LEA", "LECO",
    "LEG", "LEGH", "LESL", "LEU", "LFUS", "LGIH", "LHCG", "LHX", "LIF", "LITE",
    "LIVN", "LKQ", "LLYVK", "LMND", "LNC", "LNTH", "LOB", "LOPE", "LOVE", "LPX",
    "LRN", "LSCC", "LSI", "LSTR", "LU", "LTH", "LZ", "M", "MARA", "MAT",
    "MATV", "MATX", "MBC", "MBUU", "MC", "MCW", "MD", "MDGL", "MDU", "MEDP",
    "MFA", "MGA", "MGEE", "MGNI", "MGPI", "MIDD", "MIR", "MKL", "MKSI", "MLCO",
    "MLI", "MLKN", "MMC", "MMS", "MMSI", "MNDY", "MNR", "MOD", "MODG", "MODV",
    "MOFG", "MORN", "MPC", "MPLX", "MP", "MPLN", "MRCY", "MSA", "MSM", "MSTR",
    "MTCH", "MTG", "MTH", "MTN", "MTZ", "MUR", "MVST", "NABL", "NARI", "NATL",
    "NATI", "NATL", "NAVI", "NBIX", "NBTB", "NCNO", "NCR", "NDSN", "NEOG", "NEP",
    "NET", "NEU", "NEWM", "NFE", "NFG", "NHI", "NJR", "NKTX", "NMIH", "NNN",
    "NOG", "NOV", "NOVT", "NRIX", "NSIT", "NTAP", "NTB", "NVT", "NWBI", "NWE",
    "NWL", "NXST", "NYCB", "NYT", "OBDC", "OC", "ODP", "OGN", "OGS", "OLLI",
    "OLN", "OLPX", "OMAB", "OMI", "OMF", "ONB", "ONTO", "OPCH", "OPRA", "ORA",
    "ORI", "OSCR", "OSIS", "OSK", "OTEX", "OTTR", "OUST", "OVV", "OXM", "PACB",
    "PAG", "PAGS", "PANL", "PATK", "PAYO", "PB", "PBF", "PBH", "PCRX", "PCTY",
    "PDD", "PDFS", "PDCO", "PDM", "PEB", "PENN", "PFGC", "PFSI", "PGNY", "PHIN",
    "PI", "PII", "PINC", "PIPR", "PLAB", "PLAY", "PLNT", "PLXS", "PLYA", "PNFP",
    "PNW", "POR", "POST", "POWI", "PPC", "PPBI", "PR", "PRCT", "PRGO", "PRIM",
    "PRKS", "PRLB", "PRMW", "PRNH", "PRTA", "PRU", "PSMT", "PSN", "PSTG", "PSXP",
    "PTEN", "PTGX", "PUMP", "PWP", "PWR", "PWSC", "PZZA", "QDEL", "QGEN", "QLYS",
    "QRTEA", "QTWO", "RAMP", "RBC", "RBCN", "RBLX", "RCII", "RDN", "RDFN", "RDNT",
    "RDWR", "REAL", "RELY", "RES", "REXR", "REYN", "RGA", "RGEN", "RGLD", "RIG",
    "RKLB", "RLAY", "RMBS", "RNG", "ROAD", "ROB", "ROG", "ROLL", "ROOT", "RPD",
    "RRC", "RRX", "RS", "RUSHA", "RVLV", "RXO", "SAIA", "SAIC", "SAM", "SANM",
    "SATS", "SBLK", "SBRA", "SBSW", "SCCO", "SCHL", "SCI", "SCPH", "SDGR", "SE",
    "SEE", "SEIC", "SEM", "SF", "SFM", "SG", "SHAK", "SHC", "SHLS", "SHO",
    "SIG", "SITE", "SIX", "SKX", "SLAB", "SLG", "SLM", "SLNO", "SM", "SMAR",
    "SMG", "SMPL", "SNA", "SNBR", "SNDR", "SNEX", "SNV", "SOUN", "SPB", "SPXC",
    "SR", "SRCL", "SSD", "SSRM", "ST", "STAA", "STEP", "STLD", "STNE", "STR",
    "STRA", "STWD", "SUM", "SUN", "SUPN", "SWAV", "SWI", "SWIM", "SWN", "SXT",
    "SYM", "SYNA", "TAP", "TCBI", "TCMD", "TCX", "TDC", "TDUP", "TENB", "TEVA",
    "TEX", "TFSL", "TGTX", "THC", "THG", "THO", "THRM", "TIGR", "TIXT", "TKR",
    "TLN", "TMDX", "TMHC", "TNET", "TNL", "TOI", "TOL", "TOUR", "TPB", "TPH",
    "TPH", "TPIC", "TPR", "TRIP", "TRN", "TRNO", "TRS", "TRUP", "TRU", "TSEM",
    "TTAN", "TTC", "TTMI", "TTEK", "TUP", "TW", "TWI", "TWLO", "TX", "TXG",
    "TXRH", "U", "UAA", "UAL", "UBSI", "UFPI", "UHAL", "UI", "ULCC", "ULTI",
    "UMBF", "UNF", "UNIT", "UNM", "UPST", "UPWK", "URBN", "USFD", "USLM", "UTHR",
    "VAC", "VAL", "VC", "VCEL", "VERA", "VERX", "VFC", "VG", "VGR", "VIR",
    "VIRT", "VIST", "VLY", "VNOM", "VOC", "VOYA", "VRDN", "VRNS", "VRRM", "VRSK",
    "VSAT", "VSH", "VSTS", "VVV", "W", "WAL", "WBS", "WD", "WDFC", "WERN",
    "WFRD", "WH", "WHD", "WING", "WK", "WMS", "WNS", "WOLF", "WOR", "WPC",
    "WRK", "WSBC", "WSFS", "WSO", "WTFC", "WU", "WWD", "X", "XENE", "XOM",
    "XP", "XPEL", "XPO", "YELP", "YETI", "YOU", "YUMC", "ZD", "ZETA", "ZG",
    "ZI", "ZION", "ZIP", "ZM", "ZWS", "AA", "AAON", "AAT", "ABCB", "ABG",
    "ABM", "ABR", "ABRDN", "ABSI", "ACAD", "ACEL", "ACGLN", "ACHR", "ACLX", "ACLS",
    "ACVA", "ADC", "ADES", "ADPT", "ADTN", "AEO", "AER", "AFCG", "AFG", "AFYA",
    "AGI", "AGIO", "AGL", "AHCO", "AHR", "AHT", "AIP", "AIRC", "AKR", "AKRO",
    "AKYA", "ALC", "ALGT", "ALHC", "ALIT", "ALKS", "ALLE", "ALLO", "ALRS", "ALTG",
    "AMAL", "AMBC", "AMCX", "AMED", "AMH", "AMK", "AMPH", "AMPL", "AMRX", "AMSF",
    "AMTB", "AMWD", "ANIP", "ANVS", "APAM", "APGE", "APG", "APLE", "APLS", "APOG",
    "ARCT", "ARHS", "ARLP", "ARQT", "ARRY", "ASGN", "ASH", "ASND", "ASTE", "ATEN",
    "ATGE", "ATLC", "ATNI", "ATSG", "ATUS", "AUPH", "AVA", "AVD", "AVNS", "AVPT",
    "AVTX", "AWR", "AXGN", "AXS", "AZEK", "AZZ", "B", "BALY", "BBSI", "BC",
    "BCRX", "BDC", "BELFB", "BEN", "BFST", "BGS", "BHC", "BHE", "BHVN", "BKE",
    "BLFS", "BLMN", "BLND", "BMBL", "BMI", "BNL", "BOH", "BRCC", "BRZE", "BTSG",
    "BW", "BWA", "BYRN", "CACC", "CALX", "CASH", "CATY", "CBU", "CCOI", "CDE",
    "CDMO", "CEIX", "CELC", "CENT", "CERT", "CFLT", "CGAU", "CHCO", "CHX", "CHY",
    "CIM", "CIVB", "CLB", "CLDX", "CLMT", "CMBM", "CMPR", "CNK", "CNM", "CNNE",
    "CNTA", "CNX", "CODI", "COHU", "COLM", "COMP", "CONN", "COUR", "CPRX", "CRNX",
    "CROX", "CRVL", "CSGS", "CSQ", "CSR", "CSTM", "CVBF", "CVCO", "CWAN", "CWEN",
    "DAWN", "DBRG", "DCTH", "DEA", "DFH", "DNOW", "DNUT", "DOMA", "DPRO", "DRH",
    "DVAX", "DV", "EBF", "ECVT", "EDIT", "EFSC", "EGO", "ELP", "ENFN", "ENLC",
    "ENSG", "ENTA", "EOLS", "EPD", "ESGR", "ESE", "ESRT", "ESTA", "ETD", "ETNB",
    "ETRN", "EU", "EVTC", "EWTX", "EXAS", "EXG", "EXPI", "EYPT", "FA", "FBNC",
    "FBP", "FCEL", "FFBC", "FHB", "FIBK", "FIP", "FLGT", "FLYW", "FMBH", "FN",
    "FNLC", "FOR", "FRSH", "FSLY", "FUFU", "FULC", "FWRG", "GABC", "GBIO", "GDOT",
    "GEF-B", "GHLD", "GIC", "GILD", "GLAD", "GLDD", "GNK", "GOGL", "GPI", "GPRO",
    "GRC", "GRC", "GRFS", "GSAT", "GVA", "HAIN", "HCAT", "HCKT", "HE", "HEES",
    "HEI", "HGV", "HNI", "HRI", "HTH", "HTLF", "HY", "IAE", "IAS", "IBP",
    "ICHR", "IDT", "IESC", "IGT", "IIIN", "ILMN", "IMCR", "IMGN", "IMKTA", "INGN",
    "INN", "INSP", "IOT", "IPGP", "IRBT", "IRTC", "IRT", "IVT", "JBLU", "JBSS",
    "JELD", "JXN", "KALU", "KAR", "KBH", "KLIC", "KMPR", "KNSA", "KRC", "KREF",
    "KURA", "LANC", "LAND", "LBTYA", "LECO", "LEVI", "LILA", "LMAT", "LNW", "LPG",
    "LQDA", "LSPD", "LXU", "MANT", "MBCN", "MCB", "MCRI", "MDXG", "MERC", "MIRM",
    "MLAB", "MLNK", "MMSI", "MNKD", "MNTK", "MOMO", "MORN", "MPLX", "MTDR", "MTW",
    "NABL", "NBN", "NBR", "NCL", "NCSM", "NDMO", "NHC", "NMM", "NMRK", "NNI",
    "NPO", "NRDY", "NREF", "NSSC", "NWN", "OAS", "OFG", "OGE", "OLMA", "OMCL",
    "OMER", "ONEW", "OPEN", "ORA", "ORGO", "ORRF", "OSPN", "OUT", "PAC", "PACS",
    "PAHC", "PAYA", "PAX", "PBYI", "PD", "PGEN", "PGRE", "PHR", "PLMR", "PLUS",
    "PMTS", "PNTG", "POWL", "PRA", "PRDO", "PRFT", "PRM", "PRPL", "PSFE", "PSEC",
    "PTCT", "PTLO", "QTWO", "RARE", "RCKT", "RCUS", "REVG", "RGEN", "RGR", "RHP",
    "RIGL", "RIOT", "RLJ", "RNA", "ROCK", "ROIV", "RPAY", "RUSHA", "RVMD", "S",
    "SAFE", "SASR", "SAVA", "SBH", "SBGI", "SBR", "SCSC", "SEMR", "SFNC", "SGH",
    "SGML", "SHAK", "SHOO", "SIGI", "SKT", "SLCA", "SLGN", "SLRC", "SMTC", "SNBR",
    "SNDX", "SPHR", "SPT", "SPTN", "SRAD", "SRRK", "SSTK", "STBA", "STC", "STEL",
    "STKL", "STNG", "SUP", "SVM", "SYBT", "TCBK", "TCBX", "TDW", "TGNA", "TGTX",
    "THFF", "THS", "TMDX", "TMST", "TNC", "TRMK", "TRNS", "TROX", "TRST", "TRTX",
    "TTEC", "TWI", "TWO", "UFCS", "UHT", "UNFI", "UPBD", "UTL", "VCYT", "VECO",
    "VERV", "VFC", "VIR", "VITL", "VKTX", "VNO", "VNTR", "VRE", "VRNT", "VSEC",
    "WABC", "WAFD", "WASH", "WCC", "WEAV", "WGO", "WHD", "WIRE", "WLK", "WNC",
    "WRBY", "WS", "WWEX", "XNCR", "XNOM", "XRX", "YEXT", "ZIM", "ZLAB",
])

FALLBACK_SYMBOLS = US_RECOMMENDATION_UNIVERSE[:FALLBACK_UNIVERSE_SIZE]

SYMBOL_GROUPS = {
    "all": US_RECOMMENDATION_UNIVERSE,
    "large": US_RECOMMENDATION_UNIVERSE[:1000],
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


def get_default_symbols(universe_size: int | None = None) -> list[str]:
    """Return the default recommendation universe capped to a supported size."""
    normalized_size = normalize_universe_size(universe_size)
    try:
        if not US_RECOMMENDATION_UNIVERSE:
            raise ValueError("Configured stock universe is empty.")

        limited_symbols = US_RECOMMENDATION_UNIVERSE[:normalized_size]
        logger.info(
            "Loaded default stock universe with %d symbols (requested size %d)",
            len(limited_symbols),
            normalized_size,
        )
        return limited_symbols
    except Exception:
        logger.exception("Falling back to the backup stock universe")
        return FALLBACK_SYMBOLS[:normalized_size]


def get_symbols_for_group(group: str | None, universe_size: int | None = None) -> list[str]:
    """Return a curated symbol subset for the requested group."""
    normalized_size = normalize_universe_size(universe_size)
    if not group:
        return get_default_symbols(normalized_size)

    normalized_group = group.strip().lower()
    selected_symbols = SYMBOL_GROUPS.get(normalized_group)
    if not selected_symbols:
        logger.warning("Unknown symbol group '%s', using defaults instead", normalized_group)
        return get_default_symbols(normalized_size)

    return _dedupe_symbols(selected_symbols)[:normalized_size]
