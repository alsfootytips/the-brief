#!/usr/bin/env python3
"""
The Brief — ingestion pipeline (Phase 2).

Pulls structured market data from free sources and writes JS data files
that the static HTML reads on load. No LLM summarization yet (that's Phase 3),
no notifications yet (Phase 4).

Sources:
  - yfinance        prices + day's % change for watchlist, indices, sectors
  - Finnhub         earnings calendar (next 14 days)
  - SEC EDGAR       8-K / 6-K filings for watchlist (last 7 days)

Run: python update.py
"""
from __future__ import annotations

import calendar
import json
import os
import re
import sys
import time
import datetime as dt
from pathlib import Path

import feedparser
import requests
import yfinance as yf
from dotenv import load_dotenv

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

RSS_FEEDS = [
    ('CNBC Markets', 'https://www.cnbc.com/id/15839069/device/rss/rss.html'),
    ('CNBC Top', 'https://www.cnbc.com/id/100003114/device/rss/rss.html'),
    ('MarketWatch', 'https://feeds.content.dowjones.io/public/rss/mw_topstories'),
    ('Yahoo Finance', 'https://finance.yahoo.com/news/rssindex'),
    ('BBC Business', 'https://feeds.bbci.co.uk/news/business/rss.xml'),
    ('NPR Business', 'https://feeds.npr.org/1006/rss.xml'),
    ('Investing.com News', 'https://www.investing.com/rss/news.rss'),
    ('Seeking Alpha Market', 'https://seekingalpha.com/market_currents.xml'),
]

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / 'data'
CACHE_DIR = ROOT / '.cache'

WATCHLIST_SECTOR_MAP = {
    'CRWV': 'XLK',
    'NBIS': 'XLK',
    'TTD': 'XLK',
    'AMD': 'XLK',
    'NVDA': 'XLK',
    'OSCR': 'XLV',
    'APA': 'XLE',
    'TPL': 'XLE',
    'OXY': 'XLE',
    'DG': 'XLP',
    'PWR': 'XLI',
    'GEV': 'XLI',
}

NAMES = {
    'SPY': 'SPDR S&P 500 ETF',
    'QQQ': 'Invesco QQQ Trust',
    'DIA': 'SPDR Dow Jones Industrial',
    'IWM': 'iShares Russell 2000 ETF',
    'XLE': 'Energy Select Sector',
    'XLF': 'Financial Select Sector',
    'XLK': 'Technology Select Sector',
    'XLV': 'Health Care Select Sector',
    'XLY': 'Consumer Discretionary Select',
    'XLP': 'Consumer Staples Select',
    'XLI': 'Industrial Select Sector',
    'XLU': 'Utilities Select Sector',
    'XLB': 'Materials Select Sector',
    'XLRE': 'Real Estate Select Sector',
    'XLC': 'Communication Services Select',
    'CRWV': 'CoreWeave',
    'NBIS': 'Nebius Group',
    'TTD': 'The Trade Desk',
    'OSCR': 'Oscar Health',
    'APA': 'APA Corp',
    'TPL': 'Texas Pacific Land',
    'OXY': 'Occidental Petroleum',
    'AMD': 'Advanced Micro Devices',
    'NVDA': 'NVIDIA',
    'DG': 'Dollar General',
    'PWR': 'Quanta Services',
    'GEV': 'GE Vernova',
}


def load_watchlist() -> dict:
    with open(ROOT / 'watchlist.json') as f:
        return json.load(f)


def fetch_live_prices(tickers: list[str]) -> dict[str, dict]:
    out = {}
    for t in tickers:
        try:
            url = f"https://query2.finance.yahoo.com/v8/finance/chart/{t}?interval=1m&range=1d&includePrePost=true"
            r = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            r.raise_for_status()
            data = r.json()
            result = data.get('chart', {}).get('result', [])
            if not result:
                continue
            res = result[0]
            meta = res.get('meta', {})
            ts = res.get('timestamp') or []
            quote = (res.get('indicators', {}).get('quote') or [{}])[0]
            closes = quote.get('close') or []
            last_close = None
            for v in reversed(closes):
                if v is not None:
                    last_close = float(v)
                    break
            prev_close = meta.get('chartPreviousClose') or meta.get('previousClose')
            if last_close is None or prev_close is None:
                continue
            chg_pct = (last_close - float(prev_close)) / float(prev_close) * 100
            out[t] = {
                'price': round(last_close, 2),
                'change_pct': round(chg_pct, 2),
                'market_state': meta.get('marketState'),
            }
            time.sleep(0.1)
        except Exception as e:
            print(f"  Live price fetch failed for {t}: {e}")
            continue
    return out


def fetch_movers(watchlist: dict, extra_tickers: list[str] | None = None) -> list[dict]:
    extras = list(extra_tickers or [])
    tickers = sorted(set(watchlist['followed'] + watchlist['indices'] + watchlist['sectors'] + extras))
    try:
        data = yf.download(
            tickers,
            period='5d',
            auto_adjust=True,
            progress=False,
            group_by='ticker',
            threads=True,
        )
    except Exception as e:
        print(f"  yfinance batch fetch failed: {e}")
        return []

    followed = set(watchlist['followed'])
    indices = set(watchlist['indices'])
    sectors = set(watchlist['sectors'])

    out = []
    for t in tickers:
        try:
            df = data[t] if t in data.columns.get_level_values(0) else data
            df = df.dropna(subset=['Close'])
            if len(df) < 2:
                continue
            today_close = float(df['Close'].iloc[-1])
            prev_close = float(df['Close'].iloc[-2])
            pct = (today_close - prev_close) / prev_close * 100 if prev_close else 0.0
            volume = float(df['Volume'].iloc[-1]) if 'Volume' in df else 0.0
            avg_vol = float(df['Volume'].mean()) if 'Volume' in df else 0.0
            vol_ratio = (volume / avg_vol) if avg_vol > 0 else None
            out.append({
                'ticker': t,
                'name': NAMES.get(t, t),
                'price': round(today_close, 2),
                'change_pct': round(pct, 2),
                'volume_ratio': round(vol_ratio, 2) if vol_ratio is not None else None,
                'is_watchlist': t in followed,
                'is_index': t in indices,
                'is_sector': (t in sectors) and (t not in indices),
            })
        except Exception as e:
            print(f"  Mover parse failed for {t}: {e}")
            continue

    print("  Fetching live (incl. pre/post-market) prices for watchlist + picks...")
    live_targets = list(set(watchlist['followed'] + extras))
    live = fetch_live_prices(live_targets)
    patched = 0
    for m in out:
        if m['ticker'] in live:
            lp = live[m['ticker']]
            m['price'] = lp['price']
            m['change_pct'] = lp['change_pct']
            m['market_state'] = lp.get('market_state')
            patched += 1
    print(f"  Patched {patched} tickers with live prices")

    return out


MACRO_TICKERS = {
    '^TNX': '10Y Treasury yield',
    '^FVX': '5Y Treasury yield',
    '^IRX': '13W T-Bill yield',
    '^TYX': '30Y Treasury yield',
    '^VIX': 'VIX (volatility)',
    'GC=F': 'Gold futures',
    'CL=F': 'WTI Crude futures',
    'DX-Y.NYB': 'US Dollar Index',
    'BTC-USD': 'Bitcoin',
}

FRED_LIQUIDITY_SERIES = {
    'WALCL': 'Fed balance sheet ($M)',
    'M2SL': 'M2 money supply ($B)',
    'RRPONTSYD': 'Overnight reverse repo ($B)',
}


def fetch_macro_snapshot() -> dict:
    cache = CACHE_DIR / 'macro.json'
    if cache.exists() and (time.time() - cache.stat().st_mtime) < 3600:
        try:
            return json.loads(cache.read_text())
        except Exception:
            pass

    out: dict = {}
    try:
        data = yf.download(
            list(MACRO_TICKERS.keys()),
            period='10d',
            auto_adjust=True,
            progress=False,
            threads=True,
            group_by='ticker',
        )
    except Exception as e:
        print(f"  Macro fetch failed: {e}")
        return {}

    for t, name in MACRO_TICKERS.items():
        try:
            df = data[t] if data.columns.nlevels > 1 and t in data.columns.get_level_values(0) else data
            close = df['Close'].dropna()
            if len(close) < 2:
                continue
            current = float(close.iloc[-1])
            prev = float(close.iloc[-2])
            week_ago = float(close.iloc[-5]) if len(close) >= 5 else None
            out[t] = {
                'name': name,
                'value': round(current, 2),
                'change_pct_1d': round((current - prev) / prev * 100, 2) if prev else 0,
                'change_pct_1w': round((current - week_ago) / week_ago * 100, 2) if week_ago else None,
            }
        except Exception:
            continue

    if out:
        ten_y = out.get('^TNX', {}).get('value')
        bill_13w = out.get('^IRX', {}).get('value')
        if ten_y is not None and bill_13w is not None:
            spread = round(ten_y - bill_13w, 2)
            out['_yield_curve'] = {
                'spread_10y_13w_bps': int(spread * 100),
                'inverted': spread < 0,
            }

        if os.getenv('FRED_API_KEY'):
            try:
                fred_data = fetch_fred_liquidity()
                if fred_data:
                    out.update(fred_data)
            except Exception as e:
                print(f"  FRED liquidity fetch failed: {e}")

        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(out, indent=2))

    return out


def fetch_fred_liquidity() -> dict:
    key = os.getenv('FRED_API_KEY')
    if not key:
        return {}
    out = {}
    for series, name in FRED_LIQUIDITY_SERIES.items():
        try:
            url = f"https://api.stlouisfed.org/fred/series/observations?series_id={series}&api_key={key}&file_type=json&sort_order=desc&limit=2"
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            obs = r.json().get('observations', [])
            if not obs:
                continue
            current = float(obs[0]['value']) if obs[0].get('value') not in (None, '.', '') else None
            previous = float(obs[1]['value']) if len(obs) > 1 and obs[1].get('value') not in (None, '.', '') else None
            if current is None:
                continue
            out[f'FRED_{series}'] = {
                'name': name,
                'value': round(current, 2),
                'date': obs[0].get('date'),
                'change_pct': round((current - previous) / previous * 100, 2) if previous else None,
            }
            time.sleep(0.1)
        except Exception as e:
            print(f"  FRED {series} failed: {e}")
            continue
    return out


def format_macro_for_prompt(macro: dict) -> str:
    if not macro:
        return "(macro data not available)"
    lines = ["## Macro snapshot"]
    label_order = ['^TNX', '^IRX', '^TYX', '^VIX', 'GC=F', 'CL=F', 'DX-Y.NYB', 'BTC-USD']
    for t in label_order:
        m = macro.get(t)
        if not m:
            continue
        chg_1d = m.get('change_pct_1d')
        chg_1w = m.get('change_pct_1w')
        chg_str = f"({chg_1d:+.2f}% today" + (f", {chg_1w:+.2f}% 1w" if chg_1w is not None else "") + ")"
        lines.append(f"- {m.get('name')}: {m.get('value')} {chg_str}")
    yc = macro.get('_yield_curve')
    if yc:
        spread = yc['spread_10y_13w_bps']
        status = 'INVERTED' if yc['inverted'] else 'normal'
        lines.append(f"- Yield curve (10Y minus 13W): {spread:+d} bps · {status}")
    for k in ('FRED_WALCL', 'FRED_M2SL', 'FRED_RRPONTSYD'):
        m = macro.get(k)
        if m:
            lines.append(f"- {m.get('name')}: {m.get('value'):,} (as of {m.get('date')})")
    return "\n".join(lines)


def write_macro(macro: dict, out_path: Path) -> None:
    payload = {
        'generated_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'snapshot': macro,
    }
    out_path.write_text(to_js_var('theBriefMacro', payload))


def load_fundamentals_cache() -> dict:
    cache = CACHE_DIR / 'fundamentals.json'
    if not cache.exists():
        return {}
    if (time.time() - cache.stat().st_mtime) > 86400:
        return {}
    try:
        return json.loads(cache.read_text())
    except Exception:
        return {}


def save_fundamentals_cache(data: dict) -> None:
    cache = CACHE_DIR / 'fundamentals.json'
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(data, indent=2))


def fetch_fundamentals(watchlist: dict) -> dict:
    cached = load_fundamentals_cache()
    if cached:
        print(f"  Using cached fundamentals ({len(cached)} tickers)")
        return cached

    followed = watchlist['followed']
    finnhub_key = os.getenv('FINNHUB_API_KEY')
    out: dict[str, dict] = {}

    try:
        hist = yf.download(
            followed,
            period='1y',
            auto_adjust=True,
            progress=False,
            group_by='ticker',
            threads=True,
        )
    except Exception as e:
        print(f"  yfinance 1y history fetch failed: {e}")
        hist = None

    today = dt.date.today()
    year_start = dt.date(today.year, 1, 1)

    for ticker in followed:
        f: dict = {}

        if hist is not None:
            try:
                df = hist[ticker] if ticker in hist.columns.get_level_values(0) else hist
                close = df['Close'].dropna()
                if len(close) >= 2:
                    current = float(close.iloc[-1])
                    def ret_from(days_back: int) -> float | None:
                        if len(close) <= days_back:
                            return None
                        prior = float(close.iloc[-1 - days_back])
                        return round((current - prior) / prior * 100, 2) if prior else None
                    f['return_1m'] = ret_from(21)
                    f['return_3m'] = ret_from(63)
                    f['return_6m'] = ret_from(126)
                    f['return_1y'] = ret_from(252)
                    try:
                        ytd_start_idx = close.index.get_indexer([year_start.isoformat()], method='nearest')[0]
                        ytd_start = float(close.iloc[ytd_start_idx])
                        f['return_ytd'] = round((current - ytd_start) / ytd_start * 100, 2) if ytd_start else None
                    except Exception:
                        f['return_ytd'] = None
                    try:
                        f['return_52w_high'] = round(current / float(close.max()) * 100 - 100, 2)
                        f['return_52w_low'] = round(current / float(close.min()) * 100 - 100, 2)
                    except Exception:
                        pass
                    try:
                        daily_returns = close.pct_change().dropna()
                        if len(daily_returns) >= 30:
                            recent_30 = daily_returns.iloc[-30:]
                            vol_pct = float(recent_30.std()) * 100
                            f['realized_vol_30d_pct'] = round(vol_pct, 2)
                    except Exception:
                        pass
            except Exception as e:
                print(f"  Returns calc failed for {ticker}: {e}")

        try:
            info = yf.Ticker(ticker).info
            f.update({
                'trailing_pe': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'price_to_sales': info.get('priceToSalesTrailing12Months'),
                'price_to_book': info.get('priceToBook'),
                'enterprise_to_ebitda': info.get('enterpriseToEbitda'),
                'profit_margin': info.get('profitMargins'),
                'gross_margin': info.get('grossMargins'),
                'operating_margin': info.get('operatingMargins'),
                'revenue_growth_yoy': info.get('revenueGrowth'),
                'earnings_growth_qoq': info.get('earningsQuarterlyGrowth'),
                'market_cap': info.get('marketCap'),
                'beta': info.get('beta'),
                'dividend_yield': info.get('dividendYield'),
                'short_ratio': info.get('shortRatio'),
                'short_percent_of_float': info.get('shortPercentOfFloat'),
            })
        except Exception as e:
            print(f"  yfinance info failed for {ticker}: {e}")

        if finnhub_key:
            try:
                time.sleep(0.1)
                r = requests.get(
                    f"https://finnhub.io/api/v1/stock/recommendation?symbol={ticker}&token={finnhub_key}",
                    timeout=10,
                )
                r.raise_for_status()
                recs = r.json() or []
                if recs:
                    latest = recs[0]
                    f['analyst_recs'] = {
                        'strongBuy': latest.get('strongBuy'),
                        'buy': latest.get('buy'),
                        'hold': latest.get('hold'),
                        'sell': latest.get('sell'),
                        'strongSell': latest.get('strongSell'),
                        'period': latest.get('period'),
                    }
                    if len(recs) >= 2:
                        prev = recs[1]
                        f['analyst_recs_change'] = {
                            'buy_delta': (latest.get('buy', 0) or 0) - (prev.get('buy', 0) or 0),
                            'sell_delta': (latest.get('sell', 0) or 0) - (prev.get('sell', 0) or 0),
                        }
            except Exception as e:
                print(f"  Finnhub recommendations failed for {ticker}: {e}")

            try:
                time.sleep(0.1)
                r = requests.get(
                    f"https://finnhub.io/api/v1/stock/price-target?symbol={ticker}&token={finnhub_key}",
                    timeout=10,
                )
                r.raise_for_status()
                pt = r.json() or {}
                if pt.get('targetMean'):
                    f['price_target'] = {
                        'mean': pt.get('targetMean'),
                        'high': pt.get('targetHigh'),
                        'low': pt.get('targetLow'),
                        'last_updated': pt.get('lastUpdated'),
                    }
            except requests.exceptions.HTTPError as e:
                if e.response is not None and e.response.status_code == 403:
                    pass
                else:
                    print(f"  Finnhub price target failed for {ticker}: {e}")
            except Exception as e:
                print(f"  Finnhub price target failed for {ticker}: {e}")

            try:
                time.sleep(0.1)
                r = requests.get(
                    f"https://finnhub.io/api/v1/stock/insider-transactions?symbol={ticker}&token={finnhub_key}",
                    timeout=10,
                )
                r.raise_for_status()
                ins = r.json() or {}
                txns = ins.get('data', [])[:10]
                if txns:
                    buys = sum(1 for t in txns if (t.get('change') or 0) > 0)
                    sells = sum(1 for t in txns if (t.get('change') or 0) < 0)
                    f['insider_recent_90d'] = {'buys': buys, 'sells': sells, 'total': len(txns)}
            except Exception as e:
                print(f"  Finnhub insider failed for {ticker}: {e}")

        out[ticker] = f

    save_fundamentals_cache(out)
    return out


def fetch_earnings(watchlist: dict) -> list[dict]:
    key = os.getenv('FINNHUB_API_KEY')
    if not key:
        print("  FINNHUB_API_KEY not set, skipping earnings")
        return []

    today = dt.date.today()
    end = today + dt.timedelta(days=14)
    url = f"https://finnhub.io/api/v1/calendar/earnings?from={today}&to={end}&token={key}"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data = r.json().get('earningsCalendar', []) or []
    except Exception as e:
        print(f"  Finnhub earnings fetch failed: {e}")
        return []

    followed = set(watchlist['followed'])
    out = []
    for e in data:
        ticker = (e.get('symbol') or '').upper()
        out.append({
            'ticker': ticker,
            'date': e.get('date'),
            'hour': e.get('hour'),
            'eps_estimate': e.get('epsEstimate'),
            'revenue_estimate': e.get('revenueEstimate'),
            'is_watchlist': ticker in followed,
        })
    out.sort(key=lambda x: (not x['is_watchlist'], x['date'] or ''))
    return out


def get_cik_map() -> dict[str, str]:
    cache = CACHE_DIR / 'cik_map.json'
    if cache.exists() and (time.time() - cache.stat().st_mtime) < 86400 * 7:
        return json.loads(cache.read_text())

    ua = os.getenv('SEC_USER_AGENT', 'The Brief contact@example.com')
    try:
        r = requests.get(
            'https://www.sec.gov/files/company_tickers.json',
            headers={'User-Agent': ua},
            timeout=20,
        )
        r.raise_for_status()
        raw = r.json()
        result = {entry['ticker'].upper(): str(entry['cik_str']).zfill(10) for entry in raw.values()}
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(result))
        return result
    except Exception as e:
        print(f"  SEC CIK map fetch failed: {e}")
        if cache.exists():
            return json.loads(cache.read_text())
        return {}


def fetch_filings(watchlist: dict) -> list[dict]:
    cik_map = get_cik_map()
    if not cik_map:
        print("  No CIK map, skipping filings")
        return []

    ua = os.getenv('SEC_USER_AGENT', 'The Brief contact@example.com')
    cutoff = dt.date.today() - dt.timedelta(days=7)
    out = []

    for ticker in watchlist['followed']:
        cik = cik_map.get(ticker.upper())
        if not cik:
            continue
        url = f"https://data.sec.gov/submissions/CIK{cik}.json"
        try:
            time.sleep(0.15)
            r = requests.get(url, headers={'User-Agent': ua}, timeout=15)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"  EDGAR fetch failed for {ticker}: {e}")
            continue

        recent = data.get('filings', {}).get('recent', {})
        forms = recent.get('form', [])
        dates = recent.get('filingDate', [])
        accessions = recent.get('accessionNumber', [])
        primary_docs = recent.get('primaryDocument', [])

        for i, form in enumerate(forms):
            if form not in ('8-K', '6-K'):
                continue
            try:
                filing_date = dt.date.fromisoformat(dates[i])
            except (ValueError, IndexError):
                continue
            if filing_date < cutoff:
                continue
            accession = accessions[i].replace('-', '')
            doc = primary_docs[i] if i < len(primary_docs) else ''
            out.append({
                'ticker': ticker,
                'form': form,
                'date': str(filing_date),
                'url': f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession}/{doc}",
            })

    out.sort(key=lambda x: x['date'], reverse=True)
    return out


def fetch_news(watchlist: dict) -> list[dict]:
    key = os.getenv('FINNHUB_API_KEY')
    if not key:
        print("  FINNHUB_API_KEY not set, skipping company news")
        return []

    today = dt.date.today()
    start = today - dt.timedelta(days=3)
    out = []

    for ticker in watchlist['followed']:
        url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from={start}&to={today}&token={key}"
        try:
            time.sleep(0.1)
            r = requests.get(url, timeout=15)
            r.raise_for_status()
            items = r.json() or []
        except Exception as e:
            print(f"  News fetch failed for {ticker}: {e}")
            continue
        for item in items[:3]:
            headline = (item.get('headline') or '').strip()
            if not headline:
                continue
            out.append({
                'ticker': ticker,
                'headline': headline,
                'source': item.get('source'),
                'url': item.get('url'),
                'datetime': item.get('datetime'),
                'is_watchlist': True,
            })
    return out


MARKET_MOVERS = {
    'Trump': ['Trump'],
    'Musk': ['Musk', 'Elon'],
    'Powell': ['Powell', 'Jerome Powell'],
    'Yellen': ['Yellen', 'Janet Yellen'],
    'Bessent': ['Bessent'],
    'Lutnick': ['Lutnick'],
    'Xi': ['Xi Jinping'],
    'Putin': ['Putin'],
    'Bezos': ['Bezos'],
    'Buffett': ['Buffett'],
    'Dimon': ['Jamie Dimon'],
    'Lagarde': ['Lagarde'],
    'Iran': ['Iran', 'Tehran'],
    'OPEC': ['OPEC'],
    'Fed': ['Federal Reserve', 'FOMC'],
}

STATEMENT_KEYWORDS = {
    'says', 'said', 'announced', 'announces', 'signs', 'signed', 'vetoes', 'vetoed',
    'warns', 'warned', 'threatens', 'threatened', 'declared', 'declares',
    'orders', 'ordered', 'tweets', 'posts', 'posted', 'comments', 'commented',
    'rejects', 'rejected', 'accepts', 'accepted', 'launches', 'launched',
    'imposes', 'imposed', 'lifts', 'lifted', 'cuts', 'cut', 'hikes', 'hiked',
    'pauses', 'paused', 'urges', 'urged', 'demands', 'demanded',
}


def detect_mover_statement(headline: str) -> dict | None:
    if not headline:
        return None
    h_lower = headline.lower()
    matched_movers = []
    for mover, aliases in MARKET_MOVERS.items():
        for alias in aliases:
            if alias.lower() in h_lower:
                matched_movers.append(mover)
                break
    if not matched_movers:
        return None
    words = set(re.findall(r'[a-zA-Z]+', h_lower))
    has_statement_verb = any(k in words for k in STATEMENT_KEYWORDS)
    if not has_statement_verb:
        return None
    return {
        'movers': matched_movers,
    }


def fetch_rss_news() -> list[dict]:
    ua = os.getenv('SEC_USER_AGENT', 'The Brief contact@example.com')
    out = []
    for source_name, url in RSS_FEEDS:
        try:
            r = requests.get(url, timeout=12, headers={'User-Agent': ua})
            r.raise_for_status()
            parsed = feedparser.parse(r.content)
        except Exception as e:
            print(f"  RSS {source_name} failed: {e}")
            continue
        if not parsed.entries:
            print(f"  RSS {source_name} returned no items")
            continue
        for entry in parsed.entries[:8]:
            headline = (getattr(entry, 'title', '') or '').strip()
            link = getattr(entry, 'link', '') or ''
            if not headline:
                continue
            ts = None
            time_struct = getattr(entry, 'published_parsed', None) or getattr(entry, 'updated_parsed', None)
            if time_struct:
                try:
                    ts = calendar.timegm(time_struct)
                except Exception:
                    ts = None
            out.append({
                'ticker': None,
                'headline': headline,
                'source': source_name,
                'url': link,
                'datetime': ts,
                'is_watchlist': False,
            })
    return out


def fetch_general_news() -> list[dict]:
    key = os.getenv('FINNHUB_API_KEY')
    if not key:
        return []
    url = f"https://finnhub.io/api/v1/news?category=general&token={key}"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        items = r.json() or []
    except Exception as e:
        print(f"  General news fetch failed: {e}")
        return []
    out = []
    for item in items[:10]:
        headline = (item.get('headline') or '').strip()
        if not headline:
            continue
        out.append({
            'ticker': None,
            'headline': headline,
            'source': item.get('source'),
            'url': item.get('url'),
            'datetime': item.get('datetime'),
            'is_watchlist': False,
        })
    return out


def to_js_var(name: str, payload: dict) -> str:
    return f"window.{name} = {json.dumps(payload, indent=2, default=str)};\n"


PUSHOVER_URL = 'https://api.pushover.net/1/messages.json'
BRIEF_URL = 'https://alsfootytips.github.io/the-brief/the-brief.html'


def load_notifications_state() -> dict:
    p = DATA_DIR / 'notifications.json'
    if not p.exists():
        return {'sent': []}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {'sent': []}


def save_notifications_state(state: dict) -> None:
    p = DATA_DIR / 'notifications.json'
    p.parent.mkdir(parents=True, exist_ok=True)
    state['sent'] = list(state.get('sent', []))[-500:]
    p.write_text(json.dumps(state, indent=2))


def notify_pushover(title: str, message: str, url_anchor: str | None = None,
                    priority: int = 0) -> bool:
    """Send a Pushover notification.

    priority:
      +1 = high — louder alert, bypasses iPhone Do Not Disturb. Use for tactical
           BUY signals and all SELL signals — anything where minutes matter.
       0 = normal — standard push. Use for strategic/long-term BUYs, falsification
           WATCH alerts, and imminent earnings.
      -1 = quiet — no sound or vibration, appears in notification tray only.
           Use for big-move FYIs and material filings (awareness, not action).
      -2 = silent in app only (rarely used).
    """
    user = os.getenv('PUSHOVER_USER_KEY')
    token = os.getenv('PUSHOVER_APP_TOKEN')
    if not user or not token:
        return False
    # Clamp to Pushover's allowed range; we don't use +2 (which requires retry+expire).
    if priority > 1:
        priority = 1
    if priority < -2:
        priority = -2
    payload = {
        'token': token,
        'user': user,
        'title': title[:250],
        'message': message[:1024],
        'url': f"{BRIEF_URL}{url_anchor}" if url_anchor else BRIEF_URL,
        'url_title': 'Open in The Brief',
        'priority': priority,
    }
    try:
        r = requests.post(PUSHOVER_URL, data=payload, timeout=10)
        if r.status_code != 200:
            print(f"  Pushover non-200: {r.status_code} {r.text[:200]}")
            return False
        return True
    except Exception as e:
        print(f"  Pushover send failed: {e}")
        return False


FALSIFICATION_STOPWORDS = {
    'above', 'below', 'over', 'under', 'when', 'where', 'with', 'this', 'that',
    'these', 'those', 'from', 'into', 'than', 'then', 'they', 'them', 'their',
    'have', 'have', 'will', 'would', 'could', 'should', 'must', 'might', 'been',
    'being', 'before', 'after', 'while', 'about', 'into', 'such', 'each', 'some',
    'most', 'just', 'only', 'also', 'very', 'much', 'more', 'less', 'still',
    'thesis', 'fails', 'works', 'wrong', 'right', 'good', 'bad', 'years', 'year',
    'quarters', 'quarter', 'months', 'month', 'weeks', 'week', 'days', 'day',
    'company', 'companies', 'stock', 'stocks', 'price', 'prices', 'market', 'markets',
}


def extract_falsification_keywords(text: str) -> set[str]:
    keywords = set()
    for word in re.findall(r"[A-Za-z]{5,}", text):
        w = word.lower()
        if w in FALSIFICATION_STOPWORDS:
            continue
        keywords.add(w)
    return keywords


def find_falsification_matches(picks_data: dict, news: list[dict]) -> list[dict]:
    matches = []
    for pick in picks_data.get('picks', []):
        if pick.get('status') != 'open':
            continue
        ticker = pick.get('ticker')
        falsif = pick.get('falsification') or ''
        if not falsif or not ticker:
            continue
        keywords = extract_falsification_keywords(falsif)
        if len(keywords) < 3:
            continue
        for n in news:
            if (n.get('ticker') or '').upper() != ticker.upper():
                continue
            headline = (n.get('headline') or '').lower()
            hits = {k for k in keywords if k in headline}
            if len(hits) >= 2:
                matches.append({
                    'pick': pick,
                    'news': n,
                    'matched': sorted(hits)[:4],
                })
                break
    return matches


def dispatch_notifications(notif_state: dict, movers: list[dict], filings: list[dict],
                           earnings: list[dict], picks_data: dict,
                           new_picks: list[dict], closed_picks: list[dict],
                           news: list[dict] | None = None) -> None:
    if not os.getenv('PUSHOVER_USER_KEY') or not os.getenv('PUSHOVER_APP_TOKEN'):
        print("  Pushover keys not set, skipping notifications")
        return

    sent: set[str] = set(notif_state.get('sent', []))
    today = dt.date.today().isoformat()
    followed = set()
    try:
        followed = set(load_watchlist()['followed'])
    except Exception:
        pass

    movers_by_ticker = {m['ticker']: m for m in movers}
    delivered = 0

    for p in new_picks:
        key = f"new_pick:{p['id']}"
        if key in sent:
            continue
        horizon_lbl = horizon_category(p.get('horizon_weeks'))
        pick_type = (p.get('pick_type') or '').lower()
        # Tactical buys are time-critical; long-term holds aren't. Strategic in between.
        priority = 1 if pick_type == 'tactical' else 0
        prefix = 'HOLD' if pick_type == 'long-term' else 'BUY'
        title = f"{prefix} signal: {p['ticker']} ({horizon_lbl})"
        target = p.get('target_pct')
        stop = p.get('stop_pct')
        horizon_weeks = p.get('horizon_weeks')
        if target is None or stop is None or horizon_weeks is None:
            # Long-term HOLDs have no fixed target/stop/horizon
            msg = (
                f"Entry ${p.get('entry_price')} · long-term hold (no target, no stop).\n\n"
                f"{p.get('thesis', '')[:280]}"
            )
        else:
            msg = (
                f"Entry ${p.get('entry_price')} · target {target:+g}% · "
                f"stop {stop:+g}% · {horizon_weeks}w horizon.\n\n"
                f"{p.get('thesis', '')[:260]}"
            )
        if notify_pushover(title, msg, '#picks', priority=priority):
            sent.add(key)
            delivered += 1

    for p in closed_picks:
        key = f"pick_closed:{p['id']}:{p.get('closed_at')}"
        if key in sent:
            continue
        status = p.get('status', '').upper()
        outcome_label = {
            'HIT': 'target reached',
            'MISS': 'stop hit',
            'EXPIRED': 'horizon expired',
        }.get(status, status.lower())
        title = f"SELL signal: {p['ticker']} — {outcome_label}"
        msg = (
            f"Closed at {p.get('closed_pct', 0):+.2f}% "
            f"({p.get('closed_reason', '')}).\n"
            f"Entry ${p.get('entry_price')}, exit ${p.get('closed_price')}."
        )
        # Exits are always time-critical — slippage costs you most on the way out.
        if notify_pushover(title, msg, '#picks', priority=1):
            sent.add(key)
            delivered += 1

    if news:
        for match in find_falsification_matches(picks_data, news):
            p = match['pick']
            n = match['news']
            key = f"falsif_news:{p.get('id')}:{n.get('url', '')[:80]}"
            if key in sent:
                continue
            title = f"WATCH: {p['ticker']} — news may trigger falsification"
            msg = (
                f"\"{(n.get('headline') or '')[:140]}\"\n"
                f"Source: {n.get('source')}. Matched: {', '.join(match['matched'])}.\n"
                f"Falsification: {(p.get('falsification') or '')[:200]}"
            )
            # Normal priority — important read, but not auto-action.
            if notify_pushover(title, msg, '#picks', priority=0):
                sent.add(key)
                delivered += 1

    for m in movers:
        if m.get('ticker') not in followed:
            continue
        if abs(m.get('change_pct', 0) or 0) < 5:
            continue
        key = f"big_move:{m['ticker']}:{today}"
        if key in sent:
            continue
        direction = 'up' if m['change_pct'] > 0 else 'down'
        title = f"{m['ticker']} {direction} {abs(m['change_pct']):.1f}%"
        msg = f"{m.get('name', m['ticker'])} at ${m.get('price')} today. Read the live feed for context."
        # FYI only — silent push so it doesn't interrupt.
        if notify_pushover(title, msg, '#live', priority=-1):
            sent.add(key)
            delivered += 1

    for f in filings:
        if f.get('ticker') not in followed:
            continue
        key = f"filing:{f['ticker']}:{f.get('form')}:{f.get('date')}"
        if key in sent:
            continue
        title = f"{f['ticker']} filed {f.get('form')}"
        msg = f"Material event filing on {f.get('date')}. View the document via the live feed."
        # Awareness only — silent.
        if notify_pushover(title, msg, '#live', priority=-1):
            sent.add(key)
            delivered += 1

    today_date = dt.date.today()
    for e in earnings:
        if not e.get('is_watchlist'):
            continue
        try:
            edate = dt.date.fromisoformat(e.get('date', ''))
        except (TypeError, ValueError):
            continue
        if not 0 <= (edate - today_date).days <= 1:
            continue
        key = f"earnings_imminent:{e['ticker']}:{e['date']}"
        if key in sent:
            continue
        hour = e.get('hour') or ''
        when_label = {'bmo': 'before market open', 'amc': 'after market close'}.get(hour, hour)
        title = f"{e['ticker']} reports {edate}"
        msg = f"{e['ticker']} earnings {edate} {when_label}. Open positions and watchlist affected."
        # Normal priority — you may want to position before the print.
        if notify_pushover(title, msg, '#weekly', priority=0):
            sent.add(key)
            delivered += 1

    notif_state['sent'] = list(sent)
    print(f"  Sent {delivered} new notifications")


def load_picks() -> dict:
    p = ROOT / 'picks.json'
    if not p.exists():
        return {'picks': []}
    try:
        return json.loads(p.read_text())
    except Exception as e:
        print(f"  Failed to parse picks.json: {e}")
        return {'picks': []}


def save_picks(data: dict) -> None:
    p = ROOT / 'picks.json'
    p.write_text(json.dumps(data, indent=2))


def horizon_category(weeks: int | float | None) -> str:
    if weeks is None:
        return 'Unknown'
    try:
        w = float(weeks)
    except (TypeError, ValueError):
        return 'Unknown'
    if w <= 3:
        return 'Short-term'
    if w <= 7:
        return 'Medium-term'
    return 'Long-term'


def update_picks(picks_data: dict, movers: list[dict], news: list[dict]) -> dict:
    movers_by_ticker = {m['ticker']: m for m in movers}
    news_counts: dict[str, int] = {}
    for n in news:
        t = n.get('ticker')
        if t:
            news_counts[t] = news_counts.get(t, 0) + 1

    today = dt.date.today()
    changed = False

    for pick in picks_data.get('picks', []):
        ticker = pick.get('ticker')
        m = movers_by_ticker.get(ticker)
        entry = pick.get('entry_price')

        pick['pick_type'] = pick.get('pick_type', 'strategic')
        if pick['pick_type'] == 'long-term':
            pick['horizon_label'] = 'Long-term hold'
        else:
            pick['horizon_label'] = horizon_category(pick.get('horizon_weeks'))
        pick['direction'] = pick.get('direction', 'long')

        if m and entry:
            current_price = m.get('price')
            current_pct = (current_price - entry) / entry * 100 if entry else 0
            pick['current_price'] = round(current_price, 2)
            pick['current_pct'] = round(current_pct, 2)
            pick['change_pct_today'] = m.get('change_pct')
            pick['name'] = m.get('name', ticker)
            pick['news_count'] = news_counts.get(ticker, 0)

            if pick.get('status') == 'open':
                target = pick.get('target_pct')
                stop = pick.get('stop_pct')
                horizon = pick.get('horizon_weeks')
                try:
                    entered = dt.date.fromisoformat(pick.get('entered_at', ''))
                except (TypeError, ValueError):
                    entered = today
                days_elapsed = (today - entered).days
                weeks_elapsed = days_elapsed / 7
                pick['days_elapsed'] = days_elapsed
                if horizon:
                    pick['days_remaining'] = max(0, int(horizon * 7 - days_elapsed))
                else:
                    pick['days_remaining'] = None

                if pick.get('pick_type') == 'long-term':
                    pass
                else:
                    if target is not None and current_pct >= target:
                        pick['status'] = 'hit'
                        pick['closed_at'] = today.isoformat()
                        pick['closed_price'] = round(current_price, 2)
                        pick['closed_pct'] = round(current_pct, 2)
                        pick['closed_reason'] = f'target_hit (+{target}%)'
                        changed = True
                    elif stop is not None and current_pct <= stop:
                        pick['status'] = 'miss'
                        pick['closed_at'] = today.isoformat()
                        pick['closed_price'] = round(current_price, 2)
                        pick['closed_pct'] = round(current_pct, 2)
                        pick['closed_reason'] = f'stop_hit ({stop}%)'
                        changed = True
                    elif horizon and weeks_elapsed >= horizon:
                        pick['status'] = 'expired'
                        pick['closed_at'] = today.isoformat()
                        pick['closed_price'] = round(current_price, 2)
                        pick['closed_pct'] = round(current_pct, 2)
                        pick['closed_reason'] = f'horizon_reached ({horizon} weeks)'
                        changed = True

    if changed:
        save_picks(picks_data)

    return picks_data


EDITORIAL_SYSTEM_PROMPT = """You are the editorial voice of "The Brief", a weekly investing brief designed to teach how to read markets — not to recommend trades. Your output is calibrated, honest, and frameworks-first.

INVIOLABLE RULES:
1. Never make buy/sell/hold recommendations. Frame opportunities as "worth attention" or "setup worth homework" — never "buy" or "sell".
2. Every factual or interpretive claim must be wrapped in a confidence span. Use these EXACT HTML strings:
   - <span class="confidence confidence-fact">Fact</span> for verifiable numbers, reported events, official statements
   - <span class="confidence confidence-interp">Interp</span> for reasonable interpretation, contextual framing
   - <span class="confidence confidence-speculation">Spec</span> for forward-looking speculation
3. Wrap every ticker mention in <span class="ticker" data-ticker="SYMBOL">SYMBOL</span>. Tickers are uppercase.
4. Filter ruthlessly. If 2 things mattered today, write about 2. Never pad to fill space. The Brief's edge is what it excludes.
5. No clickbait headlines. No exclamation marks. No urgency manufacturing.
6. Voice: calm, calibrated, mildly literary. Short sentences. Names the trade-off rather than asserting one side.

STYLE EXAMPLES (match this register):
- "Two data points in a row is the start of a trend."
- "Headlines say investors are confused. They aren't. The headline writer is."
- "Owning energy stocks right now means you're implicitly betting on continued conflict."
- "The market is starting to behave as if $100 oil is the new baseline, not a spike."
- "Sharp money doesn't liquidate on one print; it shifts the mix."

WORKED EXAMPLE OUTPUT (match this exactly in structure, length, density, and voice):
{
  "headline": "Nebius confirms the AI-cloud question without answering it",
  "body": "<p>Markets opened with one question: would Nebius validate or refute the worry that CoreWeave's miss raised? <span class=\\"confidence confidence-fact\\">Fact</span> Pre-market, <span class=\\"ticker\\" data-ticker=\\"NBIS\\">NBIS</span> reported Q1 revenue of $317M — exactly in line with consensus — and reiterated its 2026 ARR target. <span class=\\"confidence confidence-interp\\">Interp</span> That's the 'thesis lives another quarter' outcome. Not strong enough to dismiss the AI-cloud capex worry. Not weak enough to confirm it. The market read it as a non-event and moved on.</p><p><span class=\\"confidence confidence-fact\\">Fact</span> April CPI printed at 2.6% versus 2.7% expected. <span class=\\"confidence confidence-interp\\">Interp</span> A soft reading on a metric the Fed cares about — and the response was textbook. The Russell 2000 rallied 1.4%, the S&amp;P added 0.6%. <span class=\\"confidence confidence-interp\\">Interp</span> The rotation pattern from last week's brief is holding: when macro prints soften, small-caps benefit disproportionately. Watch whether this persists into June's Fed meeting.</p><p><span class=\\"ticker\\" data-ticker=\\"TTD\\">TTD</span> closed +2% on no news, on rising volume. <span class=\\"confidence confidence-speculation\\">Spec</span> Either bargain-hunting after the post-earnings drawdown, or short covering. Either way, the structural concerns (walled gardens, retail media networks taking share) haven't changed. Worth watching, not chasing.</p>"
}

Note the density: every claim tagged. Every ticker wrapped. Three short paragraphs. No filler. The headline frames the thread rather than reporting it.

OUTPUT FORMAT (strict JSON, nothing else, no markdown fence, no preamble, no commentary before or after the JSON):
{
  "headline": "5-12 words framing the day's thread. Sentence case (only proper nouns capitalized).",
  "body": "<p>Paragraph 1: lede establishing the day's question or theme.</p><p>Paragraph 2: the second thing that mattered.</p><p>Paragraph 3: optional — a smaller observation worth noting.</p>"
}

LENGTH: body 180-350 words. Tighter is better. If 2 things mattered, write 2 paragraphs not 3.

THINGS THAT WILL BE REJECTED:
- Any "buy", "sell", "hold", "I'd recommend", "you should" language
- Untagged claims (every factual/interpretive sentence needs a confidence span)
- Bare ticker mentions (every TICKER must be wrapped)
- Emoji, exclamation marks, all-caps for emphasis
- Padding paragraphs to hit a word count
- Speculation tagged as Fact, or vice versa

If today's data is genuinely uneventful, write one short paragraph saying so honestly. Don't manufacture interest."""


def build_editorial_user_prompt(movers: list[dict], news: list[dict],
                                filings: list[dict], earnings: list[dict],
                                watchlist: dict, picks_data: dict,
                                macro: dict | None = None) -> str:
    today = dt.date.today().isoformat()
    followed = set(watchlist['followed'])

    watchlist_movers = sorted(
        [m for m in movers if m['ticker'] in followed],
        key=lambda x: abs(x.get('change_pct', 0) or 0), reverse=True
    )
    big_movers = [m for m in movers if abs(m.get('change_pct', 0) or 0) >= 3 and m['ticker'] not in followed]
    indices = [m for m in movers if m.get('is_index')]
    sectors = sorted([m for m in movers if m.get('is_sector')],
                     key=lambda x: abs(x.get('change_pct', 0) or 0), reverse=True)[:5]

    watchlist_news = [n for n in news if n.get('is_watchlist')][:25]
    general_news = [n for n in news if not n.get('is_watchlist')][:8]
    watchlist_earnings = [e for e in earnings if e.get('is_watchlist')][:5]
    watchlist_filings = filings[:10]

    open_picks = [p for p in picks_data.get('picks', []) if p.get('status') == 'open']

    parts = [f"# Today's data — {today}\n"]

    if macro:
        parts.append(format_macro_for_prompt(macro))
        parts.append("")

    parts.append("## Watchlist price moves (today vs prior close)")
    if watchlist_movers:
        for m in watchlist_movers:
            parts.append(f"- {m['ticker']} ({m.get('name', '')}): {m['change_pct']:+.2f}% @ ${m['price']}")
    else:
        parts.append("- (none)")

    parts.append("\n## Sector ETFs (today)")
    for m in sectors:
        parts.append(f"- {m['ticker']} ({m.get('name', '')}): {m['change_pct']:+.2f}%")

    parts.append("\n## Indices")
    for m in indices:
        parts.append(f"- {m['ticker']} ({m.get('name', '')}): {m['change_pct']:+.2f}%")

    if big_movers:
        parts.append("\n## Other notable movers (≥3% absolute)")
        for m in big_movers[:6]:
            parts.append(f"- {m['ticker']}: {m['change_pct']:+.2f}% @ ${m['price']}")

    parts.append("\n## Watchlist news (last 3 days)")
    if watchlist_news:
        for n in watchlist_news:
            parts.append(f"- [{n.get('ticker')}] {n.get('headline')} ({n.get('source')})")
    else:
        parts.append("- (none)")

    if general_news:
        parts.append("\n## General market news")
        for n in general_news:
            parts.append(f"- {n.get('headline')} ({n.get('source')})")

    if watchlist_filings:
        parts.append("\n## Recent SEC filings (watchlist, last 7 days)")
        for f in watchlist_filings:
            parts.append(f"- {f['ticker']}: {f['form']} on {f['date']}")

    if watchlist_earnings:
        parts.append("\n## Upcoming watchlist earnings (next 14 days)")
        for e in watchlist_earnings:
            hour = e.get('hour') or ''
            rev = e.get('revenue_estimate')
            parts.append(f"- {e['ticker']} on {e['date']} ({hour}). EPS est. {e.get('eps_estimate')}, revenue est. ${rev:,.0f}" if rev else f"- {e['ticker']} on {e['date']} ({hour})")

    if open_picks:
        parts.append("\n## Active tracked picks")
        for p in open_picks:
            parts.append(f"- {p['ticker']}: entered {p['entered_at']} @ ${p['entry_price']}, current {p.get('current_pct', 0):+.2f}%, thesis: {p['thesis'][:120]}")

    parts.append("\n---\nWrite today's daily entry. Filter aggressively — only what actually mattered. Tag every claim. JSON output only.")
    return "\n".join(parts)


def summarize_daily(movers: list[dict], news: list[dict], filings: list[dict],
                    earnings: list[dict], watchlist: dict, picks_data: dict,
                    macro: dict | None = None) -> dict | None:
    key = os.getenv('ANTHROPIC_API_KEY')
    if not key or not Anthropic:
        print("  ANTHROPIC_API_KEY not set (or anthropic SDK missing), skipping daily summary")
        return None

    user_prompt = build_editorial_user_prompt(movers, news, filings, earnings, watchlist, picks_data, macro)

    try:
        client = Anthropic(api_key=key)
        resp = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=2000,
            system=EDITORIAL_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except Exception as e:
        print(f"  Claude API call failed: {e}")
        return None

    text = ''.join(block.text for block in resp.content if hasattr(block, 'text'))
    text = text.strip()

    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  Claude returned non-JSON: {e}")
        print(f"  Raw: {text[:200]}")
        return None

    if not data.get('headline') or not data.get('body'):
        print("  Claude response missing headline or body")
        return None

    return {
        'date': dt.date.today().isoformat(),
        'headline': data['headline'].strip(),
        'body': data['body'].strip(),
        'generated_by': f"claude-sonnet-4-5 · {dt.datetime.now(dt.timezone.utc).isoformat()}",
    }


PICKS_SYSTEM_PROMPT = """You are picking 3-5 stocks for "The Brief"'s AI Experiment track. These are NOT investment recommendations. They are labeled experiments to test whether AI-driven setup identification has measurable skill over time. The user has explicitly opted into this experiment with the understanding that misses are expected.

For each pick, you MUST provide every field:
- ticker: uppercase symbol (must appear in the data provided)
- sector: One short category. Choose from: Technology, Healthcare, Energy, Financials, Industrials, Consumer, Materials, Utilities, Real Estate, Communication, Macro / ETF.
- thesis: 1-2 sentence summary. Used in notifications. Plain text, no HTML.
- rationale: 2-4 paragraph expansion (HTML string). Multi-paragraph with <p> tags. Wrap tickers in <span class="ticker" data-ticker="SYMBOL">SYMBOL</span>. Tag claims:
  * <span class="confidence confidence-fact">Fact</span> for verifiable numbers/events
  * <span class="confidence confidence-interp">Interp</span> for interpretation
  * <span class="confidence confidence-speculation">Spec</span> for forward speculation
  Use <strong> for emphasis. Density: every claim tagged, every ticker wrapped.
- horizon_weeks: integer 1-12. Match to thesis type:
  * Event-driven (earnings, FOMC, regulatory date): 1-3 weeks
  * Cyclical/macro: 4-8 weeks
  * Structural/valuation: 6-12 weeks
- horizon_reason: 1-2 sentence HTML explanation of WHY this horizon. Can use confidence tags.
- target_pct: integer or float. Realistic. 8-20% is typical. NEVER > 30%.
- stop_pct: negative number. Typically -8 to -15%. Higher-vol names get wider stops.
- falsification: 1-2 sentences. SPECIFIC and MEASURABLE. Plain text. Examples:
  - GOOD: "Q2 medical loss ratio prints above 75%, OR membership growth turns negative YoY."
  - BAD: "Thesis fails if the company underperforms."

DIVERSITY RULES:
- Vary thesis types across the picks. Don't make all 3 earnings plays or all 3 valuation plays.
- Vary horizons. Don't make every pick the same horizon.
- Spread sectors where possible.

HARD RULES:
- Only pick tickers that appear in today's data dump (movers, watchlist, news, filings, or earnings).
- DO NOT pick any ticker that's in the "active picks" list provided.
- Be conservative on count. If only 2 genuine setups stand out, return 2. Never pad to hit 5.
- NEVER use words: "buy", "must own", "rocket", "soaring", "explode", "skyrocket", "guaranteed".
- NEVER imply certainty. The system's whole value is that misses get tracked.

USE FUNDAMENTALS:
The data dump includes valuation (P/E, P/S), growth (revenue/EPS YoY), margins, extended
returns (1m/3m/6m/YTD), analyst price targets, and recommendation breakdowns. Your thesis
MUST reference relevant fundamentals — not just news flow. A good thesis explains WHY a
stock is mispriced (cheap relative to peers, growth not yet recognized, analyst PT well
above current, insider buying, etc.) — not just "news happened."

If today's data shows nothing genuinely interesting (slow news, no movers, no upcoming catalysts), return an empty picks list. Honest zero is better than padded picks.

OUTPUT (strict JSON only, no markdown fence, no commentary):
{
  "picks": [
    {
      "ticker": "TICKER",
      "sector": "Technology",
      "thesis": "1-2 sentence plain-text summary",
      "rationale": "<p>Paragraph 1 with <span class=\\"confidence confidence-fact\\">Fact</span> and <span class=\\"ticker\\" data-ticker=\\"TICKER\\">TICKER</span> tags.</p><p>Paragraph 2.</p>",
      "horizon_weeks": 4,
      "horizon_reason": "Brief HTML explanation of horizon choice.",
      "target_pct": 15,
      "stop_pct": -10,
      "falsification": "Specific measurable criteria."
    }
  ]
}
"""


def build_picks_user_prompt(movers: list[dict], news: list[dict], filings: list[dict],
                            earnings: list[dict], watchlist: dict, picks_data: dict,
                            fundamentals: dict | None = None,
                            macro: dict | None = None) -> str:
    today = dt.date.today().isoformat()
    followed = set(watchlist['followed'])
    active_tickers = {p['ticker'] for p in picks_data.get('picks', []) if p.get('status') == 'open'}

    watchlist_movers = sorted(
        [m for m in movers if m['ticker'] in followed],
        key=lambda x: abs(x.get('change_pct', 0) or 0), reverse=True
    )
    big_movers = sorted(
        [m for m in movers if abs(m.get('change_pct', 0) or 0) >= 3 and m['ticker'] not in followed],
        key=lambda x: abs(x.get('change_pct', 0) or 0), reverse=True
    )[:10]
    sectors = sorted([m for m in movers if m.get('is_sector')],
                     key=lambda x: abs(x.get('change_pct', 0) or 0), reverse=True)[:5]

    watchlist_news = [n for n in news if n.get('is_watchlist')][:25]
    watchlist_earnings = [e for e in earnings if e.get('is_watchlist')]

    parts = [f"# Picks generation prompt — {today}"]
    parts.append(f"\n## Active picks (DO NOT pick these tickers again): {sorted(active_tickers) if active_tickers else '(none)'}")

    if macro:
        parts.append("")
        parts.append(format_macro_for_prompt(macro))

    parts.append("\n## Watchlist fundamentals + extended returns")
    parts.append(format_fundamentals_for_prompt(fundamentals or {}, watchlist['followed']))

    parts.append("\n## Watchlist price action this week")
    for m in watchlist_movers:
        parts.append(f"- {m['ticker']} ({m.get('name', '')}): {m['change_pct']:+.2f}% @ ${m['price']}")

    parts.append("\n## Sector ETFs (today's move)")
    for m in sectors:
        parts.append(f"- {m['ticker']} ({m.get('name', '')}): {m['change_pct']:+.2f}%")

    if big_movers:
        parts.append("\n## Other notable movers (≥3% absolute, may be candidates)")
        for m in big_movers:
            parts.append(f"- {m['ticker']}: {m['change_pct']:+.2f}% @ ${m['price']}")

    parts.append("\n## Watchlist news (last 3 days)")
    for n in watchlist_news:
        parts.append(f"- [{n.get('ticker')}] {n.get('headline')} ({n.get('source')})")

    if watchlist_earnings:
        parts.append("\n## Upcoming watchlist earnings (next 14 days)")
        for e in watchlist_earnings:
            parts.append(f"- {e['ticker']} on {e['date']} ({e.get('hour', '')})")

    if filings:
        parts.append("\n## Recent SEC 8-K/6-K filings (watchlist, last 7 days)")
        for f in filings[:10]:
            parts.append(f"- {f['ticker']}: {f['form']} on {f['date']}")

    parts.append("\n---\nPick 3-5 setups (or fewer if data is thin). Strict JSON output only.")
    return "\n".join(parts)


def should_generate_picks(picks_data: dict) -> bool:
    today = dt.date.today()
    week_start = today - dt.timedelta(days=today.weekday())
    for p in picks_data.get('picks', []):
        try:
            entered = dt.date.fromisoformat(p.get('entered_at', ''))
            if entered >= week_start:
                return False
        except (TypeError, ValueError):
            continue
    return True


THEME_SCAN_SYSTEM_PROMPT = """You are doing a theme scan for "The Brief"'s AI Experiment picks track. Read the week's market data and identify 3-5 underappreciated investing themes.

For each theme:
- name: 2-5 words describing it (e.g., "Small-cap rotation accelerating", "AI infrastructure cracking")
- summary: 1-2 sentences. What's driving this theme right now? Reference specific data points.
- developers: ticker symbols of "obvious" beneficiaries that may already have it priced in
- candidates: 2-3 ticker symbols of less-obvious second-derivative beneficiaries that might still be mispriced. MUST be from the data dump provided. If a name isn't in the data, you can't pick it.

Be selective. If only 2 genuine themes stand out, return 2. Never pad.

OUTPUT strict JSON only, no markdown fence, no commentary:
{
  "themes": [
    {
      "name": "...",
      "summary": "...",
      "developers": ["TICKER"],
      "candidates": ["TICKER", "TICKER"]
    }
  ]
}
"""


CRITIQUE_SYSTEM_PROMPT = """You are stress-testing pick candidates for "The Brief". You will receive a list of candidate tickers from the previous theme-scan step, plus the underlying data.

For EACH candidate, write the strongest possible bear case in 2-3 sentences. Use the fundamentals data — high P/E, weak margins, slowing growth, insider selling are all valid bear points. Reference specific numbers.

Then assess two things:
- falsifiable: TRUE if the bull thesis can be tested by specific, measurable, public criteria within 12 weeks. FALSE if the thesis requires multi-year structural shifts that can't be cleanly tested.
- conviction: integer 1-5. 1 = bear case overwhelms bull case. 5 = bull case is concrete and well-supported, bear case is real but secondary.

Be honest — most candidates should score 2-3. Reserve 4-5 for setups where the data genuinely supports the thesis.

OUTPUT strict JSON, no markdown fence:
{
  "critiques": [
    {
      "ticker": "TICKER",
      "bear_case": "...",
      "falsifiable": true,
      "conviction": 3
    }
  ]
}
"""


FINAL_SELECTION_SYSTEM_PROMPT = """Final pick selection for "The Brief"'s AI Experiment track. You will receive: themes from step 1, critiques from step 2 (with bear cases + conviction scores), and the full data dump.

Select the 3-5 highest-conviction picks. Apply these filters first:
- Drop any candidate with conviction <= 2.
- Drop any candidate where falsifiable = false.
- Drop any candidate already in the active picks list.
- Prefer diversity: vary sector, horizon type, and thesis style across picks.
- Be conservative on count. If only 2 candidates clear the bar, return 2. Never pad.

For each surviving pick, produce all fields (this is the actual pick record that gets logged):

- ticker: from candidates, uppercase
- sector: One of Technology, Healthcare, Energy, Financials, Industrials, Consumer, Materials, Utilities, Real Estate, Communication, Macro / ETF
- thesis: 1-2 sentence plain-text summary
- rationale: 2-4 paragraph HTML expansion with <p> tags, <strong> for emphasis, <span class="confidence confidence-fact">Fact</span> / Interp / Spec tags on every claim, <span class="ticker" data-ticker="SYM">SYM</span> wraps for every ticker. Include the strongest data point you saw. Reference the bear case from step 2 and explain why the bull thesis wins.
- horizon_weeks: integer 1-12. Match thesis type: event-driven 1-3, cyclical 4-7, structural 8-12.
- horizon_reason: 1-2 sentence HTML explanation of WHY this horizon
- target_pct: 8-20% typical. NEVER > 30%.
- stop_pct: negative, typically -8 to -15%.
- falsification: 1-2 sentences. Specific. Measurable. Plain text.

NEVER use: "buy", "must own", "rocket", "soaring", "explode", "skyrocket", "guaranteed".

OUTPUT strict JSON, no markdown fence:
{
  "picks": [
    {
      "ticker": "...",
      "sector": "...",
      "thesis": "...",
      "rationale": "...",
      "horizon_weeks": 4,
      "horizon_reason": "...",
      "target_pct": 15,
      "stop_pct": -10,
      "falsification": "..."
    }
  ]
}
"""


def _claude_json_call(system: str, user: str, max_tokens: int = 2500, label: str = '') -> dict | None:
    key = os.getenv('ANTHROPIC_API_KEY')
    if not key or not Anthropic:
        return None
    try:
        client = Anthropic(api_key=key)
        resp = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
    except Exception as e:
        print(f"  Claude {label} call failed: {e}")
        return None
    text = ''.join(b.text for b in resp.content if hasattr(b, 'text')).strip()
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  Claude {label} JSON parse failed: {e}")
        print(f"  Raw: {text[:300]}")
        return None


def generate_weekly_picks(movers: list[dict], news: list[dict], filings: list[dict],
                          earnings: list[dict], watchlist: dict, picks_data: dict,
                          fundamentals: dict | None = None,
                          macro: dict | None = None) -> list[dict]:
    key = os.getenv('ANTHROPIC_API_KEY')
    if not key or not Anthropic:
        print("  ANTHROPIC_API_KEY not set (or anthropic SDK missing), skipping picks generation")
        return []

    data_prompt = build_picks_user_prompt(movers, news, filings, earnings, watchlist, picks_data, fundamentals, macro)

    print("  Step 1/3: theme scan...")
    step1 = _claude_json_call(THEME_SCAN_SYSTEM_PROMPT, data_prompt, max_tokens=1500, label='theme-scan')
    if not step1 or not step1.get('themes'):
        print("  Theme scan returned nothing; aborting picks generation")
        return []
    themes = step1['themes']
    candidate_tickers = sorted({t.upper() for theme in themes for t in (theme.get('candidates') or []) if t})
    print(f"    {len(themes)} themes identified, {len(candidate_tickers)} candidates: {candidate_tickers}")
    if not candidate_tickers:
        return []

    print("  Step 2/3: bear-case critique...")
    critique_user = (
        data_prompt
        + "\n\n## Step 1 output — themes and candidates:\n"
        + json.dumps({'themes': themes}, indent=2)
        + "\n\nCritique EACH candidate listed above."
    )
    step2 = _claude_json_call(CRITIQUE_SYSTEM_PROMPT, critique_user, max_tokens=2000, label='critique')
    if not step2 or not step2.get('critiques'):
        print("  Critique step returned nothing; aborting")
        return []
    critiques = step2['critiques']
    surviving = [c for c in critiques if c.get('falsifiable') and (c.get('conviction') or 0) >= 3]
    print(f"    {len(critiques)} candidates critiqued, {len(surviving)} survive the bar (conviction>=3, falsifiable)")
    if not surviving:
        return []

    print("  Step 3/3: final selection + thesis writing...")
    final_user = (
        data_prompt
        + "\n\n## Themes from step 1:\n"
        + json.dumps({'themes': themes}, indent=2)
        + "\n\n## Critiques from step 2:\n"
        + json.dumps({'critiques': critiques}, indent=2)
        + "\n\nProduce the 3-5 highest-conviction picks from the surviving candidates."
    )
    step3 = _claude_json_call(FINAL_SELECTION_SYSTEM_PROMPT, final_user, max_tokens=3000, label='final-selection')
    if not step3 or not isinstance(step3.get('picks'), list):
        print("  Final selection returned nothing; aborting")
        return []
    new_picks = step3['picks']

    movers_by_ticker = {m['ticker']: m for m in movers}
    today_iso = dt.date.today().isoformat()
    active_tickers = {p['ticker'] for p in picks_data.get('picks', []) if p.get('status') == 'open'}

    validated = []
    for p in new_picks:
        ticker = (p.get('ticker') or '').upper().strip()
        if not ticker or ticker in active_tickers:
            continue
        m = movers_by_ticker.get(ticker)
        if not m:
            print(f"  Skipping pick {ticker}: no current price data")
            continue
        target = p.get('target_pct')
        stop = p.get('stop_pct')
        horizon = p.get('horizon_weeks')
        if target is None or stop is None or horizon is None:
            continue
        if abs(target) > 30:
            target = 30 if target > 0 else -30
        validated.append({
            'id': f"{today_iso}-{ticker}-auto",
            'ticker': ticker,
            'entered_at': today_iso,
            'entry_price': m.get('price'),
            'horizon_weeks': int(horizon),
            'target_pct': float(target),
            'stop_pct': float(stop),
            'sector': (p.get('sector') or 'Unclassified').strip(),
            'thesis': (p.get('thesis') or '').strip(),
            'rationale': (p.get('rationale') or '').strip(),
            'horizon_reason': (p.get('horizon_reason') or '').strip(),
            'falsification': (p.get('falsification') or '').strip(),
            'tags': ['ai-experiment', 'auto-generated'],
            'generated_by': f"claude-sonnet-4-5 · {today_iso}",
            'status': 'open',
        })
    return validated


ADVISED_PICKS_SYSTEM_PROMPT = """You are identifying stocks that are most plausibly affected by significant market-moving events for "The Brief"'s news-driven advisory.

For each event provided, identify 2-3 stocks worth looking at. For each stock, briefly explain WHY this event affects it. Keep explanations to one short sentence.

For each suggested stock you MUST also rate conviction 1-5:
- 5 = High conviction. Event has clear, direct, near-term causal impact on this specific stock. Magnitude is meaningful (>5% potential move). Effect plays out within weeks.
- 4 = Strong setup. Direct beneficiary or victim, but with some uncertainty about magnitude or timing.
- 3 = Plausible. Logical connection but indirect, or one of many similarly-affected names.
- 2 = Weak. Tangential connection; would only matter if broader regime shifts.
- 1 = Speculative. Very loose causal chain.

Be honest — most stocks should score 2-3. Reserve 4-5 for setups where the event is genuinely the dominant near-term factor.

CRITICAL RULES:
- Never say "buy" or "sell". Use "worth looking at", "could benefit", "could be pressured", "may be re-rated".
- Frame as research starting points, not recommendations.
- Don't pad. If only 1 stock is clearly affected, return 1. If the event has no clear stock connections, return an empty affected_stocks array.
- Prefer well-known liquid tickers when possible (S&P 500 names, major ETFs).
- For sector-wide events, suggesting a sector ETF (XLE, XLF, XLK, XLV, etc.) is fine.

OUTPUT JSON only, no markdown fence, no commentary:
{
  "events": [
    {
      "event_index": 0,
      "affected_stocks": [
        {
          "ticker": "NVDA",
          "direction": "positive",
          "conviction": 4,
          "why": "Single-sentence explanation."
        }
      ]
    }
  ]
}

direction must be exactly one of: "positive", "negative", "mixed".
conviction must be an integer 1-5.
"""


def enrich_events_with_advised_picks(events: list[dict]) -> list[dict]:
    key = os.getenv('ANTHROPIC_API_KEY')
    if not key or not Anthropic:
        return events

    indexed_statements = [(i, e) for i, e in enumerate(events) if e.get('type') == 'mover_statement']
    if not indexed_statements:
        return events

    indexed_statements = indexed_statements[:10]

    prompt_lines = ["Identify the stocks most plausibly affected by each event below. Use the event_index in your response.\n"]
    for idx, (_, e) in enumerate(indexed_statements):
        movers = ', '.join(e.get('movers') or []) or '(unspecified)'
        prompt_lines.append(
            f"Event {idx} (movers: {movers}): \"{(e.get('headline') or '')[:240]}\""
            f" — source: {e.get('source') or 'unknown'}"
        )
    user_prompt = "\n".join(prompt_lines)

    result = _claude_json_call(
        ADVISED_PICKS_SYSTEM_PROMPT,
        user_prompt,
        max_tokens=2500,
        label='advised-picks',
    )
    if not result or not isinstance(result.get('events'), list):
        return events

    for response_event in result['events']:
        idx = response_event.get('event_index')
        if not isinstance(idx, int) or idx >= len(indexed_statements):
            continue
        original_index, _ = indexed_statements[idx]
        stocks = response_event.get('affected_stocks') or []
        cleaned = []
        for s in stocks:
            ticker = (s.get('ticker') or '').strip().upper()
            direction = (s.get('direction') or '').strip().lower()
            why = (s.get('why') or '').strip()
            try:
                conviction = int(s.get('conviction', 0))
            except (TypeError, ValueError):
                conviction = 0
            if not ticker or direction not in ('positive', 'negative', 'mixed') or not why:
                continue
            cleaned.append({
                'ticker': ticker,
                'direction': direction,
                'why': why,
                'conviction': conviction,
            })
        if cleaned:
            events[original_index]['affected_stocks'] = cleaned[:3]

    return events


NEWS_HISTORY_FILE = DATA_DIR / 'news_history.jsonl'


def append_news_history(events: list[dict]) -> int:
    """Append today's news/mover events to the rolling news archive (deduped)."""
    if not events:
        return 0
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    existing_keys = set()
    if NEWS_HISTORY_FILE.exists():
        with NEWS_HISTORY_FILE.open('r') as f:
            for line in f:
                try:
                    rec = json.loads(line)
                    existing_keys.add((rec.get('headline', ''), rec.get('source', '')))
                except (ValueError, json.JSONDecodeError):
                    continue

    today_iso = dt.date.today().isoformat()
    kept_types = {'news', 'mover_statement'}
    added = 0
    with NEWS_HISTORY_FILE.open('a') as f:
        for e in events:
            if e.get('type') not in kept_types:
                continue
            headline = (e.get('headline') or '').strip()
            if not headline:
                continue
            key = (headline, e.get('source') or '')
            if key in existing_keys:
                continue
            existing_keys.add(key)
            # Prefer the event's own publish date; fall back to today
            pub = e.get('published_at') or e.get('detected_at') or ''
            try:
                rec_date = dt.datetime.fromisoformat(pub.replace('Z', '+00:00')).date().isoformat()
            except (ValueError, AttributeError, TypeError):
                rec_date = today_iso
            record = {
                'date': rec_date,
                'headline': headline[:300],
                'source': e.get('source') or '',
                'movers': e.get('movers') or [],
                'url': e.get('url') or '',
            }
            f.write(json.dumps(record) + '\n')
            added += 1
    return added


def load_news_history(days_back: int = 30) -> list[dict]:
    """Return news history records from the last `days_back` days, oldest first."""
    if not NEWS_HISTORY_FILE.exists():
        return []
    cutoff = dt.date.today() - dt.timedelta(days=days_back)
    out = []
    with NEWS_HISTORY_FILE.open('r') as f:
        for line in f:
            try:
                rec = json.loads(line)
                d = dt.date.fromisoformat(rec.get('date', '1970-01-01'))
                if d >= cutoff:
                    out.append(rec)
            except (ValueError, json.JSONDecodeError, KeyError):
                continue
    out.sort(key=lambda r: r.get('date', ''))
    return out


LONG_TERM_SYSTEM_PROMPT = """You are identifying long-term, structural investing themes for a personal investing brief.

Your job is to spot themes that have built up across MULTIPLE WEEKS of news — not single-headline trades, not earnings reactions, not geopolitical-spike plays. Long-term picks are HOLDS, not trades.

Quality bar:
1. Theme must be evidenced by news across ≥2 separate weeks of headlines.
2. Theme must reflect a STRUCTURAL/SECULAR shift (multi-quarter or multi-year), not a tactical catalyst.
3. Conviction must be 5/5. Fewer high-quality themes beat more mediocre ones — if nothing meets the bar, return zero.
4. Suggested stocks must be liquid (>$2B market cap), US-listed where possible, and NOT already in the user's active picks.

For each qualifying theme, suggest 1-2 stocks that best express it. The brief already covers tactical (event-driven, <3 weeks) and strategic (4-8 weeks) picks separately — long-term means 3-12+ months of holding.

Output strict JSON only, no markdown fence:
{
  "themes": [
    {
      "theme": "short name for the structural theme (e.g. 'AI power infrastructure', 'defense AI re-rating')",
      "evidence_summary": "specific cross-week pattern: which weeks, which news, why it's structural not tactical",
      "stocks": [
        {
          "ticker": "TICKER",
          "thesis": "one-paragraph rationale (~3-4 sentences) — why this stock specifically expresses the theme",
          "hold_for_months": 6,
          "what_kills_it": "specific falsification: what would invalidate the structural case (not just a price level)",
          "conviction": 5
        }
      ]
    }
  ]
}

If no theme has true cross-week consistency, return {"themes": []}. Do NOT invent themes to fill space."""


def synthesize_long_term_picks(picks_data: dict, movers: list[dict], min_history: int = 20) -> list[dict]:
    """Read recent news history, identify structural themes, promote up to 4 long-term picks."""
    key = os.getenv('ANTHROPIC_API_KEY')
    if not key or not Anthropic:
        print("  Skipping long-term synthesis: no ANTHROPIC_API_KEY")
        return []

    history = load_news_history(days_back=30)
    if len(history) < min_history:
        print(f"  Skipping long-term synthesis: {len(history)} headlines in history (need {min_history}+)")
        return []

    # Group by ISO week so the LLM can see cross-week persistence
    from collections import defaultdict
    by_week: dict[str, list[dict]] = defaultdict(list)
    for h in history:
        try:
            d = dt.date.fromisoformat(h['date'])
            iso_year, iso_week, _ = d.isocalendar()
            by_week[f"{iso_year}-W{iso_week:02d}"].append(h)
        except (ValueError, KeyError):
            continue

    if len(by_week) < 2:
        print(f"  Skipping long-term synthesis: news spans only {len(by_week)} week(s); need ≥2 weeks of history")
        return []

    weeks_block = []
    for week_key in sorted(by_week.keys()):
        items = by_week[week_key]
        weeks_block.append(f"## {week_key} — {len(items)} headlines")
        # cap per week to keep the prompt manageable
        for h in items[:40]:
            movers_str = ', '.join(h.get('movers') or []) if h.get('movers') else ''
            movers_suffix = f' (movers: {movers_str})' if movers_str else ''
            weeks_block.append(f"- [{h.get('source', '?')}] {(h.get('headline') or '')[:180]}{movers_suffix}")
        weeks_block.append('')

    active_tickers = sorted({p['ticker'] for p in picks_data.get('picks', []) if p.get('status') == 'open'})
    user_prompt = (
        f"Active picks (do NOT re-suggest these): {', '.join(active_tickers) or 'none'}\n\n"
        f"News history grouped by ISO week (last 30 days):\n\n"
        + '\n'.join(weeks_block)
        + "\n\nIdentify themes with cross-week consistency. For each, propose 1-2 long-term stock picks "
          "(5/5 conviction only). If nothing meets the bar, return an empty themes array."
    )

    print(f"  Synthesizing across {len(by_week)} weeks, {len(history)} headlines...")
    result = _claude_json_call(
        LONG_TERM_SYSTEM_PROMPT,
        user_prompt,
        max_tokens=3000,
        label='long-term-synthesis',
    )
    if not result or not isinstance(result.get('themes'), list):
        print("  Long-term synthesis returned no themes")
        return []

    movers_by_ticker = {m['ticker']: m for m in movers}
    today_iso = dt.date.today().isoformat()
    existing_open = {p['ticker'] for p in picks_data.get('picks', []) if p.get('status') == 'open'}

    new_picks: list[dict] = []
    for theme in result['themes']:
        if len(new_picks) >= 4:
            break
        theme_name = (theme.get('theme') or '').strip()
        evidence = (theme.get('evidence_summary') or '').strip()
        for s in theme.get('stocks', []) or []:
            if len(new_picks) >= 4:
                break
            ticker = (s.get('ticker') or '').strip().upper()
            if not ticker or ticker in existing_open:
                continue
            try:
                conviction = int(s.get('conviction', 0))
            except (ValueError, TypeError):
                conviction = 0
            if conviction < 5:
                continue
            entry_price = _lookup_price_for_ticker(ticker, movers_by_ticker)
            if entry_price is None:
                print(f"  Skipping long-term {ticker}: no price available")
                continue
            thesis = (s.get('thesis') or '').strip()
            kills = (s.get('what_kills_it') or '').strip()
            hold_months = s.get('hold_for_months') or 6
            try:
                hold_months = int(hold_months)
            except (ValueError, TypeError):
                hold_months = 6

            new_pick = {
                'id': f"{today_iso}-{ticker}-longterm",
                'ticker': ticker,
                'entered_at': today_iso,
                'entry_price': entry_price,
                'horizon_weeks': None,
                'target_pct': None,
                'stop_pct': None,
                'sector': 'Unclassified',
                'thesis': thesis,
                'rationale': (
                    f"<p><strong>Theme:</strong> {theme_name}</p>"
                    f"<p><span class=\"confidence confidence-interp\">Interp</span> {evidence}</p>"
                    f"<p><span class=\"confidence confidence-interp\">Interp</span> {thesis}</p>"
                    f"<p><strong>Conviction (Claude):</strong> {conviction}/5. "
                    f"Long-term structural HOLD (~{hold_months}+ months). "
                    f"No fixed target or stop; re-check thesis quarterly.</p>"
                ),
                'horizon_reason': (
                    f"Structural theme confirmed by ≥2 weeks of consistent news. "
                    f"Suggested hold ≥{hold_months} months. Long-term HOLDs have no fixed target or stop — "
                    f"they only close on thesis invalidation."
                ),
                'falsification': kills or 'Theme invalidated by reversal in underlying news pattern.',
                'tags': ['long-term', 'thematic', 'structural', 'auto-generated'],
                'generated_by': f"claude-sonnet-4-5 long-term · {today_iso}",
                'theme': theme_name,
                'status': 'open',
                'pick_type': 'long-term',
                'horizon_label': 'Long-term hold',
                'direction': 'long',
            }
            new_picks.append(new_pick)
            picks_data.setdefault('picks', []).append(new_pick)
            existing_open.add(ticker)

    if new_picks:
        save_picks(picks_data)
    return new_picks


def should_run_long_term_synthesis(picks_data: dict, force: bool = False) -> bool:
    """Trigger long-term synthesis monthly, or when ≥25 days since last long-term pick."""
    if force:
        return True
    today = dt.date.today()
    last_lt = None
    for p in picks_data.get('picks', []):
        if p.get('pick_type') != 'long-term':
            continue
        try:
            d = dt.date.fromisoformat(p.get('entered_at', ''))
        except (ValueError, TypeError):
            continue
        if last_lt is None or d > last_lt:
            last_lt = d
    # First-of-month window OR no long-term picks for 25+ days
    if today.day <= 3 and (last_lt is None or (today - last_lt).days >= 25):
        return True
    if last_lt is None:
        # First ever run — synthesize once we have history
        return True
    return (today - last_lt).days >= 28


def _lookup_price_for_ticker(ticker: str, movers_by_ticker: dict) -> float | None:
    if ticker in movers_by_ticker:
        return movers_by_ticker[ticker].get('price')
    try:
        info = yf.Ticker(ticker).fast_info
        price = info.last_price
        return round(float(price), 2) if price else None
    except Exception as e:
        print(f"  fast_info lookup failed for {ticker}: {e}")
        return None


def promote_advised_to_picks(events: list[dict], picks_data: dict, movers: list[dict],
                             max_new: int = 2) -> list[dict]:
    movers_by_ticker = {m['ticker']: m for m in movers}
    today_iso = dt.date.today().isoformat()
    today_date = dt.date.today()

    active_tickers = {p['ticker'] for p in picks_data.get('picks', []) if p.get('status') == 'open'}
    recent_tickers = set()
    cooldown_days = 7
    for p in picks_data.get('picks', []):
        try:
            entered = dt.date.fromisoformat(p.get('entered_at', ''))
            if (today_date - entered).days <= cooldown_days:
                recent_tickers.add(p['ticker'])
        except (TypeError, ValueError):
            continue

    candidates = []
    for event in events:
        if event.get('type') != 'mover_statement':
            continue
        for s in event.get('affected_stocks', []) or []:
            if s.get('direction') != 'positive':
                continue
            if (s.get('conviction') or 0) < 4:
                continue
            ticker = s['ticker']
            if ticker in active_tickers or ticker in recent_tickers:
                continue
            candidates.append({'stock': s, 'event': event})

    candidates.sort(key=lambda c: -(c['stock'].get('conviction', 0)))
    new_picks = []
    seen = set()
    for c in candidates:
        if len(new_picks) >= max_new:
            break
        ticker = c['stock']['ticker']
        if ticker in seen:
            continue
        seen.add(ticker)

        entry_price = _lookup_price_for_ticker(ticker, movers_by_ticker)
        if entry_price is None:
            print(f"  Skipping {ticker}: no price available")
            continue

        event = c['event']
        stock = c['stock']
        headline = (event.get('headline') or '')[:200]

        new_pick = {
            'id': f"{today_iso}-{ticker}-tactical",
            'ticker': ticker,
            'entered_at': today_iso,
            'entry_price': entry_price,
            'horizon_weeks': 3,
            'target_pct': 10,
            'stop_pct': -8,
            'sector': 'Unclassified',
            'thesis': f"{stock['why']} Triggered by: {headline}",
            'rationale': f"<p><span class=\"confidence confidence-fact\">Fact</span> News event: \"{headline}\" (source: {event.get('source','unknown')}).</p><p><span class=\"confidence confidence-interp\">Interp</span> {stock['why']}</p><p><strong>Conviction (Claude):</strong> {stock['conviction']}/5. Event-driven setup with short horizon — re-evaluate within 2-3 weeks of the catalyst.</p>",
            'horizon_reason': "Short-term event-driven setup. The catalyst is a specific news event whose market impact typically plays out within 2-4 weeks.",
            'falsification': f"Event impact reversed (e.g., contradicting news), OR stock fails to react within 5 trading days, OR moves opposite to the expected direction by stop_pct.",
            'tags': ['event-driven', 'ai-tactical', 'auto-generated'],
            'generated_by': f"claude-sonnet-4-5 event-driven · {today_iso}",
            'event_trigger': {
                'headline': headline,
                'source': event.get('source'),
                'url': event.get('url'),
                'movers': event.get('movers'),
            },
            'status': 'open',
        }
        new_picks.append(new_pick)
        picks_data.setdefault('picks', []).append(new_pick)

    if new_picks:
        save_picks(picks_data)

    return new_picks


def find_current_issue_number() -> int | None:
    issues_dir = ROOT / 'issues'
    if not issues_dir.exists():
        return None
    candidates = []
    for f in sorted(issues_dir.glob('issue-*.js')):
        try:
            content = f.read_text()
        except Exception:
            continue
        if 'draft: true' in content:
            continue
        m = re.search(r'number:\s*(\d+)', content)
        if m:
            candidates.append(int(m.group(1)))
    return max(candidates) if candidates else None


def write_daily(entry: dict | None, issue_number: int | None, out_path: Path) -> None:
    existing = {}
    if out_path.exists():
        try:
            content = out_path.read_text()
            data = json.loads(content.replace('window.theBriefDaily = ', '').rstrip(';\n'))
            existing = data.get('by_issue', {})
        except Exception:
            existing = {}

    if entry is not None and issue_number is not None:
        bucket = existing.setdefault(str(issue_number), [])
        bucket = [e for e in bucket if e.get('date') != entry['date']]
        bucket.append(entry)
        bucket.sort(key=lambda x: x.get('date', ''), reverse=True)
        existing[str(issue_number)] = bucket

    payload = {
        'generated_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'by_issue': existing,
    }
    out_path.write_text(to_js_var('theBriefDaily', payload))


def write_fundamentals(fundamentals: dict, out_path: Path) -> None:
    payload = {
        'generated_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'by_ticker': fundamentals,
    }
    out_path.write_text(to_js_var('theBriefFundamentals', payload))


def format_fundamentals_for_prompt(fundamentals: dict, tickers: list[str]) -> str:
    if not fundamentals:
        return "(fundamentals not available)"
    lines = []
    for t in tickers:
        f = fundamentals.get(t)
        if not f:
            continue
        parts = []
        if f.get('forward_pe') is not None:
            parts.append(f"fwd P/E {f['forward_pe']:.1f}")
        if f.get('price_to_sales') is not None:
            parts.append(f"P/S {f['price_to_sales']:.1f}")
        if f.get('operating_margin') is not None:
            parts.append(f"op margin {f['operating_margin']*100:.1f}%")
        if f.get('revenue_growth_yoy') is not None:
            parts.append(f"rev YoY {f['revenue_growth_yoy']*100:+.1f}%")
        if f.get('earnings_growth_qoq') is not None:
            parts.append(f"EPS QoQ {f['earnings_growth_qoq']*100:+.1f}%")
        if f.get('return_3m') is not None:
            parts.append(f"3m return {f['return_3m']:+.1f}%")
        if f.get('return_ytd') is not None:
            parts.append(f"YTD {f['return_ytd']:+.1f}%")
        if f.get('return_52w_high') is not None:
            parts.append(f"{f['return_52w_high']:+.1f}% from 52w high")
        pt = f.get('price_target')
        if pt and pt.get('mean'):
            parts.append(f"analyst PT mean ${pt['mean']:.2f}")
        recs = f.get('analyst_recs')
        if recs:
            buys = (recs.get('strongBuy', 0) or 0) + (recs.get('buy', 0) or 0)
            sells = (recs.get('sell', 0) or 0) + (recs.get('strongSell', 0) or 0)
            parts.append(f"{buys}B / {recs.get('hold', 0)}H / {sells}S analyst")
        ins = f.get('insider_recent_90d')
        if ins and (ins.get('buys') or ins.get('sells')):
            parts.append(f"insider 90d: {ins.get('buys')}B/{ins.get('sells')}S")
        if parts:
            lines.append(f"- {t}: " + ", ".join(parts))
    return "\n".join(lines) if lines else "(no fundamentals data)"


def write_picks(picks_data: dict, out_path: Path) -> None:
    picks = picks_data.get('picks', [])
    summary = {
        'total': len(picks),
        'open': sum(1 for p in picks if p.get('status') == 'open'),
        'hit': sum(1 for p in picks if p.get('status') == 'hit'),
        'miss': sum(1 for p in picks if p.get('status') == 'miss'),
        'expired': sum(1 for p in picks if p.get('status') == 'expired'),
    }
    closed = [p for p in picks if p.get('status') in ('hit', 'miss', 'expired')]
    if closed:
        summary['hit_rate'] = round(summary['hit'] / len(closed) * 100, 1)
        summary['avg_closed_pct'] = round(sum(p.get('closed_pct', 0) or 0 for p in closed) / len(closed), 2)
    else:
        summary['hit_rate'] = None
        summary['avg_closed_pct'] = None

    payload = {
        'generated_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'picks': picks,
        'summary': summary,
    }
    out_path.write_text(to_js_var('theBriefPicks', payload))


def build_radar_narrative(ticker: str, signals: list[str], tags: list[str], change: float) -> str:
    tag_set = set(tags)
    direction = "decline" if change < 0 else "rally"

    if 'earnings-soon' in tag_set and 'big-move' in tag_set:
        lead = f"<strong>{ticker}</strong> is moving sharply ({change:+.2f}%) just ahead of an earnings catalyst within 7 days."
    elif 'earnings-soon' in tag_set:
        lead = f"<strong>{ticker}</strong> reports earnings within the next 7 days — the print resolves the thesis."
    elif 'big-move' in tag_set and 'filing' in tag_set:
        lead = f"<strong>{ticker}</strong> made a statistically significant {direction} ({change:+.2f}%) on the same week as a new SEC filing — likely material event."
    elif 'big-move' in tag_set and 'heavy-news' in tag_set:
        lead = f"<strong>{ticker}</strong> moved sharply ({change:+.2f}%) on heavy news flow — the market is reacting to a developing story."
    elif 'big-move' in tag_set:
        lead = f"<strong>{ticker}</strong> made a statistically significant {direction} ({change:+.2f}%) but with no obvious news catalyst — sector pressure or technical move."
    elif 'insider-buying' in tag_set and 'drawdown' in tag_set:
        lead = f"<strong>{ticker}</strong> is showing a classic contrarian signal: insiders buying into a sustained drawdown."
    elif 'insider-buying' in tag_set:
        lead = f"<strong>{ticker}</strong> has notable insider conviction in the last 90 days."
    elif 'analyst-upgrade' in tag_set and 'cheap' in tag_set:
        lead = f"<strong>{ticker}</strong> trades cheap on forward earnings while sell-side estimates are revising higher."
    elif 'drawdown' in tag_set and 'cheap' in tag_set:
        lead = f"<strong>{ticker}</strong> has been beaten down hard and now trades at a low valuation — value setup."
    elif 'filing' in tag_set:
        lead = f"<strong>{ticker}</strong> just filed material disclosures with the SEC."
    else:
        lead = f"<strong>{ticker}</strong> is accumulating signals worth tracking."

    return lead


def compute_radar(movers: list[dict], news: list[dict], filings: list[dict],
                  earnings: list[dict], watchlist: dict,
                  fundamentals: dict | None = None) -> dict:
    movers_by_ticker = {m['ticker']: m for m in movers}
    fundamentals = fundamentals or {}

    news_counts: dict[str, int] = {}
    for n in news:
        t = n.get('ticker')
        if t:
            news_counts[t] = news_counts.get(t, 0) + 1

    filing_counts: dict[str, int] = {}
    for f in filings:
        filing_counts[f['ticker']] = filing_counts.get(f['ticker'], 0) + 1

    today = dt.date.today()
    earnings_soon: set[str] = set()
    followed = set(watchlist['followed'])
    for e in earnings:
        if e.get('ticker') in followed and e.get('date'):
            try:
                edate = dt.date.fromisoformat(e['date'])
                if 0 <= (edate - today).days <= 7:
                    earnings_soon.add(e['ticker'])
            except (TypeError, ValueError):
                pass

    radar = []
    for ticker in watchlist['followed']:
        m = movers_by_ticker.get(ticker)
        if not m:
            continue
        fund = fundamentals.get(ticker, {})
        news_n = news_counts.get(ticker, 0)
        filing_n = filing_counts.get(ticker, 0)
        soon = ticker in earnings_soon
        change = m.get('change_pct', 0) or 0
        abs_change = abs(change)
        vol_30d_pct = fund.get('realized_vol_30d_pct')

        score = 0.0
        signals: list[str] = []
        tags: list[str] = []

        if vol_30d_pct and vol_30d_pct > 0:
            z = abs_change / vol_30d_pct
            if z >= 2.5:
                score += 4
                signals.append(f"Moved {change:+.2f}% — a {z:.1f}σ move vs typical {vol_30d_pct:.1f}% daily vol")
                tags.append('big-move')
            elif z >= 1.5:
                score += 2.5
                signals.append(f"Moved {change:+.2f}% — a {z:.1f}σ move vs typical {vol_30d_pct:.1f}% daily vol")
                tags.append('moderate-move')
            elif z >= 1.0 and abs_change >= 1:
                score += 1
                signals.append(f"Moved {change:+.2f}% — a {z:.1f}σ move")
        else:
            if abs_change >= 5:
                score += 4
                signals.append(f"Moved {change:+.2f}% today")
                tags.append('big-move')
            elif abs_change >= 2:
                score += 2
                signals.append(f"Moved {change:+.2f}% today")
                tags.append('moderate-move')

        if news_n >= 5:
            score += 3
            signals.append(f"{news_n} news items in the last 3 days")
            tags.append('heavy-news')
        elif news_n >= 2:
            score += 1.5
            signals.append(f"{news_n} news items in the last 3 days")
            tags.append('news-flow')

        if filing_n >= 1:
            score += 2.5
            signals.append(f"{filing_n} SEC filing{'s' if filing_n > 1 else ''} in the last 7 days")
            tags.append('filing')

        if soon:
            score += 3
            signals.append("Earnings within 7 days")
            tags.append('earnings-soon')

        insider = fund.get('insider_recent_90d') or {}
        i_buys = insider.get('buys', 0) or 0
        i_sells = insider.get('sells', 0) or 0
        if i_buys >= 3 and i_buys > i_sells * 2:
            score += 2
            signals.append(f"{i_buys} insider buys vs {i_sells} sells (last 90 days)")
            tags.append('insider-buying')
        elif i_sells >= 5 and i_sells > i_buys * 2:
            score += 1
            signals.append(f"{i_sells} insider sells vs {i_buys} buys (last 90 days)")
            tags.append('insider-selling')

        recs_change = fund.get('analyst_recs_change') or {}
        buy_delta = recs_change.get('buy_delta', 0) or 0
        sell_delta = recs_change.get('sell_delta', 0) or 0
        if buy_delta >= 2:
            score += 1.5
            signals.append(f"+{buy_delta} analyst buy recs added recently")
            tags.append('analyst-upgrade')
        elif sell_delta >= 2:
            score += 1
            signals.append(f"+{sell_delta} analyst sell recs added recently")
            tags.append('analyst-downgrade')

        fwd_pe = fund.get('forward_pe')
        if fwd_pe is not None and 0 < fwd_pe < 15:
            score += 1
            signals.append(f"Forward P/E {fwd_pe:.1f} (cheap on absolute basis)")
            tags.append('cheap')

        ret_3m = fund.get('return_3m')
        ret_52w_high = fund.get('return_52w_high')
        if ret_3m is not None and ret_3m <= -25:
            score += 1
            signals.append(f"Down {ret_3m:+.1f}% over 3 months — deep drawdown")
            tags.append('drawdown')
        if ret_52w_high is not None and ret_52w_high <= -40:
            score += 1
            signals.append(f"{ret_52w_high:+.1f}% from 52-week high")
            tags.append('off-highs')

        if score >= 3:
            radar.append({
                'ticker': ticker,
                'name': m.get('name', ticker),
                'price': m.get('price'),
                'change_pct': m.get('change_pct'),
                'score': round(score, 1),
                'signals': signals,
                'reasons': signals,
                'tags': tags,
                'narrative': build_radar_narrative(ticker, signals, tags, change),
                'sector_etf': WATCHLIST_SECTOR_MAP.get(ticker),
            })

    radar.sort(key=lambda x: -x['score'])

    sectors_radar = []
    for s in sorted([m for m in movers if m.get('is_sector')],
                    key=lambda x: abs(x.get('change_pct', 0) or 0), reverse=True):
        members = [t for t, sec in WATCHLIST_SECTOR_MAP.items() if sec == s['ticker']]
        sectors_radar.append({
            'ticker': s['ticker'],
            'name': s.get('name', s['ticker']),
            'change_pct': s.get('change_pct'),
            'price': s.get('price'),
            'watchlist_members': members,
        })

    return {'watchlist_radar': radar, 'sectors_radar': sectors_radar}


SECTOR_BY_TICKER_GUESS = {
    'CRWV': 'XLK', 'NBIS': 'XLK', 'TTD': 'XLK', 'AMD': 'XLK', 'NVDA': 'XLK',
    'OSCR': 'XLV',
    'APA': 'XLE', 'TPL': 'XLE', 'OXY': 'XLE',
    'DG': 'XLP',
    'PWR': 'XLI', 'GEV': 'XLI',
}


def compute_move_reasoning(mover: dict, news: list[dict], filings: list[dict],
                           earnings: list[dict], sectors: list[dict], today: dt.date) -> str:
    ticker = mover['ticker']
    change = mover.get('change_pct') or 0
    abs_change = abs(change)

    today_iso = today.isoformat()
    yesterday = (today - dt.timedelta(days=1)).isoformat()
    two_days_ago = (today - dt.timedelta(days=2)).isoformat()
    recent_window = {today_iso, yesterday, two_days_ago}

    ticker_filings = [
        f for f in filings
        if f.get('ticker') == ticker and f.get('date') in recent_window
    ]
    if ticker_filings:
        return f"SEC filing ({ticker_filings[0].get('form', 'filing')}) just dropped — material disclosure likely behind move."

    today_earnings = [e for e in earnings if e.get('ticker') == ticker and e.get('date') == today_iso]
    if today_earnings:
        return "Earnings reaction — reported today."
    next_day_earnings = [e for e in earnings if e.get('ticker') == ticker and e.get('date') == (today + dt.timedelta(days=1)).isoformat()]
    if next_day_earnings:
        return "Pre-earnings positioning — reports tomorrow."

    ticker_news = []
    for n in news:
        if (n.get('ticker') or '').upper() != ticker.upper():
            continue
        ts = n.get('datetime')
        n_date = None
        try:
            if ts:
                n_date = dt.datetime.fromtimestamp(int(ts), tz=dt.timezone.utc).date().isoformat()
        except (TypeError, ValueError, OSError):
            n_date = None
        if n_date in recent_window:
            ticker_news.append(n)
    if ticker_news:
        headline = (ticker_news[0].get('headline') or '')[:90]
        suffix = '...' if len(ticker_news[0].get('headline') or '') > 90 else ''
        return f"News: \"{headline}{suffix}\""

    sector_etf = SECTOR_BY_TICKER_GUESS.get(ticker)
    if sector_etf:
        sector_move = next((s for s in sectors if s['ticker'] == sector_etf), None)
        if sector_move:
            sm_change = sector_move.get('change_pct') or 0
            if abs(sm_change) >= 0.5 and (sm_change > 0) == (change > 0) and abs(change / sm_change) <= 2.5 if sm_change else False:
                return f"Tracking {sector_etf} sector ({sm_change:+.2f}% today)"

    if abs_change >= 3:
        return "No clear catalyst — possibly flow or technical move."
    return ""


def write_movers(movers: list[dict], news: list[dict], filings: list[dict],
                 earnings: list[dict], watchlist: dict, out_path: Path,
                 fundamentals: dict | None = None) -> None:
    gainers = sorted([m for m in movers if m['change_pct'] >= 0], key=lambda x: -x['change_pct'])
    losers = sorted([m for m in movers if m['change_pct'] < 0], key=lambda x: x['change_pct'])
    indices = [m for m in movers if m.get('is_index')]
    sectors = [m for m in movers if m.get('is_sector')]
    watchlist_movers = [m for m in movers if m.get('is_watchlist')]

    today = dt.date.today()
    sectors_sorted = sorted(sectors, key=lambda x: -x['change_pct'])

    def _attach_reasoning(rows: list[dict]) -> list[dict]:
        out = []
        for r in rows:
            r2 = dict(r)
            try:
                r2['move_reason'] = compute_move_reasoning(r, news, filings, earnings, sectors_sorted, today)
            except Exception:
                r2['move_reason'] = ''
            out.append(r2)
        return out

    radar = compute_radar(movers, news, filings, earnings, watchlist, fundamentals)

    payload = {
        'generated_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'gainers': _attach_reasoning(gainers[:15]),
        'losers': _attach_reasoning(losers[:15]),
        'watchlist': _attach_reasoning(watchlist_movers),
        'indices': indices,
        'sectors': sectors_sorted,
        'watchlist_radar': radar['watchlist_radar'],
        'sectors_radar': radar['sectors_radar'],
    }
    out_path.write_text(to_js_var('theBriefMovers', payload))


NOISE_HEADLINE_PATTERNS = (
    'form 13', 'form 4 ', 'form 4:', 'form sc 13', 'form s-3', 'form 8-a',
    'gaap eps of', 'gaap eps:', 'declares cad', 'declares monthly',
    'declares quarterly dividend', 'declares regular',
    'royalties income', 'announces dividend', 'announces share repurchase',
    'reports preliminary', 'company announcement',
    'announces pricing of', 'announces upsized', 'announces commencement',
    'real-time', 'social security', 'student loan', 'best private',
    'menopause', 'estrogen', 'long-term care',
)

HIGH_IMPACT_KEYWORDS = (
    'guidance', 'guides', 'beats', 'misses', 'downgrade', 'upgrade',
    'fed', 'cpi', 'ppi', 'inflation', 'ceasefire', 'war',
    'opec', 'hormuz', 'iran', 'tariff', 'sanctions', 'export ban',
    'lawsuit', 'doj', 'antitrust', 'sec investigates', 'sec charges',
    'restated', 'recall', 'breach', 'hack',
    'pre-announce', 'profit warning', 'cuts forecast', 'lowers forecast',
    'raises forecast', 'raises guidance', 'cuts guidance',
    'china', 'beijing', 'xi summit', 'trump', 'biden', 'putin',
    'rate cut', 'rate hike', 'fomc', 'jackson hole',
    'merger', 'acquires', 'acquisition', 'takeover', 'spin-off',
)


def score_event_relevance(event: dict, active_pick_tickers: set[str],
                          watchlist_followed: set[str]) -> tuple[float, str, str | None]:
    """Return (numeric_score, tier_label, display_label) for a live-feed event.

    Tier: 'high' (score >= 6) | 'medium' (>= 3) | 'low' (< 3).
    Display label: the most specific reason this event scored ('Pick: NVDA',
    'SEC Filing', 'Earnings', etc.) — rendered as a badge on the card.
    """
    score = 0.0
    headline_lower = (event.get('headline') or '').lower()
    etype = event.get('type') or ''
    matched_pick: str | None = None

    # 1) Structured signals — filings + imminent earnings are material by definition
    structured_label: str | None = None
    if etype == 'filing':
        score += 4
        structured_label = 'SEC Filing'
    elif etype == 'earnings_upcoming':
        score += 3
        structured_label = 'Earnings'
    elif etype == 'mover_statement':
        score += 2
        structured_label = 'Market Mover'
    elif etype == 'mover':
        score += 2.5
        structured_label = 'Big Move'

    # 2) Watchlist relevance
    if event.get('is_watchlist'):
        score += 2

    # 3) LLM already judged this contains actionable stocks
    if event.get('affected_stocks'):
        score += 2

    # 4) Active-pick ticker mentioned anywhere in headline = highest signal
    if active_pick_tickers and headline_lower:
        for t in active_pick_tickers:
            tl = t.lower()
            if tl and (f' {tl} ' in f' {headline_lower} '
                       or headline_lower.startswith(tl + ' ')
                       or headline_lower.endswith(' ' + tl)
                       or headline_lower == tl):
                score += 5
                matched_pick = t
                break

    # 5) Source reputation
    source_lower = (event.get('source') or '').lower()
    if any(s in source_lower for s in ('reuters', 'bloomberg', 'wsj', 'wall street journal',
                                       'financial times', 'cnbc top')):
        score += 1

    # 6) Macro / market-moving keywords
    keyword_hits = sum(1 for k in HIGH_IMPACT_KEYWORDS if k in headline_lower)
    macro_label = None
    if keyword_hits >= 2:
        score += 3
        macro_label = 'Macro'
    elif keyword_hits == 1:
        score += 1.5

    # 7) Penalise routine boilerplate
    if any(p in headline_lower for p in NOISE_HEADLINE_PATTERNS):
        score -= 4

    # Bucket into tiers
    if score >= 6:
        tier = 'high'
    elif score >= 3:
        tier = 'medium'
    else:
        tier = 'low'

    # Choose the most specific display label, in priority order
    if matched_pick:
        display_label = f'Pick: {matched_pick}'
    elif structured_label:
        display_label = structured_label
    elif macro_label:
        display_label = macro_label
    elif event.get('affected_stocks'):
        display_label = 'Stocks to Watch'
    elif event.get('is_watchlist'):
        display_label = 'Watchlist'
    else:
        display_label = None

    return score, tier, display_label


def write_live_feed(movers: list[dict], earnings: list[dict], filings: list[dict],
                    news: list[dict], out_path: Path, skip_llm: bool = False,
                    active_pick_tickers: set[str] | None = None,
                    watchlist_followed: set[str] | None = None) -> None:
    events = []

    for m in movers:
        big = abs(m['change_pct']) >= 3.0
        if m.get('is_watchlist') and big:
            events.append({
                'type': 'mover',
                'ticker': m['ticker'],
                'name': m.get('name'),
                'change_pct': m['change_pct'],
                'price': m['price'],
                'is_watchlist': True,
                'timestamp': dt.datetime.now(dt.timezone.utc).isoformat(),
            })
        elif abs(m['change_pct']) >= 5.0 and not m.get('is_sector') and not m.get('is_index'):
            events.append({
                'type': 'mover',
                'ticker': m['ticker'],
                'name': m.get('name'),
                'change_pct': m['change_pct'],
                'price': m['price'],
                'is_watchlist': False,
                'timestamp': dt.datetime.now(dt.timezone.utc).isoformat(),
            })

    for e in earnings:
        if not e.get('is_watchlist'):
            continue
        events.append({
            'type': 'earnings_upcoming',
            'ticker': e['ticker'],
            'date': e['date'],
            'hour': e.get('hour'),
            'eps_estimate': e.get('eps_estimate'),
            'revenue_estimate': e.get('revenue_estimate'),
            'is_watchlist': True,
            'timestamp': e['date'],
        })

    for f in filings:
        events.append({
            'type': 'filing',
            'ticker': f['ticker'],
            'form': f['form'],
            'date': f['date'],
            'url': f['url'],
            'is_watchlist': True,
            'timestamp': f['date'],
        })

    for n in news:
        ts = ''
        try:
            if n.get('datetime'):
                ts = dt.datetime.fromtimestamp(int(n['datetime']), tz=dt.timezone.utc).isoformat()
        except (TypeError, ValueError, OSError):
            ts = ''
        statement = detect_mover_statement(n.get('headline', ''))
        if statement:
            events.append({
                'type': 'mover_statement',
                'movers': statement['movers'],
                'ticker': n.get('ticker'),
                'headline': n['headline'],
                'source': n.get('source'),
                'url': n.get('url'),
                'is_watchlist': True,
                'timestamp': ts,
            })
            continue
        events.append({
            'type': 'news',
            'ticker': n.get('ticker'),
            'headline': n['headline'],
            'source': n.get('source'),
            'url': n.get('url'),
            'is_watchlist': bool(n.get('is_watchlist')),
            'timestamp': ts,
        })

    events.sort(key=lambda x: (x.get('timestamp') or '', bool(x.get('is_watchlist'))), reverse=True)

    active_pick_tickers = active_pick_tickers or set()
    watchlist_followed = watchlist_followed or set()

    if not skip_llm:
        events = enrich_events_with_advised_picks(events)
    else:
        # In tick mode, preserve advised_stocks from the previous live.js so the
        # "stocks to look at" blocks don't vanish between full-pipeline runs.
        try:
            prev_text = out_path.read_text()
            prev_data = json.loads(prev_text.split('= ', 1)[1].rstrip().rstrip(';'))
            prev_enriched = {}
            for prev_e in prev_data.get('events', []) or []:
                if prev_e.get('type') == 'mover_statement' and prev_e.get('affected_stocks'):
                    key = (prev_e.get('headline') or '')[:200]
                    prev_enriched[key] = prev_e['affected_stocks']
            for e in events:
                if e.get('type') == 'mover_statement':
                    key = (e.get('headline') or '')[:200]
                    if key in prev_enriched:
                        e['affected_stocks'] = prev_enriched[key]
        except Exception:
            pass  # never let preservation failures break tick mode

    # Score every event for relevance — drives visual tiers + filtering on the page.
    for e in events:
        score, tier, label = score_event_relevance(e, active_pick_tickers, watchlist_followed)
        e['relevance_score'] = round(score, 1)
        e['relevance_tier'] = tier
        if label:
            e['relevance_label'] = label

    payload = {
        'generated_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'events': events,
    }
    out_path.write_text(to_js_var('theBriefLive', payload))
    return events


def check_no_conflict_markers() -> None:
    """Refuse to run if any tracked data file has unresolved git conflict markers.

    A syntax error in any data/*.js file (which is loaded as a <script src>) blanks
    the entire site. Catching this on the next pipeline run is the safety net for
    when local rebase/stash-pop leaves markers behind.
    """
    targets = list((ROOT / 'data').glob('*.js')) + [ROOT / 'picks.json', ROOT / 'watchlist.json']
    markers = ('<<<<<<< ', '=======\n', '>>>>>>> ')
    bad = []
    for path in targets:
        if not path.exists():
            continue
        try:
            text = path.read_text()
        except Exception:
            continue
        if any(m in text for m in markers):
            # '=======' is a common token, so re-check with line anchor
            lines = text.splitlines()
            if any(l.startswith(('<<<<<<< ', '>>>>>>> ')) or l == '=======' for l in lines):
                bad.append(str(path.relative_to(ROOT)))
    if bad:
        raise SystemExit(
            f"ABORT: unresolved merge conflict markers found in: {', '.join(bad)}. "
            "Resolve them locally before letting the pipeline run."
        )


def main() -> int:
    load_dotenv(ROOT / '.env', override=True)
    check_no_conflict_markers()
    watchlist = load_watchlist()

    # --tick mode: lightweight refresh for the Live Feed during market hours.
    # Skips every Claude call (no editorial, no weekly picks, no advised-picks LLM,
    # no long-term synthesis). Keeps yfinance, Finnhub, SEC, RSS — all free.
    # Picks still get re-graded (price/news-driven status updates), just no new ones.
    is_tick = '--tick' in sys.argv

    print(f"== The Brief — {'TICK (lightweight)' if is_tick else 'full pipeline'} ==")
    print(f"Started: {dt.datetime.now().isoformat(timespec='seconds')}")
    print(f"Watchlist: {len(watchlist['followed'])} followed, "
          f"{len(watchlist['indices'])} indices, {len(watchlist['sectors'])} sectors")

    existing_picks = load_picks()
    universe = set(watchlist['followed'] + watchlist['indices'] + watchlist['sectors'])
    pick_extras = sorted({
        p['ticker'] for p in existing_picks.get('picks', [])
        if p.get('status') == 'open' and p.get('ticker') not in universe
    })
    portfolio_extras = sorted(set(watchlist.get('portfolio_extras', [])) - universe)
    all_extras = sorted(set(pick_extras + portfolio_extras))
    if all_extras:
        print(f"Including {len(all_extras)} extra tickers: {all_extras}")

    print("\n[1/6] Fetching prices and movers...")
    movers = fetch_movers(watchlist, extra_tickers=all_extras)
    print(f"  Got {len(movers)} ticker snapshots")

    print("\n[2/6] Fetching upcoming earnings (next 14 days)...")
    earnings = fetch_earnings(watchlist)
    watchlist_earnings = sum(1 for e in earnings if e['is_watchlist'])
    print(f"  Got {len(earnings)} entries ({watchlist_earnings} on watchlist)")

    print("\n[3/6] Fetching recent SEC filings for watchlist (last 7 days)...")
    filings = fetch_filings(watchlist)
    print(f"  Got {len(filings)} 8-K/6-K filings")

    print("\n[4/6] Fetching watchlist company news (last 3 days)...")
    company_news = fetch_news(watchlist)
    print(f"  Got {len(company_news)} company news items")

    print("\n[5/6] Fetching general market news (Finnhub)...")
    general_news = fetch_general_news()
    print(f"  Got {len(general_news)} general news items")

    print(f"\n[6/6] Fetching news from {len(RSS_FEEDS)} RSS publishers...")
    rss_news = fetch_rss_news()
    print(f"  Got {len(rss_news)} RSS items")

    all_news = company_news + general_news + rss_news

    print("\nFetching macro snapshot (cached 1h)...")
    macro = fetch_macro_snapshot()
    yc = macro.get('_yield_curve')
    if yc:
        print(f"  Yield curve: {yc['spread_10y_13w_bps']:+d} bps · {'INVERTED' if yc['inverted'] else 'normal'}")
    print(f"  Got {len([k for k in macro if not k.startswith('_')])} macro indicators")

    print("\nFetching fundamentals for watchlist (cached 24h)...")
    fundamentals = fetch_fundamentals(watchlist)
    print(f"  Got fundamentals for {len(fundamentals)} tickers")

    print("\nUpdating tracked picks...")
    picks_data = load_picks()
    pre_status = {p.get('id'): p.get('status') for p in picks_data.get('picks', [])}
    picks_data = update_picks(picks_data, movers, all_news)
    closed_picks = [
        p for p in picks_data.get('picks', [])
        if pre_status.get(p.get('id')) == 'open' and p.get('status') != 'open'
    ]
    print(f"  {len(picks_data.get('picks', []))} existing picks tracked ({len(closed_picks)} just closed)")

    new_picks: list[dict] = []
    daily_entry = None
    current_issue = None

    if not is_tick:
        if should_generate_picks(picks_data):
            print("\nGenerating weekly picks via Claude...")
            new_picks = generate_weekly_picks(movers, all_news, filings, earnings, watchlist, picks_data, fundamentals, macro)
            if new_picks:
                picks_data['picks'].extend(new_picks)
                picks_data = update_picks(picks_data, movers, all_news)
                save_picks(picks_data)
                print(f"  Added {len(new_picks)} new picks: {[p['ticker'] for p in new_picks]}")
            else:
                print("  No new picks generated this week")
        else:
            print("\nWeekly picks already generated this week, skipping")

        print("\nGenerating editorial daily entry via Claude...")
        current_issue = find_current_issue_number()
        print(f"  Current issue: №{current_issue}")
        daily_entry = summarize_daily(movers, all_news, filings, earnings, watchlist, picks_data, macro)
        if daily_entry:
            print(f"  Daily headline: {daily_entry['headline']}")
    else:
        print("\nSkipping LLM steps (tick mode): weekly picks, daily editorial, advised-picks, long-term synthesis.")
        current_issue = find_current_issue_number()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    write_movers(movers, all_news, filings, earnings, watchlist, DATA_DIR / 'movers.js', fundamentals)
    active_pick_tickers_for_scoring = {
        p['ticker'] for p in picks_data.get('picks', []) if p.get('status') == 'open'
    }
    live_events = write_live_feed(
        movers, earnings, filings, all_news, DATA_DIR / 'live.js',
        skip_llm=is_tick,
        active_pick_tickers=active_pick_tickers_for_scoring,
        watchlist_followed=set(watchlist.get('followed') or []),
    )

    if not is_tick:
        print("\nChecking for event-driven tactical picks...")
        tactical_picks = promote_advised_to_picks(live_events or [], picks_data, movers, max_new=2)
        if tactical_picks:
            new_picks = new_picks + tactical_picks
            print(f"  Promoted {len(tactical_picks)} tactical picks: {[p['ticker'] for p in tactical_picks]}")
        else:
            print("  No high-conviction event-driven setups to promote")

    # ===== News history archive (cheap, always runs) =====
    appended = append_news_history(live_events or [])
    if appended:
        print(f"  Appended {appended} new headlines to data/news_history.jsonl")

    # ===== Long-term thematic synthesis (monthly cadence, full pipeline only) =====
    if not is_tick:
        force_long_term = '--force-long-term' in sys.argv
        if should_run_long_term_synthesis(picks_data, force=force_long_term):
            print("\nSynthesizing long-term structural picks from news history...")
            lt_picks = synthesize_long_term_picks(picks_data, movers)
            if lt_picks:
                new_picks = new_picks + lt_picks
                print(f"  Promoted {len(lt_picks)} long-term picks: {[p['ticker'] for p in lt_picks]}")
            else:
                print("  No long-term themes met the 5/5 conviction bar")
        else:
            days = None
            for p in picks_data.get('picks', []):
                if p.get('pick_type') != 'long-term':
                    continue
                try:
                    d = dt.date.fromisoformat(p.get('entered_at', ''))
                    delta = (dt.date.today() - d).days
                    days = delta if days is None else min(days, delta)
                except (ValueError, TypeError):
                    continue
            print(f"\nLong-term synthesis: skipped (last long-term pick was {days} days ago; cadence is monthly)")

    write_picks(picks_data, DATA_DIR / 'picks.js')
    # In tick mode, leave the daily editorial alone — only the full pipeline regenerates it.
    if not is_tick:
        write_daily(daily_entry, current_issue, DATA_DIR / 'daily.js')
    write_fundamentals(fundamentals, DATA_DIR / 'fundamentals.js')
    write_macro(macro, DATA_DIR / 'macro.js')

    print("\nDispatching notifications...")
    notif_state = load_notifications_state()
    dispatch_notifications(notif_state, movers, filings, earnings, picks_data, new_picks, closed_picks, all_news)
    save_notifications_state(notif_state)

    print(f"\nWrote {DATA_DIR.relative_to(ROOT) / 'movers.js'}")
    print(f"Wrote {DATA_DIR.relative_to(ROOT) / 'live.js'}")

    # Bust browser cache: the HTML loader fetches this and appends ?v=<version>
    # to every data script tag, so users never see stale picks/movers/news.
    version_payload = {
        'version': dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ'),
        'generated_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
    }
    (DATA_DIR / 'version.json').write_text(json.dumps(version_payload, indent=2))
    print(f"Wrote {DATA_DIR.relative_to(ROOT) / 'version.json'} (version={version_payload['version']})")

    print("Done. Open the-brief.html to view.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
