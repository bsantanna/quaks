FINANCIAL_ANALYST_V1_AGENT_CONFIGURATION = {
    "data_collector": {
        "name": "data_collector",
        "desc": "Fetches company profiles, technical indicators, price stats, and news from Elasticsearch",
        "desc_for_llm": (
            "Collects all financial data for the requested ticker(s) using tools: "
            "company profile (metadata, multiples, analyst ratings), "
            "price stats (latest close, variance), "
            "technical indicators (RSI, MACD, EMA, ADX), "
            "and recent news headlines. Outputs structured JSON data for downstream analysts."
        ),
        "is_optional": False,
    },
    "fundamental_analyst": {
        "name": "fundamental_analyst",
        "desc": "Evaluates intrinsic value via multiples, profitability, balance sheet health, and earnings estimates",
        "desc_for_llm": (
            "Senior fundamental analyst performing Chain-of-Thought valuation analysis: "
            "comparable multiples (P/E, EV/EBITDA, P/B, PEG), profitability metrics "
            "(margins, ROE, ROA), balance sheet quality (leverage, liquidity), "
            "earnings growth, analyst consensus. Produces a BUY/HOLD/SELL recommendation "
            "with a conviction score (1-10) for each ticker."
        ),
        "is_optional": False,
    },
    "technical_analyst": {
        "name": "technical_analyst",
        "desc": "Evaluates price action, momentum, volume, and trend signals from technical indicators",
        "desc_for_llm": (
            "Senior technical analyst performing multi-indicator confluence analysis: "
            "trend identification (ADX, EMA crossover, 50/200 MA), "
            "momentum confirmation (RSI, MACD), "
            "price positioning (52-week range, variance). "
            "Produces a BUY/HOLD/SELL recommendation with a conviction score (1-10) for each ticker."
        ),
        "is_optional": False,
    },
    "consensus_reporter": {
        "name": "consensus_reporter",
        "desc": "Tallies fundamental and technical votes, then formats the final HTML report",
        "desc_for_llm": (
            "Chief Investment Officer who reads both analyst recommendations, "
            "applies voting rules (agreement = +1 bonus, disagreement = hedged HOLD with -1 penalty), "
            "and produces a polished HTML report with per-ticker verdicts, summaries, and key metrics."
        ),
        "is_optional": False,
    },
    "portfolio_xray": {
        "name": "portfolio_xray",
        "desc": "Generates a Morningstar-style Portfolio X-Ray with sector, region, style, and stats breakdown",
        "desc_for_llm": (
            "Deterministic Portfolio X-Ray generator that queries stock metadata and computes "
            "equal-weight portfolio aggregations: asset allocation, investment style box (size x value/growth), "
            "sector breakdown (Cyclical/Sensitive/Defensive), world region exposure, "
            "weighted-average stock stats (P/E, P/B, EV/EBITDA), and top holdings. "
            "Produces structured HTML output. No LLM required."
        ),
        "is_optional": False,
    },
}

FINANCIAL_ANALYST_V1_AGENTS = list(FINANCIAL_ANALYST_V1_AGENT_CONFIGURATION.keys())
