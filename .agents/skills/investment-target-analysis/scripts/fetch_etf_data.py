#!/usr/bin/env python3
"""Fetch ETF data and generate reusable JSON files for this skill.

Capabilities:
- Fetch price series (close/volume) for trend analysis.
- Fetch ETF profile (benchmark/issuer/top holdings/sector weights).
- Build ETF factor input (`etf_data`) for `calculate_ratios.py`.
- Generate `analysis_input.json` scaffold to reduce manual prep.

Data source:
- Yahoo Finance public endpoints (chart + quoteSummary).
- Local JSON payloads are also supported for offline/reproducible runs.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


CHART_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range={range}&interval=1d"
SUMMARY_URL = (
    "https://query2.finance.yahoo.com/v10/finance/quoteSummary/{symbol}"
    "?modules=price,summaryDetail,defaultKeyStatistics,fundProfile,topHoldings"
)
USER_AGENT = "Mozilla/5.0 (compatible; investment-target-analysis/1.0)"


@dataclass
class PriceRow:
    date: str
    close: float
    volume: float


def _normalize_symbol(raw_code: str) -> str:
    """Normalize ticker format (adapted from daily_stock_analysis style)."""
    code = raw_code.strip().upper()

    if re.fullmatch(r"^[A-Z]{1,5}(\.[A-Z])?$", code):
        return code

    if code.startswith("HK"):
        hk_code = code[2:].lstrip("0") or "0"
        return f"{hk_code.zfill(4)}.HK"

    if code.endswith((".SS", ".SZ", ".HK")):
        return code

    if code.isdigit() and len(code) == 6:
        if code.startswith(("600", "601", "603", "688", "51", "52", "56", "58")):
            return f"{code}.SS"
        if code.startswith(("000", "001", "002", "003", "15", "16", "18", "300")):
            return f"{code}.SZ"

    return code


def _default_benchmark(symbol: str) -> str:
    if symbol.endswith((".SS", ".SZ")):
        return "000300.SS"
    if symbol.endswith(".HK"):
        return "2800.HK"
    return "^GSPC"


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    if isinstance(value, dict):
        if "raw" in value:
            return _to_float(value.get("raw"))
        if "fmt" in value:
            return _to_float(value.get("fmt"))
    return None


def _to_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, dict):
        for key in ("longName", "shortName", "fmt", "raw"):
            if key in value and isinstance(value.get(key), str):
                return value.get(key, default)
    return str(value)


def _round(value: float | None, digits: int = 8) -> float | None:
    return round(float(value), digits) if value is not None else None


def _load_json(path: str | None) -> dict[str, Any] | None:
    if not path:
        return None
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON payload must be object: {path}")
    return payload


def _fetch_json(url: str, timeout: int) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Unexpected payload from {url}")
    return payload


def _extract_chart_rows(payload: dict[str, Any]) -> list[PriceRow]:
    chart = payload.get("chart", {})
    if chart.get("error"):
        raise ValueError(f"Chart API error: {chart['error']}")
    results = chart.get("result") or []
    if not isinstance(results, list) or not results:
        raise ValueError("No chart result returned")

    item = results[0]
    timestamps = item.get("timestamp") or []
    quote = ((item.get("indicators") or {}).get("quote") or [{}])[0]
    closes = quote.get("close") or []
    volumes = quote.get("volume") or []

    rows: list[PriceRow] = []
    for i, ts in enumerate(timestamps):
        if i >= len(closes) or closes[i] is None:
            continue
        close = float(closes[i])
        volume = float(volumes[i]) if i < len(volumes) and volumes[i] is not None else 0.0
        rows.append(
            PriceRow(
                date=datetime.fromtimestamp(int(ts), tz=timezone.utc).strftime("%Y-%m-%d"),
                close=close,
                volume=volume,
            )
        )

    if len(rows) < 20:
        raise ValueError("Need at least 20 rows of daily data")
    return rows


def _extract_summary_item(payload: dict[str, Any]) -> dict[str, Any]:
    qs = payload.get("quoteSummary", {})
    if qs.get("error"):
        raise ValueError(f"quoteSummary error: {qs['error']}")
    results = qs.get("result") or []
    if not isinstance(results, list) or not results:
        raise ValueError("No quoteSummary result returned")
    item = results[0]
    if not isinstance(item, dict):
        raise ValueError("Invalid quoteSummary result row")
    return item


def _daily_returns(rows: list[PriceRow]) -> list[float]:
    ret: list[float] = []
    for i in range(1, len(rows)):
        prev = rows[i - 1].close
        curr = rows[i].close
        if prev > 0:
            ret.append(curr / prev - 1.0)
    return ret


def _period_return(rows: list[PriceRow], lookback_days: int) -> float | None:
    if len(rows) <= lookback_days:
        return None
    start = rows[-lookback_days - 1].close
    end = rows[-1].close
    if start <= 0:
        return None
    return end / start - 1.0


def _annualized_return(rows: list[PriceRow], lookback_days: int) -> float | None:
    if len(rows) <= lookback_days:
        return None
    start = rows[-lookback_days - 1].close
    end = rows[-1].close
    if start <= 0 or end <= 0:
        return None
    years = lookback_days / 252.0
    if years <= 0:
        return None
    return (end / start) ** (1.0 / years) - 1.0


def _volatility_annualized(rows: list[PriceRow], lookback_days: int = 252) -> float | None:
    window = rows[-(lookback_days + 1):] if len(rows) > lookback_days else rows
    ret = _daily_returns(window)
    if len(ret) < 20:
        return None
    return statistics.pstdev(ret) * math.sqrt(252.0)


def _max_drawdown(rows: list[PriceRow], lookback_days: int = 252) -> float | None:
    window = rows[-lookback_days:] if len(rows) > lookback_days else rows
    if len(window) < 2:
        return None
    peak = window[0].close
    worst = 0.0
    for row in window:
        peak = max(peak, row.close)
        if peak > 0:
            worst = min(worst, row.close / peak - 1.0)
    return worst


def _cov(xs: list[float], ys: list[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    mx = statistics.mean(xs)
    my = statistics.mean(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / len(xs)


def _var(xs: list[float]) -> float:
    if len(xs) < 2:
        return 0.0
    m = statistics.mean(xs)
    return sum((x - m) ** 2 for x in xs) / len(xs)


def _beta_and_tracking_error(primary: list[PriceRow], benchmark: list[PriceRow]) -> tuple[float | None, float | None]:
    p_map = {r.date: r.close for r in primary}
    b_map = {r.date: r.close for r in benchmark}
    dates = sorted(set(p_map.keys()) & set(b_map.keys()))
    if len(dates) < 61:
        return None, None

    p_ret: list[float] = []
    b_ret: list[float] = []
    for i in range(1, len(dates)):
        d0 = dates[i - 1]
        d1 = dates[i]
        p0 = p_map[d0]
        p1 = p_map[d1]
        b0 = b_map[d0]
        b1 = b_map[d1]
        if p0 > 0 and b0 > 0:
            p_ret.append(p1 / p0 - 1.0)
            b_ret.append(b1 / b0 - 1.0)

    if len(p_ret) < 60:
        return None, None
    var_b = _var(b_ret)
    beta = _cov(p_ret, b_ret) / var_b if var_b > 0 else None
    active = [p - b for p, b in zip(p_ret, b_ret)]
    tracking_error = statistics.pstdev(active) * math.sqrt(252.0) if len(active) >= 20 else None
    return beta, tracking_error


def _parse_top_holdings(top_holdings: dict[str, Any], max_items: int) -> tuple[list[dict[str, Any]], dict[str, float]]:
    holdings: list[dict[str, Any]] = []
    for item in top_holdings.get("holdings") or []:
        if not isinstance(item, dict):
            continue
        symbol = _to_text(item.get("symbol"), "").strip()
        name = _to_text(item.get("holdingName"), symbol).strip()
        weight = _to_float(item.get("holdingPercent"))
        if symbol or name:
            holdings.append({"symbol": symbol or name, "name": name or symbol, "weight": weight})
    holdings = holdings[:max_items]

    sector_weights: dict[str, float] = {}
    for item in top_holdings.get("sectorWeightings") or []:
        if not isinstance(item, dict):
            continue
        for key, value in item.items():
            v = _to_float(value)
            if v is not None:
                sector_weights[str(key)] = v
    return holdings, sector_weights


def _sector_hhi(sector_weights: dict[str, float]) -> float | None:
    vals = [v for v in sector_weights.values() if isinstance(v, (int, float)) and v > 0]
    if not vals:
        return None
    total = sum(vals)
    if total <= 0:
        return None
    normalized = [v / total for v in vals]
    return sum(v * v for v in normalized)


def _build_summary(etf_data: dict[str, Any]) -> str:
    return (
        f"Expense ratio {etf_data.get('expense_ratio')}, "
        f"tracking error {etf_data.get('tracking_error')}, "
        f"AUM {etf_data.get('aum')}, "
        f"1Y return {etf_data.get('one_year_return')}, "
        f"Sharpe {etf_data.get('sharpe_1y')}, "
        f"top10 weight {etf_data.get('top10_holding_weight')}."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch ETF data and generate reusable skill inputs")
    parser.add_argument("--ticker", required=True, help="ETF code or ticker, e.g., SPY, 510300, hk02800")
    parser.add_argument("--company", default="", help="Optional display name override")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    parser.add_argument("--mode", choices=["standard", "detailed"], default="standard")
    parser.add_argument("--analysis-date", default=datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    parser.add_argument("--benchmark", help="Optional benchmark symbol override")
    parser.add_argument("--price-range", default="5y")
    parser.add_argument("--benchmark-range", default="2y")
    parser.add_argument("--risk-free-rate", type=float, default=0.02)
    parser.add_argument("--max-holdings", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=20)
    parser.add_argument("--chart-json", help="Local chart JSON payload")
    parser.add_argument("--summary-json", help="Local quoteSummary JSON payload")
    parser.add_argument("--benchmark-chart-json", help="Local benchmark chart JSON payload")
    parser.add_argument("--skip-analysis-input", action="store_true")
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    symbol = _normalize_symbol(args.ticker)
    benchmark = _normalize_symbol(args.benchmark) if args.benchmark else _default_benchmark(symbol)

    chart_payload = _load_json(args.chart_json)
    chart_url = f"file://{args.chart_json}" if chart_payload else CHART_URL.format(
        symbol=urllib.parse.quote(symbol), range=args.price_range
    )
    if chart_payload is None:
        chart_payload = _fetch_json(chart_url, timeout=args.timeout)

    summary_payload = _load_json(args.summary_json)
    summary_url = f"file://{args.summary_json}" if summary_payload else SUMMARY_URL.format(
        symbol=urllib.parse.quote(symbol)
    )
    if summary_payload is None:
        summary_payload = _fetch_json(summary_url, timeout=args.timeout)

    benchmark_payload = _load_json(args.benchmark_chart_json)
    benchmark_url = (
        f"file://{args.benchmark_chart_json}"
        if benchmark_payload
        else CHART_URL.format(symbol=urllib.parse.quote(benchmark), range=args.benchmark_range)
    )
    if benchmark_payload is None:
        benchmark_payload = _fetch_json(benchmark_url, timeout=args.timeout)

    rows = _extract_chart_rows(chart_payload)
    benchmark_rows = _extract_chart_rows(benchmark_payload)
    summary_item = _extract_summary_item(summary_payload)

    price = summary_item.get("price", {}) if isinstance(summary_item.get("price"), dict) else {}
    detail = summary_item.get("summaryDetail", {}) if isinstance(summary_item.get("summaryDetail"), dict) else {}
    stats = (
        summary_item.get("defaultKeyStatistics", {})
        if isinstance(summary_item.get("defaultKeyStatistics"), dict)
        else {}
    )
    fund_profile = summary_item.get("fundProfile", {}) if isinstance(summary_item.get("fundProfile"), dict) else {}
    top_holdings_module = summary_item.get("topHoldings", {}) if isinstance(summary_item.get("topHoldings"), dict) else {}

    current_price = _to_float(price.get("regularMarketPrice")) or rows[-1].close
    currency = _to_text(price.get("currency"), "USD")
    company = (
        args.company
        or _to_text(price.get("longName"))
        or _to_text(price.get("shortName"))
        or symbol
    )

    one_year_return = _period_return(rows, 252)
    three_year_return = _annualized_return(rows, 252 * 3)
    five_year_return = _annualized_return(rows, 252 * 5)
    volatility = _volatility_annualized(rows, 252)
    drawdown = _max_drawdown(rows, 252)
    beta_calc, tracking_error_calc = _beta_and_tracking_error(rows, benchmark_rows)
    sharpe = None
    if one_year_return is not None and volatility is not None and volatility > 0:
        sharpe = (one_year_return - args.risk_free_rate) / volatility

    bid = _to_float(detail.get("bid"))
    ask = _to_float(detail.get("ask"))
    spread_pct = None
    if bid is not None and ask is not None and (bid + ask) > 0:
        spread_pct = (ask - bid) / ((bid + ask) / 2.0) * 100.0

    holdings, sector_weights = _parse_top_holdings(top_holdings_module, args.max_holdings)
    top10_weight = sum(h["weight"] for h in holdings[:10] if isinstance(h.get("weight"), (int, float)))
    sector_hhi = _sector_hhi(sector_weights)

    expense_ratio = _to_float(detail.get("expenseRatio")) or _to_float(stats.get("annualReportExpenseRatio"))
    tracking_error = tracking_error_calc
    aum = _to_float(detail.get("totalAssets")) or _to_float(stats.get("totalAssets"))
    avg_daily_volume = _to_float(detail.get("averageVolume")) or statistics.mean(r.volume for r in rows[-20:])
    beta = _to_float(stats.get("beta")) or beta_calc
    turnover_ratio = _to_float(detail.get("annualHoldingsTurnover"))
    dividend_yield = _to_float(detail.get("yield"))

    etf_data = {
        "expense_ratio": _round(expense_ratio),
        "tracking_error": _round(tracking_error),
        "aum": _round(aum, 2),
        "avg_daily_volume": _round(avg_daily_volume, 2),
        "bid_ask_spread_pct": _round(spread_pct, 6),
        "one_year_return": _round(one_year_return),
        "three_year_return_annualized": _round(three_year_return),
        "five_year_return_annualized": _round(five_year_return),
        "volatility_1y": _round(volatility),
        "max_drawdown_1y": _round(drawdown),
        "sharpe_1y": _round(sharpe),
        "beta": _round(beta),
        "turnover_ratio": _round(turnover_ratio),
        "dividend_yield": _round(dividend_yield),
        "top10_holding_weight": _round(top10_weight if top10_weight > 0 else None),
        "sector_concentration_hhi": _round(sector_hhi),
    }

    etf_profile = {
        "benchmark_index": _to_text(fund_profile.get("benchmark"), benchmark),
        "issuer": _to_text(fund_profile.get("family"), ""),
        "asset_class": _to_text(fund_profile.get("legalType"), ""),
        "strategy": _to_text(fund_profile.get("categoryName"), ""),
        "holdings_count": len(holdings) if holdings else None,
        "top_holdings": holdings,
        "sector_weights": sector_weights,
    }

    prices_payload = [{"date": r.date, "close": r.close, "volume": r.volume} for r in rows]
    financial_payload = {"asset_type": "etf", "ticker": symbol, "company": company, "etf_data": etf_data}
    analysis_input = {
        "ticker": symbol,
        "company": company,
        "asset_type": "etf",
        "mode": args.mode,
        "analysis_date": args.analysis_date,
        "market": {
            "current_price": _round(current_price, 6),
            "currency": currency,
            "price_date": rows[-1].date,
        },
        "thesis": "",
        "fundamental_summary": _build_summary(etf_data),
        "etf_profile": etf_profile,
        "valuation": {
            "bull": {"target": round((current_price or 0.0) * 1.12, 6), "probability": 0.25},
            "base": {"target": round((current_price or 0.0) * 1.05, 6), "probability": 0.5},
            "bear": {"target": round((current_price or 0.0) * 0.88, 6), "probability": 0.25},
        },
        "catalysts": {"near_term": [], "mid_term": []},
        "risks": [],
        "position_sizing": "Core allocation vehicle; size by portfolio risk budget.",
        "assumptions": {
            "verified_sources": [f"chart:{chart_url}", f"summary:{summary_url}", f"benchmark_chart:{benchmark_url}"],
            "unverified_assumptions": [],
        },
        "disclaimer": "Educational/research only. Not financial advice.",
    }

    (out_dir / "prices.json").write_text(
        json.dumps(prices_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "etf_financial_data.json").write_text(
        json.dumps(financial_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (out_dir / "etf_profile.json").write_text(
        json.dumps(etf_profile, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if not args.skip_analysis_input:
        (out_dir / "analysis_input.json").write_text(
            json.dumps(analysis_input, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    generated = ["prices.json", "etf_financial_data.json", "etf_profile.json"]
    if not args.skip_analysis_input:
        generated.append("analysis_input.json")

    print(
        json.dumps(
            {
                "ticker": symbol,
                "company": company,
                "benchmark": benchmark,
                "output_dir": str(out_dir),
                "generated_files": generated,
            },
            indent=2,
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
