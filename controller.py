"""Controller: maps native Maya UI actions to Model operations."""
from .model import BridgeModel


class MeshPortController:
    def __init__(self, view, model=None):
        self.view = view
        self.model = model or BridgeModel(port=view.port_value())
        view.bind(check_connection=self.check_connection,
                  refresh_meshes=self.refresh_meshes,
                  pull=self.pull,
                  push=self.push,
                  port_changed=self._port_changed,
                  workspace_changed=self._workspace_changed,
                  browse_workspace=self._browse_workspace)
        self._workspace_changed(view.workspace_path())

    def _port_changed(self, value):
        self.model.port = int(value)
        self.view.save_port(int(value))
        self.view.set_connection_status(False)

    def _workspace_changed(self, path):
        self.model.workspace = path.strip()
        self.view.save_workspace(path.strip())

    def _browse_workspace(self):
        path = self.view.browse_workspace()
        if path:
            self.view.set_workspace_path(path)
            self._workspace_changed(path)

    def _failure(self, title, exc):
        self.view.append_log('{}: {}'.format(title, exc))
        self.view.warning(title, str(exc))

    def check_connection(self, show_dialog=True):
        try:
            details = self.model.check_connection()
            self.view.set_connection_status(True, details=details)
            self.view.append_log('Connected: Blender {} | Scene {}'.format(
                details.get('blender_version', '?'), details.get('scene', '?')))
            return True
        except Exception as exc:
            self.view.set_connection_status(False, error=exc)
            self.view.append_log('Connection failed: {}'.format(exc))
            if show_dialog:
                self.view.warning('Connection failed',
                                  'Could not communicate with Blender MCP.\n{}'.format(exc))
            return False

    def _preflight(self):
        if self.check_connection(show_dialog=False):
            return True
        self.view.warning('Blender MCP not connected',
                          'Could not communicate with Blender MCP.\n'
                          'Check Blender MCP Running and TCP host/port.')
        return False

    def refresh_meshes(self):
        if not self._preflight():
            return
        try:
            meshes = self.model.list_blender_meshes()
            self.view.set_meshes(meshes)
            self.view.append_log('Found {} Blender mesh(es)'.format(len(meshes)))
        except Exception as exc:
            self._failure('Refresh failed', exc)

    def pull(self):
        if not self._preflight():
            return
        names = self.view.selected_blender_names()
        if not names:
            self._failure('No Blender meshes selected', 'Select meshes from the list.')
            return
        try:
            nodes = self.model.blender_to_maya(names, self.view.options())
            self.view.append_log('Imported {} Maya node(s). Transfer assets retained.'.format(len(nodes or [])))
        except Exception as exc:
            self._failure('Import to Maya failed', exc)

    def push(self):
        if not self._preflight():
            return
        try:
            nodes, response = self.model.maya_to_blender(self.view.options())
            self.view.append_log('Sent {} Maya mesh(es); Blender imported: {}'.format(
                len(nodes), response.get('imported')))
            self.view.append_log('Transfer assets retained in workspace.')
        except Exception as exc:
            self._failure('Send to Blender failed', exc)
