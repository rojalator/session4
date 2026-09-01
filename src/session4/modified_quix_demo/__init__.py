from pathlib import Path

from quixote import enable_ptl
from quixote.publish import Publisher

enable_ptl()
from modified_quix_demo.root import RootDirectory


def create_publisher() -> Publisher:
    print('**** RUNNING from ', Path.cwd())

    return Publisher(RootDirectory(), display_exceptions='plain')
