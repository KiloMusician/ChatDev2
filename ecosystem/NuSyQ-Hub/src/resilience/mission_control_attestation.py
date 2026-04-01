"""Mission Control Attestation & Audit Enhancement (Phase 8).

Goals:
    1. Add cryptographic attestation (SHA256 signing) to all artifacts
    2. Track policy compliance (sandboxing, resource limits, etc)
    3. Include execution spans, failure patterns, and lessons in report
    4. Provide audit trail for every action (audit log)
    5. Enable post-mortem analysis and pattern detection

Design:
    - AuditEntry: Immutable audit log entry with signature
    - PolicyStatus: Compliance tracking for execution constraints
    - ArtifactAttestation: Binds artifact to audit trail + policy
    - MissionControlReport: Enriched summary with audits, policies, patterns
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class AuditEntry:
    """Immutable audit log entry for action accountability."""

    audit_id: str
    timestamp: str  # ISO 8601
    action: str  # e.g., "chatdev_generate", "ollama_call", "artifact_create"
    agent: str  # Which agent performed the action
    result: str  # success, failure, partial
    context: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    entry_hash: str = ""  # SHA256 (immutable signature)

    def __post_init__(self) -> None:
        """Compute entry hash for tamper detection."""
        hashable = json.dumps(
            {
                "action": self.action,
                "agent": self.agent,
                "result": self.result,
                "timestamp": self.timestamp,
                "context": self.context,
            },
            sort_keys=True,
            default=str,
        )
        self.entry_hash = hashlib.sha256(hashable.encode()).hexdigest()

    def to_dict(self) -> dict:
        """Serialize to dict."""
        return asdict(self)

    def verify(self) -> bool:
        """Verify entry hasn't been tampered with."""
        hashable = json.dumps(
            {
                "action": self.action,
                "agent": self.agent,
                "result": self.result,
                "timestamp": self.timestamp,
                "context": self.context,
            },
            sort_keys=True,
            default=str,
        )
        computed = hashlib.sha256(hashable.encode()).hexdigest()
        return computed == self.entry_hash


@dataclass
class PolicyStatus:
    """Policy compliance status for execution context."""

    sandboxing_enabled: bool = False
    resource_limits: dict = field(default_factory=dict)  # {"memory": "2GB", "timeout": 300}
    isolation_level: str = "none"  # none, process, container, vm
    network_restrictions: str = "none"  # none, local-only, sandboxed
    persistence_mode: str = "full"  # full, read-only, disabled
    attestation_required: bool = True
    policy_hash: str = ""

    def __post_init__(self) -> None:
        """Compute policy hash."""
        hashable = json.dumps(asdict(self), sort_keys=True, default=str)
        self.policy_hash = hashlib.sha256(hashable.encode()).hexdigest()

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ArtifactAttestation:
    """Cryptographic attestation linking artifact to audit trail & policy."""

    artifact_id: str
    run_id: str
    artifact_hash: str  # SHA256 of artifact content
    audit_trail: list = field(default_factory=list)  # List of AuditEntry dicts
    policy_status: dict = field(default_factory=dict)  # PolicyStatus dict
    timestamp: str = ""
    signer: str = "mission_control"  # Who issued this attestation
    attestation_hash: str = ""

    def __post_init__(self) -> None:
        """Compute attestation hash."""
        if not self.timestamp:
            self.timestamp = datetime.now(UTC).isoformat() + "Z"
        hashable = json.dumps(
            {
                "artifact_id": self.artifact_id,
                "artifact_hash": self.artifact_hash,
                "audit_trail": self.audit_trail,
                "policy_status": self.policy_status,
                "signer": self.signer,
            },
            sort_keys=True,
            default=str,
        )
        self.attestation_hash = hashlib.sha256(hashable.encode()).hexdigest()

    def to_dict(self) -> dict:
        return asdict(self)

    def verify(self, artifact_content: str) -> bool:
        """Verify artifact hasn't been modified."""
        computed = hashlib.sha256(artifact_content.encode()).hexdigest()
        return computed == self.artifact_hash


@dataclass
class ExecutionSpan:
    """Recorded span for an execution segment (like distributed tracing)."""

    span_id: str
    parent_span_id: str | None
    operation: str
    start_time: str
    end_time: str
    duration_ms: float
    status: str  # success, failure, degraded
    tags: dict = field(default_factory=dict)  # Custom attributes
    logs: list = field(default_factory=list)  # [{"timestamp", "message"}]


@dataclass
class PatternObservation:
    """Pattern observed across multiple executions."""

    pattern_id: str
    category: str  # failure, success, bottleneck, improvement
    description: str
    frequency: int
    first_seen: str
    last_seen: str
    affected_operations: list = field(default_factory=list)
    severity: str = "info"  # info, warning, critical
    lesson: str = ""  # What we learned


@dataclass
class CultureShipReport:
    """Expanded Culture Ship governance report with spans/lessons/patterns."""

    report_id: str
    timestamp: str
    execution_spans: list = field(default_factory=list)  # [ExecutionSpan dicts]
    patterns_observed: list = field(default_factory=list)  # [PatternObservation dicts]
    audit_summary: dict = field(default_factory=dict)  # counts by result/action
    policy_violations: list = field(default_factory=list)  # Violations detected
    lessons_learned: list = field(default_factory=list)  # Key insights
    recommendations: list = field(default_factory=list)  # Suggested improvements
    health_score: float = 1.0  # 0.0-1.0

    def to_dict(self) -> dict:
        return asdict(self)


class AuditLog:
    """Persistent audit log for accountability."""

    def __init__(self, log_path: Path | str = "state/audit.jsonl"):
        """Initialize AuditLog with log_path."""
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, entry: AuditEntry) -> None:
        """Append audit entry to log."""
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry.to_dict(), default=str) + "\n")
        logger.info(f"Audit entry recorded: {entry.audit_id} ({entry.action})")

    def read_all(self) -> list[AuditEntry]:
        """Read all audit entries."""
        if not self.log_path.exists():
            return []
        entries = []
        with open(self.log_path) as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    entries.append(AuditEntry(**data))
        return entries

    def filter_by_action(self, action: str) -> list[AuditEntry]:
        """Get entries for specific action."""
        return [e for e in self.read_all() if e.action == action]

    def filter_by_result(self, result: str) -> list[AuditEntry]:
        """Get entries by result (success/failure/partial)."""
        return [e for e in self.read_all() if e.result == result]

    def verify_integrity(self) -> bool:
        """Verify all entries are unmodified."""
        entries = self.read_all()
        return all(e.verify() for e in entries)


class AttestationManager:
    """Create and manage artifact attestations."""

    def __init__(self, attestation_root: Path | str = "state/attestations"):
        """Initialize AttestationManager with attestation_root."""
        self.root = Path(attestation_root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.audit_log = AuditLog()

    def attest_artifact(
        self,
        artifact_id: str,
        artifact_content: str,
        audit_entries: list[AuditEntry],
        policy_status: PolicyStatus,
        run_id: str = "",
    ) -> ArtifactAttestation:
        """Create attestation for artifact."""
        artifact_hash = hashlib.sha256(artifact_content.encode()).hexdigest()
        attestation = ArtifactAttestation(
            artifact_id=artifact_id,
            run_id=run_id or artifact_id,
            artifact_hash=artifact_hash,
            audit_trail=[e.to_dict() for e in audit_entries],
            policy_status=policy_status.to_dict(),
        )
        # Persist attestation
        attestation_file = self.root / f"{artifact_id}_attestation.json"
        attestation_file.write_text(json.dumps(attestation.to_dict(), indent=2, default=str))
        logger.info(f"Attestation created: {attestation.attestation_hash} for {artifact_id}")
        return attestation

    def verify_artifact(
        self, artifact_id: str, artifact_content: str
    ) -> tuple[bool, ArtifactAttestation | None]:
        """Verify artifact against attestation."""
        attestation_file = self.root / f"{artifact_id}_attestation.json"
        if not attestation_file.exists():
            return False, None
        data = json.loads(attestation_file.read_text())
        attestation = ArtifactAttestation(**data)
        is_valid = attestation.verify(artifact_content)
        return is_valid, attestation


class MissionControlReportBuilder:
    """Build enriched Mission Control report with audits, patterns, and lessons."""

    def __init__(self):
        """Initialize MissionControlReportBuilder."""
        self.audit_log = AuditLog()
        self.attestation_mgr = AttestationManager()

    def build_report(self) -> CultureShipReport:
        """Build comprehensive report."""
        audit_entries = self.audit_log.read_all()

        # Aggregate audit summary
        audit_summary = {
            "total_entries": len(audit_entries),
            "by_result": {},
            "by_action": {},
        }
        for entry in audit_entries:
            audit_summary["by_result"][entry.result] = (
                audit_summary["by_result"].get(entry.result, 0) + 1
            )
            audit_summary["by_action"][entry.action] = (
                audit_summary["by_action"].get(entry.action, 0) + 1
            )

        # Detect patterns
        patterns = self._detect_patterns(audit_entries)

        # Extract lessons
        lessons = self._extract_lessons(audit_entries, patterns)

        # Detect violations
        violations = self._detect_violations(audit_entries)

        # Calculate health score
        health_score = self._calculate_health_score(audit_summary, violations)

        report = CultureShipReport(
            report_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC).isoformat() + "Z",
            audit_summary=audit_summary,
            patterns_observed=patterns,
            lessons_learned=lessons,
            policy_violations=violations,
            health_score=health_score,
        )
        return report

    def _detect_patterns(self, entries: list[AuditEntry]) -> list[dict]:
        """Detect recurring patterns in audit log."""
        patterns = []

        # Pattern: High failure rate for specific action
        action_stats = {}
        for entry in entries:
            if entry.action not in action_stats:
                action_stats[entry.action] = {"success": 0, "failure": 0}
            if entry.result == "success":
                action_stats[entry.action]["success"] += 1
            else:
                action_stats[entry.action]["failure"] += 1

        for action, stats in action_stats.items():
            total = stats["success"] + stats["failure"]
            failure_rate = stats["failure"] / total if total > 0 else 0
            if failure_rate > 0.1:  # >10% failure rate
                patterns.append(
                    {
                        "pattern_id": str(uuid.uuid4()),
                        "category": "failure",
                        "description": f"High failure rate for {action}",
                        "frequency": stats["failure"],
                        "first_seen": entries[0].timestamp if entries else "",
                        "last_seen": entries[-1].timestamp if entries else "",
                        "affected_operations": [action],
                        "severity": "critical" if failure_rate > 0.5 else "warning",
                    }
                )

        return patterns

    def _extract_lessons(self, entries: list[AuditEntry], patterns: list[dict]) -> list[str]:
        """Extract lessons from execution patterns."""
        lessons = []

        # Lesson: Retry effectiveness
        retries = [e for e in entries if "retry" in e.metadata.get("attempt", "")]
        if retries:
            success_after_retry = sum(1 for e in retries if e.result == "success")
            lessons.append(
                f"Retry mechanism: {success_after_retry}/{len(retries)} recovered "
                f"({100 * success_after_retry / len(retries):.0f}% success rate)"
            )

        # Lesson: Pattern insights
        for pattern in patterns:
            lessons.append(f"Pattern detected: {pattern['description']}")

        return lessons

    def _detect_violations(self, entries: list[AuditEntry]) -> list[dict]:
        """Detect policy violations in audit trail."""
        violations = []

        # Violation: Unauthorized agent action
        for entry in entries:
            if "unauthorized" in entry.result.lower():
                violations.append(
                    {
                        "timestamp": entry.timestamp,
                        "violation": "Unauthorized action",
                        "agent": entry.agent,
                        "action": entry.action,
                    }
                )

        return violations

    def _calculate_health_score(self, audit_summary: dict, violations: list) -> float:
        """Calculate system health score (0.0-1.0)."""
        if audit_summary["total_entries"] == 0:
            return 1.0

        failures = audit_summary["by_result"].get("failure", 0)
        total = audit_summary["total_entries"]
        failure_rate = failures / total

        health = 1.0 - (failure_rate * 0.8) - (len(violations) * 0.05)
        return max(0.0, min(1.0, health))

    def save_report(
        self, report: CultureShipReport, path: Path | str = "state/reports/culture_ship_report.json"
    ) -> None:
        """Persist report to disk."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report.to_dict(), indent=2, default=str))
        logger.info(f"Culture Ship report saved: {path}")
