"""Controller: connect native Maya GUI actions to transfer operations."""

from .model import BridgeModel


class MeshPortController:
    """Event coordination only; Blender/Maya operations stay in the model."""

    def __init__(self, view, model=None):
        self.view = view
        self.model = model if model is not None else BridgeModel(port=view.port_value())
        self.view.bind(
            check_connection=self.check_connection,
            refresh_meshes=self.refresh_meshes,
            pull=self.pull,
            push=self.push,
            port_changed=self._port_changed,
            workspace_changed=self._workspace_changed,
            browse_workspace=self._browse_workspace,
        )
        self._workspace_changed(view.workspace_path())

    def _port_changed(self, value):
        self.model.port = int(value)
        self.view.save_port(int(value))
        self.view.set_connection_status(False)

    def _workspace_changed(self, path):
        workspace = path.strip()
        self.model.workspace = workspace
        self.view.save_workspace(workspace)

    def _browse_workspace(self):
        path = self.view.browse_workspace()
        if path:
            self.view.set_workspace_path(path)
            self._workspace_changed(path)

    def _failure(self, title, error):
        self.view.append_log('{}: {}'.format(title, error))
        self.view.warning(title, str(error))

    def check_connection(self, show_dialog=True):
        try:
            details = self.model.check_connection()
        except Exception as error:
            self.view.set_connection_status(False, error=error)
            self.view.append_log('Connection failed: {}'.format(error))
            if show_dialog:
                self.view.warning(
                    'Connection failed',
                    'Could not communicate with Blender MCP.\n{}'.format(error),
                )
            return False

        self.view.set_connection_status(True, details=details)
        self.view.append_log('Connected: Blender {} | Scene {}'.format(
            details.get('blender_version', '?'), details.get('scene', '?')
        ))
        return True

    def _preflight(self):
        if self.check_connection(show_dialog=False):
            return True
        self.view.warning(
            'Blender MCP not connected',
            'Could not communicate with Blender MCP.\n'
            'Check Blender MCP Running and TCP host/port.',
        )
        return False

    def _run_transfer(self, title, action):
        """Handle connection preflight and transfer errors in one place."""
        if not self._preflight():
            return
        try:
            action()
        except Exception as error:
            self._failure(title, error)

    def refresh_meshes(self):
        def action():
            meshes = self.model.list_blender_meshes()
            self.view.set_meshes(meshes)
            self.view.append_log('Found {} Blender mesh(es)'.format(len(meshes)))

        self._run_transfer('Refresh failed', action)

    def pull(self):
        def action():
            names = self.view.selected_blender_names()
            if not names:
                raise ValueError('Select meshes from the Blender mesh list.')
            nodes = self.model.blender_to_maya(names, self.view.options())
            self.view.append_log(
                'Imported {} Maya node(s). Transfer assets retained.'.format(
                    len(nodes or [])
                )
            )

        self._run_transfer('Import to Maya failed', action)

    def push(self):
        def action():
            nodes, response = self.model.maya_to_blender(self.view.options())
            self.view.append_log(
                'Sent {} Maya mesh(es); Blender imported: {}'.format(
                    len(nodes), response.get('imported')
                )
            )
            self.view.append_log('Transfer assets retained in workspace.')

        self._run_transfer('Send to Blender failed', action)
