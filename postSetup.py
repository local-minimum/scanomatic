import os
import shutil
import sys
import glob
import stat

import scanomatic.io.logger as logger

_logger = logger.Logger("Post Install")

homeDir = os.path.expanduser("~")

defaltPermission = 0644
installPath = ".scan-o-matic"
defaultSourceBase = "data"

data_files = [
    ('config', {'calibration.polynomials': False,
                'calibration.data': False,
                'grayscales.cfg': False,
                'rpc.config': False,
                'scan-o-matic.desktop': True}),
    (os.path.join('config', 'fixtures'), {}),
    ('logs', {}),
    ('locks', {}),
    ('images', None),
    ('ui_server', None)
]


_launcher_text = """[Desktop Entry]
Type=Application
Terminal=false
Icon={user_home}/.scan-o-matic/images/scan-o-matic_icon_256_256.png
Name=Scan-o-Matic
Comment=Large-scale high-quality phenomics platform
Exec={executable_path}
Categories=Science;
"""


def _clone_all_files_in(path):

    for child in glob.glob(os.path.join(path, "*")):
        local_child = child[len(path) + (not path.endswith(os.sep) and 1 or 0):]
        if os.path.isdir(child):
            for grandchild, _ in _clone_all_files_in(child):
                yield os.path.join(local_child, grandchild), True
        else:
            yield local_child, True


def install_data_files(target_base=None, source_base=None, install_list=None):

    if target_base is None:
        target_base = os.path.join(homeDir, installPath)

    if source_base is None:
        source_base = defaultSourceBase

    if install_list is None:
        install_list = data_files

    if not os.path.isdir(target_base):
        os.mkdir(target_base)
        os.chmod(target_base, 0755)

    for install_instruction in install_list:

        relative_directory, files = install_instruction
        source_directory = os.path.join(source_base, relative_directory)
        target_directory = os.path.join(target_base, relative_directory)

        if not os.path.isdir(target_directory):
            os.makedirs(target_directory, 0755)

        if files is None:
            files = dict(_clone_all_files_in(source_directory))
            print files

        for file_name in files:

            source_path = os.path.join(source_directory, file_name)
            target_path = os.path.join(target_directory, file_name)

            if not os.path.isdir(os.path.dirname(target_path)):
                os.makedirs(os.path.dirname(target_path), 0755)

            if not os.path.isfile(target_path) and files[file_name] is None:
                _logger.info("Creating file {0}".format(target_path))
                fh = open(target_path, 'w')
                fh.close()
            elif (not os.path.isfile(target_path) or files[file_name]
                    or 'y' in raw_input(
                        "Do you want to overwrite {0} (y/N)".format(
                            target_path)).lower()):

                _logger.info(
                    "Copying file: {0} => {1}".format(
                        source_path, target_path))

                shutil.copy(source_path, target_path)
                os.chmod(target_path, defaltPermission)


def linux_launcher_install():

    user_home = os.path.expanduser("~")
    exec_path = os.path.join(user_home, '.local', 'bin', 'scan-o-matic')
    if not os.path.isfile(exec_path):
        exec_path = os.path.join(os.sep, 'usr', 'local', 'bin', 'scan-o-matic')
    text = _launcher_text.format(user_home=user_home, executable_path=exec_path)
    target = os.path.join(user_home, '.local', 'share','applications', 'scan-o-matic.desktop')
    with open(target, 'w') as fh:
        fh.write(text)

    os.chmod(target, os.stat(target)[stat.ST_MODE] | stat.S_IXUSR)
    _logger.info("Installed desktop launcher for linux menu/dash etc.")

def install_launcher():

    if os.name == 'posix':
        linux_launcher_install()
    else:
        _logger.warning("Don't know how to install launchers for this os...")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'install':
        install_data_files()

    install_launcher()