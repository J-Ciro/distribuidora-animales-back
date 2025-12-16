# Temporary compatibility imports to ease migration
# Re-export common symbols from new locations to preserve old imports
try:
    from .presentation.schemas import *  # noqa
except Exception:
    pass
try:
    from .presentation.routers.__all__ import *  # noqa
except Exception:
    pass
try:
    from .infrastructure.models import *  # noqa
except Exception:
    pass
try:
    from .infrastructure.db import *  # noqa
except Exception:
    pass
try:
    from .application import *  # noqa
except Exception:
    pass
