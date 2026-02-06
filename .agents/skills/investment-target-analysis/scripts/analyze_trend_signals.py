#!/usr/bin/env python3
"""Analyze trend and discipline signals from price/volume series."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from typing import Any


def _load_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _to_rows(payload: Any) -> list[dict[str, float]]:
    if isinstance(payload, dict):
        for key in ("prices", "price_data", "raw_data"):
            if isinstance(payload.get(key), list):
                payload = payload[key]
                break
    if not isinstance(payload, list):
        raise ValueError("Expected a list of price rows or a dict containing prices/price_data/raw_data")

    rows: list[dict[str, float]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        close = item.get("close")
        if close is None:
            continue
        row = {"close": float(close)}
        if item.get("volume") is not None:
            row["volume"] = float(item.get("volume"))
        rows.append(row)

    if len(rows) < 20:
        raise ValueError("Need at least 20 rows of close prices")
    return rows


def _sma(values: list[float], period: int) -> float:
    if len(values) < period:
        return mean(values)
    return mean(values[-period:])


def _ema_series(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    k = 2.0 / (period + 1)
    series = [values[0]]
    for value in values[1:]:
        series.append(value * k + series[-1] * (1 - k))
    return series


def _rsi(values: list[float], period: int = 14) -> float:
    if len(values) < 2:
        return 50.0
    deltas = [values[i] - values[i - 1] for i in range(1, len(values))]
    window = deltas[-period:] if len(deltas) >= period else deltas
    gains = [d for d in window if d > 0]
    losses = [-d for d in window if d < 0]
    avg_gain = mean(gains) if gains else 0.0
    avg_loss = mean(losses) if losses else 0.0
    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def analyze(rows: list[dict[str, float]]) -> dict[str, Any]:
    closes = [row["close"] for row in rows]
    volumes = [row.get("volume", 0.0) for row in rows]

    current_price = closes[-1]
    ma5 = _sma(closes, 5)
    ma10 = _sma(closes, 10)
    ma20 = _sma(closes, 20)

    ema12 = _ema_series(closes, 12)
    ema26 = _ema_series(closes, 26)
    macd_line = ema12[-1] - ema26[-1]
    signal_line = _ema_series([a - b for a, b in zip(ema12, ema26)], 9)[-1]

    rsi14 = _rsi(closes, 14)
    bias_ma5 = ((current_price - ma5) / ma5 * 100) if ma5 else 0.0

    volume_ratio = 1.0
    if len(volumes) >= 6 and any(v > 0 for v in volumes):
        baseline = mean(volumes[-6:-1])
        if baseline > 0:
            volume_ratio = volumes[-1] / baseline

    if ma5 > ma10 > ma20:
        trend_status = "bullish"
    elif ma5 < ma10 < ma20:
        trend_status = "bearish"
    else:
        trend_status = "neutral"

    score = 50
    score += 20 if trend_status == "bullish" else -20 if trend_status == "bearish" else 0
    score += 15 if bias_ma5 <= 2 else 5 if bias_ma5 <= 5 else -20
    score += 10 if macd_line >= signal_line else -10
    score += 10 if 40 <= rsi14 <= 65 else -10 if rsi14 >= 70 else 0
    score = max(0, min(100, score))

    if score >= 70:
        decision = "buy"
        confidence = "high"
    elif score <= 35:
        decision = "sell"
        confidence = "high" if score <= 20 else "medium"
    else:
        decision = "hold"
        confidence = "medium"

    # Hard discipline enforcement (not just score penalties).
    if bias_ma5 > 5 and decision == "buy":
        decision = "hold"
    if trend_status == "bearish" and decision == "buy":
        decision = "hold"

    if rsi14 >= 70:
        if confidence == "high":
            confidence = "medium"
        elif confidence == "medium":
            confidence = "low"

    checklist = [
        f"{'PASS' if trend_status == 'bullish' else 'FAIL' if trend_status == 'bearish' else 'WARN'}: MA alignment bullish (ma5 {ma5:.2f}, ma10 {ma10:.2f}, ma20 {ma20:.2f})",
        f"{'PASS' if bias_ma5 <= 5 else 'FAIL'}: Bias vs MA5 <= 5% (actual {bias_ma5:.2f}%)",
        f"{'PASS' if macd_line >= signal_line else 'WARN'}: MACD line >= signal line",
        f"{'PASS' if rsi14 < 70 else 'WARN'}: RSI below overbought zone (actual {rsi14:.2f})",
        f"{'PASS' if volume_ratio <= 1.5 else 'WARN'}: Avoid panic chasing (volume ratio {volume_ratio:.2f})",
    ]

    return {
        "trend_status": trend_status,
        "metrics": {
            "current_price": round(current_price, 4),
            "ma5": round(ma5, 4),
            "ma10": round(ma10, 4),
            "ma20": round(ma20, 4),
            "bias_ma5_pct": round(bias_ma5, 4),
            "macd_line": round(macd_line, 6),
            "macd_signal": round(signal_line, 6),
            "rsi14": round(rsi14, 4),
            "volume_ratio": round(volume_ratio, 4),
        },
        "recommendation": {
            "decision_type": decision,
            "confidence": confidence,
            "score": score,
            "invalidation": "Break of key support and failure of base-case assumptions",
        },
        "action_checklist": checklist,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze trend signals from price data")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--output", help="Optional output JSON path")
    args = parser.parse_args()

    payload = _load_json(args.input)
    result = analyze(_to_rows(payload))

    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2), encoding="utf-8")
    else:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
