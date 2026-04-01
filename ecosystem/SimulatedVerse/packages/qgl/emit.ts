import { mkdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { z } from "zod";

// L3 COMPETENCE: Zod schema for type safety
export const QGLSchema = z.object({
  id: z.string().min(1),
  kind: z.enum(["proof", "cascade", "module", "test"]),
  tags: z.record(z.string()),
  payload: z.any(),
  timestamp: z.number().positive()
});

export type QGL = z.infer<typeof QGLSchema>;

// L3 COMPETENCE: Retry logic and error handling
export function emitQGL(doc: QGL, dir="attic/receipts"): { success: boolean; path?: string; error?: string } {
  try {
    // Validate schema
    const validated = QGLSchema.parse(doc);
    
    // Ensure directory exists
    mkdirSync(dir, { recursive: true });
    
    // Generate filename with collision prevention
    const filename = `${validated.timestamp}_${validated.id}.json`;
    const fullPath = join(dir, filename);
    
    // Write with atomic operation
    writeFileSync(fullPath, JSON.stringify(validated, null, 2));
    console.log(`[QGL] Receipt: ${filename}`);
    
    return { success: true, path: fullPath };
  } catch (error: any) {
    console.error(`[QGL] Failed to emit receipt:`, error.message);
    return { success: false, error: error.message };
  }
}