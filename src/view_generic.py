#!/usr/bin/env python
"""The GTK-GUI view"""
__author__ = "Martin Zackrisson"
__copyright__ = "Swedish copyright laws apply"
__credits__ = ["Martin Zackrisson"]
__license__ = "GPL v3.0"
__version__ = "0.998"
__maintainer__ = "Martin Zackrisson"
__email__ = "martin.zackrisson@gu.se"
__status__ = "Development"

#
# DEPENDENCIES
#

import pygtk
pygtk.require('2.0')
import gtk
import numpy

#
# INTERNAL DEPENDENCIES
#

import src.resource_scanner as resource_scanner

#
# STATIC GLOBALS
#

PADDING_LARGE = 10
PADDING_MEDIUM = 4
PADDING_SMALL = 2
PADDING_NONE = 0

#
# FUNCTIONS
#


def select_dir(title, start_in=None):

    d = gtk.FileChooserDialog(title=title, 
        action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER, 
        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, 
        gtk.STOCK_APPLY, gtk.RESPONSE_APPLY))

    if start_in is not None:
        d.set_current_folder(start_in)

    res = d.run()
    file_list = d.get_filename()
    d.destroy()

    if res == gtk.RESPONSE_APPLY:

        return file_list

    else:

        return None


def select_file(title, multiple_files=False, file_filter=None,
        start_in=None):

    d = gtk.FileChooserDialog(title=title, 
        action=gtk.FILE_CHOOSER_ACTION_OPEN, 
        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, 
        gtk.STOCK_APPLY, gtk.RESPONSE_APPLY))

    d.set_select_multiple(multiple_files)

    if start_in is not None:
        d.set_current_folder(start_in)

    if file_filter is not None:

        f = gtk.FileFilter()
        f.set_name(file_filter['filter_name'])
        for m, p in file_filter['mime_and_patterns']:
            f.add_mime_type(m)
            f.add_pattern(p)
        d.add_filter(f)

    res = d.run()
    file_list = d.get_filenames()
    d.destroy()

    if res == gtk.RESPONSE_APPLY:

        return file_list

    else:

        return list()

def save_file(title, multiple_files=False, file_filter=None,
        start_in=None):

    d = gtk.FileChooserDialog(title=title, 
        action=gtk.FILE_CHOOSER_ACTION_SAVE, 
        buttons=(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, 
        gtk.STOCK_APPLY, gtk.RESPONSE_APPLY))

    d.set_select_multiple(multiple_files)

    if start_in is not None:
        d.set_current_folder(start_in)

    if file_filter is not None:

        f = gtk.FileFilter()
        f.set_name(file_filter['filter_name'])
        for m, p in file_filter['mime_and_patterns']:
            f.add_mime_type(m)
            f.add_pattern(p)
        d.add_filter(f)

    res = d.run()
    file_list = d.get_filenames()
    d.destroy()

    if res == gtk.RESPONSE_APPLY:

        return file_list

    else:

        return list()


def overwrite(text, file_name, window):

    dialog = gtk.MessageDialog(window,
                    gtk.DIALOG_DESTROY_WITH_PARENT,
                    gtk.MESSAGE_WARNING, gtk.BUTTONS_NONE,
                    text.format(file_name))

    dialog.add_button(gtk.STOCK_NO, False)
    dialog.add_button(gtk.STOCK_YES, True)

    dialog.show_all()

    resp = dialog.run()

    dialog.destroy()

    return resp


def dialog(window, text, d_type="info", yn_buttons=False):

    d_types = {'info': gtk.MESSAGE_INFO, 'error': gtk.MESSAGE_ERROR,
        'warning': gtk.MESSAGE_WARNING, 'question': gtk.MESSAGE_QUESTION,
        'other': gtk.MESSAGE_OTHER}

    if d_type in d_types.keys():

        d_type = d_types[d_type]

    else:

        d_type = gtk.MESSAGE_INFO

    d = gtk.MessageDialog(window, gtk.DIALOG_DESTROY_WITH_PARENT,
        gtk.MESSAGE_INFO, gtk.BUTTONS_NONE,
        text)

    if yn_buttons:

        d.add_button(gtk.STOCK_YES, True)
        d.add_button(gtk.STOCK_NO, False)

    else:

        d.add_button(gtk.STOCK_OK, -1)

    result = d.run()

    d.destroy()

    return result


def claim_a_scanner_dialog(window, text, image_path, scanners):

    scanners.update()
    scanner_names = scanners.get_names()

    dialog = gtk.MessageDialog(window, gtk.DIALOG_DESTROY_WITH_PARENT,
        gtk.MESSAGE_INFO, gtk.BUTTONS_NONE,
        text)

    for i, s in enumerate(scanner_names):
        dialog.add_button(s, i)

    dialog.add_button(gtk.STOCK_CANCEL, -1)

    img = gtk.Image()
    img.set_from_file(image_path)
    dialog.set_image(img)
    dialog.show_all()

    resp = dialog.run()

    dialog.destroy()

    if resp >= 0:
        return scanner_names[resp]
    else:
        return None

#
# CLASSES
#


class Fixture_Drawing(gtk.DrawingArea):

    HEIGHT = 0
    WIDTH = 1
    PADDING = 0.01

    def __init__(self, fixture, width=None, height=None):

        super(Fixture_Drawing, self).__init__()
        self.connect("expose_event", self.expose)

        self._fixture = fixture
        self._set_data()

        if width is not None and height is not None:
            self.set_size_request(width, height)

    def _set_data(self):

        self._plates = np.array(self._fixture.get_plates('fixture'))
        self._grayscale = np.array(self._fixture['fixture']['grayscale_area'])

        self._data_height = max(self._plates[:,:,self.HEIGHT].max(),
            self._grayscale[:,self.HEIGHT].max())
    
        self._data_width = max(self._plates[:,:,self.WIDTH].max(),
            self._grayscale[:,self.WIDTH].max())


    def _get_pos(self, d2, d1):

        new_pos = (d1 / self._data_width * self._cr_active_w + 
            self._cr_padding_w, d2 / self._data_height * self._cr_active_h +
            self._cr_padding_h)

        return new_pos

    def _draw_rect(self, cr, positions, stroke_rgba=None, stroke_width=0.5, fill_rgba=None):

        cr.move_to(*self._get_pos(*positions[0]))
 
        for pos in positions[1:]:

            cr.line_to(*self._get_pos(*pos))

        cr.close_path()

        if stroke_rgba is not None:
            cr.set_line_width(stroke_width)
            cr.set_source_rgba(*stroke_rgba)
            cr.stroke()

        if fill_arggs is not None:
            cr.set_source_rgba(*fill_rgba)
            cr.fill()

    def expose(self. widget, event):

        cr = widget.window.cairo_create()
        rect = self.get_allocation()

        w = rect.width
        h = rect.height

        #CALCULATE CURRENT PARAMETERS
        self._cr_padding_w = w * self.PADDING
        self._cr_padding_h = h * self.PADDING
        self._cr_active_w = w - 2 * self._cr_padding_w
        self._cr_active_h = h - 2 * self._cr_padding_h


class Start_Button(gtk.Button):

    def __init__(self, controller, model):

        self._controller = controller
        self._model = model

        super(Start_Button, self).__init__(
                                stock=gtk.STOCK_EXECUTE)

        al = self.get_children()[0]
        hbox = al.get_children()[0]
        im, l = hbox.get_children()

        l.set_text(model['start-text'])

        self.connect("clicked", controller.start)


class Pinning(gtk.VBox):

    def __init__(self, controller, model, project_veiw, 
            plate_number, pinning = None):

            self._model = model
            self._controller = controller
            self._project_view = project_veiw

            super(Pinning, self).__init__()

            label = gtk.Label(
                model['plate-label'].format(
                plate_number))


            self.pack_start(label, False, False, PADDING_SMALL)

            if pinning is None:

                pinning = model['pinning-default']

            self.dropbox = gtk.combo_box_new_text()                   

            def_key = 0
            ref_matrices = model['pinning-matrices-reversed']
            for i, m in enumerate(sorted(model['pinning-matrices'].keys())):

                self.dropbox.append_text(m)

                if pinning in ref_matrices and ref_matrices[pinning] == m:
                    def_key = i

            self.dropbox.set_active(def_key)
            
            self.dropbox_signal = self.dropbox.connect("changed",
                self._controller.set_pinning,
                plate_number)


            self.pack_start(self.dropbox, True, True, PADDING_SMALL)

    def set_sensitive(self, val):

        if val is None:
            val = False

        self.dropbox.set_sensitive(val)


    def set_pinning(self, pinning):

        orig_key = self.dropbox.get_active()
        new_key = -2
        pinning_text = self._model['pinning-matrices-reversed'][pinning]

        for i, m in enumerate(sorted(self._model['pinning-matrices'].keys())):

            if pinning_text == m:
                new_key = i

        if new_key != orig_key:

            self.dropbox.handler_block(self.dropbox_signal)
            self.dropbox.set_active(new_key)
            self.dropbox.handler_unblock(self.dropbox_signal)


class Page(gtk.VBox):

    def __init__(self, controller, model, top=None, stage=None):

        super(Page, self).__init__(False, 0)

        self._controller = controller
        self._model = model

        self.set_top(top)
        self.set_stage(stage)

    def _remove_child(self, pos=0):

        children = self.get_children()

        if len(children) - pos > 0:

            self.remove(children[pos])
            
    def get_controller(self):

        return self._controller

    def set_controller(self, c):

        self._controller = c

    def set_top(self, widget=None):

        if widget is None:

            widget = self._default_top()

        self._top = widget
        self._remove_child(pos=0)
        self.pack_start(widget, False, True, PADDING_LARGE)

    def _default_top(self):

        return gtk.VBox()

    def get_top(self):

        return self._top

    def set_stage(self, widget=None):

        if widget is None:

            widget = self._default_stage()

        self._stage = widget
        self._remove_child(pos=1)
        self.pack_end(widget, True, True, 10)
        widget.show_all()

    def _default_stage(self):

        return gtk.VBox()

    def get_stage(self):

        return self._stage


class Top(gtk.HBox):

    def __init__(self, controller, model):

        super(Top, self).__init__(False, 0)

        self._controller = controller
        self._model = model

    def pack_back_button(self, label, callback, message):

        button = gtk.Button(stock=gtk.STOCK_GO_BACK)
        al = button.get_children()[0]
        hbox = al.get_children()[0]
        im, l = hbox.get_children()
        l.set_text(label)
        button.connect("clicked", callback, message)
        self.pack_start(button, False, False, PADDING_SMALL)
        button.show()
        return button
    

class Top_Next_Button(gtk.Button):

    def __init__(self, controller, model, specific_model, label_text,
        callback, stage_signal_text):

        self._controller = controller
        self._model = model
        self._specific_model = specific_model

        super(Top_Next_Button, self).__init__(
                                stock=gtk.STOCK_GO_FORWARD)

        al = self.get_children()[0]
        hbox = al.get_children()[0]
        im, l = hbox.get_children()

        l.set_text(label_text)
        hbox.remove(im)
        hbox.remove(l)
        hbox.pack_start(l, False, False, PADDING_SMALL)
        hbox.pack_end(im, False, False, PADDING_SMALL)

        self.connect("clicked", callback,
                            stage_signal_text, specific_model)
