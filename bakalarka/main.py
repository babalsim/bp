from tkinter import filedialog, messagebox, Frame, Canvas, Button, Scale, DoubleVar, Checkbutton, BooleanVar
from os import path
import time

import cv2 as cv
import asyncio
from tkinter import Tk, NW, HORIZONTAL
from PIL import Image, ImageTk
from capture import Capture
from cropper import Cropper


class Program:
    SIZE_X = 400
    SIZE_Y = 200
    capture = Capture()
    playing = False
    currentFrame = None
    middleC = None

    def __init__(self):
        self._initGUI()
        self.master.update()
        self.segmentation()
        self.master.mainloop()

    def __del__(self):
        if self.capture.isOpened():
            self.capture.release()

    def _initGUI(self):
        self.master = Tk()
        self.master.title('Bakalarka')
        self._initFrameCanvasGUI()
        self._initLoadResetGUI()
        self._initExportGUI()
        self._initTimeControlGUI()
        self._initBackgroundCropGUI()
        self._initPlayControlGUI()
        self._initCheckButtons()

    def _initFrameCanvasGUI(self):
        self.frame = Frame(self.master, width=self.SIZE_X + 250, height=self.SIZE_X * 2 + 100)
        self.frame.pack()
        self.canvas = Canvas(self.frame, width=self.SIZE_X, height=self.SIZE_Y)
        self.canvas.place(x=0, y=0)

    def _initLoadResetGUI(self):
        Button(self.frame, text='Load', padx=10, pady=1, command=self.load).place(
            x=self.SIZE_X + 5, y=5)
        Button(self.frame, text='Reset', padx=10, pady=1, command=self.reset).place(
            x=self.SIZE_X + 115, y=5)

    def _initExportGUI(self):
        Button(self.frame, text='Export to MIDI', padx=10, pady=1, command=self.exportMIDI).place(
            x=self.SIZE_X + 5, y=45)
        Button(self.frame, text='Export to MusicXML', padx=10, pady=1, command=self.exportMusicXML).place(
            x=self.SIZE_X + 115, y=45)

    def _initTimeControlGUI(self):
        self.position = DoubleVar(0)
        self.scale = Scale(self.frame, label='----', from_=0, orient=HORIZONTAL,
                           length=self.SIZE_X, tickinterval=15, command=self.updatePosition, variable=self.position)
        self.scale.place(x=20, y=self.SIZE_X + 20)

    def _initBackgroundCropGUI(self):
        Button(self.frame, text='Set Background', padx=10, pady=1, command=self.setBackground).place(
            x=self.SIZE_X + 5, y=95)
        Button(self.frame, text='Crop Keyboard', padx=10, pady=1, command=self.cropKeyboardArea).place(
            x=self.SIZE_X + 115, y=95)

    def _initPlayControlGUI(self):
        self.playOrStopButton = Button(self.frame, text='Play', padx=10, pady=1, command=self.playOrStop)
        self.playOrStopButton.place(x=self.SIZE_X + 5, y=135)
        Button(self.frame, text='nothing', padx=10, pady=1, command=lambda: None).place(
            x=self.SIZE_X + 115, y=135)

    def _initCheckButtons(self):
        self.handFilter = BooleanVar()
        self.handFilter.set(False)
        Checkbutton(self.frame, text="HandFilter", variable=self.handFilter).place(x=self.SIZE_X + 5, y=165)
        self.transcribing = BooleanVar()
        self.transcribing.set(False)
        Checkbutton(self.frame, text="Transcribing", variable=self.transcribing).place(x=self.SIZE_X + 5, y=185)

    def _setTimeControlGUI(self):
        self.fps = self.capture.get(cv.CAP_PROP_FPS)
        self.frame_count = int(self.capture.get(cv.CAP_PROP_FRAME_COUNT))
        self.duration = self.frame_count / self.fps
        self.scale['to'] = self.duration

    def load(self):
        try:
            filename = filedialog.askopenfilename(title="Vyberte súbor")
            if not path.isfile(filename):
                raise FileNotFoundError
            self.capture.setVideoFile(filename)
            self.capture.setCanvasSize(self.SIZE_X, self.SIZE_Y)
            self._setTimeControlGUI()
            self.showFrame()
        except FileNotFoundError:
            messagebox.showinfo("Chyba", "Súbor sa nepodarilo prečítať")

    def showProccessed(self, frame):
        canvas = Canvas(self.frame, width=self.SIZE_X, height=self.SIZE_X)
        canvas.place(x=0, y=self.SIZE_X)
        photo = ImageTk.PhotoImage(image=Image.fromarray(cv.cvtColor(frame, cv.COLOR_BGR2RGB)).resize(
            (self.SIZE_X, self.SIZE_X), Image.ANTIALIAS))
        canvas.create_image(0, 0, image=photo, anchor=NW)

    def play(self):
        self.playing = True
        self.playOrStopButton['text'] = 'Stop'
        while self.playing:
            self.capture.grab()
            self.showFrame()
            self.showPosition()

    def stop(self):
        self.playing = False
        self.playOrStopButton['text'] = 'Play'

    def showFrame(self):
        if self.handFilter.get():
            frame = self.removeHands(self.capture.getCurrentFrame())
        # if self.background is not None:
        #     frame = self.background - frame
        self.drawFrame()

    def drawFrame(self):
        self.currentFrame = self.capture.getCurrentFramePhotoImage()
        self.drawImage(self.currentFrame)

    def drawImage(self, image):
        self.canvas.create_image(0, 0, image=image, anchor=NW)
        self.frame.update()

    def segmentation(self):
        img = cv.imread('dataset/klaviatura.png')
        # self.drawFrame(img)

    def removeHands(self, frame):
        for i in range(self.y_start, self.y_end):
            for j in range(self.x_start, self.x_end):
                r, g, b = map(int, frame[i][j])
                if (r > 65 and g > 40 and b > 30):
                    # and max(r, g, b) - min(r, g, b) > 15
                    #  and r > g and r > b):
                    frame[i][j] = [255, 0, 0]
        return frame

    def reset(self):
        raise NotImplementedError()

    def exportMIDI(self):
        raise NotImplementedError()

    def exportMusicXML(self):
        raise NotImplementedError()

    def setBackground(self):
        _, self.background = self.capture.retrieve()

    def playOrStop(self):
        if self.playing:
            self.stop()
        elif self.capture.isOpened():
            self.play()
        else:
            messagebox.showinfo('Chyba', 'Nie je načítané video.')

    def updatePosition(self, position):
        frameNumber = int(position) * self.fps
        self.capture.set(cv.CAP_PROP_POS_FRAMES, frameNumber)
        ret, frame = self.capture.read()
        self.showFrame(frame)

    def showPosition(self):
        self.position.set(self.capture.get(cv.CAP_PROP_POS_MSEC) / 1000)

    def cropKeyboardArea(self):
        Cropper(self.capture)
        self.drawFrame()


if __name__ == '__main__':
    try:
        Program()
        exit(0)
    except FileExistsError:
        exit(1)
