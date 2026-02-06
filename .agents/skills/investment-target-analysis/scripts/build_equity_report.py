#!/usr/bin/env python3
"""Build structured JSON and markdown equity reports for MVP skill."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _weighted_target(valuation: dict[str, Any], current_price: float) -> tuple[float, dict[str, Any]]:
    defaults = {
        "bull": {"target": current_price * 1.2, "probability": 0.25},
        "base": {"target": current_price * 1.05, "probability": 0.50},
        "bear": {"target": current_price * 0.85, "probability": 0.25},
    }

    scenarios: dict[str, dict[str, float]] = {}
    for key in ("bull", "base", "bear"):
        user_value = valuation.get(key, {}) if isinstance(valuation, dict) else {}
        target = float(user_value.get("target", defaults[key]["target"]))
        probability = float(user_value.get("probability", defaults[key]["probability"]))
        scenarios[key] = {"target": target, "probability": probability}

    total_prob = sum(v["probability"] for v in scenarios.values())
    if total_prob <= 0:
        total_prob = 1.0
    for item in scenarios.values():
        item["probability"] = item["probability"] / total_prob

    weighted = sum(v["target"] * v["probability"] for v in scenarios.values())
    return weighted, scenarios


def _valuation_decision(upside_pct: float) -> str:
    if upside_pct >= 15:
        return "buy"
    if upside_pct <= -10:
        return "sell"
    return "hold"


def _merge_decisions(valuation_decision: str, trend_decision: str) -> str:
    trend = str(trend_decision).lower()
    valuation = str(valuation_decision).lower()

    if trend == "sell" or valuation == "sell":
        return "sell"
    if trend == "buy" and valuation == "buy":
        return "buy"
    return "hold"


def _decision_to_rating(decision: str) -> str:
    return {"buy": "BUY", "hold": "HOLD", "sell": "SELL"}.get(str(decision).lower(), "HOLD")


def _normalize_confidence(value: str) -> str:
    normalized = str(value).lower()
    if normalized in {"high", "medium", "low"}:
        return normalized
    return "medium"


def _downgrade_confidence(level: str, steps: int) -> str:
    normalized = _normalize_confidence(level)
    levels = ["low", "medium", "high"]
    idx = levels.index(normalized)
    return levels[max(0, idx - max(0, steps))]


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _collect_data_quality(data: dict[str, Any], mode: str, trend: dict[str, Any]) -> tuple[dict[str, Any], int]:
    assumptions = data.get("assumptions", {}) if isinstance(data.get("assumptions"), dict) else {}
    verified_sources = assumptions.get("verified_sources", [])
    unverified_assumptions = assumptions.get("unverified_assumptions", [])

    ratio_results = data.get("ratio_results", {}) if isinstance(data.get("ratio_results"), dict) else {}
    ratio_quality = ratio_results.get("data_quality", {}) if isinstance(ratio_results.get("data_quality"), dict) else {}
    missing_fields = ratio_quality.get("missing_fields", [])
    invalid_fields = ratio_quality.get("invalid_fields", [])

    technical_metrics = trend.get("metrics", {}) if isinstance(trend.get("metrics"), dict) else {}
    rsi14 = _to_float(technical_metrics.get("rsi14"), 0.0)
    bias_ma5_pct = _to_float(technical_metrics.get("bias_ma5_pct"), 0.0)

    confidence_impact: list[str] = []
    downgrade_steps = 0

    if unverified_assumptions:
        downgrade_steps += 1
        confidence_impact.append("unverified_assumptions_present")

    if missing_fields or invalid_fields:
        downgrade_steps += 1
        confidence_impact.append("ratio_input_quality_incomplete")

    intel = data.get("intel", {}) if isinstance(data.get("intel"), dict) else {}
    if mode == "detailed" and not intel.get("key_configured", False):
        downgrade_steps += 1
        confidence_impact.append("detailed_mode_without_external_intel")

    if rsi14 >= 70:
        downgrade_steps += 1
        confidence_impact.append("rsi_overbought_confidence_downgrade")

    if bias_ma5_pct > 5:
        downgrade_steps += 1
        confidence_impact.append("ma5_bias_above_5pct")

    return (
        {
            "verified_sources": verified_sources if isinstance(verified_sources, list) else [],
            "unverified_assumptions": (
                unverified_assumptions if isinstance(unverified_assumptions, list) else []
            ),
            "ratio_input_quality": ratio_quality if isinstance(ratio_quality, dict) else {},
            "confidence_impact": confidence_impact,
        },
        downgrade_steps,
    )


def _normalize_asset_type(value: Any) -> str:
    asset_type = str(value or "equity").lower()
    return "etf" if asset_type == "etf" else "equity"


def _build_etf_analysis(data: dict[str, Any], ratio_results: dict[str, Any]) -> dict[str, Any]:
    etf_profile = data.get("etf_profile", {}) if isinstance(data.get("etf_profile"), dict) else {}
    ratio_block = ratio_results if isinstance(ratio_results, dict) else {}
    cost_efficiency = ratio_block.get("cost_efficiency", {}) if isinstance(ratio_block.get("cost_efficiency"), dict) else {}
    liquidity = ratio_block.get("liquidity", {}) if isinstance(ratio_block.get("liquidity"), dict) else {}
    risk_return = ratio_block.get("risk_return", {}) if isinstance(ratio_block.get("risk_return"), dict) else {}
    concentration = ratio_block.get("concentration", {}) if isinstance(ratio_block.get("concentration"), dict) else {}

    return {
        "benchmark_index": etf_profile.get("benchmark_index", etf_profile.get("index_name", "")),
        "issuer": etf_profile.get("issuer", ""),
        "asset_class": etf_profile.get("asset_class", ""),
        "strategy": etf_profile.get("strategy", ""),
        "holdings_count": etf_profile.get("holdings_count"),
        "top_holdings": etf_profile.get("top_holdings", []),
        "sector_weights": etf_profile.get("sector_weights", {}),
        "cost_snapshot": {
            "expense_ratio": cost_efficiency.get("expense_ratio"),
            "tracking_error": cost_efficiency.get("tracking_error"),
        },
        "liquidity_snapshot": {
            "aum_usd_bn": liquidity.get("aum_usd_bn"),
            "avg_daily_volume": liquidity.get("avg_daily_volume"),
            "bid_ask_spread_pct": liquidity.get("bid_ask_spread_pct"),
        },
        "risk_snapshot": {
            "volatility_1y": risk_return.get("volatility_1y"),
            "max_drawdown_1y": risk_return.get("max_drawdown_1y"),
            "sharpe_1y": risk_return.get("sharpe_1y"),
            "beta": risk_return.get("beta"),
            "top10_holding_weight": concentration.get("top10_holding_weight"),
        },
    }


def _label_rating(value: str, lang: str) -> str:
    if lang != "zh":
        return value
    return {"BUY": "买入", "HOLD": "观望", "SELL": "卖出"}.get(value, value)


def _label_decision(value: str, lang: str) -> str:
    if lang != "zh":
        return value
    return {"buy": "买入", "hold": "观望", "sell": "卖出"}.get(str(value).lower(), value)


def _label_confidence(value: str, lang: str) -> str:
    if lang != "zh":
        return value
    return {"high": "高", "medium": "中", "low": "低"}.get(str(value).lower(), value)


def build_report(data: dict[str, Any]) -> dict[str, Any]:
    ticker = data.get("ticker", "UNKNOWN")
    company = data.get("company", ticker)
    mode = data.get("mode", "standard")
    asset_type = _normalize_asset_type(data.get("asset_type", "equity"))
    analysis_date = data.get("analysis_date", "")

    market = data.get("market", {})
    current_price = float(market.get("current_price", 0.0))

    trend = data.get("trend_signals", {})
    trend_rec = trend.get("recommendation", {}) if isinstance(trend, dict) else {}
    trend_decision = str(trend_rec.get("decision_type", "hold")).lower()
    trend_score = _to_float(trend_rec.get("score", 50), 50.0)
    ratio_results_raw = data.get("ratio_results", {})
    if isinstance(ratio_results_raw, dict) and isinstance(ratio_results_raw.get("ratios"), dict):
        ratio_results = ratio_results_raw.get("ratios", {})
    elif isinstance(ratio_results_raw, dict):
        ratio_results = ratio_results_raw
    else:
        ratio_results = {}
    etf_analysis = _build_etf_analysis(data, ratio_results) if asset_type == "etf" else {}

    weighted_target, scenarios = _weighted_target(data.get("valuation", {}), current_price)
    upside_pct = ((weighted_target - current_price) / current_price * 100) if current_price else 0.0

    valuation_decision = _valuation_decision(upside_pct)
    final_decision = _merge_decisions(valuation_decision, trend_decision)
    rating = _decision_to_rating(final_decision)

    base_confidence = _normalize_confidence(trend_rec.get("confidence", "medium"))
    data_quality, confidence_penalty = _collect_data_quality(data, mode, trend)
    confidence = _downgrade_confidence(base_confidence, confidence_penalty)
    conviction = {"high": "High", "medium": "Medium", "low": "Low"}[confidence]

    report = {
        "metadata": {
            "ticker": ticker,
            "company": company,
            "asset_type": asset_type,
            "analysis_date": analysis_date,
            "mode": mode,
        },
        "executive_summary": {
            "rating": rating,
            "current_price": current_price,
            "weighted_target_price": round(weighted_target, 4),
            "implied_upside_pct": round(upside_pct, 4),
            "conviction": conviction,
            "thesis": data.get("thesis", "") or "Thesis not provided",
        },
        "fundamental_analysis": {
            "asset_type": asset_type,
            "summary": data.get("fundamental_summary", ""),
            "ratio_results": ratio_results,
            "ratio_interpretation": data.get("ratio_interpretation", {}),
            "etf_analysis": etf_analysis,
        },
        "catalyst_analysis": {
            "near_term": data.get("catalysts", {}).get("near_term", []),
            "mid_term": data.get("catalysts", {}).get("mid_term", []),
        },
        "valuation": {
            "scenarios": scenarios,
            "weighted_target_price": round(weighted_target, 4),
        },
        "risk_assessment": {
            "risks": data.get("risks", []),
            "position_sizing": data.get("position_sizing", "1%-5% depending on conviction"),
            "invalidation": trend_rec.get(
                "invalidation",
                "Break of key support and invalidation of base-case assumptions",
            ),
        },
        "technical_context": {
            "trend_status": trend.get("trend_status", "neutral"),
            "metrics": trend.get("metrics", {}),
            "action_checklist": trend.get("action_checklist", []),
        },
        "enhanced_intelligence": data.get("intel", {}),
        "recommendation": {
            "decision_type": final_decision,
            "rating": rating,
            "confidence": confidence,
            "valuation_decision": valuation_decision,
            "trend_decision": trend_decision,
            "trend_score": trend_score,
            "next_checkpoints": data.get("next_checkpoints", []),
        },
        "data_quality": data_quality,
        "disclaimer": data.get("disclaimer", "Educational/research only. Not financial advice."),
    }
    return report


def to_markdown(report: dict[str, Any], lang: str = "zh") -> str:
    meta = report["metadata"]
    summary = report["executive_summary"]
    valuation = report["valuation"]["scenarios"]
    recommendation = report["recommendation"]
    asset_type = _normalize_asset_type(meta.get("asset_type", "equity"))
    etf_analysis = report.get("fundamental_analysis", {}).get("etf_analysis", {})

    etf_summary_zh = [
        f"- 基准指数: {etf_analysis.get('benchmark_index') or '未提供'}",
        f"- 管理人/发行商: {etf_analysis.get('issuer') or '未提供'}",
        f"- 资产类别/策略: {(etf_analysis.get('asset_class') or '未提供')} / {(etf_analysis.get('strategy') or '未提供')}",
        f"- 费用率/跟踪误差: {etf_analysis.get('cost_snapshot', {}).get('expense_ratio', 'N/A')} / {etf_analysis.get('cost_snapshot', {}).get('tracking_error', 'N/A')}",
        f"- 流动性(AUM bn/日均量/价差%): {etf_analysis.get('liquidity_snapshot', {}).get('aum_usd_bn', 'N/A')} / {etf_analysis.get('liquidity_snapshot', {}).get('avg_daily_volume', 'N/A')} / {etf_analysis.get('liquidity_snapshot', {}).get('bid_ask_spread_pct', 'N/A')}",
        f"- 风险(波动/回撤/Sharpe): {etf_analysis.get('risk_snapshot', {}).get('volatility_1y', 'N/A')} / {etf_analysis.get('risk_snapshot', {}).get('max_drawdown_1y', 'N/A')} / {etf_analysis.get('risk_snapshot', {}).get('sharpe_1y', 'N/A')}",
    ]

    etf_summary_en = [
        f"- Benchmark index: {etf_analysis.get('benchmark_index') or 'N/A'}",
        f"- Issuer: {etf_analysis.get('issuer') or 'N/A'}",
        f"- Asset class/strategy: {(etf_analysis.get('asset_class') or 'N/A')} / {(etf_analysis.get('strategy') or 'N/A')}",
        f"- Expense ratio / tracking error: {etf_analysis.get('cost_snapshot', {}).get('expense_ratio', 'N/A')} / {etf_analysis.get('cost_snapshot', {}).get('tracking_error', 'N/A')}",
        f"- Liquidity (AUM bn / ADV / spread%): {etf_analysis.get('liquidity_snapshot', {}).get('aum_usd_bn', 'N/A')} / {etf_analysis.get('liquidity_snapshot', {}).get('avg_daily_volume', 'N/A')} / {etf_analysis.get('liquidity_snapshot', {}).get('bid_ask_spread_pct', 'N/A')}",
        f"- Risk (vol / drawdown / Sharpe): {etf_analysis.get('risk_snapshot', {}).get('volatility_1y', 'N/A')} / {etf_analysis.get('risk_snapshot', {}).get('max_drawdown_1y', 'N/A')} / {etf_analysis.get('risk_snapshot', {}).get('sharpe_1y', 'N/A')}",
    ]

    if lang == "zh":
        lines = [
            f"# {meta['company']} ({meta['ticker']}) - 投资研究报告",
            "",
            "## 1. 执行摘要",
            f"- 评级: {_label_rating(summary['rating'], lang)}",
            f"- 当前价格: {summary['current_price']}",
            f"- 概率加权目标价: {summary['weighted_target_price']}",
            f"- 隐含涨跌幅: {summary['implied_upside_pct']}%",
            f"- 置信等级: {_label_confidence(summary['conviction'], lang)}",
            f"- 核心观点: {summary['thesis']}",
            "",
            "## 2. 基本面分析",
            f"- 资产类型: {'ETF' if asset_type == 'etf' else '股票'}",
            f"- 摘要: {report['fundamental_analysis'].get('summary', '') or ('ETF结构与风险分析' if asset_type == 'etf' else '')}",
            "",
            "## 3. 催化剂分析",
            f"- 近端催化剂: {', '.join(report['catalyst_analysis']['near_term']) or '无'}",
            f"- 中期催化剂: {', '.join(report['catalyst_analysis']['mid_term']) or '无'}",
            "",
            "## 4. 估值与目标价",
            f"- 乐观情景: {valuation['bull']['target']} ({valuation['bull']['probability']:.2%})",
            f"- 基准情景: {valuation['base']['target']} ({valuation['base']['probability']:.2%})",
            f"- 悲观情景: {valuation['bear']['target']} ({valuation['bear']['probability']:.2%})",
            "",
            "## 5. 风险评估与仓位建议",
            f"- 核心风险: {', '.join(report['risk_assessment']['risks']) or '无'}",
            f"- 仓位建议: {report['risk_assessment']['position_sizing']}",
            f"- 失效条件: {report['risk_assessment']['invalidation']}",
            "",
            "## 6. 技术面上下文",
            f"- 趋势状态: {report['technical_context']['trend_status']}",
            "",
            "## 7. 增强情报（详细模式）",
            "- 详见结构化 JSON 的 `enhanced_intelligence` 字段。",
            "",
            "## 8. 最终建议",
            f"- 最终动作: {_label_rating(recommendation['rating'], lang)} ({_label_decision(recommendation['decision_type'], lang)})",
            f"- 置信度: {_label_confidence(recommendation['confidence'], lang)}",
            "",
            "## 9. 数据质量",
            f"- 已验证来源: {', '.join(report['data_quality'].get('verified_sources', [])) or '无'}",
            f"- 未验证假设: {', '.join(report['data_quality'].get('unverified_assumptions', [])) or '无'}",
            f"- 置信度影响: {', '.join(report['data_quality'].get('confidence_impact', [])) or '无'}",
            "",
            "## 免责声明",
            f"- {report['disclaimer']}",
        ]
        if asset_type == "etf":
            lines[12:12] = etf_summary_zh + [""]
    else:
        lines = [
            f"# {meta['company']} ({meta['ticker']}) - EQUITY RESEARCH",
            "",
            "## 1. EXECUTIVE SUMMARY",
            f"- Rating: {summary['rating']}",
            f"- Current Price: {summary['current_price']}",
            f"- Weighted Target Price: {summary['weighted_target_price']}",
            f"- Implied Upside: {summary['implied_upside_pct']}%",
            f"- Conviction: {summary['conviction']}",
            f"- Thesis: {summary['thesis']}",
            "",
            "## 2. FUNDAMENTAL ANALYSIS",
            f"- Asset type: {'ETF' if asset_type == 'etf' else 'Equity'}",
            f"- Summary: {report['fundamental_analysis'].get('summary', '') or ('ETF structure and risk snapshot' if asset_type == 'etf' else '')}",
            "",
            "## 3. CATALYST ANALYSIS",
            f"- Near-term: {', '.join(report['catalyst_analysis']['near_term']) or 'N/A'}",
            f"- Mid-term: {', '.join(report['catalyst_analysis']['mid_term']) or 'N/A'}",
            "",
            "## 4. VALUATION & PRICE TARGETS",
            f"- Bull case: {valuation['bull']['target']} ({valuation['bull']['probability']:.2%})",
            f"- Base case: {valuation['base']['target']} ({valuation['base']['probability']:.2%})",
            f"- Bear case: {valuation['bear']['target']} ({valuation['bear']['probability']:.2%})",
            "",
            "## 5. RISK ASSESSMENT & POSITION SIZING",
            f"- Risks: {', '.join(report['risk_assessment']['risks']) or 'N/A'}",
            f"- Position Sizing: {report['risk_assessment']['position_sizing']}",
            f"- Invalidation: {report['risk_assessment']['invalidation']}",
            "",
            "## 6. TECHNICAL CONTEXT",
            f"- Trend status: {report['technical_context']['trend_status']}",
            "",
            "## 7. ENHANCED INTELLIGENCE",
            "- See structured JSON section `enhanced_intelligence` for mode-specific details.",
            "",
            "## 8. RECOMMENDATION",
            f"- Final action: {recommendation['rating']} ({recommendation['decision_type']})",
            f"- Confidence: {recommendation['confidence']}",
            "",
            "## 9. DATA QUALITY",
            f"- Verified sources: {', '.join(report['data_quality'].get('verified_sources', [])) or 'N/A'}",
            f"- Unverified assumptions: {', '.join(report['data_quality'].get('unverified_assumptions', [])) or 'N/A'}",
            f"- Confidence impact: {', '.join(report['data_quality'].get('confidence_impact', [])) or 'N/A'}",
            "",
            "## Disclaimer",
            f"- {report['disclaimer']}",
        ]
        if asset_type == "etf":
            lines[12:12] = etf_summary_en + [""]

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build JSON + markdown equity report")
    parser.add_argument("--input", required=True, help="Input JSON path")
    parser.add_argument("--json-output", help="Output JSON report path")
    parser.add_argument("--md-output", help="Output markdown report path")
    parser.add_argument("--lang", choices=["zh", "en"], default="zh", help="Markdown output language")
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    report = build_report(data)
    markdown = to_markdown(report, lang=args.lang)

    json_text = json.dumps(report, indent=2)

    if args.json_output:
        Path(args.json_output).write_text(json_text, encoding="utf-8")
    if args.md_output:
        Path(args.md_output).write_text(markdown, encoding="utf-8")

    if not args.json_output and not args.md_output:
        print(json_text)
        print("\n" + "=" * 80 + "\n")
        print(markdown)


if __name__ == "__main__":
    main()
