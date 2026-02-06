#!/usr/bin/env python3
"""
Financial ratio interpretation module.
Provides industry benchmarks and contextual analysis.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from typing import Any, Optional


class RatioInterpreter:
    """Interpret financial ratios with industry context."""

    # Industry benchmark ranges (simplified for demonstration)
    BENCHMARKS = {
        "technology": {
            "current_ratio": {"excellent": 2.5, "good": 1.8, "acceptable": 1.2, "poor": 1.0},
            "debt_to_equity": {"excellent": 0.3, "good": 0.5, "acceptable": 1.0, "poor": 2.0},
            "roe": {"excellent": 0.25, "good": 0.18, "acceptable": 0.12, "poor": 0.08},
            "gross_margin": {"excellent": 0.70, "good": 0.50, "acceptable": 0.35, "poor": 0.20},
            "pe_ratio": {"undervalued": 15, "fair": 25, "growth": 35, "expensive": 50},
        },
        "retail": {
            "current_ratio": {"excellent": 2.0, "good": 1.5, "acceptable": 1.0, "poor": 0.8},
            "debt_to_equity": {"excellent": 0.5, "good": 0.8, "acceptable": 1.5, "poor": 2.5},
            "roe": {"excellent": 0.20, "good": 0.15, "acceptable": 0.10, "poor": 0.05},
            "gross_margin": {"excellent": 0.40, "good": 0.30, "acceptable": 0.20, "poor": 0.10},
            "pe_ratio": {"undervalued": 12, "fair": 18, "growth": 25, "expensive": 35},
        },
        "financial": {
            "current_ratio": {"excellent": 1.5, "good": 1.2, "acceptable": 1.0, "poor": 0.8},
            "debt_to_equity": {"excellent": 1.0, "good": 2.0, "acceptable": 4.0, "poor": 6.0},
            "roe": {"excellent": 0.15, "good": 0.12, "acceptable": 0.08, "poor": 0.05},
            "pe_ratio": {"undervalued": 10, "fair": 15, "growth": 20, "expensive": 30},
        },
        "manufacturing": {
            "current_ratio": {"excellent": 2.2, "good": 1.7, "acceptable": 1.3, "poor": 1.0},
            "debt_to_equity": {"excellent": 0.4, "good": 0.7, "acceptable": 1.2, "poor": 2.0},
            "roe": {"excellent": 0.18, "good": 0.14, "acceptable": 0.10, "poor": 0.06},
            "gross_margin": {"excellent": 0.35, "good": 0.25, "acceptable": 0.18, "poor": 0.12},
            "pe_ratio": {"undervalued": 14, "fair": 20, "growth": 28, "expensive": 40},
        },
        "healthcare": {
            "current_ratio": {"excellent": 2.3, "good": 1.8, "acceptable": 1.4, "poor": 1.0},
            "debt_to_equity": {"excellent": 0.3, "good": 0.6, "acceptable": 1.0, "poor": 1.8},
            "roe": {"excellent": 0.22, "good": 0.16, "acceptable": 0.11, "poor": 0.07},
            "gross_margin": {"excellent": 0.65, "good": 0.45, "acceptable": 0.30, "poor": 0.20},
            "pe_ratio": {"undervalued": 18, "fair": 28, "growth": 40, "expensive": 55},
        },
        "etf": {
            "expense_ratio": {"direction": "lower", "excellent": 0.0015, "good": 0.0030, "acceptable": 0.0060},
            "tracking_error": {"direction": "lower", "excellent": 0.0025, "good": 0.0050, "acceptable": 0.0100},
            "aum_usd_bn": {"direction": "higher", "excellent": 20.0, "good": 5.0, "acceptable": 1.0},
            "avg_daily_volume": {"direction": "higher", "excellent": 2000000, "good": 500000, "acceptable": 100000},
            "bid_ask_spread_pct": {"direction": "lower", "excellent": 0.08, "good": 0.15, "acceptable": 0.30},
            "one_year_return": {"direction": "higher", "excellent": 0.15, "good": 0.08, "acceptable": 0.03},
            "sharpe_1y": {"direction": "higher", "excellent": 1.2, "good": 0.8, "acceptable": 0.3},
            "volatility_1y": {"direction": "lower", "excellent": 0.12, "good": 0.18, "acceptable": 0.25},
            "max_drawdown_1y": {
                "direction": "lower",
                "excellent": 0.10,
                "good": 0.18,
                "acceptable": 0.30,
                "abs_value": True,
            },
            "beta": {"direction": "range", "excellent_low": 0.8, "excellent_high": 1.2, "acceptable_low": 0.6, "acceptable_high": 1.4},
            "top10_holding_weight": {"direction": "lower", "excellent": 0.25, "good": 0.40, "acceptable": 0.55},
            "sector_concentration_hhi": {"direction": "lower", "excellent": 0.12, "good": 0.18, "acceptable": 0.25},
        },
    }

    def __init__(self, industry: str = "general"):
        """
        Initialize interpreter with industry context.

        Args:
            industry: Industry sector for benchmarking
        """
        self.industry = industry.lower()
        self.benchmarks = self.BENCHMARKS.get(self.industry, self._get_general_benchmarks())

    def _get_general_benchmarks(self) -> dict[str, Any]:
        """Get general industry-agnostic benchmarks."""
        return {
            "current_ratio": {"excellent": 2.0, "good": 1.5, "acceptable": 1.0, "poor": 0.8},
            "debt_to_equity": {"excellent": 0.5, "good": 1.0, "acceptable": 1.5, "poor": 2.5},
            "roe": {"excellent": 0.20, "good": 0.15, "acceptable": 0.10, "poor": 0.05},
            "gross_margin": {"excellent": 0.40, "good": 0.30, "acceptable": 0.20, "poor": 0.10},
            "pe_ratio": {"undervalued": 15, "fair": 22, "growth": 30, "expensive": 45},
        }

    def interpret_ratio(self, ratio_name: str, value: float) -> dict[str, Any]:
        """
        Interpret a single ratio with context.

        Args:
            ratio_name: Name of the ratio
            value: Calculated ratio value

        Returns:
            Dictionary with interpretation details
        """
        interpretation = {
            "value": value,
            "rating": "N/A",
            "message": "",
            "recommendation": "",
            "benchmark_comparison": {},
        }

        if self.industry == "etf" and ratio_name in self.benchmarks:
            benchmark = self.benchmarks[ratio_name]
            interpretation["benchmark_comparison"] = benchmark
            interpreted_value = abs(value) if benchmark.get("abs_value") else value
            direction = benchmark.get("direction")

            if direction == "higher":
                if interpreted_value >= benchmark["excellent"]:
                    interpretation["rating"] = "Excellent"
                    interpretation["message"] = "Strong ETF quality relative to benchmark"
                elif interpreted_value >= benchmark["good"]:
                    interpretation["rating"] = "Good"
                    interpretation["message"] = "Healthy ETF profile"
                elif interpreted_value >= benchmark["acceptable"]:
                    interpretation["rating"] = "Acceptable"
                    interpretation["message"] = "Usable profile but monitor closely"
                else:
                    interpretation["rating"] = "Poor"
                    interpretation["message"] = "Below ETF benchmark expectations"

            elif direction == "lower":
                if interpreted_value <= benchmark["excellent"]:
                    interpretation["rating"] = "Excellent"
                    interpretation["message"] = "Low friction/risk vs ETF benchmark"
                elif interpreted_value <= benchmark["good"]:
                    interpretation["rating"] = "Good"
                    interpretation["message"] = "Reasonable ETF quality"
                elif interpreted_value <= benchmark["acceptable"]:
                    interpretation["rating"] = "Acceptable"
                    interpretation["message"] = "Borderline quality, monitor deterioration"
                else:
                    interpretation["rating"] = "Poor"
                    interpretation["message"] = "Unfavorable ETF metric for this style"

            elif direction == "range":
                low = benchmark["excellent_low"]
                high = benchmark["excellent_high"]
                acceptable_low = benchmark["acceptable_low"]
                acceptable_high = benchmark["acceptable_high"]
                if low <= interpreted_value <= high:
                    interpretation["rating"] = "Excellent"
                    interpretation["message"] = "Metric is in target ETF range"
                elif acceptable_low <= interpreted_value <= acceptable_high:
                    interpretation["rating"] = "Acceptable"
                    interpretation["message"] = "Metric is outside target but still acceptable"
                else:
                    interpretation["rating"] = "Poor"
                    interpretation["message"] = "Metric deviates materially from target range"

        elif ratio_name in self.benchmarks:
            benchmark = self.benchmarks[ratio_name]
            interpretation["benchmark_comparison"] = benchmark

            # Determine rating based on benchmarks
            if ratio_name in ["current_ratio", "roe", "gross_margin"]:
                # Higher is better
                if value >= benchmark["excellent"]:
                    interpretation["rating"] = "Excellent"
                    interpretation["message"] = (
                        "Performance significantly exceeds industry standards"
                    )
                elif value >= benchmark["good"]:
                    interpretation["rating"] = "Good"
                    interpretation["message"] = (
                        f"Above average performance for {self.industry} industry"
                    )
                elif value >= benchmark["acceptable"]:
                    interpretation["rating"] = "Acceptable"
                    interpretation["message"] = "Meets industry standards"
                else:
                    interpretation["rating"] = "Poor"
                    interpretation["message"] = "Below industry standards - attention needed"

            elif ratio_name == "debt_to_equity":
                # Lower is better
                if value <= benchmark["excellent"]:
                    interpretation["rating"] = "Excellent"
                    interpretation["message"] = "Very conservative capital structure"
                elif value <= benchmark["good"]:
                    interpretation["rating"] = "Good"
                    interpretation["message"] = "Healthy leverage level"
                elif value <= benchmark["acceptable"]:
                    interpretation["rating"] = "Acceptable"
                    interpretation["message"] = "Moderate leverage"
                else:
                    interpretation["rating"] = "Poor"
                    interpretation["message"] = "High leverage - potential risk"

            elif ratio_name == "pe_ratio":
                # Context-dependent
                if value > 0:
                    if value < benchmark["undervalued"]:
                        interpretation["rating"] = "Potentially Undervalued"
                        interpretation["message"] = (
                            f"Trading below typical {self.industry} multiples"
                        )
                    elif value < benchmark["fair"]:
                        interpretation["rating"] = "Fair Value"
                        interpretation["message"] = "In line with industry averages"
                    elif value < benchmark["growth"]:
                        interpretation["rating"] = "Growth Premium"
                        interpretation["message"] = "Market pricing in growth expectations"
                    else:
                        interpretation["rating"] = "Expensive"
                        interpretation["message"] = "High valuation relative to industry"

        # Add specific recommendations
        interpretation["recommendation"] = self._get_recommendation(
            ratio_name, interpretation["rating"]
        )

        return interpretation

    def _get_recommendation(self, ratio_name: str, rating: str) -> str:
        """Generate actionable recommendations based on ratio and rating."""
        recommendations = {
            "current_ratio": {
                "Poor": "Consider improving working capital management, reducing short-term debt, or increasing liquid assets",
                "Acceptable": "Monitor liquidity closely and consider building additional cash reserves",
                "Good": "Maintain current liquidity management practices",
                "Excellent": "Strong liquidity position - consider productive use of excess cash",
            },
            "debt_to_equity": {
                "Poor": "High leverage increases financial risk - consider debt reduction strategies",
                "Acceptable": "Monitor debt levels and ensure adequate interest coverage",
                "Good": "Balanced capital structure - maintain current approach",
                "Excellent": "Conservative leverage - may consider strategic use of debt for growth",
            },
            "roe": {
                "Poor": "Focus on improving operational efficiency and profitability",
                "Acceptable": "Explore opportunities to enhance returns through operational improvements",
                "Good": "Solid returns - continue current strategies",
                "Excellent": "Outstanding performance - ensure sustainability of high returns",
            },
            "pe_ratio": {
                "Potentially Undervalued": "May present buying opportunity if fundamentals are solid",
                "Fair Value": "Reasonably priced relative to industry peers",
                "Growth Premium": "Ensure growth prospects justify premium valuation",
                "Expensive": "Consider valuation risk - ensure fundamentals support high multiple",
            },
            "expense_ratio": {
                "Poor": "Prefer lower-cost alternatives unless exposure is unique",
                "Acceptable": "Cost is manageable but compare with cheaper peers",
                "Good": "Cost profile is competitive",
                "Excellent": "Very low fee drag supports long-term compounding",
            },
            "tracking_error": {
                "Poor": "Tracking quality is weak; verify replication method and liquidity",
                "Acceptable": "Tracking is serviceable but needs monitoring",
                "Good": "Tracking quality is reliable",
                "Excellent": "Tracking efficiency is strong",
            },
            "bid_ask_spread_pct": {
                "Poor": "Execution cost may be high; use limit orders and avoid illiquid windows",
                "Acceptable": "Spread is tradable with careful execution",
                "Good": "Execution friction is manageable",
                "Excellent": "Tight spread supports efficient entry/exit",
            },
            "top10_holding_weight": {
                "Poor": "Concentration risk is elevated; position size conservatively",
                "Acceptable": "Concentration is moderate; monitor top holdings drift",
                "Good": "Diversification is reasonable",
                "Excellent": "Diversification quality is strong",
            },
        }

        if ratio_name in recommendations and rating in recommendations[ratio_name]:
            return recommendations[ratio_name][rating]

        return "Continue monitoring this metric"

    def analyze_trend(
        self, ratio_name: str, values: list[float], periods: list[str]
    ) -> dict[str, Any]:
        """
        Analyze trend in a ratio over time.

        Args:
            ratio_name: Name of the ratio
            values: List of ratio values
            periods: List of period labels

        Returns:
            Trend analysis dictionary
        """
        if len(values) < 2:
            return {
                "trend": "Insufficient data",
                "message": "Need at least 2 periods for trend analysis",
            }

        # Calculate trend
        first_value = values[0]
        last_value = values[-1]
        change = last_value - first_value
        pct_change = (change / abs(first_value)) * 100 if first_value != 0 else 0

        # Determine trend direction
        if abs(pct_change) < 5:
            trend = "Stable"
        elif pct_change > 0:
            trend = "Improving" if ratio_name != "debt_to_equity" else "Deteriorating"
        else:
            trend = "Deteriorating" if ratio_name != "debt_to_equity" else "Improving"

        return {
            "trend": trend,
            "change": change,
            "pct_change": pct_change,
            "message": f"{ratio_name} has {'increased' if change > 0 else 'decreased'} by {abs(pct_change):.1f}% from {periods[0]} to {periods[-1]}",
            "values": list(zip(periods, values)),
        }

    def generate_report(self, ratios: dict[str, Any]) -> str:
        """
        Generate a comprehensive interpretation report.

        Args:
            ratios: Dictionary of calculated ratios

        Returns:
            Formatted report string
        """
        report_lines = [
            f"Financial Analysis Report - {self.industry.title()} Industry Context",
            "=" * 70,
            "",
        ]

        for category, category_ratios in ratios.items():
            report_lines.append(f"\n{category.upper()} ANALYSIS")
            report_lines.append("-" * 40)

            for ratio_name, value in category_ratios.items():
                if isinstance(value, (int, float)):
                    interpretation = self.interpret_ratio(ratio_name, value)
                    report_lines.append(f"\n{ratio_name.replace('_', ' ').title()}:")
                    report_lines.append(f"  Value: {value:.2f}")
                    report_lines.append(f"  Rating: {interpretation['rating']}")
                    report_lines.append(f"  Analysis: {interpretation['message']}")
                    report_lines.append(f"  Action: {interpretation['recommendation']}")

        return "\n".join(report_lines)


def perform_comprehensive_analysis(
    ratios: dict[str, Any],
    industry: str = "general",
    historical_data: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """
    Perform comprehensive ratio analysis with interpretations.

    Args:
        ratios: Calculated financial ratios
        industry: Industry sector for benchmarking
        historical_data: Optional historical ratio data for trend analysis

    Returns:
        Complete analysis with interpretations and recommendations
    """
    inferred_industry = industry
    if industry == "general":
        etf_ratio_keys = {"expense_ratio", "tracking_error", "aum_usd_bn", "sharpe_1y"}
        flat_keys = set()
        for _category, category_ratios in ratios.items():
            if isinstance(category_ratios, dict):
                flat_keys.update(category_ratios.keys())
        if flat_keys & etf_ratio_keys:
            inferred_industry = "etf"

    interpreter = RatioInterpreter(inferred_industry)
    analysis = {
        "industry": interpreter.industry,
        "current_analysis": {},
        "trend_analysis": {},
        "overall_health": {},
        "recommendations": [],
    }

    # Analyze current ratios
    for category, category_ratios in ratios.items():
        analysis["current_analysis"][category] = {}
        for ratio_name, value in category_ratios.items():
            if isinstance(value, (int, float)):
                analysis["current_analysis"][category][ratio_name] = interpreter.interpret_ratio(
                    ratio_name, value
                )

    # Perform trend analysis if historical data provided
    if historical_data:
        for ratio_name, historical_values in historical_data.items():
            if "values" in historical_values and "periods" in historical_values:
                analysis["trend_analysis"][ratio_name] = interpreter.analyze_trend(
                    ratio_name, historical_values["values"], historical_values["periods"]
                )

    # Generate overall health assessment
    analysis["overall_health"] = _assess_overall_health(analysis["current_analysis"])

    # Generate key recommendations
    analysis["recommendations"] = _generate_key_recommendations(analysis)

    # Add formatted report
    analysis["report"] = interpreter.generate_report(ratios)

    return analysis


def _assess_overall_health(current_analysis: dict[str, Any]) -> dict[str, str]:
    """Assess overall financial health based on ratio analysis."""
    ratings = []
    for _category, category_analysis in current_analysis.items():
        for _ratio_name, ratio_analysis in category_analysis.items():
            if "rating" in ratio_analysis:
                ratings.append(ratio_analysis["rating"])

    # Simple scoring system
    score_map = {
        "Excellent": 4,
        "Good": 3,
        "Acceptable": 2,
        "Poor": 1,
        "Fair Value": 3,
        "Potentially Undervalued": 3,
        "Growth Premium": 2,
        "Expensive": 1,
    }

    scores = [score_map.get(rating, 2) for rating in ratings]
    avg_score = sum(scores) / len(scores) if scores else 0

    if avg_score >= 3.5:
        health = "Excellent"
        message = "Company shows strong financial health across most metrics"
    elif avg_score >= 2.5:
        health = "Good"
        message = "Overall healthy financial position with some areas for improvement"
    elif avg_score >= 1.5:
        health = "Fair"
        message = "Mixed financial indicators - attention needed in several areas"
    else:
        health = "Poor"
        message = "Significant financial challenges requiring immediate attention"

    return {"status": health, "message": message, "score": f"{avg_score:.1f}/4.0"}


def _generate_key_recommendations(analysis: dict[str, Any]) -> list[str]:
    """Generate prioritized recommendations based on analysis."""
    recommendations = []

    # Check for critical issues
    for _category, category_analysis in analysis["current_analysis"].items():
        for ratio_name, ratio_analysis in category_analysis.items():
            if ratio_analysis.get("rating") == "Poor":
                recommendations.append(
                    f"Priority: Address {ratio_name.replace('_', ' ')} - {ratio_analysis.get('recommendation', '')}"
                )

    # Add trend-based recommendations
    for ratio_name, trend in analysis.get("trend_analysis", {}).items():
        if trend.get("trend") == "Deteriorating":
            recommendations.append(
                f"Monitor: {ratio_name.replace('_', ' ')} showing negative trend"
            )

    # Add general recommendations if healthy
    if not recommendations:
        recommendations.append("Continue current financial management practices")
        recommendations.append("Consider strategic growth opportunities")

    return recommendations[:5]  # Return top 5 recommendations


def _load_ratio_payload(input_path: Path) -> dict[str, Any]:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Input JSON must be an object")

    ratios = payload.get("ratios")
    if isinstance(ratios, dict):
        return ratios

    # Fallback: input is already ratio categories.
    return payload


def _load_historical_payload(path: str | None) -> Optional[dict[str, Any]]:
    if not path:
        return None
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Interpret ratio results with industry benchmarks")
    parser.add_argument("--input", required=True, help="Path to ratio JSON")
    parser.add_argument("--output", help="Optional output JSON path")
    parser.add_argument("--industry", default="general", help="Industry context for benchmarks")
    parser.add_argument(
        "--historical",
        help="Optional historical ratio JSON for trend analysis: {ratio: {values: [], periods: []}}",
    )
    parser.add_argument("--indent", type=int, default=2, help="JSON indent spaces (default: 2)")
    args = parser.parse_args()

    analysis = perform_comprehensive_analysis(
        ratios=_load_ratio_payload(Path(args.input)),
        industry=args.industry,
        historical_data=_load_historical_payload(args.historical),
    )
    text = json.dumps(analysis, indent=args.indent)

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
