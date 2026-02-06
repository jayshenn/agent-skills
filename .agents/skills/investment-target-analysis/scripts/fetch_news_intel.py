#!/usr/bin/env python3
"""Fetch multi-dimensional equity intelligence with Tavily."""

from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


TAVILY_URL = "https://api.tavily.com/search"


def _build_queries(ticker: str, company: str, mode: str) -> dict[str, str]:
    display = company or ticker
    queries = {
        "latest_news": f"{display} {ticker} latest news material events",
        "risk_check": f"{display} {ticker} litigation regulation downgrade warning",
        "earnings": f"{display} {ticker} earnings guidance revenue margin",
    }
    if mode == "detailed":
        queries.update(
            {
                "market_analysis": f"{display} {ticker} analyst rating target price",
                "industry": f"{display} industry competitors market share outlook",
                "options_flow": f"{display} {ticker} options unusual activity implied volatility",
                "insider_activity": f"{display} {ticker} insider buying selling filing",
                "esg_notes": f"{display} {ticker} ESG sustainability governance controversy",
            }
        )
    return queries


def _tavily_search(api_key: str, query: str, max_results: int) -> dict[str, Any]:
    body = {
        "api_key": api_key,
        "query": query,
        "max_results": max_results,
        "search_depth": "advanced",
        "include_answer": False,
        "include_raw_content": False,
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        TAVILY_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return {"success": False, "error": f"http_{exc.code}"}
    except Exception as exc:  # pylint: disable=broad-except
        return {"success": False, "error": str(exc)}

    items = []
    for row in payload.get("results", []):
        items.append(
            {
                "title": row.get("title", ""),
                "url": row.get("url", ""),
                "snippet": row.get("content", ""),
                "published_date": row.get("published_date"),
                "source": row.get("url", ""),
            }
        )

    return {"success": True, "results": items}


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch equity intelligence from Tavily")
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--company", default="")
    parser.add_argument("--mode", choices=["standard", "detailed"], default="standard")
    parser.add_argument("--max-results", type=int, default=3)
    parser.add_argument("--output")
    args = parser.parse_args()

    api_key = os.getenv("TAVILY_API_KEY", "")
    queries = _build_queries(args.ticker, args.company, args.mode)

    output: dict[str, Any] = {
        "provider": "tavily",
        "mode": args.mode,
        "key_configured": bool(api_key),
        "dimensions": {},
    }

    if not api_key:
        for name, query in queries.items():
            output["dimensions"][name] = {
                "query": query,
                "success": False,
                "error": "missing_tavily_api_key",
                "results": [],
            }
    else:
        for name, query in queries.items():
            result = _tavily_search(api_key, query, args.max_results)
            output["dimensions"][name] = {"query": query, **result}
            time.sleep(0.4)

    text = json.dumps(output, indent=2)
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
