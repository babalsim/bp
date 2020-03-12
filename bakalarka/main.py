# pip install opencv-python MIDIUtil tk

import numpy as np
import cv2 as cv
import time
from tkinter import filedialog, messagebox, NW
from os import path
from capture import Capture
from cropper import Cropper
from marker import Marker
from gui import Gui


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

    def __init__(self, debug=False):
        self.gui = Gui(self, self.SIZE_X, self.SIZE_Y)
        # if debug:
        #     self.load('../dataset/samplek.mp4')
        #     self.capture.y_start, self.capture.y_end = 273, 432
        #     self.capture.x_start, self.capture.x_end = 200, 772
        #     self.capture.x_middle, self.capture.y_middle = 450, 390
        #     self.drawFrame()
        #     self.setBackground()
        self.gui.master.update()
        self.gui.master.mainloop()

    def __del__(self):
        if self.capture.isOpened():
            self.capture.release()

    def load(self, filename=''):
        try:
            if not filename:
                filename = filedialog.askopenfilename(title="Vyberte súbor")
            if not path.isfile(filename):
                raise FileNotFoundError
            self.capture.setVideoFile(filename)
            self.capture.setCanvasSize(self.SIZE_X, self.SIZE_Y)
            self.gui.setTimeControlGUI()
            self.showFrame()
        except FileNotFoundError:
            messagebox.showinfo("Chyba", "Súbor sa nepodarilo prečítať")

    def step(self):
        self.capture.grab()
        if self.gui.transcribing.get():
            self.transcribe()
        self.showFrame()
        self.gui.showPosition()

    def transcribe(self):
        frame = cv.cvtColor(self.capture.getCurrentFrameCropped(), cv.COLOR_BGR2GRAY)
        pressed = set()
        for key, points in self.blackKeys.items():
            dif = 0
            for x, y in points:
                if self.capture.grayBackground[y][x] != frame[y][x]:
                    dif += 1
            if dif / len(points) > 0.97:
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

    def showFrame(self):
        self.drawFrame()

    def drawFrame(self):
        if self.gui.transcribing.get() and False:
            frame1 = cv.cvtColor(self.capture.background, cv.COLOR_BGR2GRAY)
            frame2 = cv.cvtColor(self.capture.getCurrentFrameCropped(), cv.COLOR_BGR2GRAY)
            self.currentFrame = self.capture.getSubtractedFramePhotoImage(frame1, frame2)
        else:
            self.currentFrame = self.capture.getCurrentFramePhotoImage()
        self.drawImage(self.currentFrame)

    def drawImage(self, image):
        self.gui.canvas.create_image(0, 0, image=image, anchor=NW)
        self.gui.frame.update()

    def segmentation(self, t=180):
        gray = cv.cvtColor(self.capture.background, cv.COLOR_BGR2GRAY)
        gray = cv.GaussianBlur(gray, (3, 3), 0)
        ret, thresh = cv.threshold(gray, t, 255, cv.THRESH_BINARY_INV)
        # ret, thresh = cv.adaptiveThreshold(gray,255,cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, 3)
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
        Program(True)
        exit(0)
    except FileExistsError:
        exit(1)
