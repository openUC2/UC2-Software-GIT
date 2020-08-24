import sys
from typing import Optional
from vimba import *
import cv2
import numpy as np 
from threading import Thread 


'''
print('importing matloblib...')
import matplotlib
#matplotlib.use('Agg')
import matplotlib.pyplot as plt
print('Done: importing matloblib...')
'''


'''
class VimbaCamera(Thread): 
    def __init__(self, n): 
        super().__init__() 
        self.n = 0
          
    def run(self): 
        while self.n > 0:        
    print('T-minus', self.n) 
    self.n -= 1
    time.sleep(5) 
      
c = CountdownThread(5) 
c.start()
''' 



def get_camera() -> Camera:
    with Vimba.get_instance() as vimba:
        cams = vimba.get_all_cameras()
        return cams[0]

def setup_camera(cam: Camera):
    with cam:
        # Try to adjust GeV packet size. This Feature is only available for GigE - Cameras.
        try:
            cam.GVSPAdjustPacketSize.run()

            while not cam.GVSPAdjustPacketSize.is_done():
                pass

        except (AttributeError, VimbaFeatureError):
            pass


global cam

def main():

    with Vimba.get_instance():
        with get_camera() as cam:
            setup_camera(cam)     

            # Acquire 10 frame with a custom timeout (default is 2000ms) per frame acquisition.
            frameiterator = 0
            for frame in cam.get_frame_generator(limit=50, timeout_ms=3000):
                
                ENTER_KEY_CODE = 13

                key = cv2.waitKey(1)
                if key == ENTER_KEY_CODE:
                    self.shutdown_event.set()
                    return


                msg = 'Stream from \'{}\'. Press <Enter> to stop stream.'
                myframe = frame.as_opencv_image()
                cv2.imshow(msg.format(cam.get_name()), myframe)


                frameiterator += 1

                print('Got {}'.format(frame), flush=True)
                msg = 'Stream from \'{}\'. Press <Enter> to stop stream.'



if __name__ == '__main__':
    main()