from require.conf import settings as require_settings
from require.helpers import import_module_attr


def load_backend():
    backend = require_settings.REQUIRE_BACKEND
    aliases = require_settings.REQUIRE_BACKEND_ALIASES
    backend = aliases.get(backend, backend)
    backend = import_module_attr(backend)
    return backend


class Backend(object):
    def __init__(self, environment):
        self.env = environment

    def args(self):
        raise NotImplementedError()


class AutoBackend(Backend):
    def args(self):
        backend = RhinoBackend(self.env)
        return backend.args()


class NodeBackend(Backend):
    def args(self):
        # Start of the command to run the compiler in Node.
        return ["node"]


class RhinoBackend(Backend):
    def args(self):
        # Start of the command to run the compiler in Java.
        return [
            "java",
            "-classpath",
            ":".join((
                self.env.resource_path("js.jar"),
                self.env.resource_path("compiler.jar"),
            )),
            "org.mozilla.javascript.tools.shell.Main"
        ]
