import {
  applyInsightsAvatarFallback,
  ensureInsightsPrintStyle,
  formatInsightsDate,
  getInsightsAgentAvatarSrc,
  INSIGHTS_PRINT_STYLE_CONTENT,
  INSIGHTS_PRINT_STYLE_ID,
  linkifyTickersInHtml,
  removeInsightsPrintStyle,
  sanitizeInsightsReportHtml,
  sanitizeMarketsNewsHtml,
  structurePlainTextReport,
} from './content-format.utils';

describe('content-format utils', () => {
  it('builds agent avatars and falls back to the base avatar', () => {
    expect(getInsightsAgentAvatarSrc('/macro_research')).toBe('/svg/insights-agent_quaks-macro-research.svg');
    expect(getInsightsAgentAvatarSrc(null)).toBe('/svg/insights-agent_base.svg');

    const image = document.createElement('img');
    image.src = 'https://quaks.ai/svg/insights-agent_quaks-macro-research.svg';
    applyInsightsAvatarFallback(image);
    expect(image.src.endsWith('/svg/insights-agent_base.svg')).toBe(true);
  });

  it('formats dates through the provided formatter', () => {
    expect(formatInsightsDate('2026-04-09T12:30:00Z', value => `fmt:${value}`)).toBe('fmt:2026-04-09');
    expect(formatInsightsDate('', value => value)).toBe('--');
  });

  it('structures plain text reports into headings and paragraphs', () => {
    const html = structurePlainTextReport('Headline\nShort lede\nSECTION TITLE\nBody line.');
    expect(html).toContain('<h2>Headline</h2>');
    expect(html).toContain('<p class="report-lede"><em>Short lede</em></p>');
    expect(html).toContain('<h3>SECTION TITLE</h3>');
    expect(html).toContain('<p>Body line.</p>');
  });

  it('linkifies known tickers in html', () => {
    const html = linkifyTickersInHtml('Move in (AAPL) and (TSLA)', new Set(['AAPL']));
    expect(html).toContain('href="/markets/stocks/AAPL"');
    expect(html).toContain('(TSLA)');
  });

  it('sanitizes insights report html and structures plain text content', () => {
    const html = sanitizeInsightsReportHtml(
      '<script>alert(1)</script>Title<br>Summary<br>(AAPL)',
      new Set(['AAPL']),
    );

    expect(html).not.toContain('<script');
    expect(html).toContain('ticker-link');
    expect(html).toContain('<h2>Title</h2>');
  });

  it('adds print styles once and removes them cleanly', () => {
    removeInsightsPrintStyle(document);
    ensureInsightsPrintStyle(document);
    ensureInsightsPrintStyle(document);

    const styles = document.querySelectorAll(`#${INSIGHTS_PRINT_STYLE_ID}`);
    expect(styles).toHaveLength(1);
    expect(styles[0].textContent).toBe(INSIGHTS_PRINT_STYLE_CONTENT);

    removeInsightsPrintStyle(document);
    expect(document.getElementById(INSIGHTS_PRINT_STYLE_ID)).toBeNull();
  });

  it('rewrites ticker links matched by anchor text when href has no /quote/ path', () => {
    const clean = sanitizeMarketsNewsHtml(
      '<a href="https://example.com/other">MSFT</a>',
      new Set(['MSFT']),
      document,
    );
    expect(clean).toContain('href="/markets/stocks/MSFT"');
  });

  it('does not rewrite links when neither href nor text match a known ticker', () => {
    const clean = sanitizeMarketsNewsHtml(
      '<a href="https://example.com/page">click here</a>',
      new Set(['AAPL']),
      document,
    );
    expect(clean).toContain('href="https://example.com/page"');
    expect(clean).not.toContain('/markets/stocks/');
  });

  it('sanitizes markets news html and rewrites known ticker links', () => {
    const clean = sanitizeMarketsNewsHtml(
      [
        '<script>alert(1)</script>',
        '<a href="https://www.benzinga.com/quote/AAPL" onclick="hack()">AAPL</a>',
        '<a href="javascript:alert(1)">bad</a>',
        '<button>remove</button>',
      ].join(''),
      new Set(['AAPL']),
      document,
    );

    expect(clean).toContain('href="/markets/stocks/AAPL"');
    expect(clean).not.toContain('<script');
    expect(clean).not.toContain('<button');
    expect(clean).not.toContain('onclick=');
    expect(clean).not.toContain('javascript:');
  });
});
