NEWS_AGENT_CONFIGURATION = {
    "aggregator": {
        "name": "aggregator",
        "desc": "Collects the latest news articles from the last 24 hours via Elasticsearch",
        "desc_for_llm": (
            "Fetches market news from the Elasticsearch datasource using the fetch_latest_news tool. "
            "Retrieves articles from the last 24 hours across all exchanges. "
            "Outputs the raw collected articles as structured data for downstream processing."
        ),
        "is_optional": False,
    },
    "headlines_creator": {
        "name": "headlines_creator",
        "desc": "Groups news by similarity and creates attention-capturing topic headlines",
        "desc_for_llm": (
            "Analyzes the collected news articles and groups them by similarity of subject, "
            "sector, and industry. Creates attention-capturing headlines or topic names for each group. "
            "Outputs a structured list of topics, each with a headline and the associated articles."
        ),
        "is_optional": False,
    },
    "news_writer": {
        "name": "news_writer",
        "desc": "Writes professional summaries for each topic group",
        "desc_for_llm": (
            "Takes the grouped and categorized topics and writes a concise, copywriter-quality summary "
            "of exactly 3 paragraphs per topic. The writing should be engaging, informative, and help "
            "investors quickly understand the key events and their potential impact."
        ),
        "is_optional": False,
    },
    "editor": {
        "name": "editor",
        "desc": "Formats the final investor briefing report",
        "desc_for_llm": (
            "Head editor that takes the work of all other agents and formats it into a polished, "
            "professional investor briefing report in Markdown. Ensures consistency, readability, "
            "and that the report helps investors get in context and make informed decisions."
        ),
        "is_optional": False,
    },
}

NEWS_AGENTS = list(NEWS_AGENT_CONFIGURATION.keys())
