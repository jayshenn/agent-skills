# Output Schema (MVP)

Use this JSON structure for machine-readable output.

```json
{
  "metadata": {
    "ticker": "AAPL",
    "company": "Apple",
    "asset_type": "equity",
    "analysis_date": "2026-02-06",
    "mode": "standard"
  },
  "executive_summary": {
    "rating": "BUY",
    "current_price": 200.0,
    "weighted_target_price": 224.5,
    "implied_upside_pct": 12.25,
    "conviction": "Medium",
    "thesis": "..."
  },
  "fundamental_analysis": {
    "asset_type": "equity",
    "summary": "...",
    "ratio_results": {},
    "ratio_interpretation": {},
    "etf_analysis": {}
  },
  "catalyst_analysis": {
    "near_term": [],
    "mid_term": []
  },
  "valuation": {
    "scenarios": {
      "bull": {"target": 250.0, "probability": 0.25},
      "base": {"target": 225.0, "probability": 0.50},
      "bear": {"target": 180.0, "probability": 0.25}
    },
    "weighted_target_price": 220.0
  },
  "risk_assessment": {
    "risks": [],
    "position_sizing": "1%-5%",
    "invalidation": "..."
  },
  "technical_context": {
    "trend_status": "bullish",
    "metrics": {},
    "action_checklist": []
  },
  "enhanced_intelligence": {},
  "recommendation": {
    "decision_type": "buy",
    "rating": "BUY",
    "confidence": "medium",
    "valuation_decision": "buy",
    "trend_decision": "hold",
    "trend_score": 72,
    "next_checkpoints": []
  },
  "data_quality": {
    "verified_sources": [],
    "unverified_assumptions": [],
    "ratio_input_quality": {},
    "confidence_impact": []
  },
  "disclaimer": "Educational/research only. Not financial advice."
}
```
