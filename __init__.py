"""Blender MeshPort: Maya cmds UI and reload-aware entry points."""
import importlib
import sys

_WINDOW = None
_CONTROLLER = None


def _close():
    """Remove the previous window before a controller or view is reloaded."""
    global _WINDOW, _CONTROLLER
    try:
        if _WINDOW is not None:
            _WINDOW.close()
        else:
            from maya import cmds
            if cmds.window('BlenderMeshPortWindow', exists=True):
                cmds.deleteUI('BlenderMeshPortWindow', window=True)
    finally:
        _WINDOW = None
        _CONTROLLER = None


def _reload_modules():
    """Reload dependencies in order; the package itself need not be reloaded."""
    for name in ('config', 'settings', 'blender_commands', 'maya_fbx',
                 'model', 'view', 'controller'):
        module = sys.modules.get(__name__ + '.' + name)
        if module is not None:
            importlib.reload(module)


def show(reload=False):
    """Open GUI. If reload=True, refresh Python source first (no Maya restart)."""
    global _WINDOW, _CONTROLLER
    _close()
    if reload:
        _reload_modules()
    from .view import MeshPortView
    from .controller import MeshPortController
    _WINDOW = MeshPortView()
    _CONTROLLER = MeshPortController(_WINDOW)
    _WINDOW.show()
    return _WINDOW


def reload():
    """Backward-compatible alias; use show(reload=True) for new code."""
    return show(reload=True)


show_meshport = show
reload_meshport = reload
