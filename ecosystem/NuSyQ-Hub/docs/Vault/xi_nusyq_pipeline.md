# ΞNuSyQ Pipeline DSL — Quick Reference

This file captures a short, runnable mapping of the `ΞNuSyQ Mesh` design into
small, practical Python primitives for building safe, observable, and composable
workflows.

Concepts

- Gate: predicate that guards transitions between steps
- Shadow: metadata attached to steps (audit, pii, ttl)
- Step: a composable unit with run, gate, shade, and seal
- Seal: predicate on outputs ensuring closure

Examples

- Compose steps with `pipeline(a,b,c)` or use `a >> b` semantics via Step
  composition.
- Use Shadows to attach observability/audit markers; merge_shadow combines
  metadata when composing.

Testing

- Unit tests are under `tests/test_xi_pipeline.py` and exercise composition,
  gate blocking, and shadow merging.

Design notes

- This is intentionally small and focused: it provides the core building blocks
  for implementing Corridor/Shadow/Gate patterns. It is not a full workflow
  engine but can serve as a foundation for expanding into effect handlers, event
  sourcing, or model-checkable state machines.
