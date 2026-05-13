#!/usr/bin/env python3
"""
The Brief — portfolio screenshot importer.

Takes a screenshot of a brokerage portfolio (Trading 212, Robinhood, etrade,
Schwab, etc.) and uses Claude vision to extract holdings as a JSON blob
ready to paste into the Portfolio tab's "Import" textarea.

Usage:
  ./venv/bin/python import_portfolio.py path/to/screenshot.png
  ./venv/bin/python import_portfolio.py screenshot.png --copy   # copy to clipboard (macOS)

The extracted JSON is printed to stdout and optionally copied to the clipboard.
Paste it into the Portfolio tab → "Import portfolio JSON" textarea → Save.

No data is committed anywhere. Your screenshot and holdings never leave
your machine except for the vision call to Anthropic.
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv

try:
    from anthropic import Anthropic
except ImportError:
    print("anthropic SDK not installed. Run: pip install anthropic", file=sys.stderr)
    sys.exit(1)


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env', override=True)


SYSTEM_PROMPT = """You are extracting brokerage portfolio holdings from a screenshot.

Return JSON with this exact shape, no markdown fence, no commentary:
{
  "holdings": [
    {
      "ticker": "TICKER",
      "shares": 0.0,
      "entry_price": 0.0,
      "entry_date": "YYYY-MM-DD",
      "currency": "USD or GBP or EUR",
      "notes": "optional context (e.g., 'Vanguard FTSE All-World ETF, LSE listed')"
    }
  ]
}

RULES:
- ticker: uppercase, no spaces. If the broker shows a long name (e.g., "Vanguard FTSE All-World (Acc)"), use the actual ticker symbol shown (e.g., "VWRP"). If LSE-listed (UK ETFs), append ".L" so yfinance can fetch it (VWRP → VWRP.L, VUAG → VUAG.L).
- shares: exact share count visible (preserve full precision, e.g., 39.62298195).
- entry_price: COST BASIS PER SHARE in the same currency the broker displays. To compute: cost_basis = current_value − gain_or_loss; entry_price = cost_basis / shares. Round to 4 decimal places.
- entry_date: if visible use it; otherwise omit or use today.
- currency: the currency the broker displays values in (usually GBP for UK brokers, USD for US brokers).

If something is unclear (no shares shown, no cost basis derivable, etc.), still return the ticker but leave numeric fields null and add a note explaining what's missing. Don't skip holdings just because some data is missing.

Output strict JSON only.
"""


def encode_image(path: Path) -> tuple[str, str]:
    mime, _ = mimetypes.guess_type(str(path))
    if mime not in ('image/png', 'image/jpeg', 'image/gif', 'image/webp'):
        raise ValueError(f"Unsupported image type: {mime}. Use PNG, JPEG, GIF, or WebP.")
    data = path.read_bytes()
    return mime, base64.standard_b64encode(data).decode('ascii')


def extract_holdings(image_path: Path) -> dict:
    if not os.getenv('ANTHROPIC_API_KEY'):
        print("ANTHROPIC_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)

    mime, b64 = encode_image(image_path)

    client = Anthropic()
    resp = client.messages.create(
        model='claude-sonnet-4-5',
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                'role': 'user',
                'content': [
                    {'type': 'image', 'source': {'type': 'base64', 'media_type': mime, 'data': b64}},
                    {'type': 'text', 'text': 'Extract the portfolio holdings from this screenshot.'},
                ],
            }
        ],
    )
    text = ''.join(b.text for b in resp.content if hasattr(b, 'text')).strip()
    if text.startswith('```'):
        text = text.split('\n', 1)[1] if '\n' in text else text[3:]
        if text.endswith('```'):
            text = text[: -3]
        text = text.strip()
    return json.loads(text)


def normalise(holdings: list[dict]) -> list[dict]:
    out = []
    for h in holdings:
        ticker = (h.get('ticker') or '').strip().upper()
        if not ticker:
            continue
        shares = h.get('shares')
        entry_price = h.get('entry_price')
        entry_date = (h.get('entry_date') or '').strip()
        out.append({
            'ticker': ticker,
            'shares': float(shares) if shares else None,
            'entry_price': float(entry_price) if entry_price else None,
            'entry_date': entry_date or None,
            'currency': (h.get('currency') or '').strip().upper() or None,
            'notes': (h.get('notes') or '').strip() or None,
        })
    return out


def copy_to_clipboard(text: str) -> bool:
    try:
        proc = subprocess.run(['pbcopy'], input=text.encode(), check=True)
        return proc.returncode == 0
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description='Import portfolio from broker screenshot.')
    parser.add_argument('image', help='Path to portfolio screenshot (PNG/JPEG)')
    parser.add_argument('--copy', action='store_true', help='Copy resulting JSON to clipboard (macOS)')
    args = parser.parse_args()

    image_path = Path(args.image).expanduser().resolve()
    if not image_path.exists():
        print(f"File not found: {image_path}", file=sys.stderr)
        return 1

    print(f"Extracting holdings from {image_path.name}...", file=sys.stderr)
    raw = extract_holdings(image_path)
    holdings = normalise(raw.get('holdings', []))

    payload = {'holdings': holdings}
    out_text = json.dumps(payload, indent=2)

    print()
    print(out_text)
    print()
    print(f"Found {len(holdings)} holdings: {[h['ticker'] for h in holdings]}", file=sys.stderr)

    if args.copy:
        if copy_to_clipboard(out_text):
            print("Copied to clipboard. Paste into the Portfolio tab → Import.", file=sys.stderr)
        else:
            print("Could not copy to clipboard. Copy the JSON above manually.", file=sys.stderr)
    else:
        print("Tip: re-run with --copy to put the JSON straight on your clipboard.", file=sys.stderr)

    return 0


if __name__ == '__main__':
    sys.exit(main())
