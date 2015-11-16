from __future__ import unicode_literals

import hashlib
import os.path
import shutil
import subprocess
import tempfile
from contextlib import closing

from django.contrib.staticfiles.storage import (
    CachedStaticFilesStorage, StaticFilesStorage)
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import File
from django.core.files.storage import FileSystemStorage

from require.conf import settings as require_settings
from require.environments import load_environment
from require.helpers import resolve_require_url


class TemporaryCompileEnvironment(object):

    REQUIRE_RESOURCES_DIR = os.path.abspath(
        os.path.join(os.path.dirname(__file__), 'resources'))

    def __init__(self, verbosity):
        self.compile_dir = tempfile.mkdtemp()
        self.build_dir = tempfile.mkdtemp()
        self.verbosity = verbosity

    def resource_path(self, name):
        return os.path.join(self.REQUIRE_RESOURCES_DIR, name)

    def compile_dir_path(self, name):
        return os.path.abspath(
            os.path.join(
                self.compile_dir, require_settings.REQUIRE_BASE_URL, name))

    def build_dir_path(self, name):
        return os.path.abspath(
            os.path.join(
                self.build_dir, require_settings.REQUIRE_BASE_URL, name))

    def run_optimizer(self, *args, **kwargs):
        # load the environment and initialize
        compiler = load_environment()(self)
        compiler_args = compiler.args()
        compiler_args.extend([self.resource_path('r.js'), '-o'])
        compiler_args.extend(args)
        if self.verbosity == 0:
            kwargs.setdefault('logLevel', '4')
        compiler_args.extend(
            '{0}={1}'.format(
                key, value
            )
            for key, value
            in kwargs.items()
        )
        # Run the compiler in a subprocess.
        if subprocess.call(compiler_args) != 0:
            raise OptimizationError('Error while running r.js optimizer.')

    def __enter__(self):
        return self

    def __exit__(self, *args):
        shutil.rmtree(self.compile_dir, ignore_errors=True)
        shutil.rmtree(self.build_dir, ignore_errors=True)


class OptimizationError(Exception):
    pass


class OptimizedFilesMixin(object):

    REQUIRE_COPY_BLOCK_SIZE = 1024 * 1024  # 1 MB.
    files_md5 = {}
    env = None
    paths = {}
    compiled_storage = None

    def _file_iter(self, handle):
        yield handle.read(self.REQUIRE_COPY_BLOCK_SIZE)

    def _prepare_assets(self):
        """
        Copy all assets into the compile dir, while calculating and
        storing their MD5 hashes.
        """
        for name, storage_details in self.paths.items():
            storage, path = storage_details
            dst_path = os.path.join(self.env.compile_dir, name)
            dst_dir = os.path.dirname(dst_path)
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)
            # Copy and generate md5
            hash_md5 = hashlib.md5()
            with closing(storage.open(path, 'rb')) as src_handle:
                with open(dst_path, 'wb') as dst_handle:
                    for block in self._file_iter(src_handle):
                        hash_md5.update(block)
                        dst_handle.write(block)
            # Store md5 hash of file.
            self.files_md5[name] = hash_md5.digest()

    def _run_optimizer(self):
        if require_settings.REQUIRE_BUILD_PROFILE is False:
            return
        if require_settings.REQUIRE_BUILD_PROFILE is not None:
            app_build_js_path = self.env.compile_dir_path(
                require_settings.REQUIRE_BUILD_PROFILE)
        else:
            app_build_js_path = self.env.resource_path('app.build.js')
        self.env.run_optimizer(
            app_build_js_path,
            dir=self.env.build_dir,
            appDir=self.env.compile_dir,
            baseUrl=require_settings.REQUIRE_BASE_URL,
        )

    def _setup_if_standalone(self):
        if require_settings.REQUIRE_STANDALONE_MODULES:
            shutil.copyfile(
                self.env.resource_path('almond.js'),
                self.env.compile_dir_path('almond.js'),
            )
            self.exclude_names.append(resolve_require_url('almond.js'))

    def _iterate_standalones(self, standalone_module, standalone_config):
        if 'out' not in standalone_config:
            # No out section, early exit.
            raise ImproperlyConfigured(
                'No \'out\' option specified for module \'{module}\' '
                'in REQUIRE_STANDALONE_MODULES setting.'.format(
                    module=standalone_module
                ))
        relative_baseurl = standalone_config.get('relative_baseurl', '')
        if 'build_profile' in standalone_config:
            module_build_js_path = self.env.compile_dir_path(os.path.join(
                relative_baseurl, standalone_config['build_profile']))
        else:
            module_build_js_path = self.env.resource_path(
                'module.build.js')
        entry_file_name = standalone_config.get('entry_file_name')
        if entry_file_name is not None:
            entry_file_name = os.path.join(relative_baseurl, entry_file_name)
        else:
            entry_file_name = standalone_module
        self.env.run_optimizer(
            module_build_js_path,
            name='almond',
            include=entry_file_name,
            out=self.env.build_dir_path(
                os.path.join(relative_baseurl, standalone_config['out'])),
            baseUrl=os.path.join(
                self.env.compile_dir,
                require_settings.REQUIRE_BASE_URL,
                relative_baseurl))

    def _check_if_modified(self, build_dirpath, build_filename):
        # Determine asset name.
        build_filepath = os.path.join(build_dirpath, build_filename)
        build_name = build_filepath[len(self.env.build_dir) + 1:]
        build_storage_name = build_name.replace(os.sep, '/')
        # Ignore certain files.
        if build_storage_name in self.exclude_names:
            # Delete from storage, if originally present.
            if build_name in self.files_md5:
                del self.paths[build_name]
                self.delete(build_storage_name)
            return
        # Update the asset.
        with File(open(
                build_filepath, 'rb'), build_storage_name) as build_handle:
            # Calculate asset hash.
            hash_md5 = hashlib.md5()
            for block in self._file_iter(build_handle):
                hash_md5.update(block)
            build_handle.seek(0)
            # Check if the asset has been modifed.
            if build_name in self.files_md5:
                # Get the hash of the new file.
                if hash_md5.digest() == self.files_md5[build_name]:
                    return
            # If we're here, then the asset has been modified by
            # the build script! Time to re-save it!
            self.paths[build_name] = (self.compiled_storage, build_name)
            # It's definitely time to save this file.
            self.delete(build_storage_name)
            self.save(build_storage_name, build_handle)
            # Report on the modified asset.
            return build_name, build_name, True

    def _run_post_process(self, paths, dry_run, options):
        self._prepare_assets()

        # Run the optimizer.
        self._run_optimizer()

        # Compile standalone modules.
        self._setup_if_standalone()
        standalone_items = require_settings.REQUIRE_STANDALONE_MODULES.items()
        for standalone_module, standalone_config in standalone_items:
            self._iterate_standalones(standalone_module, standalone_config)

        # Update assets with modified ones.
        self.compiled_storage = FileSystemStorage(self.env.build_dir)

        # Walk the compiled directory, checking for modified assets.
        for build_dirpath, _, build_filenames in os.walk(self.env.build_dir):
            for build_filename in build_filenames:
                ret_value = self._check_if_modified(
                    build_dirpath, build_filename)
                if ret_value is not None:
                    yield ret_value

        # Report on modified assets.
        super_class = super(OptimizedFilesMixin, self)
        if hasattr(super_class, 'post_process'):
            for path in super_class.post_process(paths, dry_run, **options):
                yield path

    def post_process(self, paths, dry_run=False, verbosity=1, **options):
        # If this is a dry run, give up now!
        if dry_run:
            # We're an iterator function, so return an empty iterator.
            return range(0)
        # Compile in a temporary environment.
        with TemporaryCompileEnvironment(verbosity=verbosity) as env:
            self.env = env
            self.paths = paths
            self.exclude_names = list(require_settings.REQUIRE_EXCLUDE)
            return self._run_post_process(paths, dry_run, options)


class OptimizedStaticFilesStorage(OptimizedFilesMixin, StaticFilesStorage):
    pass


class OptimizedCachedStaticFilesStorage(
        OptimizedFilesMixin, CachedStaticFilesStorage):
    pass


try:
    from django.contrib.staticfiles.storage import ManifestStaticFilesStorage
except ImportError:  # pragma: no cover, Django < 1.7
    pass
else:
    class OptimizedManifestStaticFilesStorage(
            OptimizedFilesMixin, ManifestStaticFilesStorage):

        pass
