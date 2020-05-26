'''
    Autofocus of UC2-GUI.
'''
# %% imports

# own
import fluidiscopeGlobVar as fg
import fluidiscopeToolbox as toolbox

# general imports
import unipath as uni
from datetime import datetime
from os import listdir
from glob import glob
from time import sleep
import logging

# math
import numpy as np
#import scipy.fftpack as ftp
#from scipy.optimize import curve_fit
#import matplotlib.pyplot as plt
#import cv2
from PIL import Image


if not fg.my_dev_flag:
    from picamera.array import PiRGBArray
else:
    import imageio as imo

# %% parameters and pre starts
logger = logging.getLogger('UC2_Autofocus')

#
# %%
# ----------------------------------- #
# @       interface toolbox         @ #
# ----------------------------------- #


def autofocus_callback(self, instance, *rargs):
    '''
        Tests whether autofocus is already running or anything else is blocking. If not: blocks all measurements (and further autofocus-calls) and resets autofocus-count if scheduled.
        To block running autofocus, click "AF now" as implemented in Toolbox.run_autofocus-function.
    '''
    # skip if AF already running
    if fg.config['experiment']['autofocus_busy']:
        pass
    else:
        # wait 1s before checking again
        while fg.config['experiment']['imaging_active']:
            sleep(1)
        fg.config['experiment']['autofocus_busy'] = True
        autofocus_routine(self)
        fg.config['experiment']['is_autofocus_busy'] = False
#
#

        # %%
        # ----------------------------------- #
        # @       algorithm toolbox          @ #
        # ----------------------------------- #


def autofocus_routine(self):
    '''
    Prepares parameters for scanning, sets everything up and calls scanning and calculation routines. 
    Note:
        > scan_range: half of the total (symmetric) scanning distance
    '''

    # generate image name
    image_name_template = autofocus_imagename_gen()

    # set correct number of iteration
    fg.config['experiment']['autofocus_num'] = 1 if fg.config['experiment']['autofocus_new'] else fg.config['experiment']['autofocus_num'] + 1

    # set parameters
    scan_range_coarse = fg.config['autofocus']['step_dist_coarse'] * fg.config['autofocus']['steps_coarse']
    scan_range_fine = fg.config['autofocus']['step_dist_fine'] * fg.config['autofocus']['steps_fine']
    pos_start = fg.config['motor']['calibration_z_pos']
    pos_max = fg.config['motor']['calibration_z_max']
    pos_min = fg.config['motor']['calibration_z_min']
    smethod = fg.config['autofocus']['technique']
    max_steps = fg.config['autofocus']['max_steps']

    # start video-stream of camera (to avoid re-init and long capture times)
    while True:
        # implement here
        break

    # init camera and allow for warmup
    camera = autofocus_setupCamera()
    rawCapture = PiRGBArray(camera, fg.config['autofocus']['resolution'])
    time.sleep(0.1)

    # Coarse scan -> get coarse-sharpness measures + new position of motor
    sharpness_coarse, pos_coarse = autofocus_scan(self, names=image_name_template, rawCapture=rawCapture, smethod=smethod, scan_range=scan_range_coarse, pos_start=pos_start, pos_min=pos_min, pos_max=pos_max, max_steps=max_steps)

    # Fit Gauss to graph and find new position of highest sharpness
    pos_optimum_coarse = find_optimum(sharpness_coarse, smethod)
    step_2opt_coarse = get_distvec(pos_coarse, pos_optimum_coarse)

    # move to new center with z motor
    toolbox.move_motor(None, 2, motor_stepsize=step_2opt_coarse)

    # fine scan around new position ->
    sharpness_fine, pos_fine = autofocus_scan(self, names=image_name_template, rawCapture=rawCapture, smethod=smethod, scan_range=scan_range_fine, pos_start=pos_optimum_coarse, pos_min=pos_min, pos_max=pos_max, max_steps=max_steps)

    # Fit Gauss to graph and find new position of highest sharpness
    pos_optimum_fine = find_optimum(sharpness_fine, smethod)
    step_2opt_fine = get_distvec(pos_fine, pos_optimum_coarse)

    # move to new center with z motor
    toolbox.move_motor(None, 2, motor_stepsize=step_2opt_coarse)

    # done
    return True


def get_distvec(a, b):
    '''
    Calculates signed distance two positions, where direction points from a to b. 
    '''
    return b - a


def autofocus_scan(self, names='nonamegiven', rawCapture, smethod, scan_range, pos_start, pos_min, pos_max, max_steps):
    '''
    Implements modules of how to scan through the object and how to use/ check for backlash!

    :scan_methods:      0=slow Filter-based, 1=fast Filter-based, 2=fast stream-size reading, 3=simulation

    TODO: 
        1) provide iteration limit NIter
    '''
    logger.debug("Autofocus ---> Scanning.")

    # set parameters and variables
    found_focus = False

    tim = []
    tproc = []
    sharpness = []
    ttotal = time.time()
    timstart = time.time()

    m = 0
    # faster way to acquire images and especially ensure same illumination properties etc per image as opposed to long-warm ups for single captures
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):

        # get raw numpy-array of shape [Y,X,Channel]
        image = frame.array
        tim.append(time.time() - timstart)

        # calculate sharpness measure
        tprocstart = time.time()
        if smethod == 0:
            sharpness.append(diff_tenengrad(np.reshape(image, [image.shape[-1], image.shape[-2], image.shape[-3]])))
        elif
        tproc.append(time.time() - tprocstart)

        # clear the stream in preparation for the next frame
        timstart = time.time()
        rawCapture.truncate(0)

        # set counter
        m += 1
        if m >= max_steps:
            break

    # TODO: update autofocus GUI-feedback
    # autofocus_display_update()

    # (slow) sharpness-Filter based method

        # get range
        scan_range = autofocus_getRange()

        #
        fine_steps_size = autofocus_getSteps(fine_range, fg.config['motor']['steps_fine'], step_method=0)

        image_ref, imqual_ref = autofocus_take_image(self, image_name_template=names, method=method)  # ==1.
        upd_val = 100 / (fine_steps * iter_max)

        while not (found_focus or myc >= iter_max or fine_range == 0):
            autofocus_move_motor(-fine_range + scan_offset)
            _, imqualh = autofocus_take_image(
                self, image_name_template=names, method=method)
            imqual_zpos, imqual_stack = autofocus_update_stacks(
                imqual_zpos, imqual_stack, imqualh)
            for myd in range(1, fine_steps):
                logger.debug("Autofocus-05b- autofocus_scan- step {} / {} in routine {} / {}.".format(
                    myd, fine_steps, myc, iter_max))
                autofocus_move_motor(fine_steps_size)
                _, imqualh = autofocus_take_image(
                    self, image_name_template=names, method=method)
                if myd == fine_steps / 2:  # information gain not yet used in code -> later: use to correct for backlash
                    refcomp_res = autofocus_compare_refs(image_ref, _)
                imqual_zpos, imqual_stack = autofocus_update_stacks(
                    imqual_zpos, imqual_stack, imqualh)
                autofocus_display_update(
                    self, upd_val, myd, fine_steps, myc, iter_max)
            imqual_max_zpos, imqual_max_val, imqual_fit_maxAmplitude, imqual_fit_centerZpos, found_focus = find_focus(
                imqual_zpos, imqual_stack)
            # move to max position
            autofocus_move_motor(imqual_fit_centerZpos -
                                 fg.config['motor']['calibration_z_pos'])
        autofocus_update_dict(found_focus, method,
                              fine_range, fine_steps, fine_steps_size)
    elif fg.config['autofocus']['scan_method'] == 1:
        # (fast) sharpness Filter-based
        pass
    elif fg.config['autofocus']['scan_method'] == 2:
        # (fast) byte-stream reading based
        pass
    elif fg.config['autofocus']['scan_method'] == 3:
        # simulates sharpness stack and tests performance
        pass
    else:
        logger.debug(
            "Not implemented method for Autofocus chosen. Hence: Idly waiting.")


def autofocus_update_dict(found_focus, method, fine_range, fine_steps, fine_steps_size):
    fg.config['autofocus']['success'] = found_focus
    fg.config['autofocus']['method'] = method
    fg.config['autofocus']['fine_range'] = fine_range
    fg.config['autofocus']['fine_steps'] = fine_steps
    fg.config['autofocus']['fine_steps_size'] = fine_steps_size


def autofocus_compare_refs(self, image_ref, _):
    # correlate
    # roughly same?
    pass


def autofocus_update_stacks(imqual_zpos, imqual_stack, imqualh):
    imqual_zpos = [imqual_zpos, fg.config['motor']['calibration_z_pos']]
    imqual_stack = [imqual_stack, imqualh]
    return imqual_zpos, imqual_stack


def autofocus_move_motor(stepsize):
    wait_time = fg.config['motor']['standard_move_time_z'] * \
        stepsize / fg.config['motor']['standard_move_dist_z']
    fg.motors.send("DRVZ", stepsize)
    fg.config['motor']['calibration_z_pos'] += stepsize
    # wait for movement to finish
    sleep(wait_time)


def autofocus_display_update(self, upd_val, myd, fine_steps, myc, iter_max, *largs):
    if (self.ids['pb_autofocus'].value < 100):
        # update toolbar
        self.ids['pb_autofocus'].value += upd_val
        logger.debug("Updated autofocus progressbar to {}".format(
            self.ids['pb_autofocus'].value))
        # update message-display
        msg = "Autofocus: Step {}/{} in iteration {}/{}.".format(
            myd, fine_steps, myc, iter_max)
        self.ids['lbl_warning'].text = msg
        self.ids['user_notify_expt'].text = msg
    else:
        self.ids['pb_autofocus'].value = 0
        self.ids['lbl_warning'].text = ""
        self.ids['user_notify_expt'].text = ""


def autofocus_getRange(srange, pos_start, pos_min, pos_max):
    '''
    Calculates absolut range for reference printing with respect to the motor position, movement and limits. 

    :PARAM:
    =======
    :scanrange:     2 * of the scanning range that will symmetrically be stepped about
    :pos_start:      start-position of scan (=center)
    :

    '''

    if scanrange == 0:
        # calculate maximum symmetric distance to borders from actual position
        scan_limits = [abs(get_distvec(pos_start, pos_min)), abs(get_distvec(pos_start, pos_max))]

        # select smaller distance
        scanrange = scan_limits[1] if (scan_limits[0] >
                                       scan_limits[1]) else scan_limits[0]
        scanrange = np.array(scanrange, dtype=int) // 2
    else:
        # check limits to not go over boundaries for motors
        if (pos_start + scanrange > pos_max):
            scanrange = pos_max - pos_start
        if (pos_start - scanrange < pos_min):
            scanrange = abs(get_distvec(pos_start, pos_min))
    return scanrange


def autofocus_getSteps(scan_range, steps, step_method=0):
    if step_method == 0:
        scan_steps = scan_range / steps
    return scan_steps


def autofocus_curveFit(imqual_zpos, imqual_stack, p0, type):
    xr = [np.min(imqual_zpos), np.max(imqual_zpos), len(imqual_zpos)]
    if type == 0:
        if 0:
            coeff, var_matrix = curve_fit(
                fitf_gauss, imqual_zpos, imqual_stack, p0=p0)  # coeff=[A, mu, sigma]
        else:
            coeff = p0
        a_fit = fitf_gauss(imqual_zpos, *coeff)  # Get the fitted curve
        xn = np.linspace(xr[0], xr[1], num=xr[2])
        xrss = np.linspace(xr[0], xr[1], num=xr[2] * 4)
        yn = fitf_gauss(xn, *coeff)  # Get the fitted curve
        yrss = fitf_gauss(xrss, *coeff)  # Get the fitted curve
    elif type == 1:
        # using numpy and lstsq
        # coeff, var_matrix = np.linalg.lstsq(fitf_gauss, imqual_zpos, imqual_stack, p0=p0)  # coeff=[A, mu, sigma]
        #a = np.vstack([imqual_zpos, np.ones(len(imqual_zpos))]).T
        a = np.random.randn(100)
        fitp = np.polyfit(imqual_zpos, fitf_gauss, 2)
        xn = np.linspace(xr[0], xr[1], num=xr[2])
        xrss = np.linspace(xr[0], xr[1], num=xr[2] * 4)
        yn = np.polyval(fitp, xn)
        yn = np.polyval(fitp, xrss)
        coeff = [fitp[0], np.argmax(yn), fitp[2]]  # max-pos
    else:
        pass
    # format for gauss (type=0): A,mu,sigma
    return coeff, xr, xn, xrss, yn, yrss


def find_focus(names, method, imqual_zpos, imqual_stack, myc=0, max_iter=2):
    xunit = 'pix'
    method = 'Tenengrad'
    # test gaussian -> from: https://stackoverflow.com/a/11507723
    from timeit import default_timer as timer
    tstart = timer()
    # -------
    try:
        p0 = [1., 0., 1.]
        # coeff, var_matrix = curve_fit(fitf_gauss, bin_centres, hist, p0=p0)
        coeff, xr, xn, xrss, a_fit, a_fit_rss = autofocus_curveFit(
            imqual_zpos, imqual_stack, p0, 1)
        if all(coeff == p0):
            p0l = [1., 0.]
            #coeff, var_matrixl = curve_fit(fitf_lin, imqual_zpos, imqual_stack, p0=p0l)
            # a_fitl = fitf_lin(imqual_zpos, *coeff)  # Get the fitted curve
            #plt.plot(imqual_zpos, a_fitl, label='Lin. Fitted data')
            succs = False
        else:
            succs = True
        #plt.plot(imqual_zpos, imqual_stack, label='Meas.Data')
        #plt.plot(imqual_zpos, a_fit, label='Gauss-Fit.')
        #plt.plot(xrss, a_fit_rss, label='supersampled Gauss-Fit.')
        #plt.xlabel('Absolut Motor Position in [{0}]'.format(xunit))
        #plt.ylabel('Sharpness Value normed StartingPos in [a.U.]')
        #plt.title('Autofocus-Results using\nmetric={0} at step={1}/{2}'.format(method, myc, max_iter))
        # plt.legend()
        # plt.show()
        #plt.savefig(names+'Autofocus-{0}-myc_{1}'.format(names, myc))
    except RuntimeError as err:
        logger.debug("intercepted")
        logger.debug(err)
        # try linear fit again
        p0l = [1., 0.]
        coeff, var_matrixl = curve_fit(
            fitf_lin, imqual_zpos, imqual_stack, p0=p0l)
        succs = False
        # try modifications on input data-set
        # but cut autofocus for now
    tend = timer()
    # save out dictionary:
    autofocus_res = {'z_Pos': imqual_zpos,
                     'sharpness': imqual_stack,
                     'iteration': myc,
                     'iteration_limit': max_iter,
                     'fine_steps': xr[2],
                     'fine_steps_dist': xr[1] - xr[0],
                     'backlash': fg.config['autofocus_properties']['backlash'],
                     'im_taken_before': fg.config['experiment']['images_taken'],
                     'total_time': tstart - tend,
                     'A,mu,sigma': coeff,
                     'success': succs,
                     }
    np.save('{}-iter_{}-results.npy'.format(myc, names), autofocus_res)
    #d2 = np.load('autofocus_res-20190327_0917.npy')
    return imqual_zpos[np.argmax(imqual_stack)], np.max(imqual_stack), coeff[0], coeff[1], succs
#
#
# %%
# ----------------------------------- #
# @       function toolbox          @ #
# ----------------------------------- #


def imqual_metric(image, method='Tenengrad'):
    if method == 'Tenengrad':
        offsets = [2, image.shape[0], 2, image.shape[1]]
        # calculate shifted subsets of images
        I_xp1_ym1 = image[offsets[0] - 2:offsets[1] - 2, offsets[2]:offsets[3]]
        I_xp1_y0 = image[offsets[0] - 1:offsets[1] - 1, offsets[2]:offsets[3]]
        I_xp1_yp1 = image[offsets[0]:offsets[1], offsets[2]:offsets[3]]
        I_x0_ym1 = image[offsets[0] - 2:offsets[1] -
                         2, offsets[2] - 1:offsets[3] - 1]
        I_x0_y0 = image[offsets[0] - 1:offsets[1] -
                        1, offsets[2] - 1:offsets[3] - 1]
        I_x0_yp1 = image[offsets[0]:offsets[1], offsets[2] - 1:offsets[3] - 1]
        I_xm1_ym1 = image[offsets[0] - 2:offsets[1] - 2, offsets[2] - 2:offsets[3] - 2]
        I_xm1_y0 = image[offsets[0] - 1:offsets[1] -
                         1, offsets[2] - 2:offsets[3] - 2]
        I_xm1_yp1 = image[offsets[0]:offsets[1], offsets[2] - 2:offsets[3] - 2]
        # sobel-filter to implement crossed derivatives
        Sobel_h = I_xp1_ym1 + 2 * I_xp1_y0 + I_xp1_yp1 - \
            I_xm1_ym1 - 2 * I_xm1_y0 - I_xm1_yp1
        Sobel_v = I_xm1_yp1 + 2 * I_x0_yp1 + I_xp1_yp1 - \
            I_xm1_ym1 - 2 * I_x0_ym1 - I_xp1_ym1
        # normalize image
        imqual_result = 1.0 / np.prod(np.shape(I_xp1_ym1)) * \
            np.sum(np.square(Sobel_h) + np.square(Sobel_v), axis=(0, 1))
    else:
        pass
    return imqual_result


def read_stack(file_names):
    rstack = np.array(imo.imread(file_names[0]))[np.newaxis]
    for myc in range(1, len(file_names)):
        rstack = np.concatenate(
            (rstack, np.array(imo.imread(file_names[myc]))[np.newaxis]), axis=0)
    return rstack


def fitf_gauss(x, *parameters):
    A, mu, sigma = parameters
    return A * np.exp(-(x - mu)**2 / (2. * sigma**2))


def fitf_lin(x, *parameters):
    m, b = parameters
    return m * x + b


def get_slope(x, y):
    # determine the slope of the current focus values
    # x is given by the steps
    # y is given by the measured contrast
    # x = np.array([0, 1, , 3])
    # y = np.array([-1, 0.2, 0.9, 2.1])
    A = np.vstack([x, np.ones(len(x))]).T
    m, c = np.linalg.lstsq(A, y)[0]
    logger.debug(m, c)
    return m

#


def gauss_residual(updated_parameter, x, data):
    resid = fitf_gauss(x, updated_parameter) - data
    res = np.sum(np.square(resid))
    return res


def residual_derivative(updated_data, static_data, data):
    pass


def autofocus_imagename_gen():
    now = str(datetime.now().strftime("%Y%m%d_%H%M%S"))
    image_name_template = '{}-Autofocus_it_{}-'.format(
        now, fg.config['experiment']['autofocus_num'])
    return image_name_template


def autofocus_take_image(self, image_name_template, method):
    imvar = 0
    mythresh = 0.005  # has to be adjusted again
    myc = 0
    eps = 0.00001
    image_stack = []
    imvar_stack = []
    # neutralize with prior image to have more averaging? -> NOT IMPLEMENTED
    # take again if variance is too small until limit
    while (imvar < mythresh or myc == 4):
        image = toolbox.take_image(self, 'autofocus', image_name_template)
        # normalize image to reside in [0,1]
        help_image = image - np.min(image)
        help_image[help_image == 0] = eps
        help_image /= np.max(help_image)
        imvar = np.var(help_image)
        myc += 1
    image_stack = [image_stack, image, ]
    imvar_stack = [imvar_stack, imvar, ]
    # calc_image_quality -> TENENGRAD for now
    logger.debug("autofocus_take_image -> myc={}".format(myc))
    if myc == 4:
        # note: stack was created as list of arrays! -> so: access array
        image = image_stack[np.argmax(imvar_stack)]
    imqual_res = imqual_metric(image, method=method)
    return image, imqual_res


def simulate_data_stack():
    open_dir = 'C:/Users/rene/Documents/Programming/matlab/Fluidi/swen/data/noise-data-01/'
    open_file = glob(open_dir + '*.tif')
    data_stack = read_stack(open_file)
    imqual_res = [imqual_metric(data_stack[0, :, :], method='Tenengrad')]
    for myc in range(1, data_stack.shape[0]):
        imqual_res = np.concatenate((imqual_res, [imqual_metric(
            data_stack[myc, :, :], method='Tenengrad')]), axis=0)
    step_sizes = np.arange(41) / 8.0
    return step_sizes, imqual_res
