from jarvis.application.standalone.workstation_impl.acceptance import *  # noqa: F403

try:
    from aiplatform.workstation.acceptance import run_acceptance as _platform_run_acceptance  # noqa: F401
except ImportError:
    pass
