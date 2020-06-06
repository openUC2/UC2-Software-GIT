'''
    Autofocus of UC2-GUI.
'''
# %% imports

# own
import fluidiscopeGlobVar as fg
import fluidiscopeToolbox as toolbox
import fluidiscopeIO as fio
from fluidiscopeLogging import logger_createChild

# general imports
import unipath as uni
from datetime import datetime
from os import listdir
from glob import glob
from time import sleep
import logging
import tifffile as tif
# math
import numpy as np
from PIL import Image


if not fg.my_dev_flag:
    from picamera.array import PiRGBArray
else:
    import imageio as imo

# %% parameters and pre starts
logger = logger_createChild('autofocus','UC2')
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
# @            Parameters           @ #
# ----------------------------------- #

def get_camstats(camera,printme=False):
    '''
    Retrieves all available camera-properties and stores them into a dictionary.

    :PARAMS:
    ========
    :camera:    pointing to PiCamera() instance
    :printme:   Whether the dict should be printed nicely

    :OUTPUTS:
    =========
    :camProp:   (DICT) with available camera properties

    '''
    # retrieve all existing get_functions
    all_getter =  [s for s in dir(camera) if "_get_" in s]
    camProp = {}
    for m in all_getter:
        try: 
            camProp[m[5:]] = eval('camera.' + m + '()')
        except:
            pass

    if printme:
        print("\nlen(all_getter)={}\nlen(camProp)={}\n".format(len(all_getter),len(camProp)))
        for m in camProp:
            print(m + " = \t\t{}".format(camProp[m]))

    return camProp

def get_camstatsSorted(camStats, sel=None, just_subset=False, printme=False):
    '''
    Sorts resulting measurements so it can be used as a table.
    if just_subset==True, returns a list, else a dictionary.

    Example: 
    sel=['awb_gains','iso','shutter_speed','analog_gain']
    get_camstatsSorted(camStats,sel)

    '''
    if just_subset and sel is not None:
        camStats_sorted = [[[s,a[s]] for s in a if s in sel] for a in camStats]
    else: 
    
        # fill selection to all entries if not chosen
        sel = [m for m in camStats[0]] if sel is None else sel
        camStats_sorted = {}

        # traverse time-points and collect datasets
        for m in sel:
            camStats_sorted[m] = [a[m] for a in camStats]
    
        # print formatted
        if printme:
            for m in camStats_sorted:
                print(m+"=\t {}".format(camStats_sorted[m]))

    return camStats_sorted

def autofocus_setupCAM(camStats):
    '''
        Prepares camera. 
        Make sure that Autofocus-config entries are updated before running this. 
        Does not do anything if global camera-properties are already active OR if Autofocus already configured camera.
    '''
    # record existing configuration
    camStats.append(get_camstats(fg.camera,printme=False))

    # if parameters not globally fixed AND not yet fixed by Autofocus-routine
    if not fg.config['autofocus']['use_global_camProp'] and not fg.config['autofocus']['camProp_defined']:

        # set basic modes 
        fg.camera.image_denoise = fg.config['cam_af']['image_denoise']
        fg.camera.iso = fg.config['cam_af']['iso']
        fg.camera.meter_mode = fg.config['cam_af']['meter_mode']   
        fg.camera.resolution = fg.config['cam_af']['resolution']
        fg.camera.sensor_mode = fg.config['autofocus']['sensor_mode']
        fg.camera.video_denoise = fg.config['cam_af']['video_denoise']
        fg.camera.video_stabilization = fg.config['cam_af']['video_stabilization']     
        
        
        # wait for camera to settle on new setup
        sleep(0.5)

        # prepare Buffer
        rawCapture = PiRGBArray(fg.camera, fg.config['autofocus']['resolution'])
        
        # take an image to use auto-functions for parameter estimation
        fg.camera.capture(rawCapture, format="bgr", use_video_port=True, bayer=False)
        camStats.append(get_camstats(fg.camera,printme=False))

        # refresh autofocus-dictionary
        fg.config['cam_af']['analog_gain'] = camStats[-1]['analog_gain']
        fg.config['cam_af']['awb_gains'] = camStats[-1]['awb_gains']
        fg.config['cam_af']['digital_gain'] = camStats[-1]['digital_gain']
        fg.config['cam_af']['framerate'] = camStats[-1]['framerate']
        fg.config['cam_af']['shutter_speed'] = camStats[-1]['shutter_speed']
        
        # overwrite camera parameters AND (therwith) FIX 
        fg.camera.awb_gains = fg.config['cam_af']['awb_gains'] 
        fg.camera.awb_mode = fg.config['cam_af']['awb_mode']
        fg.camera.exposure_compensation = fg.config['cam_af']['exposure_compensation']
        fg.camera.exposure_mode = fg.config['cam_af']['exposure_mode']
        fg.camera.framerate = fg.config['cam_af']['framerate']
        fg.camera.shutter_speed = fg.config['cam_af']['shutter_speed']

        # set True to use setting for future 
        fg.config['autofocus']['camProp_defined'] = 1
          

    return camStats




# %%
# ----------------------------------- #
# @           algorithms            @ #
# ----------------------------------- #


def autofocus_routine(self, camStats=None):
    '''
    Prepares parameters for scanning, sets everything up and calls scanning and calculation routines. 
    Note:
        > scan_range: half of the total (symmetric) scanning distance
    '''
    # turn on light (so that Photon-flux can already be passively evaluated by Sensor)
    fio.update_matrix(self, ignore_NA=True, sync_only=False)
    sleep(0.2)

    # get parameters
    image_name_template, steps_coarse_dist, steps_coarse_nbr, steps_fine_dist, steps_fine_nbr, pos_start, pos_max, pos_min, smethod, max_steps, imres, motor, save_im, NIterTotal = autofocus_getParameters()


    # sanity-check Scanrange
    scan_range = autofocus_getRange(scanrange, pos_start, pos_min, pos_max)

    # initialize camera-properties
    camStats = [] if camStats is None else camStats
    camStats = autofocus_setupCAM(camStats)

    # Coarse scan -> get coarse-sharpness measures + new position of motor
    sharpness_coarse, poslist, tim, tproc, ttotal = autofocus_scan(self, names=image_name_template, rawCapture=rawCapture, smethod=smethod, pos_start=pos_start, pos_min=pos_min, pos_max=pos_max, max_steps=max_steps, steps_nbr=steps_coarse_nbr, steps_dist=steps_coarse_dist, direction = 1, NIterTotal=NIterTotal,motor=motor, status='coarse', save_im=save_im, save_name=image_name_template)

    # Fit Gauss to graph and find new position of highest sharpness
    coarse_posOptimum, coarse_max, coarse_coeff, coarse_succs = autofocus_findOptimum(s=sharpness_coarse, offset=1, smethod=smethod, NIterTotal=NIterTotal, steps=steps_coarse_nbr , poslist=poslist, save_name=image_name_template, status='coarse', plotme=True, storeme=True)
    step_2opt_coarse = get_distvec(pos_coarse, coarse_posOptimum)

    # move to new center with z motor
    toolbox.move_motor(None, 2, motor_stepsize=step_2opt_coarse)
    
    if not fg.config['autofocus']['use_coarse_only']:

        # fine scan around new position ->
        sharpness_fine, pos_fine = autofocus_scan(self, names=image_name_template, rawCapture=rawCapture, smethod=smethod, scan_range=scan_range_fine, pos_start=pos_optimum_coarse, pos_min=pos_min, pos_max=pos_max, max_steps=max_steps, save_im=save_im)

        sharpness, poslist, tim, tproc, ttotal = autofocus_scan(self, names=image_name_template, rawCapture=rawCapture, smethod=smethod, pos_start=pos_start, pos_min=pos_min, pos_max=pos_max, max_steps=max_steps, steps_nbr=steps_coarse_nbr, steps_dist=steps_, direction = 1, NIterTotal=NIterTotal,motor=motor, status='coarse', save_im=save_im, save_name=image_name_template)

        # Fit Gauss to graph and find new position of highest sharpness
        fine_posOptimum, fine_max, fine_coeff, fine_succs = autofocus_findOptimum(s=sharpness_coarse, offset=1, smethod=smethod, NIterTotal=NIterTotal, steps=steps_coarse_nbr , poslist=poslist, save_name=image_name_template, status='fine', plotme=True, storeme=True)
        step_2opt_fine = get_distvec(pos_fine, pos_optimum_coarse)

        # move to new center with z motor AND clear LED-array
        toolbox.move_motor(None, 2, motor_stepsize=step_2opt_coarse)
    
    fg.ledarr.send("CLEAR")

    # done?
    return True


def get_distvec(a, b):
    '''
    Calculates signed distance two positions, where direction points from a to b. 
    '''
    return b - a



def autofocus_getParameters():
    '''
    Assignes variables to dict-entries for easier readability. 
    '''
    # generate image name
    image_name_template = autofocus_imagename_gen()

    # set correct number of iteration
    fg.config['experiment']['autofocus_num'] = 1 if fg.config['experiment']['autofocus_new'] else fg.config['experiment']['autofocus_num'] + 1

    # set parameters
    steps_coarse_dist = fg.config['autofocus']['step_dist_coarse']
    steps_coarse_nbr = fg.config['autofocus']['steps_coarse'] 
    steps_fine_dist = fg.config['autofocus']['step_dist_fine']
    steps_fine_nbr = fg.config['autofocus']['steps_fine']
    pos_start = fg.config['motor']['calibration_z_pos']
    pos_max = fg.config['motor']['calibration_z_max']
    pos_min = fg.config['motor']['calibration_z_min']
    smethod = fg.config['autofocus']['technique']
    max_steps = fg.config['autofocus']['max_steps'] 
    fg.config['autofocus']['resolution'] = fg.config['camera']['sensor_mode_size'][fg.config['autofocus']['sensor_mode']]
    imres = fg.config['autofocus']['resolution']
    motor = fg.config['autofocus']['motor']
    save_im = fg.config['autofocus']['save_images']
    NIterTotal = fg.config['autofocus']['scan_iterations']

    return image_name_template, steps_coarse_dist, steps_coarse_nbr, steps_fine_dist, steps_fine_nbr, pos_start, pos_max, pos_min, smethod, max_steps, imres, motor, save_im, NIterTotal

def autofocus_scan(self, names, rawCapture, smethod, pos_start, pos_min, pos_max, max_steps, steps_nbr, steps_dist, direction, NIterTotal, motor, status='coarse', save_im=False, save_name=None):
    '''
    Implements modules of how to scan through the object and how to use/ check for backlash!

    :scan_methods:      0=slow Filter-based (DEFAULT), 1=fast Filter-based, 2=fast stream-size reading, 3=simulation

    TODO: 
        1) provide iteration limit NIter
    '''
    logger.debug("Autofocus ---> {} - Scanning.".format(status))

    # set parameters and variables
    m = 0
    scan_range = steps_dist * steps_nbr
    poslist = [pos_start,]

    # prepare containers
    tim = []
    tproc = []
    sharpness = []
    timstart = time.time()
    ttotal = time.time()

    #image_ref, imqual_ref = autofocus_take_image(self, image_name_template=names, method=method)  # ==1.
    upd_val = 100 / ((steps_nbr+1)*NIterTotal)


    # faster way to acquire images and especially ensure same illumination properties etc per image as opposed to long-warm ups for single captures
    for n in range(NIterTotal):
        for frame in fg.camera.capture_continuous(rawCapture, format="rgb", use_video_port=True):

            # get raw numpy-array of shape [Y,X,Channel]
            image = frame.array
            tim.append(time.time() - timstart)
            sharpness, tproc = autofocus_getMeasure(image, sharpness, tproc)

            # if save
            if save_im:
                tif.imwrite(save_name + str(n)+ "_"+str(m) + '.tif', image, photometric='rgb')

            if m==0:
                # move motor to start
                step_2_start = get_distvec(pos_start, pos_start + direction* scan_range//2)
                wait_time = autofocus_move_motor(step_2_start,motor,wait_time=None)
                poslist.append(poslist[-1]+step_2_start)
            else:
                # move motor 1 step up
                wait_time = autofocus_move_motor(direction*steps_dist,motor,wait_time=wait_time)
                poslist.append(poslist[-1]+direction*steps_dist)

            # clear the stream in preparation for the next frame
            timstart = time.time()
            rawCapture.truncate(0)

            # update display
            autofocus_display_update(self, upd_val, m, steps_nbr, n, NIterTotal*(steps_nbr+1))

            # set counter
            m += 1
            if m > steps_nbr:
                break
        
        # iterate the stack inversely 
        m=1
        direction *= -1
    ttotal = time.time() - ttotal

    # done?
    return sharpness, poslist, tim, tproc, ttotal


def autofocus_getMeasure(im, sharpness, tproc):
    '''
    Calculates sharpness measure and returns value
    '''
    # calculate sharpness measure
    tprocstart = time.time()
    if fg.config['autofocus']['scan_method'] == 1:
        # (fast) sharpness Filter-based
        pass
    elif fg.config['autofocus']['scan_method'] == 2:
        # (fast) byte-stream reading based
        pass
    elif fg.config['autofocus']['scan_method'] == 3:
        # simulates sharpness stack and tests performance
        pass
    else:
        sharpness.append(diff_tenengrad(np.reshape(im, [im.shape[-1], im.shape[-2], im.shape[-3]])))    
    tproc.append(time.time() - tprocstart)

    return tproc, sharpness

def autofocus_update_dict(found_focus, method, fine_range, fine_steps, fine_steps_size):
    fg.config['experiment']['autofocus_success'] = found_focus
    fg.config['autofocus']['method'] = method
    fg.config['autofocus']['fine_range'] = fine_range
    fg.config['autofocus']['fine_steps'] = fine_steps
    fg.config['autofocus']['fine_steps_size'] = fine_steps_size

'''
def autofocus_compare_refs(self, image_ref, _):
    # correlate
    # roughly same?
    pass


def autofocus_update_stacks(imqual_zpos, imqual_stack, imqualh):
    imqual_zpos = [imqual_zpos, fg.config['motor']['calibration_z_pos']]
    imqual_stack = [imqual_stack, imqualh]
    return imqual_zpos, imqual_stack
'''

def autofocus_move_motor(stepsize,motor,wait_time=None):
    '''
    Moves motor accordingly. 
    '''
    
    # dict
    letter = ['x','y','z']
    name = ['DRVX','DRVY','DRVZ']

    # calculate proper waiting time
    if wait_time is None: 
        wait_time = fg.config['motor']['standard_move_time_'+letter[motor]] * \
            stepsize / fg.config['motor']['standard_move_dist_'+letter[motor]]

    # move and update config
    toolbox.move_motor(None, motor, motor_stepsize=stepsize)
    fg.config['motor']['calibration_'+letter[motor]+'_pos'] += stepsize
    
    # wait for movement to finish
    sleep(wait_time)

    return wait_time


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


def autofocus_getRange(scanrange, pos_start, pos_min, pos_max):
    '''
    Checks for boundary violations with respect to the motor position, movement and limits. Scanrange is interpreted as full-range AND calculation tests from actual pos as center-position with respect to both-sided limits.

    :PARAM:
    =======
    :scanrange:     2 * of the scanning range that will symmetrically be stepped about
    :pos_start:      start-position of scan (=center)

    '''

    if scanrange == 0:
        # calculate maximum symmetric distance to borders from actual position
        scan_limits = [abs(get_distvec(pos_start, pos_min)), abs(get_distvec(pos_start, pos_max))]

        # select smaller distance
        scanrange = scan_limits[1] if (scan_limits[0] >
                                       scan_limits[1]) else scan_limits[0]
        scanrange = np.array(scanrange, dtype=int) 
    else:
        # check limits to not go over boundaries for motors
        if (pos_start + scanrange//2 > pos_max):
            scanrange = pos_max - pos_start
        if (pos_start - scanrange//2 < pos_min):
            scanrange = abs(get_distvec(pos_start, pos_min))

    return scanrange


def autofocus_getSteps(scan_range, steps, step_method=0):
    if step_method == 0:
        scan_steps = scan_range / steps
    return scan_steps


def autofocus_plotOptSearch(x,y,yfit,xrss,yfit_rss,smethod,name_im,nbr_dir,nbr_iter):
    '''
    Plots fit for optimum search. 
    
    '''
    fig1 = plt.figure()
    plt.plot(x, y, label='Meas.Data')
    plt.plot(x, yfit, label='Gauss-Fit.')
    plt.plot(xrss, yfit_rss, label='supersampled Gauss-Fit.')
    plt.xlabel('Absolut Motor Position in [{0}]'.format(xunit))
    plt.ylabel('Sharpness Value normed StartingPos in [a.U.]')
    plt.title('Autofocus-Results using\nmetric={0} at step={1}/{2}'.format(smethod, myc, max_iter))
    plt.legend()
    plt.savefig(name_im+'_{}of{}.png'.format(nbr_dir,nbr_iter),dpi=300)


def autofocus_findOptimum(s, offset, smethod, NIterTotal, steps, poslist, save_name, status='coarse', plotme=True, storeme=True, ): 
    '''
    Calculates optimum position given input parameters.
    Structure of s=Sharpness_list: 
        s[0] = reference image
        s[1:steps] = 1st direction scan
        s[steps:2*steps] = 2nd direction scan etc for amount of NIterTotal 
    poslist only provided for printme-option to actually evaluate positions.
    '''
    xlabel = 'motor-Pos'
    ylabel = 'sharpness'

    for m in NIterTotal:
        ttotal = time.time()
        y = s[offset+m*steps:offset+(m+1)*steps]
        x = poslist[offset+m*steps:offset+(m+1)*steps]
        autofocus_curveFit(x,y,)

        try:
            p0 = [1., 0., 1.]
            coeff, xr, xn, xrss, yfit, yfit_rss = autofocus_curveFit(
                x, y, p0, 1)
            if all(coeff == p0):
                p0l = [1., 0.]
                succs = False
            else:
                succs = True

        except RuntimeError as err:
            logger.debug("intercepted")
            logger.debug(err)
            # try linear fit again
            p0l = [1., 0.]
            coeff, var_matrixl = curve_fit(
                fitf_lin, x, y, p0=p0l)
            succs = False

         # save out dictionary:
        if storeme:    
            autofocus_res = {'z_Pos': x,
                            'sharpness': y,
                            'iteration': m,
                            'iteration_limit': NIterTotal,
                            'steps_nbr': xr[2],
                            'steps_dist': xr[1] - xr[0],
                            'backlash': fg.config['autofocus_properties']['backlash'],
                            'im_taken_before': fg.config['experiment']['images_taken'],
                            'total_time': ttotal - time.time(),
                            'A,mu,sigma': coeff,
                            'success': succs,
                            }
            np.save(save_name + '_{}-{}_of_{}-results.npy'.format(status,m, NIterTotal), autofocus_res)
        if plotme:
            autofocus_plotOptSearch(x=x,y=y,yfit=yfit,xrss=xrss,yfit_rss=yfit_rss,smethod=smethod,name_im=save_name + '_{}_'.format(status),nbr_dir=m,nbr_iter=NIter)
    # results
    pos_max = xr[np.argmax(yfit)]
    max_val = np.max(yfit)

    # done?
    return pos_max, max_val, coeff, succs

def autofocus_curveFit(x, y, p0, type):
    '''
    Actually courve-fitting routine for finding the maximum-position of sharpness-calculations.
    Calculates a normal fitted and a sub-sampled fit.

    :PARAMS:
    ========
    :x:     (LIST) Scan-positions
    :y:     (LIST) calculated sharpness measures


    :OUTPUT:
    ========
    :coeff: (LIST) of calculated coefficients (depending on fitting function)
    :xr:    xrange-parameters from input list
    :xn:    x-positions used for fitting
    :xrss:  sub-sampled x-positions for fitting
    :yn:    y-fitted values
    :yrss:  sub-sampled y-fitted values

    '''

    xr = [np.min(x), np.max(x), len(x)]
    if type == 0:
        if 0:
            coeff, var_matrix = curve_fit(
                fitf_gauss, x, y, p0=p0)  # coeff=[A, mu, sigma]
        else:
            coeff = p0
        a_fit = fitf_gauss(x, *coeff)  # Get the fitted curve
        xn = np.linspace(xr[0], xr[1], num=xr[2])
        xrss = np.linspace(xr[0], xr[1], num=xr[2] * 4)
        yn = fitf_gauss(xn, *coeff)  # Get the fitted curve
        yrss = fitf_gauss(xrss, *coeff)  # Get the fitted curve
    elif type == 1:
        # using numpy and lstsq
        # coeff, var_matrix = np.linalg.lstsq(fitf_gauss, x, imqual_stack, p0=p0)  # coeff=[A, mu, sigma]
        #a = np.vstack([x, np.ones(len(x))]).T
        a = np.random.randn(100)
        fitp = np.polyfit(x, fitf_gauss, 2)
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


def read_stack(file_names):
    rstack = np.array(imo.imread(file_names[0]))[np.newaxis]
    for myc in range(1, len(file_names)):
        rstack = np.concatenate(
            (rstack, np.array(imo.imread(file_names[myc]))[np.newaxis]), axis=0)
    return rstack


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
