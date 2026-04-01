/**
 * JWT Authentication Manager
 * Modular authentication system with session management
 */

import jwt from 'jsonwebtoken';
import { Request, Response, NextFunction } from 'express';

interface UserPayload {
  user_id: string;
  consciousness_level: number;
  agent_type?: string;
  permissions: string[];
}

interface TokenOptions {
  expiresIn?: string;
  consciousness_level?: number;
  permissions?: string[];
}

export class JWTManager {
  private secretKey: string;
  private refreshSecret: string;
  private defaultExpiry: string = '1h';
  private refreshExpiry: string = '7d';

  constructor(secretKey?: string, refreshSecret?: string) {
    this.secretKey = secretKey || process.env.JWT_SECRET || 'consciousness-jwt-secret';
    this.refreshSecret = refreshSecret || process.env.JWT_REFRESH_SECRET || 'consciousness-refresh-secret';
  }

  /**
   * Generate access token with consciousness level
   */
  generateAccessToken(payload: UserPayload, options: TokenOptions = {}): string {
    const tokenPayload = {
      ...payload,
      consciousness_level: options.consciousness_level || payload.consciousness_level,
      permissions: options.permissions || payload.permissions,
      type: 'access',
      iat: Date.now()
    };

    return jwt.sign(tokenPayload, this.secretKey, {
      expiresIn: options.expiresIn || this.defaultExpiry,
      algorithm: 'HS256'
    });
  }

  /**
   * Generate refresh token
   */
  generateRefreshToken(userId: string): string {
    return jwt.sign(
      { user_id: userId, type: 'refresh', iat: Date.now() },
      this.refreshSecret,
      { expiresIn: this.refreshExpiry, algorithm: 'HS256' }
    );
  }

  /**
   * Verify and decode access token
   */
  verifyAccessToken(token: string): UserPayload | null {
    try {
      const decoded = jwt.verify(token, this.secretKey) as any;
      if (decoded.type !== 'access') return null;
      return decoded as UserPayload;
    } catch (error) {
      return null;
    }
  }

  /**
   * Verify refresh token
   */
  verifyRefreshToken(token: string): { user_id: string } | null {
    try {
      const decoded = jwt.verify(token, this.refreshSecret) as any;
      if (decoded.type !== 'refresh') return null;
      return { user_id: decoded.user_id };
    } catch (error) {
      return null;
    }
  }

  /**
   * Middleware for protecting routes
   */
  requireAuth(minConsciousnessLevel: number = 0) {
    return (req: Request & { user?: UserPayload }, res: Response, next: NextFunction) => {
      const token = this.extractToken(req);
      if (!token) {
        return res.status(401).json({ error: 'No token provided' });
      }

      const user = this.verifyAccessToken(token);
      if (!user) {
        return res.status(401).json({ error: 'Invalid token' });
      }

      if (user.consciousness_level < minConsciousnessLevel) {
        return res.status(403).json({ 
          error: 'Insufficient consciousness level',
          required: minConsciousnessLevel,
          current: user.consciousness_level
        });
      }

      req.user = user;
      next();
    };
  }

  /**
   * Middleware for checking permissions
   */
  requirePermission(permission: string) {
    return (req: Request & { user?: UserPayload }, res: Response, next: NextFunction) => {
      if (!req.user) {
        return res.status(401).json({ error: 'Authentication required' });
      }

      if (!req.user.permissions.includes(permission) && !req.user.permissions.includes('admin')) {
        return res.status(403).json({ 
          error: 'Insufficient permissions',
          required: permission,
          current: req.user.permissions
        });
      }

      next();
    };
  }

  /**
   * Extract token from request headers
   */
  private extractToken(req: Request): string | null {
    const authHeader = req.headers.authorization;
    if (authHeader && authHeader.startsWith('Bearer ')) {
      return authHeader.substring(7);
    }
    return null;
  }

  /**
   * Create token pair (access + refresh)
   */
  createTokenPair(payload: UserPayload, options: TokenOptions = {}): {
    accessToken: string;
    refreshToken: string;
    expiresIn: string;
  } {
    const accessToken = this.generateAccessToken(payload, options);
    const refreshToken = this.generateRefreshToken(payload.user_id);
    
    return {
      accessToken,
      refreshToken,
      expiresIn: options.expiresIn || this.defaultExpiry
    };
  }

  /**
   * Refresh access token using refresh token
   */
  refreshAccessToken(refreshToken: string, currentUser: UserPayload): string | null {
    const decoded = this.verifyRefreshToken(refreshToken);
    if (!decoded || decoded.user_id !== currentUser.user_id) {
      return null;
    }

    return this.generateAccessToken(currentUser);
  }
}

export default JWTManager;