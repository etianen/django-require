import os.path, shutil
from optparse import make_option

from django.core.management.base import NoArgsCommand, CommandError
from django.conf import settings

from require.settings import REQUIRE_BASE_URL, REQUIRE_BUILD_PROFILE, REQUIRE_JS, REQUIRE_STANDALONE_MODULES


class Command(NoArgsCommand):
    
    help = "Copy the base require.js files into your STATICFILES_DIRS."
    
    option_list = NoArgsCommand.option_list + (
        make_option(
            "-f",
            "--force",
            action = "store_true",
            dest = "force",
            default = False,
            help = "Overwrite existing files if found.", 
        ),
    )
    
    requires_model_validation = False
    
    def handle_noargs(self, **options):
        # Get the destination dir.
        staticfiles_dirs = getattr(settings, "STATICFILES_DIRS", ())
        if len(staticfiles_dirs) != 1:
            raise CommandError("Expected settings.STATICFILES_DIRS to contain one item, aborting.")
        dst_dir = staticfiles_dirs[0]
        # Calculate paths.
        resources_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "resources"))
        resources = [
            ("require.js", REQUIRE_JS),
            ("app.build.js", REQUIRE_BUILD_PROFILE),
        ]
        for _, standalone_config in REQUIRE_STANDALONE_MODULES.items():
            if "build_profile" in standalone_config:
                resources.append(("module.build.js", standalone_config["build_profile"]))
        # Check if the file exists.
        for resource_name, dst_name in resources:
            dst_path = os.path.abspath(os.path.join(dst_dir, REQUIRE_BASE_URL, dst_name))
            if os.path.exists(dst_path) and not options["force"]:
                self.stdout.write("{} already exists, skipping.\n".format(dst_path))
            else:
                shutil.copyfile(os.path.join(resources_dir, resource_name), dst_path)
                self.stdout.write("Copied {} to {}.\n".format(resource_name, dst_path))