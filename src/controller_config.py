#!/usr/bin/env python
"""The Config Controller"""
__author__ = "Martin Zackrisson"
__copyright__ = "Swedish copyright laws apply"
__credits__ = ["Martin Zackrisson"]
__license__ = "GPL v3.0"
__version__ = "0.997"
__maintainer__ = "Martin Zackrisson"
__email__ = "martin.zackrisson@gu.se"
__status__ = "Development"

#
# DEPENDENCIES
#

import re
import os
import subprocess
import tarfile
import glob

#
# INTERNAL DEPENDENCIES
#

import src.model_config as model_config
import src.view_config as view_config
import src.controller_generic as controller_generic

#
# EXCEPTIONS
#

class Bad_Stage_Call(Exception): pass
class Could_Not_Save_Log_And_State(Exception): pass

#
# FUNCTIONS
#


class Config_Controller(controller_generic.Controller):

    def __init__(self, main_controller, logger=None):

        super(Config_Controller, self).__init__(main_controller,
            logger=logger)

        self._paths = self.get_top_controller().paths

    def _get_default_view(self):

        return view_config.Config_View(self, self._model)

    def _get_default_model(self):

        return model_config.get_gui_model()

    def make_state_backup(self, widget):

        target_list = view_config.save_file(
            self._model['config-log-save-dialog'],
            multiple_files=False,
            file_filter=self._model['config-log-file-filter'],
            start_in=self.get_top_controller().paths.experiment_root)

        if target_list is not None and len(target_list) == 1:

            tc = self.get_top_controller()
            paths = tc.paths

            try:
                fh = tarfile.open(target_list[0], 'w:gz')
            except:
                raise Could_Not_Save_Log_And_State(target_list[0])
                return False

            save_paths = list()
            save_paths.append(paths.fixture_conf_file_pattern.format("*"))
            save_paths.append(paths.lock_root + "*")
            save_paths.append(paths.log_scanner_out.format("*"))
            save_paths.append(paths.log_scanner_err.format("*"))
            save_paths.append(paths.log_main_out)
            save_paths.append(paths.log_main_err)

            tc.close_simple_logger()

            for pattern in save_paths:

                for p in glob.iglob(pattern):

                    fh.add(p, arcname=os.path.basename(p), recursive=False)

            fh.close()
            tc.set_simple_logger()

            view_config.dialog(self.get_window(), 
                self._model['config-log-save-done'],
                d_type="info", yn_buttons=False)

            return True

    def set_desktop_shortcut(self, widget):

        desktop_path = self.get_desktop_path()
        source_path = self._paths.desktop_file_path
        target_path = os.sep.join((desktop_path, self._paths.desktop_file))

        try:
            fh = open(source_path, 'r')
            cont = fh.read()
            fh.close()
        except:
            cont = None

        if cont is not None:

            f_dict = {
                'version': __version__,
                'icon': os.sep.join((self._paths.images, 
                        'scan-o-matic_icon_48_48.png')),
                'exec': self._paths.scanomatic,
                'name': 'Scan-o-Matic' }

            cont = cont.format(**f_dict)

            try:

                fh = open(target_path, 'w')
                fh.write(cont)
                fh.close()
            except:
                self._logger.error('Could not create desktop short-cut properly')
                return

            os.chmod(target_path, 0777)

        else:

            self._logger.error('Could not find desktop short-cut template')
            return

        view_config.dialog(self.get_window(), 
            self._model['config-desktop-short_cut-made'],
            d_type="info", yn_buttons=False)

    def get_desktop_path(self):

        """
        D_paths = list()

        try:

            fs = open(os.sep.join((os.path.expanduser("~"), ".config", "user-dirs.dirs")),'r')
            data = fs.read()
            fs.close()
        except:
            data = ""

        D_paths = re.findall(r'XDG_DESKTOP_DIR=\"([^\"]*)', data)

        if len(D_paths) == 1:
            D_path = D_paths[0]
            D_path = re.sub(r'\$HOME', os.path.expanduser("~"), D_path)

        else:
            D_path = os.sep.join((os.path.expanduser("~"), 'Desktop'))
        """
        try:
            D_path = subprocess.check_output(['xdg-user-dir', 'DESKTOP'])
            return D_path
        except:
            return None