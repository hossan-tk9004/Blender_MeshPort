# Blender MeshPort

**Blender MeshPort** is a Maya tool for exchanging mesh data with Blender through the [official Blender MCP add-on](https://projects.blender.org/lab/blender_mcp) and FBX files.

It provides a lightweight **`maya.cmds` UI** for browsing meshes in an open Blender scene and sending selected meshes in either direction. Transfers are initiated directly from Maya, without prompting an AI agent for each operation.

> **Version:** 1.0.0  

[日本語版 README](README_ja.md)

## Features

- **Connection check:** Verify that Blender's MCP add-on responds to a Python execution request. Displays the Blender version and current scene.
- **Blender mesh browser:** List mesh objects in the active Blender scene, including vertex and face counts; select multiple meshes to import.
- **Blender → Maya:** Export selected Blender mesh objects to FBX and import them into Maya.
- **Maya → Blender:** Export only the currently selected Maya mesh transforms (or selected mesh shapes) to FBX and import them into Blender.
- **Simplified FBX options:** Include Bones / Skin, Embed Textures, and Include Animation.
- **Persistent workspace:** Keep transfer FBX files and any importer-extracted associated files; no automatic deletion.
- **Shelf installation:** Drag `install.py` into Maya to create a button on the active shelf.
- **Reload without restarting Maya:** Launch using `blender_meshport.show(reload=True)` to reload Python modules.
- **Native Maya UI:** Uses `maya.cmds`, not PySide, Shiboken, or `QSettings` directly.

## Requirements

- Autodesk Maya with Python 3 and the **fbxmaya** plugin. The tool is intended for Maya 2024/2025; compatibility may vary by environment.
- Blender with the **official Blender MCP add-on** installed and its server running. The project has been developed and tested with a Blender 5.1.1 workflow; compatibility may vary across versions and environments.
- Maya and Blender running on the same computer and able to access the **same local workspace path**.
- The Blender MCP add-on's TCP listener accessible at `127.0.0.1` (default port: `9876`, configurable in the tool).

**Communication note:** MeshPort talks directly to the Blender MCP add-on's local TCP interface, using its NUL-terminated JSON protocol. It is **not** a general-purpose MCP stdio client. Changes in the add-on's internal transport may require code updates.

## Installation

1. Extract the project so that `blender_meshport` remains a Python package containing `__init__.py` and `install.py`.
2. Start Maya and select the shelf tab where you want the button.
3. Drag **`blender_meshport/install.py`** from your file browser onto Maya's viewport.
4. A **BMP / MeshPort** shelf button will be created. Click it to launch the tool.
5. In Blender, enable and start the official Blender MCP add-on server.
6. In MeshPort, set the TCP port if needed and choose a **Workspace Folder** before transferring files.

Reinstalling onto the same shelf replaces the existing MeshPort button with the same installer tag. The shelf command stores an **absolute installation path**; if you move the package, drag `install.py` into Maya again.

### Manual launch

Add the folder **containing** `blender_meshport` to Python's module search path:

```python
import sys

root = r"C:\Tools\BlenderMeshPort"
if root not in sys.path:
    sys.path.insert(0, root)

import blender_meshport
blender_meshport.show()
```

To reload changes without restarting Maya:

```python
import blender_meshport
blender_meshport.show(reload=True)
```

## Usage

### 1. Connect to Blender

Start the Blender MCP add-on server, then click **Check Connection** in MeshPort. A successful connection shows a message similar to:

```text
Connected: Blender 5.1.1 | Scene
```

The tool also checks the connection automatically before communication-dependent operations. An unsuccessful check produces a warning.

### 2. List Blender meshes

Click **Refresh Blender Mesh List**. The list displays mesh object names and their vertex/face counts. Select one or more rows for transfer.

### 3. Import from Blender to Maya

1. Set the **Workspace Folder**.
2. Refresh the Blender mesh list and select the target meshes.
3. Set the FBX options as needed.
4. Click **Import to Maya**.

MeshPort asks Blender to export an FBX into the shared workspace, then imports that FBX into Maya (using the `BlenderMeshPort` namespace).

### 4. Send from Maya to Blender

1. In Maya, select the desired **mesh transforms or mesh shapes**. Only selected meshes are targeted; selecting a parent group alone does not automatically mean all descendant meshes will be exported.
2. Set the **Workspace Folder** and FBX options.
3. Click **Send to Blender (Selection)**.

MeshPort exports the current Maya mesh selection (plus related joints when enabled), then asks Blender to import the FBX.

### FBX options

| Option | Purpose |
| --- | --- |
| **Include Bones / Skin** | Include relevant skeleton/skin information where supported by the FBX exporter/importer. |
| **Embed Textures (FBX)** | Request embedded textures in the exported FBX; actual material/texture portability depends on both applications. |
| **Include Animation** | Enable FBX animation export/import behavior. |

Embedded textures **may** be extracted to a sibling `<fbx_filename>.fbm` directory by an importer. This behavior is importer-dependent; the tool does not create or delete `.fbm` folders itself.

## Workspace layout

Choose a workspace directory in the GUI. Transfer files are retained with unique names:

```text
Workspace/
├── transfers_Maya2Blender/
│   ├── transfer_M2B_<unique-id>.fbx
│   └── transfer_M2B_<unique-id>.fbm/   # if created by the importer
└── transfers_Blender2Maya/
    ├── transfer_B2M_<unique-id>.fbx
    └── transfer_B2M_<unique-id>.fbm/   # if created by the importer
```

**MeshPort does not automatically clean up transfer files.** Existing references may point to extracted textures, so review dependencies before deleting files manually. As transfers accumulate, disk usage increases.

Workspace and port preferences are saved using Maya `cmds.optionVar` (`BlenderMeshPort_workspace_path` and `BlenderMeshPort_port`). Settings previously stored with Qt `QSettings` are **not migrated automatically**.

## Architecture

```text
blender_meshport/
├── __init__.py          # launch and module reload
├── install.py           # Maya drag-and-drop shelf installer
├── config.py            # connection defaults / version label
├── settings.py          # Maya optionVar persistence
├── view.py              # maya.cmds user interface
├── controller.py        # UI events, checks and errors
├── model.py             # TCP communication and transfer orchestration
├── blender_commands.py  # Blender-side Python command generation
└── maya_fbx.py          # Maya FBX import/export
```

The design separates the View, Controller, and Model so UI changes do not require rewriting transport or FBX code.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| Connection refused (`WinError 10061`) | Verify that the Blender MCP server is **running** and the host/port match. |
| TCP connects, but the request times out | Check that Blender is responsive, and that its MCP add-on version supports the expected TCP request/response protocol. |
| Blender mesh list is empty | Check the active Blender scene for mesh objects and refresh the list. |
| FBX cannot be transferred | Check the workspace path, write permissions, shared filesystem access, and Maya's `fbxmaya` plugin. |
| Textures are missing | Confirm the Embed Textures option and inspect importer-created material paths / `.fbm` folders; embedded media is not guaranteed for every material. |
| Shelf button stops working after moving files | Drag `install.py` into Maya again so it records the new absolute path. |

## Known limitations

- **Local-only transport:** The code restricts the TCP host to localhost and assumes a shared filesystem.
- **FBX interchange:** Differences in material graphs, rigs, skin weights, animation and axis/unit handling may need manual adjustment.
- **UI responsiveness:** The client performs synchronous requests, which may temporarily block the Maya UI during longer operations.
- **State restoration:** The tool preserves Maya FBX settings and attempts to restore Blender's selection, active object and mode after export; some Blender contexts may prevent full mode restoration.
- **Security:** Blender-side Python execution is powerful. Only use the MCP listener with trusted local processes; do not expose it publicly.

## License

This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.
