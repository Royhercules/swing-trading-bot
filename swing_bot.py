import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
from mailer import send_email

# ==============================
# CONFIG
# ==============================
LOOKBACK_SUPPORT = 80
HOLD_DAYS = 30
RR = 2
MAX_RUNUP = 0.15
TOP_N = 10

# ==============================
# HELPERS
# ==============================
def clean_ohlcv(df):
    df = df.copy()
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    return df[["Open","High","Low","Close","Volume"]].astype(float)

def add_indicators(df):
    df["SMA200"] = df["Close"].rolling(200).mean()
    df["EMA20"] = df["Close"].ewm(span=20).mean()
    df["EMA50"] = df["Close"].ewm(span=50).mean()

    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    rs = gain.rolling(14).mean() / loss.rolling(14).mean()
    df["RSI"] = 100 - (100 / (1 + rs))
    df["AVG_VOL"] = df["Volume"].rolling(20).mean()
    return df

def detect_support(df):
    recent = df.tail(LOOKBACK_SUPPORT)
    support = recent["Low"].min()
    touches = np.sum(abs(recent["Low"] - support) / support < 0.03)
    return touches >= 2, support

def ran_too_much(df):
    swing_low = df["Low"].tail(LOOKBACK_SUPPORT).min()
    return (df["Close"].iloc[-1] - swing_low) / swing_low > MAX_RUNUP

def daily_signal(df):
    last, prev = df.iloc[-1], df.iloc[-2]
    return (
        last["Close"] > last["Open"] and
        prev["RSI"] < 45 and last["RSI"] > prev["RSI"] and
        last["Volume"] > 1.1 * last["AVG_VOL"]
    )

def calc_sl_target(entry, support):
    sl = support * 0.97
    target = entry + (entry - sl) * RR
    return round(sl,2), round(target,2)

# ==============================
# MARKET FILTERS
# ==============================
def market_ok():
    nifty = clean_ohlcv(yf.download("^NSEI", period="2y", progress=False))
    vix = clean_ohlcv(yf.download("^INDIAVIX", period="2y", progress=False))

    nifty["SMA200"] = nifty["Close"].rolling(200).mean()

    return (
        nifty["Close"].iloc[-1] > nifty["SMA200"].iloc[-1] and
        vix["Close"].iloc[-1] < 20
    )

# ==============================
# STOCK UNIVERSE (TOP 500 SAFE)
# ==============================
from universe import nse_stocks

# ==============================
# MAIN SCAN
# ==============================
def run_scan():
    signals = []
    charts = []

    if not market_ok():
        send_email([], [], market_fail=True)
        return

    for symbol in nse_stocks:
        df = yf.download(symbol, period="1y", progress=False)
        if df.empty or len(df) < 220:
            continue

        df = add_indicators(clean_ohlcv(df))

        close = df["Close"].iloc[-1]
        sma200 = df["SMA200"].iloc[-1]

        if abs(close - sma200) / sma200 > 0.05:
            continue

        ok, support = detect_support(df)
        if not ok or ran_too_much(df) or not daily_signal(df):
            continue

        entry = round(close,2)
        sl, target = calc_sl_target(entry, support)

        # Chart
        plt.figure(figsize=(6,4))
        plt.plot(df["Close"], label="Close")
        plt.plot(df["SMA200"], label="SMA200")
        plt.axhline(support, color="green", linestyle="--")
        plt.title(symbol)
        plt.legend()
        fname = f"{symbol}.png"
        plt.savefig(fname)
        plt.close()

        charts.append(fname)
        signals.append({
            "Symbol": symbol,
            "Entry": entry,
            "SL": sl,
            "Target": target
        })

        if len(signals) >= TOP_N:
            break

    send_email(signals, charts)

if __name__ == "__main__":
    run_scan()
