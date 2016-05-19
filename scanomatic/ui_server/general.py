import glob
import os
import re
from itertools import chain

from scanomatic.io.app_config import Config
from scanomatic.io.paths import Paths
from scanomatic.models.factories.scanning_factory import ScanningModelFactory


_safe_dir = re.compile(r"^[A-Za-z_0-9./]*$")
_no_super = re.compile(r"/?\.{2}/")


def safe_directory_name(name):
    return _safe_dir.match(name) is not None and _no_super.search(name) is None


def convert_url_to_path(url):
    if url is None:
        url = ""
    else:
        url = url.split("/")
    root = Config().paths.projects_root
    return os.path.abspath(os.path.join(*chain([root], url)))


def convert_path_to_url(prefix, path):
    if prefix:
        path = "/".join(chain([prefix], os.path.relpath(path, Config().paths.projects_root).split(os.sep)))
    else:
        path = "/".join(os.path.relpath(path, Config().paths.projects_root).split(os.sep))

    if safe_directory_name(path):
        return path
    return None


def path_is_in_jail(path):

    return Config().paths.projects_root in path


def get_search_results(path, url_prefix):

    projects = _get_possible_paths(path)
    names = list(get_project_name(p) for p in projects)
    urls = list(convert_path_to_url(url_prefix, p) for p in projects)
    if None in urls:
        try:
            names, urls = zip(*tuple((n, u) for n, u in zip(names, urls) if u is not None))
        except ValueError:
            pass
    return {'names': names, 'urls': urls}


def _get_possible_paths(path):

    dirs = tuple()
    root = None
    for root, dirs, _ in os.walk(path, followlinks=True):
        break

    if root is None:
        return tuple()
    return tuple(os.path.join(root, d) for d in dirs)


def get_project_name(project_path):
    no_name = None

    if not path_is_in_jail(project_path):
        return no_name

    candidates = glob.glob(os.path.join(project_path, Paths().scan_project_file_pattern.format("*")))
    if candidates:
        for candidate in candidates:
            model = ScanningModelFactory.serializer.load_first(candidate)
            if model:
                return model.project_name if model.project_name else no_name

    if project_path:
        return get_project_name(os.path.dirname(project_path))

    return no_name


def strip_empty_exits(exits, data):
    """
        :param exits : Exit keys
        :type exits : list[str]

        :param data : Data dict
        :type data : dict
    """
    all_exits = [e for e in exits]
    for e in all_exits:
        if e in data and len(data[e]) == 0:
            del data[e]
            exits.remove(e)
        elif e not in data:
            exits.remove(e)


def json_response(exits, data, success=True):

    strip_empty_exits(exits, data)
    is_endpoint = len(exits) == 0
    data["is_endpoint"] = is_endpoint

    if success is not None:
        data["success"] = success

    if is_endpoint:
        if "exits" in data:
            del data["exits"]
    else:
        data["exits"] = exits

    return data
