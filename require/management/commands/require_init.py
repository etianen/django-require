from __future__ import unicode_literals

import os.path
import shutil
from optparse import make_option

from django.conf import settings
from django.core.management.base import CommandError, NoArgsCommand

from require.conf import settings as require_settings


def default_staticfiles_dir():
    staticfiles_dirs = getattr(settings, 'STATICFILES_DIRS', ())
    if len(staticfiles_dirs) == 0:
        return None
    return staticfiles_dirs[0]


class Command(NoArgsCommand):

    help = (
        'Copies the base require.js file into your STATICFILES_DIRS.\n\n'
        'Also copies default implementations of any build profiles listed in '
        'the REQUIRE_BUILD_PROFILE and REQUIRE_STANDALONE_MODULES settings.'
    )

    option_list = NoArgsCommand.option_list + (
        make_option(
            '-f',
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help='Overwrite existing files if found.',
        ),
        make_option(
            '-d',
            '--dir',
            action='store',
            dest='dir',
            help='Copy files into the named directory. Defaults to the first '
            'item in your STATICFILES_DIRS setting.',
        ),
    )

    requires_model_validation = False

    def handle_noargs(self, **options):
        verbosity = int(options.get('verbosity', 1))
        # Calculate the destination dir.
        dst_dir = options['dir'] or default_staticfiles_dir()
        if not dst_dir:
            raise CommandError(
                'settings.STATICFILES_DIRS is empty, and no --dir '
                'option specified')
        # Handle destination directory tuples.
        if isinstance(dst_dir, (list, tuple)):
            # Could do something more intelligent here with matching prefixes,
            # but is it worth it?
            dst_dir = dst_dir[1]
        # Calculate paths.
        resources_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'resources'))
        resources = [
            ('require.js', require_settings.REQUIRE_JS),
        ]
        if require_settings.REQUIRE_BUILD_PROFILE not in (False, None):
            resources.append(
                ('app.build.js', require_settings.REQUIRE_BUILD_PROFILE))
        for standalone_config in \
                require_settings.REQUIRE_STANDALONE_MODULES.values():
            if 'build_profile' in standalone_config:
                resources.append(
                    ('module.build.js', os.path.join(
                        standalone_config.get('relative_baseurl', ''),
                        standalone_config['build_profile'])))
        # Check if the file exists.
        for resource_name, dst_name in resources:
            dst_path = os.path.abspath(
                os.path.join(
                    dst_dir, require_settings.REQUIRE_BASE_URL, dst_name))
            if os.path.exists(dst_path) and not options['force']:
                if verbosity > 0:
                    self.stdout.write(
                        '{0} already exists, skipping.\n'.format(dst_path))
            else:
                dst_dirname = os.path.dirname(dst_path)
                if not os.path.exists(dst_dirname):
                    os.makedirs(dst_dirname)
                shutil.copyfile(
                    os.path.join(resources_dir, resource_name), dst_path)
                if verbosity > 0:
                    self.stdout.write(
                        'Copied {0} to {1}.\n'.format(resource_name, dst_path))
