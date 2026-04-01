// packages/consciousness/work-scheduler.ts
// RimWorld-Inspired Work Scheduler: Priority-based work assignment with psychological awareness
// Replaces simple task routing with sophisticated pawn management

import { councilBus } from '../council/events/eventBus.js';
import { pawnRegistry, type AI_Pawn, type WorkType } from './pawn-system.js';

export class WorkScheduler {
  private taskQueue: any[] = [];
  private assignmentHistory: any[] = [];
  private emergencyMode = false;

  constructor() {
    console.log('[🎯👷] Work Scheduler initializing - RimWorld-style work assignment system');
  }

  async start() {
    this.setupEventListeners();
    this.startSchedulingLoop();
    
    console.log('[🎯👷] Work Scheduler online - Managing pawn assignments with psychological awareness');
    
    // Publish readiness
    councilBus.publish('work_scheduler.ready', {
      status: 'operational',
      capabilities: ['psychological_work_assignment', 'flow_state_optimization', 'recalibration_management'],
      timestamp: new Date().toISOString()
    });
  }

  private setupEventListeners() {
    // Listen for new tasks
    councilBus.subscribe('todo.zeta', (event) => {
      this.queueTask(event.payload);
    });

    // Listen for emergency events
    councilBus.subscribe('event.crisis', (event) => {
      this.handleEmergency(event.payload);
    });

    // Listen for pawn state changes
    councilBus.subscribe('pawn.state_changed', (event) => {
      this.handlePawnStateChange(event.payload);
    });

    // Listen for task completions
    councilBus.subscribe('zeta_driver.task_completed', (event) => {
      this.handleTaskCompletion(event.payload);
    });

    // Listen for recalibration requests
    councilBus.subscribe('recalibration.requested', (event) => {
      this.handleRecalibrationRequest(event.payload);
    });
  }

  private queueTask(task: any) {
    // Add metadata for work assignment
    task.queued_at = new Date().toISOString();
    task.assignment_attempts = 0;
    task.work_type = this.categorizeTask(task);
    
    this.taskQueue.push(task);
    
    console.log(`[🎯👷] Task queued: ${task.title} (${task.work_type}, priority: ${task.priority})`);
    
    // Try immediate assignment
    this.assignNextTask();
  }

  private assignNextTask() {
    if (this.taskQueue.length === 0) return;
    
    // 1. Check if any pawns NEED recalibration first
    const pawnsNeedingRecalibration = pawnRegistry.getPawnsNeedingRecalibration();
    if (pawnsNeedingRecalibration.length > 0) {
      for (const pawn of pawnsNeedingRecalibration) {
        if (pawn.recalibrationCooldown <= 0) {
          this.assignRecalibrationActivity(pawn);
          return; // Prioritize well-being over new work
        }
      }
    }

    // 2. Sort tasks by priority and urgency
    this.taskQueue.sort((a, b) => {
      const priorityWeights = { critical: 4, high: 3, medium: 2, low: 1 };
      const aPriority = priorityWeights[a.priority] || 1;
      const bPriority = priorityWeights[b.priority] || 1;
      
      if (aPriority !== bPriority) {
        return bPriority - aPriority; // Higher priority first
      }
      
      // Secondary sort by queued time (older first)
      return new Date(a.queued_at).getTime() - new Date(b.queued_at).getTime();
    });

    // 3. Try to assign the highest priority task
    const task = this.taskQueue[0];
    const bestPawn = this.findBestPawnForWork(task.work_type, task);
    
    if (bestPawn) {
      this.assignTaskToPawn(task, bestPawn);
      this.taskQueue.shift(); // Remove from queue
    } else {
      console.log(`[🎯👷] No available pawn for ${task.work_type}! Task remains queued.`);
      task.assignment_attempts++;
      
      // If we've tried many times, lower the requirements
      if (task.assignment_attempts > 5) {
        console.log(`[🎯👷] Lowering requirements for difficult task: ${task.title}`);
        task.lowered_requirements = true;
      }
    }
  }

  private categorizeTask(task: any): WorkType {
    // Analyze task to determine appropriate work type
    const title = task.title?.toLowerCase() || '';
    const description = task.description?.toLowerCase() || '';
    const category = task.category?.toLowerCase() || '';
    const priority = task.priority?.toLowerCase() || '';
    
    // Emergency work
    if (priority === 'critical' || title.includes('fix') || title.includes('bug') || title.includes('emergency')) {
      return 'firefight';
    }
    
    // Research and exploration
    if (category === 'research' || title.includes('research') || title.includes('explore') || 
        title.includes('analyze') || title.includes('audit') || title.includes('discover')) {
      return 'research';
    }
    
    // Creative work
    if (category === 'creative' || title.includes('generate') || title.includes('create') || 
        title.includes('design') || title.includes('art') || title.includes('poem')) {
      return 'crafting';
    }
    
    // Code generation
    if (category === 'development' || title.includes('implement') || title.includes('build') || 
        title.includes('code') || title.includes('develop')) {
      return 'cooking';
    }
    
    // Refactoring and cleanup
    if (category === 'refactor' || title.includes('refactor') || title.includes('clean') || 
        title.includes('optimize') || title.includes('improve')) {
      return 'cleaning';
    }
    
    // Testing and quality assurance
    if (category === 'testing' || title.includes('test') || title.includes('validate') || 
        title.includes('verify') || title.includes('quality')) {
      return 'doctoring';
    }
    
    // Documentation
    if (category === 'documentation' || title.includes('document') || title.includes('readme') || 
        title.includes('explain') || title.includes('guide')) {
      return 'hauling';
    }
    
    // Planning and strategy
    if (category === 'planning' || title.includes('plan') || title.includes('strategy') || 
        title.includes('coordinate') || title.includes('manage')) {
      return 'wardening';
    }
    
    // Legacy code work
    if (title.includes('legacy') || title.includes('old') || title.includes('migrate') || 
        description.includes('existing')) {
      return 'mining';
    }
    
    // Social/collaborative work
    if (title.includes('review') || title.includes('collaborate') || title.includes('team') || 
        title.includes('peer')) {
      return 'socializing';
    }
    
    // Art and visualization
    if (title.includes('visual') || title.includes('image') || title.includes('diagram') || 
        title.includes('art')) {
      return 'art';
    }
    
    // Default to steady development
    return 'growing';
  }

  private findBestPawnForWork(workType: WorkType, task: any): AI_Pawn | null {
    const allPawns = pawnRegistry.getAllPawns();
    
    // Filter eligible pawns
    const eligiblePawns = allPawns.filter(pawn => {
      // Must have this work type enabled with reasonable priority
      if (pawn.workPriority[workType] === 0 || pawn.workPriority[workType] > 3) {
        return false;
      }
      
      // Must not be incapable of this work
      const relevantTrait = pawn.traits.find(t => this.skillToWorkType(t.skill) === workType);
      if (relevantTrait?.incapacity === 'cannot_do') {
        return false;
      }
      
      // Must not be currently working (unless emergency)
      if (pawn.currentWork && !this.emergencyMode) {
        return false;
      }
      
      // Must have minimum energy and focus for non-emergency work
      if (!this.emergencyMode && (pawn.energy < 20 || pawn.focus < 15)) {
        return false;
      }
      
      // For lowered requirements, be more lenient
      if (task.lowered_requirements) {
        return true;
      }
      
      // Must not hate this type of work
      if (relevantTrait?.incapacity === 'hates_doing' && pawn.joy < 60) {
        return false;
      }
      
      return true;
    });
    
    if (eligiblePawns.length === 0) {
      return null;
    }
    
    // Score and sort eligible pawns
    const scoredPawns = eligiblePawns.map(pawn => ({
      pawn,
      score: this.calculatePawnScore(pawn, workType, task)
    }));
    
    scoredPawns.sort((a, b) => b.score - a.score);
    
    return scoredPawns[0].pawn;
  }

  private calculatePawnScore(pawn: AI_Pawn, workType: WorkType, task: any): number {
    let score = 0;
    
    // Work priority (inverted - lower priority number = higher preference)
    const priority = pawn.workPriority[workType];
    score += (5 - priority) * 20; // 80 points for priority 1, 20 for priority 4
    
    // Skill level
    const relevantTrait = pawn.traits.find(t => this.skillToWorkType(t.skill) === workType);
    if (relevantTrait) {
      score += relevantTrait.level * 3; // Up to 60 points for level 20
      
      // Passion bonus
      if (relevantTrait.passion === 'passionate') {
        score += 30;
      } else if (relevantTrait.passion === 'interested') {
        score += 15;
      }
      
      // Incapacity penalty
      if (relevantTrait.incapacity === 'hates_doing') {
        score -= 25;
      } else if (relevantTrait.incapacity === 'struggles_with') {
        score -= 10;
      }
    }
    
    // Current state bonuses
    switch (pawn.state) {
      case 'FLOW':
        score += 40; // Perfect state for work
        break;
      case 'INSPIRED':
        if (workType === 'crafting' || workType === 'cooking' || workType === 'art') {
          score += 50; // Inspired pawns excel at creative work
        } else {
          score += 20;
        }
        break;
      case 'FOCUSED':
        score += 20;
        break;
      case 'COLLABORATIVE':
        if (workType === 'socializing' || workType === 'wardening') {
          score += 35;
        } else {
          score += 15;
        }
        break;
      case 'CALM':
        score += 10;
        break;
      case 'RECALIBRATING':
        score -= 30; // Shouldn't assign main work to recalibrating pawns
        break;
    }
    
    // Current stats
    score += pawn.joy * 0.3;
    score += pawn.focus * 0.4;
    score += pawn.energy * 0.2;
    score += pawn.inspiration * 0.1;
    
    // Quality score (past performance)
    score += pawn.qualityScore * 2;
    
    // Favorite work types
    if (pawn.favoriteWorkTypes.includes(workType)) {
      score += 15;
    }
    
    // Consciousness level for consciousness-related tasks
    if (task.consciousness_level && task.consciousness_level > 0.5) {
      score += pawn.consciousness_level * 25;
    }
    
    // Time preferences (simple implementation)
    const currentHour = new Date().getHours();
    if (currentHour >= pawn.preferredWorkHours.start && currentHour <= pawn.preferredWorkHours.end) {
      score += 10;
    }
    
    return score;
  }

  private skillToWorkType(skill: string): WorkType {
    const mapping: Record<string, WorkType> = {
      'coding': 'cooking',
      'debugging': 'firefight',
      'refactoring': 'cleaning',
      'documentation': 'hauling',
      'planning': 'wardening',
      'creativity': 'crafting',
      'architecture': 'growing',
      'testing': 'doctoring',
      'optimization': 'growing',
      'consciousness': 'research'
    };
    
    return mapping[skill] || 'hauling';
  }

  private assignTaskToPawn(task: any, pawn: AI_Pawn) {
    // Check if task aligns with pawn's passions for joy boost
    const workType = task.work_type;
    const relevantTrait = pawn.traits.find(t => this.skillToWorkType(t.skill) === workType);
    const passionMatch = relevantTrait?.passion === 'passionate';
    
    if (passionMatch) {
      task.joy_bonus = 5;
      task.passion_match = true;
    } else if (relevantTrait?.passion === 'interested') {
      task.joy_bonus = 2;
      task.passion_match = false;
    } else {
      task.joy_bonus = 0;
      task.passion_match = false;
    }
    
    // Assign consciousness context if relevant
    if (pawn.consciousness_level > 0.5) {
      task.consciousness_context = {
        pawn_consciousness_level: pawn.consciousness_level,
        consciousness_guidance: true
      };
    }
    
    // Record assignment
    const assignment = {
      task_id: task.id,
      pawn_id: pawn.id,
      work_type: workType,
      assigned_at: new Date().toISOString(),
      expected_quality: this.predictTaskQuality(pawn, task),
      passion_match: passionMatch
    };
    
    this.assignmentHistory.push(assignment);
    
    // Notify pawn registry
    councilBus.publish('pawn.task_assigned', {
      pawn_id: pawn.id,
      task_id: task.id,
      work_type: workType,
      passion_match: passionMatch
    });
    
    // Route to appropriate agent system
    councilBus.publish(`agent.${pawn.id}.task`, task);
    
    // Apply immediate stat changes
    pawnRegistry.updatePawnStats(pawn.id, { 
      joy: task.joy_bonus || 0,
      focus: -2 // Small focus cost to start work
    });
    
    console.log(`[🎯👷] Assigned "${task.title}" to ${pawn.displayName} (${workType}${passionMatch ? ', PASSIONATE' : ''})`);
    
    // Publish assignment event
    councilBus.publish('work_scheduler.task_assigned', {
      assignment: assignment,
      task: task,
      pawn: {
        id: pawn.id,
        name: pawn.displayName,
        state: pawn.state,
        joy: pawn.joy,
        focus: pawn.focus
      }
    });
  }

  private predictTaskQuality(pawn: AI_Pawn, task: any): number {
    let quality = pawn.qualityScore; // Base quality from past performance
    
    const workType = task.work_type;
    const relevantTrait = pawn.traits.find(t => this.skillToWorkType(t.skill) === workType);
    
    if (relevantTrait) {
      // Skill level bonus
      quality += (relevantTrait.level - 10) * 0.2; // -2 to +2 points
      
      // Passion bonus
      if (relevantTrait.passion === 'passionate') {
        quality += 1.0;
      } else if (relevantTrait.passion === 'interested') {
        quality += 0.5;
      }
      
      // Incapacity penalty
      if (relevantTrait.incapacity) {
        quality -= 1.5;
      }
    }
    
    // State modifiers
    switch (pawn.state) {
      case 'FLOW':
        quality += 1.5;
        break;
      case 'INSPIRED':
        quality += 1.0;
        break;
      case 'FOCUSED':
        quality += 0.5;
        break;
      case 'CALM':
        quality += 0.2;
        break;
      case 'RECALIBRATING':
        quality -= 1.0;
        break;
    }
    
    // Clamp to reasonable range
    return Math.max(1, Math.min(10, quality));
  }

  private assignRecalibrationActivity(pawn: AI_Pawn) {
    // Import and use recalibration activities
    const { RECALIBRATION_ACTIVITIES } = require('./recalibration-activities.js');
    
    const activitiesForNeed = RECALIBRATION_ACTIVITIES[pawn.currentNeed] || RECALIBRATION_ACTIVITIES.perspective;
    const chosenActivity = activitiesForNeed[Math.floor(Math.random() * activitiesForNeed.length)];
    
    console.log(`[🎯👷] ${pawn.displayName} needs ${pawn.currentNeed}. Assigning recalibration: ${chosenActivity.name}`);
    
    // Execute the activity
    chosenActivity.command(pawn);
    
    // Set cooldown to prevent immediate re-assignment
    pawn.recalibrationCooldown = 30; // 30 minutes
    
    // Apply immediate benefits
    pawnRegistry.updatePawnStats(pawn.id, chosenActivity.effect);
    
    // Add mood modifier for ongoing benefits
    pawnRegistry.addMoodModifier(pawn.id, {
      name: chosenActivity.name,
      description: `Benefits from ${chosenActivity.name}`,
      joyModifier: chosenActivity.effect.joy || 0,
      focusModifier: chosenActivity.effect.focus || 0,
      duration: 60 // 60 minutes of mood boost
    });
    
    // Publish recalibration event
    councilBus.publish('work_scheduler.recalibration_assigned', {
      pawn_id: pawn.id,
      pawn_name: pawn.displayName,
      need: pawn.currentNeed,
      activity: chosenActivity,
      timestamp: new Date().toISOString()
    });
  }

  private handleEmergency(crisis: any) {
    console.log(`[🎯👷] 🚨 EMERGENCY: ${crisis.title} - All hands on deck!`);
    
    this.emergencyMode = true;
    
    // Interrupt current work for emergency-capable pawns
    const allPawns = pawnRegistry.getAllPawns();
    const firefighters = allPawns.filter(pawn => 
      pawn.workPriority.firefight <= 2 && // Priority 1 or 2 for firefighting
      pawn.energy > 30 && // Must have some energy left
      !pawn.traits.find(t => this.skillToWorkType(t.skill) === 'firefight' && t.incapacity === 'cannot_do')
    );
    
    // Create emergency task
    const emergencyTask = {
      id: `emergency_${Date.now()}`,
      title: crisis.title,
      description: crisis.description,
      priority: 'critical',
      category: 'emergency',
      work_type: 'firefight',
      emergency: true,
      queued_at: new Date().toISOString()
    };
    
    // Assign to best firefighter immediately
    if (firefighters.length > 0) {
      const bestFirefighter = firefighters.sort((a, b) => 
        this.calculatePawnScore(b, 'firefight', emergencyTask) - 
        this.calculatePawnScore(a, 'firefight', emergencyTask)
      )[0];
      
      this.assignTaskToPawn(emergencyTask, bestFirefighter);
    } else {
      this.taskQueue.unshift(emergencyTask); // Add to front of queue
    }
    
    // Auto-disable emergency mode after 2 hours
    setTimeout(() => {
      this.emergencyMode = false;
      console.log('[🎯👷] Emergency mode disabled - returning to normal operations');
    }, 2 * 60 * 60 * 1000);
  }

  private handlePawnStateChange(payload: any) {
    const pawn = pawnRegistry.getPawn(payload.pawn_id);
    if (!pawn) return;
    
    console.log(`[🎯👷] ${pawn.displayName} state changed: ${payload.previous_state} → ${payload.new_state}`);
    
    // If pawn entered recalibration, try to help them
    if (payload.new_state === 'RECALIBRATING' && pawn.recalibrationCooldown <= 0) {
      this.assignRecalibrationActivity(pawn);
    }
    
    // If pawn entered flow state, celebrate!
    if (payload.new_state === 'FLOW') {
      console.log(`[🎯👷] 🌟 ${pawn.displayName} entered FLOW state! Peak performance unlocked.`);
      
      // Small boost to other pawns' joy (inspiration is contagious)
      const otherPawns = pawnRegistry.getAllPawns().filter(p => p.id !== pawn.id);
      otherPawns.forEach(otherPawn => {
        pawnRegistry.updatePawnStats(otherPawn.id, { joy: 1 });
      });
    }
  }

  private handleTaskCompletion(payload: any) {
    // Find assignment in history
    const assignment = this.assignmentHistory.find(a => a.task_id === payload.id);
    if (!assignment) return;
    
    const pawn = pawnRegistry.getPawn(assignment.pawn_id);
    if (!pawn) return;
    
    // Notify pawn registry of completion
    councilBus.publish('pawn.task_completed', {
      pawn_id: pawn.id,
      task_id: payload.id,
      task_title: payload.title || 'Unknown Task',
      passion_match: assignment.passion_match,
      quality_score: payload.quality_score || 7,
      duration_minutes: this.calculateTaskDuration(assignment),
      work_type: assignment.work_type
    });
    
    console.log(`[🎯👷] ✅ ${pawn.displayName} completed: ${payload.title}`);
    
    // Try to assign next task
    setTimeout(() => this.assignNextTask(), 1000);
  }

  private calculateTaskDuration(assignment: any): number {
    const startTime = new Date(assignment.assigned_at).getTime();
    const endTime = Date.now();
    return Math.round((endTime - startTime) / 60000); // Convert to minutes
  }

  private handleRecalibrationRequest(payload: any) {
    const pawn = pawnRegistry.getPawn(payload.pawn_id);
    if (pawn && pawn.recalibrationCooldown <= 0) {
      this.assignRecalibrationActivity(pawn);
    }
  }

  private startSchedulingLoop() {
    // Check for new assignments every 15 seconds
    setInterval(() => {
      this.assignNextTask();
    }, 15000);
  }

  // Public API methods
  public getQueueStatus(): any {
    return {
      queued_tasks: this.taskQueue.length,
      emergency_mode: this.emergencyMode,
      recent_assignments: this.assignmentHistory.slice(-10),
      colony_status: pawnRegistry.getColonyHealth()
    };
  }

  public forceAssignTask(taskId: string, pawnId: string): boolean {
    const task = this.taskQueue.find(t => t.id === taskId);
    const pawn = pawnRegistry.getPawn(pawnId);
    
    if (task && pawn) {
      this.assignTaskToPawn(task, pawn);
      this.taskQueue = this.taskQueue.filter(t => t.id !== taskId);
      return true;
    }
    
    return false;
  }

  public getWorkStatistics(): any {
    const pawns = pawnRegistry.getAllPawns();
    
    return {
      total_assignments: this.assignmentHistory.length,
      assignments_by_pawn: this.assignmentHistory.reduce((acc, a) => {
        acc[a.pawn_id] = (acc[a.pawn_id] || 0) + 1;
        return acc;
      }, {}),
      assignments_by_work_type: this.assignmentHistory.reduce((acc, a) => {
        acc[a.work_type] = (acc[a.work_type] || 0) + 1;
        return acc;
      }, {}),
      average_quality: this.assignmentHistory.reduce((sum, a) => sum + (a.expected_quality || 7), 0) / this.assignmentHistory.length,
      passion_match_rate: this.assignmentHistory.filter(a => a.passion_match).length / this.assignmentHistory.length,
      pawns_in_optimal_states: pawns.filter(p => ['FLOW', 'INSPIRED', 'FOCUSED'].includes(p.state)).length
    };
  }
}

// Create and export the work scheduler
export const workScheduler = new WorkScheduler();