"""Fixed Blender-side scripts for the official Blender Lab MCP TCP transport.

Scripts assign a JSON-serializable dictionary to the top-level ``result``.
Python ``repr`` formatting safely embeds user-selected names and file paths.
"""


def list_meshes_code():
    """Build a Blender script returning all mesh objects in the active scene."""
    return '''import bpy
meshes = [
    {'name': obj.name, 'vertices': len(obj.data.vertices),
     'faces': len(obj.data.polygons)}
    for obj in bpy.context.scene.objects if obj.type == 'MESH'
]
meshes.sort(key=lambda item: item['name'].lower())
result = {'meshes': meshes}
'''


def export_fbx_code(names, filepath, bones, textures, animation):
    """Build a selection-only export script that restores Blender UI state."""
    return '''import bpy
import os
from pathlib import Path

names = {names!r}
filepath = {filepath!r}
with_bones = {bones!r}
with_textures = {textures!r}
with_animation = {animation!r}

view_layer = bpy.context.view_layer
original_selection = list(bpy.context.selected_objects)
original_active = view_layer.objects.active
original_mode = original_active.mode if original_active else 'OBJECT'

try:
    scene_objects = {{obj.name: obj for obj in bpy.context.scene.objects}}
    objects = [scene_objects.get(name) for name in names]
    if not objects or any(obj is None or obj.type != 'MESH' for obj in objects):
        raise RuntimeError('Selected Blender mesh is unavailable in the current scene')

    if with_bones:
        extra = set(objects)
        for mesh in objects:
            for modifier in mesh.modifiers:
                if modifier.type == 'ARMATURE' and modifier.object:
                    extra.add(modifier.object)
            if mesh.parent and mesh.parent.type == 'ARMATURE':
                extra.add(mesh.parent)
        objects = list(extra)

    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    view_layer.objects.active = objects[0]

    Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.fbx(
        filepath=filepath, use_selection=True,
        object_types={{'MESH', 'ARMATURE'}} if with_bones else {{'MESH'}},
        path_mode='COPY' if with_textures else 'AUTO',
        embed_textures=with_textures, bake_anim=with_animation,
        add_leaf_bones=False, use_mesh_modifiers=True)
    if not os.path.isfile(filepath) or os.path.getsize(filepath) == 0:
        raise RuntimeError('Blender FBX exporter created no data')
    result = {{'exported': filepath, 'objects': len(objects)}}
finally:
    # Keep cleanup from masking the original exception whenever possible.
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    for obj in original_selection:
        if obj.name in bpy.data.objects:
            obj.select_set(True)
    if original_active and original_active.name in bpy.data.objects:
        view_layer.objects.active = original_active
        if original_mode != 'OBJECT':
            try:
                bpy.ops.object.mode_set(mode=original_mode)
            except (RuntimeError, TypeError, ValueError):
                # A deleted/incompatible object or context may prevent restoration.
                pass
'''.format(
        names=list(names), filepath=str(filepath).replace('\\', '/'),
        bones=bool(bones), textures=bool(textures), animation=bool(animation),
    )


def import_fbx_code(filepath, bones, textures, animation):
    """Build a Blender FBX import script; retain previously supported options."""
    return '''import bpy
filepath = {filepath!r}
with_bones = {bones!r}
with_animation = {animation!r}

if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
old_objects = set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=filepath, use_anim=with_animation,
                         ignore_leaf_bones=True)
new_objects = [obj for obj in bpy.data.objects if obj not in old_objects]
if not with_bones:
    for obj in list(new_objects):
        if obj.type == 'ARMATURE':
            bpy.data.objects.remove(obj, do_unlink=True)
            new_objects.remove(obj)
result = {{'imported': [obj.name for obj in new_objects]}}
'''.format(
        filepath=str(filepath).replace('\\', '/'),
        bones=bool(bones), animation=bool(animation),
    )
