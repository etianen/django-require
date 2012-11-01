from django.contrib.staticfiles.finders import FileSystemFinder


class TestableFileSystemFinder(FileSystemFinder):
    
    """
    This finder re-inits at the start of each method, allowing the STATICFILES_DIRS
    settings to be overridden at runtime.
    """
    
    def find(self, *args, **kwargs):
        self.__init__()
        return super(TestableFileSystemFinder, self).find(*args, **kwargs)

    def find_location(self, *args, **kwargs):
        self.__init__()
        return super(TestableFileSystemFinder, self).find_location(*args, **kwargs)

    def list(self, *args, **kwargs):
        self.__init__()
        return super(TestableFileSystemFinder, self).list(*args, **kwargs)