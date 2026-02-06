#!/usr/bin/env python3
"""Financial ratio calculation module with CLI support."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


class FinancialRatioCalculator:
    """Calculate financial ratios from financial statement data."""

    REQUIRED_FIELDS: tuple[tuple[str, str], ...] = (
        ("income_statement", "revenue"),
        ("income_statement", "cost_of_goods_sold"),
        ("income_statement", "operating_income"),
        ("income_statement", "ebit"),
        ("income_statement", "ebitda"),
        ("income_statement", "interest_expense"),
        ("income_statement", "net_income"),
        ("balance_sheet", "shareholders_equity"),
        ("balance_sheet", "total_assets"),
        ("balance_sheet", "current_assets"),
        ("balance_sheet", "current_liabilities"),
        ("balance_sheet", "inventory"),
        ("balance_sheet", "cash_and_equivalents"),
        ("balance_sheet", "total_debt"),
        ("balance_sheet", "current_portion_long_term_debt"),
        ("balance_sheet", "accounts_receivable"),
        ("market_data", "share_price"),
        ("market_data", "shares_outstanding"),
        ("market_data", "earnings_growth_rate"),
    )
    ETF_REQUIRED_FIELDS: tuple[tuple[str, str], ...] = (
        ("etf_data", "expense_ratio"),
        ("etf_data", "tracking_error"),
        ("etf_data", "aum"),
        ("etf_data", "avg_daily_volume"),
        ("etf_data", "bid_ask_spread_pct"),
        ("etf_data", "one_year_return"),
        ("etf_data", "volatility_1y"),
        ("etf_data", "max_drawdown_1y"),
        ("etf_data", "sharpe_1y"),
        ("etf_data", "top10_holding_weight"),
    )

    def __init__(self, financial_data: dict[str, Any]):
        """
        Initialize with financial statement data.

        Args:
            financial_data: Dictionary containing income_statement, balance_sheet,
                          cash_flow, and market_data
        """
        self.income_statement = financial_data.get("income_statement", {})
        self.balance_sheet = financial_data.get("balance_sheet", {})
        self.cash_flow = financial_data.get("cash_flow", {})
        self.market_data = financial_data.get("market_data", {})
        self.etf_data = financial_data.get("etf_data", {})
        self.asset_type = str(financial_data.get("asset_type", "equity")).lower()
        self.ratios: dict[str, Any] = {}
        self.missing_fields: set[str] = set()
        self.invalid_fields: set[str] = set()

    def safe_divide(self, numerator: float, denominator: float, default: float = 0.0) -> float:
        """Safely divide two numbers, returning default if denominator is zero."""
        if denominator == 0:
            return default
        return numerator / denominator

    def _get_number(
        self,
        section: dict[str, Any],
        section_name: str,
        field_name: str,
        default: float = 0.0,
    ) -> float:
        """Read numeric field and track data-quality issues."""
        path = f"{section_name}.{field_name}"
        if field_name not in section or section.get(field_name) is None:
            self.missing_fields.add(path)
            return default

        value = section.get(field_name)
        try:
            return float(value)
        except (TypeError, ValueError):
            self.invalid_fields.add(path)
            return default

    def calculate_profitability_ratios(self) -> dict[str, float]:
        """Calculate profitability ratios."""
        ratios: dict[str, float] = {}

        # ROE (Return on Equity)
        net_income = self._get_number(self.income_statement, "income_statement", "net_income")
        shareholders_equity = self._get_number(
            self.balance_sheet, "balance_sheet", "shareholders_equity"
        )
        ratios["roe"] = self.safe_divide(net_income, shareholders_equity)

        # ROA (Return on Assets)
        total_assets = self._get_number(self.balance_sheet, "balance_sheet", "total_assets")
        ratios["roa"] = self.safe_divide(net_income, total_assets)

        # Gross Margin
        revenue = self._get_number(self.income_statement, "income_statement", "revenue")
        cogs = self._get_number(self.income_statement, "income_statement", "cost_of_goods_sold")
        gross_profit = revenue - cogs
        ratios["gross_margin"] = self.safe_divide(gross_profit, revenue)

        # Operating Margin
        operating_income = self._get_number(
            self.income_statement, "income_statement", "operating_income"
        )
        ratios["operating_margin"] = self.safe_divide(operating_income, revenue)

        # Net Margin
        ratios["net_margin"] = self.safe_divide(net_income, revenue)

        return ratios

    def calculate_liquidity_ratios(self) -> dict[str, float]:
        """Calculate liquidity ratios."""
        ratios: dict[str, float] = {}

        current_assets = self._get_number(self.balance_sheet, "balance_sheet", "current_assets")
        current_liabilities = self._get_number(
            self.balance_sheet, "balance_sheet", "current_liabilities"
        )

        # Current Ratio
        ratios["current_ratio"] = self.safe_divide(current_assets, current_liabilities)

        # Quick Ratio (Acid Test)
        inventory = self._get_number(self.balance_sheet, "balance_sheet", "inventory")
        quick_assets = current_assets - inventory
        ratios["quick_ratio"] = self.safe_divide(quick_assets, current_liabilities)

        # Cash Ratio
        cash = self._get_number(self.balance_sheet, "balance_sheet", "cash_and_equivalents")
        ratios["cash_ratio"] = self.safe_divide(cash, current_liabilities)

        return ratios

    def calculate_leverage_ratios(self) -> dict[str, float]:
        """Calculate leverage/solvency ratios."""
        ratios: dict[str, float] = {}

        total_debt = self._get_number(self.balance_sheet, "balance_sheet", "total_debt")
        shareholders_equity = self._get_number(
            self.balance_sheet, "balance_sheet", "shareholders_equity"
        )

        # Debt-to-Equity Ratio
        ratios["debt_to_equity"] = self.safe_divide(total_debt, shareholders_equity)

        # Interest Coverage Ratio
        ebit = self._get_number(self.income_statement, "income_statement", "ebit")
        interest_expense = self._get_number(
            self.income_statement, "income_statement", "interest_expense"
        )
        ratios["interest_coverage"] = self.safe_divide(ebit, interest_expense)

        # Debt Service Coverage Ratio
        net_operating_income = self._get_number(
            self.income_statement, "income_statement", "operating_income"
        )
        current_debt = self._get_number(
            self.balance_sheet, "balance_sheet", "current_portion_long_term_debt"
        )
        total_debt_service = interest_expense + current_debt
        ratios["debt_service_coverage"] = self.safe_divide(net_operating_income, total_debt_service)

        return ratios

    def calculate_efficiency_ratios(self) -> dict[str, float]:
        """Calculate efficiency/activity ratios."""
        ratios: dict[str, float] = {}

        revenue = self._get_number(self.income_statement, "income_statement", "revenue")
        total_assets = self._get_number(self.balance_sheet, "balance_sheet", "total_assets")

        # Asset Turnover
        ratios["asset_turnover"] = self.safe_divide(revenue, total_assets)

        # Inventory Turnover
        cogs = self._get_number(self.income_statement, "income_statement", "cost_of_goods_sold")
        inventory = self._get_number(self.balance_sheet, "balance_sheet", "inventory")
        ratios["inventory_turnover"] = self.safe_divide(cogs, inventory)

        # Receivables Turnover
        accounts_receivable = self._get_number(
            self.balance_sheet, "balance_sheet", "accounts_receivable"
        )
        ratios["receivables_turnover"] = self.safe_divide(revenue, accounts_receivable)

        # Days Sales Outstanding
        ratios["days_sales_outstanding"] = self.safe_divide(365, ratios["receivables_turnover"])

        return ratios

    def calculate_valuation_ratios(self) -> dict[str, float]:
        """Calculate valuation ratios."""
        ratios: dict[str, float] = {}

        share_price = self._get_number(self.market_data, "market_data", "share_price")
        shares_outstanding = self._get_number(self.market_data, "market_data", "shares_outstanding")
        market_cap = share_price * shares_outstanding

        # P/E Ratio
        net_income = self._get_number(self.income_statement, "income_statement", "net_income")
        eps = self.safe_divide(net_income, shares_outstanding)
        ratios["pe_ratio"] = self.safe_divide(share_price, eps)
        ratios["eps"] = eps

        # P/B Ratio
        book_value = self._get_number(self.balance_sheet, "balance_sheet", "shareholders_equity")
        book_value_per_share = self.safe_divide(book_value, shares_outstanding)
        ratios["pb_ratio"] = self.safe_divide(share_price, book_value_per_share)
        ratios["book_value_per_share"] = book_value_per_share

        # P/S Ratio
        revenue = self._get_number(self.income_statement, "income_statement", "revenue")
        ratios["ps_ratio"] = self.safe_divide(market_cap, revenue)

        # EV/EBITDA
        ebitda = self._get_number(self.income_statement, "income_statement", "ebitda")
        total_debt = self._get_number(self.balance_sheet, "balance_sheet", "total_debt")
        cash = self._get_number(self.balance_sheet, "balance_sheet", "cash_and_equivalents")
        enterprise_value = market_cap + total_debt - cash
        ratios["ev_to_ebitda"] = self.safe_divide(enterprise_value, ebitda)

        # PEG Ratio (if growth rate available)
        earnings_growth = self._get_number(self.market_data, "market_data", "earnings_growth_rate")
        if earnings_growth > 0:
            ratios["peg_ratio"] = self.safe_divide(ratios["pe_ratio"], earnings_growth * 100)

        return ratios

    def calculate_etf_ratios(self) -> dict[str, Any]:
        """Calculate ETF-focused metrics and derived indicators."""
        expense_ratio = self._get_number(self.etf_data, "etf_data", "expense_ratio")
        tracking_error = self._get_number(self.etf_data, "etf_data", "tracking_error")
        aum = self._get_number(self.etf_data, "etf_data", "aum")
        avg_daily_volume = self._get_number(self.etf_data, "etf_data", "avg_daily_volume")
        bid_ask_spread_pct = self._get_number(self.etf_data, "etf_data", "bid_ask_spread_pct")
        one_year_return = self._get_number(self.etf_data, "etf_data", "one_year_return")
        three_year_return_annualized = self._get_number(
            self.etf_data, "etf_data", "three_year_return_annualized"
        )
        five_year_return_annualized = self._get_number(
            self.etf_data, "etf_data", "five_year_return_annualized"
        )
        volatility_1y = self._get_number(self.etf_data, "etf_data", "volatility_1y")
        max_drawdown_1y = self._get_number(self.etf_data, "etf_data", "max_drawdown_1y")
        sharpe_1y = self._get_number(self.etf_data, "etf_data", "sharpe_1y")
        beta = self._get_number(self.etf_data, "etf_data", "beta")
        turnover_ratio = self._get_number(self.etf_data, "etf_data", "turnover_ratio")
        dividend_yield = self._get_number(self.etf_data, "etf_data", "dividend_yield")
        top10_holding_weight = self._get_number(self.etf_data, "etf_data", "top10_holding_weight")
        sector_concentration_hhi = self._get_number(
            self.etf_data, "etf_data", "sector_concentration_hhi"
        )

        spread_bps = bid_ask_spread_pct * 100.0
        drawdown_abs = abs(max_drawdown_1y)
        return_over_drawdown = self.safe_divide(one_year_return, drawdown_abs)
        risk_adjusted_return = self.safe_divide(one_year_return, volatility_1y)

        return {
            "cost_efficiency": {
                "expense_ratio": expense_ratio,
                "turnover_ratio": turnover_ratio,
                "tracking_error": tracking_error,
            },
            "liquidity": {
                "aum_usd_bn": self.safe_divide(aum, 1_000_000_000.0),
                "avg_daily_volume": avg_daily_volume,
                "bid_ask_spread_pct": bid_ask_spread_pct,
                "bid_ask_spread_bps": spread_bps,
            },
            "risk_return": {
                "one_year_return": one_year_return,
                "three_year_return_annualized": three_year_return_annualized,
                "five_year_return_annualized": five_year_return_annualized,
                "volatility_1y": volatility_1y,
                "max_drawdown_1y": max_drawdown_1y,
                "sharpe_1y": sharpe_1y,
                "beta": beta,
                "risk_adjusted_return": risk_adjusted_return,
                "return_over_drawdown": return_over_drawdown,
                "dividend_yield": dividend_yield,
            },
            "concentration": {
                "top10_holding_weight": top10_holding_weight,
                "sector_concentration_hhi": sector_concentration_hhi,
            },
        }

    def calculate_all_ratios(self) -> dict[str, Any]:
        """Calculate all financial ratios."""
        if self.asset_type == "etf":
            return self.calculate_etf_ratios()

        return {
            "profitability": self.calculate_profitability_ratios(),
            "liquidity": self.calculate_liquidity_ratios(),
            "leverage": self.calculate_leverage_ratios(),
            "efficiency": self.calculate_efficiency_ratios(),
            "valuation": self.calculate_valuation_ratios(),
        }

    def get_data_quality(self) -> dict[str, Any]:
        """Summarize data-quality issues used in calculations."""
        required_fields = self.ETF_REQUIRED_FIELDS if self.asset_type == "etf" else self.REQUIRED_FIELDS
        required_paths = {f"{section}.{field}" for section, field in required_fields}
        total = len(required_fields)
        required_missing = sorted(path for path in self.missing_fields if path in required_paths)
        required_invalid = sorted(path for path in self.invalid_fields if path in required_paths)
        optional_missing = sorted(path for path in self.missing_fields if path not in required_paths)
        optional_invalid = sorted(path for path in self.invalid_fields if path not in required_paths)
        missing_count = len(required_missing)
        invalid_count = len(required_invalid)
        coverage_pct = round(((total - missing_count) / total * 100), 2) if total else 100.0

        if invalid_count > 0 or missing_count >= 6:
            confidence_hint = "low"
        elif missing_count > 0:
            confidence_hint = "medium"
        else:
            confidence_hint = "high"

        return {
            "asset_type": self.asset_type,
            "required_fields_count": total,
            "missing_fields_count": missing_count,
            "invalid_fields_count": invalid_count,
            "coverage_pct": coverage_pct,
            "missing_fields": required_missing,
            "invalid_fields": required_invalid,
            "optional_missing_fields": optional_missing,
            "optional_invalid_fields": optional_invalid,
            "confidence_hint": confidence_hint,
        }

    def interpret_ratio(self, ratio_name: str, value: float) -> str:
        """Provide interpretation for a specific ratio."""
        interpretations = {
            "current_ratio": lambda v: (
                "Strong liquidity"
                if v > 2
                else "Adequate liquidity"
                if v > 1.5
                else "Potential liquidity concerns"
                if v > 1
                else "Liquidity issues"
            ),
            "debt_to_equity": lambda v: (
                "Low leverage"
                if v < 0.5
                else "Moderate leverage"
                if v < 1
                else "High leverage"
                if v < 2
                else "Very high leverage"
            ),
            "roe": lambda v: (
                "Excellent returns"
                if v > 0.20
                else "Good returns"
                if v > 0.15
                else "Average returns"
                if v > 0.10
                else "Below average returns"
                if v > 0
                else "Negative returns"
            ),
            "pe_ratio": lambda v: (
                "Potentially undervalued"
                if 0 < v < 15
                else "Fair value"
                if 15 <= v < 25
                else "Growth premium"
                if 25 <= v < 40
                else "High valuation"
                if v >= 40
                else "N/A (negative earnings)"
                if v <= 0
                else "N/A"
            ),
        }

        if ratio_name in interpretations:
            return interpretations[ratio_name](value)
        return "No interpretation available"

    def format_ratio(self, name: str, value: float, format_type: str = "ratio") -> str:
        """Format ratio value for display."""
        if format_type == "percentage":
            return f"{value * 100:.2f}%"
        elif format_type == "times":
            return f"{value:.2f}x"
        elif format_type == "days":
            return f"{value:.1f} days"
        elif format_type == "currency":
            return f"${value:.2f}"
        else:
            return f"{value:.2f}"


def calculate_ratios_from_data(financial_data: dict[str, Any]) -> dict[str, Any]:
    """
    Main function to calculate all ratios from financial data.

    Args:
        financial_data: Dictionary with financial statement data

    Returns:
        Dictionary with calculated ratios and interpretations
    """
    calculator = FinancialRatioCalculator(financial_data)
    ratios = calculator.calculate_all_ratios()

    # Add interpretations
    interpretations = {}
    for category, category_ratios in ratios.items():
        interpretations[category] = {}
        for ratio_name, value in category_ratios.items():
            interpretations[category][ratio_name] = {
                "value": value,
                "formatted": calculator.format_ratio(ratio_name, value),
                "interpretation": calculator.interpret_ratio(ratio_name, value),
            }

    return {
        "ratios": ratios,
        "interpretations": interpretations,
        "summary": generate_summary(ratios),
        "data_quality": calculator.get_data_quality(),
    }


def generate_summary(ratios: dict[str, Any]) -> str:
    """Generate a text summary of the financial analysis."""
    if "cost_efficiency" in ratios and "risk_return" in ratios:
        cost = ratios.get("cost_efficiency", {})
        liq = ratios.get("liquidity", {})
        rr = ratios.get("risk_return", {})
        conc = ratios.get("concentration", {})

        summary_parts = []
        if "expense_ratio" in cost and "tracking_error" in cost:
            summary_parts.append(
                f"ETF cost profile: expense ratio {cost['expense_ratio'] * 100:.2f}%, tracking error {cost['tracking_error'] * 100:.2f}%."
            )
        if "aum_usd_bn" in liq and "avg_daily_volume" in liq:
            summary_parts.append(
                f"Liquidity profile: AUM {liq['aum_usd_bn']:.2f}bn, average daily volume {liq['avg_daily_volume']:.0f}."
            )
        if "one_year_return" in rr and "sharpe_1y" in rr:
            summary_parts.append(
                f"Risk-return: 1Y return {rr['one_year_return'] * 100:.2f}%, Sharpe {rr['sharpe_1y']:.2f}."
            )
        if "top10_holding_weight" in conc:
            summary_parts.append(
                f"Concentration: top-10 holdings weight {conc['top10_holding_weight'] * 100:.2f}%."
            )
        return " ".join(summary_parts) if summary_parts else "ETF ratio summary unavailable."

    summary_parts = []

    # Profitability summary
    prof = ratios.get("profitability", {})
    if prof.get("roe", 0) > 0:
        summary_parts.append(
            f"ROE of {prof['roe'] * 100:.1f}% indicates {'strong' if prof['roe'] > 0.15 else 'moderate'} shareholder returns."
        )

    # Liquidity summary
    liq = ratios.get("liquidity", {})
    if liq.get("current_ratio", 0) > 0:
        summary_parts.append(
            f"Current ratio of {liq['current_ratio']:.2f} suggests {'good' if liq['current_ratio'] > 1.5 else 'potential'} liquidity {'position' if liq['current_ratio'] > 1.5 else 'concerns'}."
        )

    # Leverage summary
    lev = ratios.get("leverage", {})
    if lev.get("debt_to_equity", 0) >= 0:
        summary_parts.append(
            f"Debt-to-equity of {lev['debt_to_equity']:.2f} indicates {'conservative' if lev['debt_to_equity'] < 0.5 else 'moderate' if lev['debt_to_equity'] < 1 else 'high'} leverage."
        )

    # Valuation summary
    val = ratios.get("valuation", {})
    if val.get("pe_ratio", 0) > 0:
        summary_parts.append(
            f"P/E ratio of {val['pe_ratio']:.1f} suggests the stock is trading at {'a discount' if val['pe_ratio'] < 15 else 'fair value' if val['pe_ratio'] < 25 else 'a premium'}."
        )

    return " ".join(summary_parts) if summary_parts else "Insufficient data for summary."


def _load_financial_data(input_path: Path) -> dict[str, Any]:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Input JSON must be an object")

    if isinstance(payload.get("financial_data"), dict):
        return payload["financial_data"]
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Calculate financial ratios from statement data")
    parser.add_argument("--input", required=True, help="Path to financial data JSON")
    parser.add_argument("--output", help="Optional output JSON path")
    parser.add_argument("--indent", type=int, default=2, help="JSON indent spaces (default: 2)")
    args = parser.parse_args()

    result = calculate_ratios_from_data(_load_financial_data(Path(args.input)))
    text = json.dumps(result, indent=args.indent)

    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    else:
        print(text)


if __name__ == "__main__":
    main()
