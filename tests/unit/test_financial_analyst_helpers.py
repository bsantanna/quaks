from app.services.agent_types.quaks.insights.financial_analyst.v1.agent import (
    QuaksFinancialAnalystV1Agent,
    _NOT_CLASSIFIED,
    _normalize_sector,
    _build_sector_table,
    _build_region_table,
    SUPERSECTOR_SECTORS,
    REGION_SUBREGIONS,
)


def test_not_classified_constant():
    assert _NOT_CLASSIFIED == "Not Classified"


def test_normalize_sector_unknown():
    assert _normalize_sector("UnknownIndustry123") == _NOT_CLASSIFIED


def test_normalize_sector_known():
    assert _normalize_sector("Technology") == "Technology"


def test_format_style_text():
    grid = {(s, v): 0.0 for s in ("Large", "Mid", "Small") for v in ("Value", "Blend", "Growth")}
    grid[("Large", "Growth")] = 60.0
    grid[("Mid", "Value")] = 40.0
    result = QuaksFinancialAnalystV1Agent._format_style_text(grid)
    assert "Large/Growth: 60%" in result
    assert "Mid/Value: 40%" in result
    assert "Small" not in result


def test_format_style_text_empty():
    grid = {(s, v): 0.0 for s in ("Large", "Mid", "Small") for v in ("Value", "Blend", "Growth")}
    result = QuaksFinancialAnalystV1Agent._format_style_text(grid)
    assert result == "Style: "


def test_format_weighted_groups_text():
    groups = {"GroupA": ["X", "Y"], "GroupB": ["Z"]}
    weights = {"X": 30.0, "Y": 20.0, "Z": 50.0}
    result = QuaksFinancialAnalystV1Agent._format_weighted_groups_text("Test", groups, weights)
    assert "GroupA 50%" in result
    assert "X 30%" in result
    assert "GroupB 50%" in result


def test_format_weighted_groups_text_empty():
    groups = {"GroupA": ["X"]}
    weights = {}
    result = QuaksFinancialAnalystV1Agent._format_weighted_groups_text("Label", groups, weights)
    assert result == "Label: "


def test_build_sector_table_with_not_classified():
    sector_wt = {_NOT_CLASSIFIED: 15.0}
    rows = _build_sector_table(sector_wt)
    html = "\n".join(rows)
    assert _NOT_CLASSIFIED in html
    assert "15.00" in html


def test_build_region_table_with_not_classified():
    subregion_wt = {_NOT_CLASSIFIED: 10.0}
    rows = _build_region_table(subregion_wt)
    html = "\n".join(rows)
    assert _NOT_CLASSIFIED in html
    assert "10.00" in html
