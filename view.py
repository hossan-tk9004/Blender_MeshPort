"""View: Maya cmds UI only; no PySide, shiboken or Qt imports."""
from maya import cmds
from maya.common.ui import LayoutManager
from . import config, settings

WINDOW_NAME = 'BlenderMeshPortWindow'


class MeshPortView:
    def __init__(self):
        self._mesh_by_label = {}
        self._handlers = {}
        self.window = None
        self.build()

    def build(self):
        if cmds.window(WINDOW_NAME, exists=True):
            cmds.deleteUI(WINDOW_NAME, window=True)
        self.window = cmds.window(
                        WINDOW_NAME, title=config.APP_TITLE,
                        sizeable=True, widthHeight=(480, 640)
                    )
        with LayoutManager(cmds.formLayout()) as root:
            with LayoutManager(cmds.columnLayout(
                                    adjustableColumn=True,
                                    rowSpacing=7
                                )) as headder:
                cmds.separator(height=6, style='none')
                cmds.text(label='Blender MCP Connection', align='left', font='boldLabelFont')
            with LayoutManager(cmds.rowLayout(
                                    numberOfColumns=3,
                                    adjustableColumn=2,
                                    #columnWidth3=(95, 100, 340)
                                )) as BlenderConnect:
                cmds.text(label='Blender Port:')
                self.port = cmds.intField(value=settings.get_int('port', config.DEFAULT_PORT),
                                        minValue=1024, maxValue=65535)
                self.check_button = cmds.button(label='Check Connection')
            with LayoutManager(cmds.columnLayout(
                                                adjustableColumn=True,
                                                rowSpacing=7
                                            )) as workSpace:
                self.status = cmds.text(label='Not checked', align='left')
                cmds.separator(style='in')
                cmds.text(label='Workspace Folder (transfer files are retained)',
                        align='left', font='boldLabelFont')
                
            with LayoutManager(cmds.rowLayout(
                                numberOfColumns=2,
                                adjustableColumn=1,
                                #columnWidth2=(430, 100)
                            )) as workSpaceEditor:
                self.workspace_edit = cmds.textField(text=settings.get_string('workspace_path'))
                self.browse_workspace_button = cmds.button(label='Browse...')

            with LayoutManager(cmds.columnLayout(
                                                adjustableColumn=True,
                                                rowSpacing=7
                                            )) as refreshButton:
                cmds.separator(style='in')
                self.refresh_button = cmds.button(label='Refresh Blender Mesh List', height=30)
                cmds.text(label='Blender meshes (multi-select):', align='left')

                # textScrollList supports multiselection in Maya 2024/2025.
                self.meshes = cmds.textScrollList(allowMultiSelection=True, height=160)
            with LayoutManager(cmds.frameLayout(
                                label='FBX Options',
                                collapsable=False,
                                marginWidth=8,
                                marginHeight=6
                            )) as fbxOptions:
                self.bones = cmds.checkBox(label='Include Bones / Skin', value=True)
                self.textures = cmds.checkBox(label='Embed Textures (FBX)', value=False)
                self.animation = cmds.checkBox(label='Include Animation', value=False)

            with LayoutManager(cmds.paneLayout(
                                configuration='vertical2',
                                ps=[(1, 50, 100), (2, 50, 100)]
                            )) as Sender:
                self.pull_button = cmds.button(label='Import to Maya', height=34)
                self.push_button = cmds.button(label='Send to Blender (Selection)', height=34)

            with LayoutManager(cmds.columnLayout(
                                                            adjustableColumn=True,
                                                            rowSpacing=7
                                                        )) as fudder:
                cmds.separator(height=6, style='none')
                cmds.text(label='Log', align='left', font='boldLabelFont')
            self.log = cmds.scrollField(
                    editable=False, wordWrap=True, height=95, text=''
                )

        cmds.formLayout(
            root, edit=True,
            af=[
                (headder, 'left', 5),
                (headder, 'right', 5),
                (headder, 'top', 2),
                (BlenderConnect, 'left', 5),
                (BlenderConnect, 'right', 5),
                (workSpace, 'left', 5),
                (workSpace, 'right', 5),
                (workSpaceEditor, 'left', 5),
                (workSpaceEditor, 'right', 5),
                (refreshButton, 'left', 5),
                (refreshButton, 'right', 5),
                (fbxOptions, 'left', 5),
                (fbxOptions, 'right', 5),
                (Sender, 'left', 5),
                (Sender, 'right', 5),
                (fudder, 'left', 5),
                (fudder, 'right', 5),
                (self.log, 'left', 5),
                (self.log, 'right', 5),
                (self.log, 'bottom', 5)
            ],
            ac=[
                (BlenderConnect, 'top', 0, headder),
                (workSpace, 'top', 0, BlenderConnect),
                (workSpaceEditor, 'top', 0, workSpace),
                (refreshButton, 'top', 0, workSpaceEditor),
                (fbxOptions, 'top', 0, refreshButton),
                (Sender, 'top', 0, fbxOptions),
                (fudder, 'top', 0, Sender),
                (self.log, 'top', 0, fudder),
            ],
        )
                

    def bind(self, **handlers):
        """Register controller callbacks, ignoring maya.cmds callback arguments."""
        self._handlers = handlers
        for widget, event, name in (
            (self.check_button, 'command', 'check_connection'),
            (self.refresh_button, 'command', 'refresh_meshes'),
            (self.pull_button, 'command', 'pull'),
            (self.push_button, 'command', 'push'),
            (self.browse_workspace_button, 'command', 'browse_workspace'),
        ):
            cmds.button(widget, edit=True, **{event: (lambda *args, key=name: self._handlers[key]())})
        cmds.intField(self.port, edit=True,
                      changeCommand=lambda *args: self._handlers['port_changed'](self.port_value()))
        cmds.textField(self.workspace_edit, edit=True,
                       changeCommand=lambda *args: self._handlers['workspace_changed'](self.workspace_path()))

    def show(self):
        cmds.showWindow(self.window)

    def close(self):
        if cmds.window(WINDOW_NAME, exists=True):
            cmds.deleteUI(WINDOW_NAME, window=True)

    def port_value(self):
        return cmds.intField(self.port, query=True, value=True)

    def workspace_path(self):
        return cmds.textField(self.workspace_edit, query=True, text=True).strip()

    def set_workspace_path(self, path):
        cmds.textField(self.workspace_edit, edit=True, text=path)

    def save_workspace(self, path):
        settings.set_string('workspace_path', path)

    def save_port(self, port):
        settings.set_int('port', port)

    def browse_workspace(self):
        paths = cmds.fileDialog2(fileMode=3, dialogStyle=2,
                                 caption='Choose Blender MeshPort Workspace',
                                 startingDirectory=self.workspace_path() or '')
        return paths[0] if paths else None

    def options(self):
        return {'bones': cmds.checkBox(self.bones, query=True, value=True),
                'textures': cmds.checkBox(self.textures, query=True, value=True),
                'animation': cmds.checkBox(self.animation, query=True, value=True)}

    def selected_blender_names(self):
        labels = cmds.textScrollList(self.meshes, query=True, selectItem=True) or []
        return [self._mesh_by_label[label] for label in labels if label in self._mesh_by_label]

    def set_meshes(self, meshes):
        cmds.textScrollList(self.meshes, edit=True, removeAll=True)
        self._mesh_by_label.clear()
        for mesh in meshes:
            # Render a readable row; use lookup rather than parsing the display label.
            name = str(mesh['name'])
            label = '{}   |   {} verts   |   {} faces'.format(
                name, mesh['vertices'], mesh['faces'])
            # Each Blender object name is unique in its scene.
            self._mesh_by_label[label] = name
            cmds.textScrollList(self.meshes, edit=True, append=label)

    def set_connection_status(self, connected, error=None, details=None):
        if connected:
            status = 'Connected: Blender {} | {}'.format(
                (details or {}).get('blender_version', '?'),
                (details or {}).get('scene', '?'))
            color = (0.35, 0.8, 0.42)
        elif error:
            status = 'Disconnected / Protocol mismatch'
            color = (0.95, 0.4, 0.4)
        else:
            status = 'Not checked'
            color = (0.75, 0.75, 0.75)
        cmds.text(self.status, edit=True, label=status, bgc=color)

    def append_log(self, message):
        old = cmds.scrollField(self.log, query=True, text=True)
        content = (old + '\n' if old else '') + str(message)
        cmds.scrollField(self.log, edit=True, text=content)
        cmds.scrollField(self.log, edit=True, insertionPosition=len(content))

    def warning(self, title, message):
        cmds.confirmDialog(title=str(title), message=str(message),
                           button=['OK'], defaultButton='OK', icon='warning')
