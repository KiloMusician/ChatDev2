"""
ΞNuSyQ Resource Monitor - Flexible Resource Management (Not Hard Limits)

Philosophy:
    "Don't kill processes for using 'too much' RAM.
     Track usage patterns, understand context, scale intelligently."

Old Mindset:
    ❌ "Max 4GB RAM per process or kill it"
    ❌ "CPU > 80% for 1min = throttle"
    ❌ Hard limits based on arbitrary thresholds

New Mindset:
    ✅ "Is this normal for this operation?"
    ✅ "Downloading model = high disk, low CPU (normal)"
    ✅ "Training = high RAM, high CPU (expected)"
    ✅ Context-aware resource understanding

Examples:
    - ChatDev generating huge project: 6GB RAM might be normal
    - Ollama loading 70B model: 40GB RAM expected
    - Video generation: 95% CPU for 2hrs legitimate

    OLD: Kill them all for "excessive usage"
    NEW: Understand context, show progress, scale if needed
"""

import psutil
from dataclasses import dataclass
from typing import Dict
from enum import Enum


class ResourceContext(Enum):
    """Different contexts have different 'normal' resource profiles"""

    IDLE = "idle"  # Minimal resource use expected
    DOWNLOADING = "downloading"  # High disk I/O, moderate network
    MODEL_LOADING = "model_loading"  # High RAM spike, then stable
    INFERENCE = "inference"  # Moderate RAM/CPU, steady
    TRAINING = "training"  # High everything, sustained
    COMPILATION = "compilation"  # High CPU, moderate RAM
    VIDEO_GENERATION = "video_gen"  # Extreme CPU/GPU, long duration


@dataclass
class ResourceProfile:
    """Expected resource usage for a context (not limits, but baselines)"""

    context: ResourceContext
    typical_ram_mb: range  # e.g., range(1000, 4000) = 1-4GB
    typical_cpu_percent: range  # e.g., range(10, 30) = 10-30%
    typical_duration_min: range  # e.g., range(5, 60) = 5-60min
    notes: str


class ResourceMonitor:
    """
    Monitor resource usage WITH CONTEXT, not arbitrary limits.
    Understand what's normal for each operation type.
    """

    # Resource profiles for different contexts
    PROFILES = {
        ResourceContext.DOWNLOADING: ResourceProfile(
            context=ResourceContext.DOWNLOADING,
            typical_ram_mb=range(500, 2000),  # 0.5-2GB
            typical_cpu_percent=range(5, 30),  # 5-30% CPU
            typical_duration_min=range(1, 60),  # 1-60min
            notes="High disk I/O, network activity normal",
        ),
        ResourceContext.MODEL_LOADING: ResourceProfile(
            context=ResourceContext.MODEL_LOADING,
            typical_ram_mb=range(2000, 40000),  # 2-40GB (70B models!)
            typical_cpu_percent=range(20, 80),  # 20-80% during load
            typical_duration_min=range(1, 5),  # 1-5min spike
            notes="RAM spike expected, then stabilizes",
        ),
        ResourceContext.INFERENCE: ResourceProfile(
            context=ResourceContext.INFERENCE,
            typical_ram_mb=range(1000, 8000),  # 1-8GB
            typical_cpu_percent=range(30, 90),  # 30-90% during inference
            typical_duration_min=range(0, 10),  # Seconds to minutes
            notes="Steady resource use while generating",
        ),
        ResourceContext.TRAINING: ResourceProfile(
            context=ResourceContext.TRAINING,
            typical_ram_mb=range(8000, 64000),  # 8-64GB
            typical_cpu_percent=range(80, 100),  # Near max CPU
            typical_duration_min=range(30, 1440),  # 30min to 24hrs
            notes="Extreme resource use sustained, totally normal",
        ),
    }

    def analyze_usage(self, pid: int, context: ResourceContext) -> Dict:
        """
        Analyze if resource usage is ABNORMAL for this context.
        Not 'too high', but 'unexpected for what we're doing'.
        """
        try:
            process = psutil.Process(pid)

            # Get current usage
            current_ram_mb = process.memory_info().rss / (1024 * 1024)
            current_cpu = process.cpu_percent(interval=1.0)

            # Get expected profile
            profile = self.PROFILES.get(context)
            if not profile:
                return {"status": "unknown_context"}

            # Compare to expected
            ram_normal = current_ram_mb in profile.typical_ram_mb
            cpu_normal = current_cpu in profile.typical_cpu_percent

            if ram_normal and cpu_normal:
                return {
                    "status": "normal",
                    "context": context.value,
                    "ram_mb": current_ram_mb,
                    "cpu_percent": current_cpu,
                    "assessment": f"✓ Normal for {context.value}",
                    "action": "Continue monitoring",
                }

            # Abnormal - but investigate, don't kill
            reasons = []
            if not ram_normal:
                expected = (
                    f"{profile.typical_ram_mb.start}-{profile.typical_ram_mb.stop}MB"
                )
                reasons.append(
                    f"RAM {current_ram_mb:.0f}MB outside expected {expected}"
                )
            if not cpu_normal:
                expected = f"{profile.typical_cpu_percent.start}-{profile.typical_cpu_percent.stop}%"
                reasons.append(f"CPU {current_cpu:.0f}% outside expected {expected}")

            return {
                "status": "investigate",
                "context": context.value,
                "ram_mb": current_ram_mb,
                "cpu_percent": current_cpu,
                "reasons": reasons,
                "assessment": "⚠️ Unusual for this operation",
                "action": "Check if memory leak, unexpected load, or legitimate variation",
                "suggestion": "Don't auto-kill - investigate context first",
            }

        except psutil.NoSuchProcess:
            return {"status": "process_ended"}


# Example usage
if __name__ == "__main__":
    print("=== Resource Monitor Demo ===\n")

    monitor = ResourceMonitor()

    # Example: Ollama loading 70B model
    print("Scenario: Loading deepseek-coder-33b model")
    print("RAM Usage: 35GB")
    print("CPU Usage: 75%")

    # Simulate analysis
    analysis = {
        "status": "normal",
        "context": "model_loading",
        "ram_mb": 35000,
        "cpu_percent": 75,
        "assessment": "✓ Normal for model_loading",
        "action": "Continue monitoring",
    }

    print(f"\nAnalysis: {analysis['assessment']}")
    print(f"Action: {analysis['action']}")
    print("\nKey Difference:")
    print("  ❌ Hard Limit: 'Kill if RAM > 4GB'")
    print("  ✅ Context-Aware: '35GB normal for loading 33B model'")
