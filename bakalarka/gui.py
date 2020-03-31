from os import path
from tkinter import Frame, Canvas, Button, Scale, DoubleVar, Checkbutton, BooleanVar, HORIZONTAL, Tk, messagebox, \
    Spinbox, IntVar, Label, filedialog, NW
import cv2 as cv
from cropper import Cropper
from marker import Marker
from segmentation import Segmentation


class Gui:
    fps = None
    frame_count = None
    duration = None
    currentFrameImage = None

    def __init__(self, main, size_x, size_y):
        self.main = main
        self.SIZE_X = size_x
        self.SIZE_Y = size_y
        self._initGUI()

    def _initGUI(self):
        self._initMasterFrameCanvasGUI()
        self._initLoadResetGUI()
        self._initExportGUI()
        self._initTimeControlGUI()
        self._initBackgroundCropGUI()
        self._initPlayMarkGUI()
        self._initCheckButtons()
        self._initMidiParameters()
        self._initThreshParameterPicker()

    def _initMasterFrameCanvasGUI(self):
        self.master = Tk()
        self.master.title('Bakalarka')
        self.frame = Frame(self.master, width=self.SIZE_X + 250, height=self.SIZE_Y + 100)
        self.frame.pack()
        self.canvas = Canvas(self.frame, width=self.SIZE_X, height=self.SIZE_Y)
        self.canvas.place(x=0, y=0)

    def _initLoadResetGUI(self):
        Button(self.frame, text='Load', padx=10, pady=1, command=self.load).place(
            x=self.SIZE_X + 5, y=5)

    def _initExportGUI(self):
        Button(self.frame, text='Export', padx=10, pady=1, command=self.main.export).place(
            x=self.SIZE_X + 125, y=5)

    def _initTimeControlGUI(self):
        self.position = DoubleVar(0)
        self.scale = Scale(self.frame, from_=0, orient=HORIZONTAL,
                           length=self.SIZE_X, tickinterval=15, command=self._updatePosition, variable=self.position)
        self.scale.place(x=0, y=self.SIZE_Y + 20)

    def _initBackgroundCropGUI(self):
        Button(self.frame, text='Set Background', padx=10, pady=1, command=self._setBackground).place(
            x=self.SIZE_X + 5, y=95)
        Button(self.frame, text='Crop Keyboard', padx=10, pady=1, command=self._cropKeyboardArea).place(
            x=self.SIZE_X + 5, y=35)

    def _initPlayMarkGUI(self):
        self.playOrStopButton = Button(self.frame, text='Play', padx=10, pady=1, command=self._playOrStop)
        self.playOrStopButton.place(x=self.SIZE_X + 5, y=135)
        Button(self.frame, text='Mark C', padx=10, pady=1, command=self._markKeyboardMiddle).place(
            x=self.SIZE_X + 115, y=35)

    def _initCheckButtons(self):
        self.handFilter = BooleanVar(value=False)
        Checkbutton(self.frame, text='HandFilter', variable=self.handFilter).place(x=self.SIZE_X + 5, y=165)
        self.transcribing = BooleanVar(value=False)
        Checkbutton(self.frame, text='Transcribing', variable=self.transcribing).place(x=self.SIZE_X + 5, y=185)

    def _initMidiParameters(self):
        self.tempo = IntVar(value=60)
        Label(self.frame, text='Tempo').place(x=self.SIZE_X + 5, y=220)
        Spinbox(self.frame, from_=20, to=150, textvariable=self.tempo, width=5).place(x=self.SIZE_X + 5, y=240)
        self.transpose = IntVar(value=0)
        Label(self.frame, text='Transpose').place(x=self.SIZE_X + 55, y=220)
        Spinbox(self.frame, from_=-10, to=10, textvariable=self.transpose, width=5).place(x=self.SIZE_X + 55, y=240)

    def _initThreshParameterPicker(self):
        self.thresh = IntVar(value=85)
        Label(self.frame, text='Thresh').place(x=self.SIZE_X + 135, y=85)
        Spinbox(self.frame, from_=0, to=255, textvariable=self.thresh, width=5,
                command=self._showThreshParameter).place(x=self.SIZE_X + 135, y=105)

    def _showThreshParameter(self):
        gray = cv.cvtColor(self.main.capture.getCurrentFrameCropped(), cv.COLOR_BGR2GRAY)
        gray = cv.GaussianBlur(gray, (3, 3), 0)
        ret, thresh = cv.threshold(gray, self.thresh.get(), 255, cv.THRESH_BINARY_INV)
        self.threshExampleImage = self.main.capture.getPhotoImageFromFrame(thresh)
        self.drawImage(self.threshExampleImage)

    def _playOrStop(self):
        if self.main.playing:
            self.stop()
        elif self.main.capture is not None and self.main.capture.isOpened():
            self.play()
        else:
            messagebox.showinfo('Chyba', 'Nie je načítané video.')

    def play(self):
        self.main.playing = True
        self.playOrStopButton['text'] = 'Stop'
        while self.main.playing and (self.main.capture.get(cv.CAP_PROP_POS_FRAMES) < self.frame_count):
            self.main.step()
        self.stop()

    def stop(self):
        self.main.playing = False
        self.playOrStopButton['text'] = 'Play'

    def setTimeControlGUI(self):
        self.fps = self.main.capture.get(cv.CAP_PROP_FPS)
        self.frame_count = int(self.main.capture.get(cv.CAP_PROP_FRAME_COUNT))
        self.duration = self.frame_count / self.fps
        self.scale['to'] = self.duration

    def _updatePosition(self, position):
        frameNumber = int(position) * self.fps
        self.main.capture.set(cv.CAP_PROP_POS_FRAMES, frameNumber)
        self.showFrame()

    def showPosition(self):
        self.position.set(self.main.capture.get(cv.CAP_PROP_POS_MSEC) / 1000)

    def load(self, filename=''):
        try:
            if not filename:
                filename = filedialog.askopenfilename(title="Vyberte súbor")
            if not path.isfile(filename):
                raise FileNotFoundError
            self.main.capture.setVideoFile(filename)
            self.main.capture.setCanvasSize(self.SIZE_X, self.SIZE_Y)
            self.setTimeControlGUI()
            self.showFrame()
            self.frame.update()
        except FileNotFoundError:
            messagebox.showinfo("Chyba", "Súbor sa nepodarilo prečítať")

    def showFrame(self):
        self.drawFrame()

    def drawFrame(self):
        if self.transcribing.get() and False:  #####################################################  to do
            frame1 = cv.cvtColor(self.main.capture.background, cv.COLOR_BGR2GRAY)
            frame2 = cv.cvtColor(self.main.capture.getCurrentFrameCropped(), cv.COLOR_BGR2GRAY)
            self.currentFrameImage = self.main.capture.getSubtractedFramePhotoImage(frame1, frame2)
        else:
            self.currentFrameImage = self.main.capture.getCurrentFramePhotoImage()
        self.drawImage(self.currentFrameImage)

    def drawImage(self, image):
        self.canvas.create_image(0, 0, image=image, anchor=NW)
        self.frame.update()

    def _cropKeyboardArea(self):
        Cropper(self.main.capture)
        self.drawFrame()

    def _markKeyboardMiddle(self):
        Marker(self.main.capture)

    def _setBackground(self):
        self.main.capture.background = self.main.capture.getCurrentFrameCropped()
        self.main.capture.grayBackground = cv.cvtColor(self.main.capture.background, cv.COLOR_BGR2GRAY)
        Segmentation(self.main)

    @staticmethod
    def showExample(img, name='sample'):
        cv.imshow(name, img)
        cv.waitKey(0)
