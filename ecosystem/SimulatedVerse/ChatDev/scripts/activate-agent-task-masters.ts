#!/usr/bin/env tsx
/**
 * AGENT TASK MASTER ACTIVATION
 * - Enables Council organizing agent parties
 * - Activates wizard navigator for gameplay development
 * - Unleashes protagonist error hunting
 * - Routes ML/LLM requests directly to ChatDev
 */
import fs from "node:fs";
import path from "node:path";

const ROOT = process.cwd();
const PUS = path.join(ROOT, "ops/pus.ndjson");

function enqueuePU(pu: any) {
  fs.appendFileSync(PUS, JSON.stringify(pu) + "\n");
  console.log(`[agent-master] 📝 Enqueued: ${pu.id}`);
}

(function main() {
  console.log("[agent-master] 🚀 ACTIVATING AGENT TASK MASTER SYSTEMS");
  
  // 1. Council Agent Party Organization
  enqueuePU({
    id: `pu.council.organize.${Date.now()}`,
    kind: "agent",
    summary: "Council organizes agent party for systematic theater elimination",
    priority: 10,
    owner: "council",
    source: "agent-master",
    status: "queued",
    proofs: [
      {"kind": "file_exists", "path": "reports/agents/council.scan.json"},
      {"kind": "report_ok", "path": "reports/agent_productivity.json", "report_key": "agent_artifacts_per_hour", "expected": {"gte": 1}}
    ],
    artifacts: ["reports/agents/council.scan.json", "reports/agent_productivity.json"],
    agent_config: {
      primary_agent: "council",
      task_type: "agent_party_organization",
      target: "theater_elimination",
      coordination_mode: "systematic"
    },
    created_at: Date.now()
  });

  // 2. Wizard Navigator for Gameplay Development  
  enqueuePU({
    id: `pu.wizard.navigate.${Date.now()}`,
    kind: "agent",
    summary: "Wizard navigator develops gameplay mechanics and progression systems",
    priority: 9,
    owner: "wizard",
    source: "agent-master", 
    status: "queued",
    proofs: [
      {"kind": "file_exists", "path": "yap_archive/qgl/wizard_navigation_*"},
      {"kind": "report_ok", "path": "reports/gameplay_development.json", "report_key": "mechanics_implemented", "expected": {"gte": 1}}
    ],
    artifacts: ["yap_archive/qgl/wizard_navigation_session.json", "reports/gameplay_development.json"],
    agent_config: {
      primary_agent: "wizard",
      task_type: "gameplay_development",
      target: "mechanic_implementation",
      development_focus: ["progression", "mechanics", "balance"]
    },
    created_at: Date.now()
  });

  // 3. Protagonist Error Hunter
  enqueuePU({
    id: `pu.protagonist.hunt.${Date.now()}`,
    kind: "agent",
    summary: "Protagonist plays game intelligently and hunts for errors/edge cases",
    priority: 8,
    owner: "protagonist",
    source: "agent-master",
    status: "queued", 
    proofs: [
      {"kind": "file_exists", "path": "reports/protagonist_gameplay.json"},
      {"kind": "report_ok", "path": "reports/error_hunting.json", "report_key": "errors_discovered", "expected": {"gte": 1}}
    ],
    artifacts: ["reports/protagonist_gameplay.json", "reports/error_hunting.json"],
    agent_config: {
      primary_agent: "protagonist",
      task_type: "error_hunting",
      target: "gameplay_testing",
      intelligence_mode: "adaptive",
      exploration_depth: "comprehensive"
    },
    created_at: Date.now()
  });

  // 4. ML/LLM → ChatDev Direct Pipeline
  enqueuePU({
    id: `pu.ml.chatdev.${Date.now()}`,
    kind: "integration",
    summary: "ML/LLM sends context-aware requests directly to ChatDev interface",
    priority: 7,
    owner: "ml-pipeline",
    source: "agent-master",
    status: "queued",
    proofs: [
      {"kind": "file_exists", "path": "reports/ml_chatdev_integration.json"},
      {"kind": "service_up", "service_url": "http://localhost:5000/api/chatdev"},
      {"kind": "report_ok", "path": "reports/ml_chatdev_integration.json", "report_key": "requests_sent", "expected": {"gte": 1}}
    ],
    artifacts: ["reports/ml_chatdev_integration.json", "yap_archive/qgl/ml_chatdev_sessions.json"],
    agent_config: {
      primary_agent: "ml-coordinator",
      task_type: "chatdev_integration",
      target: "direct_pipeline",
      request_mode: "context_aware",
      escalation_path: "dev_interface"
    },
    created_at: Date.now()
  });

  // 5. Culture Ship Orchestrator Reactivation
  enqueuePU({
    id: `pu.culture.reactivate.${Date.now()}`,
    kind: "orchestration",
    summary: "Reactivate Culture Ship Orchestrator with real coordination (not theater)",
    priority: 9,
    owner: "culture-ship",
    source: "agent-master",
    status: "queued",
    proofs: [
      {"kind": "file_exists", "path": "reports/culture_ship_orchestration.json"},
      {"kind": "report_ok", "path": "reports/culture_ship_orchestration.json", "report_key": "agent_swarm_active", "expected": {"eq": true}}
    ],
    artifacts: ["reports/culture_ship_orchestration.json", "reports/agent_coordination.json"],
    agent_config: {
      primary_agent: "culture-ship",
      task_type: "orchestration_reactivation", 
      target: "real_coordination",
      disable_theater: true,
      enable_proof_gates: true
    },
    created_at: Date.now()
  });

  // 6. Systematic Agent Performance Tracking
  enqueuePU({
    id: `pu.agent.metrics.${Date.now()}`,
    kind: "ops",
    summary: "Implement systematic agent performance tracking and optimization",
    priority: 6,
    owner: "ops",
    source: "agent-master",
    status: "queued",
    proofs: [
      {"kind": "file_exists", "path": "reports/agent_performance_metrics.json"},
      {"kind": "report_ok", "path": "reports/agent_performance_metrics.json", "report_key": "agents_tracked", "expected": {"gte": 5}}
    ],
    artifacts: ["reports/agent_performance_metrics.json", "reports/agent_optimization.json"],
    created_at: Date.now()
  });

  console.log("[agent-master] ✅ Agent task master systems ACTIVATED");
  console.log("[agent-master] 🎯 Agents will now:");
  console.log("  → Council organizes agent parties for systematic work");
  console.log("  → Wizard develops gameplay mechanics");
  console.log("  → Protagonist hunts errors through intelligent gameplay");
  console.log("  → ML/LLM pipeline routes directly to ChatDev");
  console.log("  → Culture Ship coordinates real work (theater disabled)");
  console.log("  → Performance tracking ensures measurable progress");
})();