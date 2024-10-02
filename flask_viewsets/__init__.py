"""Module initializing the Flask-Viewsets package.

It imports the ViewSets class from the extension module and making it available for
import when the package is imported.

Classes:
    ViewSets: A class that provides viewset functionality for Flask applications.

__all__:
    A tuple that defines the public interface of the module, containing:
        - "ViewSets": The ViewSets class.
"""

from .extension import ViewSets

__all__ = ("ViewSets",)
