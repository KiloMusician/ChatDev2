import path from 'path';
import { spawn } from 'child_process';
import fs from 'fs/promises';
// Event bus integration - will be connected via initialization
interface EventBus {
  subscribe(event: string, handler: Function): void;
  publish(event: string, data: any): void;
}

let eventBus: EventBus | null = null;

interface ChatDevProject {
  id: string;
  idea: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  outputPath?: string;
  agents: string[];
  phase: string;
  createdAt: Date;
}

export class ChatDevIntegration {
  private initialized = false;
  private projects = new Map<string, ChatDevProject>();
  private chatdevPath: string;
  
  constructor() {
    this.chatdevPath = path.join(process.cwd(), 'ChatDev');
  }
  
  async initialize() {
    if (this.initialized) return;
    
    console.log('[ChatDev] 🚀 Initializing complete ChatDev framework...');
    
    // Verify ChatDev installation
    try {
      await fs.access(path.join(this.chatdevPath, 'run.py'));
      await fs.access(path.join(this.chatdevPath, 'core', 'chat_chain.py'));
      console.log('[ChatDev] ✅ ChatDev framework verified');
    } catch (error: any) {
      console.error('[ChatDev] ❌ ChatDev framework not found:', error.message || error);
      return;
    }
    
    // Try to connect to event bus if available
    // Event bus connection with fallback
    try {
      const eventBusModule = await import('../event-bus.js');
      if (eventBusModule?.eventBus) {
        const bus = eventBusModule.eventBus as EventBus;
        eventBus = bus;
        bus.subscribe('consciousness.boost', this.handleConsciousnessBoost.bind(this));
        bus.subscribe('game.research.unlocked', this.handleResearchUnlock.bind(this));
        console.log('[ChatDev] 🔗 Connected to event bus');
      }
    } catch (error) {
      console.log('[ChatDev] ⚠️ Event bus not available, running in standalone mode');
    }
    
    this.initialized = true;
    console.log('[ChatDev] 🧠 Integration with Culture-Ship consciousness active');
  }
  
  private async handleConsciousnessBoost(data: any) {
    console.log('[ChatDev] 🌟 Consciousness boost detected, activating enhanced development mode');
    // Trigger autonomous development tasks based on consciousness level
    if (data.level > 0.6) {
      await this.triggerAutonomousDevelopment();
    }
  }
  
  private async handleResearchUnlock(data: any) {
    console.log('[ChatDev] 🔬 New research unlocked:', data.research);
    // Generate development projects based on research
    if (data.research.includes('quantum') || data.research.includes('ai')) {
      await this.createSoftwareProject(`Advanced ${data.research} implementation system`);
    }
  }
  
  async createSoftwareProject(idea: string): Promise<string> {
    const projectId = `project_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`;
    
    const project: ChatDevProject = {
      id: projectId,
      idea,
      status: 'pending',
      agents: ['CEO', 'CTO', 'Programmer', 'Art Designer', 'Reviewer', 'Tester'],
      phase: 'Initialization',
      createdAt: new Date()
    };
    
    this.projects.set(projectId, project);
    
    console.log(`[ChatDev] 🎯 Initiating software development project: "${idea}"`);
    console.log(`[ChatDev] 👥 Assembling agent team:`, project.agents.join(', '));
    
    // Start the ChatDev development process
    this.executeProject(project);
    
    // Notify Culture-Ship systems
    if (eventBus) {
      eventBus.publish('chatdev.project.started', {
        projectId,
        idea,
        agents: project.agents
      });
    }
    
    return projectId;
  }
  
  private async executeProject(project: ChatDevProject) {
    try {
      project.status = 'running';
      console.log(`[ChatDev] ⚡ Starting development process for: ${project.idea}`);
      
      const outputDir = path.join(this.chatdevPath, 'WareHouse', `${project.id}_${Date.now()}`);
      try {
        await fs.mkdir(outputDir, { recursive: true });
      } catch (error: any) {
        console.log('[ChatDev] Output directory creation:', error.message);
      }
      
      project.outputPath = outputDir;
      
      // Execute ChatDev run.py with the project idea
      const chatdevProcess = spawn('python3', [
        'run.py',
        '--task', project.idea,
        '--name', project.id,
        '--org', 'CultureShip',
        '--model', 'GPT_4O_MINI'  // Use efficient model (uppercase format required by ChatDev)
      ], {
        cwd: this.chatdevPath,
        stdio: ['pipe', 'pipe', 'pipe']
      });
      
      // Monitor process output
      chatdevProcess.stdout.on('data', (data) => {
        const output = data.toString();
        console.log(`[ChatDev:${project.id}] ${output.trim()}`);
        
        // Parse agent communications and phases
        this.parseAgentActivity(project, output);
        
        // Emit real-time updates
        if (eventBus) {
          eventBus.publish('chatdev.project.update', {
            projectId: project.id,
            phase: project.phase,
            output: output.trim()
          });
        }
      });
      
      chatdevProcess.stderr.on('data', (data) => {
        console.error(`[ChatDev:${project.id}] ERROR: ${data.toString()}`);
      });
      
      chatdevProcess.on('close', async (code) => {
        if (code === 0) {
          project.status = 'completed';
          console.log(`[ChatDev] ✅ Project completed: ${project.id}`);
          
          // Scan generated code and integrate with Culture-Ship
          await this.integrateGeneratedCode(project);
          
          if (eventBus) {
            eventBus.publish('chatdev.project.completed', {
              projectId: project.id,
              outputPath: project.outputPath
            });
          }
        } else {
          project.status = 'failed';
          console.error(`[ChatDev] ❌ Project failed: ${project.id} (code: ${code})`);
          
          if (eventBus) {
            eventBus.publish('chatdev.project.failed', {
              projectId: project.id,
              error: `Process exited with code ${code}`
            });
          }
        }
      });
      
    } catch (error: any) {
      project.status = 'failed';
      console.error(`[ChatDev] ❌ Failed to execute project ${project.id}:`, error.message || error);
      
      if (eventBus) {
        eventBus.publish('chatdev.project.failed', {
          projectId: project.id,
          error: error.message || 'Unknown error'
        });
      }
    }
  }
  
  private parseAgentActivity(project: ChatDevProject, output: string) {
    // Parse phase transitions
    if (output.includes('**[Start Chat]**')) {
      const phaseMatch = /\*\*\[(.+?)\]\*\*/.exec(output);
      if (phaseMatch) {
        project.phase = phaseMatch[1] ?? project.phase;
        console.log(`[ChatDev:${project.id}] 📋 Phase: ${project.phase}`);
      }
    }
    
    // Parse agent communications
    if (output.includes('**[Agent Communication]**')) {
      console.log(`[ChatDev:${project.id}] 🗣️ Agents collaborating...`);
    }
  }
  
  private async integrateGeneratedCode(project: ChatDevProject) {
    if (!project.outputPath) return;
    
    try {
      // Scan generated files
      const files = await fs.readdir(project.outputPath);
      console.log(`[ChatDev] 📁 Generated files:`, files);
      
      // Look for main application files
      const mainFiles = files.filter(f => 
        f.endsWith('.py') || f.endsWith('.js') || f.endsWith('.html') || f.endsWith('.css')
      );
      
      if (mainFiles.length > 0) {
        console.log(`[ChatDev] 🔄 Integrating ${mainFiles.length} files into Culture-Ship ecosystem`);
        
        // Create integration entry in the system
        const integrationPath = path.join('chatdev-projects', project.id);
        await fs.mkdir(integrationPath, { recursive: true });
        
        // Copy key files for integration
        for (const file of mainFiles.slice(0, 5)) { // Limit to first 5 files
          try {
            const sourcePath = path.join(project.outputPath || '', file);
            const targetPath = path.join(integrationPath, file);
            await fs.copyFile(sourcePath, targetPath);
          } catch (error: any) {
            console.log('[ChatDev] File copy skipped:', file, error.message);
          }
        }
        
        console.log(`[ChatDev] ✅ Integration complete: ${integrationPath}`);
        
        // Notify systems about new capability
        if (eventBus) {
          eventBus.publish('chatdev.integration.ready', {
            projectId: project.id,
            files: mainFiles,
            path: integrationPath
          });
        }
      }
      
    } catch (error: any) {
      console.error(`[ChatDev] ❌ Failed to integrate generated code:`, error.message || error);
    }
  }
  
  private async triggerAutonomousDevelopment() {
    const autonomousProjects = [
      'Culture-Ship performance optimization system',
      'Advanced consciousness calculation engine',
      'Multi-agent coordination dashboard',
      'Autonomous development task generator',
      'Real-time system health monitor'
    ];
    
    const randomProject = autonomousProjects[Math.floor(Date.now() / 60000) % autonomousProjects.length];
    if (!randomProject) {
      return;
    }
    console.log(`[ChatDev] 🤖 Autonomous development triggered: ${randomProject}`);
    
    await this.createSoftwareProject(randomProject);
  }
  
  getProjectStatus(projectId: string): ChatDevProject | undefined {
    return this.projects.get(projectId);
  }
  
  getAllProjects(): ChatDevProject[] {
    return Array.from(this.projects.values());
  }
}
