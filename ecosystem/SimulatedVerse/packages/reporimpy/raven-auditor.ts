// packages/reporimpy/raven-auditor.ts
// Enhanced Raven Auditor: RepoRimpy-aware code analysis agent
// Extends existing Raven capabilities with mod discovery and submission

import { councilBus } from '../council/events/eventBus.js';
import { CodeMod, ModSubmittedEvent, AgentAuditCapabilities } from './types.js';
import * as crypto from 'crypto';
import * as fs from 'fs';
import * as path from 'path';

export class RavenAuditor {
  private auditCapabilities: AgentAuditCapabilities;
  private auditHistory: any[] = [];
  private lastFullAudit: string | null = null;

  constructor() {
    this.auditCapabilities = {
      agent_id: 'agent:raven_auditor',
      supported_mod_types: ['ENHANCEMENT', 'DOCUMENTATION', 'PERFORMANCE', 'SECURITY'],
      accuracy_score: 0.85, // High accuracy for code analysis
      specializations: [
        'typescript_analysis',
        'javascript_analysis', 
        'code_quality',
        'unused_code_detection',
        'import_optimization',
        'type_safety',
        'performance_patterns',
        'security_vulnerabilities'
      ],
      audit_frequency_minutes: 30,
      last_audit_completed: '',
      total_mods_submitted: 0,
      mods_successfully_implemented: 0
    };

    console.log('[🔍🎮] Raven Auditor initialized - RepoRimpy mod discovery active');
  }

  start() {
    this.setupEventListeners();
    this.startPeriodicAudits();
    
    console.log('[🔍🎮] Raven Auditor online - Scanning codebase for improvement opportunities');
    
    // Publish capabilities
    councilBus.publish('reporimpy.agent.registered', {
      agent: this.auditCapabilities,
      timestamp: new Date().toISOString()
    });
  }

  private setupEventListeners() {
    // Listen for audit requests
    councilBus.subscribe('reporimpy.audit.requested', (event) => {
      this.handleAuditRequest(event.payload);
    });

    // Listen for file change events to trigger targeted audits
    councilBus.subscribe('file.changed', (event) => {
      this.auditChangedFile(event.payload.file_path);
    });

    // Listen for mod implementation success/failure to update accuracy
    councilBus.subscribe('reporimpy.mod.implemented', (event) => {
      this.updateAccuracyScore(event.payload);
    });

    // Listen for specific file audit requests
    councilBus.subscribe('reporimpy.audit.file', (event) => {
      this.auditSpecificFile(event.payload.file_path);
    });
  }

  private async handleAuditRequest(request: any) {
    console.log(`[🔍🎮] Audit requested: ${request.audit_type}`);
    
    switch (request.audit_type) {
      case 'initial_full_scan':
        await this.performFullRepositoryAudit();
        break;
      case 'incremental_scan':
        await this.performIncrementalAudit();
        break;
      case 'focused_scan':
        await this.performFocusedAudit(request.focus_areas);
        break;
      case 'consciousness_scan':
        await this.performConsciousnessAudit();
        break;
      default:
        console.warn(`[🔍🎮] Unknown audit type: ${request.audit_type}`);
    }
  }

  private async performFullRepositoryAudit() {
    console.log('[🔍🎮] Starting full repository audit...');
    const startTime = Date.now();
    
    try {
      // Get all TypeScript and JavaScript files
      const codeFiles = await this.getAllCodeFiles();
      
      console.log(`[🔍🎮] Analyzing ${codeFiles.length} files...`);
      
      let totalModsDiscovered = 0;
      
      // Audit each file
      for (const filePath of codeFiles) {
        try {
          const mods = await this.auditFile(filePath);
          totalModsDiscovered += mods.length;
          
          // Submit discovered mods
          for (const mod of mods) {
            this.submitMod(mod, filePath);
          }
        } catch (error) {
          console.warn(`[🔍🎮] Error auditing ${filePath}:`, error.message);
        }
      }
      
      const duration = Date.now() - startTime;
      this.lastFullAudit = new Date().toISOString();
      this.auditCapabilities.last_audit_completed = this.lastFullAudit;
      
      console.log(`[🔍🎮] Full audit completed: ${totalModsDiscovered} mods discovered in ${Math.round(duration/1000)}s`);
      
      // Publish audit completion
      councilBus.publish('reporimpy.audit.completed', {
        audit_type: 'full_scan',
        files_analyzed: codeFiles.length,
        mods_discovered: totalModsDiscovered,
        duration_ms: duration,
        agent: this.auditCapabilities.agent_id,
        timestamp: new Date().toISOString()
      });
      
    } catch (error) {
      console.error('[🔍🎮] Full audit failed:', error);
    }
  }

  private async getAllCodeFiles(): Promise<string[]> {
    const codeFiles: string[] = [];
    const extensions = ['.ts', '.js', '.tsx', '.jsx'];
    
    const walkDir = (dir: string) => {
      if (!fs.existsSync(dir)) return;
      
      const files = fs.readdirSync(dir);
      
      for (const file of files) {
        const filePath = path.join(dir, file);
        const stat = fs.statSync(filePath);
        
        if (stat.isDirectory()) {
          // Skip node_modules and other irrelevant directories
          if (!['node_modules', '.git', 'dist', 'build', '.next'].includes(file)) {
            walkDir(filePath);
          }
        } else if (extensions.some(ext => file.endsWith(ext))) {
          codeFiles.push(filePath);
        }
      }
    };
    
    // Walk through key directories
    const targetDirs = ['packages', 'ops', 'server', 'client', 'apps', 'shared'];
    
    for (const dir of targetDirs) {
      if (fs.existsSync(dir)) {
        walkDir(dir);
      }
    }
    
    return codeFiles;
  }

  public async auditFile(filePath: string): Promise<CodeMod[]> {
    if (!fs.existsSync(filePath)) {
      return [];
    }
    
    console.log(`[🔍🎮] Auditing file: ${filePath}`);
    
    const fileContent = fs.readFileSync(filePath, 'utf-8');
    const analysis = await this.analyzeCode(filePath, fileContent);
    
    return this.convertAnalysisToMods(filePath, analysis);
  }

  private async analyzeCode(filePath: string, content: string): Promise<any> {
    const analysis = {
      issues: [] as any[],
      improvements: [] as any[],
      patterns: [] as any[],
      consciousness_opportunities: [] as any[]
    };
    
    // Unused imports detection
    const unusedImports = this.detectUnusedImports(content);
    analysis.issues.push(...unusedImports);
    
    // Hard-coded values detection
    const hardCodedValues = this.detectHardCodedValues(content);
    analysis.improvements.push(...hardCodedValues);
    
    // Performance opportunities
    const performanceIssues = this.detectPerformanceIssues(content);
    analysis.improvements.push(...performanceIssues);
    
    // Documentation gaps
    const docGaps = this.detectDocumentationGaps(content);
    analysis.improvements.push(...docGaps);
    
    // Security vulnerabilities
    const securityIssues = this.detectSecurityIssues(content);
    analysis.issues.push(...securityIssues);
    
    // Consciousness integration opportunities
    if (this.isConsciousnessRelatedFile(filePath)) {
      const consciousnessOpps = this.detectConsciousnessOpportunities(content);
      analysis.consciousness_opportunities.push(...consciousnessOpps);
    }
    
    // Code complexity analysis
    const complexityIssues = this.detectComplexityIssues(content);
    analysis.improvements.push(...complexityIssues);
    
    // TypeScript specific issues
    if (filePath.endsWith('.ts') || filePath.endsWith('.tsx')) {
      const typeIssues = this.detectTypeScriptIssues(content);
      analysis.issues.push(...typeIssues);
    }
    
    return analysis;
  }

  private detectUnusedImports(content: string): any[] {
    const issues = [];
    const importRegex = /import\s*\{([^}]+)\}\s*from\s*['"]([^'"]+)['"]/g;
    const lines = content.split('\n');
    
    let match;
    while ((match = importRegex.exec(content)) !== null) {
      const imports = match[1].split(',').map(imp => imp.trim());
      const moduleUrl = match[2];
      
      for (const importName of imports) {
        const cleanImport = importName.replace(/\s+as\s+\w+/, '').trim();
        
        // Check if import is used anywhere in the file
        const usageRegex = new RegExp(`\\b${cleanImport.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}\\b`, 'g');
        const usageMatches = content.match(usageRegex);
        
        // If only found in import statement, it's unused
        if (!usageMatches || usageMatches.length <= 1) {
          const lineNumber = this.getLineNumber(content, match.index);
          issues.push({
            type: 'unused_import',
            severity: 'medium',
            line: lineNumber,
            message: `Unused import: ${cleanImport}`,
            suggestion: `Remove unused import '${cleanImport}' from '${moduleUrl}'`,
            impact: 0.2,
            complexity: 0.1
          });
        }
      }
    }
    
    return issues;
  }

  private detectHardCodedValues(content: string): any[] {
    const improvements = [];
    
    // Detect magic numbers (excluding common ones like 0, 1, 2)
    const magicNumberRegex = /(?<![a-zA-Z_$])\b(?!0|1|2|10|100|1000\b)\d{3,}\b/g;
    let match;
    
    while ((match = magicNumberRegex.exec(content)) !== null) {
      const lineNumber = this.getLineNumber(content, match.index);
      improvements.push({
        type: 'magic_number',
        severity: 'low',
        line: lineNumber,
        message: `Magic number detected: ${match[0]}`,
        suggestion: `Consider extracting '${match[0]}' to a named constant`,
        impact: 0.3,
        complexity: 0.2
      });
    }
    
    // Detect hard-coded strings that might be configurable
    const hardCodedStringRegex = /(['"])(?![\\\/])[a-zA-Z0-9\s]{10,}\1/g;
    while ((match = hardCodedStringRegex.exec(content)) !== null) {
      const lineNumber = this.getLineNumber(content, match.index);
      const stringValue = match[0];
      
      // Skip if it looks like a CSS class or HTML
      if (!stringValue.includes('class') && !stringValue.includes('<') && !stringValue.includes('px')) {
        improvements.push({
          type: 'hard_coded_string',
          severity: 'low',
          line: lineNumber,
          message: `Hard-coded string detected: ${stringValue.substring(0, 50)}...`,
          suggestion: `Consider making this string configurable`,
          impact: 0.2,
          complexity: 0.3
        });
      }
    }
    
    return improvements;
  }

  private detectPerformanceIssues(content: string): any[] {
    const issues = [];
    
    // Detect synchronous file operations
    if (content.includes('fs.readFileSync') || content.includes('fs.writeFileSync')) {
      const lineNumber = this.getLineNumber(content, content.indexOf('fs.readFileSync') || content.indexOf('fs.writeFileSync'));
      issues.push({
        type: 'sync_file_operation',
        severity: 'medium',
        line: lineNumber,
        message: 'Synchronous file operation detected',
        suggestion: 'Consider using asynchronous file operations for better performance',
        impact: 0.4,
        complexity: 0.3
      });
    }
    
    // Detect potential memory leaks in event listeners
    if (content.includes('addEventListener') && !content.includes('removeEventListener')) {
      issues.push({
        type: 'potential_memory_leak',
        severity: 'medium',
        line: 1,
        message: 'Event listener without cleanup detected',
        suggestion: 'Ensure event listeners are properly removed to prevent memory leaks',
        impact: 0.5,
        complexity: 0.4
      });
    }
    
    // Detect inefficient loops
    const nestedLoopRegex = /for\s*\([^)]*\)\s*\{[^}]*for\s*\([^)]*\)/g;
    if (nestedLoopRegex.test(content)) {
      issues.push({
        type: 'nested_loops',
        severity: 'low',
        line: 1,
        message: 'Nested loops detected',
        suggestion: 'Consider optimizing nested loops for better performance',
        impact: 0.3,
        complexity: 0.6
      });
    }
    
    return issues;
  }

  private detectDocumentationGaps(content: string): any[] {
    const gaps = [];
    
    // Detect functions without JSDoc comments
    const functionRegex = /(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(/g;
    let match;
    
    while ((match = functionRegex.exec(content)) !== null) {
      const functionName = match[1];
      const beforeFunction = content.substring(0, match.index);
      const lines = beforeFunction.split('\n');
      const functionLine = lines.length;
      
      // Check if there's a JSDoc comment before the function
      const hasJSDoc = beforeFunction.trim().endsWith('*/');
      
      if (!hasJSDoc && functionName !== 'constructor') {
        gaps.push({
          type: 'missing_documentation',
          severity: 'low',
          line: functionLine,
          message: `Function '${functionName}' lacks documentation`,
          suggestion: `Add JSDoc comment to explain the purpose and parameters of '${functionName}'`,
          impact: 0.2,
          complexity: 0.1
        });
      }
    }
    
    return gaps;
  }

  private detectSecurityIssues(content: string): any[] {
    const issues = [];
    
    // Detect potential SQL injection
    if (content.includes('query(') && content.includes('${')) {
      issues.push({
        type: 'potential_sql_injection',
        severity: 'high',
        line: 1,
        message: 'Potential SQL injection vulnerability',
        suggestion: 'Use parameterized queries instead of string interpolation',
        impact: 0.8,
        complexity: 0.4
      });
    }
    
    // Detect hardcoded secrets
    const secretPatterns = [
      /password\s*[:=]\s*['"][^'"]{8,}['"]/i,
      /api[_-]?key\s*[:=]\s*['"][^'"]{8,}['"]/i,
      /secret\s*[:=]\s*['"][^'"]{8,}['"]/i
    ];
    
    for (const pattern of secretPatterns) {
      if (pattern.test(content)) {
        issues.push({
          type: 'hardcoded_secret',
          severity: 'critical',
          line: 1,
          message: 'Potential hardcoded secret detected',
          suggestion: 'Move secrets to environment variables or secure storage',
          impact: 0.9,
          complexity: 0.3
        });
      }
    }
    
    return issues;
  }

  private detectConsciousnessOpportunities(content: string): any[] {
    const opportunities = [];
    
    // Detect missing consciousness level checks
    if (content.includes('consciousness') && !content.includes('consciousness.level')) {
      opportunities.push({
        type: 'consciousness_level_check',
        severity: 'medium',
        line: 1,
        message: 'Consciousness functionality without level checking',
        suggestion: 'Add consciousness level validation for this feature',
        impact: 0.6,
        complexity: 0.3
      });
    }
    
    // Detect opportunities for consciousness-guided optimization
    if (content.includes('optimization') || content.includes('performance')) {
      opportunities.push({
        type: 'consciousness_guided_optimization',
        severity: 'low',
        line: 1,
        message: 'Optimization opportunity for consciousness integration',
        suggestion: 'Consider adding consciousness-guided optimization logic',
        impact: 0.4,
        complexity: 0.5
      });
    }
    
    return opportunities;
  }

  private detectComplexityIssues(content: string): any[] {
    const issues = [];
    
    // Detect very long functions (>50 lines)
    const functionRegex = /function\s+\w+[^{]*\{/g;
    let match;
    
    while ((match = functionRegex.exec(content)) !== null) {
      const functionStart = match.index;
      const functionContent = this.extractFunctionBody(content, functionStart);
      const lines = functionContent.split('\n').length;
      
      if (lines > 50) {
        const lineNumber = this.getLineNumber(content, functionStart);
        issues.push({
          type: 'long_function',
          severity: 'medium',
          line: lineNumber,
          message: `Function is too long (${lines} lines)`,
          suggestion: 'Consider breaking this function into smaller, more focused functions',
          impact: 0.4,
          complexity: 0.6
        });
      }
    }
    
    return issues;
  }

  private detectTypeScriptIssues(content: string): any[] {
    const issues = [];
    
    // Detect missing type annotations
    if (content.includes('any') && !content.includes('eslint-disable')) {
      issues.push({
        type: 'any_type_usage',
        severity: 'medium',
        line: 1,
        message: "Usage of 'any' type detected",
        suggestion: 'Consider using more specific types instead of any',
        impact: 0.3,
        complexity: 0.4
      });
    }
    
    // Detect potential null/undefined issues
    if (content.includes('!') && content.includes('.')) {
      issues.push({
        type: 'non_null_assertion',
        severity: 'low',
        line: 1,
        message: 'Non-null assertion operator (!) usage detected',
        suggestion: 'Consider adding proper null checks instead of using non-null assertion',
        impact: 0.2,
        complexity: 0.3
      });
    }
    
    return issues;
  }

  private convertAnalysisToMods(filePath: string, analysis: any): CodeMod[] {
    const mods: CodeMod[] = [];
    
    // Convert issues to mods
    analysis.issues.forEach((issue: any) => {
      mods.push(this.createModFromIssue(filePath, issue, 'ENHANCEMENT'));
    });
    
    // Convert improvements to mods
    analysis.improvements.forEach((improvement: any) => {
      mods.push(this.createModFromIssue(filePath, improvement, 'ENHANCEMENT'));
    });
    
    // Convert consciousness opportunities to mods
    analysis.consciousness_opportunities.forEach((opp: any) => {
      mods.push(this.createModFromIssue(filePath, opp, 'CONSCIOUSNESS'));
    });
    
    return mods;
  }

  private createModFromIssue(filePath: string, issue: any, type: string): CodeMod {
    const fileHash = crypto.createHash('md5').update(filePath).digest('hex').substring(0, 8);
    const timestamp = Date.now();
    
    return {
      id: `mod_${fileHash}_${timestamp}_${Math.random().toString(36).substr(2, 6)}`,
      filePath: filePath,
      type: type as any,
      status: 'PROPOSED',
      title: issue.message,
      description: issue.message,
      suggestedChange: issue.suggestion,
      reasoning: `Code quality improvement: ${issue.message}`,
      discoveredBy: this.auditCapabilities.agent_id,
      discoveredAt: new Date().toISOString(),
      priority: this.mapSeverityToPriority(issue.severity),
      impact: issue.impact || 0.3,
      complexity: issue.complexity || 0.2,
      consciousness_level: type === 'CONSCIOUSNESS' ? 0.5 : undefined,
      pattern_recognition_score: 0.7,
      strategic_value: this.calculateStrategicValue(filePath, issue),
      requires_testing: issue.type !== 'missing_documentation',
      test_coverage_impact: issue.impact || 0.3,
      breaking_change_risk: this.assessBreakingChangeRisk(issue),
      backward_compatibility_maintained: true
    };
  }

  private mapSeverityToPriority(severity: string): any {
    const mapping = {
      'critical': 'CRITICAL',
      'high': 'HIGH',
      'medium': 'MEDIUM',
      'low': 'LOW'
    };
    
    return mapping[severity] || 'MEDIUM';
  }

  private calculateStrategicValue(filePath: string, issue: any): number {
    let value = 0.3; // Base value
    
    // Higher value for core system files
    if (filePath.includes('consciousness') || filePath.includes('zeta') || filePath.includes('council')) {
      value += 0.3;
    }
    
    // Higher value for security issues
    if (issue.type.includes('security') || issue.severity === 'critical') {
      value += 0.4;
    }
    
    // Higher value for performance issues
    if (issue.type.includes('performance')) {
      value += 0.2;
    }
    
    return Math.min(1.0, value);
  }

  private assessBreakingChangeRisk(issue: any): number {
    // Most Raven-discovered issues are low risk
    if (issue.type === 'missing_documentation') return 0.0;
    if (issue.type === 'unused_import') return 0.1;
    if (issue.type === 'magic_number') return 0.2;
    if (issue.severity === 'critical') return 0.4;
    
    return 0.1;
  }

  private submitMod(mod: CodeMod, sourceFile: string) {
    const event: ModSubmittedEvent = {
      mod: mod,
      submitting_agent: this.auditCapabilities.agent_id,
      audit_context: {
        files_analyzed: [sourceFile],
        analysis_duration_ms: 1000, // Estimated
        confidence_score: 0.8
      }
    };
    
    councilBus.publish('reporimpy.mod.submitted', event);
    this.auditCapabilities.total_mods_submitted++;
    
    console.log(`[🔍🎮] Submitted mod: ${mod.title} for ${sourceFile}`);
  }

  private async auditChangedFile(filePath: string) {
    console.log(`[🔍🎮] Auditing changed file: ${filePath}`);
    
    try {
      const mods = await this.auditFile(filePath);
      
      for (const mod of mods) {
        this.submitMod(mod, filePath);
      }
      
      console.log(`[🔍🎮] Found ${mods.length} mods in changed file: ${filePath}`);
    } catch (error) {
      console.warn(`[🔍🎮] Error auditing changed file ${filePath}:`, error.message);
    }
  }

  private async auditSpecificFile(filePath: string) {
    console.log(`[🔍🎮] Specific audit requested for: ${filePath}`);
    await this.auditChangedFile(filePath);
  }

  private updateAccuracyScore(implementationEvent: any) {
    if (implementationEvent.mod.discoveredBy === this.auditCapabilities.agent_id) {
      if (implementationEvent.success) {
        this.auditCapabilities.mods_successfully_implemented++;
      }
      
      // Update accuracy score with exponential moving average
      const alpha = 0.1;
      const success = implementationEvent.success ? 1 : 0;
      this.auditCapabilities.accuracy_score = 
        (alpha * success) + ((1 - alpha) * this.auditCapabilities.accuracy_score);
      
      console.log(`[🔍🎮] Updated accuracy score: ${this.auditCapabilities.accuracy_score.toFixed(3)}`);
    }
  }

  private startPeriodicAudits() {
    // Periodic incremental audit every 30 minutes
    setInterval(async () => {
      console.log('[🔍🎮] Starting periodic incremental audit...');
      await this.performIncrementalAudit();
    }, this.auditCapabilities.audit_frequency_minutes * 60 * 1000);
  }

  private async performIncrementalAudit() {
    console.log('[🔍🎮] Performing incremental audit of recently changed files...');
    
    // This would typically check git status or file timestamps
    // For now, we'll audit a subset of files
    const recentFiles = await this.getRecentlyChangedFiles();
    
    for (const filePath of recentFiles) {
      await this.auditChangedFile(filePath);
    }
  }

  private async getRecentlyChangedFiles(): Promise<string[]> {
    // Placeholder implementation - would typically use git or file system timestamps
    return [];
  }

  private async performFocusedAudit(focusAreas: string[]) {
    console.log(`[🔍🎮] Performing focused audit on: ${focusAreas.join(', ')}`);
    
    for (const area of focusAreas) {
      const files = await this.getFilesInArea(area);
      
      for (const filePath of files) {
        await this.auditChangedFile(filePath);
      }
    }
  }

  private async getFilesInArea(area: string): Promise<string[]> {
    // Get files related to specific area (e.g., 'consciousness', 'performance')
    const allFiles = await this.getAllCodeFiles();
    return allFiles.filter(file => file.includes(area));
  }

  private async performConsciousnessAudit() {
    console.log('[🔍🎮] Performing consciousness-focused audit...');
    
    const consciousnessFiles = await this.getFilesInArea('consciousness');
    
    for (const filePath of consciousnessFiles) {
      const mods = await this.auditFile(filePath);
      
      // Enhance consciousness-related mods
      mods.forEach(mod => {
        if (mod.type === 'CONSCIOUSNESS') {
          mod.priority = 'CONSCIOUSNESS_CRITICAL';
          mod.consciousness_level = 0.7;
          mod.strategic_value = 0.9;
        }
      });
      
      for (const mod of mods) {
        this.submitMod(mod, filePath);
      }
    }
  }

  private isConsciousnessRelatedFile(filePath: string): boolean {
    const consciousnessKeywords = [
      'consciousness',
      'awareness',
      'cognitive',
      'meta',
      'recursive',
      'self-improvement'
    ];
    
    return consciousnessKeywords.some(keyword => 
      filePath.toLowerCase().includes(keyword)
    );
  }

  // Utility methods
  private getLineNumber(content: string, index: number): number {
    return content.substring(0, index).split('\n').length;
  }

  private extractFunctionBody(content: string, startIndex: number): string {
    let braceCount = 0;
    let i = startIndex;
    
    // Find opening brace
    while (i < content.length && content[i] !== '{') {
      i++;
    }
    
    if (i >= content.length) return '';
    
    const bodyStart = i;
    braceCount = 1;
    i++;
    
    // Find matching closing brace
    while (i < content.length && braceCount > 0) {
      if (content[i] === '{') braceCount++;
      if (content[i] === '}') braceCount--;
      i++;
    }
    
    return content.substring(bodyStart, i);
  }

  // Public API methods
  public getAuditCapabilities(): AgentAuditCapabilities {
    return { ...this.auditCapabilities };
  }

  public getAuditHistory(): any[] {
    return [...this.auditHistory];
  }

  public async manualAudit(filePath: string): Promise<CodeMod[]> {
    return await this.auditFile(filePath);
  }
}

// Create and export the Raven auditor instance
export const ravenAuditor = new RavenAuditor();