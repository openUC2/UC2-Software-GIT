'''
    Toolbox used for data-processing of the Macrophage and MDCK video in the publication: 
    https://www.biorxiv.org/content/10.1101/2020.03.02.973073v1
    "UC2 – A Versatile and Customizable low-cost 3D-printed Optical Open-Standard for microscopic imaging"
    
    Author: René Lachmann
    Date: 24.09.2020
'''

# import external modules
import cv2
from datetime import datetime
import io
import logging
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib import rcParams as mplParams
from matplotlib_scalebar.scalebar import ScaleBar
import NanoImagingPack as nip
import numpy as np
import os
import PIL
from socket import gethostname
from time import time, sleep
import yaml

# %%
# -------------------------------- INOUT TOOLS -------------------------------
def rename_files(file_dir, extension='jpg',version=1):
    '''
    Renames numbered stack and inserts 0s so that readin it in works better.
    Leaves out image #9. Why?

    Note: 
        09.07.2020 -> version_parameter not needen anymore due to updated regex for file_search. 
    '''
    tstart = time()
    brename = False

    # load file_list without path and exclude files of wrong extension
    file_list = os.listdir(file_dir)
    file_list = [m for m in file_list if m[-len(extension):] == extension]

    # sorts the string-list ascending by length
    if len(file_list):
        file_list.sort(key=len)  
        index_max_nbr = len(file_list)
        file_max_length = len(file_list[-1])  

        # do renaming
        if not len(file_list[0]) == file_max_length:
            for myc in range(0, index_max_nbr-1):
                file_len = len(file_list[myc])
                if(file_len < file_max_length):
                    try:
                        pos_help = re.search('(_|--|-)[0-9]+(.|_)', file_list[myc])
                        string_help = str(0)*(file_max_length-file_len)
                        offset = pos_help.start()+pos_help.lastindex-1
                        os.rename(file_dir + file_list[myc], file_dir + file_list[myc][0:offset] + string_help + file_list[myc][offset:])
                    except Exception as e: 
                        print("Input file myc={}, hence: {} has wrong formatting. Exception: -->{}<-- raised. ".format(myc,file_list[myc],e))
                        
            brename = True
        tdelta = time()-tstart
        print('Renaming took: {0}s.'.format(tdelta))

    else: 
        print('No file with extension >{}< found in directory {}.'.format(extension,file_dir))
        tdelta = 0
        brename = False

    # done?
    return tdelta, brename

def get_filelist(load_path='.', fn_proto='jpg'):
    '''
    Gets a list of file according to a prototype.

    :param:
    =======
    load_path: absolute path to load directory
    :fn_proto: prototype-filename to select basic structure on and use e.g. regex on -> not implemented yet

    :out:
    =====
    fl: file_list

    '''
    # better, but traversing and checking not necessary for now
    # fl = os.listdir(load_path).sort(reverse=False) # automatically excludes '.' and '..'
    # if os.path.isdir(fname)

    # for now -> short solution
    try:
        from NanoImagingPack import get_sorted_file_list as gsfl
        fl = gsfl(load_path, fn_proto, sort='integer_key', key='0')
    except Exception as e:
        print('Exception in Get_Filelist: {}'.format(e))
        from os import listdir
        from os.path import isfile, join, getmtime
        fl = [(f, getmtime(join(load_path, f)))
              for f in listdir(load_path) if isfile(join(load_path, f))]
        fl = list(filter(lambda x: x[0].find(fn_proto) >= 0, fl))
    if type(fl[0]) == tuple:
        fl = [m[0] for m in fl]  # make sure that only filenames are left over
    fl.sort()
    return fl

def get_batch_numbers(filelist=['', ], batch_size=100):
    '''
    Calculates the number of batches

    :param:DEFAULT:
    =======
    :filelist:['',]: (LIST) list of files
    :batch_size:100: (INT) number of images per batch

    :out:
    =====
    :fl_len: length of filelist
    :fl_iter: number of batches for full stack
    :fl_lastiter: size of last batch
    '''
    #
    from math import floor
    #
    fl_len = len(filelist)
    fl_iter = floor(fl_len/batch_size) + (1 if fl_len % batch_size > 0 else 0)
    fl_lastiter = batch_size if (
        fl_len % batch_size == 0 and fl_iter > 0) else fl_len % batch_size
    print("{} files will be split into {} iterations with {} objects in the last iteration using a batch_size of {}.".format(
        fl_len, fl_iter, fl_lastiter, batch_size))
    return fl_len, fl_iter, fl_lastiter


def loadStackfast(file_list, logger=False, colorful=1):
    '''
    Easy alternative to load stack fast and make useable afterwards.
    '''
    from cv2 import imread
    from tifffile import imread as timread
    im = []
    rl = []
    for m in range(len(file_list)):

        # try to read in
        try:
            if colorful:
                imh = imread(file_list[m])
            else:
                imh = imread(file_list[m], 0)
                if not type(imh) == np.ndarray:
                    # if imh == None:
                    imh = timread(file_list[m])
        except Exception as ex:
            logger_switch_output(
                "Exception ---->{}<---- occured. Trying again with tiffile.".format(ex), logger=logger)
            try:
                imh = timread(file_list[m])
            except Exception as ex2:
                logger_switch_output(
                    "2nd try failed with Exception:  ---->{}<---- occured. Trying again with tiffile.".format(ex2), logger=logger)

        # check formatting
        if type(imh) == np.ndarray:
            im.append(imh)
            rl.append(m)
        else:
            logger_switch_output("Readin of {} is of type {} and thus was discarded.".format(
                file_list[m], type(imh)), logger=logger)
    im = np.array(im)
    if im.ndim > 3:
        im = np.transpose(im, [0, -1, 1, 2])
    return np.array(im), rl


def loadStack(file_list, ids=None, ide=None, channel=1):
    '''
    loads an image stack from a file-list (containing the absolute path to a file) given a start and end-number.
    Caution: Errors in file_list or exp_path not catched yet

    Param:
        exp_path: Path to experiment Folder (containing all the images)
        file_list: list of all images to be loaded for this stack
        ids: start index
        ide: end index
        channel: which channel to be read in
        not_prepent standard if file-list already contains full path
    Return:
        im1: stack of read images
        read_list: read list from stack (empty images skipped)
    '''
    # define vars -----------------------------------------------------------
    read_list = []
    prepent_path = False
    # catch some errors -----------------------------------------------------
    fll = len(file_list)  # =maximum iterated entry in list
    if ids == None:
        ids = 0
    if ide == None:
        ide = fll - 1
    if ids < 0:
        raise ValueError('Start-Index is negative. Make ids positive.')
    if ide > fll:
        # raise ValueError('Batch-length too long. Make ide smaller.')
        ide = fll-1
    if not (isinstance(ide, int) or isinstance(ids, int)):
        raise ValueError('ide or ids is not of type int.')
    # print("ids={0}, ide={1}".format(ids,ide))
    if ide < ids:
        raise ValueError('Make sure: ide >= ids.')
    # try:
    #    if exp_path[0] == file_list[0][0]:
    #        prepent_path = False
    # except Exception as e:
    #    print(e)
    # read in ----------------------------------------------------------------
    # start list
    im1, myh = loadChkNonEmpty(file_list, idx=ids, myh=0, ide=ide,
                               channel=channel, prepent_path=prepent_path)  # might still be empty
    myc = ids+myh
    read_list.append(myc)
    im1 = im1[np.newaxis]
    myc += 1
    # iterate through images
    if myc <= ide:
        while myc <= ide:
            # print('myc={}'.format(myc))
            myh = 0
            im1h, myh = loadChkNonEmpty(
                file_list, idx=myc, myh=myh, ide=ide, channel=channel, prepent_path=prepent_path)
            # print("Load-Stack function -- mystep={0}".format(myh))
            read_list.append(myc + myh)
            myc += myh if myh > 0 else 1  # next step
            try:
                im1 = np.concatenate((im1, im1h[np.newaxis]), 0)
            except Exception as e:
                print(e)
                return im1, read_list
            # print("Load-Stack function -- myc={0}".format(myc))
    if isinstance(im1, tuple):
        im1 = nip.image(im1)
    elif isinstance(im1, np.ndarray):
        im1 = nip.image(im1)
    return im1, read_list


def loadChkNonEmpty(file_list, idx=0, myh=0, ide=100, channel=1, prepent_path=False):
    '''
     avoid empty start-image -> so concatenation is possible
    '''
    im1 = loadPrepent(file_list, idx+myh, channel, prepent_path)
    while im1.shape == ():
        myh += 1
        im1 = loadPrepent(file_list, idx+myh, channel, prepent_path)
        if myh == ide:
            break
        return im1
    return im1, myh  # return myh, but is already overwritten in place


def loadPrepent(file_list, idx=0, channel=1, prepent_path=False, exp_path=None):
    '''
    channel_limit: only 3 color-channel exist and hence 3 marks 'all'
    Only implemented for image-structure: [Y,X,channel] -> raspi images
    '''
    # print('idx={}'.format(idx));sys.stdout.flush()
    channel_limit = 3
    if prepent_path:  # somehow nip.readim is not working properly yet
        im1 = np.squeeze(nip.readim(exp_path + file_list[idx]))
        # im1 = np.squeeze(tff.(exp_path + file_list[idx]))
    else:
        im1 = np.squeeze(nip.readim(file_list[idx]))
    if channel < channel_limit:
        im1 = im1[channel, :, :]
    return im1

def dir_test_existance(mydir):
    try:
        if not os.path.exists(mydir):
            os.makedirs(mydir)
            # logger.debug(
            #    'Folder: {0} created successfully'.format(mydir))
    finally:
        # logger.debug('Folder check done!')
        pass
        
def fill_zeros(nbr, max_nbr):
    '''
    Fills pads zeros according to max_nbr in front of a number and returns it as string.
    '''
    return str(nbr).zfill(int(np.log10(max_nbr))+1)

def add_logging(logger_filepath='./logme.log', start_logger='RAWprocessor'):
    '''
    adds logging to an environment. Deletes all existing loggers and creates a stream and a file logger based on setting the root logger and later adding a file logger 'logger'.
    '''
    import logging
    from sys import stdout
    # get root
    root = logging.getLogger()
    # set formatters
    fromage = logging.Formatter(
        datefmt='%Y%m%d %H:%M:%S', fmt='[ %(levelname)-8s ] [ %(name)-13s ] [ %(asctime)s ] %(message)s')
    # set handlers
    strh = logging.StreamHandler(stdout)
    strh.setLevel(logging.DEBUG)
    strh.setFormatter(fromage)
    fh = logging.FileHandler(logger_filepath)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fromage)
    if 'logger' in locals():
        if len(logger.handlers):
            for loghdl in logger.handlers:
                logger.removeHandler(loghdl)
    if len(root.handlers):
        while len(root.handlers):  # make sure that root does not contain any more handlers
            for loghdl in root.handlers:  # it seems it only can delete 1 type of handlers and then leaves the others if multiple are existing
                # print("deleting handler={}".format(loghdl))
                root.removeHandler(loghdl)
    # set root levels
    root.setLevel(logging.DEBUG)
    root.addHandler(strh)
    root.addHandler(fh)
    # add first new handler -> root levels are automatically applied
    logger = logging.getLogger(start_logger)
    logger.setLevel(logging.DEBUG)
    return root, logger

def format_time(tsec):
    '''
    Simple time formatter.

    :param:
    ======
    tsec:INT:   seconds
    '''
    th, trest = divmod(tsec, 3600)
    tm, ts = divmod(trest, 60)
    tform = '{:02}h{:02}m{:02}s.'.format(int(th), int(tm), int(ts))
    return tform

# %%
# -------------------------------- UTILITY TOOLS -------------------------------
def subtract_from_max(im):
    '''
    Inverse intensity values of an image by subtracting the image values from the image-max.
    '''
    im = get_immax(im) - im
    return im
    
def create_value_on_dimpos(dims_total, axes=[-2, -1], scaling=[0.5, 0.5]):
    '''
    Creates dim-vectors for e.g. scaling.

    :param:
    =======
    dims_total:     e.g. via np.ndim
    :axes:          axes to change
    :scaling:       values to change to

    :Example:
    =========
    a = np.repeat(nip.readim('orka')[np.newaxis],3,0)
    b = add_multi_newaxis(a,[1,2,-1])
    print("dim of a="+str(a.shape)+"\ndim of b="+str(b.shape)+".")
    atrans = create_value_on_dimpos(b.ndim,axes=[1,-2,-1],scaling=[2,3,0.25])
    print("scaling factors for array="+str(atrans)+".")
    '''
    res = [1, ] * dims_total
    for m in range(len(axes)):
        res[axes[m]] = scaling[m]
    return res

def get_immax(im):
    '''
    Gets max value of an image.
    '''
    try:
        dmax = np.iinfo(im.dtype).max
    except:
        dmax = np.finfo(im.dtype).max
    return dmax

def subtract_from_max(im):
    '''
    Inverse intensity values of an image by subtracting the image values from the image-max.
    '''
    im = get_immax(im) - im
    return im
    

def channel_getshift(im):
    '''
    Operations on 1 image within channels
    '''
    shift = []
    myshift = 0
    id1, id2 = generate_combinations(3, combined_entries=2)
    for m in range(len(id1)):
        myshift, _, _, _ = findshift(im[id1[m]], im[id2[m]], 100)
        shift.append(myshift)
    return np.array(shift)


def image_getshift(im, im_ref, prec=100):
    '''
    Wrapper for findshift to enable shifts between stacks or with respect to a reference. Made for nD images, that will be compared on a 2D level.
    TODO: Does not work properly for e.g. ims=[10,3,120,120] and im_refs=[3,120,120]. ETC!
    :PARAM:
    ======
    im:        im-stack or images to compare
    im_ref:     reference image (2d) or comparison stack of same sace as im

    :OUT:
    =====
    shift:      the calculated shifts
    '''
    # param
    shift = []
    myshift = 0
    imd = im.ndim
    im_refd = im_ref.ndim
    ims = im.shape
    im_refs = im_ref.shape
    # sanity checks
    if imd > 3:
        im = np.reshape(im, [np.prod(ims[:-2]), ims[-2], ims[-1]])
    if im_refd > 3:
        im_ref = np.reshape(im_ref, [np.prod(ims[:-2]), ims[-2], ims[-1]])
    # execute different dimensional cases
    if imd == 2 and im_refd == 2:
        myshift, _, _, _ = findshift(im, im_ref, prec)
        shift.append(myshift)
    elif imd > im_refd and im_refd == 2:
        for m in range(ims[0]):
            myshift, _, _, _ = findshift(im[m], im_ref, prec)
            shift.append(myshift)
    elif imd > 2 and im_refd > 2:
        for m in range(im.shape[0]):
            myshift, _, _, _ = findshift(im[m], im_ref[m % im_refs[0]], prec)
            shift.append(myshift)
    else:
        raise ValueError('Wrong dimensions of input arrays.')
    if imd > 3:
        shift = np.reshape(np.array(shift), tuple(list(ims[:-2]) + [2, ]))
    else:
        shift = np.array(shift)
    return shift


def findshift(im1, im2, prec=100, printout=False):
    '''
    Just a wrapper for the Skimage function using sub-pixel shifts, but with nice info-printout.
    link: https://scikit-image.org/docs/dev/auto_examples/transform/plot_register_translation.html

    Check "image_getshift" to use for a stack or with a reference.

    :param:
    =======
    :im1: reference image
    :im2: shifted image
    :prec: upsample-factor = number of digits used for sub-pix-precision (for sub-sampling)

    :out:
    =====
    :shift: calculated shift-vector
    :error: translation invariant normalized RMS error between images
    :diffphase: global phase between images -> should be 0
    :tend: time needed for processing
    '''
    from time import time
    from skimage.feature import register_translation
    tstart = time()
    # 'real' marks that input-data still has to be fft-ed
    shift, error, diffphase = register_translation(
        im1, im2, prec, space='real', return_error=True)
    tend = np.round(time() - tstart, 2)
    if printout:
        print("Found shifts={} with upsampling={}, error={} and diffphase={} in {}s.".format(
            shift, prec, np.round(error, 4), diffphase, tend))
    return shift, error, diffphase, tend

def transpose_arbitrary(imstack, idx_startpos=[-2, -1], idx_endpos=[0, 1]):
    '''
    creates the forward- and backward transpose-list to change stride-order for easy access on elements at particular positions.

    TODO: add security/safety checks
    '''
    # some sanity
    if type(idx_startpos) == int:
        idx_startpos = [idx_startpos, ]
    if type(idx_endpos) == int:
        idx_endpos = [idx_endpos, ]
    # create transpose list
    trlist = list(range(imstack.ndim))
    for m in range(len(idx_startpos)):
        idxh = trlist[idx_startpos[m]]
        trlist[idx_startpos[m]] = trlist[idx_endpos[m]]
        trlist[idx_endpos[m]] = idxh
    return trlist

# %%
# -------------------------------- NUMBER TOOLS -------------------------------    

def generate_combinations(nbr_entries, combined_entries=2):
    '''
    Creates a set of index-lists according to "combined_entries" that complete cover all permutations that are possible within the length of the input-list (1D). For combined_entries=2 this means the classical group-combinations: n*(n-1)/2 possibilities. 
    TODO: include higher combined_entries list-combinations

    Example: 
    ========
    a = []
    '''
    if combined_entries == 2:
        id1 = []
        id2 = []
        offset = 1
        for m in range(0, nbr_entries-1):
            for n in range(offset, nbr_entries):
                id1.append(m)
                id2.append(n)
            offset += 1
    else:
        raise ValueError(
            "The expected combined_entries size is not implemented yet.")
    return id1, id2

# %%
# -------------------------------- STATISTICAL TOOLS -------------------------------    
def stf_basic(im, printout=False):
    '''
    Basic statistical sharpness metrics: MAX,MIN,MEAN,MEDIAN,VAR,NVAR. Reducing the whole dimensionality to 1 value.
    '''
    im_res = list()
    use_axis = (-2, -1)
    im_res.append(np.max(im, axis=use_axis))
    im_res.append(np.min(im, axis=use_axis))
    im_res.append(np.mean(im, axis=use_axis))
    im_res.append(np.median(im, axis=use_axis))
    im_res.append(np.var(im, axis=use_axis))
    im_res.append(im_res[4]/im_res[2]**2)  # normalized variance (NVAR)
    if printout == True:
        print("Basic analysis yields:\nMAX=\t{}\nMIN=\t{}\nMEAN=\t{}\nMEDIAN=\t{}\nVAR=\t{}\nNVAR=\t{}".format(
            im_res[0], im_res[1], im_res[2], im_res[3], im_res[4], im_res[5]))
    return np.array(im_res)

def diff_tenengrad(im):
    '''
    Calculates Tenengrad-Sharpness Metric.
    '''
    impix = 1.0 / np.sqrt(np.prod(im.shape))
    return impix * np.sum(diff_sobel_horizontal(im)**2 + diff_sobel_vertical(im)**2, axis=(-2, -1))


def diff_sobel_horizontal(im):
    '''
    Calculates the horizontal sobel-filter.
    Filter-shape: [[-1 0 1],[ -2 0 2],[-1 0 1]] -> separabel:  np.outer(np.transpose([1,2,1]),[-1,0,1])
    '''
    # use separability
    trlist = transpose_arbitrary(im, idx_startpos=[-2, -1], idx_endpos=[1, 0])
    im = np.transpose(im, trlist)
    x_res = im[:, 2:] - im[:, :-2]  # only acts on x
    xy_res = x_res[:-2] + 2*x_res[1:-1] + x_res[2:]  # only uses the y-coords
    return np.transpose(xy_res, trlist)


def diff_sobel_vertical(im):
    '''
    Calculates the vertical sobel-filter.
    Filter-shape: [[-1,-2,-1],[0,0,0],[1,2,1]] -> separabel:  np.outer(np.transpose([-1,0,1]),[1,2,1])
    '''
    # use separability
    trlist = transpose_arbitrary(im, idx_startpos=[-2, -1], idx_endpos=[1, 0])
    im = np.transpose(im, trlist)
    x_res = im[:, :-2] + 2*im[:, 1:-1] + im[:, 2:]  # only x coords
    xy_res = x_res[2:] - x_res[:-2]  # further on y coords
    return np.transpose(xy_res)
    
# %%
# -------------------------------- VIDEO TOOLS -------------------------------


def convert_stk2vid(save_file, file_list=None, batch_size=None, mode=0, vid_param={}):
    '''
    This function converts a stack of images into a movie. On standard configuration stores frames into split-videos.

    :param:
    =======
    save_file: Filename (with path) of output
    save_format: chooses file-format(compressor) used -> 0: AVI(XVID), 1: MP4(X264)
    file_list: file-list of images to be loaded and put together
    batch_size: max-size of load batch (to enable to run on weaker systems)
    mode: which channels to use -> 0: red, 1: green, 2: blue, 3: rgb, 4: split and displayed in 1 frame with roi (a 3rd), 5: split storage (default)
    frame_size: resolution of the output-image
    frame_rate: Frames per second
    frame_rescale: 1: rescales the image to the output frame_size; 0: cuts out roi from Roi position
    roi: coordinates of ROI in (xstart,xend,ystart,yend) -> (default:) maximum ROI from center that fits frame_size

    :out:
    =====
    none

    '''
    # implement basic functionality for just storing video with certain properties
    if file_list == None:
        raise ValueError('No filelist given.')
    else:
        # get parameters
        [fl_len, fl_iter, fl_lastiter] = get_batch_numbers(
            filelist=file_list, batch_size=batch_size)
        # check sanity of data
        save_file, vid_param = sanitycheck_save2vid(save_file, vid_param)
        # start out-container
        out = save2vid_initcontainer(save_file[0] + save_file[1], vid_param)
        # iterate over batches
        for cla in range(fl_iter):
            # get right iteration values
            ids = cla * batch_size
            ide = ids+batch_size-1
            if cla == fl_iter:
                batch_size = fl_lastiter
            # load batch
            data_stack, data_stack_rf = loadStack(
                file_list=file_list, ids=ids, ide=ide, channel=3)
            # limit to bit_depth and reshape for writing out
            dss = data_stack.shape
            im = np.reshape(data_stack, newshape=(
                dss[:-3]+(dss[-2],)+(dss[-1],)+(dss[-3],)))
            data_stack = limit_bitdepth(
                im, vid_param['bitformat'], imin=None, imax=None, inorm=True, hascolor=True)
            save2vid(save_file, vid_param, out)
    out.release()
    print("Thanks for calling: Convert_stk2vid. ")
    return True


def save2vid(im, save_file=None, vid_param={}, out=False,hasChannels=None,isstack=None):
    '''
    Saves an image or image-stack to a given path. All necessary parameters are hidden in vid_param.
    Needs opencv3 (py3) and FFMPEG installed (has to be installed explicitely in windows).

    :param:
    =======
    :im:        image or image-stack
    :save_file: absolute path and filename (without filetype ending) as two-element list: [PATH,FILENAME]
    :vid_param: Dictionary containing all the necessary parameters. Check 'sanitycheck_vid_param'-function desrciption for further explanation.
    :out:       opencv-videoWriter-object -> can be used to not close a video and continue to append images, e.g. for stack processing

    Complete Example:
    =================
    vid_param= {'vformat':'H264','vcontainer':'mp4',
        'vaspectratio':[16,9],'vscale':'h','vfps':12}
    save_file = [
        'D:/Data/01_Fluidi/data/processed/Inkubator-Setup02-UC2_Inku_450nm/20190815/expt_017/','20190815-01']
    '''
    # sanity checks
    im, hc, iss = save2vid_assure_stack_shape(im)
    hasChannels = hc if hasChannels is None else hasChannels
    isstack = iss if isstack is None else isstack
       
    if type(out) == bool:
        save_path, vid_param = sanitycheck_save2vid(save_file, vid_param)
        vid = save2vid_initcontainer(save_path, vid_param)
    else:
        vid = out
    if not im.dtype == np.dtype(vid_param['bitformat']):
        im = limit_bitdepth(
            im, vid_param['bitformat'], imin=None, imax=None, inorm=False, hascolor=hasChannels)
    
    # save stack or image
    if isstack:
        imh = np.transpose(im, [0, 2, 3, 1]) if im.shape[-3] == 3 else im
        for m in range(im.shape[0]):
            vid.write(imh[m])
    else:
        if hasChannels:
            imh = np.transpose(im, [1, 2, 0])
        else:
            imh = np.repeat(im[:, :, np.newaxis], axis=-1, repeats=3)
        vid.write(imh)
    # close stack
    if type(out) == bool:
        if out == False:  # to save release
            save2vid_closecontainer(vid)
            vid = out
    # return
    return vid, vid_param, hasChannels, isstack


def limit_bitdepth(im, iformat='uint8', imin=None, imax=None, inorm=True, hascolor=False):
    '''
    Rescales the image into uint8. immin and immax can be explicitely given (e.g. in term of stackprocessing).
    Asssumes stack-shape [ndim,y,x] or [ndim,Y,X,COLOR] and takes imin and imax of whole stack if not given otherwise.
    :param:
    ======
    :vformat:   e.g. 'uint8' (...16,32,64), 'float16' (32,64), 'complex64' (128)   -> possible formats of np.dtype -> https://docs.scipy.org/doc/numpy-1.13.0/reference/arrays.dtypes.html

    Example:
    ========
    a = nip.readim('orka')
    a1 = limit_bitdepth(a,'uint32')
    <intern: im = nip.readim('orka');iformat='uint8';imin=None;imax=None;inorm=True;  >
    '''
    np.array
    iformatd = np.dtype(iformat)
    imdh = im.shape
    if im.ndim < 2:
        raise ValueError(
            "Image dimension too small. Only for 2D and higher implemented.")
    else:
        if inorm == True:
            # normalize to 0 only if minimum value of aimed datatype is zero (=avoid clipping)
            if np.iinfo(iformatd).min == 0:
                if imin == None:
                    if hascolor:
                        if im.ndim > 3:
                            imin = np.min(
                                im, axis=[-3, -2])[..., np.newaxis, np.newaxis, :]
                        else:
                            imin = np.min(
                                im, axis=[-3, -2])[np.newaxis, np.newaxis, :]
                    else:
                        imin = np.min(im)
                # if not imin.shape == ():
                #    imin = imin[...,np.newaxis,np.newaxis]
                im = im - imin
            if imax == None:
                if hascolor:
                    if im.ndim > 3:
                        imax = abs(
                            np.max(abs(im), axis=[-3, -2]))[..., np.newaxis, np.newaxis, :]
                    else:
                        imax = abs(
                            np.max(abs(im), axis=[-3, -2]))[..., np.newaxis, np.newaxis, :]
                # maximum could be a negative value (inner abs) AND do not want to have change of sign (outer abs)
                imax = abs(np.max(abs(im)))
            # if not imax.shape == ():
            #    imin = imin[...,np.newaxis,np.newaxis]
            im = im / imax
        else:  # just compress range to fit into int
            im_min = np.min(im)
            im_max = np.max(im)
            im_vr = im_max - im_min  # value range
            try:
                dtm = np.iinfo(iformatd).max
            except:
                dtm = np.finfo(iformatd).max
            if im_vr > dtm:
                im -= im_min
                im = im / np.max(im) * dtm
            else:
                if np.max(im) > dtm:  # assume that even though the range fits into uint8 the image somehow (due to processing) got shifted above max-value of value-range that the original format had -> hence: shifting back to max instead of resetting by min-offset
                    im -= (np.max(im) - dtm)
                elif np.min(im) < 0:  # same as above, just for min
                    im -= np.min(im)
        # if np.issubdtype(iformatd, np.integer):
        #    im = im*np.iinfo(iformatd).max
        im = np.array(im, dtype=iformatd)
    return im


def save2vid_assure_stack_shape(im,isstack=False,hasChannels=False):
    '''
    Tests the stack for the appropriate format and converts if necessary for conversion.
    Input-Image needs to have X,Y-dimensions at last position, hence for 3D-stack with 2 channels e.g. [stackdim,channeldim,Y,X].

    :param:
    =======
    :im:        numpy or nip-array (image)
    '''
    # convert stack to correct color_space
    if im.ndim < 2:
        raise ValueError("Dimension of input-image is too small.")
    if im.ndim == 2:  # only 2D-image
        pass
    else:  # nD-image
        hasChannels = True
        if im.shape[-3] > 3 and im.ndim > 3:  # -3.dim is not channel, but stack-dimension
            im = np.reshape(im, newshape=[np.prod(
                im.shape[:-2], im.shape[-2], im.shape[-1])])
            isstack = True
        else:  # -3.dim is channel dimension
            if im.shape[-3] == 1:
                im = np.repeat(im, repeats=3, axis=-3)
            elif im.shape[-3] == 2:
                ims = im.shape
                ims[-3] = 1
                im_zeros = np.zeros(ims)
                im = np.concatenate([im, im_zeros], axis=-3)
            else:  # no problem
                pass
    # return image and whether it is a stack
    return im, hasChannels, isstack
    # if channel < 3:
    #        frame = cv2.cvtColor(
    #            np.array(a_pil, 'uint8'), cv2.COLOR_GRAY2BGR)
    #    else:
    #        frame = cv2.cvtColor(
    #           np.array(a_pil, 'uint8'), cv2.COLOR_RGB2BGR)


def rearrange_array(im, idx=None, axis=-3, assureIndices=True):
    '''
    TODO: NOT FINISHED!
    Rearranges an axis according to an index-list. Could lead to dropouts etc as well. Only positive index numbers allowed.
    '''
    # sanity for axis
    if abs(axis) > im.ndim:
        axis = im.ndim
    # sanity for idx
    if not type(idx) == list:
        if not idx == None:
            idx = [idx, ]
        else:  # nothing to be done here
            pass
    else:
        if idx == []:
            pass
    # sanity assuring indices are non-neg and smaller max-val
    if assureIndices:
        idx = abs(np.array(idx))
        idxm = im.shape[axis]
        idx = np.delete(idx, idx[idx >= idxm])
    idx_forward, idx_backward = array_switchpos_idx(
        listdim=im.ndim, pstart=axis, pend=0)
    im.transpose(idx_forward)
    # TODO: WHAT HERE?
    im.transpose(idx_backward)
    return im


def array_switchpos_idx(listdim=3, pstart=-2, pend=0):
    '''
    # TODO: NOT FINISHED!
    Calculates the indeces neccessary to switch two elements of a list (e.g. dimensions of an image)
    '''
    axis = pend
    idx1 = list(range(listdim))
    idx2 = list(range(listdim))
    idx_forward = [idx1.pop(axis), ] + idx1
    idx2.pop(0)
    idf_backward = idx2[:axis] + [0, ] + idx2[axis:]
    return idx_forward, idf_backward


def save2vid_initcontainer(save_name, vid_param={}):
    '''
    Creates an OpenCV-VideoWriter-object with the given parameters.
    Note: OpenCV switches height and width on creation/storage. Hence, formats have to be switched. (Input is: Height x Width).
    '''

    out = cv2.VideoWriter(save_name, cv2.VideoWriter_fourcc(
        *vid_param['vformat']), vid_param['vfps'], (vid_param['vpixels'][1], vid_param['vpixels'][0]))
    return out


def save2vid_closecontainer(out):
    '''
    Safely closes the container.
    '''
    sleep(0.05)
    out.release()
    sleep(0.5)


def sanitycheck_save2vid(save_file, vid_param):
    '''
    Tests the necessary entries in vid_param and adds things if missing. First values of param mark default values.

    :param:
    =======
    :vformat:STRING:            'XVID','H264','H265'            -> tested video formats
    :vcontainer:STRING:         'avi','mp4','mkv'               -> tested containers
    :vaspectratio: INT_ARRAY:   [16,9],[22,9], [4,3], [1,1]     -> tested ratios, but all should work
    :vpixels:INT_ARRAY:         [1920,1080]                     -> final resolution of the output video
    :vscale:STRING:             None,'h','w'                    -> rescale final video size using vaspectratio and the height or width of the input image(stack)
    :vfps:INT:                  14                              -> frames per second
    '''
    # Set standard-configuration
    from sys import platform as sysplatform

    # if sysplatform == 'linux': #somehow it is not working on FA8_TITANX_UBU system... -.-'
    #    std_conf = {'vformat': 'H264', 'vcontainer': 'mp4', 'vaspectratio':[16, 9], 'vscale': None, 'vfps': 12,'vpixels':[1920, 1080],'bitformat': 'uint8'} #X264+mp4 does not work on windows
    # else:
    std_conf = {'vformat': 'XVID', 'vcontainer': 'avi', 'vaspectratio': [16, 9], 'vscale': None, 'vfps': 12, 'vpixels': [
        1920, 1080], 'bitformat': 'uint8'}  # X264+mp4 does not work on windows
    # check param dict
    if not type(vid_param) == dict:
        vid_param = {}
    for m in std_conf:
        if m not in vid_param:
            vid_param[m] = std_conf[m]
    # check save_file path etc
    if save_file == None:
        save_file = [os.getcwd(), 'save2vid.' + vid_param['vcontainer']]
    else:
        save_file = save_file + '.' + vid_param['vcontainer']
    # sanity check that path exists and acessible
    save_path = check_path(save_file)
    # return
    return save_file, vid_param


def check_path(file_path):
    '''
    Checks whether file_path exists and if not, creates it.
    Note: Assume that Filepath ends with "\\" or "/" to mark a directory. 
    '''
    # match path
    try: 
        import re
        #file_path_new = re.compile(r'([A-Z:|/\w*]+)*[\\|/](([\w-]+)*[\\|/])*').search(file_path).group()
        file_path_new = re.compile(r'[\\|/]*([\w-]*[:|.]*[\\|/]+)*').search(file_path).group()
    except Exception as e:
        print(f"Exception {e} ocurred. Could not match directory path in file_path or given file_path is not of string-type.")            
    
    # create if necessary
    if not os.path.isdir(file_path_new):
            os.makedirs(file_path_new)
            print('File path -> ' + file_path_new + ' <- freshly created!')

    # done?
    return file_path_new


def convert_time2str(nbr=1,nbr2Time=[0,0,1,0,0]):
    '''
    Converts a given timepoint (in ms) to strangi
    '''
    tdict = ['ms','s','m','h','d']
    fdict = [1000,60,60,24,100000]
    timestr = ""
    start_found = False

    # skip empty tails and convert into 
    tt = [nbr*m for m in nbr2Time]
    for m in range(len(tt)):
        if nbr2Time[m] > 0 and not start_found:
            start_found = True
        if start_found:
            if m == 4:
                assert(tt[m] < fdict[m],"Unbelieveable, you made    measurements longer than 273years?!")
            a = tt[m] // fdict[m]
            if a > 0:
                tt[m+1] += a
                tt[m] = np.mod(tt[m],fdict[m])
            timestr = "{:02}{}".format(tt[m],tdict[m]) + timestr
        else:
            pass
    
    # done?
    return timestr

def matplotlib_imageInActualSize(im, printstat=False):
    '''
    Displays image in actual size. Slightly changed from here : https://stackoverflow.com/a/53816322
    '''
    dpi = mplParams['figure.dpi']
    figsize = im.shape[-1] / float(dpi), im.shape[-2] / float(dpi)
    fig = plt.figure(figsize=figsize)
    if printstat:
        print("Figure.shape = {}.\nFigure.size = {}.".format(im.shape,figsize))

    # done?
    return fig

def matplotlib_omitAxesAndBoxes(fig, im):
    '''
    Omits axes. Slightly changed from here : https://stackoverflow.com/a/53816322
    '''
    ax = fig.add_axes([0, 0, 1, 1])

    # Hide spines, ticks, etc.
    ax.axis('off')
    ax.axes.get_xaxis().set_visible(False)
    ax.axes.get_yaxis().set_visible(False)

    # Display the image.
    if im.ndim == 2:
        ax.imshow(im, cmap='gray', interpolation='none')
    elif im.ndim == 3: 
        # assumes shape: [RGB,Y,X]
        ax.imshow(np.transpose(im,[1,2,0]), interpolation='none')
    else:
        raise ValueError("Wrong dimensionality of image supplied.")

    # done?
    return ax

def matplotlib_toNumpy(fig):
    '''
    Converts a pyplot to numpy array for eg pixel-wise comparison. Inspired by: https://stackoverflow.com/a/61443397.
    '''
    # "save" into buffer to get correct formatting
    io_buf = io.BytesIO()
    fig.savefig(io_buf, format='raw')

    # get buffer and reshape to proper size
    io_buf.seek(0)
    im = np.reshape(np.frombuffer(io_buf.getvalue(), dtype=np.uint8),
                        newshape=(int(fig.bbox.bounds[3]), int(fig.bbox.bounds[2]), -1))
    io_buf.close()

    # cut out from [Y,X,RGBA]
    im = np.transpose(im,[2,0,1])[:3]

    # done?
    return im

def matplotlib_TextAndScalebar(im, ax, textstr,font_size=None,y_offset=None,dx=0.2,units="um", color='white',length_fraction=0.2):
    '''
    Adds text to the lower-left part of the image and a scalebar to the lower right edge. 
    Note: Not generic yet, but enough for the actual purpose.
    '''
    # parameters
    font_size = im.shape[-1] // 25 if font_size == None else font_size
    y_offset = int(im.shape[-2]*0.99) if y_offset == None else y_offset


    # set and add scalebar
    scalebar = ScaleBar(dx=dx,units="um",dimension='si-length',length_fraction=length_fraction, location='lower right', frameon=False, color=color,font_properties={'size': font_size, 'family': 'Helvetica'}) 
    ax.add_artist(scalebar)

    # add text
    ax.text(0,y_offset, textstr,fontsize=font_size, color='white', fontname='Helvetica') 

    # done?
    return ax

def label_image(im,nbr=0,nbr2Time=[0,0,1,0,0],pixelsize=0.17,pixelunit="um",font_size=None, use_matplotlib=True, logger=None, log_correction=False):
    '''
    Atomic version of deprecated vid_addContent_and_format.
    Assumes 2D-grey images for now.

    PARAMS:
    =======
    :im:        (IMAGE) File to work on
    :nbr:       (INT) number of image
    :nbr2Time:  (ARRAY) List of distance between equally spaced time-events -> units are: ['ms','s','m','h','d'] -> on default: [0,0,1,0,0] means 1 minute per image
    :pixelsize: (FLOAT) size of a pixel assumed in µm

    OUTPUT:
    =======
    :im:    labeled_image

    NOTE: PIL implementation not finished
    '''
    # get time-string
    timestr = convert_time2str(nbr=nbr,nbr2Time=nbr2Time)

    # make sure to suppress logging from matplotlib-matching
    #logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('matplotlib.font_manager').disabled = True

    if use_matplotlib:
        # prepare convert to work with active DPI
        fig1 = matplotlib_imageInActualSize(im, printstat=False)

        # omit any bounding boxes as good as possible
        ax1 = matplotlib_omitAxesAndBoxes(fig1, im)

        # add text and scalebar
        ax1 = matplotlib_TextAndScalebar(im, ax1, timestr,dx=pixelsize,units=pixelunit, font_size=None, color='white')

        # get back to numpy
        im_res = matplotlib_toNumpy(fig1)

        # make sure for correct shape
        if not im_res.shape == im.shape:
            if log_correction:
                if logger is not None: 
                    logger.debug(f"Corrected im_nbr{nbr} from shape={im_res.shape} to shape={im.shape}")
                else: 
                    print(f"Corrected im_nbr{nbr} from shape={im_res.shape} to shape={im.shape}")
            im_res = nip.extract(im_res,im.shape)

        # free RAM
        plt.close()

    else:
        # parameters
        scalebar_ratio = 5
        scalebar_size = 0.1

        # create image -> assumed 2D-grey-images for now
        a_pil = PIL.Image.fromarray(im.astype('uint8'), 'L')
        a_fill = 255
        draw = PIL.ImageDraw.Draw(a_pil)
        font = PIL.ImageFont.truetype(font='complex_.ttf', size=font_size)

        # get and draw time

        draw.text((0, a_pil.height-font_size), timestr, fill=a_fill, font=font)

        # get scalebar properties and draw
        if pixelsize is not None:
            # scalebar
            scalebar_height = scalebar_height//scalebar_ratio
            scalebar_width = int(im.shape[-1]*scalebar_size)
            scalebar_pos = [a_pil.height - 2*scalebar_height,a_pil.width - int(1.5*scalebar_width)]
            draw.rectangle((scalebar_pos[0],  scalebar_pos[1] , scalebar_height, scalebar_width), fill=a_fill)

        im_res = a_pil
        
    #done?
    return im_res


# %% ------------------------------------------------------
# --- Final UC2-Inkubator Processing Functions          ---
# ---------------------------------------------------------
#

def uc2_eval_shifts(res, kl=[], cla=0, ids=0, ide=0, channel=1, threshhold=[], logger=None):
    '''
    Evaluate non-excluded shifts from the analysed ROIs. Rule: if majority of ROIs is shifted, accept shift.
    Only for 1 channel!
    For now: only shift for the least amount of changes:

    :param:
    ======
    res:        dictionary containing the shift-data from various rois
    kl:         list of files that will be excluded
    ids:        start-index
    ide:        ending-index
    channel:    to be used

    :out:
    =====
    shift_list:     shifts
    sellist:        index-list of images to be shifted
    '''
    # old
    '''
    myshifts = np.squeeze(np.array(res['roi_shifts']))[:, :, channel, :]
    mysa = np.abs(np.copy(myshifts))
    shift_list = []
    sellist = []
    # eval-shift for all ROIs
    collx = []
    colly = []
    colll = []
    for roi in mysa:
        resx = np.squeeze(np.array(np.where(roi[:, 0] >= 0.9)))
        resy = np.squeeze(np.array(np.where(roi[:, 1] >= 0.9)))
        collx.append(resx)
        colly.append(resy)
        colll.append([resx.size, resy.size])
    colll = np.array(colll)
    selx, sely = [np.argmin(colll[:, 0]), np.argmin(colll[:, 1])]
    if not (colll[selx, 0] + colll[sely, 1] == 0):
        if colll[selx, 0] < colll[sely, 1]:
            sellist = colly[sely]
            selidx = sely
        else:
            sellist = collx[selx]
            selidx = selx
        sellist = [m for m in sellist if not m in kl]
        shift_list = [myshifts[selidx, m]  for m in sellist]
    '''
    # format shift_list to have [analysedROI,image-nbr,calculated x-y-shifts]
    myshifts = np.transpose(np.squeeze(
        np.array(res['roi_shifts']))[cla], [1, 0, 2])

    # propare helpful arrays -> for reconstruction: shift_list will just contain zeros where there was no shifts applied
    shift_list = np.zeros((ide-ids, 2))
    sel_shift_list = []
    x_shifts_accepted = []
    y_shifts_accepted = []
    size_of_accepted_lists = []
    if threshhold == []:
        threshhold = [0.9, 0.9]

    # only accept shifts that are bigger than threshhold and store accepted shifts into list
    for roi in myshifts:
        x_shifts_greater_thresh = np.squeeze(
            np.array(np.where(np.abs(roi[:, 0]) >= threshhold[0])))
        y_shifts_greater_thresh = np.squeeze(
            np.array(np.where(np.abs(roi[:, 1]) >= threshhold[1])))
        x_shifts_accepted.append(x_shifts_greater_thresh)
        y_shifts_accepted.append(y_shifts_greater_thresh)
        size_of_accepted_lists.append(
            [x_shifts_greater_thresh.size, y_shifts_greater_thresh.size])
    size_of_accepted_lists = np.array(size_of_accepted_lists)

    # select ROI with the least amount of shifts for x and y individually
    selx, sely = [np.argmin(size_of_accepted_lists[:, 0]),
                  np.argmin(size_of_accepted_lists[:, 1])]

    # if shifts have to be applied -> if length of shifts of accepted_x ROI is shorter than accepted_y -> work on longer list, hence y -> and vice-versa
    if not (size_of_accepted_lists[selx, 0] + size_of_accepted_lists[sely, 1] == 0):
        if size_of_accepted_lists[selx, 0] < size_of_accepted_lists[sely, 1]:
            sel_shift_list = y_shifts_accepted[sely]
            sel_ROI = sely
        else:
            sel_shift_list = x_shifts_accepted[selx]
            sel_ROI = selx
        try:
            sel_shift_listn = []
            for m in range(ide-ids):
                if not m in kl:
                    if m in sel_shift_list:
                        sel_shift_listn.append(m)
                        shift_list[m] = myshifts[sel_ROI, m]
            sel_shift_list = sel_shift_listn
        except Exception as e:
            if not logger == None:
                logger.warning(e)
                logger.warning(
                    'To continue proper processing, empty lists where generated.')
            sel_shift_list = []
            shift_list = []
    return shift_list, sel_shift_list


def uc2_preprocessing_refuseImages(data_stack, res, ids=0, ide=0, channel=1, criteria='mean'):
    '''
    Using a given criteria to refuse empty/insufficient images

    :param:
    =======
    data_stack: image stack in
    res:        super-functions dictionary to store processing info
    criteria:   Only 'mean' yet

    :out:
    =====
    data_stack: manipulated data_stack
    res:        manipulated dictionary
    kl:         index-list of excluded elements
    '''
    thresh = 0.15
    im_dat = np.array([np.array(res['image_min'])[ids:ide, channel], np.array(
        res['image_mean'])[ids:ide, channel], np.array(res['image_max'])[ids:ide, channel]])
    if criteria == 'mean':
        # use mean of active stack to have a more stable measure
        tm = np.mean(im_dat[1])
        c = [m or n for m,n in zip(im_dat[1] < thresh*tm,im_dat[1] > (2-thresh)*tm)]
        kl = np.where(c)[0]
        if kl.size:
            for idx,pos in enumerate(kl):
                res['image_skipped_filename'].append(
                    res['image_filename_list'][ids+pos])
                res['image_skipped_index'].append(ids + pos)
                data_stack = np.delete(data_stack, obj=pos-idx, axis=0)
            # del
    return data_stack, res, kl


def uc2_preprocessing_metrics(data_stack, mean_ref=[], pred=[], ROIs=None, res=None, ids=0, ide=0, cla=0, name_metrics=None, name_stacks=None, prec=10):
    '''
    Calculates a set of predefined metrics to populate the dictionary for further analysis

    :param:
    ======
    ids:    Start index
    ide:    End-index
    cla:    counter for global (superior/calling functions) iteration
    '''

    # make sure mean_ref is non-empty
    if len(mean_ref) == 0:
        raise ValueError(
            'Reference for calculation of relative shifts not provided.')

    # generate ROIs for analysis -> assumes stack to be 4D ([series,color,y,x]) and ROI to be [ymin,ymax,xmin,xmax]
    data_stack_ROIs = []
    for m in ROIs:
        dat = data_stack[:, :, m[0]:m[1], m[2]:m[3]]
        data_stack_ROIs.append(dat)

    # 1st -> interchannel shifts; 2nd -> interimage changes
    if cla == 0:
        res['interchannel_shift_offset'] = channel_getshift(
            np.array(nip.DampEdge(data_stack[0], rwidth=0.1)))
        res['interchannel_shift_offset_roi'] = [channel_getshift(
            np.array(nip.DampEdge(dat, rwidth=0.1))) for dat in data_stack_ROIs]
    elif cla > 0:
        res['image_shifts'] = res['image_shifts'] + \
            list(image_getshift(
                data_stack[0], mean_ref, prec=prec)[np.newaxis])
        res['image_diff_var'] = res['image_diff_var'] + \
            list(np.var(data_stack[0]-pred, axis=(-2, -1))[np.newaxis])
    if ide-ids > 0:
        roi_shifts = []
        roi_diff_var = []
        for m in range(len(ROIs)):
            # nip.v5(nip.cat((data_stack_ROIs[m][1][1], mean_ref[1, ROIs[m][0]: ROIs[m][1], ROIs[m][2]: ROIs[m][3]])))
            roi_shifts.append(image_getshift(
                data_stack_ROIs[m], mean_ref[:, ROIs[m][0]: ROIs[m][1], ROIs[m][2]: ROIs[m][3]], prec=prec))
        res['roi_shifts'] = res['roi_shifts'] + roi_shifts
        res['image_shifts'] = res['image_shifts'] + \
            list(image_getshift(
                data_stack[1:], data_stack[:-1], prec=prec))
        # res['roi_diff_var'] = res['roi_diff_var'] + list(np.var(data_stack_roi[1:] - data_stack_roi[:-1], axis=(-2, -1)))
        res['image_diff_var'] = res['image_diff_var'] + \
            list(np.var(data_stack[1:]-data_stack[:-1], axis=(-2, -1)))
    datal = [data_stack]  # , data_stack_roi
    namel = [name_stacks[0]]  # , name_roi
    for m in range(len(datal)):
        ima = datal[m]
        res_stf_basics = stf_basic(ima)
        for n in range(4):
            res[namel[m] + name_metrics[n]] = res[namel[m] +
                                                  name_metrics[n]] + list(res_stf_basics[n])
        res[namel[m] + name_metrics[4]] = res[namel[m] +
                                              name_metrics[4]] + list(diff_tenengrad(ima))
    # store for next round
    pred = data_stack[-1].copy()
    # pred_roi = data_stack_roi[-1].copy()

    return res, pred


def get_mean_from_stack(load_path, save_path='', load_fn_proto='jpg', mean_range=[], channel=None, batch_size=50, binning=None, colorful=1, inverse_intensity=False, save_every=False, clear_path=False):
    '''
    Calcutes the mean from a range of readin-images from a folder. Idea: Create a reference, e.g. to do shift analysis, but have a cleaner stack with better SNR and less influenced by noise.

    :param:
    load_path:  path to be used
    mean_range: Array denoting start and end of filelist (hence files) to be used -> e.g.: [75,110]
    channel:    Color-channel to be used

    :out:
    ref_mean
    '''
    # variable
    stack_meanh = []

    # read in
    os.chdir(load_path)
    fl = get_filelist(load_path=load_path, fn_proto=load_fn_proto)
    if not mean_range == []:
        fl = fl[mean_range[0]:mean_range[1]]
    [fl_len, fl_iter, fl_lastiter] = get_batch_numbers(
        filelist=fl, batch_size=batch_size)

    # start iteration
    for cla in range(fl_iter):
        tstart = time()

        # get right iteration values
        ids = cla * batch_size
        ide = (ids + batch_size) if cla < (fl_iter -
                                           1) else (ids + fl_lastiter)
        if cla == fl_iter-1:
            batch_size = fl_lastiter

        # read in
        data_stack, _ = loadStackfast(fl[ids:ide], colorful=colorful)

        # inverse
        if inverse_intensity:
            data_stack = subtract_from_max(data_stack)

        # if not data_stack.shape
        if not channel == None:
            data_stack = data_stack[:, channel, :, :]
        if binning:
            data_stack = np.array(nip.resample(data_stack, create_value_on_dimpos(
                data_stack.ndim, axes=[-2, -1], scaling=[1.0/binning[0], 1.0/binning[1]]))) / (binning[0] * binning[1])

        # calculate mean
        stack_meanh1 = np.mean(data_stack, axis=0)
        stack_meanh.append(stack_meanh1)

        # save every single mean if selected
        if save_every:
            if not stack_meanh1.dtype == np.dtype('float16'):
                stack_meanh1 = nip.image(limit_bitdepth(nip.image(
                    stack_meanh1), 'float16', imin=None, imax=None, inorm=False, hascolor=True))
            save_name = 'mean_cla_' + fill_zeros(cla, fl_iter)
            nip.imsave(stack_meanh1, save_path + save_name,
                       form='tif', BitDepth='auto')

    # calculate global mean
    stack_meanh = np.squeeze(np.array(stack_meanh))
    if fl_iter > 1:
        stack_mean = np.mean(stack_meanh, axis=0)
    else:
        stack_mean = stack_meanh
    stack_mean = nip.image(stack_mean)

    # save if wanted
    if not stack_mean.dtype == np.dtype('float16'):
        stack_mean = nip.image(limit_bitdepth(
            nip.image(stack_mean), 'float16', imin=None, imax=None, inorm=False, hascolor=True))
    if not save_path == '':
        if not mean_range == []:
            save_name = 'meanref_f{}-{}'.format(mean_range[0], mean_range[1]) if (
                mean_range[1]-mean_range[0] <= fl_len) else 'stack_mean'
        else:
            save_name = 'stack_mean'
        nip.imsave(stack_mean, save_path + save_name,
                   form='tif', BitDepth='auto')

    # clear load_path if necessary
    if clear_path:
        delete_files_in_path(load_path)

    return stack_mean


def uc2_preprocessing(load_path, save_path, binning=[2, 2], batch_size=50, preview=False, interleave=100, ROIs=[], channel=1, mean_ref=False, load_fn_proto='jpg', vid_param={}, proc_range=None, prec=10, inverse_intensity=False, delete_means=True, threshhold=[], use_shifts=True, check_filenames=False):
    '''
    UC2-preprocessing.
    if preview=True:
        > Takes every n-th image from a stack
        > selects 1 channel
        > BINS
        > stores results (Video + selected-channel) in pre-view folder
    else:

    '''
    # supporting definitions
    chan_dict = {0: 'red', 1: 'green', 2: 'blue'}
    name_metrics = ['max', 'min', 'mean', 'median', 'tenengrad']

    # parameters
    tbegin = time()
    tnow = datetime.strftime(datetime.now(), "%Y%m%d_%H%M%S")
    criteria = 'mean'

    # paths
    dir_test_existance(save_path)
    name_fullim = 'image_'
    name_roi = 'roi_'
    mean_path_pre = save_path + 'mean' + os.sep
    if 'vname' in vid_param:
        save_vid = save_path + vid_param['vname'] + \
            '-ORIG--BIN-{}x_{}y--{}fps--AllChan'.format(
                binning[0], binning[1], vid_param['vfps'])
        save_meas = save_vid + '-res_calculation.yaml'
    else:
        save_vid = save_path + 'BIN_'
        save_meas = save_path + 'res.yaml'
    logpref = 'preview-' if preview else 'preproc-'
    logger_filepath = save_path + logpref + 'log-' + tnow + '.uc2log'
    os.chdir(load_path)

    # set-Logger and add system parameters
    if not 'logger' in locals():
        logger_root, logger = add_logging(
            logger_filepath, start_logger='PREVIEWprocessor')
    logger.debug('Processing running on DEVICE = {}'.format(
        gethostname()))
    logger.debug(
        'Logger created and started. Saving to: {}'.format(logger_filepath))

    #  creating result containers
    if preview == True:
        res = {'image_number': [], 'image_filepath': [], 'data_load_path': load_path,
               'data_save_path': save_path, 'image_filename_list': [], 'date_eval_start': '', 'date_eval_end': '', 'save_vid': ''}
    else:
        res = {'interchannel_offsets': [], 'image_shifts': [], 'image_number': [], 'image_filepath': [], 'data_load_path': load_path,
               'data_save_path': save_path, 'image_skipped_filename': [], 'image_skipped_index': [], 'res_stf_basics': [], 't_times': [], 't_comments': [], 'image_filename_list': [], 'roi_shifts': [], 'roi_diff_var': [], 'image_shifts': [], 'image_diff_var': [], 'shift_list': [], 'date_eval_start': '', 'date_eval_end': '', 'save_vid': ''}
        for n in [name_fullim, name_roi]:
            for m in name_metrics:
                res[n + m] = []
    res['date_eval_start'] = tnow

    # Filenames and Filelist
    if check_filenames:
        tdelta, brename = rename_files(load_path, version=2)
        if brename:
            logger.debug('Renaming of files took {}s.'.format(tdelta))
        else:
            logger.debug('No renaming necessary.')
    logger.debug('Get Filelist for load_path={}. Results will be stored in save_path={}.'.format(
        load_path, save_path))
    fl = get_filelist(load_path=load_path, fn_proto=load_fn_proto)
    if preview:
        fl = fl[::interleave]
    elif delete_means:
        delete_files_in_path(mean_path_pre)
    if not proc_range == None:
        fl = fl[proc_range[0]:proc_range[1]]
    [fl_len, fl_iter, fl_lastiter] = get_batch_numbers(
        filelist=fl, batch_size=batch_size)  # fl[2500:2510]

    # do iterations over all files
    for cla in range(fl_iter):
        tstart = time()
        if cla > 0:
            tform = format_time(np.round(tend * (fl_iter-cla-1), 0))
            logger.debug(
                'Estimated time needed until processing is completed: {}'.format(tform))

        # get right iteration values
        ids = cla * batch_size
        ide = (ids + batch_size) if cla < (fl_iter -
                                           1) else (ids + fl_lastiter)
        if cla == fl_iter-1:
            batch_size = fl_lastiter
        # Fast read data-stack  -> format = [time,color,y,x]
        logger.debug('Load stack {} of {}.'.format(cla+1, fl_iter))
        data_stack, data_stack_rf = loadStackfast(
            file_list=fl[ids:ide], logger=logger.warning)
        data_stack_rf = [m+ids for m in data_stack_rf]
        #if preview == True:
            #logger.debug('Only work on {} channel'.format(chan_dict[channel]))
            #data_stack = data_stack[:, channel, :, :]
        res['image_number'] = res['image_number'] + data_stack_rf
        res['image_filename_list'] = res['image_filename_list'] + [fl[m]
                                                                   for m in data_stack_rf]

        # work on inverse as transmission image taken
        if inverse_intensity:
            data_stack = subtract_from_max(data_stack)

        # subtract min to take "readout offset" into account
        logger.debug('Subtract Minima.')
        data_stack = data_stack - np.min(data_stack, keepdims=True)

        # Do binning and set video-pixel-param
        if binning:
            logger.debug('Bin image-stack.')
            data_stack_dtype = data_stack.dtype
            data_stack = np.array(nip.resample(data_stack, create_value_on_dimpos(
                data_stack.ndim, axes=[-2, -1], scaling=[1.0/binning[0], 1.0/binning[1]]))) / (binning[0] * binning[1])
        if cla == 0:
            vid_param['vpixels'] = list(data_stack.shape[-2:])

        if preview:
            kl = []
            sellist = []
        else:
            # Calculate chosen metrics --> all channels
            logger.debug('Calculate Metrics for Stack and ROI.')
            if cla == 0:
                pred = []
            res, pred = uc2_preprocessing_metrics(
                data_stack, mean_ref=mean_ref, ROIs=ROIs, pred=pred, res=res, ids=ids, ide=ide, cla=cla, name_metrics=name_metrics, name_stacks=[name_fullim, name_roi])

            # get rid of empty-images --> only 1 channel
            logger.debug(
                'Refuse images by using criteria {}.'.format(criteria))
            data_stack, res, kl = uc2_preprocessing_refuseImages(
                data_stack, res, ids=ids, ide=ide, channel=channel, criteria=criteria)
            mean_path = mean_path_pre + \
                'mean_cla_' + fill_zeros(cla, fl_iter)

            # get shifts (previously calculated in uc2_proprocessing_metrics)
            shift_list, sellist = uc2_eval_shifts(
                res, kl=kl, cla=cla, ids=ids, ide=ide, channel=channel, threshhold=threshhold, logger=logger)
            res['shift_list'] = res['shift_list'] + \
                list(shift_list[np.newaxis])

        # store video
        logger.debug('Write images into video and single TIFF-files.')
        if not data_stack.dtype == np.dtype('uint8'):
            data_stack = nip.image(limit_bitdepth(
                data_stack, 'uint8', imin=None, imax=None, inorm=False, hascolor=True))
        for udi in range(len(data_stack)):
            out = True if (cla == 0 and udi == 0) else out
            out, vid_param, hasChannels, isstack = save2vid(
                data_stack[udi], save_file=save_vid, vid_param=vid_param, out=out)

        # shift and store 1 channel of stack
        data_stack = np.squeeze(data_stack[:, channel])
        nbr_shifts = []
        for udi in range(batch_size):
            if udi not in kl:
                if udi in sellist and use_shifts:
                    # shift-values can be used directly -> negative values mean "image has to be shifted back  towards bigger pixel-pos-values"
                    try:
                        data_stack[udi] = nip.shift2Dby(
                            data_stack[udi], shift_list[udi])
                        nbr_shifts.append(m)
                    except Exception as e:
                        logger.warning(e)
                        logger.warning(
                            'Skipped step {}of{}, because shift_list has no such entry. Shift_list='.format(udi, batch_size))
                        logger.warning(shift_list)
                try:
                    if not data_stack.dtype == np.dtype('uint8'):
                        data_stack[udi] = nip.image(limit_bitdepth(
                            data_stack[udi], 'uint8', imin=None, imax=None, inorm=False, hascolor=True))
                    nip.imsave(data_stack[udi], save_path + 'images' + os.sep +
                               res['image_filename_list'][ids+udi][:-4], form='tif', BitDepth='auto')
                except Exception as e:
                    logger.warning(
                        'Tried to access out of bound index {} of data_stack. Still continued safely.'.format(udi))
        logger.debug('Applied {} shifts.'.format(len(nbr_shifts)))
        # calculate mean of active & shifted stack and store --> only 1 channel
        mean_format = 'tif'
        if not preview:
            logger.debug(
                'Calculate mean of active stack and store into {}.'.format(mean_path + mean_format))
            ds_mean = np.array(np.mean(data_stack, axis=0), dtype=np.float16)
            nip.imsave(nip.image(ds_mean), mean_path,
                    form=mean_format, BitDepth='auto')
        tend = time() - tstart
        del data_stack
        logger.debug('Iteration {} took: {}s.'.format(
            cla+1, np.round(tend, 2)))
        logger.debug(
            '--- > Succesfully written stack {} of {}'.format(cla+1, fl_iter))
    save2vid_closecontainer(out)
    res['date_eval_end'] = datetime.strftime(datetime.now(), "%Y%m%d_%H%M%S")
    res['save_vid'] = save_vid
    with open(save_meas, 'w') as file:
        yaml.dump(res, file)
    logger.debug('<<<< FINISHED AFTER {} >>>>'.format(
        format_time(np.round(time() - tbegin))))
    return res


def uc2_processing(load_path, save_path, res_old=None, batch_size=50, stack_mean=None, vid_param=None, load_fn_proto='tif', channel=None, colorful=0, inverse_intensity=False, correction_method='mean', use_shifts=True, draw_frameProperties=False, pixelsize=0.17, pixelunit="um", only_convert_2video=False, proc_range=None):
    '''
    Final clean-up of data.
    '''
    # parameters
    tbegin = time()
    tnow = datetime.strftime(datetime.now(), "%Y%m%d_%H%M%S")

    # set backend -> standard is: 'TkAgg'
    if draw_frameProperties: 
        mpl.use('Agg')
    # paths
    save_vid = save_path + vid_param['vname'] + \
        '-processed-{}fps'.format(vid_param['vfps'])
    logger_filepath = save_path + 'processing-log-' + tnow + '.uc2log'
    os.chdir(load_path)
    save_path_images = save_path + 'images-proc' + os.sep
    save_meas = save_path_images + 'res-proc.yaml'
    check_path(save_path_images)

    # set-Logger and add system parameters
    if not 'logger' in locals():
        logger_root, logger = add_logging(
            logger_filepath, start_logger='LASTprocessor')
    logger.debug('Processing running on DEVICE = {}'.format(
        gethostname()))
    logger.debug(
        'Logger created and started. Saving to: {}'.format(logger_filepath))

    #  creating result containers
    res = {'data_load_path': load_path,
           'date_eval_start': '', 'date_eval_end': '', 'image_number': [], 'image_filename_list': []}
    res['date_eval_start'] = tnow
    logger.debug('Get Filelist for load_path={}. Results will be stored in save_path={}.'.format(
        load_path, save_path))

    logger.debug('Get Filelist for load_path={}. Results will be stored in save_path={}.'.format(
        load_path, save_path))
    fl = get_filelist(load_path=load_path, fn_proto=load_fn_proto)
    if not proc_range == None:
        fl = fl[proc_range[0]:proc_range[1]]
    [fl_len, fl_iter, fl_lastiter] = get_batch_numbers(
        filelist=fl, batch_size=batch_size)

    # Parameters
    global_max = np.max(np.array(res_old['image_max'])[:, 1])
    norm_factor1 = 255/global_max
    if not only_convert_2video and use_shifts:
        if len(res_old['shift_list']) == 0:
            shifts_max = [0, 0]
        else:
            if not type(res_old['shift_list']) == np.ndarray:
                if len(res_old['shift_list']) == 1:
                    res_help = res_old['shift_list'][0]
                    shifts_max = np.array(np.round(np.max(np.abs(res_help),axis=0)), dtype=np.uint16)
                else:
                    res_help = np.array(res_old['shift_list'][:-1])
                    res_helpr = res_old['shift_list'][-1]
                    shifts_maxh = np.max(np.abs(res_help),axis=(0,1))
                    shifts_maxhr = np.max(np.abs(res_helpr),axis=0)
                    shifts_max = np.array(np.round(np.max(np.vstack((shifts_maxh,shifts_maxhr)),axis=0)),dtype=np.uint16)
            else: 
                shifts_max = np.array(np.round(np.max(np.abs(res_old['shift_list']), axis=((0, 1)))), dtype=np.uint16)
            if (shifts_max == [0, 0]).all():
                shifts_max = [4, 4]
    else:
        shifts_max = [0,0]

    # do iteration
    for cla in range(fl_iter):
        tstart = time()
        if cla > 0:
            tform = format_time(np.round(tend * (fl_iter-cla), 0))
            logger.debug(
                'Estimated time needed until processing is completed: {}'.format(tform))

        # get right iteration values
        ids = cla * batch_size
        ide = (ids + batch_size) if cla < (fl_iter -
                                           1) else (ids + fl_lastiter)
        if cla == fl_iter-1:
            batch_size = fl_lastiter
        # Fast read data-stack  -> format = [time,color,y,x]
        logger.debug('Load stack {} of {}.'.format(cla+1, fl_iter))
        data_stack, data_stack_rf = loadStackfast(
            file_list=fl[ids:ide], logger=logger.warning, colorful=0)
        data_stack_rf = [m+ids for m in data_stack_rf]
        res['image_number'] = res['image_number'] + data_stack_rf
        res['image_filename_list'] = res['image_filename_list'] + [fl[m]
                                                                   for m in data_stack_rf]

        if not only_convert_2video:
            # small error in divison/correction, but avoids division by zero problems
            if stack_mean.min() < 1:
                delta = stack_mean.min()
                stack_mean += (1-delta)

            # correct by mean and normalize to stack-full range -> TODO: not fully implemented
            if correction_method == 'max':
                corr_factor = data_stack.max(axis=(-2, -1))
                data_stack = (data_stack / stack_mean[np.newaxis])
                data_stack = data_stack * dsm[:, np.newaxis, np.newaxis]/np.max(
                    data_stack, axis=(-2, -1))[:, np.newaxis, np.newaxis]  # *norm_factor1
            elif correction_method == 'mean':
                data_stack = (data_stack / stack_mean[np.newaxis])
                # corr_factor = np.iinfo(np.uint8).max / data_stack.mean()
                corr_factor = 100
                data_stack = data_stack / data_stack.mean(
                    (-2, -1))[:, np.newaxis, np.newaxis] * corr_factor
                data_stack[data_stack > np.iinfo(
                    np.uint8).max] = np.iinfo(np.uint8).max
                if inverse_intensity:
                    data_stack = np.iinfo(np.uint8).max - data_stack
            else:
                pass
            # crop image
            data_stack = data_stack[:, shifts_max[0]:data_stack.shape[1] -
                                    shifts_max[0], shifts_max[1]:data_stack.shape[2]-shifts_max[1]]

            # save images
            data_stack = nip.image(data_stack)
            logger.debug('Store images in TIFF-files.')
            if not data_stack.dtype == np.dtype('uint8'):  # float16
                data_stack = nip.image(limit_bitdepth(
                    data_stack, 'uint8', imin=None, imax=None, inorm=False, hascolor=True))
            for udi in range(len(data_stack)):
                nip.imsave(data_stack[udi], save_path_images +
                        res['image_filename_list'][ids+udi][:-4], form='tif', BitDepth='auto')
        
        # set video dimensions
        if cla == 0:
            vid_param['vpixels'] = list(data_stack.shape[-2:])
        
        # store video
        logger.debug('Create Video')
        if not data_stack.dtype == np.dtype('uint8'):
            data_stack = limit_bitdepth(
                data_stack, 'uint8', imin=None, imax=None, inorm=False, hascolor=True)
        data_stack = nip.image(
            np.repeat(data_stack[:, np.newaxis, :, :], axis=1, repeats=3))
        for udi in range(len(data_stack)):
            out = True if (cla == 0 and udi == 0) else out
            if draw_frameProperties:
                data_stack[udi] = label_image(im=data_stack[udi],nbr=ids+udi,nbr2Time=[0,0,1,0,0],pixelsize=pixelsize, logger=logger)
            out, vid_param, hasChannels, isstack = save2vid(
                data_stack[udi], save_file=save_vid, vid_param=vid_param, out=out)
        tend = time() - tstart
        del data_stack
        logger.debug('Iteration {} took: {}s.'.format(
            cla+1, np.round(tend, 2)))
        logger.debug(
            '--- > Succesfully written stack {} of {}'.format(cla+1, fl_iter))
    save2vid_closecontainer(out)
    res['date_eval_end'] = datetime.strftime(datetime.now(), "%Y%m%d_%H%M%S")
    res['save_vid'] = save_vid
    with open(save_meas, 'w') as file:
        yaml.dump(res, file)
    logger.debug('<<<< FINISHED AFTER {} >>>>'.format(
        format_time(np.round(time() - tbegin))))
    return res
