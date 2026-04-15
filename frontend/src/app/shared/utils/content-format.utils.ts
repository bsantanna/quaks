const BASE_AVATAR_SRC = '/svg/insights-agent_base.svg';
export const INSIGHTS_PRINT_STYLE_ID = 'quaks-print-style';
export const INSIGHTS_PRINT_STYLE_CONTENT = `
  @media print {
    app-navigation-header,
    app-navigation-footer,
    .print-hide { display: none !important; }
    .print-cover { display: block !important; }
    .print-cover-summary { display: none !important; }
    .briefing-card { display: none !important; }
    .briefing-report { border: none !important; }
    @page {
      margin: 2cm 1.5cm 2.5cm;
      size: A4;
    }
    .print-logo {
      display: block !important;
      position: fixed;
      bottom: 0;
      right: 0;
      width: 48px;
      height: 48px;
      opacity: 0.6;
    }
  }
`;

export function getInsightsAgentAvatarSrc(skillName?: string | null): string {
  if (!skillName) return BASE_AVATAR_SRC;
  const normalized = skillName.replace(/^\//, '').replaceAll('_', '-');
  return `/svg/insights-agent_quaks-${normalized}.svg`;
}

export function applyInsightsAvatarFallback(image: HTMLImageElement): void {
  if (!image.src.endsWith('insights-agent_base.svg')) {
    image.src = BASE_AVATAR_SRC;
  }
}

export function formatInsightsDate(dateStr: string, formatDate: (value: string) => string): string {
  if (!dateStr) return '--';
  return formatDate(dateStr.substring(0, 10));
}

export function sanitizeInsightsReportHtml(html: string | null, tickers: Set<string>): string | null {
  if (!html) return html;

  let clean = html
    .replaceAll(/<script[\s\S]*?<\/script>/gi, '')
    .replaceAll(/<script[\s\S]*?\/>/gi, '')
    .replaceAll(/\bon\w+\s*=\s*"[^"]*"/gi, '')
    .replaceAll(/\bon\w+\s*=\s*'[^']*'/gi, '');

  if (!/<(h[1-6]|p|div|ul|ol|table|section|article)\b/i.test(clean)) {
    clean = structurePlainTextReport(clean);
  }

  return linkifyTickersInHtml(clean, tickers);
}

export function structurePlainTextReport(text: string): string {
  const raw = stripHtmlTags(text.replaceAll(/<br\s*\/?>/gi, '\n'));
  const lines = raw.split(/\n/).map(line => line.trim()).filter(Boolean);
  if (lines.length === 0) return '';

  const parts: string[] = [`<h2>${lines[0]}</h2>`];
  let start = 1;

  if (lines.length > 2 && lines[1].length < 200) {
    parts.push(`<p class="report-lede"><em>${lines[1]}</em></p>`);
    start = 2;
  }

  for (let i = start; i < lines.length; i++) {
    const line = lines[i];
    const isHeader = line.length < 100
      && !line.endsWith('.')
      && !line.endsWith(',')
      && !line.endsWith(':')
      && !/\d%/.test(line)
      && (
        line === line.toUpperCase()
        || (/^[A-Z]/.test(line) && !line.includes('.') && /[A-Z]/.test(line.substring(1)))
        || line.includes('—')
        || line.includes(' — ')
      );

    parts.push(isHeader ? `<h3>${line}</h3>` : `<p>${line}</p>`);
  }

  return parts.join('\n');
}

function stripHtmlTags(text: string): string {
  let result = '';
  let inTag = false;
  for (const ch of text) {
    if (ch === '<') inTag = true;
    else if (ch === '>' && inTag) inTag = false;
    else if (!inTag) result += ch;
  }
  return result;
}

export function linkifyTickersInHtml(html: string, tickers: Set<string>): string {
  if (tickers.size === 0) return html;

  return html.replaceAll(
    /\(([A-Z]{1,5})\)/g,
    (match, ticker) => tickers.has(ticker)
      ? `(<a href="/markets/stocks/${ticker}" class="ticker-link">${ticker}</a>)`
      : match
  );
}

export function ensureInsightsPrintStyle(doc: Document): void {
  if (doc.getElementById(INSIGHTS_PRINT_STYLE_ID)) return;

  const style = doc.createElement('style');
  style.id = INSIGHTS_PRINT_STYLE_ID;
  style.textContent = INSIGHTS_PRINT_STYLE_CONTENT;
  doc.head.appendChild(style);
}

export function removeInsightsPrintStyle(doc: Document): void {
  doc.getElementById(INSIGHTS_PRINT_STYLE_ID)?.remove();
}

export function sanitizeMarketsNewsHtml(
  htmlContent: string | null | undefined,
  tickers: Set<string>,
  doc: Document,
): string {
  if (!htmlContent) return '';

  const parser = new DOMParser();
  const tempDoc = parser.parseFromString(htmlContent, 'text/html');
  const root = tempDoc.body;

  root.querySelectorAll('script, style, iframe, noscript, object, embed, form, input, button')
    .forEach(el => el.remove());

  root.querySelectorAll('*').forEach(el => {
    for (const attr of Array.from(el.attributes)) {
      if (attr.name.startsWith('on') || attr.name === 'srcdoc') {
        el.removeAttribute(attr.name);
      }
    }

    if (el instanceof HTMLAnchorElement && el.hasAttribute('href')) {
      const href = el.getAttribute('href') ?? '';
      if (href.trim().toLowerCase().startsWith('javascript:')) {
        el.removeAttribute('href');
      }
    }
  });

  root.querySelectorAll('a[href]').forEach(el => {
    const anchor = el as HTMLAnchorElement;
    const href = anchor.getAttribute('href') ?? '';
    const text = (anchor.textContent ?? '').trim();
    const hrefMatch = href.match(/\/quote\/([A-Z]+)$/);
    const tickerFromHref = hrefMatch ? hrefMatch[1] : '';
    const ticker = tickers.has(tickerFromHref) ? tickerFromHref
      : tickers.has(text) ? text
      : '';

    if (ticker) {
      anchor.setAttribute('href', `/markets/stocks/${ticker}`);
    }
  });

  return root.innerHTML;
}
