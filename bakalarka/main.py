# this code is published in github repository https://github.com/babalsim/bp with instructions to run
# to run this project you need following libraries: opencv-python MIDIUtil music21 Pillow tk

import time

import cv2 as cv

from capture import Capture
from gui import Gui


class Program:
    blackKeyParameter = 0.9
    SIZE_X = 400
    SIZE_Y = 200
    blackBrightnessChange = 6
    whiteBrightnessChange = 4
    capture = Capture()
    playing = False
    middleC = None
    blackKeys, whiteKeys = {}, {}
    blackAvgKeys, whiteAvgKeys = {}, {}
    blackPressed, whitePressed = {}, {}
    forExport = []
    segmentBlack, segmentWhite = None, None

    def __init__(self, demo=False, demo_data=()):
        self.gui = Gui(self, self.SIZE_X, self.SIZE_Y)
        if demo:
            self.gui.load(demo_data[0])
            self.capture.y_start, self.capture.y_end = demo_data[1], demo_data[2]
            self.capture.x_start, self.capture.x_end = demo_data[3], demo_data[4]
            self.capture.x_middle, self.capture.y_middle = demo_data[5], demo_data[6]
            self.gui.position.set(demo_data[7])
            self.gui.updatePosition(demo_data[7])
        self.gui.master.mainloop()

    def __del__(self):
        if self.capture.isOpened():
            self.capture.release()

    def step(self):
        self.capture.grab()
        if self.gui.transcribing.get():
            s = time.time()
            self._transcribeBlack(self.blackKeys, self.blackPressed, self.blackBrightnessChange)
            print(f'TranscribeBlack step processed in {time.time() - s} ms')
            s = time.time()
            self._transcribeWhite(self.whiteKeys, self.whitePressed, self.whiteBrightnessChange)
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
        if duration > 100:
            self.forExport.append((key, duration, previous_pressed[key]))
            print(f'{key} pressed for {duration} ms')


if __name__ == '__main__':
    Program()
