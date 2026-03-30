NEWS_AGENT_CONFIGURATION = {
    "aggregator": {
        "name": "aggregator",
        "desc": "Collects the latest news articles from the last 24 hours via Elasticsearch",
        "desc_for_llm": (
            "Fetches market news from the Elasticsearch datasource using the get_markets_news tool."
            "Retrieves articles from the last 24 hours across all exchanges. "
            "Outputs the raw collected articles as structured data for downstream processing."
        ),
        "is_optional": False,
    },
    "reporter": {
        "name": "reporter",
        "desc": "Groups articles by topic, writes 4-paragraph summaries, and produces the final investor briefing",
        "desc_for_llm": (
            "Senior financial journalist that performs three phases in a single pass: "
            "(1) groups articles by similarity and creates compelling topic headlines, "
            "(2) writes exactly 4 paragraphs per topic (what happened, why it matters, market context, what to watch), "
            "(3) formats the final polished Markdown investor briefing report."
        ),
        "is_optional": False,
    },
}

NEWS_AGENTS = list(NEWS_AGENT_CONFIGURATION.keys())
