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
from segmentBlack import SegmentBlack
from segmentWhite import SegmentWhite


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
    segmentBlack, segmentWhite = None, None

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
                self.releaseBlackKey(key)
            else:
                pressed.remove(key)
        for key in pressed:
            self.pressed[key] = self.capture.get(cv.CAP_PROP_POS_MSEC)
        while self.rel:
            self.pressed.pop(self.rel.pop())

    def releaseBlackKey(self, key):
        duration = self.capture.get(cv.CAP_PROP_POS_MSEC) - self.pressed[key]
        self.rel.append(key)
        self.forExport.append((key, duration, self.pressed[key]))
        print(f'{key} pressed for {duration} ms')

    def showFrame(self):
        self.drawFrame()

    def drawFrame(self):
        if self.gui.transcribing.get() and False:  #####################################################  to do
            frame1 = cv.cvtColor(self.capture.background, cv.COLOR_BGR2GRAY)
            frame2 = cv.cvtColor(self.capture.getCurrentFrameCropped(), cv.COLOR_BGR2GRAY)
            self.currentFrame = self.capture.getSubtractedFramePhotoImage(frame1, frame2)
        else:
            self.currentFrame = self.capture.getCurrentFramePhotoImage()
        self.drawImage(self.currentFrame)

    def drawImage(self, image):
        self.gui.canvas.create_image(0, 0, image=image, anchor=NW)
        self.gui.frame.update()

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
        thresh = averageArea * 0.6
        for i in range(len(contours)):
            if cv.contourArea(contours[i]) < thresh:
                forRemove.append(i)
        while forRemove:
            contours.pop(forRemove.pop())
        return contours

    @staticmethod
    def showSegmentedKeys(img, black):
        if black:
            cv.imshow('Black Keys', img)
        else:
            cv.imshow('White Keys', img)

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
            midi.addNote(0, 0, pitch + self.gui.transpose.get(), start / 1000, duration / 1000, 100)
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

    def segmentation(self):
        self.segmentBlack = SegmentBlack(self)
        self.segmentWhite = SegmentWhite(self)
        cv.waitKey(0)

    def mapKeys(self):
        self.segmentBlack.mapBlackKeys()
        self.segmentWhite.mapWhiteKeys()

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
        Program()
        exit(0)
    except FileExistsError:
        exit(1)
