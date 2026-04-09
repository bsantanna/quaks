export type SharePlatform =
  | 'facebook'
  | 'x'
  | 'whatsapp'
  | 'threads'
  | 'linkedin'
  | 'reddit'
  | 'email'
  | 'copy';

export interface SharePayload {
  url: string;
  title: string;
}

export type ShareAction =
  | {kind: 'popup'; targetUrl: string}
  | {kind: 'redirect'; targetUrl: string}
  | {kind: 'clipboard'; text: string};

export function buildShareAction(platform: SharePlatform, payload: SharePayload): ShareAction | null {
  const urlEncoded = encodeURIComponent(payload.url);
  const text = encodeURIComponent(payload.title);

  switch (platform) {
    case 'facebook':
      return {kind: 'popup', targetUrl: `https://www.facebook.com/sharer.php?u=${urlEncoded}`};
    case 'x':
      return {kind: 'popup', targetUrl: `https://twitter.com/intent/tweet?url=${urlEncoded}&text=${text}`};
    case 'whatsapp':
      return {kind: 'popup', targetUrl: `https://api.whatsapp.com/send?text=${text}%20${urlEncoded}`};
    case 'threads':
      return {kind: 'popup', targetUrl: `https://www.threads.net/intent/post?text=${text}&url=${urlEncoded}`};
    case 'linkedin':
      return {kind: 'popup', targetUrl: `https://www.linkedin.com/shareArticle?url=${urlEncoded}&title=${text}`};
    case 'reddit':
      return {kind: 'popup', targetUrl: `https://reddit.com/submit?url=${urlEncoded}&title=${text}`};
    case 'email':
      return {kind: 'redirect', targetUrl: `mailto:?subject=Quaks&body=${text}%20${urlEncoded}`};
    case 'copy':
      return {kind: 'clipboard', text: payload.url};
    default:
      return null;
  }
}
