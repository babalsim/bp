# pip install opencv-python MIDIUtil music21 Pillow tk

import numpy as np
import cv2 as cv
import time
from tkinter import filedialog, messagebox, NW
from os import path, remove

from music21 import converter

from capture import Capture
from cropper import Cropper
from marker import Marker
from gui import Gui
from midiutil import MIDIFile


class Program:
    blackKeyParameter = 0.9
    SIZE_X = 400
    SIZE_Y = 200
    capture = Capture()
    playing = False
    currentFrame = None
    middleC = None
    contours = None
    lowerBlack, higherBlack, lowerWhite, higherWhite = [], [], [], []
    blackKeys, whiteKeys = {}, {}
    pressed = {}
    rel = []
    forExport = []

    def __init__(self, debug=False):
        self.gui = Gui(self, self.SIZE_X, self.SIZE_Y)
        if debug:
            self.load('../dataset/samplek.mp4')
            self.capture.y_start, self.capture.y_end = 277, 432
            self.capture.x_start, self.capture.x_end = 200, 772
            self.capture.x_middle, self.capture.y_middle = 450, 390
            self.drawFrame()
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
            self.pressed[key] = self.capture.get(cv.CAP_PROP_POS_MSEC)
        while self.rel:
            self.pressed.pop(self.rel.pop())

    def releaseKey(self, key):
        duration = self.capture.get(cv.CAP_PROP_POS_MSEC) - self.pressed[key]
        self.rel.append(key)
        self.forExport.append((key, duration, self.pressed[key]))
        print(f'{key} pressed for {duration} ms')

    def showFrame(self):
        self.drawFrame()

    def drawFrame(self):
        if self.gui.transcribing.get() and False: #####################################################  to do
            frame1 = cv.cvtColor(self.capture.background, cv.COLOR_BGR2GRAY)
            frame2 = cv.cvtColor(self.capture.getCurrentFrameCropped(), cv.COLOR_BGR2GRAY)
            self.currentFrame = self.capture.getSubtractedFramePhotoImage(frame1, frame2)
        else:
            self.currentFrame = self.capture.getCurrentFramePhotoImage()
        self.drawImage(self.currentFrame)

    def drawImage(self, image):
        self.gui.canvas.create_image(0, 0, image=image, anchor=NW)
        self.gui.frame.update()

    # noinspection DuplicatedCode
    def _getBlackKeysContours(self):
        gray = cv.cvtColor(self.capture.background, cv.COLOR_BGR2GRAY)
        gray = cv.GaussianBlur(gray, (3, 3), 0)
        ret, thresh = cv.threshold(gray, self.gui.thresh.get(), 255, cv.THRESH_BINARY_INV)
        kernel = np.ones((5, 5), np.uint8)
        thresh = cv.dilate(thresh, kernel, iterations=1)
        thresh = cv.erode(thresh, kernel, iterations=1)
        dist_transform = cv.distanceTransform(thresh, cv.DIST_LABEL_PIXEL, 5)
        ret, sure_fg = cv.threshold(dist_transform, 0.05 * dist_transform.max(), 255, 0)
        sure_fg = np.uint8(sure_fg)
        contours, hierarchy = cv.findContours(sure_fg, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
        return contours

    # noinspection DuplicatedCode
    def _getWhiteKeysContours(self):
        croppedKeys = self.capture.background[0:self.blackKeysYBound, 0:len(self.capture.background[0])]
        gray = cv.cvtColor(croppedKeys, cv.COLOR_BGR2GRAY)
        gray = cv.GaussianBlur(gray, (3, 3), 0)
        ret, thresh = cv.threshold(gray, self.gui.thresh.get(), 255, cv.THRESH_BINARY)
        kernel = np.ones((5, 5), np.uint8)
        thresh = cv.dilate(thresh, kernel, iterations=1)
        dist_transform = cv.distanceTransform(thresh, cv.DIST_LABEL_PIXEL, 5)
        ret, sure_fg = cv.threshold(dist_transform, 0.05 * dist_transform.max(), 255, 0)
        sure_fg = np.uint8(sure_fg)
        contours, hierarchy = cv.findContours(sure_fg, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_NONE)
        contours = self._splitWideContours(contours)
        return contours

    def _blackKeysSegmentation(self):
        rawContours = self._getBlackKeysContours()
        contours = self._filterContours(rawContours)
        self._setBlackKeysYBound(contours)
        contours.sort(key=lambda ctr: cv.boundingRect(ctr)[0])
        print(f'Detected {len(contours)} Black Keys')
        self.drawAndMapKeys(contours, True)

    def _setBlackKeysYBound(self, contours):
        averageYBound = sum([cv.boundingRect(cnt)[3] for cnt in contours]) / len(contours)
        self.blackKeysYBound = int(averageYBound * 0.95)

    def _whiteKeysSegmentation(self):
        rawContours = self._getWhiteKeysContours()
        contours = self._filterContours(self._splitWideContours(rawContours))
        contours.sort(key=lambda ctr: cv.boundingRect(ctr)[0])
        print(f'Detected {len(contours)} White Keys')
        self.drawAndMapKeys(contours, False)

    def _splitWideContours(self, contours):
        averageWidth = sum([cv.boundingRect(cnt)[2] for cnt in contours]) / len(contours)
        biggerContours = [cnt for cnt in enumerate(contours) if cv.boundingRect(cnt[1])[2] > averageWidth * 1.5]
        while biggerContours:
            index, cnt = biggerContours.pop()
            contours.pop(index)
            a, b = self._splitContour(cnt)
            contours.append(a)
            contours.append(b)
        return contours

    def _splitContour(self, cnt):
        a, b = [], []
        for point in cnt:
            box = sorted(cv.boxPoints(cv.minAreaRect(cnt)).tolist(), key=lambda x: x[1])
            x1, x2 = self._getBounds(box)
            x, y = point[0]
            if x < x1 and y < 25 or x < x2 and y > 25 or x in range(min(round(x1), round(x2))):
                a.append([[x, y]])
            else:
                b.append([[x, y]])
        return np.asarray(a), np.asarray(b)

    @staticmethod
    def _getBounds(box):
        lower, higher = box[:2], box[2:]
        x1 = (lower[0][0] + lower[1][0]) / 2
        x2 = (higher[0][0] + higher[1][0]) / 2
        return x1, x2

    @staticmethod
    def _filterContours(contours):
        forRemove = []
        averageArea = sum([cv.contourArea(cnt) for cnt in contours]) / len(contours)
        thresh = averageArea * 0.5
        for i in range(len(contours)):
            if cv.contourArea(contours[i]) < thresh:
                forRemove.append(i)
        while forRemove:
            contours.pop(forRemove.pop())
        return contours

    def segmentation(self):
        self._blackKeysSegmentation()
        self._whiteKeysSegmentation()
        cv.waitKey(0)

    def drawAndMapKeys(self, contours, black):
        colors = self.getColorsFromFile()
        img = self.capture.background.copy()
        for i in range(len(contours)):
            r, g, b = colors[i]
            key = np.zeros((len(img), len(img[0]), 3), np.uint8)
            M = cv.moments(contours[i])
            x = int(M['m10'] / M['m00'])
            y = int(M['m01'] / M['m00'])
            cv.drawContours(key, [contours[i]], -1, (r, g, b), -1)
            cv.drawContours(img, [contours[i]], -1, (r, g, b), -1)
            cv.putText(img, str(i), (x - 5, y + 100), cv.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
            if black:
                self.assignBlackKey(x, key)
            else:
                self.assignWhiteKey(x, key)
        self.showSegmentedKeys(img, black)

    @staticmethod
    def showSegmentedKeys(img, black):
        if black:
            cv.imshow('Black Keys', img)
        else:
            cv.imshow('White Keys', img)

    def assignBlackKey(self, x, key):
        if self.capture.x_middle == 0:
            raise AttributeError()
        points = self.getNonZeroPoints(key)
        if x < self.capture.x_middle:
            self.lowerBlack.append(points)
        else:
            self.higherBlack.append(points)

    def assignWhiteKey(self, x, key):
        if self.capture.x_middle == 0:
            raise AttributeError()
        points = self.getNonZeroPoints(key)
        if x < self.capture.x_middle:
            self.lowerWhite.append(points)
        else:
            self.higherWhite.append(points)

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

    def export(self):
        self.gui.stop()
        fileTypes = [('MIDI File', '.midi'), ('MusicXML File', '.musicxml')]
        filename = filedialog.asksaveasfilename(filetypes=fileTypes, defaultextension='.midi')
        if '.midi' in filename:
            self._exportMIDI(filename)
        elif '.musicxml' in filename:
            self._exportMusicXML(filename)
        else:
            raise RuntimeError('Chosen Wrong File Extension')
        print(f'Successfully Exported To {filename}')

    def _exportMIDI(self, filename='.tmpMidiFileForExport'):
        self.gui.stop()
        midi = MIDIFile(1)
        midi.addTempo(0, 0, self.gui.tempo.get())
        for pitch, duration, start in self.forExport:
            midi.addNote(0, 0, pitch+self.gui.transpose.get(), start/1000, duration/1000, 100)
        with open(filename, 'wb') as file:
            midi.writeFile(file)

    def _exportMusicXML(self, filename):
        self._exportMIDI()
        score = converter.parse('.tmpMidiFileForExport', format='midi')
        remove('.tmpMidiFileForExport')
        score.write('musicxml', filename)

    def setBackground(self):
        self.capture.background = self.capture.getCurrentFrameCropped()
        self.capture.grayBackground = cv.cvtColor(self.capture.background, cv.COLOR_BGR2GRAY)
        self.segmentation()
        self.mapKeys()

    def mapKeys(self):
        self.mapBlackKeys()
        self.mapWhiteKeys()

    def mapBlackKeys(self):
        self._mapBlackHigherKeys()
        self._mapBlackLowerKeys()

    def _mapBlackHigherKeys(self):
        auxHigher = [2, 3, 2, 2, 3] * 5
        midiHigher = [61]
        for step in auxHigher:
            midiHigher.append(midiHigher[-1] + step)
        for key in zip(midiHigher, self.higherBlack):
            midiNumber, points = key
            self.blackKeys[midiNumber] = points

    def _mapBlackLowerKeys(self):
        auxLower = [2, 2, 3, 2, 3] * 5
        midiLower = [58]
        for step in auxLower:
            midiLower.append(midiLower[-1] - step)
        self.lowerBlack.reverse()
        for key in zip(midiLower, self.lowerBlack):
            midiNumber, points = key
            self.blackKeys[midiNumber] = points

    def mapWhiteKeys(self):
        self._mapWhiteHigherKeys()
        self._mapWhiteLowerKeys()

    def _mapWhiteHigherKeys(self):
        auxHigher = [2, 1, 2, 2, 2, 1, 2] * 5
        midiHigher = [62]
        for step in auxHigher:
            midiHigher.append(midiHigher[-1] + step)
        for key in zip(midiHigher, self.higherBlack):
            midiNumber, points = key
            self.whiteKeys[midiNumber] = points

    def _mapWhiteLowerKeys(self):
        auxLower = [1, 2, 2, 2, 1, 2, 2] * 5
        midiLower = [60]
        for step in auxLower:
            midiLower.append(midiLower[-1] - step)
        self.lowerWhite.reverse()
        for key in zip(midiLower, self.lowerWhite):
            midiNumber, points = key
            self.whiteKeys[midiNumber] = points

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

    def show(self, img):
        cv.imshow('tmp', img)
        cv.waitKey(0)

if __name__ == '__main__':
    try:
        Program(True)
        exit(0)
    except FileExistsError:
        exit(1)
