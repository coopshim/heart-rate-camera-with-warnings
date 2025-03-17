import cv2
import numpy as np
from PyQt5 import QtCore

from PyQt5.QtCore import QThread
from PyQt5.QtGui import QFont, QImage, QPixmap
from PyQt5.QtWidgets import QPushButton, QApplication, QComboBox, QLabel, QFileDialog, QStatusBar, QDesktopWidget, QMessageBox, QMainWindow

import pyqtgraph as pg
import sys
import time
from process import Process
from webcam import Webcam
from video import Video
from interface import waitKey, plotXY

class GUI(QMainWindow, QThread):
    def __init__(self):
        super(GUI,self).__init__()
        self.initUI()
        self.webcam = Webcam()
        self.video = Video()
        self.input = self.webcam
        self.dirname = ""
        print("Input: webcam")
        self.statusBar.showMessage("Input: webcam",5000)
        self.btnOpen.setEnabled(False)
        self.process = Process()
        self.status = False
        self.frame = np.zeros((10,10,3),np.uint8)
        #self.plot = np.zeros((10,10,3),np.uint8)
        self.bpm = 0
        self.terminate = False
        
    def initUI(self):
    
        #set font
        font = QFont()
        font.setPointSize(16)
        
        #widgets
        self.btnStart = QPushButton("Start", self)
        self.btnStart.move(440,520)
        self.btnStart.setFixedWidth(200)
        self.btnStart.setFixedHeight(50)
        self.btnStart.setFont(font)
        self.btnStart.clicked.connect(self.run)
        
        self.btnOpen = QPushButton("Open", self)
        self.btnOpen.move(230,520)
        self.btnOpen.setFixedWidth(200)
        self.btnOpen.setFixedHeight(50)
        self.btnOpen.setFont(font)
        self.btnOpen.clicked.connect(self.openFileDialog)
        
        self.cbbInput = QComboBox(self)
        self.cbbInput.addItem("Webcam")
        self.cbbInput.addItem("Video")
        self.cbbInput.setCurrentIndex(0)
        self.cbbInput.setFixedWidth(200)
        self.cbbInput.setFixedHeight(50)
        self.cbbInput.move(20,520)
        self.cbbInput.setFont(font)
        self.cbbInput.activated.connect(self.selectInput)
        #-------------------
        
        self.lblDisplay = QLabel(self) #label to show frame from camera
        self.lblDisplay.setGeometry(10,10,640,480)
        self.lblDisplay.setStyleSheet("background-color: #000000")
        
        self.lblROI = QLabel(self) #label to show face with ROIs
        self.lblROI.setGeometry(660,10,200,200)
        self.lblROI.setStyleSheet("background-color: #000000")
        
        self.lblHR = QLabel(self) #label to show HR change over time
        self.lblHR.setGeometry(900,20,300,40)
        self.lblHR.setFont(font)
        self.lblHR.setText("Frequency: ")
        
        self.lblHR2 = QLabel(self) #label to show stable HR
        self.lblHR2.setGeometry(900,70,300,40)
        self.lblHR2.setFont(font)
        self.lblHR2.setText("Heart rate: ")
        
        # self.lbl_Age = QLabel(self) #label to show stable HR
        # self.lbl_Age.setGeometry(900,120,300,40)
        # self.lbl_Age.setFont(font)
        # self.lbl_Age.setText("Age: ")
        
        # self.lbl_Gender = QLabel(self) #label to show stable HR
        # self.lbl_Gender.setGeometry(900,170,300,40)
        # self.lbl_Gender.setFont(font)
        # self.lbl_Gender.setText("Gender: ")
        
        #dynamic plot
        self.signal_Plt = pg.PlotWidget(self)
        
        self.signal_Plt.move(660,220)
        self.signal_Plt.resize(480,192)
        self.signal_Plt.setLabel('bottom', "Signal") 
        
        self.fft_Plt = pg.PlotWidget(self)
        
        self.fft_Plt.move(660,425)
        self.fft_Plt.resize(480,192)
        self.fft_Plt.setLabel('bottom', "FFT") 
        
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(200)
        
        
        self.statusBar = QStatusBar()
        self.statusBar.setFont(font)
        self.setStatusBar(self.statusBar)

        #config main window
        self.setGeometry(100,100,1160,640)
        #self.center()
        self.setWindowTitle("Heart rate monitor")
        self.show()
        
        
    def update(self):
        self.signal_Plt.clear()
        self.signal_Plt.plot(self.process.samples[20:],pen='g')

        self.fft_Plt.clear()
        self.fft_Plt.plot(np.column_stack((self.process.freqs, self.process.fft)), pen = 'g')
        
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        
    def closeEvent(self, event):
        reply = QMessageBox.question(self,"Message", "Are you sure want to quit",
            QMessageBox.Yes|QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            event.accept()
            self.input.stop()
            # cv2.destroyAllWindows()
            self.terminate = True
            sys.exit()

        else: 
            event.ignore()
    
    def selectInput(self):
        self.reset()
        if self.cbbInput.currentIndex() == 0:
            self.input = self.webcam
            print("Input: webcam")
            self.btnOpen.setEnabled(False)
            #self.statusBar.showMessage("Input: webcam",5000)
        elif self.cbbInput.currentIndex() == 1:
            self.input = self.video
            print("Input: video")
            self.btnOpen.setEnabled(True)
            #self.statusBar.showMessage("Input: video",5000)   
    
    # def make_bpm_plot(self):
        # plotXY([[self.process.times[20:],
                     # self.process.samples[20:]],
                    # [self.process.freqs,
                     # self.process.fft]],
                    # labels=[False, True],
                    # showmax=[False, "bpm"],
                    # label_ndigits=[0, 0],
                    # showmax_digits=[0, 1],
                    # skip=[3, 3],
                    # name="Plot",
                    # bg=None)
        
        # fplot = QImage(self.plot, 640, 280, QImage.Format_RGB888)
        # self.lblPlot.setGeometry(10,520,640,280)
        # self.lblPlot.setPixmap(QPixmap.fromImage(fplot))
    
    def key_handler(self):
        """
        cv2 window must be focused for keypresses to be detected.
        """
        self.pressed = waitKey(1) & 255  # wait for keypress for 10 ms
        if self.pressed == 27:  # exit program on 'esc'
            print("[INFO] Exiting")
            self.webcam.stop()
            sys.exit()
    
    def openFileDialog(self):
        self.dirname = QFileDialog.getOpenFileName(self, 'OpenFile')
        #self.statusBar.showMessage("File name: " + self.dirname,5000)
    
    def reset(self):
        self.process.reset()
        self.lblDisplay.clear()
        self.lblDisplay.setStyleSheet("background-color: #000000")

    def main_loop(self):
        frame = self.input.get_frame()

        self.process.frame_in = frame
        if self.terminate == False:
            ret = self.process.run()
    
        # 처리 결과에 따라 frame, ROI, 심박수 업데이트
        if ret == True:
            self.frame = self.process.frame_out  # GUI에 출력할 프레임
            self.f_fr = self.process.frame_ROI   # 얼굴 ROI 프레임
            self.bpm = self.process.bpm          # 현재 심박수 값
        else:
            self.frame = frame
            self.f_fr = np.zeros((10, 10, 3), np.uint8)
            self.bpm = 0
    
        # OpenCV의 putText()를 사용하기 위해 프레임을 RGB에서 BGR로 변환
        self.frame = cv2.cvtColor(self.frame, cv2.COLOR_RGB2BGR)
    
        # FPS 정보 오버레이(기존 기능)
        cv2.putText(self.frame, "FPS "+str(float("{:.2f}".format(self.process.fps))),
                   (20,460), cv2.FONT_HERSHEY_PLAIN, 1.5, (0, 255, 255), 2)
    
        # 심박수 측정 값 설정
        HIGH_THRESHOLD = 150    # 높은 심박수 
        LOW_THRESHOLD = 60      # 낮은 심박수    
        NO_THRESHOLD = 0        # 심박수가 측정되지 아니함

        # 심박수가 측정되지 않을 때 상태 메시지 표출(초기 부팅시, 얼굴 미감지시)
        if self.bpm == NO_THRESHOLD:
            cv2.putText(self.frame, "SYSTEM: Heart Rate Not Detected", (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
            
        # 심박수가 임계 값보다 높거나 낮을 경우 경고를 표출
        elif self.bpm > HIGH_THRESHOLD or (0 < self.bpm < LOW_THRESHOLD):
            cv2.putText(self.frame, "WARNING: Abnormal Heart Rate!", (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 0, 0), 2)

        # 그 외의 경우는 '정상 심박수'로 판정     
        else:
            cv2.putText(self.frame, "SYSTEM: Heart Rate Normal", (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
    
        # 변경된 프레임을 QImage로 변환하여 라벨에 출력
        img = QImage(self.frame, self.frame.shape[1], self.frame.shape[0], 
                    self.frame.strides[0], QImage.Format_RGB888)
        self.lblDisplay.setPixmap(QPixmap.fromImage(img))
    
        # ROI 영상 처리 및 출력
        self.f_fr = cv2.cvtColor(self.f_fr, cv2.COLOR_RGB2BGR)
        self.f_fr = np.transpose(self.f_fr, (0,1,2)).copy()
        f_img = QImage(self.f_fr, self.f_fr.shape[1], self.f_fr.shape[0], 
                    self.f_fr.strides[0], QImage.Format_RGB888)
        self.lblROI.setPixmap(QPixmap.fromImage(f_img))
    
        # 실시간 심박수 및 주파수 표출 관련 (우측/기존기능)  
        self.lblHR.setText("Freq: " + str(float("{:.2f}".format(self.bpm))))
    
        if len(self.process.bpms) > 50:
            if (max(self.process.bpms - np.mean(self.process.bpms)) < 5):
                self.lblHR2.setText("Heart rate: " + str(float("{:.2f}".format(np.mean(self.process.bpms)))) + " bpm")
    
        # 키 입력 처리
        self.key_handler()  # cv2 창이 활성화 되어 있어야 키 입력이 감지됨


    def run(self, input):
        print("run")
        self.reset()
        input = self.input
        self.input.dirname = self.dirname
        if self.input.dirname == "" and self.input == self.video:
            print("choose a video first")
            #self.statusBar.showMessage("choose a video first",5000)
            return
        if self.status == False:
            self.status = True
            input.start()
            self.btnStart.setText("Stop")
            self.cbbInput.setEnabled(False)
            self.btnOpen.setEnabled(False)
            self.lblHR2.clear()
            while self.status == True:
                self.main_loop()

        elif self.status == True:
            self.status = False
            input.stop()
            self.btnStart.setText("Start")
            self.cbbInput.setEnabled(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = GUI()
    sys.exit(app.exec_())
