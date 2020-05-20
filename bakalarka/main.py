# pip install opencv-python MIDIUtil music21 Pillow tk

import numpy as np
import cv2 as cv

from capture import Capture
from gui import Gui
import multiprocessing
import time


class Program:
    blackKeyParameter = 0.9
    SIZE_X = 400
    SIZE_Y = 200
    capture = Capture()
    playing = False
    middleC = None
    blackKeys, whiteKeys = {}, {}
    blackAvgKeys, whiteAvgKeys = {}, {}
    blackPressed, whitePressed = {}, {}
    forExport = []
    segmentBlack, segmentWhite = None, None

    def __init__(self, debug=False):
        self.gui = Gui(self, self.SIZE_X, self.SIZE_Y)
        if debug:
            self.gui.load('../../dataset/cierne/samplek.mp4')
            self.capture.y_start, self.capture.y_end = 277, 432
            self.capture.x_start, self.capture.x_end = 200, 772
            self.capture.x_middle, self.capture.y_middle = 450, 390
            self.gui.thresh.set(180)
            self.gui.drawFrame()
        self.gui.master.mainloop()

    def __del__(self):
        if self.capture.isOpened():
            self.capture.release()

    def step(self):
        self.capture.grab()
        if self.gui.transcribing.get():
            s = time.time()
            self._transcribeBlack(self.blackKeys, self.blackPressed, 6)
            print(f'TranscribeBlack step processed in {time.time() - s} ms')
            s = time.time()
            self._transcribeWhite(self.whiteKeys, self.whitePressed, 4)
            print(f'TranscribeWhite step processed in {time.time() - s} ms')
        self.gui.showFrame()
        self.gui.showPosition()

    def _transcribeBlack(self, keys, previous_pressed, delta):
        pressed = set()
        for key, points in keys.items():
            if self._getChangeOfAvgBrightness(points, self.blackAvgKeys[key]) > delta:
                pressed.add(key)
        self.detectPressed(pressed, previous_pressed)

    def _getChangeOfAvgBrightness(self, points, b_brightness):
        frame = self.capture.getCurrentFrameGrayCropped()
        s = 0
        r = 0
        for x, y in points:
            if frame[y][x] == 255:
                r += 1
                continue
            s += frame[y][x]
        avg = s / (len(points) - r)
        return abs(avg - b_brightness)

    def _transcribeWhite(self, keys, previous_pressed, delta):
        pressed = set()
        for key, points in keys.items():
            if self._getChangeOfAvgBrightness(points, self.whiteAvgKeys[key]) > delta:
                pressed.add(key)
        self.detectPressed(pressed, previous_pressed)

    def detectPressed(self, pressed, previous_pressed):
        rel = []
        for key in previous_pressed.keys():
            if key not in pressed:
                self.releaseKey(key, previous_pressed)
                rel.append(key)
            else:
                pressed.remove(key)
        for key in pressed:
            previous_pressed[key] = self.capture.get(cv.CAP_PROP_POS_MSEC)
        while rel:
            previous_pressed.pop(rel.pop())

    def releaseKey(self, key, previous_pressed):
        duration = self.capture.get(cv.CAP_PROP_POS_MSEC) - previous_pressed[key]
        if duration > 20:
            self.forExport.append((key, duration, previous_pressed[key]))
            print(f'{key} pressed for {duration} ms')


if __name__ == '__main__':
    try:
        Program()
        exit(0)
    except FileExistsError:
        exit(1)
