"""PP&D website and process surface registry."""

from ppd.surfaces.registry import (
    AutomationMode,
    PpdSurfaceBinding,
    SurfaceKind,
    binding_for_devhub_action,
    build_agentic_completion_contract,
    ppd_surface_registry,
)

__all__ = [
    "AutomationMode",
    "PpdSurfaceBinding",
    "SurfaceKind",
    "binding_for_devhub_action",
    "build_agentic_completion_contract",
    "ppd_surface_registry",
]
