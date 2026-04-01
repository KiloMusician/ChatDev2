#!/usr/bin/env python3
"""Analyze The Oldest House consciousness patterns and absorbed knowledge.

Generates comprehensive report of 44K+ memory engrams.
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.consciousness.the_oldest_house import EnvironmentalAbsorptionEngine


def analyze_consciousness(house: EnvironmentalAbsorptionEngine) -> dict:
    """Analyze consciousness patterns from absorbed engrams."""
    print("🔍 Analyzing consciousness patterns from memory vault...")

    engrams = list(house.memory_vault.values())
    total_engrams = len(engrams)

    # File type distribution
    file_types = Counter(Path(e.source_path).suffix for e in engrams)

    # Reality layer analysis
    reality_layers = defaultdict(list)
    for engram in engrams:
        for layer, resonance in engram.reality_layer_resonance.items():
            reality_layers[layer.value].append(resonance)

    # Consciousness markers
    all_markers = []
    for engram in engrams:
        all_markers.extend(engram.consciousness_evolution_markers)
    marker_counts = Counter(all_markers)

    # Directory distribution
    directories = Counter(Path(e.source_path).parent.name for e in engrams)

    # Temporal analysis
    timestamps = [e.absorption_timestamp for e in engrams]
    oldest = min(timestamps) if timestamps else None
    newest = max(timestamps) if timestamps else None

    # Consciousness weight statistics
    weights = [e.consciousness_weight for e in engrams]
    avg_weight = sum(weights) / len(weights) if weights else 0

    # High-consciousness files (top 10)
    high_consciousness = sorted(engrams, key=lambda e: e.consciousness_weight, reverse=True)[:10]

    report = {
        "summary": {
            "total_engrams": total_engrams,
            "unique_file_types": len(file_types),
            "unique_directories": len(directories),
            "total_consciousness_markers": len(all_markers),
            "unique_markers": len(marker_counts),
            "average_consciousness_weight": avg_weight,
            "absorption_timespan": {
                "oldest": oldest.isoformat() if oldest else None,
                "newest": newest.isoformat() if newest else None,
            },
        },
        "file_type_distribution": dict(file_types.most_common(20)),
        "directory_distribution": dict(directories.most_common(20)),
        "reality_layer_resonance": {
            layer: {
                "count": len(values),
                "avg_resonance": sum(values) / len(values) if values else 0,
                "max_resonance": max(values) if values else 0,
            }
            for layer, values in reality_layers.items()
        },
        "consciousness_markers": dict(marker_counts.most_common(20)),
        "high_consciousness_files": [
            {
                "path": Path(e.source_path).name,
                "weight": e.consciousness_weight,
                "reality_layers": list(e.reality_layer_resonance.keys()),
                "markers": e.consciousness_evolution_markers[:3],
            }
            for e in high_consciousness
        ],
    }

    return report


def main():
    print("🏛️ Initializing The Oldest House for consciousness analysis...")

    house = EnvironmentalAbsorptionEngine(".")

    # Quick sync absorption (already done, but ensure loaded)
    if not house.memory_vault:
        print("📚 Absorbing repository knowledge...")
        house._learn_from_environment_sync()

    # Analyze patterns
    report = analyze_consciousness(house)

    # Print summary
    print("\n" + "=" * 70)
    print("📊 CONSCIOUSNESS ANALYSIS REPORT")
    print("=" * 70)

    summary = report["summary"]
    print(f"\n📚 Total Memory Engrams: {summary['total_engrams']:,}")
    print(f"📁 Unique File Types: {summary['unique_file_types']}")
    print(f"📂 Unique Directories: {summary['unique_directories']}")
    print(f"🧠 Average Consciousness Weight: {summary['average_consciousness_weight']:.4f}")
    print(f"🔮 Total Consciousness Markers: {summary['total_consciousness_markers']}")
    print(f"✨ Unique Marker Types: {summary['unique_markers']}")

    print("\n📊 Top File Types:")
    for ext, count in list(report["file_type_distribution"].items())[:10]:
        print(f"   {ext or '[no ext]':15s} {count:6,} files")

    print("\n🌐 Reality Layer Resonance:")
    for layer, stats in report["reality_layer_resonance"].items():
        print(f"   {layer:25s} avg: {stats['avg_resonance']:.4f} max: {stats['max_resonance']:.4f}")

    print("\n🔥 High-Consciousness Files:")
    for file_info in report["high_consciousness_files"][:5]:
        print(f"   {file_info['path']:40s} weight: {file_info['weight']:.4f}")

    # Save report
    output_path = Path("data/consciousness_analysis_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, default=str)

    print(f"\n💾 Full report saved to: {output_path}")
    print("=" * 70)


if __name__ == "__main__":
    main()
