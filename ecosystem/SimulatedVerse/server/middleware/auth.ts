import { Request, Response, NextFunction } from "express";

export function adminGuard(req: Request, res: Response, next: NextFunction) {
  const token = req.headers.authorization?.replace('Bearer ', '');
  
  if (!token || token !== process.env.ADMIN_TOKEN) {
    return res.status(401).json({ 
      error: "Admin access required",
      hint: "Set ADMIN_TOKEN environment variable"
    });
  }
  
  next();
}