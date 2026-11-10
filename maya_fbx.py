"""Maya selection and FBX import/export; no UI, Qt, or network dependencies."""

from contextlib import contextmanager

from maya import cmds


def _ensure_fbx():
    """Load Maya's FBX plugin only when needed."""
    if not cmds.pluginInfo('fbxmaya', query=True, loaded=True):
        cmds.loadPlugin('fbxmaya')


@contextmanager
def _preserved_fbx_settings():
    """Preserve Maya FBX I/O preferences, including when a transfer fails.

    Maya's FBXPushSettings/FBXPopSettings operate on the plugin settings
    stack. They must remain balanced; do not reset settings before pushing.
    """
    import maya.mel as mel

    _ensure_fbx()
    mel.eval('FBXPushSettings;')
    try:
        yield mel
    finally:
        mel.eval('FBXPopSettings;')


@contextmanager
def _preserved_selection():
    """Restore the user's Maya selection, including on export failures."""
    original = cmds.ls(selection=True, long=True) or []
    try:
        yield
    finally:
        # Some scene commands may delete or rename nodes before restoration.
        existing = [node for node in original if cmds.objExists(node)]
        if existing:
            cmds.select(existing, replace=True)
        else:
            cmds.select(clear=True)


def selected_maya_transforms():
    """Return unique selected transforms containing non-intermediate meshes."""
    selected = cmds.ls(selection=True, long=True, objectsOnly=True) or []
    result = []
    for node in selected:
        if cmds.nodeType(node) == 'mesh':
            parents = cmds.listRelatives(node, parent=True, fullPath=True) or []
            node = parents[0] if parents else node
        if cmds.nodeType(node) != 'transform':
            continue
        shapes = cmds.listRelatives(
            node, shapes=True, fullPath=True, noIntermediate=True
        ) or []
        if any(cmds.nodeType(shape) == 'mesh' for shape in shapes):
            if node not in result:
                result.append(node)
    return result


def armature_roots_for_meshes(meshes):
    """Collect top-level joint roots driving the specified Maya meshes."""
    joints = set()
    for mesh in meshes:
        history = cmds.listHistory(mesh) or []
        for skin in cmds.ls(history, type='skinCluster') or []:
            influences = cmds.skinCluster(skin, query=True, influence=True) or []
            for joint in influences:
                if cmds.objExists(joint):
                    joints.add((cmds.ls(joint, long=True) or [joint])[0])

    roots = set()
    for joint in joints:
        current = joint
        while True:
            parents = cmds.listRelatives(current, parent=True, fullPath=True) or []
            if not parents or cmds.nodeType(parents[0]) != 'joint':
                break
            current = parents[0]
        roots.add(current)
    return sorted(roots)


def _bool_mel(value):
    return 'true' if value else 'false'


def export_maya_fbx(path, nodes, bones, textures, animation):
    """Export only selected transforms (plus joint roots when requested)."""
    with _preserved_fbx_settings() as mel:
        with _preserved_selection():
            items = list(nodes)
            if bones:
                items.extend(armature_roots_for_meshes(nodes))
            if not items:
                raise RuntimeError('No Maya nodes to export.')
            cmds.select(items, replace=True)
            mel.eval('FBXResetExport;')
            mel.eval('FBXExportSmoothingGroups -v true;')
            mel.eval('FBXExportSkins -v {};'.format(_bool_mel(bones)))
            mel.eval('FBXExportShapes -v {};'.format(_bool_mel(bones)))
            mel.eval('FBXExportEmbeddedTextures -v {};'.format(_bool_mel(textures)))
            mel.eval('FBXExportBakeComplexAnimation -v {};'.format(_bool_mel(animation)))
            # MEL paths use forward slashes; escape embedded quotes as well.
            export_path = str(path).replace('\\', '/').replace('"', '\\"')
            mel.eval('FBXExport -f "{}" -s;'.format(export_path))
            if not path.is_file() or path.stat().st_size == 0:
                raise RuntimeError('Maya FBX export did not produce a nonempty file.')


def import_maya_fbx(path, bones, animation):
    """Import FBX into a new namespace without changing Maya FBX settings."""
    with _preserved_fbx_settings() as mel:
        mel.eval('FBXResetImport;')
        mel.eval('FBXImportSkins -v {};'.format(_bool_mel(bones)))
        mel.eval('FBXImportShapes -v {};'.format(_bool_mel(bones)))
        mel.eval('FBXImportFillTimeline -v {};'.format(_bool_mel(animation)))
        return cmds.file(
            str(path), i=True, type='FBX', ignoreVersion=True,
            mergeNamespacesOnClash=False, namespace='BlenderMeshPort',
            returnNewNodes=True, options='fbx'
        )
