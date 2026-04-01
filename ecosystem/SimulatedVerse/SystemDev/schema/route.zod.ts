import { z } from 'zod';

// Route guard conditions
export const RouteGuardSchema = z.object({
  type: z.enum(['proof_exists', 'milestone_reached', 'resource_threshold', 'always', 'never']),
  condition: z.string(), // JSON path or requirement string
  required_value: z.any().optional(),
  grace_period_ms: z.number().default(0) // how long to show route after proof expires
});

// Route registration for menu system
export const RouteRegistrationSchema = z.object({
  route_id: z.string(),
  path: z.string(), // URL path
  label: z.string(), // Display name
  description: z.string().optional(),
  icon: z.string().optional(),
  guards: z.array(RouteGuardSchema).default([]),
  adapter_type: z.enum(['ascii', 'godot', 'previewui', 'hybrid']),
  mechanic_id: z.string().optional(), // links to GameDev spec
  menu_category: z.string().default('main'),
  priority: z.number().default(100), // lower = higher priority
  registered_at: z.number(),
  registered_by: z.string() // which agent/system registered it
});

// Route validation result
export const RouteValidationSchema = z.object({
  route_id: z.string(),
  is_valid: z.boolean(),
  checks: z.array(z.object({
    check_name: z.string(),
    status: z.enum(['pass', 'fail', 'skip']),
    message: z.string().optional()
  })),
  last_validated: z.number(),
  proof_freshness: z.number(), // age of most recent proof in ms
  should_show: z.boolean() // final decision after all guards
});

// Menu state for navigation
export const MenuStateSchema = z.object({
  visible_routes: z.array(z.string()), // route IDs that should be shown
  hidden_routes: z.array(z.object({
    route_id: z.string(),
    reason: z.string() // why it's hidden
  })),
  categories: z.record(z.array(z.string())), // category -> route_ids
  last_updated: z.number(),
  guard_violations: z.number() // count of routes hidden due to guard failures
});

// Tooltip data for routes
export const TooltipDataSchema = z.object({
  title: z.string(),
  description: z.string(),
  status: z.enum(['available', 'locked', 'coming_soon', 'broken']),
  requirements: z.array(z.string()).optional(),
  eta_seconds: z.number().optional(), // time until unlocked
  last_proof: z.number().optional(), // timestamp of last proof
  proof_status: z.enum(['fresh', 'stale', 'missing']).optional()
});

// Export types
export type RouteGuard = z.infer<typeof RouteGuardSchema>;
export type RouteRegistration = z.infer<typeof RouteRegistrationSchema>;
export type RouteValidation = z.infer<typeof RouteValidationSchema>;
export type MenuState = z.infer<typeof MenuStateSchema>;
export type TooltipData = z.infer<typeof TooltipDataSchema>;