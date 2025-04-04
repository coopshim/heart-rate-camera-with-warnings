import cv2
import numpy as np
import time

class Webcam(object):
    def __init__(self):
        #print ("WebCamEngine init")
        self.index = 0  # Camera input number
        self.dirname = "" # for nothing, just to make 2 inputs the same
        self.cap = None
    
    def start(self):
        print("[INFO] Start webcam")
        time.sleep(1) # wait for camera to be ready
        self.cap = cv2.VideoCapture(self.index)
        # 웹캠 해상도 조절 기능 (주의: 고해상도일수록 불러오는 시간이 증가함.)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640) # 웹캠 해상도 조절(Width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480) # 웹캠 해상도 조절(Height)
        self.valid = False
        try:
            resp = self.cap.read()
            self.shape = resp[1].shape
            self.valid = True
        except:
            self.shape = None
    
    def get_frame(self):
    
        if self.valid:
            _,frame = self.cap.read()
            frame = cv2.flip(frame,1)
            # cv2.putText(frame, str(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            #           (65,220), cv2.FONT_HERSHEY_PLAIN, 2, (0,256,256))
        else:
            frame = np.ones((480,640,3), dtype=np.uint8)
            col = (0,256,256)
            cv2.putText(frame, "(Error: Camera not accessible)",
                       (65,220), cv2.FONT_HERSHEY_PLAIN, 2, col)
        return frame

    def stop(self):
        if self.cap is not None:
            self.cap.release()
            print("[INFO] Stop webcam")

        
