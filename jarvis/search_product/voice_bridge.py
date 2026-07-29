"""Thin re-exports for bridge modules."""

from jarvis.search_product.bridges import automation_bridge, planner_bridge, vision_bridge, voice_bridge

__all__ = ["automation_bridge", "planner_bridge", "vision_bridge", "voice_bridge"]
