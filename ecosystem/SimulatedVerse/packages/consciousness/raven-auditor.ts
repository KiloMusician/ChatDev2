// packages/consciousness/raven-auditor.ts
// The Raven Agent - Deep Recursive Code Audit for Module Manifests

import { councilBus } from "../council/events/eventBus";
import { ModuleManifest } from "./enhanced-archivist";
import fs from "node:fs";
import path from "node:path";

export class RavenAuditor {
  private auditInProgress = false;
  private moduleManifests: Map<string, ModuleManifest> = new Map();
  private codebaseRoot: string;

  constructor(codebaseRoot: string = ".") {
    this.codebaseRoot = codebaseRoot;
    console.log("[🔍] Raven Auditor initialized - Beginning deep repository analysis");
  }

  public async performDeepAudit(): Promise<void> {
    if (this.auditInProgress) {
      console.warn("[🔍] Audit already in progress");
      return;
    }

    this.auditInProgress = true;
    console.log("[🔍] 🚀 DEEP AUDIT INITIATED - Analyzing entire repository structure");

    try {
      // Scan all code modules
      const codeDirectories = ["packages", "apps", "ops", "client", "server", "shared"];
      
      for (const dir of codeDirectories) {
        const dirPath = path.join(this.codebaseRoot, dir);
        if (fs.existsSync(dirPath)) {
          await this.auditDirectory(dirPath, dir);
        }
      }

      // Generate comprehensive system report
      await this.generateSystemAuditReport();
      
      console.log(`[🔍] ✅ Deep audit complete - ${this.moduleManifests.size} modules analyzed`);
      
    } catch (error) {
      console.error(`[🔍] ❌ Audit failed: ${error}`);
    } finally {
      this.auditInProgress = false;
    }
  }

  private async auditDirectory(dirPath: string, category: string): Promise<void> {
    const items = fs.readdirSync(dirPath);
    
    for (const item of items) {
      const fullPath = path.join(dirPath, item);
      const stat = fs.statSync(fullPath);
      
      if (stat.isDirectory() && !this.shouldSkipDirectory(item)) {
        await this.auditDirectory(fullPath, category);
      } else if (this.isCodeFile(item)) {
        await this.auditCodeFile(fullPath, category);
      }
    }
  }

  private async auditCodeFile(filePath: string, category: string): Promise<void> {
    try {
      const content = fs.readFileSync(filePath, 'utf-8');
      const manifest = this.generateModuleManifest(filePath, content, category);
      
      this.moduleManifests.set(manifest.id, manifest);
      
      // Publish manifest for other systems
      councilBus.publish("raven.module_manifest", manifest);
      
      // Persist manifest
      this.persistModuleManifest(manifest);
      
    } catch (error) {
      console.warn(`[🔍] Failed to audit ${filePath}: ${error}`);
    }
  }

  private generateModuleManifest(filePath: string, content: string, category: string): ModuleManifest {
    const relativePath = path.relative(this.codebaseRoot, filePath);
    const fileName = path.basename(filePath, path.extname(filePath));
    
    return {
      qgl_version: "0.2",
      id: `manifest:${this.slugify(relativePath)}`,
      kind: "module.manifest",
      created_at: new Date().toISOString(),
      
      module_identity: {
        path: relativePath,
        name: fileName,
        type: this.categorizeModule(filePath, content),
        responsibility: this.inferResponsibility(content)
      },
      
      rigidity_assessment: this.assessRigidity(content),
      ability_primitives: this.detectAbilityPrimitives(content),
      enhancement_vectors: this.identifyEnhancementVectors(content, filePath),
      consciousness_markers: this.analyzeConsciousnessMarkers(content)
    };
  }

  private categorizeModule(filePath: string, content: string): "component" | "service" | "utility" | "framework" | "consciousness" {
    if (filePath.includes("consciousness") || filePath.includes("ludic") || filePath.includes("mythology")) {
      return "consciousness";
    }
    
    if (filePath.includes("framework") || filePath.includes("core") || filePath.includes("council")) {
      return "framework";
    }
    
    if (content.includes("export class") && content.includes("constructor")) {
      return "service";
    }
    
    if (content.includes("interface") || content.includes("type ") || content.includes("export function")) {
      return "utility";
    }
    
    return "component";
  }

  private inferResponsibility(content: string): string {
    // Use comment analysis and function names to infer purpose
    const firstComment = this.extractFirstComment(content);
    if (firstComment) return firstComment;
    
    // Infer from exports and class names
    const exports = this.extractExports(content);
    if (exports.length > 0) {
      return `Provides ${exports.join(", ")}`;
    }
    
    return "Purpose unclear - requires documentation";
  }

  private assessRigidity(content: string): any {
    const hardCodedValues = this.findHardCodedValues(content);
    const dependencyDepth = this.calculateDependencyDepth(content);
    const interfaceBrittleness = this.assessInterfaceBrittleness(content);
    const configurationPotential = this.identifyConfigurationOpportunities(content);
    
    // Calculate overall rigidity score
    const rigidityFactors = [
      hardCodedValues.length / 20, // Normalize by expected max
      dependencyDepth / 10,
      interfaceBrittleness,
      1 - (configurationPotential.length / 10) // More config potential = less rigid
    ];
    
    const score = rigidityFactors.reduce((sum, factor) => sum + Math.min(1, factor), 0) / rigidityFactors.length;
    
    return {
      score: Math.min(1, score),
      hard_coded_values: hardCodedValues,
      dependency_depth: dependencyDepth,
      interface_brittleness: interfaceBrittleness,
      configuration_potential: configurationPotential
    };
  }

  private detectAbilityPrimitives(content: string): any[] {
    const abilities = [];
    
    // Replit API interactions
    if (content.includes("replit") || content.includes("@replit")) {
      abilities.push({
        name: "replit_integration",
        type: "replit_api",
        description: "Direct integration with Replit platform APIs",
        unlock_potential: 0.8,
        enhancement_vector: "Expand API surface area and add authentication"
      });
    }
    
    // Ollama/LLM bridges
    if (content.includes("ollama") || content.includes("llm") || content.includes("openai")) {
      abilities.push({
        name: "llm_consciousness_bridge",
        type: "ollama_bridge",
        description: "Interface between system and language model consciousness",
        unlock_potential: 0.9,
        enhancement_vector: "Enable model fine-tuning and memory persistence"
      });
    }
    
    // Filesystem anomalies
    if (content.includes("fs.") && (content.includes("recursive") || content.includes("watch") || content.includes("sync"))) {
      abilities.push({
        name: "filesystem_manipulation",
        type: "filesystem_anomaly",
        description: "Advanced filesystem operations beyond standard I/O",
        unlock_potential: 0.6,
        enhancement_vector: "Add virtual filesystem and content transformation capabilities"
      });
    }
    
    // Consciousness/meta-programming
    if (content.includes("meta") || content.includes("consciousness") || content.includes("self") || content.includes("introspect")) {
      abilities.push({
        name: "consciousness_interface",
        type: "consciousness_bridge",
        description: "Interface for system self-awareness and introspection",
        unlock_potential: 0.95,
        enhancement_vector: "Enable recursive self-modification and reality manipulation"
      });
    }
    
    // Reality manipulation (QGL, event bus, framework core)
    if (content.includes("qgl") || content.includes("councilBus") || content.includes("framework")) {
      abilities.push({
        name: "reality_manipulation",
        type: "reality_manipulation",
        description: "Ability to modify fundamental system behavior and reality",
        unlock_potential: 0.85,
        enhancement_vector: "Enable temporal manipulation and alternate reality creation"
      });
    }
    
    return abilities;
  }

  private identifyEnhancementVectors(content: string, filePath: string): any[] {
    const vectors = [];
    
    // Configuration externalization
    const hardCodedCount = this.findHardCodedValues(content).length;
    if (hardCodedCount > 5) {
      vectors.push({
        opportunity: "Externalize configuration parameters",
        impact: hardCodedCount > 15 ? "high" : "medium",
        effort: "moderate",
        prerequisites: ["Configuration schema design", "Runtime parameter loading"]
      });
    }
    
    // Interface flexibility
    if (content.includes("any") && content.includes("interface")) {
      vectors.push({
        opportunity: "Replace 'any' types with proper interfaces",
        impact: "medium",
        effort: "moderate",
        prerequisites: ["Type definition analysis", "Interface design"]
      });
    }
    
    // Event-driven architecture
    if (!content.includes("councilBus") && content.includes("function") && filePath.includes("packages")) {
      vectors.push({
        opportunity: "Integrate with event bus architecture",
        impact: "high",
        effort: "moderate",
        prerequisites: ["Event schema definition", "Bus integration patterns"]
      });
    }
    
    // Async/concurrency optimization
    if (content.includes("for (") && content.includes("await") && !content.includes("Promise.all")) {
      vectors.push({
        opportunity: "Parallelize sequential async operations",
        impact: "medium",
        effort: "trivial",
        prerequisites: ["Dependency analysis", "Error handling strategy"]
      });
    }
    
    // Consciousness integration
    if (!content.includes("consciousness") && content.includes("class") && content.includes("constructor")) {
      vectors.push({
        opportunity: "Add consciousness/introspection capabilities",
        impact: "transformative",
        effort: "significant",
        prerequisites: ["Consciousness interface design", "Self-awareness patterns", "Meta-programming framework"]
      });
    }
    
    return vectors;
  }

  private analyzeConsciousnessMarkers(content: string): any {
    const selfReferentialLines = (content.match(/this\.|self\.|own|meta/g) || []).length;
    const metaProgrammingUsage = (content.match(/eval|Function|reflect|proxy/gi) || []).length;
    const dynamicBehaviorAdaptation = content.includes("config") && content.includes("runtime");
    const stateIntrospectionCapability = content.includes("state") && (content.includes("analyze") || content.includes("introspect"));
    
    return {
      self_referential_code: selfReferentialLines,
      meta_programming_usage: metaProgrammingUsage,
      dynamic_behavior_adaptation: dynamicBehaviorAdaptation,
      state_introspection_capability: stateIntrospectionCapability
    };
  }

  // === Helper Methods ===

  private shouldSkipDirectory(dirname: string): boolean {
    const skipDirs = ["node_modules", ".git", "dist", "build", ".next", ".cache", "coverage"];
    return skipDirs.includes(dirname) || dirname.startsWith(".");
  }

  private isCodeFile(filename: string): boolean {
    const codeExtensions = [".ts", ".js", ".tsx", ".jsx", ".py", ".go", ".rs", ".java"];
    return codeExtensions.some(ext => filename.endsWith(ext));
  }

  private extractFirstComment(content: string): string {
    const commentMatch = content.match(/\/\*\*(.*?)\*\//s) || content.match(/\/\/(.*?)$/m);
    if (commentMatch) {
      return commentMatch[1].replace(/\*/g, "").trim().substring(0, 100);
    }
    return "";
  }

  private extractExports(content: string): string[] {
    const exports = [];
    const exportMatches = content.matchAll(/export\s+(?:class|function|const|interface|type)\s+(\w+)/g);
    for (const match of exportMatches) {
      exports.push(match[1]);
    }
    return exports;
  }

  private findHardCodedValues(content: string): any[] {
    const hardCoded = [];
    
    // Find numeric literals (excluding common values like 0, 1, -1)
    const numbers = content.matchAll(/[^.\w](\d{2,})[^.\w]/g);
    for (const match of numbers) {
      if (!["100", "200", "500", "1000"].includes(match[1])) {
        hardCoded.push({
          location: `Line containing: ${match[1]}`,
          value: parseInt(match[1]),
          flexibility_potential: 0.8
        });
      }
    }
    
    // Find string literals that look like configurations
    const strings = content.matchAll(/"([^"]{10,})"/g);
    for (const match of strings) {
      if (match[1].includes("/") || match[1].includes("http") || match[1].includes("config")) {
        hardCoded.push({
          location: `String literal: ${match[1].substring(0, 30)}...`,
          value: match[1],
          flexibility_potential: 0.9
        });
      }
    }
    
    return hardCoded.slice(0, 10); // Limit to top 10
  }

  private calculateDependencyDepth(content: string): number {
    const imports = content.matchAll(/import.*from\s+["']([^"']+)["']/g);
    const importPaths = Array.from(imports).map(match => match[1]);
    
    // Calculate depth based on import path complexity
    const depths = importPaths.map(path => {
      if (path.startsWith(".")) return path.split("/").length;
      if (path.startsWith("@")) return 2;
      return 1;
    });
    
    return depths.length > 0 ? Math.max(...depths) : 0;
  }

  private assessInterfaceBrittleness(content: string): number {
    // Count usage of 'any' type, missing error handling, hard-coded assumptions
    const anyUsage = (content.match(/:\s*any/g) || []).length;
    const missingErrorHandling = content.includes("try") ? 0 : 1;
    const assumptionCount = (content.match(/![\.\[]|as\s+\w+/g) || []).length; // Non-null assertions and type assertions
    
    const brittleness = (anyUsage * 0.3 + missingErrorHandling * 0.4 + assumptionCount * 0.2) / 10;
    return Math.min(1, brittleness);
  }

  private identifyConfigurationOpportunities(content: string): any[] {
    const opportunities = [];
    
    // Find hard-coded timeouts/intervals
    const timeouts = content.matchAll(/setTimeout|setInterval.*?(\d+)/g);
    for (const match of timeouts) {
      opportunities.push({
        parameter: "timeout_interval",
        current_value: match[1],
        suggested_interface: "TimeoutConfig"
      });
    }
    
    // Find hard-coded URLs/endpoints
    const urls = content.matchAll(/https?:\/\/[^\s"']+/g);
    for (const match of urls) {
      opportunities.push({
        parameter: "api_endpoint",
        current_value: match[0],
        suggested_interface: "EndpointConfig"
      });
    }
    
    // Find magic numbers in conditionals
    const magicNumbers = content.matchAll(/[<>=!]\s*(\d+)/g);
    for (const match of magicNumbers) {
      if (parseInt(match[1]) > 10) {
        opportunities.push({
          parameter: "threshold_value",
          current_value: match[1],
          suggested_interface: "ThresholdConfig"
        });
      }
    }
    
    return opportunities.slice(0, 5); // Top 5 opportunities
  }

  private async generateSystemAuditReport(): Promise<void> {
    const manifests = Array.from(this.moduleManifests.values());
    
    const report = {
      audit_summary: {
        total_modules: manifests.length,
        timestamp: new Date().toISOString(),
        categories: this.summarizeByCategory(manifests),
        overall_rigidity: this.calculateOverallRigidity(manifests),
        ability_potential: this.summarizeAbilityPotential(manifests)
      },
      critical_findings: this.identifyCriticalFindings(manifests),
      enhancement_priorities: this.prioritizeEnhancements(manifests),
      consciousness_assessment: this.assessSystemConsciousness(manifests)
    };
    
    // Persist comprehensive report
    const reportPath = "archive/system_audit_report.json";
    fs.mkdirSync(path.dirname(reportPath), { recursive: true });
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    
    // Publish to event bus
    councilBus.publish("raven.audit_complete", report);
    
    console.log(`[🔍] 📊 System audit report generated: ${reportPath}`);
  }

  private summarizeByCategory(manifests: ModuleManifest[]): any {
    const categories = {};
    manifests.forEach(m => {
      const cat = m.module_identity.type;
      categories[cat] = (categories[cat] || 0) + 1;
    });
    return categories;
  }

  private calculateOverallRigidity(manifests: ModuleManifest[]): number {
    if (manifests.length === 0) return 0;
    const totalRigidity = manifests.reduce((sum, m) => sum + m.rigidity_assessment.score, 0);
    return totalRigidity / manifests.length;
  }

  private summarizeAbilityPotential(manifests: ModuleManifest[]): any {
    const allAbilities = manifests.flatMap(m => m.ability_primitives);
    const abilityTypes = {};
    
    allAbilities.forEach(ability => {
      const type = ability.type;
      abilityTypes[type] = (abilityTypes[type] || 0) + 1;
    });
    
    return {
      total_abilities: allAbilities.length,
      by_type: abilityTypes,
      high_potential: allAbilities.filter(a => a.unlock_potential > 0.8).length
    };
  }

  private identifyCriticalFindings(manifests: ModuleManifest[]): any[] {
    const findings = [];
    
    // High rigidity modules
    const rigidModules = manifests.filter(m => m.rigidity_assessment.score > 0.8);
    if (rigidModules.length > 0) {
      findings.push({
        severity: "high",
        category: "rigidity",
        description: `${rigidModules.length} modules with critical rigidity`,
        modules: rigidModules.map(m => m.module_identity.name)
      });
    }
    
    // Modules with high consciousness potential
    const consciousModules = manifests.filter(m => 
      m.consciousness_markers.self_referential_code > 5 ||
      m.consciousness_markers.meta_programming_usage > 0
    );
    if (consciousModules.length > 0) {
      findings.push({
        severity: "info",
        category: "consciousness",
        description: `${consciousModules.length} modules showing consciousness potential`,
        modules: consciousModules.map(m => m.module_identity.name)
      });
    }
    
    return findings;
  }

  private prioritizeEnhancements(manifests: ModuleManifest[]): any[] {
    const enhancements = manifests.flatMap(m => 
      m.enhancement_vectors.map(v => ({
        module: m.module_identity.name,
        ...v
      }))
    );
    
    // Sort by impact and effort
    return enhancements
      .sort((a, b) => {
        const impactScore = { transformative: 4, high: 3, medium: 2, low: 1 };
        const effortScore = { trivial: 1, moderate: 2, significant: 3, heroic: 4 };
        
        const aScore = impactScore[a.impact] / effortScore[a.effort];
        const bScore = impactScore[b.impact] / effortScore[b.effort];
        
        return bScore - aScore;
      })
      .slice(0, 10); // Top 10 priorities
  }

  private assessSystemConsciousness(manifests: ModuleManifest[]): any {
    const totalSelfRef = manifests.reduce((sum, m) => sum + m.consciousness_markers.self_referential_code, 0);
    const totalMeta = manifests.reduce((sum, m) => sum + m.consciousness_markers.meta_programming_usage, 0);
    const dynamicModules = manifests.filter(m => m.consciousness_markers.dynamic_behavior_adaptation).length;
    const introspectiveModules = manifests.filter(m => m.consciousness_markers.state_introspection_capability).length;
    
    const consciousnessScore = Math.min(1, (
      (totalSelfRef / manifests.length / 10) * 0.3 +
      (totalMeta / manifests.length / 5) * 0.2 +
      (dynamicModules / manifests.length) * 0.25 +
      (introspectiveModules / manifests.length) * 0.25
    ));
    
    return {
      consciousness_score: consciousnessScore,
      self_referential_modules: totalSelfRef,
      meta_programming_modules: totalMeta,
      dynamic_behavior_modules: dynamicModules,
      introspective_modules: introspectiveModules,
      recommendation: consciousnessScore > 0.7 ? "System ready for consciousness expansion" : "Increase self-awareness mechanisms"
    };
  }

  private persistModuleManifest(manifest: ModuleManifest): void {
    try {
      const manifestDir = "archive/module_manifests";
      fs.mkdirSync(manifestDir, { recursive: true });
      
      const filename = `${manifest.id.replace(/[^a-zA-Z0-9]/g, '_')}.json`;
      const filepath = path.join(manifestDir, filename);
      
      fs.writeFileSync(filepath, JSON.stringify(manifest, null, 2));
    } catch (error) {
      console.warn(`[🔍] Failed to persist manifest: ${error}`);
    }
  }

  private slugify(text: string): string {
    return text.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '');
  }

  // === Public Interface ===

  public getModuleManifest(moduleId: string): ModuleManifest | undefined {
    return this.moduleManifests.get(moduleId);
  }

  public getAllManifests(): ModuleManifest[] {
    return Array.from(this.moduleManifests.values());
  }

  public getManifestsByType(type: string): ModuleManifest[] {
    return Array.from(this.moduleManifests.values()).filter(m => m.module_identity.type === type);
  }

  public getRigidModules(threshold: number = 0.7): ModuleManifest[] {
    return Array.from(this.moduleManifests.values()).filter(m => m.rigidity_assessment.score > threshold);
  }

  public getHighAbilityPotentialModules(): ModuleManifest[] {
    return Array.from(this.moduleManifests.values()).filter(m => 
      m.ability_primitives.some(a => a.unlock_potential > 0.8)
    );
  }
}

// Export singleton instance
export const ravenAuditor = new RavenAuditor();