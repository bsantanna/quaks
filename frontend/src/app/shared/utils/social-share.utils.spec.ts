import {buildShareAction} from './social-share.utils';

describe('social-share utils', () => {
  const payload = {
    url: 'https://quaks.ai/markets/stocks/AAPL',
    title: 'Apple update',
  };

  it('builds popup urls for social platforms', () => {
    expect(buildShareAction('facebook', payload)).toEqual({
      kind: 'popup',
      targetUrl: 'https://www.facebook.com/sharer.php?u=https%3A%2F%2Fquaks.ai%2Fmarkets%2Fstocks%2FAAPL',
    });
    expect(buildShareAction('x', payload)).toEqual({
      kind: 'popup',
      targetUrl: 'https://twitter.com/intent/tweet?url=https%3A%2F%2Fquaks.ai%2Fmarkets%2Fstocks%2FAAPL&text=Apple%20update',
    });
    expect(buildShareAction('whatsapp', payload)).toEqual({
      kind: 'popup',
      targetUrl: 'https://api.whatsapp.com/send?text=Apple%20update%20https%3A%2F%2Fquaks.ai%2Fmarkets%2Fstocks%2FAAPL',
    });
  });

  it('builds popup urls for remaining web share targets', () => {
    expect(buildShareAction('threads', payload)).toEqual({
      kind: 'popup',
      targetUrl: 'https://www.threads.net/intent/post?text=Apple%20update&url=https%3A%2F%2Fquaks.ai%2Fmarkets%2Fstocks%2FAAPL',
    });
    expect(buildShareAction('linkedin', payload)).toEqual({
      kind: 'popup',
      targetUrl: 'https://www.linkedin.com/shareArticle?url=https%3A%2F%2Fquaks.ai%2Fmarkets%2Fstocks%2FAAPL&title=Apple%20update',
    });
    expect(buildShareAction('reddit', payload)).toEqual({
      kind: 'popup',
      targetUrl: 'https://reddit.com/submit?url=https%3A%2F%2Fquaks.ai%2Fmarkets%2Fstocks%2FAAPL&title=Apple%20update',
    });
  });

  it('builds redirect and clipboard actions', () => {
    expect(buildShareAction('email', payload)).toEqual({
      kind: 'redirect',
      targetUrl: 'mailto:?subject=Quaks&body=Apple%20update%20https%3A%2F%2Fquaks.ai%2Fmarkets%2Fstocks%2FAAPL',
    });
    expect(buildShareAction('copy', payload)).toEqual({
      kind: 'clipboard',
      text: 'https://quaks.ai/markets/stocks/AAPL',
    });
  });

  it('returns null for unknown platforms', () => {
    expect(buildShareAction('mastodon' as never, payload)).toBeNull();
  });
});
