# Data Sources and API Key Handling

## Priority
1. Company filings and official reports.
2. Market prices and volume series.
3. Consensus/analyst expectations.
4. News and event intelligence.

## ETF Data Ingestion (Reusable Script)
- Script: `scripts/fetch_etf_data.py`
- Primary endpoints (Yahoo Finance public APIs):
  - Market prices and volume: `chart` endpoint (`query1.finance.yahoo.com/v8/finance/chart/...`)
  - ETF profile/fee/AUM/liquidity: `quoteSummary` modules `price,summaryDetail,defaultKeyStatistics,fundProfile`
  - Holdings and sector weights: `quoteSummary` module `topHoldings` (`holdings`, `sectorWeightings`)
- Output files:
  - `prices.json`
  - `etf_financial_data.json`
  - `etf_profile.json`
  - optional `analysis_input.json`
- Offline reproducibility:
  - Use `--chart-json`, `--summary-json`, `--benchmark-chart-json` with local payloads to avoid live-network dependency.

## Tavily Integration (Optional)
- Script: `scripts/fetch_news_intel.py`
- Environment variable: `TAVILY_API_KEY`
- Do not hardcode API keys in code, markdown, or committed config files.
- Template file: repo root `.env.example`

## Example
```bash
export TAVILY_API_KEY="your_key_here"
python3 scripts/fetch_news_intel.py --ticker AAPL --company Apple --mode detailed
```

## Confidence Downgrade Rules
- If ETF `topHoldings` or `sectorWeightings` is missing, keep report in reduced-confidence mode and list fields under `unverified_assumptions`.
- If ETF benchmark time series is unavailable, keep `tracking_error`/`beta` as `null` and mark as unverified.
- If no external intelligence is available, keep report in reduced-confidence mode.
- If valuation assumptions are incomplete, label target price as scenario-only.
