"""The crypto dashboard API: ``/api/crypto``.

Anonymous on purpose: the dashboard is the app's public surface, served without a caller
the way the health routes are. The package name is the URL segment (``/api/crypto``) and
``route.py`` is the directory index serving every path beneath it.
"""

from fastapi import params

dependencies: tuple[params.Depends, ...] = ()
