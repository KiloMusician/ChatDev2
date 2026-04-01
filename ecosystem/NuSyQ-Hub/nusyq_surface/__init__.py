"""
nusyq_surface — shared Python package for all NuSyQ ecosystem repos.
Import from any repo to get: registry, paths, bridge_client, hub_client, env.
"""
from .registry import get_registry, get_repo, list_repos
from .env import REGISTRY_PATH, CHATDEV_API, DEV_MENTOR_API, CONCEPT_SAMURAI_API
