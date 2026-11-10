"""Blender-side scripts executed via official Blender Lab MCP TCP protocol.

Each script must assign a JSON-serializable value to the top-level ``result``.
Scripts are fixed templates; parameter values are serialized as Python literals.
"""


def list_meshes_code():
    return '''import bpy
meshes = [
    {'name': o.name, 'vertices': len(o.data.vertices),
     'faces': len(o.data.polygons)}
    for o in bpy.context.scene.objects if o.type == 'MESH'
]
meshes.sort(key=lambda item: item['name'].lower())
result = {'meshes': meshes}
'''


def export_fbx_code(names, filepath, bones, textures, animation):
    return '''import bpy
import os
from pathlib import Path
names = {names!r}
filepath = {filepath!r}
with_bones = {bones!r}
with_textures = {textures!r}
with_animation = {animation!r}
original_selection = list(bpy.context.selected_objects)
original_active = bpy.context.view_layer.objects.active
try:
    scene_objects = {{ob.name: ob for ob in bpy.context.scene.objects}}
    objects = [scene_objects.get(n) for n in names]
    if not objects or any(ob is None or ob.type != 'MESH' for ob in objects):
        raise RuntimeError('Selected Blender mesh is unavailable in the current scene')
    if with_bones:
        extras = set(objects)
        for mesh in objects:
            for mod in mesh.modifiers:
                if mod.type == 'ARMATURE' and mod.object:
                    extras.add(mod.object)
            parent = mesh.parent
            if parent and parent.type == 'ARMATURE':
                extras.add(parent)
        objects = list(extras)
    if bpy.context.object and bpy.context.object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
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
    bpy.ops.object.select_all(action='DESELECT')
    for ob in original_selection:
        if ob.name in bpy.data.objects:
            ob.select_set(True)
    if original_active and original_active.name in bpy.data.objects:
        bpy.context.view_layer.objects.active = original_active
'''.format(names=list(names), filepath=str(filepath).replace('\\', '/'),
           bones=bool(bones), textures=bool(textures), animation=bool(animation))


def import_fbx_code(filepath, bones, textures, animation):
    return '''import bpy
filepath = {filepath!r}
with_bones = {bones!r}
with_animation = {animation!r}
if bpy.context.object and bpy.context.object.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
old_objects = set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=filepath, use_anim=with_animation,
                         ignore_leaf_bones=True)
new_objects = [ob for ob in bpy.data.objects if ob not in old_objects]
if not with_bones:
    for ob in list(new_objects):
        if ob.type == 'ARMATURE':
            bpy.data.objects.remove(ob, do_unlink=True)
            new_objects.remove(ob)
result = {{'imported': [ob.name for ob in new_objects]}}
'''.format(filepath=str(filepath).replace('\\', '/'),
           bones=bool(bones), animation=bool(animation))
