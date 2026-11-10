"""Model: official Blender Lab add-on TCP transport and FBX operations. No Qt.

IMPORTANT: this is NOT the stdio MCP protocol. It speaks the official Blender
Lab MCP add-on's underlying TCP wire protocol (NUL-delimited JSON messages).
"""
import json
import socket
import uuid
from pathlib import Path

from . import config
from .blender_commands import list_meshes_code, export_fbx_code, import_fbx_code


class BridgeError(RuntimeError):
    pass


class LabTcpClient:
    """Official Blender Lab TCP: {type: execute, code, strict_json}\0."""

    def __init__(self, host=config.HOST, port=config.DEFAULT_PORT):
        self.host = host
        self.port = int(port)
        if self.host not in ('127.0.0.1', 'localhost', '::1'):
            raise BridgeError('Only localhost is supported for safety.')

    @staticmethod
    def make_request(code):
        return {'type': 'execute', 'code': code, 'strict_json': True}

    @staticmethod
    def decode_response(response):
        if not isinstance(response, dict):
            raise BridgeError('Invalid Blender response (expected JSON object).')
        if response.get('status') != 'ok':
            raise BridgeError('Blender execution failed: {}'.format(
                response.get('message') or response.get('error') or repr(response)))
        return response.get('result')

    def execute(self, code, timeout=config.COMMAND_TIMEOUT):
        request = (json.dumps(self.make_request(code), ensure_ascii=False)
                   .encode('utf-8') + b'\0')
        try:
            sock = socket.create_connection((self.host, self.port),
                                            timeout=config.CONNECT_TIMEOUT)
        except (OSError, socket.timeout) as exc:
            raise BridgeError('TCP connect failed ({}:{}): {}'.format(
                self.host, self.port, exc)) from exc
        with sock:
            sock.settimeout(timeout)
            try:
                sock.sendall(request)
                chunks = bytearray()
                while True:
                    part = sock.recv(65536)
                    if not part:
                        raise BridgeError('Blender closed connection before a NUL-terminated response.')
                    chunks.extend(part)
                    if len(chunks) > config.MAX_RESPONSE_BYTES:
                        raise BridgeError('Blender response exceeds {} bytes'.format(config.MAX_RESPONSE_BYTES))
                    marker = chunks.find(b'\0')
                    if marker != -1:
                        payload = bytes(chunks[:marker])
                        break
            except socket.timeout as exc:
                raise BridgeError('Blender response timeout after {} seconds. '
                                  'Check Blender is idle and the add-on is running.'.format(timeout)) from exc
            except OSError as exc:
                raise BridgeError('Blender TCP send/receive failed: {}'.format(exc)) from exc
        try:
            response = json.loads(payload.decode('utf-8'))
        except (ValueError, UnicodeError) as exc:
            raise BridgeError('Invalid JSON response from Blender: {}'.format(exc)) from exc
        return self.decode_response(response)

    def ping(self):
        result = self.execute("import bpy\nresult = {'ping': 'pong', "
                              "'blender_version': bpy.app.version_string, "
                              "'scene': bpy.context.scene.name}", timeout=config.PING_TIMEOUT)
        if not isinstance(result, dict) or result.get('ping') != 'pong':
            raise BridgeError('Blender responded without expected ping: {!r}'.format(result))
        return result


def workspace_fbx(workspace, direction):
    """Reserve an FBX name in a persistent direction-specific workspace folder.

    FBX importers can extract embedded media into a sibling ``<stem>.fbm``
    directory. Unique stems prevent collisions between those media folders.
    Nothing is automatically deleted, including failed transfer artifacts.
    """
    if not workspace or not str(workspace).strip():
        raise BridgeError('Set a Workspace Folder before transferring FBX files.')
    folders = {
        'maya_to_blender': ('transfers_Maya2Blender', 'transfer_M2B_'),
        'blender_to_maya': ('transfers_Blender2Maya', 'transfer_B2M_'),
    }
    if direction not in folders:
        raise BridgeError('Unknown transfer direction: {!r}'.format(direction))
    folder_name, filename_prefix = folders[direction]
    try:
        root = Path(workspace).expanduser().resolve()
        folder = root / folder_name
        folder.mkdir(parents=True, exist_ok=True)
        if not folder.is_dir():
            raise OSError('Workspace destination is not a directory')
        # A unique name also gives an FBX importer a unique matching .fbm folder.
        return folder / '{}{}.fbx'.format(filename_prefix, uuid.uuid4().hex)
    except OSError as exc:
        raise BridgeError('Workspace is not writable or cannot be created: {}'.format(exc)) from exc


class BridgeModel:
    """Orchestrate Maya/Blender transfers; Blender and Maya must share a PC."""

    def __init__(self, port=config.DEFAULT_PORT, client_factory=LabTcpClient, workspace=None):
        self.port = int(port)
        self.workspace = workspace
        self._client_factory = client_factory

    def client(self):
        return self._client_factory(port=self.port)

    def check_connection(self):
        return self.client().ping()

    def list_blender_meshes(self):
        result = self.client().execute(list_meshes_code())
        if not isinstance(result, dict) or not isinstance(result.get('meshes'), list):
            raise BridgeError('Expected Blender result with meshes list; got: {!r}'.format(result))
        return result['meshes']

    def blender_to_maya(self, names, options):
        if not names:
            raise BridgeError('Select one or more meshes in the Blender mesh list.')
        from .maya_fbx import import_maya_fbx
        path = workspace_fbx(self.workspace, 'blender_to_maya')
        report = self.client().execute(export_fbx_code(names, path, **options),
                                       timeout=config.TRANSFER_TIMEOUT)
        if not isinstance(report, dict) or not report.get('exported'):
            raise BridgeError('Blender did not confirm an FBX export: {!r}'.format(report))
        if not path.is_file() or path.stat().st_size == 0:
            raise BridgeError('FBX was not written to the workspace transfer directory.')
        return import_maya_fbx(path, options['bones'], options['animation'])

    def maya_to_blender(self, options):
        from .maya_fbx import selected_maya_transforms, export_maya_fbx
        nodes = selected_maya_transforms()
        if not nodes:
            raise BridgeError('Select one or more Maya mesh transforms or mesh shapes.')
        path = workspace_fbx(self.workspace, 'maya_to_blender')
        export_maya_fbx(path, nodes, **options)
        result = self.client().execute(import_fbx_code(path, **options),
                                       timeout=config.TRANSFER_TIMEOUT)
        if not isinstance(result, dict) or 'imported' not in result:
            raise BridgeError('Blender did not confirm FBX import: {!r}'.format(result))
        return nodes, result
