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
                                watchlist: dict, picks_data: dict) -> str:
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
                    earnings: list[dict], watchlist: dict, picks_data: dict) -> dict | None:
    key = os.getenv('ANTHROPIC_API_KEY')
    if not key or not Anthropic:
        print("  ANTHROPIC_API_KEY not set (or anthropic SDK missing), skipping daily summary")
        return None

    user_prompt = build_editorial_user_prompt(movers, news, filings, earnings, watchlist, picks_data)

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
- thesis: 2-4 sentences. Specific. Reference the data you saw, not vague claims. Confidence tags optional in thesis.
- horizon_weeks: integer 1-12. Match to thesis type:
  * Event-driven (earnings, FOMC, regulatory date): 1-3 weeks
  * Cyclical/macro: 4-8 weeks
  * Structural/valuation: 6-12 weeks
- target_pct: integer or float. Realistic. 8-20% is typical. NEVER > 30%.
- stop_pct: negative number. Typically -8 to -15%. Higher-vol names get wider stops.
- falsification: 1-2 sentences. SPECIFIC and MEASURABLE. Examples:
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

If today's data shows nothing genuinely interesting (slow news, no movers, no upcoming catalysts), return an empty picks list. Honest zero is better than padded picks.

OUTPUT (strict JSON only, no markdown fence, no commentary):
{
  "picks": [
    {
      "ticker": "TICKER",
      "thesis": "...",
      "horizon_weeks": 4,
      "target_pct": 15,
      "stop_pct": -10,
      "falsification": "..."
    }
  ]
}
"""


def build_picks_user_prompt(movers: list[dict], news: list[dict], filings: list[dict],
                            earnings: list[dict], watchlist: dict, picks_data: dict) -> str:
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


def generate_weekly_picks(movers: list[dict], news: list[dict], filings: list[dict],
                          earnings: list[dict], watchlist: dict, picks_data: dict) -> list[dict]:
    key = os.getenv('ANTHROPIC_API_KEY')
    if not key or not Anthropic:
        print("  ANTHROPIC_API_KEY not set (or anthropic SDK missing), skipping picks generation")
        return []

    user_prompt = build_picks_user_prompt(movers, news, filings, earnings, watchlist, picks_data)

    try:
        client = Anthropic(api_key=key)
        resp = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=2500,
            system=PICKS_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
    except Exception as e:
        print(f"  Claude picks call failed: {e}")
        return []

    text = ''.join(b.text for b in resp.content if hasattr(b, 'text')).strip()
    if text.startswith('```'):
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)

    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        print(f"  Picks JSON parse failed: {e}")
        print(f"  Raw: {text[:200]}")
        return []

    new_picks = data.get('picks', []) if isinstance(data, dict) else []
    if not isinstance(new_picks, list):
        return []

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
            'thesis': (p.get('thesis') or '').strip(),
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

    print("\nUpdating tracked picks...")
    picks_data = load_picks()
    picks_data = update_picks(picks_data, movers, all_news)
    print(f"  {len(picks_data.get('picks', []))} existing picks tracked")

    if should_generate_picks(picks_data):
        print("\nGenerating weekly picks via Claude...")
        new_picks = generate_weekly_picks(movers, all_news, filings, earnings, watchlist, picks_data)
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
    daily_entry = summarize_daily(movers, all_news, filings, earnings, watchlist, picks_data)
    if daily_entry:
        print(f"  Daily headline: {daily_entry['headline']}")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    write_movers(movers, all_news, filings, earnings, watchlist, DATA_DIR / 'movers.js')
    write_live_feed(movers, earnings, filings, all_news, DATA_DIR / 'live.js')
    write_picks(picks_data, DATA_DIR / 'picks.js')
    write_daily(daily_entry, current_issue, DATA_DIR / 'daily.js')

    print(f"\nWrote {DATA_DIR.relative_to(ROOT) / 'movers.js'}")
    print(f"Wrote {DATA_DIR.relative_to(ROOT) / 'live.js'}")
    print("Done. Open the-brief.html to view.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
