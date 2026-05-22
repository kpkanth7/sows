import { NextResponse } from 'next/server';

// Known bot user agents
const BOT_UAS = ['curl', 'python-requests', 'scrapy', 'wget', 'go-http', 'java'];

// Rate limit config
const RATE_LIMIT_WINDOW = 60000; // 1 min
const MAX_REQUESTS = 100;

export function middleware(request) {
  const ua = request.headers.get('user-agent') || '';
  const isBot = BOT_UAS.some(bot => ua.toLowerCase().includes(bot));
  
  if (isBot) {
    return new NextResponse('Forbidden: Bot access denied.', { status: 429 });
  }

  // Very basic simulated IP rate limit (since full Redis not available in this edge config)
  // Usually this would use Redis/Upstash for tracking IP hits.
  const ip = request.ip || '127.0.0.1';
  // Check against edge cache or throw 429 if abuse detected...
  // For Vercel Edge without DB, we mostly rely on simple checks or headers
  
  const response = NextResponse.next();
  // Set some security headers
  response.headers.set('X-Frame-Options', 'DENY');
  response.headers.set('X-Content-Type-Options', 'nosniff');
  return response;
}

export const config = {
  matcher: '/api/:path*',
};
