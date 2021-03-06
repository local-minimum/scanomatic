from __future__ import absolute_import
from datetime import datetime
import os

import pytz


class ImageNotFoundError(LookupError):
    pass


class ImageStore(object):
    def __init__(self, path):
        self._path = path

    def put(self, image, scan):
        imagepath = self._mk_image_path(scan)
        dirpath = os.path.dirname(imagepath)
        if not os.path.isdir(dirpath):
            os.makedirs(dirpath)
        with open(imagepath, 'w') as f:
            f.write(image)
            f.flush()
            os.fsync(f)

    def get(self, scan):
        imagepath = self._mk_image_path(scan)
        try:
            with open(imagepath, 'rb') as f:
                return f.read()
        except IOError:
            raise ImageNotFoundError

    def _mk_image_path(self, scan):
        dirname = scan.scanjob_id
        filename = '{}.tiff'.format(scan.id)
        return os.path.join(self._path, dirname, filename)
