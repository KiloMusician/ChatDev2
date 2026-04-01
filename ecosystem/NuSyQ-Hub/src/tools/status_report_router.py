"""StatusReportRouter: Centralized status aggregation and formatting for NuSyQ-Hub.

Modular, config-driven, supports partial and multi-format output.
"""

from typing import Any


class StatusReportRouter:
    def __init__(self, modules: list[Any] | None = None):
        """Initialize StatusReportRouter with modules."""
        self.modules = modules or []

    def register_module(self, module):
        self.modules.append(module)

    def aggregate_status(
        self, section_flags: dict[str, bool] | None = None, output_format: str = "markdown"
    ) -> str:
        section_flags = section_flags or {}
        results = []
        for module in self.modules:
            if hasattr(module, "get_status_sections"):
                sections = module.get_status_sections(section_flags)
                results.extend(sections)
            elif hasattr(module, "generate_status_report"):
                results.append(module.generate_status_report(section_flags, output_format))
        if output_format == "json":
            import json

            return json.dumps(results, indent=2)
        return "\n".join(results)

    def format_status(self, status: Any, output_format: str = "markdown") -> str:
        if output_format == "json":
            import json

            return json.dumps(status, indent=2)
        if isinstance(status, list):
            return "\n".join(status)
        return str(status)


# Example usage:
# router = StatusReportRouter([KILOSystemStatusChecker(), SystemEvolutionAuditor()])
# print(router.aggregate_status({"health": True, "issues": False}, output_format="markdown"))
