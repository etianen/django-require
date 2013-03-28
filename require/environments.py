from require.conf import settings as require_settings
from require.helpers import import_module_attr


def load_environment():
    environment = require_settings.REQUIRE_ENVIRONMENT
    aliases = require_settings.REQUIRE_ENVIRONMENT_ALIASES
    environment = aliases.get(environment, environment)
    environment = import_module_attr(environment)
    return environment


class Environment(object):
    def __init__(self, environment):
        self.env = environment

    def args(self):
        raise NotImplementedError()


class AutoEnvironment(Environment):
    def args(self):
        environment = RhinoEnvironment(self.env)
        return environment.args()


class NodeEnvironment(Environment):
    def args(self):
        # Start of the command to run the compiler in Node.
        return ["node"]


class RhinoEnvironment(Environment):
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
