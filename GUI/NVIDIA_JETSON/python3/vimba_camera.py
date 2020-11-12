import copy
import cv2
import threading
import queue
import numpy as np
import os
import time 

from typing import Optional
from vimba import *

import fluidiscopeGlobVar as fg

FRAME_QUEUE_SIZE = 1
FRAME_HEIGHT = 1088
FRAME_WIDTH = 1456


WINDOW_START_FROM_LEFT = 80 #fg.config['imaging']['window'][0]
WINDOW_START_FROM_TOP = 80 # fg.config['imaging']['window'][1]
WINDOW_HEIGHT = 480 # fg.config['imaging']['window'][2]
WINDOW_WIDTH = 320 #  fg.config['imaging']['window'][3]
IMAGE_CAPTION = 'UC2-Livestream'


# Camera Settings
#CAM_GAIN = 20 # dB
T_EXPOSURE_MAX = 1e6 # µs => 1s
ExposureTime = 50e3

T_PERIODE = 0.5 # [s] - time between acquired frames


def add_camera_id(frame: Frame, cam_id: str) -> Frame:
    # Helper function inserting 'cam_id' into given frame. This function
    # manipulates the original image buffer inside frame object.
    cv2.putText(frame.as_opencv_image(), 'Cam: {}'.format(cam_id), org=(0, 30), fontScale=1,
                color=255, thickness=1, fontFace=cv2.FONT_HERSHEY_COMPLEX_SMALL)
    return frame


def resize_if_required(frame: Frame) -> np.ndarray:
    # Helper function resizing the given frame, if it has not the required dimensions.
    # On resizing, the image data is copied and resized, the image inside the frame object
    # is untouched.
    cv_frame = frame.as_opencv_image()

    if (frame.get_height() != FRAME_HEIGHT) or (frame.get_width() != FRAME_WIDTH):
        cv_frame = cv2.resize(cv_frame, (FRAME_WIDTH, FRAME_HEIGHT), interpolation=cv2.INTER_AREA)
        cv_frame = cv_frame[..., np.newaxis]

    return cv_frame

def create_dummy_frame() -> np.ndarray:
    cv_frame = np.zeros((WINDOW_WIDTH, WINDOW_HEIGHT, 1), np.uint8)
    cv_frame[:] = 0

    cv2.putText(cv_frame, 'No Stream available. Please connect a Camera.', org=(30, 30),
                fontScale=1, color=255, thickness=1, fontFace=cv2.FONT_HERSHEY_COMPLEX_SMALL)

    return cv_frame

def try_put_frame(q: queue.Queue, cam: Camera, frame: Optional[Frame]):
    try:
        q.put_nowait((cam.get_id(), frame))

    except queue.Full:
        pass

def set_nearest_value(cam: Camera, feat_name: str, feat_value: int):
    # Helper function that tries to set a given value. If setting of the initial value failed
    # it calculates the nearest valid value and sets the result. This function is intended to
    # be used with Height and Width Features because not all Cameras allow the same values
    # for height and width.
    feat = cam.get_feature_by_name(feat_name)

    try:
        feat.set(feat_value)

    except VimbaFeatureError:
        min_, max_ = feat.get_range()
        inc = feat.get_increment()

        if feat_value <= min_:
            val = min_

        elif feat_value >= max_:
            val = max_

        else:
            val = (((feat_value - min_) // inc) * inc) + min_

        feat.set(val)

        msg = ('Camera {}: Failed to set value of Feature \'{}\' to \'{}\': '
               'Using nearest valid value \'{}\'. Note that, this causes resizing '
               'during processing, reducing the frame rate.')
        Log.get_instance().info(msg.format(cam.get_id(), feat_name, feat_value, val))


# Thread Objects
class FrameProducer(threading.Thread):
    def __init__(self, cam: Camera, frame_queue: queue.Queue):
        threading.Thread.__init__(self)

        self.log = Log.get_instance()
        self.cam = cam
        self.frame_queue = frame_queue
        self.killswitch = threading.Event()
        self.IntensityControllerTarget = 50 # percent
        self.Gain = 1

    def __call__(self, cam: Camera, frame: Frame):
        # This method is executed within VimbaC context. All incoming frames
        # are reused for later frame acquisition. If a frame shall be queued, the
        # frame must be copied and the copy must be sent, otherwise the acquired
        # frame will be overridden as soon as the frame is reused.
        if frame.get_status() == FrameStatus.Complete:

            if not self.frame_queue.full():
                frame_cpy = copy.deepcopy(frame)
                try_put_frame(self.frame_queue, cam, frame_cpy)

        cam.queue_frame(frame)

    def stop(self):
        self.killswitch.set()

    def setIntensityCorrection(self, IntensityControllerTarget):
        self.IntensityControllerTarget = IntensityControllerTarget

    def setExposureTime(self, ExposureTime):
        self.ExposureTime = ExposureTime
        try:
            self.cam.ExposureTime.set(self.ExposureTime)
        except:
            print("Error setting ExposureTime1 - frame producer already running?")

    def setGain(self, Gain):
        self.Gain = Gain

    def setup_camera(self):
        #set_nearest_value(self.cam, 'Height', FRAME_HEIGHT)
        #set_nearest_value(self.cam, 'Width', FRAME_WIDTH)

        # try to set IntensityControllerTarget
        '''
        try:
            self.cam.ExposureAutoMax.set(T_EXPOSURE_MAX)

        except (AttributeError, VimbaFeatureError):
            self.log.info('Camera {}: Failed to set Feature \'ExposureAutoMax\'.'.format(
                        self.cam.get_id()))
        '''

        # try to set IntensityControllerTarget
        '''
        try:
            self.cam.IntensityControllerTarget.set(self.IntensityControllerTarget)

        except (AttributeError, VimbaFeatureError):
            self.log.info('Camera {}: Failed to set Feature \'IntensityControllerTarget\'.'.format(
                        self.cam.get_id()))
        '''

        # Try to set exposure time to something reasonable 
        try:
            self.cam.AcquisitionFrameRateEnable.set(True)

        except (AttributeError, VimbaFeatureError):
            self.log.info('Camera {}: Failed to set Feature \'AcquisitionFrameRateEnable\'.'.format(
                          self.cam.get_id()))

        # Try to set exposure time to something reasonable 
        try:
            self.cam.AcquisitionFrameRate.set(25)

        except (AttributeError, VimbaFeatureError):
            self.log.info('Camera {}: Failed to set Feature \'AcquisitionFrameRate\'.'.format(
                          self.cam.get_id()))


        # Try to set exposure time to something reasonable 
        try:
            self.cam.ExposureTime.set(self.ExposureTime)

        except (AttributeError, VimbaFeatureError):
            self.log.info('Camera {}: Failed to set Feature \'ExposureTime\'.'.format(
                          self.cam.get_id()))


        # Try to set GAIN automatic
        try:
            self.cam.Gain.set(self.Gain)

        except (AttributeError, VimbaFeatureError):
            self.log.info('Camera {}: Failed to set Feature \'Gain\'.'.format(
                          self.cam.get_id()))


        # Try to enable automatic exposure time setting
        
        try:
            self.cam.ExposureAuto.set('Off')

        except (AttributeError, VimbaFeatureError):
            self.log.info('Camera {}: Failed to set Feature \'ExposureAuto\'.'.format(
                          self.cam.get_id()))

        '''
        # Try to set GAIN automatic
        try:
            self.cam.GainAuto.set('Once')

        except (AttributeError, VimbaFeatureError):
            self.log.info('Camera {}: Failed to set Feature \'GainAuto\'.'.format(
                          self.cam.get_id()))
        '''


        self.cam.set_pixel_format(PixelFormat.Mono8)





    def run(self):
        self.log.info('Thread \'FrameProducer({})\' started.'.format(self.cam.get_id()))

        try:
            with self.cam:
                self.setup_camera()

                try:
                    self.cam.start_streaming(self)
                    self.killswitch.wait()

                finally:
                    self.cam.stop_streaming()

        except VimbaCameraError:
            pass

        finally:
            try_put_frame(self.frame_queue, self.cam, None)

        self.log.info('Thread \'FrameProducer({})\' terminated.'.format(self.cam.get_id()))


class FrameConsumer(threading.Thread):
    def __init__(self, frame_queue: queue.Queue, is_record=False, filename=''):
        threading.Thread.__init__(self)

        self.is_window_on_top = False
        self.is_stop = False
        self.is_record = is_record
        self.filename = filename
        self.log = Log.get_instance()
        self.frame_queue = frame_queue
        self.iframe = 0
        
        # timing for frame acquisition
        self.t_min = T_PERIODE  # s
        self.t_last = 0
        self.t_now = 0
        

    def run(self):
        KEY_CODE_ENTER = 13

        frames = {}
        alive = True

        self.log.info('Thread \'FrameConsumer\' started.')

        

        while alive:
            # Update current state by dequeuing all currently available frames.
            frames_left = self.frame_queue.qsize()

            # get time for frame acquisition
            self.t_now = time.time()

            while frames_left:
                try:
                    cam_id, frame = self.frame_queue.get_nowait()

                except queue.Empty:
                    break

                # Add/Remove frame from current state.
                if frame:
                    frames[cam_id] = frame

                else:
                    frames.pop(cam_id, None)

                frames_left -= 1
            
            # Construct image by stitching frames together.
            if frames:
                cv_images = [resize_if_required(frames[cam_id]) for cam_id in sorted(frames.keys())]
                np_images = np.concatenate(cv_images, axis=1)

                # save frames as they come
                if self.is_record and (np.abs(time.time()-self.t_last)>self.t_min): # make sure we pick frames after T_period
                    filename = self.filename+'/BURST_t-'+str(T_PERIODE)+'_'+str(self.iframe)+'.jpg'
                    self.log.info('Saving images at: '+filename)
                    self.t_last = time.time()
                    print(np_images.shape)
                    cv2.imwrite(filename, np_images)
                    self.iframe += 1

                # resize to fit in the window
                np_images = cv2.resize(np_images, (WINDOW_HEIGHT, WINDOW_WIDTH), interpolation=cv2.INTER_NEAREST)
                from scipy.ndimage import median_filter
                np_images = median_filter(np_images, size=2, mode="mirror")
                
                from skimage import exposure
                np_images = exposure.equalize_adapthist(np_images, clip_limit=0.03)
                #https://scikit-image.org/docs/dev/auto_examples/color_exposure/plot_equalize.html
                #np_images = np.float32(np_images)
                #np_images = .25*np_images/np.mean(np_images) # increase brightness # TODO: Make it adaptive
                #np_images = np.float32(cv2.equalizeHist(np_images))/255.
                #np_images = np.float32(np_images)/255.
                #print("pre: "+ str(np.min(np_images))+"/"+str(np.max(np_images))+"/"+str(np_images.shape))
                #np_images = np_images**2
                #np_images = np_images - np.min(np_images)
                #np_images = 2*255*np_images / np.max(np_images)
                #np_images[np_images>255]=255
                #np_images = np.uint8(np_images) 
                #print("pst: "+ str(np.min(np_images))+"/"+str(np.max(np_images)))
                
#                np_images = np.uint8( np_images * Ü cv2.normalize(np.p_images), 0., 255., cv2.NORM_MINMAX))#, cv2.CV_8UC1)
                #print("post: "+ str(np.min(np_images))+"/"+str(np.max(np_images)))
                cv2.imshow(IMAGE_CAPTION, np_images)
                cv2.moveWindow(IMAGE_CAPTION,WINDOW_START_FROM_LEFT,WINDOW_START_FROM_TOP)

                if not self.is_window_on_top:
                    # set window upfront
                    self.log.info('Setting window "always on top"')
                    # https://askubuntu.com/questions/394998/why-wmctrl-doesnt-work-for-certain-windows
                    os.system('wmctrl -r "UC2-Livestream" -b add,above')
                    self.is_window_on_top = True

            # If there are no frames available, show dummy image instead
            else:
                cv2.imshow(IMAGE_CAPTION, create_dummy_frame())
                cv2.moveWindow(IMAGE_CAPTION,WINDOW_START_FROM_LEFT,WINDOW_START_FROM_TOP)

            # Check for shutdown condition
            if self.is_stop or KEY_CODE_ENTER == cv2.waitKey(10):
                cv2.destroyAllWindows()
                alive = False
                self.is_window_on_top = False

        self.log.info('Thread \'FrameConsumer\' terminated.')


class VimbaCameraThread(threading.Thread):
    def __init__(self, is_record=False, filename=''):
        threading.Thread.__init__(self)

        self.frame_queue = queue.Queue(maxsize=FRAME_QUEUE_SIZE)
        self.producers = {}
        self.producers_lock = threading.Lock()
        self.is_record = is_record
        self.filename = filename
        self.is_active = False
        self.IntensityCorrection = 50
        self.Gain = 1
        self.ExposureTime = ExposureTime

    def __call__(self, cam: Camera, event: CameraEvent):
        # New camera was detected. Create FrameProducer, add it to active FrameProducers
        if event == CameraEvent.Detected:
            with self.producers_lock:
                self.producer = FrameProducer(cam, self.frame_queue)
                self.producer.start()

        # An existing camera was disconnected, stop associated FrameProducer.
        elif event == CameraEvent.Missing:
            with self.producers_lock:
                self.producer.stop()
                self.producer.join()

    def run(self):
        log = Log.get_instance()
        self.consumer = FrameConsumer(self.frame_queue, self.is_record, self.filename)

        vimba = Vimba.get_instance()
        vimba.enable_log(LOG_CONFIG_INFO_CONSOLE_ONLY)

        log.info('Thread \'VimbaCameraThread\' started.')

        with vimba:
            # Construct FrameProducer threads for all detected cameras
            cams = vimba.get_all_cameras()
            cam = cams[0]
            self.producer = FrameProducer(cam, self.frame_queue)
            #self.producer.setIntensityCorrection(self.IntensityCorrection)
            self.producer.setGain(self.Gain)
            self.producer.setExposureTime(self.ExposureTime)
            
            # Start FrameProducer threads
            with self.producers_lock:
                self.is_active = True
                self.producer.start()
            
            # Start and wait for consumer to terminate
            vimba.register_camera_change_handler(self)
            self.consumer.start()
            self.consumer.join()
            vimba.unregister_camera_change_handler(self)

            # Stop all FrameProducer threads
            with self.producers_lock:
                # Initiate concurrent shutdown
                self.producer.stop()

                # Wait for shutdown to complete
                self.producer.join()
        
        self.is_active = False
        log.info('Thread \'VimbaCameraThread\' terminated.')

    def stop(self):
        # Stop all FrameProducer threads
        print("Stopping main thread ")
        self.consumer.is_stop = True

    def setIntensityCorrection(self, IntensityCorrection=50):
        self.IntensityCorrection = IntensityCorrection

    def setGain(self, Gain=1):
        self.Gain = Gain
        try:
            self.producer.setGain(self.Gain)
        except:
            print("Error setting gain - frame producer already running?")


    def setExposureTime(self, ExposureTime):
        self.ExposureTime = ExposureTime
        try:
            self.producer.setExposureTime(self.ExposureTime)
        except:
            print("Error setting exposure time - frame producer already running?")


if __name__ == '__main__':
    Camera = VimbaCameraThread()
    Camera.start()
    #main.join()
    import time 
    time.sleep(10)
    Camera.stop()
