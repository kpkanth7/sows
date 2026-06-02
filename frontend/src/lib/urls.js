export function safeUrl(url) {
  if (!url) return '#';

  try {
    const parsed = new URL(url);
    return parsed.protocol === 'http:' || parsed.protocol === 'https:' ? parsed.href : '#';
  } catch {
    return '#';
  }
}
