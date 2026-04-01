import { Request, Response, NextFunction } from "express";

// Simple in-memory rate limiter
interface RateLimitEntry {
  count: number;
  windowStart: number;
}

const rateLimitMap = new Map<string, RateLimitEntry>();

// Cleanup old entries every 5 minutes
setInterval(() => {
  const fiveMinutesAgo = Date.now() - 5 * 60 * 1000;
  for (const [ip, entry] of rateLimitMap) {
    if (entry.windowStart < fiveMinutesAgo) {
      rateLimitMap.delete(ip);
    }
  }
}, 5 * 60 * 1000);

export function rateLimiter(
  maxRequests: number = 30, 
  windowMs: number = 60 * 1000 // 1 minute window
) {
  return (req: Request, res: Response, next: NextFunction) => {
    const ip = req.ip || req.connection.remoteAddress || 'unknown';
    const now = Date.now();
    
    let entry = rateLimitMap.get(ip);
    
    // Reset window if expired
    if (!entry || now - entry.windowStart > windowMs) {
      entry = { count: 0, windowStart: now };
      rateLimitMap.set(ip, entry);
    }
    
    entry.count++;
    
    if (entry.count > maxRequests) {
      return res.status(429).json({
        error: "Rate limit exceeded",
        hint: `Maximum ${maxRequests} requests per ${windowMs/1000} seconds`,
        retryAfter: Math.ceil((entry.windowStart + windowMs - now) / 1000)
      });
    }
    
    // Add rate limit headers
    res.setHeader('X-RateLimit-Limit', maxRequests);
    res.setHeader('X-RateLimit-Remaining', maxRequests - entry.count);
    res.setHeader('X-RateLimit-Reset', Math.ceil((entry.windowStart + windowMs) / 1000));
    
    next();
  };
}

// Strict rate limiter for admin operations
export const strictRateLimit = rateLimiter(10, 60 * 1000); // 10 requests per minute
export const standardRateLimit = rateLimiter(30, 60 * 1000); // 30 requests per minute