from subprocess import Popen
import os

from django.utils.functional import cached_property

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


class AutoEnvironment(Environment):
    environments = [NodeEnvironment, RhinoEnvironment]

    @cached_property
    def environment(self):
        devnull = open(os.devnull)
        for environment in self.environments:
            environment = environment(self.env)
            args = environment.args()[:1]
            try:
                Popen(args, stdout=devnull, stderr=devnull).communicate()
            except OSError as e:
                if e.errno != os.errno.ENOENT:
                    raise
            else:
                return environment

        raise EnvironmentError("no environments detected: {envs}".format(
            envs=', '.join([ str(env) for env in self.environments ])))

    def args(self):
        return self.environment.args()
