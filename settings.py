"""Maya native optionVar persistent settings; no direct Qt dependencies."""
from maya import cmds

PREFIX = 'BlenderMeshPort_'


def get_string(name, default=''):
    key = PREFIX + name
    if not cmds.optionVar(exists=key):
        return default
    return str(cmds.optionVar(query=key))


def set_string(name, value):
    cmds.optionVar(stringValue=(PREFIX + name, str(value)))


def get_int(name, default=0):
    key = PREFIX + name
    if not cmds.optionVar(exists=key):
        return int(default)
    try:
        return int(cmds.optionVar(query=key))
    except (TypeError, ValueError):
        return int(default)


def set_int(name, value):
    cmds.optionVar(intValue=(PREFIX + name, int(value)))
