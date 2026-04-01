#!/usr/bin/env python3
"""
🎮 Idler Module - NGU/Melvor-style idle progression
Handles idle bars, jobs, automation queue
"""

import time
import json
import os
from dataclasses import dataclass, asdict
from typing import Dict, List
from datetime import datetime

@dataclass
class IdleJob:
    id: str
    name: str
    progress: float = 0.0
    duration: float = 10.0  # seconds
    xp_reward: int = 1
    resource_rewards: Dict[str, int] = None
    prerequisites: List[str] = None
    
    def __post_init__(self):
        if self.resource_rewards is None:
            self.resource_rewards = {}
        if self.prerequisites is None:
            self.prerequisites = []

@dataclass
class IdleState:
    current_jobs: List[IdleJob]
    completed_jobs: List[str]
    total_xp: int = 0
    idle_multiplier: float = 1.0
    last_update: str = None
    
    def __post_init__(self):
        if self.last_update is None:
            self.last_update = datetime.now().isoformat()

class IdleEngine:
    def __init__(self, state_file=".local/idle_state.json"):
        self.state_file = state_file
        self.state = self.load_state()
        
        # Job definitions
        self.job_definitions = {
            "gather_food": IdleJob(
                id="gather_food",
                name="🍄 Gather Food",
                duration=15.0,
                xp_reward=2,
                resource_rewards={"food": 3}
            ),
            "collect_water": IdleJob(
                id="collect_water", 
                name="💧 Collect Water",
                duration=12.0,
                xp_reward=2,
                resource_rewards={"water": 4}
            ),
            "repair_systems": IdleJob(
                id="repair_systems",
                name="🔧 Repair Systems", 
                duration=30.0,
                xp_reward=5,
                resource_rewards={"energy": 10},
                prerequisites=["gather_food"]
            ),
            "scout_area": IdleJob(
                id="scout_area",
                name="🔍 Scout Area",
                duration=45.0,
                xp_reward=8,
                resource_rewards={"knowledge": 2},
                prerequisites=["collect_water"]
            ),
            "automate_gathering": IdleJob(
                id="automate_gathering",
                name="🤖 Automate Gathering",
                duration=120.0,
                xp_reward=15,
                resource_rewards={"automation": 1},
                prerequisites=["repair_systems", "scout_area"]
            )
        }
    
    def load_state(self) -> IdleState:
        """Load idle state from file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    return IdleState(
                        current_jobs=[IdleJob(**job) for job in data.get('current_jobs', [])],
                        completed_jobs=data.get('completed_jobs', []),
                        total_xp=data.get('total_xp', 0),
                        idle_multiplier=data.get('idle_multiplier', 1.0),
                        last_update=data.get('last_update')
                    )
            except Exception as e:
                print(f"⚠️  Error loading idle state: {e}")
        
        return IdleState(current_jobs=[], completed_jobs=[])
    
    def save_state(self):
        """Save idle state to file"""
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        
        data = {
            'current_jobs': [asdict(job) for job in self.state.current_jobs],
            'completed_jobs': self.state.completed_jobs,
            'total_xp': self.state.total_xp,
            'idle_multiplier': self.state.idle_multiplier,
            'last_update': datetime.now().isoformat()
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def calculate_offline_progress(self):
        """Calculate progress made while offline"""
        if not self.state.last_update:
            return
        
        last_update = datetime.fromisoformat(self.state.last_update.replace('Z', '+00:00'))
        now = datetime.now()
        offline_seconds = (now - last_update).total_seconds()
        
        if offline_seconds > 60:  # More than 1 minute offline
            # Apply offline progress with diminishing returns
            offline_multiplier = min(2.0, 1.0 + (offline_seconds / 3600))  # Max 2x for 1+ hour
            
            for job in self.state.current_jobs:
                if job.progress < 1.0:
                    offline_progress = (offline_seconds / job.duration) * offline_multiplier
                    job.progress = min(1.0, job.progress + offline_progress)
            
            print(f"⏰ Welcome back! You were offline for {offline_seconds/60:.1f} minutes")
            print(f"📈 Offline progress applied with {offline_multiplier:.1f}x multiplier")
    
    def start_job(self, job_id: str) -> bool:
        """Start a new idle job"""
        if job_id not in self.job_definitions:
            print(f"❌ Unknown job: {job_id}")
            return False
        
        job_def = self.job_definitions[job_id]
        
        # Check prerequisites
        for prereq in job_def.prerequisites:
            if prereq not in self.state.completed_jobs:
                print(f"❌ Prerequisite not met: {prereq}")
                return False
        
        # Check if already running
        for job in self.state.current_jobs:
            if job.id == job_id:
                print(f"⚠️  Job {job_id} already running")
                return False
        
        # Start the job
        new_job = IdleJob(**asdict(job_def))
        self.state.current_jobs.append(new_job)
        print(f"▶️  Started job: {new_job.name}")
        return True
    
    def update_progress(self, delta_time: float = 1.0):
        """Update job progress"""
        completed_jobs = []
        
        for job in self.state.current_jobs:
            if job.progress < 1.0:
                # Apply idle multiplier
                progress_delta = (delta_time / job.duration) * self.state.idle_multiplier
                job.progress = min(1.0, job.progress + progress_delta)
                
                # Check if completed
                if job.progress >= 1.0:
                    completed_jobs.append(job)
        
        # Process completed jobs
        for job in completed_jobs:
            self.complete_job(job)
    
    def complete_job(self, job: IdleJob):
        """Complete a job and grant rewards"""
        print(f"✅ Completed: {job.name}")
        print(f"   XP: +{job.xp_reward}")
        
        # Add to completed list
        if job.id not in self.state.completed_jobs:
            self.state.completed_jobs.append(job.id)
        
        # Grant XP
        self.state.total_xp += job.xp_reward
        
        # Grant resources (would integrate with main resource system)
        for resource, amount in job.resource_rewards.items():
            print(f"   {resource}: +{amount}")
        
        # Remove from current jobs
        self.state.current_jobs = [j for j in self.state.current_jobs if j.id != job.id]
        
        # Increase idle multiplier slightly
        self.state.idle_multiplier = min(5.0, self.state.idle_multiplier + 0.1)
    
    def display_status(self):
        """Display current idle status"""
        print("🎮 IDLE STATUS")
        print("=" * 40)
        print(f"Total XP: {self.state.total_xp}")
        print(f"Idle Multiplier: {self.state.idle_multiplier:.1f}x")
        print(f"Completed Jobs: {len(self.state.completed_jobs)}")
        
        print("\n📋 Current Jobs:")
        if not self.state.current_jobs:
            print("   (none)")
        else:
            for job in self.state.current_jobs:
                progress_bar = "█" * int(job.progress * 20) + "░" * (20 - int(job.progress * 20))
                print(f"   {job.name}: [{progress_bar}] {job.progress*100:.1f}%")
        
        print("\n🔓 Available Jobs:")
        for job_id, job_def in self.job_definitions.items():
            if job_id not in [j.id for j in self.state.current_jobs]:
                prereq_met = all(prereq in self.state.completed_jobs for prereq in job_def.prerequisites)
                status = "✅" if prereq_met else "🔒"
                print(f"   {status} {job_def.name} ({job_def.duration}s, {job_def.xp_reward} XP)")
    
    def tick(self):
        """Main idle tick - call this regularly"""
        self.calculate_offline_progress()
        self.update_progress(1.0)  # 1 second progress
        self.save_state()

def main():
    """Interactive idle game loop"""
    engine = IdleEngine()
    
    print("🎮 NuSyQ Idle Engine")
    print("Commands: status, start <job_id>, jobs, quit")
    
    while True:
        engine.tick()
        
        try:
            command = input("\n> ").strip().lower()
            
            if command == "quit":
                break
            elif command == "status":
                engine.display_status()
            elif command == "jobs":
                print("\nAvailable Job IDs:")
                for job_id in engine.job_definitions.keys():
                    print(f"  - {job_id}")
            elif command.startswith("start "):
                job_id = command.split(" ", 1)[1]
                engine.start_job(job_id)
            else:
                print("Unknown command. Try: status, start <job_id>, jobs, quit")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except EOFError:
            break
        
        time.sleep(0.1)

if __name__ == "__main__":
    main()