---
name: investment-asset-analysis
description: Institutional-grade investment asset analysis for US, Hong Kong, and China A-share markets across stocks, ETFs, and funds. Use when users ask for equity research, trading ideas, price targets, valuation scenarios, catalysts, risk assessment, or Goldman-Sachs-style reports similar to claude-equity-research output.
---

# Investment Asset Analysis

## Overview

Deliver institutional-quality investment research using the claude-equity-research framework and output structure. Support US/HK/A-share stocks plus ETFs and mutual funds with market-appropriate metrics, risk framing, and compliance disclaimers.

## Capabilities

Calculate and present:
- Institutional-grade research reports with catalysts, valuation scenarios, and risk assessment
- US, Hong Kong, and China A-share coverage for stocks, ETFs, and mutual funds
- Market-appropriate metrics (AUM/expense ratio for ETFs, NAV/benchmark for funds)
- Technical context, options flow, and insider/institutional activity when available
- Source-cited, date-stamped analysis with required disclaimers

## How to Use

1. Input: Provide a ticker, market, and asset type (stock/ETF/fund).
2. Gather: Use web search for current filings, earnings, holdings, and consensus.
3. Analyze: Adapt metrics by asset type and market conventions.
4. Report: Follow the trading-ideas structure and include the disclaimer.

## Input Format

- Ticker + market:
`AAPL` (US), `0700.HK` (HK), `600519.SS`/`000001.SZ` (A-share), funds often use `.OF`
- Name-only inputs: ask for ticker and market before proceeding
- Optional preferences: timeframe, risk tolerance, currency, report depth (`standard` or `detailed`), output language
- Optional data: text/CSV/JSON summaries of financials or holdings

## Output Format

- Follow the exact section order and headings in `references/trading-ideas.md`
- Keep the same structure for ETFs/funds, but substitute asset-appropriate metrics in each section
- Output language should match the user's current conversation language unless explicitly overridden
- Include scenarios with probability weights and a recommendation summary table
- Always include the disclaimer and cite sources for non-trivial claims

## Example Usage

"生成 AAPL 的机构级研究报告，给出 12 个月价格目标"
"分析 0700.HK，加入期权流与技术面"
"给我 600519.SS 的 bull/base/bear 估值场景"
"分析 ETF QQQ：AUM、费率、跟踪指数、持仓集中度"
"基金 110022.OF 的 NAV 表现与基准比较"

## Scripts

- None. If you add automation later, place scripts under `scripts/` and reference them here.

## Best Practices

1. Confirm ticker, market, and asset type before analysis.
2. Use the latest filings/earnings/holdings data and include dates.
3. Keep metrics consistent with asset type (stocks vs ETFs vs funds).
4. Provide explicit timeframes (YoY/QoQ/12m) and scenario probabilities.
5. Flag missing data and explain assumptions.

## Limitations

- Depends on public data quality and availability.
- Options/insider data may be unavailable for some markets.
- Educational use only; not financial advice.

## References

Use these references as needed:
- `references/trading-ideas.md`: Required output structure and quality standards
- `references/docs/`: Methodology, installation, customization details
- `references/config.example.json`: Default analysis/risk settings to use when user provides no preferences
- `references/examples/`: Example reports (AAPL, HOOD)

If prompt templates are added later, place them under `references/prompts/` and reference them here.
