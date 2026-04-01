/* 
OWNERS: team/infra, ai/prime
TAGS: infra, scope, api, gateway
STABILITY: stable
INTEGRATIONS: agent/gateway, testing/chamber, ui/admin
*/

import { Router } from "express";
import { resolveScope, listAvailableModes, validateScope, type ScopeSelection } from "../lib/scope.js";

const router = Router();

// List available view modes and combos
router.get("/list", (_, res) => {
  try {
    const modes = listAvailableModes();
    res.json({ 
      ok: true, 
      ...modes,
      policies: {
        no_create_when_update_exists: true,
        enforce_rosetta_headers: true,
        run_smokes_before_merge: true
      }
    });
  } catch (error) {
    res.status(500).json({ 
      ok: false, 
      error: "Failed to list view modes",
      details: error instanceof Error ? error.message : String(error)
    });
  }
});

// Resolve scope to concrete file list
router.post("/resolve", (req, res) => {
  try {
    const scope: ScopeSelection = req.body.scope || req.body;
    
    // Validate scope selection
    const validation = validateScope(scope);
    if (!validation.valid) {
      return res.status(400).json({
        ok: false,
        error: "Invalid scope selection",
        details: validation.errors
      });
    }

    const result = resolveScope(scope);
    
    res.json({ 
      ok: true, 
      scope: result,
      count: result.files.length,
      timestamp: new Date().toISOString()
    });
  } catch (error) {
    res.status(500).json({ 
      ok: false, 
      error: "Failed to resolve scope",
      details: error instanceof Error ? error.message : String(error)
    });
  }
});

// Dry-run scope resolution (no file content, just paths)
router.post("/dry-run", (req, res) => {
  try {
    const scope: ScopeSelection = req.body.scope || req.body;
    const result = resolveScope(scope);
    
    res.json({
      ok: true,
      files: result.files.slice(0, 50), // Preview only
      total_count: result.files.length,
      stats: result.stats,
      policies: result.policies
    });
  } catch (error) {
    res.status(500).json({
      ok: false,
      error: "Dry-run failed", 
      details: error instanceof Error ? error.message : String(error)
    });
  }
});

// Validate a specific scope without resolution
router.post("/validate", (req, res) => {
  try {
    const scope: ScopeSelection = req.body.scope || req.body;
    const validation = validateScope(scope);
    
    res.json({
      ok: validation.valid,
      valid: validation.valid,
      errors: validation.errors
    });
  } catch (error) {
    res.status(500).json({
      ok: false,
      error: "Validation failed",
      details: error instanceof Error ? error.message : String(error)
    });
  }
});

export default router;