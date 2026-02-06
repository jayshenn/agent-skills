---
name: investment-target-analysis
description: Build institutional-style equity research outputs for stocks or ETFs by combining financial statement ratios, valuation scenarios, trend signals, risk discipline checks, and optional Tavily news intelligence. Use when users ask for buy/hold/sell reasoning, price targets, catalyst/risk analysis, or detailed investment-target reports.
---

# Investment Target Analysis

Keep this skill lightweight and script-first for repeatable analysis.

## MVP Workflow
1. Prepare input data (financials, price series, valuation assumptions).
   - ETF path: prefer `scripts/fetch_etf_data.py` to auto-generate `prices.json`, `etf_financial_data.json`, `etf_profile.json`, and optional `analysis_input.json` scaffold.
2. Run `scripts/calculate_ratios.py` for core ratio calculation.
3. Run `scripts/interpret_ratios.py` for benchmark-aware interpretation.
4. Run `scripts/analyze_trend_signals.py` for MA/MACD/RSI and discipline checks.
5. Optionally run `scripts/fetch_news_intel.py` (Tavily) for external intelligence.
6. Run `scripts/build_equity_report.py` to generate JSON + Markdown outputs.

## Modes
- `standard`: core report sections only.
- `detailed`: includes enhanced intelligence section (options flow, insider activity, sector notes, ESG notes if available).

## Required Inputs
- `ticker`
- analysis date
- `asset_type` (`equity` or `etf`, default `equity`)
- for `equity`: at least one period of financial statement values
- for `etf`: `etf_data` metrics (expense ratio, tracking error, liquidity, return/risk, concentration), either manually prepared or generated via `scripts/fetch_etf_data.py`
- price series (close, optional volume)
- valuation scenarios (`bull`, `base`, `bear`)

## Environment Variables
- `TAVILY_API_KEY` (optional): required only for `scripts/fetch_news_intel.py`.
- `PYTHON_BIN` (optional): preferred Python executable for all scripts. If unset, commands fall back to current environment `python3`.
- Never store API keys in `SKILL.md` or committed files.

## Python Runtime
- Use `${PYTHON_BIN:-python3}` in commands so users do not need extra setup.
- Prefer the interpreter from active virtualenv or local shell PATH.
- Minimum supported version: Python 3.9.

## Output Contract
- Structured JSON schema: `references/output-schema.md`
- Human-readable report format: `references/output-template.md`
- Risk discipline rules: `references/risk-discipline.md`
- Data source and confidence rules: `references/data-sources.md`
- Financial ratio definitions: `references/ratios-and-valuation.md`
- Legal language: `references/disclaimer.md`

## Guardrails
- Keep accounting/time basis consistent (TTM vs annual, GAAP vs non-GAAP).
- Label unavailable live data as `unverified` and reduce confidence.
- Include invalidation conditions for every recommendation.
