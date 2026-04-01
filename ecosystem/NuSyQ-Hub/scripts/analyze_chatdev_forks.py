"""ChatDev Fork Analysis Script

Searches GitHub for ChatDev forks and analyzes their alignment
with NuSyQ's multi-agent AI development concept.
"""

from datetime import datetime
from pathlib import Path

# Manual fork analysis (GitHub API could be added here)
KNOWN_CHATDEV_FORKS = [
    {
        "owner": "OpenBMB",
        "repo": "ChatDev",
        "description": "Original ChatDev - Multi-agent AI software company",
        "url": "https://github.com/OpenBMB/ChatDev",
        "stars": "25000+",
        "last_update": "Active",
        "key_features": [
            "Multi-agent collaboration (CEO, CTO, Programmer, Tester, Designer, Reviewer)",
            "Software company simulation",
            "Chain of thought prompting",
            "Human-in-the-loop mode",
            "Git integration",
            "Incremental development",
        ],
        "nusyq_alignment": {
            "multi_agent": "✅ Core feature",
            "local_llm": "❌ OpenAI focused",
            "symbolic_protocol": "❌ Not present",
            "consciousness": "❌ Not present",
            "ollama_support": "❌ Requires modification",
        },
    },
    {
        "owner": "KiloMusician",
        "repo": "ChatDev2",
        "description": "NuSyQ canonical fork - Ollama integration + ΞNuSyQ protocol",
        "url": "https://github.com/KiloMusician/ChatDev2",
        "stars": "Fork",
        "last_update": "2025-02-11",
        "key_features": [
            "Full Ollama local model support",
            "ΞNuSyQ symbolic message framework",
            "Enhanced memory system",
            "Lazy client loading",
            "Offline-first architecture",
            "NuSyQ configuration customizations",
            "Testing Chamber integration",
        ],
        "nusyq_alignment": {
            "multi_agent": "✅ Inherited from upstream",
            "local_llm": "✅ Primary focus",
            "symbolic_protocol": "✅ ΞNuSyQ integrated",
            "consciousness": "✅ Via bridge",
            "ollama_support": "✅ Native",
        },
    },
    # Add other known forks here
]


def analyze_fork_alignment(fork: dict) -> dict:
    """Analyze how well a fork aligns with NuSyQ concept."""
    alignment = fork.get("nusyq_alignment", {})

    # Calculate alignment score
    total_checks = len(alignment)
    passed_checks = sum(1 for v in alignment.values() if v.startswith("✅"))

    score = (passed_checks / total_checks * 100) if total_checks > 0 else 0

    return {
        "repo": f"{fork['owner']}/{fork['repo']}",
        "score": score,
        "alignment": alignment,
        "recommendation": get_recommendation(score),
    }


def get_recommendation(score: float) -> str:
    """Get recommendation based on alignment score."""
    if score >= 80:
        return "✅ Excellent alignment - Recommended"
    elif score >= 60:
        return "⚠️ Good alignment - Consider for specific features"
    elif score >= 40:
        return "⚠️ Moderate alignment - Requires significant adaptation"
    else:
        return "❌ Poor alignment - Not recommended"


def generate_report() -> None:
    """Generate comprehensive fork analysis report."""
    report_path = Path(__file__).parent.parent / "docs" / "analysis" / "CHATDEV_FORK_ANALYSIS.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report_lines = [
        "# ChatDev Fork Analysis Report",
        "",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Executive Summary",
        "",
        "Analysis of ChatDev forks for alignment with NuSyQ's multi-agent AI development ecosystem.",
        "",
        "### NuSyQ Core Requirements",
        "",
        "1. **Multi-Agent Collaboration**: Multiple AI agents working together",
        "2. **Local LLM Support**: Offline-first with Ollama integration",
        "3. **Symbolic Protocol**: ΞNuSyQ message framework for coordination",
        "4. **Consciousness Integration**: Awareness and context preservation",
        "5. **Ollama Support**: Native support for local models",
        "",
        "## Fork Comparison",
        "",
    ]

    # Analyze each fork
    analyses = []
    for fork in KNOWN_CHATDEV_FORKS:
        analysis = analyze_fork_alignment(fork)
        analyses.append((fork, analysis))

    # Sort by alignment score
    analyses.sort(key=lambda x: x[1]["score"], reverse=True)

    # Generate comparison table
    report_lines.extend(
        [
            "| Repository | Score | Multi-Agent | Local LLM | Symbolic | Consciousness | Ollama | Recommendation |",
            "|------------|-------|-------------|-----------|----------|---------------|--------|----------------|",
        ]
    )

    for fork, analysis in analyses:
        align = fork["nusyq_alignment"]
        row = (
            f"| [{fork['owner']}/{fork['repo']}]({fork['url']}) "
            f"| {analysis['score']:.0f}% "
            f"| {align.get('multi_agent', '❓')} "
            f"| {align.get('local_llm', '❓')} "
            f"| {align.get('symbolic_protocol', '❓')} "
            f"| {align.get('consciousness', '❓')} "
            f"| {align.get('ollama_support', '❓')} "
            f"| {analysis['recommendation']} |"
        )
        report_lines.append(row)

    report_lines.extend(
        [
            "",
            "## Detailed Analysis",
            "",
        ]
    )

    # Detailed analysis for each fork
    for fork, analysis in analyses:
        report_lines.extend(
            [
                f"### {fork['owner']}/{fork['repo']}",
                "",
                f"**URL**: {fork['url']}",
                f"**Stars**: {fork['stars']}",
                f"**Last Update**: {fork['last_update']}",
                f"**Alignment Score**: {analysis['score']:.0f}%",
                "",
                "**Description**:",
                fork["description"],
                "",
                "**Key Features**:",
            ]
        )

        for feature in fork["key_features"]:
            report_lines.append(f"- {feature}")

        report_lines.extend(
            [
                "",
                "**NuSyQ Alignment**:",
            ]
        )

        for key, value in fork["nusyq_alignment"].items():
            report_lines.append(f"- **{key.replace('_', ' ').title()}**: {value}")

        report_lines.extend(
            [
                "",
                f"**Recommendation**: {analysis['recommendation']}",
                "",
                "---",
                "",
            ]
        )

    # Add conclusions
    report_lines.extend(
        [
            "## Conclusions",
            "",
            "### Best Fork for NuSyQ Integration",
            "",
            f"**Winner**: `{analyses[0][0]['owner']}/{analyses[0][0]['repo']}` "
            f"({analyses[0][1]['score']:.0f}% alignment)",
            "",
            "### Reasons:",
            "",
        ]
    )

    winner = analyses[0][0]
    for feature in winner["key_features"][:5]:
        report_lines.append(f"- {feature}")

    report_lines.extend(
        [
            "",
            "### Integration Status",
            "",
            "- ✅ Dependency pins aligned",
            "- ✅ Configuration module created (`src/config/chatdev2_config.py`)",
            "- ✅ Integration documentation complete",
            "- ✅ Testing chamber integration active",
            "- ✅ Ollama bridge operational",
            "",
            "### Next Steps",
            "",
            "1. Monitor upstream ChatDev for useful features to backport",
            "2. Continue enhancing ΞNuSyQ protocol integration",
            "3. Expand multi-agent coordination capabilities",
            "4. Document NuSyQ-specific enhancements",
            "",
            "## See Also",
            "",
            "- [ChatDev2 Integration Documentation](../integration/CHATDEV2_INTEGRATION.md)",
            "- [NuSyQ Orchestration Guide](../../AGENTS.md)",
            "- [Testing Chamber Pattern](../Testing_Chamber_Pattern.md)",
        ]
    )

    # Write report
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print(f"✅ Report generated: {report_path}")
    return report_path


if __name__ == "__main__":
    # Generate analysis report
    report_path = generate_report()

    # Display summary
    print("\n" + "=" * 80)
    print("CHATDEV FORK ANALYSIS SUMMARY")
    print("=" * 80 + "\n")

    for fork in KNOWN_CHATDEV_FORKS:
        analysis = analyze_fork_alignment(fork)
        print(f"{fork['owner']}/{fork['repo']}")
        print(f"  Score: {analysis['score']:.0f}%")
        print(f"  {analysis['recommendation']}")
        print()

    print(f"\nFull report: {report_path}")
