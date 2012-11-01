import os.path, shutil
from optparse import make_option

from django.core.management.base import NoArgsCommand
from django.conf import settings

from require.settings import REQUIRE_BASE_URL, REQUIRE_BUILD_PROFILE, REQUIRE_JS, REQUIRE_STANDALONE_MODULES


def default_staticfiles_dir():
    staticfiles_dirs = getattr(settings, "STATICFILES_DIRS", ())
    if len(staticfiles_dirs) == 0:
        return None
    return staticfiles_dirs[0]


class Command(NoArgsCommand):
    
    help = (
        "Copies the base require.js file into your STATICFILES_DIRS.\n\n"
        "Also copies default implementations of any build profiles listed in the REQUIRE_BUILD_PROFILE "
        "and REQUIRE_STANDALONE_MODULES settings."
    )
    
    option_list = NoArgsCommand.option_list + (
        make_option(
            "-f",
            "--force",
            action = "store_true",
            dest = "force",
            default = False,
            help = "Overwrite existing files if found.", 
        ),
        make_option(
            "-d",
            "--dir",
            action = "store",
            dest = "dir",
            default = default_staticfiles_dir(),
            help = "Copy files into the named directory. Defaults to the first item in your STATICFILES_DIRS setting.", 
        ),
    )
    
    requires_model_validation = False
    
    def handle_noargs(self, **options):
        verbosity = int(options.get("verbosity", 1))
        dst_dir = options["dir"]
        # Calculate paths.
        resources_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "resources"))
        resources = [
            ("require.js", REQUIRE_JS),
        ]
        if REQUIRE_BUILD_PROFILE is not None:
            resources.append(("app.build.js", REQUIRE_BUILD_PROFILE))
        for standalone_config in REQUIRE_STANDALONE_MODULES.values():
            if "build_profile" in standalone_config:
                resources.append(("module.build.js", standalone_config["build_profile"]))
        # Check if the file exists.
        for resource_name, dst_name in resources:
            dst_path = os.path.abspath(os.path.join(dst_dir, REQUIRE_BASE_URL, dst_name))
            if os.path.exists(dst_path) and not options["force"]:
                if verbosity > 0:
                    self.stdout.write("{} already exists, skipping.\n".format(dst_path))
            else:
                dst_dirname = os.path.dirname(dst_path)
                if not os.path.exists(dst_dirname):
                    os.makedirs(dst_dirname)
                shutil.copyfile(os.path.join(resources_dir, resource_name), dst_path)
                if verbosity > 0:
                    self.stdout.write("Copied {} to {}.\n".format(resource_name, dst_path))