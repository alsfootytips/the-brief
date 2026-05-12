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


def fetch_movers(watchlist: dict) -> list[dict]:
    tickers = sorted(set(watchlist['followed'] + watchlist['indices'] + watchlist['sectors']))
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


def notify_pushover(title: str, message: str, url_anchor: str | None = None) -> bool:
    user = os.getenv('PUSHOVER_USER_KEY')
    token = os.getenv('PUSHOVER_APP_TOKEN')
    if not user or not token:
        return False
    payload = {
        'token': token,
        'user': user,
        'title': title[:250],
        'message': message[:1024],
        'url': f"{BRIEF_URL}{url_anchor}" if url_anchor else BRIEF_URL,
        'url_title': 'Open in The Brief',
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
        title = f"BUY signal: {p['ticker']} ({horizon_lbl})"
        msg = (
            f"Entry ${p.get('entry_price')} · target {p['target_pct']:+g}% · "
            f"stop {p['stop_pct']:+g}% · {p['horizon_weeks']}w horizon.\n\n"
            f"{p.get('thesis', '')[:260]}"
        )
        if notify_pushover(title, msg, '#picks'):
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
        if notify_pushover(title, msg, '#picks'):
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
            if notify_pushover(title, msg, '#picks'):
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
        if notify_pushover(title, msg, '#live'):
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
        if notify_pushover(title, msg, '#live'):
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
        if notify_pushover(title, msg, '#weekly'):
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
                target = pick.get('target_pct', 15)
                stop = pick.get('stop_pct', -10)
                try:
                    entered = dt.date.fromisoformat(pick.get('entered_at', ''))
                except (TypeError, ValueError):
                    entered = today
                days_elapsed = (today - entered).days
                weeks_elapsed = days_elapsed / 7
                horizon = pick.get('horizon_weeks', 4)
                pick['days_elapsed'] = days_elapsed
                pick['days_remaining'] = max(0, int(horizon * 7 - days_elapsed))

                if current_pct >= target:
                    pick['status'] = 'hit'
                    pick['closed_at'] = today.isoformat()
                    pick['closed_price'] = round(current_price, 2)
                    pick['closed_pct'] = round(current_pct, 2)
                    pick['closed_reason'] = f'target_hit (+{target}%)'
                    changed = True
                elif current_pct <= stop:
                    pick['status'] = 'miss'
                    pick['closed_at'] = today.isoformat()
                    pick['closed_price'] = round(current_price, 2)
                    pick['closed_pct'] = round(current_pct, 2)
                    pick['closed_reason'] = f'stop_hit ({stop}%)'
                    changed = True
                elif weeks_elapsed >= horizon:
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


def compute_radar(movers: list[dict], news: list[dict], filings: list[dict],
                  earnings: list[dict], watchlist: dict) -> dict:
    movers_by_ticker = {m['ticker']: m for m in movers}

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
        news_n = news_counts.get(ticker, 0)
        filing_n = filing_counts.get(ticker, 0)
        soon = ticker in earnings_soon
        change = m.get('change_pct', 0) or 0
        abs_change = abs(change)

        score = 0.0
        reasons: list[str] = []

        if abs_change >= 5:
            score += 4
            reasons.append(f"Moved {change:+.2f}% today")
        elif abs_change >= 2:
            score += 2
            reasons.append(f"Moved {change:+.2f}% today")

        if news_n >= 5:
            score += 3
            reasons.append(f"{news_n} news items in the last 3 days")
        elif news_n >= 2:
            score += 1.5
            reasons.append(f"{news_n} news items in the last 3 days")

        if filing_n >= 1:
            score += 2.5
            reasons.append(f"{filing_n} SEC filing{'s' if filing_n > 1 else ''} in the last 7 days")

        if soon:
            score += 3
            reasons.append("Earnings within 7 days")

        if score >= 2:
            radar.append({
                'ticker': ticker,
                'name': m.get('name', ticker),
                'price': m.get('price'),
                'change_pct': m.get('change_pct'),
                'score': round(score, 1),
                'reasons': reasons,
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


def write_movers(movers: list[dict], news: list[dict], filings: list[dict],
                 earnings: list[dict], watchlist: dict, out_path: Path) -> None:
    gainers = sorted([m for m in movers if m['change_pct'] >= 0], key=lambda x: -x['change_pct'])
    losers = sorted([m for m in movers if m['change_pct'] < 0], key=lambda x: x['change_pct'])
    indices = [m for m in movers if m.get('is_index')]
    sectors = [m for m in movers if m.get('is_sector')]
    watchlist_movers = [m for m in movers if m.get('is_watchlist')]

    radar = compute_radar(movers, news, filings, earnings, watchlist)

    payload = {
        'generated_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'gainers': gainers[:15],
        'losers': losers[:15],
        'watchlist': watchlist_movers,
        'indices': indices,
        'sectors': sorted(sectors, key=lambda x: -x['change_pct']),
        'watchlist_radar': radar['watchlist_radar'],
        'sectors_radar': radar['sectors_radar'],
    }
    out_path.write_text(to_js_var('theBriefMovers', payload))


def write_live_feed(movers: list[dict], earnings: list[dict], filings: list[dict],
                    news: list[dict], out_path: Path) -> None:
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

    payload = {
        'generated_at': dt.datetime.now(dt.timezone.utc).isoformat(),
        'events': events,
    }
    out_path.write_text(to_js_var('theBriefLive', payload))


def main() -> int:
    load_dotenv(ROOT / '.env')
    watchlist = load_watchlist()

    print("== The Brief — ingestion pipeline ==")
    print(f"Started: {dt.datetime.now().isoformat(timespec='seconds')}")
    print(f"Watchlist: {len(watchlist['followed'])} followed, "
          f"{len(watchlist['indices'])} indices, {len(watchlist['sectors'])} sectors")

    print("\n[1/6] Fetching prices and movers...")
    movers = fetch_movers(watchlist)
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

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    write_movers(movers, all_news, filings, earnings, watchlist, DATA_DIR / 'movers.js')
    write_live_feed(movers, earnings, filings, all_news, DATA_DIR / 'live.js')
    write_picks(picks_data, DATA_DIR / 'picks.js')
    write_daily(daily_entry, current_issue, DATA_DIR / 'daily.js')
    write_fundamentals(fundamentals, DATA_DIR / 'fundamentals.js')
    write_macro(macro, DATA_DIR / 'macro.js')

    print("\nDispatching notifications...")
    notif_state = load_notifications_state()
    dispatch_notifications(notif_state, movers, filings, earnings, picks_data, new_picks, closed_picks, all_news)
    save_notifications_state(notif_state)

    print(f"\nWrote {DATA_DIR.relative_to(ROOT) / 'movers.js'}")
    print(f"Wrote {DATA_DIR.relative_to(ROOT) / 'live.js'}")
    print("Done. Open the-brief.html to view.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
