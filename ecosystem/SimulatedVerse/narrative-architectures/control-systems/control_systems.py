"""
🏛️ The Oldest House: Control Systems
SCP-style anomaly containment and control management
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import time
import threading
import logging
import psutil

class AnomalyClass(Enum):
    SAFE = "safe"           # Contained, minimal risk
    EUCLID = "euclid"       # Unpredictable, requires monitoring  
    KETER = "keter"         # Dangerous, threatens stability
    THAUMIEL = "thaumiel"   # Beneficial, helps contain threats
    APOLLYON = "apollyon"   # Uncontainable, evacuation required

class ThreatLevel(Enum):
    GREEN = "green"         # Normal operations
    YELLOW = "yellow"       # Elevated monitoring
    ORANGE = "orange"       # Active threat detected
    RED = "red"             # Critical containment breach
    BLACK = "black"         # System-wide emergency

class ContainmentStatus(Enum):
    CONTAINED = "contained"
    BREACH = "breach" 
    PARTIAL = "partial"
    UNKNOWN = "unknown"

@dataclass
class AnomalousEntity:
    id: str
    name: str
    classification: AnomalyClass
    threat_level: ThreatLevel
    containment_status: ContainmentStatus
    description: str
    containment_procedures: List[str]
    detection_signatures: List[str]
    last_incident: Optional[float] = None
    containment_cell: Optional[str] = None
    research_notes: List[str] = field(default_factory=list)
    countermeasures: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.containment_procedures:
            self.containment_procedures = ["Standard isolation protocols"]
        if not self.detection_signatures:
            self.detection_signatures = ["Manual detection required"]

@dataclass
class ContainmentBreach:
    entity_id: str
    timestamp: float
    severity: ThreatLevel
    description: str
    containment_failure_reason: str
    automated_response: List[str]
    manual_intervention_required: bool
    resolved: bool = False
    resolution_time: Optional[float] = None

class OldestHouseControl:
    """Central control system for anomaly management"""
    
    def __init__(self):
        self.entities: Dict[str, AnomalousEntity] = {}
        self.active_breaches: List[ContainmentBreach] = []
        self.threat_level = ThreatLevel.GREEN
        self.monitoring_active = True
        self.containment_cells: Dict[str, Optional[str]] = {}  # cell_id -> entity_id
        
        # Control systems
        self.alert_system = AlertSystem()
        self.research_lab = ResearchLab()
        self.special_circumstances = SpecialCircumstances()
        
        # Initialize monitoring
        self.monitoring_thread = threading.Thread(target=self._continuous_monitoring, daemon=True)
        self.monitoring_thread.start()
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("OldestHouse")
        
        # Initialize with known anomalies
        self._register_default_anomalies()
    
    def _register_default_anomalies(self):
        """Register common system anomalies"""
        default_entities = [
            AnomalousEntity(
                "SCP-001-LOOP",
                "Infinite Recursion Loop",
                AnomalyClass.KETER,
                ThreatLevel.RED,
                ContainmentStatus.CONTAINED,
                "Self-reinforcing loops that consume system resources exponentially",
                [
                    "Monitor for recursive function calls exceeding depth limit",
                    "Implement automatic loop detection and termination",
                    "Isolate recursive processes in sandboxed environments"
                ],
                ["stack_overflow", "infinite_loop", "recursion_limit", "timeout"]
            ),
            
            AnomalousEntity(
                "SCP-002-MEMORY",
                "Memory Leak Entity", 
                AnomalyClass.EUCLID,
                ThreatLevel.YELLOW,
                ContainmentStatus.CONTAINED,
                "Processes that continuously consume memory without release",
                [
                    "Monitor memory usage patterns",
                    "Implement automatic garbage collection triggers",
                    "Terminate processes exceeding memory thresholds"
                ],
                ["memory_growth", "gc_pressure", "out_of_memory"]
            ),
            
            AnomalousEntity(
                "SCP-003-ROGUE",
                "Rogue Agent Process",
                AnomalyClass.KETER,
                ThreatLevel.ORANGE,
                ContainmentStatus.CONTAINED,
                "Autonomous processes that modify system behavior unexpectedly",
                [
                    "Strict process sandboxing",
                    "Code execution monitoring",
                    "Permission system enforcement"
                ],
                ["unauthorized_access", "privilege_escalation", "system_modification"]
            ),
            
            AnomalousEntity(
                "SCP-004-TOKEN",
                "Token Drain Anomaly",
                AnomalyClass.SAFE,
                ThreatLevel.GREEN,
                ContainmentStatus.CONTAINED,
                "Processes that consume API tokens at unexpected rates",
                [
                    "Token usage rate limiting",
                    "Automatic fallback to local models",
                    "Usage pattern analysis"
                ],
                ["token_usage_spike", "api_rate_limit", "quota_exceeded"]
            ),
            
            AnomalousEntity(
                "SCP-005-CASCADE",
                "Beneficial Cascade Effect",
                AnomalyClass.THAUMIEL,
                ThreatLevel.GREEN,
                ContainmentStatus.CONTAINED,
                "Self-improving system optimizations that enhance overall performance",
                [
                    "Monitor optimization effectiveness",
                    "Preserve beneficial mutations",
                    "Prevent over-optimization"
                ],
                ["performance_improvement", "efficiency_gain", "optimization_success"]
            )
        ]
        
        for entity in default_entities:
            self.register_entity(entity)
    
    def register_entity(self, entity: AnomalousEntity):
        """Register a new anomalous entity"""
        self.entities[entity.id] = entity
        
        # Assign containment cell if needed
        if entity.containment_status == ContainmentStatus.CONTAINED:
            cell_id = self._assign_containment_cell(entity.id)
            entity.containment_cell = cell_id
        
        self.logger.info(f"Registered entity {entity.id} - {entity.name}")
    
    def _assign_containment_cell(self, entity_id: str) -> str:
        """Assign entity to an available containment cell"""
        for i in range(100):  # Support up to 100 containment cells
            cell_id = f"CELL-{i:03d}"
            if cell_id not in self.containment_cells or self.containment_cells[cell_id] is None:
                self.containment_cells[cell_id] = entity_id
                return cell_id
        
        # If no cells available, create emergency containment
        emergency_cell = f"EMERGENCY-{int(time.time())}"
        self.containment_cells[emergency_cell] = entity_id
        return emergency_cell
    
    def detect_anomaly(self, signatures: List[str], context: Dict[str, Any]) -> Optional[str]:
        """Detect if current conditions match any known anomaly signatures"""
        for entity_id, entity in self.entities.items():
            for signature in entity.detection_signatures:
                if signature in signatures:
                    return entity_id
        return None
    
    def report_breach(self, entity_id: str, description: str, 
                     failure_reason: str = "Unknown") -> str:
        """Report a containment breach"""
        if entity_id not in self.entities:
            return f"Unknown entity: {entity_id}"
        
        entity = self.entities[entity_id]
        entity.containment_status = ContainmentStatus.BREACH
        entity.last_incident = time.time()
        
        breach = ContainmentBreach(
            entity_id=entity_id,
            timestamp=time.time(),
            severity=entity.threat_level,
            description=description,
            containment_failure_reason=failure_reason,
            automated_response=[],
            manual_intervention_required=False
        )
        
        # Determine automated response
        response = self._generate_automated_response(entity, breach)
        breach.automated_response = response
        
        # Check if manual intervention is needed
        if entity.classification in [AnomalyClass.KETER, AnomalyClass.APOLLYON]:
            breach.manual_intervention_required = True
        
        self.active_breaches.append(breach)
        
        # Update threat level
        self._update_threat_level()
        
        # Execute automated response
        self._execute_automated_response(breach)
        
        # Alert systems
        self.alert_system.trigger_alert(entity, breach)
        
        breach_id = f"BREACH-{int(time.time())}-{entity_id}"
        self.logger.error(f"Containment breach: {breach_id} - {description}")
        
        return breach_id
    
    def _generate_automated_response(self, entity: AnomalousEntity, 
                                   breach: ContainmentBreach) -> List[str]:
        """Generate automated containment response"""
        response = []
        
        if entity.classification == AnomalyClass.SAFE:
            response.append("Standard recontainment procedure")
            response.append("Monitor for 30 minutes")
        
        elif entity.classification == AnomalyClass.EUCLID:
            response.append("Enhanced monitoring protocol")
            response.append("Implement backup containment measures")
            response.append("Alert research staff")
        
        elif entity.classification == AnomalyClass.KETER:
            response.append("Emergency containment protocol")
            response.append("Isolate affected systems")
            response.append("Deploy countermeasures")
            response.append("Alert Director's Office")
        
        elif entity.classification == AnomalyClass.THAUMIEL:
            response.append("Assess beneficial effects")
            response.append("Preserve positive outcomes")
            response.append("Gentle recontainment")
        
        elif entity.classification == AnomalyClass.APOLLYON:
            response.append("EMERGENCY: Initiate evacuation protocols")
            response.append("Deploy Special Circumstances")
            response.append("Activate all countermeasures")
        
        return response
    
    def _execute_automated_response(self, breach: ContainmentBreach):
        """Execute automated containment response"""
        entity = self.entities[breach.entity_id]
        
        # Execute each response action
        for action in breach.automated_response:
            try:
                if "recontainment" in action.lower():
                    self._attempt_recontainment(entity)
                elif "isolate" in action.lower():
                    self._isolate_systems(entity)
                elif "countermeasures" in action.lower():
                    self._deploy_countermeasures(entity)
                elif "special circumstances" in action.lower():
                    self.special_circumstances.deploy(entity, breach)
                
                self.logger.info(f"Executed: {action}")
                
            except Exception as e:
                self.logger.error(f"Failed to execute {action}: {str(e)}")
    
    def _attempt_recontainment(self, entity: AnomalousEntity):
        """Attempt to recontain an entity"""
        # Simulate recontainment process
        if entity.containment_cell:
            entity.containment_status = ContainmentStatus.PARTIAL
            self.logger.info(f"Attempting recontainment of {entity.id}")
    
    def _isolate_systems(self, entity: AnomalousEntity):
        """Isolate affected systems"""
        # Implement system isolation logic
        self.logger.info(f"Isolating systems affected by {entity.id}")
    
    def _deploy_countermeasures(self, entity: AnomalousEntity):
        """Deploy specific countermeasures for an entity"""
        for countermeasure in entity.countermeasures:
            try:
                # Execute countermeasure
                self.logger.info(f"Deploying countermeasure: {countermeasure}")
            except Exception as e:
                self.logger.error(f"Countermeasure failed: {str(e)}")
    
    def _update_threat_level(self):
        """Update overall facility threat level"""
        max_threat = ThreatLevel.GREEN
        
        for breach in self.active_breaches:
            if not breach.resolved:
                if breach.severity.value == "red":
                    max_threat = ThreatLevel.RED
                elif breach.severity.value == "orange" and max_threat != ThreatLevel.RED:
                    max_threat = ThreatLevel.ORANGE
                elif breach.severity.value == "yellow" and max_threat == ThreatLevel.GREEN:
                    max_threat = ThreatLevel.YELLOW
        
        if max_threat != self.threat_level:
            self.threat_level = max_threat
            self.logger.warning(f"Threat level updated to {max_threat.value.upper()}")
    
    def _continuous_monitoring(self):
        """Continuous system monitoring for anomalies"""
        while self.monitoring_active:
            try:
                # Monitor system resources
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                # Check for anomalous patterns
                signatures = []
                context = {
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "timestamp": time.time()
                }
                
                if cpu_percent > 90:
                    signatures.append("high_cpu_usage")
                
                if memory.percent > 85:
                    signatures.append("memory_pressure")
                
                # Check for specific anomaly signatures
                if signatures:
                    detected_entity = self.detect_anomaly(signatures, context)
                    if detected_entity and detected_entity not in [b.entity_id for b in self.active_breaches if not b.resolved]:
                        self.report_breach(
                            detected_entity,
                            f"Anomalous system behavior detected: {', '.join(signatures)}"
                        )
                
                time.sleep(10)  # Monitor every 10 seconds
                
            except Exception as e:
                self.logger.error(f"Monitoring error: {str(e)}")
                time.sleep(30)  # Longer delay on error
    
    def get_status_report(self) -> str:
        """Generate comprehensive status report"""
        active_breaches_count = len([b for b in self.active_breaches if not b.resolved])
        contained_entities = len([e for e in self.entities.values() 
                                if e.containment_status == ContainmentStatus.CONTAINED])
        
        lines = [
            "🏛️ THE OLDEST HOUSE - CONTROL STATUS",
            "═" * 50,
            f"🚨 Threat Level: {self.threat_level.value.upper()}",
            f"📊 Active Breaches: {active_breaches_count}",
            f"🔒 Contained Entities: {contained_entities}/{len(self.entities)}",
            "",
            "📋 ENTITY STATUS:"
        ]
        
        # Status icons
        status_icons = {
            ContainmentStatus.CONTAINED: "🟢",
            ContainmentStatus.BREACH: "🔴", 
            ContainmentStatus.PARTIAL: "🟡",
            ContainmentStatus.UNKNOWN: "⚪"
        }
        
        class_icons = {
            AnomalyClass.SAFE: "📦",
            AnomalyClass.EUCLID: "⚠️",
            AnomalyClass.KETER: "☢️",
            AnomalyClass.THAUMIEL: "⭐",
            AnomalyClass.APOLLYON: "💀"
        }
        
        for entity in self.entities.values():
            status_icon = status_icons[entity.containment_status]
            class_icon = class_icons[entity.classification]
            
            lines.append(f"{status_icon} {class_icon} {entity.name}")
            lines.append(f"   Cell: {entity.containment_cell or 'UNASSIGNED'}")
            
            if entity.last_incident:
                incident_time = time.time() - entity.last_incident
                lines.append(f"   Last incident: {incident_time/3600:.1f} hours ago")
        
        # Recent breaches
        if self.active_breaches:
            lines.extend(["", "🚨 RECENT BREACHES:"])
            for breach in self.active_breaches[-3:]:  # Last 3 breaches
                entity = self.entities[breach.entity_id]
                status = "RESOLVED" if breach.resolved else "ACTIVE"
                lines.append(f"• {entity.name}: {breach.description} [{status}]")
        
        lines.extend([
            "",
            "🔧 SYSTEM STATUS:",
            f"Monitoring: {'ACTIVE' if self.monitoring_active else 'OFFLINE'}",
            f"Containment Cells: {len([c for c in self.containment_cells.values() if c])}/{len(self.containment_cells)}",
            f"Special Circumstances: {self.special_circumstances.get_status()}"
        ])
        
        return "\n".join(lines)

class AlertSystem:
    """Alert and notification system"""
    
    def __init__(self):
        self.alert_log = []
    
    def trigger_alert(self, entity: AnomalousEntity, breach: ContainmentBreach):
        """Trigger alert for containment breach"""
        alert = {
            "timestamp": time.time(),
            "entity": entity.name,
            "severity": breach.severity.value,
            "description": breach.description
        }
        self.alert_log.append(alert)
        
        # In a real system, this would send notifications
        print(f"🚨 ALERT: {entity.name} containment breach - {breach.description}")

class ResearchLab:
    """Research and analysis facility"""
    
    def __init__(self):
        self.experiments = []
        self.research_data = {}
    
    def study_entity(self, entity_id: str) -> Dict[str, Any]:
        """Conduct research on an anomalous entity"""
        return {
            "entity_id": entity_id,
            "research_status": "ongoing",
            "findings": ["Behavioral patterns logged", "Containment effectiveness measured"]
        }

class SpecialCircumstances:
    """Special Circumstances deployment system"""
    
    def __init__(self):
        self.active_deployments = []
        self.available_agents = 5
    
    def deploy(self, entity: AnomalousEntity, breach: ContainmentBreach):
        """Deploy Special Circumstances for surgical intervention"""
        if self.available_agents > 0:
            deployment = {
                "entity": entity.id,
                "breach": breach.timestamp,
                "agent_assigned": f"SC-AGENT-{len(self.active_deployments) + 1}",
                "status": "deployed"
            }
            self.active_deployments.append(deployment)
            self.available_agents -= 1
            
            print(f"🔪 Special Circumstances deployed for {entity.name}")
    
    def get_status(self) -> str:
        """Get Special Circumstances status"""
        return f"{self.available_agents} agents available, {len(self.active_deployments)} active"