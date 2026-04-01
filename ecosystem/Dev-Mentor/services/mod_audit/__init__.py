"""
services/mod_audit
~~~~~~~~~~~~~~~~~~
Mod audit engine for Terminal Keeper / RimWorld.

Entry point: recommendation_engine.analyze(mod_ids, about_xmls)
Returns a fully structured ModAuditReport dict ready to serialise as JSON.
"""
from .recommendation_engine import analyze

__all__ = ["analyze"]
