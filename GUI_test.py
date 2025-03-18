import cv2
import numpy as np
from PyQt5 import QtCore
from PyQt5.QtCore import QThread, Qt
from PyQt5.QtGui import QFont, QImage, QPixmap
from PyQt5.QtWidgets import (QPushButton, QApplication, QComboBox, QLabel, QFileDialog,
                             QStatusBar, QMessageBox, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout)
import pyqtgraph as pg
import sys
import time
from process import Process
from webcam import Webcam
from video import Video
from interface import waitKey, plotXY

class GUI(QMainWindow):
    def __init__(self):
        super(GUI, self).__init__()
        self.webcam = Webcam()
        self.video = Video()
        self.input = self.webcam
        self.dirname = ""
        self.process = Process()
        self.status = False
        self.frame = np.zeros((10,10,3), np.uint8)
        self.bpm = 0
        self.terminate = False
        self.initUI()

    def initUI(self):
        # set font
        font = QFont()
        font.setPointSize(16)

        # 중앙 위젯 및 레이아웃 사용 (반응형 인터페이스)
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # 왼쪽 레이아웃: 웹캠 영상 표시
        left_layout = QVBoxLayout()
        self.lblDisplay = QLabel()
        self.lblDisplay.setStyleSheet("background-color: #000000")
        self.lblDisplay.setAlignment(Qt.AlignCenter)
        self.lblDisplay.setScaledContents(True)  # QPixmap이 라벨 크기에 맞게 자동 조절됨
        left_layout.addWidget(self.lblDisplay)

        # 오른쪽 레이아웃: 컨트롤 및 상태 표시
        right_layout = QVBoxLayout()
        # 상단 컨트롤 버튼들
        self.cbbInput = QComboBox(self)
        self.cbbInput.addItem("Webcam")
        self.cbbInput.addItem("Video")
        self.cbbInput.setCurrentIndex(0)
        self.cbbInput.setFont(font)
        self.cbbInput.activated.connect(self.selectInput)

        self.btnOpen = QPushButton("Open", self)
        self.btnOpen.setFont(font)
        self.btnOpen.clicked.connect(self.openFileDialog)
        self.btnOpen.setEnabled(False)

        self.btnStart = QPushButton("Start", self)
        self.btnStart.setFont(font)
        self.btnStart.clicked.connect(self.run)

        # 상태 표시 라벨들
        self.lblHR = QLabel("Frequency: ", self)
        self.lblHR.setFont(font)
        self.lblHR2 = QLabel("Heart rate: ", self)
        self.lblHR2.setFont(font)

        # ROI(얼굴) 영상 표시 (크기는 고정할 수도 있고 레이아웃에 따라 변하게 할 수도 있음)
        self.lblROI = QLabel(self)
        self.lblROI.setStyleSheet("background-color: #000000")
        self.lblROI.setFixedSize(200, 200)

        # 동적 플롯 영역 (pyqtgraph)
        self.signal_Plt = pg.PlotWidget(self)
        self.signal_Plt.setLabel('bottom', "Signal")
        self.signal_Plt.setFixedSize(400, 200)
        self.fft_Plt = pg.PlotWidget(self)
        self.fft_Plt.setLabel('bottom', "FFT")
        self.fft_Plt.setFixedSize(400, 200)

        # 오른쪽 레이아웃에 위젯 추가
        right_layout.addWidget(self.cbbInput)
        right_layout.addWidget(self.btnOpen)
        right_layout.addWidget(self.btnStart)
        right_layout.addWidget(self.signal_Plt)
        right_layout.addWidget(self.fft_Plt)
        right_layout.addWidget(self.lblHR)
        right_layout.addWidget(self.lblHR2)
        right_layout.addWidget(self.lblROI)        

        # 메인 레이아웃에 왼쪽, 오른쪽 레이아웃 배치
        main_layout.addLayout(left_layout, 2)  # 왼쪽 영역은 좀 더 크게
        main_layout.addLayout(right_layout, 1)

        # 하단 상태바 설정
        self.statusBar = QStatusBar()
        self.statusBar.setFont(font)
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Input: webcam", 5000)

        # 타이머 (플롯 업데이트)
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(200)

        # 메인 창 기본 설정 (초기 해상도)
        self.setWindowTitle("Heart rate monitor")
        self.resize(1600, 900)  # 초기 창 크기를 더 크게 설정
        self.show()

    def update(self):
        self.signal_Plt.clear()
        self.signal_Plt.plot(self.process.samples[20:], pen='g')
        self.fft_Plt.clear()
        self.fft_Plt.plot(np.column_stack((self.process.freqs, self.process.fft)), pen='g')

    def closeEvent(self, event):
        reply = QMessageBox.question(self, "Message", "Are you sure want to quit",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            # 종료 플래그 설정 및 타이머 정지
            self.status = False
            self.terminate = True
            self.timer.stop()
            self.input.stop()
            event.accept()
        else:
            event.ignore()

    def selectInput(self):
        self.reset()
        if self.cbbInput.currentIndex() == 0:
            self.input = self.webcam
            self.btnOpen.setEnabled(False)
        elif self.cbbInput.currentIndex() == 1:
            self.input = self.video
            self.btnOpen.setEnabled(True)

    def openFileDialog(self):
        self.dirname = QFileDialog.getOpenFileName(self, 'OpenFile')[0]

    def reset(self):
        self.process.reset()
        self.lblDisplay.clear()
        self.lblDisplay.setStyleSheet("background-color: #000000")

    def key_handler(self):
        """
        cv2 window must be focused for keypresses to be detected.
        """
        self.pressed = waitKey(1) & 255  # wait for keypress for 10 ms
        if self.pressed == 27:  # exit program on 'esc'
            print("[INFO] Exiting")
            self.webcam.stop()
            QApplication.quit()

    def main_loop(self):
        frame = self.input.get_frame()

        self.process.frame_in = frame
        if not self.terminate:
            ret = self.process.run()
        else:
            ret = False

        if ret:
            self.frame = self.process.frame_out  # GUI에 출력할 프레임
            self.f_fr = self.process.frame_ROI   # 얼굴 ROI 프레임
            self.bpm = self.process.bpm          # 현재 심박수 값
        else:
            self.frame = frame
            self.f_fr = np.zeros((10, 10, 3), np.uint8)
            self.bpm = 0

        # 프레임 색상 변환(RGB->BGR) 후 정보 오버레이
        self.frame = cv2.cvtColor(self.frame, cv2.COLOR_RGB2BGR)
        cv2.putText(self.frame, "FPS " + str(float("{:.2f}".format(self.process.fps))),
                    (20, 700), cv2.FONT_HERSHEY_PLAIN, 1.5, (0, 255, 255), 2)

        # 심박수 임계값에 따른 메시지 표출
        HIGH_THRESHOLD = 150
        LOW_THRESHOLD = 60
        NO_THRESHOLD = 0

        if self.bpm == NO_THRESHOLD:
            cv2.putText(self.frame, "SYSTEM: Heart Rate Not Detected", (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)
        elif self.bpm > HIGH_THRESHOLD or (0 < self.bpm < LOW_THRESHOLD):
            cv2.putText(self.frame, "WARNING: Abnormal Heart Rate!", (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 0, 0), 2)
        else:
            cv2.putText(self.frame, "SYSTEM: Heart Rate Normal", (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

        # QImage로 변환 후 라벨에 출력 (반응형 lblDisplay)
        img = QImage(self.frame, self.frame.shape[1], self.frame.shape[0],
                     self.frame.strides[0], QImage.Format_RGB888)
        self.lblDisplay.setPixmap(QPixmap.fromImage(img))

        # ROI 영상 처리 및 출력
        self.f_fr = cv2.cvtColor(self.f_fr, cv2.COLOR_RGB2BGR)
        self.f_fr = np.transpose(self.f_fr, (0, 1, 2)).copy()
        f_img = QImage(self.f_fr, self.f_fr.shape[1], self.f_fr.shape[0],
                       self.f_fr.strides[0], QImage.Format_RGB888)
        self.lblROI.setPixmap(QPixmap.fromImage(f_img))

        self.lblHR.setText("Freq: " + str(float("{:.2f}".format(self.bpm))))
        if len(self.process.bpms) > 50:
            if (max(self.process.bpms - np.mean(self.process.bpms)) < 5):
                self.lblHR2.setText("Heart rate: " + str(float("{:.2f}".format(np.mean(self.process.bpms)))) + " bpm")

        self.key_handler()

    def run(self, input=None):
        self.reset()
        self.input.dirname = self.dirname
        if self.input.dirname == "" and self.input == self.video:
            print("choose a video first")
            return
        if not self.status:
            self.status = True
            # 상태바에 시작 메시지 표시 (0은 무제한 시간)
            self.statusBar.showMessage("System starting, Please wait.", 0)
            self.input.start()      # 웹캠 시작
            # 웹캠이 정상적으로 로딩될 때까지 기다림 (웹캠의 start()에서 self.valid 플래그가 설정됨)
            while not self.input.valid:
                QApplication.processEvents()
                time.sleep(0.1)
            self.statusBar.clearMessage()       # 웹캠 로딩 완료 후 상태바 메시지 삭제
            self.btnStart.setText("Stop")
            self.cbbInput.setEnabled(False)
            self.btnOpen.setEnabled(False)
            self.lblHR2.clear()
            while self.status:
                self.main_loop()
        else:
            self.status = False
            self.input.stop()
            self.btnStart.setText("Start")
            self.cbbInput.setEnabled(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = GUI()
    sys.exit(app.exec_())
