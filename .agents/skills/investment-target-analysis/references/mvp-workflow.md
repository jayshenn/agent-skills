# MVP Workflow

## 0. Python Runtime
- Commands use `${PYTHON_BIN:-python3}` by default.
- If `PYTHON_BIN` is already set in user environment, it will be used automatically.
- Optional check: `${PYTHON_BIN:-python3} --version`

## 1. Prepare Input JSON
Create an analysis input file with ticker, `asset_type`, market price, valuation scenarios, and optional catalysts/risks.
- `asset_type=equity`: provide financial statements (`income_statement`, `balance_sheet`, `market_data`).
- `asset_type=etf`: provide `etf_data` and optional `etf_profile`.

### ETF Quick Start (Auto Fetch)
Use the reusable fetcher script to reduce manual `etf_data` preparation:

```bash
${PYTHON_BIN:-python3} scripts/fetch_etf_data.py \
  --ticker SPY \
  --company "SPDR S&P 500 ETF Trust" \
  --output-dir ./data/etf \
  --mode standard
```

Generated files:
- `./data/etf/prices.json` (price series for trend analysis)
- `./data/etf/etf_financial_data.json` (`asset_type=etf` + `etf_data` for ratio calculation)
- `./data/etf/etf_profile.json` (benchmark/issuer/holdings/sector weights)
- `./data/etf/analysis_input.json` (optional report input scaffold, unless `--skip-analysis-input`)

## 2. Calculate and Interpret Ratios
```bash
${PYTHON_BIN:-python3} scripts/calculate_ratios.py \
  --input ./data/financial_data.json \
  --output ./out/ratio_results.json

${PYTHON_BIN:-python3} scripts/interpret_ratios.py \
  --input ./out/ratio_results.json \
  --industry technology \
  --output ./out/ratio_interpretation.json

# ETF mode with auto-fetched input
${PYTHON_BIN:-python3} scripts/calculate_ratios.py \
  --input ./data/etf/etf_financial_data.json \
  --output ./out/ratio_results.json

${PYTHON_BIN:-python3} scripts/interpret_ratios.py \
  --input ./out/ratio_results.json \
  --industry etf \
  --output ./out/ratio_interpretation.json
```

## 3. Analyze Trend Signals
```bash
${PYTHON_BIN:-python3} scripts/analyze_trend_signals.py --input ./data/prices.json --output ./out/trend.json

# ETF auto-fetch output
${PYTHON_BIN:-python3} scripts/analyze_trend_signals.py --input ./data/etf/prices.json --output ./out/trend.json
```

## 4. Fetch Optional Tavily Intelligence
```bash
export TAVILY_API_KEY="..."
${PYTHON_BIN:-python3} scripts/fetch_news_intel.py --ticker AAPL --company Apple --mode detailed --output ./out/intel.json
```

## 5. Build Final Report (JSON + Markdown)
```bash
${PYTHON_BIN:-python3} scripts/build_equity_report.py \
  --input ./data/analysis_input.json \
  --json-output ./out/report.json \
  --md-output ./out/report.md

# ETF auto-fetch scaffold
${PYTHON_BIN:-python3} scripts/build_equity_report.py \
  --input ./data/etf/analysis_input.json \
  --json-output ./out/report.json \
  --md-output ./out/report.md
```

## 6. Validate Output
- JSON should follow `references/output-schema.md`.
- Markdown should follow `references/output-template.md`.
- Recommendation must include invalidation conditions.
