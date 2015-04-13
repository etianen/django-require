from __future__ import unicode_literals

import tempfile, shutil, os.path, hashlib, subprocess
from functools import partial
from contextlib import closing

from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import File
from django.core.files.storage import FileSystemStorage
from django.contrib.staticfiles.storage import StaticFilesStorage, CachedStaticFilesStorage

from require.conf import settings as require_settings
from require.helpers import resolve_require_url
from require.environments import load_environment


class TemporaryCompileEnvironment(object):

    REQUIRE_RESOURCES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "resources"))

    def __init__(self, verbosity):
        self.compile_dir = tempfile.mkdtemp()
        self.build_dir = tempfile.mkdtemp()
        self.verbosity = verbosity

    def resource_path(self, name):
        return os.path.join(self.REQUIRE_RESOURCES_DIR, name)

    def compile_dir_path(self, name):
        return os.path.abspath(os.path.join(self.compile_dir, require_settings.REQUIRE_BASE_URL, name))

    def build_dir_path(self, name):
        return os.path.abspath(os.path.join(self.build_dir, require_settings.REQUIRE_BASE_URL, name))

    def run_optimizer(self, *args, **kwargs):
        # load the environment and initialize
        compiler = load_environment()(self)
        compiler_args = compiler.args()
        compiler_args.extend([self.resource_path("r.js"), "-o"])
        compiler_args.extend(args)
        if self.verbosity == 0:
            kwargs.setdefault("logLevel", "4")
        compiler_args.extend(
            "{0}={1}".format(
                key, value
            )
            for key, value
            in kwargs.items()
        )
        # Run the compiler in a subprocess.
        if subprocess.call(compiler_args) != 0:
            raise OptimizationError("Error while running r.js optimizer.")

    def __enter__(self):
        return self

    def __exit__(self, *args):
        shutil.rmtree(self.compile_dir, ignore_errors=True)
        shutil.rmtree(self.build_dir, ignore_errors=True)


class OptimizationError(Exception):

    pass


class OptimizedFilesMixin(object):

    REQUIRE_COPY_BLOCK_SIZE = 1024*1024  # 1 MB.

    def _file_iter(self, handle):
        return iter(partial(handle.read, self.REQUIRE_COPY_BLOCK_SIZE), b'')

    def post_process(self, paths, dry_run=False, verbosity=1, **options):
        # If this is a dry run, give up now!
        if dry_run:
            return
        # Compile in a temporary environment.
        with TemporaryCompileEnvironment(verbosity=verbosity) as env:
            exclude_names = list(require_settings.REQUIRE_EXCLUDE)
            compile_info = {}
            # Copy all assets into the compile dir.
            for name, storage_details in paths.items():
                storage, path = storage_details
                dst_path = os.path.join(env.compile_dir, name)
                dst_dir = os.path.dirname(dst_path)
                if not os.path.exists(dst_dir):
                    os.makedirs(dst_dir)
                # Copy and generate md5
                hash = hashlib.md5()
                with closing(storage.open(path, "rb")) as src_handle:
                    with open(dst_path, "wb") as dst_handle:
                        for block in self._file_iter(src_handle):
                            hash.update(block)
                            dst_handle.write(block)
                # Store details of file.
                compile_info[name] = hash.digest()
            # Run the optimizer.
            if require_settings.REQUIRE_BUILD_PROFILE is not False:
                if require_settings.REQUIRE_BUILD_PROFILE is not None:
                    app_build_js_path = env.compile_dir_path(require_settings.REQUIRE_BUILD_PROFILE)
                else:
                    app_build_js_path = env.resource_path("app.build.js")
                env.run_optimizer(
                    app_build_js_path,
                    dir = env.build_dir,
                    appDir = env.compile_dir,
                    baseUrl = require_settings.REQUIRE_BASE_URL,
                )
            # Compile standalone modules.
            if require_settings.REQUIRE_STANDALONE_MODULES:
                shutil.copyfile(
                    env.resource_path("almond.js"),
                    env.compile_dir_path("almond.js"),
                )
                exclude_names.append(resolve_require_url("almond.js"))
            for standalone_module, standalone_config in require_settings.REQUIRE_STANDALONE_MODULES.items():
                if "out" in standalone_config:
                    if "build_profile" in standalone_config:
                        module_build_js_path = env.compile_dir_path(standalone_config["build_profile"])
                    else:
                        module_build_js_path = env.resource_path("module.build.js")
                    env.run_optimizer(
                        module_build_js_path,
                        name = "almond",
                        include = standalone_module,
                        out = env.build_dir_path(standalone_config["out"]),
                        baseUrl = os.path.join(env.compile_dir, require_settings.REQUIRE_BASE_URL),
                    )
                else:
                    raise ImproperlyConfigured("No 'out' option specified for module '{module}' in REQUIRE_STANDALONE_MODULES setting.".format(
                        module = standalone_module
                    ))
            # Update assets with modified ones.
            compiled_storage = FileSystemStorage(env.build_dir)
            # Walk the compiled directory, checking for modified assets.
            for build_dirpath, _, build_filenames in os.walk(env.build_dir):
                for build_filename in build_filenames:
                    # Determine asset name.
                    build_filepath = os.path.join(build_dirpath, build_filename)
                    build_name = build_filepath[len(env.build_dir)+1:]
                    build_storage_name = build_name.replace(os.sep, "/")
                    # Ignore certain files.
                    if build_storage_name in exclude_names:
                        # Delete from storage, if originally present.
                        if build_name in compile_info:
                            del paths[build_name]
                            self.delete(build_storage_name)
                        continue
                    # Update the asset.
                    with File(open(build_filepath, "rb"), build_storage_name) as build_handle:
                        # Calculate asset hash.
                        hash = hashlib.md5()
                        for block in self._file_iter(build_handle):
                            hash.update(block)
                        build_handle.seek(0)
                        # Check if the asset has been modifed.
                        if build_name in compile_info:
                            # Get the hash of the new file.
                            if hash.digest() == compile_info[build_name]:
                                continue
                        # If we're here, then the asset has been modified by the build script! Time to re-save it!
                        paths[build_name] = (compiled_storage, build_name)
                        # It's definitely time to save this file.
                        self.delete(build_storage_name)
                        self.save(build_storage_name, build_handle)
                        # Report on the modified asset.
                        yield build_name, build_name, True
            # Report on modified assets.
            super_class = super(OptimizedFilesMixin, self)
            if hasattr(super_class, "post_process"):
                for path in super_class.post_process(paths, dry_run, **options):
                    yield path


class OptimizedStaticFilesStorage(OptimizedFilesMixin, StaticFilesStorage):

    pass


class OptimizedCachedStaticFilesStorage(OptimizedFilesMixin, CachedStaticFilesStorage):

    pass


try:
    from django.contrib.staticfiles.storage import ManifestStaticFilesStorage
except ImportError:  # Django < 1.7
    pass
else:
    class OptimizedManifestStaticFilesStorage(OptimizedFilesMixin, ManifestStaticFilesStorage):

        pass
