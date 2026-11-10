"""Maya API/FBX implementation. No Qt or TCP operations in this module."""
from maya import cmds


def _ensure_fbx():
    if not cmds.pluginInfo('fbxmaya', q=True, loaded=True):
        cmds.loadPlugin('fbxmaya')


def selected_maya_transforms():
    selected = cmds.ls(sl=True, long=True, objectsOnly=True) or []
    result = []
    for node in selected:
        if cmds.nodeType(node) == 'mesh':
            parents = cmds.listRelatives(node, parent=True, fullPath=True) or []
            node = parents[0] if parents else node
        if cmds.nodeType(node) != 'transform':
            continue
        shapes = cmds.listRelatives(node, shapes=True, fullPath=True, noIntermediate=True) or []
        if any(cmds.nodeType(s) == 'mesh' for s in shapes) and node not in result:
            result.append(node)
    return result


def armature_roots_for_meshes(meshes):
    joints = set()
    for mesh in meshes:
        history = cmds.listHistory(mesh) or []
        for sk in cmds.ls(history, type='skinCluster') or []:
            for joint in cmds.skinCluster(sk, q=True, influence=True) or []:
                if cmds.objExists(joint):
                    joints.add((cmds.ls(joint, long=True) or [joint])[0])
    roots = set()
    for joint in joints:
        cur = joint
        while True:
            parent = cmds.listRelatives(cur, parent=True, fullPath=True) or []
            if not parent or cmds.nodeType(parent[0]) != 'joint':
                break
            cur = parent[0]
        roots.add(cur)
    return sorted(roots)


def export_maya_fbx(path, nodes, bones, textures, animation):
    _ensure_fbx()
    import maya.mel as mel
    original = cmds.ls(sl=True, long=True) or []
    try:
        items = list(nodes)
        if bones:
            items += armature_roots_for_meshes(nodes)
        cmds.select(items, replace=True)
        mel.eval('FBXResetExport;')
        mel.eval('FBXExportSmoothingGroups -v true;')
        mel.eval('FBXExportSkins -v {};'.format('true' if bones else 'false'))
        mel.eval('FBXExportShapes -v {};'.format('true' if bones else 'false'))
        mel.eval('FBXExportEmbeddedTextures -v {};'.format('true' if textures else 'false'))
        mel.eval('FBXExportBakeComplexAnimation -v {};'.format('true' if animation else 'false'))
        mel.eval('FBXExport -f "{}" -s;'.format(str(path).replace('\\', '/').replace('"', '\\"')))
        if not path.is_file():
            raise RuntimeError('Maya FBX export did not produce a file')
    finally:
        if original:
            cmds.select(original, replace=True)
        else:
            cmds.select(clear=True)


def import_maya_fbx(path, bones, animation):
    _ensure_fbx()
    import maya.mel as mel
    mel.eval('FBXResetImport;')
    mel.eval('FBXImportSkins -v {};'.format('true' if bones else 'false'))
    mel.eval('FBXImportShapes -v {};'.format('true' if bones else 'false'))
    mel.eval('FBXImportFillTimeline -v {};'.format('true' if animation else 'false'))
    return cmds.file(str(path), i=True, type='FBX', ignoreVersion=True,
                     mergeNamespacesOnClash=False, namespace='BlenderMeshPort',
                     returnNewNodes=True, options='fbx')
