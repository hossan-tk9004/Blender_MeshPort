"""Blender MeshPort: reload-aware entry points for the Maya cmds UI."""

import importlib
import sys

_WINDOW = None
_CONTROLLER = None
_RELOAD_ORDER = (
    'config', 'settings', 'blender_commands', 'maya_fbx',
    'model', 'view', 'controller',
)


def _close():
    """Close the previous window and release its controller references."""
    global _WINDOW, _CONTROLLER
    if _WINDOW is not None:
        _WINDOW.close()
    else:
        from maya import cmds
        if cmds.window('BlenderMeshPortWindow', exists=True):
            cmds.deleteUI('BlenderMeshPortWindow', window=True)
    _WINDOW = None
    _CONTROLLER = None


def _reload_modules():
    """Reload already-imported dependencies in their dependency order."""
    for name in _RELOAD_ORDER:
        module = sys.modules.get(__name__ + '.' + name)
        if module is not None:
            importlib.reload(module)


def show(reload=False):
    """Show the window; optionally reload source without restarting Maya.

    Reload happens *before* closing the old window. If the reload raises,
    the existing UI remains available instead of disappearing silently.
    """
    global _WINDOW, _CONTROLLER
    if reload:
        try:
            _reload_modules()
        except Exception as error:
            raise RuntimeError('Blender MeshPort module reload failed: {}'.format(error)) from error

    from .view import MeshPortView
    from .controller import MeshPortController

    _close()
    try:
        window = MeshPortView()
        controller = MeshPortController(window)
        window.show()
    except Exception:
        from maya import cmds
        if cmds.window('BlenderMeshPortWindow', exists=True):
            cmds.deleteUI('BlenderMeshPortWindow', window=True)
        raise
    _WINDOW = window
    _CONTROLLER = controller
    return window


def reload():
    """Compatibility alias; prefer show(reload=True)."""
    return show(reload=True)


show_meshport = show
reload_meshport = reload
