from pathlib import Path

# ==========================================================
# BOT EXECUTION MODE
# ==========================================================

# False = normal behaviour
# True  = always assume market is closed
FORCE_MARKET_CLOSE = False


# ==========================================================
# BOT SCHEDULE
# ==========================================================

PREMARKET_UPDATE_HOUR = 8
PREMARKET_UPDATE_MINUTE = 0

PREMARKET_WAIT_HOUR = 9
PREMARKET_WAIT_MINUTE = 0

MARKET_START_HOUR = 9
MARKET_START_MINUTE = 15

MARKET_END_HOUR = 15
MARKET_END_MINUTE = 30

# ==========================================================
# LIVE STRIKE UNIVERSE
# ==========================================================

LIVE_STRIKE_BUFFER = 250

LIVE_UNIVERSE_UPDATE_SECONDS = 300      # 5 minutes

LIVE_OPTION_EXPIRIES = 3                # Current + next 2

LIVE_FUTURE_EXPIRIES = 3                # Current + next 2


BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"

INSTRUMENT_MASTER_DIR = DATA_DIR / "instrument_master"
TRACKER_DIR = DATA_DIR / "tracker"

GAP_DEBUG_FILE = BASE_DIR / "data" / "tracker" / "gap_debug.csv"

INDICES_DIR = DATA_DIR / "indices"

EXCHANGE = "NSE"
INDEX_NAME = "NIFTY 50"
INDEX_FOLDER = "nifty50"

SPOT_TOKEN = 256265

TIMEFRAMES = {
    "day": {
        "folder": "1d",
        "seconds": 86400,
        "buffer": 30,
        "chunk_days": 365
    },
    "60minute": {
        "folder": "1h",
        "seconds": 3600,
        "buffer": 20,
        "chunk_days": 90
    },
    "15minute": {
        "folder": "15m",
        "seconds": 900,
        "buffer": 10,
        "chunk_days": 60
    },
    "5minute": {
        "folder": "5m",
        "seconds": 300,
        "buffer": 10,
        "chunk_days": 30
    },
    "minute": {
        "folder": "1m",
        "seconds": 60,
        "buffer": 10,
        "chunk_days": 7
    }
}

START_DATE = "2020-01-01"
END_DATE = None

N_WEEKS = 12

STRIKE_STEP = {
    "NIFTY 50": 50,
    "SENSEX": 100,
    "BANKNIFTY": 100
}

MAX_RETRIES = 3
RETRY_DELAY_MINUTES = [5, 10, 15]

MARKET_START_HOUR = 9
MARKET_START_MINUTE = 15

MARKET_END_HOUR = 15
MARKET_END_MINUTE = 30

TIMEZONE = "Asia/Kolkata"

TRACKER_FILE = TRACKER_DIR / "tracker.parquet"
INSTRUMENT_MASTER_FILE = INSTRUMENT_MASTER_DIR / "instruments.parquet"
INSTRUMENT_MASTER_META = INSTRUMENT_MASTER_DIR / "metadata.json"