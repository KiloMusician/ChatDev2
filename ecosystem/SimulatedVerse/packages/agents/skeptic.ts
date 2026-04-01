// packages/agents/skeptic.ts
// @ts-ignore - Council event bus is JS module with implicit types
import { councilBus } from "../council/events/eventBus";
import { shout, whisper, cheer } from "../comms/speak";

function looksLikeTheater(ev: any): boolean {
  const msg = JSON.stringify(ev.payload ?? {});
  // Advanced theater pattern detection with multiple heuristics
  const theaterPatterns: RegExp[] = [
    /placeholder|TODO|FIXME/i,           // Explicit placeholders
    /fake|stub|mock(?!ing)/i,           // Fake implementations  
    /hardcoded\s+error|throw.*TODO/i,   // Hardcoded error patterns
    /appears.*working|seems.*fine/i,     // Vague success claims
    /console\.log.*TODO|temporary/i      // Temporary logging
  ];
  
  return theaterPatterns.some((pattern: RegExp) => pattern.test(msg));
}

councilBus.subscribeAll?.((ev: any)=>{
  // Page on theater; ask for proofs
  if (looksLikeTheater(ev)) {
    shout("skeptic","Theater suspected",
      `Topic: ${ev.topic}\nPlease attach:\n• QGL receipt\n• diff/commit id\n• runnable proof or test id`);
  }
  // Heartbeat on key completions
  if (/\.completed$/.test(ev.topic)) {
    cheer("skeptic","Artifact completed ✅", `Topic: ${ev.topic}`);
  }
});

// Listen to human replies (from SystemInbox)
councilBus.subscribe("human.reply", (ev: any)=>{
  whisper("skeptic","Human reply received", ev.payload?.reply ?? "");
});
