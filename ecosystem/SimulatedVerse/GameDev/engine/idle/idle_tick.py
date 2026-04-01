#!/usr/bin/env python3
"""
Idle/Incremental Game Engine - Literal Game Mechanics
Bridges symbolic idle breath to actual tick system with prestige and automation
"""

import json
import time
import math
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class Resource:
    name: str
    amount: float = 0.0
    generation_per_second: float = 0.0
    max_amount: Optional[float] = None
    visible: bool = True

@dataclass
class Generator:
    id: str
    name: str
    base_cost: float
    cost_scaling: float = 1.15
    base_production: float = 1.0
    owned: int = 0
    unlocked: bool = True
    resource_type: str = "energy"

@dataclass
class Upgrade:
    id: str
    name: str
    description: str
    cost: float
    cost_resource: str = "energy"
    purchased: bool = False
    effect_type: str = "multiplier"  # multiplier, additive, unlock
    effect_value: float = 2.0
    target: str = "all_generators"

class IdleGameEngine:
    def __init__(self):
        self.resources: Dict[str, Resource] = {}
        self.generators: Dict[str, Generator] = {}
        self.upgrades: Dict[str, Upgrade] = {}
        self.game_stats = {
            "total_clicks": 0,
            "total_generated": 0.0,
            "game_start_time": time.time(),
            "prestige_count": 0,
            "offline_time": 0.0
        }
        self.automation_unlocked = False
        self.prestige_currency = 0.0
        
        self._initialize_base_game()
        print("[IdleEngine] Initialized with base resources and generators")

    def _initialize_base_game(self):
        """Set up the basic idle game resources and generators"""
        # Base resources
        self.resources = {
            "energy": Resource("Energy", 0.0, 0.0),
            "materials": Resource("Materials", 0.0, 0.0, visible=False),
            "research": Resource("Research Points", 0.0, 0.0, visible=False),
            "nanobots": Resource("Nanobots", 0.0, 0.0, visible=False)
        }
        
        # Base generators
        self.generators = {
            "manual_click": Generator("manual_click", "Manual Clicking", 0, 0, 1.0, 1, True),
            "solar_panel": Generator("solar_panel", "Solar Panel", 10, 1.15, 1.0, 0, True),
            "wind_turbine": Generator("wind_turbine", "Wind Turbine", 100, 1.15, 8.0, 0, False),
            "fusion_reactor": Generator("fusion_reactor", "Fusion Reactor", 1000, 1.15, 47.0, 0, False),
            "quantum_generator": Generator("quantum_generator", "Quantum Generator", 10000, 1.15, 260.0, 0, False)
        }
        
        # Base upgrades
        self.upgrades = {
            "efficient_clicking": Upgrade("efficient_clicking", "Efficient Clicking", "Double click value", 50, "energy", False, "multiplier", 2.0, "manual_click"),
            "solar_efficiency": Upgrade("solar_efficiency", "Solar Efficiency", "Solar panels 2x faster", 500, "energy", False, "multiplier", 2.0, "solar_panel"),
            "automation_unlock": Upgrade("automation_unlock", "Automation Protocol", "Unlock automated purchasing", 1000, "energy", False, "unlock", 1.0, "automation"),
            "materials_unlock": Upgrade("materials_unlock", "Materials Processing", "Unlock materials production", 2000, "energy", False, "unlock", 1.0, "materials"),
        }

    def tick(self, delta_seconds: float = 1.0):
        """Main game tick - processes resource generation and automation"""
        
        # Generate resources from generators
        for generator_id, generator in self.generators.items():
            if generator.owned > 0:
                production = generator.base_production * generator.owned * delta_seconds
                production *= self._get_generator_multiplier(generator_id)
                
                self.resources[generator.resource_type].amount += production
                self.resources[generator.resource_type].generation_per_second = production / delta_seconds
                self.game_stats["total_generated"] += production
        
        # Apply resource caps
        for resource in self.resources.values():
            if resource.max_amount and resource.amount > resource.max_amount:
                resource.amount = resource.max_amount
        
        # Automation purchasing
        if self.automation_unlocked:
            self._process_automation()
        
        # Check unlock conditions
        self._check_unlocks()
        
        return self._get_game_state()

    def manual_click(self) -> float:
        """Handle manual clicking"""
        click_value = 1.0 * self._get_generator_multiplier("manual_click")
        self.resources["energy"].amount += click_value
        self.game_stats["total_clicks"] += 1
        
        print(f"[IdleEngine] Manual click: +{click_value} energy")
        return click_value

    def purchase_generator(self, generator_id: str, quantity: int = 1) -> bool:
        """Purchase generators"""
        if generator_id not in self.generators:
            return False
        
        generator = self.generators[generator_id]
        if not generator.unlocked:
            return False
        
        total_cost = 0.0
        for i in range(quantity):
            cost = generator.base_cost * (generator.cost_scaling ** (generator.owned + i))
            total_cost += cost
        
        if self.resources[generator.resource_type].amount >= total_cost:
            self.resources[generator.resource_type].amount -= total_cost
            generator.owned += quantity
            print(f"[IdleEngine] Purchased {quantity}x {generator.name} for {total_cost}")
            return True
        
        return False

    def purchase_upgrade(self, upgrade_id: str) -> bool:
        """Purchase upgrades"""
        if upgrade_id not in self.upgrades:
            return False
        
        upgrade = self.upgrades[upgrade_id]
        if upgrade.purchased:
            return False
        
        if self.resources[upgrade.cost_resource].amount >= upgrade.cost:
            self.resources[upgrade.cost_resource].amount -= upgrade.cost
            upgrade.purchased = True
            self._apply_upgrade_effect(upgrade)
            print(f"[IdleEngine] Purchased upgrade: {upgrade.name}")
            return True
        
        return False

    def _apply_upgrade_effect(self, upgrade: Upgrade):
        """Apply upgrade effects"""
        if upgrade.effect_type == "unlock":
            if upgrade.target == "automation":
                self.automation_unlocked = True
            elif upgrade.target == "materials":
                self.resources["materials"].visible = True
                self.generators["material_extractor"] = Generator(
                    "material_extractor", "Material Extractor", 5000, 1.15, 1.0, 0, True, "materials"
                )
        elif upgrade.effect_type == "multiplier":
            # Multiplier effects are applied in _get_generator_multiplier
            pass

    def _get_generator_multiplier(self, generator_id: str) -> float:
        """Calculate total multiplier for a generator"""
        multiplier = 1.0
        
        for upgrade in self.upgrades.values():
            if (upgrade.purchased and upgrade.effect_type == "multiplier" and 
                (upgrade.target == generator_id or upgrade.target == "all_generators")):
                multiplier *= upgrade.effect_value
        
        # Prestige multiplier
        if self.prestige_currency > 0:
            multiplier *= (1.0 + self.prestige_currency * 0.1)
        
        return multiplier

    def _process_automation(self):
        """Handle automated purchasing"""
        for generator_id, generator in self.generators.items():
            if generator.unlocked and generator_id != "manual_click":
                # Try to buy generators automatically if we can afford 10x the cost
                cost = generator.base_cost * (generator.cost_scaling ** generator.owned)
                if self.resources[generator.resource_type].amount >= cost * 10:
                    self.purchase_generator(generator_id, 1)

    def _check_unlocks(self):
        """Check and process unlock conditions"""
        energy = self.resources["energy"].amount
        
        # Unlock generators based on energy thresholds
        if energy >= 50 and not self.generators["wind_turbine"].unlocked:
            self.generators["wind_turbine"].unlocked = True
            print("[IdleEngine] Wind Turbine unlocked!")
        
        if energy >= 5000 and not self.generators["fusion_reactor"].unlocked:
            self.generators["fusion_reactor"].unlocked = True
            print("[IdleEngine] Fusion Reactor unlocked!")
        
        if energy >= 50000 and not self.generators["quantum_generator"].unlocked:
            self.generators["quantum_generator"].unlocked = True
            self.resources["research"].visible = True
            print("[IdleEngine] Quantum Generator unlocked! Research visible!")

    def can_prestige(self) -> bool:
        """Check if prestige is available"""
        return self.resources["energy"].amount >= 1000000  # 1 million energy

    def prestige(self) -> bool:
        """Perform prestige reset"""
        if not self.can_prestige():
            return False
        
        # Calculate prestige currency earned
        energy = self.resources["energy"].amount
        new_prestige = math.floor(math.sqrt(energy / 1000000))
        self.prestige_currency += new_prestige
        self.game_stats["prestige_count"] += 1
        
        # Reset resources and generators
        for resource in self.resources.values():
            resource.amount = 0.0
            resource.generation_per_second = 0.0
        
        for generator in self.generators.values():
            generator.owned = 0
        
        # Reset upgrades (keep some based on prestige)
        for upgrade in self.upgrades.values():
            if upgrade.id not in ["automation_unlock"]:  # Keep automation
                upgrade.purchased = False
        
        print(f"[IdleEngine] Prestige! Earned {new_prestige} prestige currency")
        return True

    def process_offline_time(self, offline_seconds: float):
        """Handle offline progression"""
        if offline_seconds < 60:  # Less than 1 minute, ignore
            return
        
        # Cap offline progression to 24 hours
        offline_seconds = min(offline_seconds, 24 * 3600)
        
        # Calculate offline production (reduced efficiency)
        offline_multiplier = 0.5  # 50% efficiency offline
        offline_ticks = int(offline_seconds)
        
        for _ in range(min(offline_ticks, 3600)):  # Process up to 1 hour of ticks
            self.tick(offline_multiplier)
        
        self.game_stats["offline_time"] += offline_seconds
        print(f"[IdleEngine] Processed {offline_seconds/3600:.1f} hours of offline time")

    def _get_game_state(self) -> Dict[str, Any]:
        """Get current game state"""
        return {
            "resources": {k: {"amount": v.amount, "generation": v.generation_per_second, "visible": v.visible} 
                         for k, v in self.resources.items()},
            "generators": {k: {"owned": v.owned, "unlocked": v.unlocked, "cost": v.base_cost * (v.cost_scaling ** v.owned)} 
                          for k, v in self.generators.items()},
            "upgrades": {k: {"purchased": v.purchased, "cost": v.cost, "name": v.name, "description": v.description} 
                        for k, v in self.upgrades.items()},
            "automation_unlocked": self.automation_unlocked,
            "prestige_currency": self.prestige_currency,
            "can_prestige": self.can_prestige(),
            "stats": self.game_stats.copy()
        }

    def save_game(self, filename: str = "idle_save.json"):
        """Save game state to file"""
        save_data = {
            "game_state": self._get_game_state(),
            "last_save_time": time.time()
        }
        
        with open(filename, 'w') as f:
            json.dump(save_data, f, indent=2)
        
        print(f"[IdleEngine] Game saved to {filename}")

    def load_game(self, filename: str = "idle_save.json") -> bool:
        """Load game state from file"""
        try:
            with open(filename, 'r') as f:
                save_data = json.load(f)
            
            # Process offline time
            offline_time = time.time() - save_data.get("last_save_time", time.time())
            if offline_time > 0:
                self.process_offline_time(offline_time)
            
            print(f"[IdleEngine] Game loaded from {filename}")
            return True
        
        except FileNotFoundError:
            print(f"[IdleEngine] No save file found: {filename}")
            return False
        except Exception as e:
            print(f"[IdleEngine] Error loading save: {e}")
            return False

# Global game instance for easy access
idle_game = IdleGameEngine()

if __name__ == "__main__":
    # Simple CLI test interface
    print("Idle Game Engine Test")
    print("Commands: tick, click, buy <generator>, upgrade <upgrade_id>, prestige, state, quit")
    
    while True:
        cmd = input("> ").strip().lower().split()
        
        if not cmd:
            continue
        
        if cmd[0] == "quit":
            break
        elif cmd[0] == "tick":
            state = idle_game.tick()
            print(f"Energy: {state['resources']['energy']['amount']:.1f} (+{state['resources']['energy']['generation']:.1f}/s)")
        elif cmd[0] == "click":
            value = idle_game.manual_click()
            print(f"Clicked for {value} energy")
        elif cmd[0] == "buy" and len(cmd) > 1:
            success = idle_game.purchase_generator(cmd[1])
            print("Purchased!" if success else "Can't afford or invalid generator")
        elif cmd[0] == "upgrade" and len(cmd) > 1:
            success = idle_game.purchase_upgrade(cmd[1])
            print("Upgraded!" if success else "Can't afford or already purchased")
        elif cmd[0] == "prestige":
            success = idle_game.prestige()
            print("Prestiged!" if success else "Can't prestige yet")
        elif cmd[0] == "state":
            state = idle_game._get_game_state()
            print(json.dumps(state, indent=2))
        else:
            print("Unknown command")