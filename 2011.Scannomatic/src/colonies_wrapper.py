#! /usr/bin/env python

# 
# colonies.py   v 0.1
#
# This is a convienience module for command line calling of all different types of colony
# analysis that are implemented.
#
# The module can also be imported directly into other scrips as a wrapper
#



#
# DEPENDENCIES
#

import numpy as np

#
# SCANNOMATIC LIBRARIES
#

import grid_array
import grid_cell
import project

#
# Functions
#

def get_grid_cell_from_array(arr, fallback_detection=False, center=None, radius=None):
    """
        get_grid_cell_from_array is a convinience function to pass a section
        of an image as argument and make the entire array be the grid_cell.

        Function takes argument:

        @arr    An numpy array containing image data of interest
                The entire array will be treated as being the grid cell


        @fallback_detection     If true (not default) will only use otsu.

        @center                 A manually set blob centrum (if set
                                radius must be set as well)
                                (if not supplied, blob will be detected
                                automatically)

       @radius                  A manually set blob radus (if set
                                center must be set as well)
                                (if not supplied, blob will be detected
                                automatically)

        Function returns a Grid_Cell instance that is ready to use.

    """

    cell = grid_cell.Grid_Cell(data_source=arr)
    cell.set_rect_size()
    #cell.set_center()
    cell.attach_analysis(use_fallback_detection=fallback_detection, 
        center=center, radius=radius)

    return cell


def get_grid_cell_analysis_from_array(arr):
    """
        get_grid_cell_analysis_from_array is a convenience function that
        allows passing a section of an image as argument and retrieving
        the analysed results.

        Function takes argument:

        @arr    An numpy array containing image data of interest
                The entire array will be treated as being the grid cell


        Function returns a features diectionary.

    """

    cell = get_grid_cell_from_array(arr)

    return cell.get_analysis()


def get_gray_scale_transformation_matrix(gs_values):
    """
        get_gray_scale_transformation_matrix takes a list of gs-values and
        returns a transformation matrix for a normal 8-bit gray scale image.

    """

    arr = grid_array.Grid_Array(None)

    return arr.get_transformation_matrix(gs_values=gs_values, 
        gs_indices = np.asarray([82,78,74,70,66,62,58,54,50,46,42,38,34,30,26,
            22,18,14,10,6,4,2,0]))


#
# WRAPPER CLASSES
#

class Grid_Array(grid_array.Grid_Array):
    def __init__(self):
        grid_array.Grid_Array.__init__(self)

class Grid_Cell(grid_cell.Grid_Cell):
    def __init__(self):
        grid_cell.Grid_Cell.__init__(self)

class Project_Image(project.Project_Image):
    def __init__(self, im_path):
        project.Project_Image.__init__(self, im_path)


#
# COMMAND LINE BEHAVIOUR
#

if __name__ == "__main__":
    pass
