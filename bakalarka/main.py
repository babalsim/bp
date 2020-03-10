#pip install opencv-python MIDIUtil tk

import numpy as np
import cv2 as cv
import time
from tkinter import filedialog, messagebox, Frame, Canvas, Button, Scale, DoubleVar, Checkbutton, BooleanVar
from os import path
from tkinter import Tk, NW, HORIZONTAL
from PIL import Image, ImageTk
from capture import Capture
from cropper import Cropper
from marker import Marker


class Program:
    blackKeyParameter = 0.9
    SIZE_X = 400
    SIZE_Y = 200
    capture = Capture()
    playing = False
    currentFrame = None
    middleC = None
    contours = None
    lowerBlack, higherBlack = [], []
    blackKeys = {}
    pressed = {}
    rel = []

    def __init__(self):
        self._initGUI()
        self.master.update()
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
        self._initPlayMarkGUI()
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

    def _initPlayMarkGUI(self):
        self.playOrStopButton = Button(self.frame, text='Play', padx=10, pady=1, command=self.playOrStop)
        self.playOrStopButton.place(x=self.SIZE_X + 5, y=135)
        Button(self.frame, text='Mark C', padx=10, pady=1, command=self.markKeyboardMiddle).place(
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

    def showProcessed(self, frame):
        canvas = Canvas(self.frame, width=self.SIZE_X, height=self.SIZE_X)
        canvas.place(x=0, y=self.SIZE_Y)
        photo = ImageTk.PhotoImage(image=Image.fromarray(cv.cvtColor(frame, cv.COLOR_BGR2RGB)).resize(
            (self.SIZE_X, self.SIZE_X), Image.ANTIALIAS))
        canvas.create_image(0, 0, image=photo, anchor=NW)

    def play(self):
        self.playing = True
        self.playOrStopButton['text'] = 'Stop'
        while self.playing:
            try:
                self._step()
            except FileNotFoundError:
                self.stop()

    def _step(self):
        self.capture.grab()
        if self.transcribing.get() and Frame:
            self.transcribe()
        self.showFrame()
        self.showPosition()

    def transcribe(self):
        frame = cv.cvtColor(self.capture.getCurrentFrameCropped(), cv.COLOR_BGR2GRAY)
        pressed = set()
        for key, points in self.blackKeys.items():
            dif = 0
            for x, y in points:
                if self.capture.grayBackground[y][x] != frame[y][x]:
                    dif += 1
            if dif/len(points) > 0.97:
                pressed.add(key)
        self.detectBlackPressed(pressed)

    def detectBlackPressed(self, pressed):
        for key in self.pressed.keys():
            if key not in pressed:
                self.releaseKey(key)
            else:
                pressed.remove(key)
        for key in pressed:
            self.pressed[key] = time.time()
        while self.rel:
            self.pressed.pop(self.rel.pop())

    def releaseKey(self, key):
        duration = time.time() - self.pressed[key]
        self.rel.append(key)
        print(f'{key} pressed for {duration}')

    def stop(self):
        self.playing = False
        self.playOrStopButton['text'] = 'Play'

    def showFrame(self):
        self.drawFrame()

    def drawFrame(self):
        if self.transcribing.get() and False:
            frame1 = cv.cvtColor(self.capture.background, cv.COLOR_BGR2GRAY)
            frame2 = cv.cvtColor(self.capture.getCurrentFrameCropped(), cv.COLOR_BGR2GRAY)
            self.currentFrame = self.capture.getSubtractedFramePhotoImage(frame1, frame2)
        else:
            self.currentFrame = self.capture.getCurrentFramePhotoImage()
        self.drawImage(self.currentFrame)

    def drawImage(self, image):
        self.canvas.create_image(0, 0, image=image, anchor=NW)
        self.frame.update()

    def segmentation(self):
        gray = cv.cvtColor(self.capture.background, cv.COLOR_BGR2GRAY)
        gray = cv.GaussianBlur(gray, (3, 3), 0)
        ret, thresh = cv.threshold(gray, 180, 255, cv.THRESH_BINARY_INV)
        kernel = np.ones((9, 9), np.uint8)
        opening = cv.morphologyEx(thresh, cv.MORPH_OPEN, kernel, iterations=1)
        dist_transform = cv.distanceTransform(opening, cv.DIST_L2, 5)
        ret, sure_fg = cv.threshold(dist_transform, 0.05 * dist_transform.max(), 255, 0)
        sure_fg = np.uint8(sure_fg)
        contours, hierarchy = cv.findContours(sure_fg, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
        self.contours = sorted(contours, key=lambda ctr: cv.boundingRect(ctr)[0])
        tmp = []
        aux = cv.contourArea(self.contours[2])
        for i in range(len(self.contours)):
            if cv.contourArea(self.contours[i]) < aux * 0.5:
                tmp.append(i)
        while tmp:
            self.contours.pop(tmp.pop())
        print(f'rozpoznanych {len(self.contours)} klaves')
        self.drawAndMapKeys()

    def drawAndMapKeys(self):
        colors = self.getColorsFromFile()
        img = self.capture.background.copy()
        for i in range(len(self.contours)):
            key = np.zeros((len(img), len(img[0]), 3), np.uint8)
            r, g, b = colors[i]
            M = cv.moments(self.contours[i])
            x = int(M['m10'] / M['m00'])
            y = int(M['m01'] / M['m00'])
            cv.drawContours(key, [self.contours[i]], -1, (r, g, b), -1)
            cv.drawContours(img, [self.contours[i]], -1, (r, g, b), -1)
            cv.putText(img, str(i), (x - 5, y + 100), cv.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
            cv.waitKey(0)
            self.assignKey(x, key)
        cv.imshow('contours', img)
        cv.waitKey(0)

    def assignKey(self, x, key):
        if self.capture.x_middle == 0:
            raise AttributeError()
        points = self.getNonZeroPoints(key)
        if x < self.capture.x_middle:
            self.lowerBlack.append(points)
        else:
            self.higherBlack.append(points)

    @staticmethod
    def getNonZeroPoints(image):
        result = []
        for i in range(len(image)):
            for j in range(len(image[0])):
                if any(image[i, j]):
                    result.append((j, i))
        return result

    def reset(self):
        raise NotImplementedError()

    def exportMIDI(self):
        raise NotImplementedError()

    def exportMusicXML(self):
        raise NotImplementedError()

    def setBackground(self):
        self.capture.background = self.capture.getCurrentFrameCropped()
        self.capture.grayBackground = cv.cvtColor(self.capture.background, cv.COLOR_BGR2GRAY)
        self.segmentation()
        self.mapKeys()

    def mapKeys(self):
        self.mapBlackKeys()
        self.mapWhiteKeys()

    def mapBlackKeys(self):
        self.mapBlackHigherKeys()
        self.mapBlackLowerKeys()

    def mapBlackHigherKeys(self):
        auxHigher = [2, 3, 2, 2, 3] * 5
        midiHigher = [61]
        for step in auxHigher:
            midiHigher.append(midiHigher[-1] + step)
        for key in zip(midiHigher, self.higherBlack):
            midiNumber, points = key
            self.blackKeys[midiNumber] = points

    def mapBlackLowerKeys(self):
        auxLower = [2, 2, 3, 2, 3] * 5
        midiLower = [58]
        for step in auxLower:
            midiLower.append(midiLower[-1] - step)
        self.lowerBlack.reverse()
        for key in zip(midiLower, self.lowerBlack):
            midiNumber, points = key
            self.blackKeys[midiNumber] = points

    def mapWhiteKeys(self):
        raise NotImplementedError()

    def playOrStop(self):
        if self.playing:
            self.stop()
        elif self.capture is not None and self.capture.isOpened():
            self.play()
        else:
            messagebox.showinfo('Chyba', 'Nie je načítané video.')

    def updatePosition(self, position):

        frameNumber = int(position) * self.fps
        self.capture.set(cv.CAP_PROP_POS_FRAMES, frameNumber)
        self.showFrame()

    def showPosition(self):
        tmp = self.position.get()
        self.position.set(self.capture.get(cv.CAP_PROP_POS_MSEC) / 1000)
        if round(self.position.get()) > round(tmp):
            print(self.position.get())

    def cropKeyboardArea(self):
        Cropper(self.capture)
        self.drawFrame()

    def markKeyboardMiddle(self):
        Marker(self.capture)

    @staticmethod
    def getColorsFromFile(filename='colors.txt'):
        with open(filename, 'r') as f:
            result = [map(int, i.split(' ')) for i in f.read().split('\n')]
            return result


if __name__ == '__main__':
    try:
        Program()
        exit(0)
    except FileExistsError:
        exit(1)
