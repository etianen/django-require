from django.conf import settings

from require.storage import OptimizedStaticFilesStorage


class TestableOptimizedStaticFilesStorage(OptimizedStaticFilesStorage):
    
    """
    The location property for this storage is dynamically looked up from
    the django settings object, allowing it to be overridden at runtime.
    """
    
    @property
    def location(self):
        return settings.STATIC_ROOT
    
    @location.setter
    def location(self, value):
        pass