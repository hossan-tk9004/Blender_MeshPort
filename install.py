# -*- coding: utf-8 -*-
"""Drag this install.py into Maya's viewport to create a shelf button.

Keep install.py INSIDE the blender_meshport package folder. The shelf command
adds the folder containing that package to sys.path and runs package.show(reload=True).
"""
import os
import sys

SHELF_DOC_TAG = 'BlenderMeshPortInstaller'


def _package_location(installer_path):
    package_dir = os.path.dirname(os.path.abspath(installer_path))
    package_name = os.path.basename(package_dir)
    if not os.path.isfile(os.path.join(package_dir, '__init__.py')):
        raise RuntimeError('Installer must be inside a Python package with __init__.py: ' + package_dir)
    return os.path.dirname(package_dir), package_name


def _command(parent_dir, package_name):
    """Return a persistent shelf command (Python source stored in Maya shelf)."""
    return (
        'import sys\n'
        'import importlib\n'
        '_meshport_parent = {parent!r}\n'
        'if _meshport_parent not in sys.path:\n'
        '    sys.path.insert(0, _meshport_parent)\n'
        '_meshport_package = importlib.import_module({name!r})\n'
        '_meshport_package = importlib.reload(_meshport_package)\n'
        '_meshport_package.show(reload=True)\n'
    ).format(parent=parent_dir, name=package_name)


def install(installer_path=None):
    """Install onto Maya's currently selected shelf, replacing our old button there."""
    from maya import cmds, mel

    path = installer_path or __file__
    parent_dir, package_name = _package_location(path)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

    shelf_top = mel.eval('$tmp = $gShelfTopLevel')
    if not shelf_top or not cmds.tabLayout(shelf_top, exists=True):
        raise RuntimeError('Maya shelf tabs are not available.')
    current_shelf = cmds.tabLayout(shelf_top, query=True, selectTab=True)
    if not current_shelf:
        raise RuntimeError('Select a Maya shelf tab before dropping the installer.')

    # Replace only our own button on the currently selected shelf.
    for child in cmds.shelfLayout(current_shelf, query=True, childArray=True) or []:
        if cmds.shelfButton(child, exists=True):
            try:
                if cmds.shelfButton(child, query=True, docTag=True) == SHELF_DOC_TAG:
                    cmds.deleteUI(child)
            except RuntimeError:
                continue

    button = cmds.shelfButton(
        parent=current_shelf,
        label='MeshPort',
        annotation='Blender MeshPort | Maya-Blender mesh transfer (reloads on launch)',
        image1='pythonFamily.png',
        imageOverlayLabel='BMP',
        sourceType='python',
        docTag=SHELF_DOC_TAG,
        command=_command(parent_dir, package_name),
    )
    print('Blender MeshPort shelf button installed on: {}'.format(current_shelf))
    return button


def onMayaDroppedPythonFile(*args):
    """Special Maya Python file drag-and-drop callback."""
    # Maya normally sets __file__; some versions also supply the dragged path.
    candidate = next((item for item in args
                      if isinstance(item, str) and item.lower().endswith('.py')
                      and os.path.isfile(item)), None)
    return install(installer_path=candidate or __file__)
