# pip install opencv-python MIDIUtil music21 Pillow tk

import numpy as np
import cv2 as cv
import time
from tkinter import filedialog
from os import remove

from music21 import converter

from capture import Capture
from gui import Gui
from midiutil import MIDIFile
from segmentation import Segmentation


class Program:
    blackKeyParameter = 0.9
    SIZE_X = 400
    SIZE_Y = 200
    capture = Capture()
    playing = False
    middleC = None
    blackKeys, whiteKeys = {}, {}
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
            self.gui.drawFrame()
        self.gui.master.mainloop()

    def __del__(self):
        if self.capture.isOpened():
            self.capture.release()

    def step(self):
        self.capture.grab()
        if self.gui.transcribing.get():
            self.transcribe(self.blackKeys, self.blackPressed, 0.97)
            self.transcribe(self.whiteKeys, self.whitePressed, 0.95)
        self.gui.showFrame()
        self.gui.showPosition()

    def transcribe(self, keys, previous_pressed, delta=0.97):
        frame = cv.cvtColor(self.capture.getCurrentFrameCropped(), cv.COLOR_BGR2GRAY)
        pressed = set()
        for key, points in keys.items():
            dif = 0
            for x, y in points:
                if self.capture.grayBackground[y][x] != frame[y][x]:
                    dif += 1
            if dif / len(points) > delta:
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
        self.forExport.append((key, duration, previous_pressed[key]))
        print(f'{key} pressed for {duration} ms')

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


if __name__ == '__main__':
    try:
        Program(True)
        exit(0)
    except FileExistsError:
        exit(1)
