import typing

# For an explanation why these next lines are so complicated, see
# https://confluence.lsstcorp.org/pages/viewpage.action?spaceKey=LTS&title=Enabling+Mypy+in+Pytest
if typing.TYPE_CHECKING:
    __version__ = "?"
else:
    try:
        import pkg_resources

        __version__ = pkg_resources.get_distribution("rubintv").version
    except:
        __version__ = "?"


# Expose the app to others
from .main import app
