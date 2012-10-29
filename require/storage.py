import tempfile, shutil, os.path, hashlib, subprocess, re
from functools import partial

from django.core.files.base import File
from django.contrib.staticfiles.storage import StaticFilesStorage

from require.settings import REQUIRE_BUILD_PROFILE


class OptimizedMixin(object):
    
    COPY_BLOCK_SIZE = 1024*1024  # 1 MB.
    
    EXCLUDE_PATTERNS = (
        re.escape("build.txt"),
    )
    
    def _file_iter(self, handle):
        return iter(partial(handle.read, self.COPY_BLOCK_SIZE), "")
    
    def post_process(self, paths, dry_run=False, **options):
        # If this is a dry run, give up now!
        if dry_run:
            return
        # Determine paths to resources.
        resources_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "resources"))
        rhino_jar_path = os.path.join(resources_dir, "js.jar")
        compiler_jar_path = os.path.join(resources_dir, "compiler.jar")
        r_js_path = os.path.join(resources_dir, "r.js")
        # Create the temporary compile dirs.
        compile_dir = tempfile.mkdtemp()
        build_dir = tempfile.mkdtemp()
        try:
            compile_info = {}
            # Copy all assets into the compile dir. 
            for name, storage_details in paths.items():
                storage, path = storage_details
                src_path = storage.path(path)
                dst_path = os.path.join(compile_dir, path)
                dst_dir = os.path.dirname(dst_path)
                if not os.path.exists(dst_dir):
                    os.makedirs(dst_dir)
                # Copy and generate md5
                hash = hashlib.sha1()
                with open(src_path, "rb") as src_handle, open(dst_path, "wb") as dst_handle:
                    for block in self._file_iter(src_handle):
                        hash.update(block)
                        dst_handle.write(block)
                # Store details of file.
                compile_info[name] = hash.digest()
            # Run the optimizer.
            app_build_js_path = os.path.join(compile_dir, REQUIRE_BUILD_PROFILE)
            compiler_result = subprocess.call((
                "java",
                "-classpath",
                ":".join((rhino_jar_path, compiler_jar_path)),
                "org.mozilla.javascript.tools.shell.Main",
                r_js_path,
                "-o",
                app_build_js_path,
                "dir={}".format(build_dir),
                "appDir={}".format(compile_dir),
            ))
            # Compile the exclude patterns.
            exclude_patterns = [
                re.compile(pattern)
                for pattern
                in self.EXCLUDE_PATTERNS + (re.escape(REQUIRE_BUILD_PROFILE),)
            ]
            # Update assets with modified ones.
            if compiler_result == 0:
                # Walk the compiled directory, checking for modified assets.
                for build_dirpath, _, build_filenames in os.walk(build_dir):
                    for build_filename in build_filenames:
                        # Determine asset name.
                        build_filepath = os.path.join(build_dirpath, build_filename)
                        build_name = build_filepath[len(build_dir)+1:]
                        # Ignore certain files.
                        if any(pattern.match(build_name) for pattern in exclude_patterns):
                            # Delete from storage, if originally present.
                            if build_name in compile_info:
                                self.delete(build_name)
                            continue
                        # Determine if asset should be updated.
                        with open(build_filepath, "rb") as build_handle:
                            # Calculate asset hash.
                            hash = hashlib.sha1()
                            for block in self._file_iter(build_handle):
                                hash.update(block)
                            build_handle.seek(0)
                            # Check if the asset has been modifed.
                            if build_name in compile_info:
                                # Get the hash of the new file.
                                if hash.digest() == compile_info[build_name]:
                                    continue
                            # If we're here, then the asset has been modified by the build script! Time to re-save it!
                            self.delete(build_name)
                            self.save(build_name, File(build_handle, build_name))
                            # Report on the modified asset.
                            yield build_name, build_name, True
        finally:
            # Clean up compile dirs.
            shutil.rmtree(compile_dir, ignore_errors=True)
            shutil.rmtree(build_dir, ignore_errors=True)
            
        
        
class OptimizedStaticFilesStorage(OptimizedMixin, StaticFilesStorage):
    
    pass