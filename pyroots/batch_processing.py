"""
Batch processing functions:
- preprocessing_filter_loop
- preprocessing_actions_loop
- pyroots_batch_loop
- fishnet_loop
- tennant_batch

"""

import os
import numpy as np
from numpy import array, uint8
import pandas as pd
from pyroots import *
from skimage import io, color, filters, morphology, img_as_ubyte, img_as_float
from multiprocessing import Pool
from warnings import warn
import cv2
from time import strftime, sleep
from tqdm import tqdm


#################################################################################################
#################################################################################################
#########                                                                           #############
#########                      Preprocessing Image Filtering Loop                   #############
#########                                                                           #############
#################################################################################################
#################################################################################################

def preprocessing_filter_loop(dir_in,
                              extension_in,
                              dir_out,
                              extension_out=".png",
                              params=None,
                              threads=1):
    """
    Combines preprocessing filters (blur, color, contrast) into a loop. Convenient to run as a vehicle to transfer images
    from a portable drive to a permanent area.

    Parameters
    ----------
    base_directory : str
        Directory to the images or subdirectories containing the images.
    extension_in : str
        Extension of images to analyze
    out_dir : str
        Name of directory to write output images. `None` to skip.
    extension_out : str
        Extension to save images.
    params : str
        Path + filename for parameters file for `pyroots.preprocessing_filters`. If `None` (default), only
        loads and (possibly) resaves images. If not `None`, will only save images that pass test. See notes for format.
    threads : int
        For multiprocessing

    Returns
    -------
    Image files.

    Notes
    -----
    The `params` file should have the following objects: `blur_params`, `temperature_params`, and `low_contrast_params`.
    Except for `blur_band`, all are dictionaries with items named as arguments in respective functions. If not present,
    defaults to `None`. Will raise a `UserWarning` if the format and names are not correct (but not if `None`).

    """

    # Import parameters
    try:
        exec(open(params).read(), globals())
    except:
        if params is not None:
            raise ValueError("Couldn't load params file. Try checking it for words like 'array' or\n'uint8' that need to be loaded with numpy and load these\n functions using `extra_imports`.... Or edit source.")

    # Count files to analyze for status bar
    print("Counting images to screen...")
    total_files = 0
    for path, folder, filename in os.walk(dir_in):
        if dir_out not in path:
            for f in filename:
                if f.endswith(extension_in):
                    total_files += 1
    print("\nYou have {} images to analyze".format(total_files))

    for path, folder, filename in os.walk(dir_in):
        if dir_out not in path:   # Don't run in the output directory.

            # Make directory for saving objects
            subpath = path[len(dir_in)+1:]

            if not os.path.exists(os.path.join(dir_out, subpath)):
                os.mkdir(os.path.join(dir_out, subpath))
                os.mkdir(os.path.join(dir_out, "DID NOT PASS", subpath))

            global _core_fn
            def _core_fn(filename):
                if filename.endswith(extension_in):
                    path_in = os.path.join(path, filename)  # what's the image called and where is it?

                    # possible locations to write the output file
                    filename_out = os.path.splitext(filename)[0] + extension_out
                    path_out_PASS = os.path.join(dir_out, subpath, filename_out)
                    path_out_FAIL = os.path.join(dir_out, "DID NOT PASS", subpath, filename_out)

                    # skip if already analyzed
                    if os.path.exists(path_out_PASS) or os.path.exists(path_out_FAIL):
                        print("SKIPPING: {}".format(os.path.join(subpath, filename)))

                    else:  # analyze
                        try:
                            img = io.imread(path_in)  # load image
                        except:
                            print("Couldn't load: {}. Continuing...".format(path_in))
                            filename_out = "MISLOAD" + filename_out
                            path_out_FAIL = os.path.join(dir_out, "DID NOT PASS", subpath, filename_out)
                            img = np.ones((30, 30, 3))  # make an image that cannot pass
                            pass

                        test = preprocessing_filters(img,
                                                     blur_params,
                                                     temperature_params,
                                                     low_contrast_params,
                                                     center)

                        # where to write the output file?
                        if test == True:
                            if dir_out is not None:
                                io.imsave(path_out_PASS, img)
                            print("PASSED: {}".format(os.path.join(subpath, filename)))

                        else:
                            if dir_out is not None:
                                io.imsave(path_out_FAIL, img)
                            print("DID NOT PASS: {}".format(os.path.join(subpath, filename)))

                    return(True)  # for progress

            # Init threads within each path
            out = []  # for counting
            if threads is None:
                out += tqdm(map(_core_fn, filename),
                            total=total_files)
            else:
                sleep(2)  # to give everything time to  load
                chunks = min(5, int(total_files/2*threads) + 1)
                thread_pool = Pool(threads)
                # Work on _core_fn (and give progressbar)
                out += tqdm(thread_pool.imap_unordered(_core_fn,
                                                       filename,
                                                       chunksize=chunks),
                            total=total_files)
                # finish
                thread_pool.close()
                thread_pool.join()
#            thread_pool = Pool(threads)
#            # Work on _core_fn
#            thread_pool.map(_core_fn, filename)
#            # finish
#            thread_pool.close()
#            thread_pool.join()

    del globals()[_core_fn]  # to keep things safe
    return("Done")

#################################################################################################
#################################################################################################
#########                                                                           #############
#########                      Preprocessing Actions Loop                           #############
#########                                                                           #############
#################################################################################################
#################################################################################################

def preprocessing_actions_loop(dir_in,
                               extension_in,
                               dir_out,
                               extension_out=".png",
                               params=None,
                               threads=1):
    """
    Combines preprocessing filters (blur, color, contrast) into a loop. Convenient to run as a vehicle to transfer images
    from a portable drive to a permanent area.

    Parameters
    ----------
    base_directory : str
        Directory to the images or subdirectories containing the images.
    extension_in : str
        Extension of images to analyze
    out_dir : str
        Name of directory to write output images. `None` to skip.
    extension_out : str
        Extension to save images.
    params : str
        Path + filename for parameters file for `pyroots.preprocessing_filters`. If `None` (default), only
        loads and (possibly) resaves images. If not `None`, will only save images that pass test. See notes for format.
    threads : int
        For multiprocessing

    Returns
    -------
    Image files.

    Notes
    -----
    The `params` file should have the following objects: `make_correction_params`,
    `brightfield_correction_params`, 'registration_params', and `low_contrast_params`.
    All are dictionaries with items named as arguments in respective functions. If not present,
    will default to `None`. Will raise a `UserWarning` if the format and names are not correct (but not if `None`).

    """


    try:
        exec(open(params).read(), globals())
    except:
        if params is not None:
            raise ValueError("Couldn't load params file")
            return  # can't do anything without the parameters!

    # make sure all dictionaries have something assigned to them, including None
    dicts = ['make_brightfield_params',
             'brightfield_correction_params',
             'smoothing_params',
             'registration_params']
    print("The parameters you've loaded are:\n")

    for i in dicts:
        try:
            print(i + " = " + str(globals()[i]))
        except:
            print(i + " = " + str('skip'))
            globals()[i] = 'skip'

    # Count files to analyze for status bar
    print("Counting {} images to screen in {}".format(extension_in, dir_in))
    total_files = 0
    for path, folder, filename in os.walk(dir_in):
        if dir_out not in path:
            for f in filename:
                if f.endswith(extension_in):
                    total_files += 1
    print("\nYou have {} images to analyze".format(total_files))

    # initiate loop
    for path, folder, filename in os.walk(dir_in):
        if dir_out not in path and "FAILED PROCESSES" not in path:   # Don't run in the output directory.
            # ID the current folder
            subpath = path[len(dir_in)+1:]

            # Make directories for saving images
            if dir_out is not None:
                if not os.path.exists(os.path.join(dir_out, subpath)):
                    os.mkdir(os.path.join(dir_out, subpath))
                if not os.path.exists(os.path.join(dir_out, "FAILED PROCESSES", subpath)):
                    os.mkdir(os.path.join(dir_out, "FAILED PROCESSES", subpath))

            # make a brightfield correction image for the directory
            def _make_brightfield_image(directory, brightfield_name, brightfield_sigma):
                correction = io.imread(os.path.join(directory, brightfield_name))
                correction = cv2.GaussianBlur(correction, (0, 0), brightfield_sigma)
                return(correction)

            try:
                correction = _make_brightfield_image(path, **make_brightfield_params)
            except:
                if make_brightfield_params is not None:
                    print("\nCould not make correction image. Does\n{}\nexist?\nContinuing to next folder...\n".format(\
                        os.path.join(subpath, make_brightfield_params['brightfield_name'])))
                    continue  # can't do this folder, so move on to the next
                else:
                    correction = None
                    pass

            global _core_fn  # bad form for compatibility with Pool.map()
            def _core_fn(filename):
                if filename.endswith(extension_in):
                    path_in = os.path.join(path, filename)  # what's the image called and where is it?

                    # possible locations to write the output file
                    filename_out = os.path.splitext(filename)[0] + extension_out
                    path_out_PASS = os.path.join(dir_out, subpath, filename_out)
                    path_out_FAIL = os.path.join(dir_out, "FAILED PROCESSES", subpath, filename_out)

                    # skip if already analyzed
                    if os.path.exists(path_out_PASS) or os.path.exists(path_out_FAIL):
                        print("Already Analyzed: {}".format(os.path.join(subpath, filename)))

                    else:  # analyze
                        try:
                            img = io.imread(path_in)  # load image
                        except:
                            print("Couldn't load: {}. Continuing...".format(path_in))
                            return

                        img_out, warnings = preprocessing_actions(img,
                                                                  correction,
                                                                  brightfield_correction_params,
                                                                  registration_params,
                                                                  smoothing_params,
                                                                  count_warnings=True)

                        # where to write the output file?
                        if warnings == 0:  # save the manipulated image
                            if dir_out is not None:
                                io.imsave(path_out_PASS, img_out)
                            #print("PASSED: {}".format(os.path.join(subpath, filename)))

                        else:
                            if dir_out is not None:  # save a copy of the preprocessed image
                                io.imsave(path_out_FAIL, img_out)
                            print("Something Failed: {}".format(os.path.join(subpath, filename)))

                    return(True)  # for tqdm compatibility

            # Init threads within each path
            out = []  # for counting with tqdm
            if threads is None:
                sleep(2)  # let everything print out nicely
                out += tqdm(map(_core_fn, filename),
                            total=total_files)
            else:
                sleep(2)  # to give everything time to  load
                #chunks = min(5, int(total_files/2*threads) + 1)
                chunks=1
                thread_pool = Pool(threads)
                # Work on _core_fn (and give progressbar)
                out += tqdm(thread_pool.imap_unordered(_core_fn,
                                                       filename,
                                                       chunksize=chunks),
                            total=total_files)
                # finish
                thread_pool.close()
                thread_pool.join()

#    del globals()[_core_fn]  # to keep things safe

    return("Done with preprocessing. You can view the results in {}".format(dir_out))


##################################################################################################################################################################################
####################                                                                                                                               ###############################
####################                                               FRANGI-BASED SEGMENTATION                                                       ###############################
####################                                                                                                                               ###############################
##################################################################################################################################################################################


def frangi_image_loop(dir_in,
                      extension_in,
                      dir_out=None,
                      table_out=None,
                      table_overwrite=False,
                      params=None,
                      mask=None,
                      save_images=False,
                      threads=1):
    """
    Reference function to loop through images in a directory. As it is written, it returns
    a dataframe from `pyroots.frangi_segmentation` and also writes images showing the objects analyzed.
    Note that all parameters in `pyroots.frangi_segmentation` must be defined in the params
    file, even as `None` for this to work.

    Parameters
    ----------
    dir_in : str
        Directory to the images or subdirectories containing the images.
    extension_in : str
        Extension of images to analyze
    dir_out : str or `None`
        Full path to write images to. If `None` and `save_images=True`, defaults to "Pyroots Analyzed" in `dir_in`.
    table_out : str or `None`
        Full path to which to write the results, including the filename. If `None`, defaults to "Pyroots Results.txt" in `dir_in`.
    table_overwrite : bool
        If `table_out` exists, do you want to overwrite it?
    params : str
        Path + filename for parameters file for `pyroots.frangi_segmentation`. If None (default), will
        print a list of subpaths + images that would be processed, with a warning.
    mask : ndarray
        Binary array of the same dimensions as each image, with 1 being the part of the image to analyze.
    save_images : bool
        Do you want to save images of the objects?
    threads : int
        For multiprocessing
    extra_imports : list
        If raises error importing params, then write a list of lists as
            [[lib1, fun1, fun2, ...],
             [lib2, fun1, fun2, ...],
             [...]].
    """
    ### make sure all dictionaries have something assigned to them, including None
    dicts = ['colors', 'frangi_args', 'threshold_args', 'color_args_1', 'color_args_2',
             'color_args_3', 'morphology_args_1', 'morphology_args_2', 'hollow_args',
             'fill_gaps_args', 'diameter_args', 'diameter_bins']

    if params is None:
        print("No parameters defined. Printing paths to images.\n")

    else:
        try:  # loading the params.
            exec(open(params).read(), globals())

            print("The parameters you've loaded are:\n")

            for i in dicts:  # report the parameters
                try:         # if present in `params` file
                    print("{} = {}".format(i, str(globals()[i])))
                    print("\n")

                except:      # if not present in `params` file, must define as None to work
                    globals()[i] = None  # assign as none
                    print("{} = {}".format(i, str(globals()[i])))
                    print("\n")

        except:
            if os.path.exists(params):
                raise ValueError("Couldn't load params file. Try checking it for words like 'array' or\
                \n'uint8' that need to be loaded with numpy and load these functions\
                \n at the top of your script.... Or edit source.")
            else:
                raise ValueError("Couldn't find params file at {}".format(params))

    ### Make and initiate table_out
    # define where to save the table
    if table_out is None:
        table_out = os.path.join(dir_in, "Pyroots Results.txt")

    # make the directory, if it doesn't exist
    try:
        os.mkdir(os.path.split(table_out)[0])
    except:
        pass

    # should the table be overwritten? If not, append.
    if os.path.exists(table_out):
        if table_overwrite is False:
            print("Appending to old data table: {}".format(table_out))
            new_table = False
        else:
            print("Overwriting old data table: {}".format(table_out))
            new_table = True
    else:
        print("Saving data table to: {}".format(table_out))
        new_table = True


    # initiate the new table
    if diameter_bins is None:
        df_out = pd.DataFrame(columns=("Time", "ImageName", "Length", "NObjects", "MeanDiam"))  # for concatenating purposes
        ncol = 5
    else:
        df_out = pd.DataFrame(columns=("Time", "ImageName", "DiameterClass", "Length"))  # for concatenating purposes
        ncol = 4

    if new_table is True:
        df_out.to_csv(table_out, sep='\t', index=False, mode='w')

    else:  # make sure it's compatible
        temp = pd.read_table(table_out, sep='\t', nrows=1).columns.values
        if len(temp) != ncol:  # same number of columns
            raise ValueError("Cannot Append to Existing Data Table. Different number of columns. Try a new name!")
        elif sum(temp != df_out.columns.values) > 0:  # same column names
            raise ValueError("Cannot Append to Existing Data Table. Different number of columns. Try a new name!")


    ### Make an output directory for the analyzed images and data.
    if dir_out is None:
        dir_out = os.path.join(dir_in, "Pyroots Analyzed")

    if save_images is True:
        if params is not None:
            print("\nSaving images to {}".format(dir_out))
        if not os.path.exists(dir_out):
            os.mkdir(dir_out)

    #Count files to analyze
    total_files = 0
    for path, folder, filename in os.walk(dir_in):
        if dir_out not in path:
            for f in filename:
                if f.endswith(extension_in):
                    total_files += 1
    print("\nYou have {} images to analyze".format(total_files))

    #Begin looping
    out = []  # secondary saving method
    for path, folder, filename in os.walk(dir_in):
        if dir_out not in path:   # Don't run in the output directory.

            # Make directory for saving objects
            subpath = path[len(dir_in)+1:]
            if not os.path.exists(os.path.join(dir_out, subpath)):
                os.mkdir(os.path.join(dir_out, subpath))

            # What we'll do:
            global _core_fn  # bad form for Pool.map() compatibility
            def _core_fn(filename):
                if filename.endswith(extension_in):
                    # count progress.

                    path_in = os.path.join(path, filename)
                    subpath_in = os.path.join(subpath, filename) # for printing purposes
                    # Where to write the output image?
                    filename_out = os.path.splitext(filename)[0] + ".png"
                    path_out = os.path.join(dir_out, subpath, filename_out)

                    if os.path.exists(path_out): #skip
                        print("\nALREADY ANALYZED: {}. Skipping...\n".format(subpath_in))

                    else: #(try to) do it
                        try:
                            img = io.imread(path_in)  # load image
                            if mask is not None:
                                img = img * mask

                            if len(img.shape) != 3:
                                print("\n{} is not a color image! Skipping...\n".format(subpath_in))

                            objects_dict = frangi_segmentation(img, colors,              #### Insert your custom function here ####
                                                               frangi_args,
                                                               threshold_args,
                                                               color_args_1,
                                                               color_args_2,
                                                               color_args_3,
                                                               morphology_args_1,
                                                               morphology_args_2,
                                                               hollow_args,
                                                               fill_gaps_args,
                                                               diameter_args,
                                                               diameter_bins,
                                                               image_name=os.path.join(subpath,
                                                                                       filename))

                            #save images?
                            if save_images is True:
                                io.imsave(path_out, 255*objects_dict['objects'].astype('uint8'))

                            #Update on progress
                            print("Done: {}".format(subpath_in))

                            df_out = objects_dict['geometry']
                            df_out.insert(0, "Time", strftime("%Y-%M-%d %H:%M:%S"))

                            df_out.to_csv(table_out, sep='\t', index=False, header=False, mode='a')

                        except:
                            df_out = None
                            if params is None:  # just list the images that *would* be analyzed
                                print(subpath_in)
                            else:
                                print("\nCouldn't Process: {}.\n     ...Continuing...".format(subpath_in))


                        return(df_out)

            # Init threads within each path
            if threads is None:
                out += tqdm(map(_core_fn, filename),
                            total=total_files)
            else:
                sleep(1)  # to give everything time to  load
                chunks = min(5, int(total_files/2*threads) + 1)
                thread_pool = Pool(threads)
                # Work on _core_fn (and give progressbar)
                out += tqdm(thread_pool.imap_unordered(_core_fn,
                                                       filename,
                                                       chunksize=chunks),
                            total=total_files)
                # finish
                thread_pool.close()
                thread_pool.join()


    out = pd.concat([i for i in out])
    del globals()[_core_fn]  # to keep things safe
    return(out)

############################################################################################################################################################################
####################                                                                                                                         ###############################
####################                                               Generic Segmentation Loop                                                 ###############################
####################                                                                                                                         ###############################
############################################################################################################################################################################

def pyroots_batch_loop(dir_in,
                       extension_in,
                       method,
                       dir_out=None,
                       extension_out='.png',
                       table_out=None,
                       table_overwrite=False,
                       params=None,
                       save_images=False,
                       threads=1):
    """
    Function to loop through images in a directory. As it is written, it returns
    a dataframe from the segmentation method of your choice and also will write images
    showing the objects analyzed. Generate a parameters file with one of the jupyter notebooks.

    Parameters
    ----------
    dir_in : str
        Directory to the images or subdirectories containing the images.
    extension_in : str
        Extension of images to analyze
    method : str
        options are 'thresholding', 'frangi', or 'custom'. Which processing method do you want to use? Note custom requires
        editing the source code.
    dir_out : str or `None`
        Full path to write images to. If `None` and `save_images=True`, defaults to "Pyroots Analyzed" in `dir_in`.
    extension_out : str
        Image type for output images. .png is default, as it is both space efficient and lossless. 
    table_out : str or `None`
        Full path to which to write the results, including the filename. If `None`, defaults to "Pyroots Results.txt" in `dir_in`.
    table_overwrite : bool
        If `table_out` exists, do you want to overwrite it?
    params : str
        Path + filename for parameters file for `pyroots.frangi_segmentation`. If None (default), will
        print a list of subpaths + images that would be processed, with a warning.
    save_images : bool
        Do you want to save images of the objects?
    threads : int
        For multiprocessing
    extra_imports : list
        If raises error importing params, then write a list of lists as
            [[lib1, fun1, fun2, ...],
             [lib2, fun1, fun2, ...],
             [...]].
    """
    ### make sure all dictionaries have something assigned to them, including None
    method = method.lower()

    if method == 'thresholding':
        dicts = [
            'colors',#
            'contrast_kernel_size',#
            'threshold_args',#
            'mask_args',
            'noise_removal_args',
            'morphology_filter_args',
            'fill_gaps_args',
            'lw_filter_args',
            'diam_filter_args',
            'diameter_bins'
        ]

    elif method == 'frangi':
        dicts = [
            'colors', 
            'frangi_args', 
            'threshold_args',
            'separate_objects', 
            'contrast_kernel_size', 
            'color_args_1', 
            'color_args_2', 
            'color_args_3', 
            'neighborhood_args', 
            'morphology_args_1', 
            'morphology_args_2', 
            'hollow_args', 
            'fill_gaps_args', 
            'diameter_args', 
            'diameter_bins'
        ]

    elif method == 'custom':
        warn('make a list of parameter/dictionary names in the source!')
    else:
        raise ValueError("Invalid method. 'thresholding', 'frangi', and 'custom' are the options")


    if params is None:
        print("No parameters defined. Printing paths to images.\n")

    else:
        try:  # loading the params.
            exec(open(params).read(), globals())

            print("The parameters you've loaded are:\n")

            for i in dicts:  # report the parameters
                try:         # if present in `params` file
                    print("{} = {}".format(i, str(globals()[i])))

                except:      # if not present in `params` file, must define as 'skip' to work
                    globals()[i] = 'skip'  # assign as 'skip'
                    print("{} = {}".format(i, str(globals()[i])))

        except:
            if os.path.exists(params):
                raise ValueError(
                """Couldn't load params file. Try checking it for words like 'array' or 
                'uint8' that need to be loaded with numpy and add a line to load these 
                functions/modules at the top of your script.... Or edit source.""")
            else:
                raise ValueError("Couldn't find params file at {}".format(params))

    ### Make and initiate table_out
    # define where to save the table
    if table_out is None:
        table_out = os.path.join(dir_in, "Pyroots Results.txt")

    # make the directory, if it doesn't exist
    try:
        os.mkdir(os.path.split(table_out)[0])
    except:
        pass

    # should the table be overwritten? If not, append.
    if os.path.exists(table_out):
        if table_overwrite is False:
            print("Appending to old data table: {}".format(table_out))
            new_table = False
        else:
            print("Overwriting old data table: {}".format(table_out))
            new_table = True
    else:
        print("Saving data table to: {}".format(table_out))
        new_table = True


    # initiate the new table
    if diameter_bins is None or diameter_bins is 'skip':
        df_out = pd.DataFrame(columns=("Time", "ImageName", "Length", "NObjects", "MeanDiam"))  # for concatenating purposes
        ncol = 5
    else:
        df_out = pd.DataFrame(columns=("Time", "ImageName", "DiameterClass", "Length"))  # for concatenating purposes
        ncol = 4

    if new_table is True:
        df_out.to_csv(table_out, sep='\t', index=False, mode='w')

    else:  # make sure it's compatible
        temp = pd.read_table(table_out, sep='\t', nrows=1).columns.values
        if len(temp) != ncol:  # same number of columns
            raise ValueError("Cannot Append to Existing Data Table. Different number of columns. Try a new name for the file!")
        elif sum(temp != df_out.columns.values) > 0:  # same column names
            raise ValueError("Cannot Append to Existing Data Table. Different number of columns. Try a new name for the file!")


    ### Make an output directory for the analyzed images and data.
    if dir_out is None:
        dir_out = os.path.join(dir_in, "Pyroots Analyzed")

    if save_images is True:
        if params is not None:
            print("\nSaving images to {}".format(dir_out))
        if not os.path.exists(dir_out):
            os.mkdir(dir_out)

    #Count files to analyze
    total_files = 0
    for path, folder, filename in os.walk(dir_in):
        if dir_out not in path:
            for f in filename:
                if f.endswith(extension_in):
                    total_files += 1
    print("\nYou have {} images to analyze".format(total_files))

    #Begin looping
    out = []  # secondary saving method
    for path, folder, filename in os.walk(dir_in):
        if dir_out not in path:   # Don't run in the output directory.

            # Make directory for saving objects
            subpath = path[len(dir_in)+1:]
            if not os.path.exists(os.path.join(dir_out, subpath)):
                os.mkdir(os.path.join(dir_out, subpath))

            # What we'll do:
            global _core_fn  # bad form for Pool.map() compatibility
            def _core_fn(filename):
                if filename.endswith(extension_in):
                    # count progress.

                    path_in = os.path.join(path, filename)
                    subpath_in = os.path.join(subpath, filename) # for printing purposes
                    # Where to write the output image?
                    filename_out = os.path.splitext(filename)[0] + extension_out
                    path_out = os.path.join(dir_out, subpath, filename_out)

                    if os.path.exists(path_out): #skip
                        print("\nALREADY ANALYZED: {}. Skipping...\n".format(subpath_in))

                    else: #(try to) do it
                        try:
                            img = io.imread(path_in)  # load image
                            image_name=os.path.join(subpath, filename)

                            if len(img.shape) != 3:
                                if len(colors) == 3:
                                    print("\n{} is not a color image! Skipping...\n".format(subpath_in))

                            if method == 'frangi':
                                objects_dict = frangi_segmentation(
                                    img, 
                                    colors,
                                    frangi_args,
                                    threshold_args,
                                    separate_objects,
                                    contrast_kernel_size,
                                    color_args_1,
                                    color_args_2,
                                    color_args_3,
                                    neighborhood_args,
                                    morphology_args_1,
                                    morphology_args_2,
                                    hollow_args,
                                    fill_gaps_args,
                                    diameter_args,
                                    diameter_bins,
                                    image_name=image_name,
                                    verbose=False
                                )

                            elif method == 'thresholding':
                                objects_dict = thresholding_segmentation(
                                    img,
                                    threshold_args,
                                    image_name,
                                    colors,
                                    contrast_kernel_size,
                                    mask_args,
                                    noise_removal_args,
                                    morphology_filter_args,
                                    fill_gaps_args,
                                    lw_filter_args,
                                    diam_filter_args,
                                    diameter_bins,
                                    verbose=False
                                )

                            elif method == 'custom':
                                raise ValueError(
                                """No custom function defined. Define it in pyroots/batch_processing.py and 
                                restart your python session (and comment out this error message)""")

                            else:
                                raise ValueError(
                                """Didn't understand what method you wanted. Options are 'frangi', 
                                'thresholding', and 'custom'""")


                            #save images?
                            if save_images is True:
                                io.imsave(path_out, img_as_ubyte(255*objects_dict['objects']))  # for black/white printing

                            #Update on progress
                            #print("Done: {}".format(subpath_in))

                            df_out = objects_dict['geometry']
                            df_out.insert(0, "Time", strftime("%Y-%m-%d_%H:%M:%S"))

                            df_out.to_csv(table_out, sep=',', index=False, header=False, mode='a')

                        except:
                            df_out = None
                            if params is None:  # just list the images that *would* be analyzed
                                print(subpath_in)
                            else:
                                print("\nCouldn't Process: {}.\n     ...Continuing...".format(subpath_in))


                        return(df_out)

            # Init threads within each path
            if threads is None:
                out += tqdm(map(_core_fn, filename),
                            total=total_files)
            else:
                sleep(1)  # to give everything time to  load
#                 chunks = min(5, int(total_files/2*threads) + 1)
#                 if total_files < 5:
#                     chunks = 1
                thread_pool = Pool(threads)
                # Work on _core_fn (and give progressbar)
                out += tqdm(thread_pool.imap_unordered(_core_fn,
                                                       filename,
                                                       chunksize=1),
                            total=total_files)
                # finish
                thread_pool.close()
                thread_pool.join()


    out = pd.concat([i for i in out])
    return(out)
    
    
#################################################################################################
#################################################################################################
#########                                                                           #############
#########                           Batch Add Grid to Images                        #############
#########                                                                           #############
#################################################################################################
#################################################################################################


def fishnet_loop(dir_in,
                 extension_in,
                 dir_out='fishnet',
                 extension_out=None,
                 size=50,
                 color=(200, 0, 0),
                 weight=1,
                 overwrite=False,
                 in_place=False,
                 cores=1):
    """
    Adds a fishnet of `size` * `size` pixels to each image of type `extension_in` in `dir_in`. 
    Saves them to a folder `dir_out` in `dir_in` as type `extension_out` (defaults to same as
    `extension_in`).

    Parameters
    ----------
    dir_in : str
        Directory to the images or subdirectories containing the images.
    extension_in : str
        Extension of images to analyze
    dir_out : str
        Name of directory to write output images. `None` or `""` to skip.
    extension_out : str
        Extension to save images.
    size : int
        Pixel length of one edge of the square mesh.
    color : int
        3 values specifying the color of the grid in 8-bit RGB space. Default is red.
    weight : int
        pixels wide of the lines. If is float, rounds down to int.
    overwrite : bool
        overwrite images if they exist? per the path specified by `dir_out` and `extension_out`
    in_place : bool
        do you want to update images in-place? If TRUE, then confirms and sets `dir_out` to 
        `None` and `overwrite` to `True`.
    cores : int
        For multiprocessing

    Returns
    -------
    Saves image files

    """
       
    if in_place:
        dir_out = None
        overwrite=True
        cont = input("Overwriting images in-place. Continue? [y, n]")
        if cont.lower() != 'y':
            print('canceling')
            return
    
    if extension_out is None:
        extension_out = extension_in
    if dir_out is None:
        dir_out = dir_in
    
    # Count files to analyze for status bar, and make lists of directories
    print("Counting images to screen...")
    total_files = 0
    subpaths = []
    files_in = []
    files_out = []
    file_names = []
    for path, folder, filename in os.walk(dir_in):
        if dir_out not in path or dir_out is dir_in:
            for f in filename:
                if f.endswith(extension_in):
                    total_files += 1  # index

                    files_in.append(os.path.join(path, f))  # input files
                    
                    subpath = path[len(dir_in)+1 :]  # subpaths
                    test_sub = sum([i == subpath for i in subpaths])
                    if test_sub==0:
                        subpaths.append(subpath)  # for making paths later on
                    
                    file_names.append(os.path.join(subpath, f)) # image names for a table later
                    
                    f_out = os.path.join(dir_out, subpath, f)  # files out = dir_in/dir_out/subpath/image.ext
                    files_out.append(f_out)
                    
    print("\nYou have {} images to analyze".format(total_files))
    
    if not os.path.exists(os.path.join(dir_in, dir_out)):
        os.mkdir(os.path.join(dir_in, dir_out))
        
    for i in subpaths:
        if not os.path.exists(os.path.join(dir_in, dir_out, i)):
            os.mkdir(os.path.join(dir_in, dir_out, i))
            
    fout = os.path.join(dir_in, dir_out, 'fishnet_images.csv')
    with open(fout, 'w') as file:
        print("Image,GridSize_px,Crosses", file=file)
        for i in file_names:
            print("{},{},".format(i, size), file=file)
    
    global _core_fn
    def _core_fn(ix):
        image = io.imread(files_in[ix])

        image = draw_fishnet(image, size=size, grid_color=color, weight=weight)

        if not os.path.exists(files_out[ix]):
            io.imsave(files_out[ix],
                      image)
        elif overwrite:
            io.imsave(files_out[ix], 
                      image)

        return
    
    sleep(2)  # to give everything time to  load
    out = []  # for tqdm counting

    with Pool(cores) as thread_pool:
        out += tqdm(thread_pool.imap_unordered(_core_fn,
                                               range(total_files),
                                               chunksize=1),
                    total=total_files)
    
    del globals()['_core_fn']

    return('Done')
    

#################################################################################################
#################################################################################################
#########                                                                           #############
#########                           Tennant Batch Measurement                       #############
#########                                                                           #############
#################################################################################################
#################################################################################################


def tennant_batch(dir_in,
                  extension_in, 
                  table_out,
                  grid_size,
                  overwrite=False,
                  cores=1):
    """
    Estimates the length of objects in binary images based on the Tennant/line-intersect method. The directory
    and extension should point to binary images that are the outputs of frangi or thresholding 
    segmentation, as these methods return only objects that pass post-skeletonization filters
    like length:width filters. 
    
    Parameters
    ----------
    dir_in : str
        Directory to the images or subdirectories containing the images.
    extension_in : str
        Extension of images to analyze
    table_out : str
        Directory and name of table to write output as. Returns comma-separated (.csv)
    size : int
        Size (in pixels) of the tenant grid.
    
    Returns
    -------
    Saves a spreadsheet with columns of file name, grid size (in px), crosses, and estimated length (in px) 
    to `table_out`. Also returns this as a pandas `DataFrame`.
    
    Notes
    -----
    The calculation for estimated pixel length is described in Tennant (1975):
    
    pixel length = 11/14 * grid_size * Ncrosses. 
    
    `pyroots.tennant_measurement.tennant_on_segmented()` calculates Ncrosses using square connectivity
    (Manhattan distance = 1) on segmented, but not medial axis, images.
    
    See Also
    --------
    `pyroots.tennant_measurement.tennant_on_segmented()` for details of how crosses are counted.
    
    Tennant, D., 1975. A test of a modified line intersect method of estimating root length. The Journal 
    of Ecology 63, 995. https://doi.org/10.2307/2258617
    
    """
    
    colnames = ['Image', 'GridSize_px', 'Crosses', 'Length_px']
    ncol = 4
    
    if os.path.exists(table_out) and not overwrite:
            df_out = pd.read_table(table_out, sep=",", nrows=1)
            temp = df_out.columns.values
            temp = sum(temp == colnames)
            if temp != ncol:
                raise ValueError("Table already exists, and is not compatible with\
                                 the output of this function. Will not overwrite")
    else:
        df_out = pd.DataFrame(columns=colnames)
        df_out.to_csv(table_out, sep=',', index=False, mode='w')

    print("Counting images to screen...")
    total_files = 0
    subpaths = []
    files_in = []
    file_names = []
    for path, folder, filename in os.walk(dir_in):
        for f in filename:
            if f.endswith(extension_in):
                total_files += 1  # index

                files_in.append(os.path.join(path, f))  # input files

                subpath = path[len(dir_in)+1 :]  # subpaths
                test_sub = sum([i == subpath for i in subpaths])
                if test_sub==0:
                    subpaths.append(subpath)  # for making paths later on

                file_names.append(os.path.join(subpath, f)) # image names for a table later
                    
    print("\nYou have {} images to analyze".format(total_files))
    
#     for ix in tqdm(range(total_files)):
    global _core_fn
    def _core_fn(ix):
        image = io.imread(files_in[ix])
        
        crosses = tennant_on_segmented(image, grid_size=grid_size)
        tennant_length = (11/14)*grid_size*crosses
        
        temp_out = pd.DataFrame(data={'Image': [file_names[ix]],
                                      'GridSize_px': [grid_size],
                                      'Crosses': [crosses],
                                      'Length_px': [tennant_length]
                                     })
        temp_out = temp_out[colnames]
        temp_out.to_csv(table_out, sep=",", index=False, header=False, mode='a')
        
        return(temp_out)
        
    
    sleep(0.5)  # to give everything time to  load
    out = []  # for tqdm counting
    with Pool(cores) as thread_pool:
        out += tqdm(thread_pool.imap_unordered(_core_fn,
                                               range(total_files),
                                               chunksize=1),
                    total=total_files)
    
    del globals()['_core_fn']
    
    df_out = pd.concat([i for i in out])

    return(df_out)
