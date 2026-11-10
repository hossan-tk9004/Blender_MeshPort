# Blender MeshPort v1.0.0

Maya <-> Blender FBX transfer using the Blender Lab MCP add-on TCP listener.
The UI uses **maya.cmds only** (no PySide, shiboken, or QSettings). Maya 2024/2025 intended.

## Install and launch

1. Unzip this distribution into a folder such as `C:\Tools\BlenderMeshPort`.
2. In Blender, run the official Blender MCP add-on server (typically 127.0.0.1:9876).
3. In Maya's Script Editor (Python):

```python
import sys
sys.path.insert(0, r'C:\Tools\BlenderMeshPort')
import blender_meshport
blender_meshport.show()
```

After editing files, no Maya restart is needed:

```python
import blender_meshport
blender_meshport.show(reload=True)
```

For a standalone launch script, execute `launch_maya.py` from Maya.

## UI

- Check Connection verifies Blender's Python execution and returns its version and scene name.
- Refresh Blender Mesh List displays mesh names, vertices and face counts. Multi-select rows to import to Maya.
- Send Selected Maya Mesh to Blender exports only the current Maya selection.
- FBX options: Include Bones / Skin, Embed Textures, Include Animation.
- Workspace location is stored in `cmds.optionVar('BlenderMeshPort_workspace_path')`.
- Port is stored in `cmds.optionVar('BlenderMeshPort_port')`.

The files are kept:

```text
<workspace>/
  transfers_Maya2Blender/transfer_M2B_<uuid>.fbx
  transfers_Blender2Maya/transfer_B2M_<uuid>.fbx
```

FBX extraction may create `<fbx_stem>.fbm` beside the imported file. It is not deleted.

## Migration

This is a renamed package. Replace the old `bridge` package with `blender_meshport` and update Maya launch commands. Existing Qt `QSettings` workspace values are **not automatically imported**, to keep a strict no-Qt dependency; choose the workspace once in v0.6. The value is persisted through Maya optionVars thereafter.

## Structure

- `view.py`: cmds GUI only
- `controller.py`: event routing and status/error handling
- `model.py`: TCP protocol and transfer orchestration
- `blender_commands.py`: Blender code templates
- `maya_fbx.py`: Maya FBX I/O
- `settings.py`: optionVar persistence
- `config.py`: defaults

## Notes

- Blender MCP's underlying transport is NUL-terminated JSON, not the MCP stdio protocol.
- Requires the same local filesystem accessible to both DCC applications.
- FBX material/texture/skin/animation portability remains dependent on exporter/importer settings.
- The Maya UI and full transfers require manual validation on an installed Maya and Blender. Unit tests do not substitute for an end-to-end transfer.

## v0.7 — Drag-and-drop shelf installer

Drag **`blender_meshport/install.py`** (inside the package folder) onto Maya's
viewport. A **BMP** button appears on the currently selected Maya shelf.
Dropping it again onto the same shelf replaces that button, avoiding duplicates.
Keep the installed folder in the same place, since the shelf button stores its
absolute location. Maya itself can save the shelf on exit as usual.

The button runs the equivalent of:

```python
import sys
import importlib
parent_folder = r'C:\Tools\BlenderMeshPort'
if parent_folder not in sys.path:
    sys.path.insert(0, parent_folder)
module = importlib.import_module('blender_meshport')
module = importlib.reload(module)
module.show(reload=True)
```

The previous `reload()` entry point still works for compatibility, but
`blender_meshport.show(reload=True)` is preferred. `show()` retains the default
non-reloading behavior. The UI remains `maya.cmds` only.

## v1.0.0 — Refactoring (Phase A + Phase B)

- Preserves the user-edited `maya.cmds` UI layout and the existing MVC structure.
- Consolidates controller command failures and keeps the preflight connection check.
- Uses `FBXPushSettings` / `FBXPopSettings` around Maya FBX exports and imports
  (even on exceptions); preserves Maya selection after FBX export.
- Restores Blender's selected/active objects and attempts to restore the
  original mode after Blender FBX export. Some Blender contexts cannot restore
  a mode; those failures are ignored during cleanup.
- Reloads Python modules before closing the current window so a reload
  exception does not immediately destroy the existing UI.
- Updates the window version to v1.0.0 and adds isolated unit tests.

**Release validation:** Static Python compilation and mocked tests are included.
Maya/Blender end-to-end FBX transfer and the exact layout in Maya require
manual verification before publishing a production-ready release.

**Scope:** Phase C (GitHub packaging, license, public-release documentation)
was not included in this refactoring.
