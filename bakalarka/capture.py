from tkinter import messagebox

import cv2 as cv
from PIL import Image, ImageTk
import numpy as np


class Capture(cv.VideoCapture):
    background = None
    cropping, mouseCropping = False, False
    x_start, y_start, x_end, y_end = 0, 0, 0, 0
    sizeX, sizeY = 0, 0

    def __init__(self, filename=None):
        if filename is not None:
            super().__init__(filename)
            self.grab()
            self.setDefaultKeyArea()

    def setVideoFile(self, filename):
        self.__init__(filename)

    def setCanvasSize(self, x=400, y=200):
        self.sizeX, self.sizeY = x, y

    def setDefaultKeyArea(self):
        frame = self.getCurrentFrame()
        self.x_start, self.y_start = 0, 0
        self.x_end, self.y_end = len(frame[0]), len(frame)

    def getCurrentFrame(self):
        _, frame = self.retrieve()
        return frame

    def getCurrentFrameCropped(self):
        frame = self.getCurrentFrame()
        cropped = frame[self.y_start:self.y_end, self.x_start:self.x_end]
        return cropped

    def getNextFrame(self):
        self.grab()
        return self.getCurrentFrameCropped()

    def getCurrentFrameRGB(self):
        frame = self.getCurrentFrameCropped()
        return cv.cvtColor(frame, cv.COLOR_BGR2RGB)

    def getNextFrameRGB(self):
        self.grab()
        return self.getCurrentFrameRGB()

    def getCurrentFramePhotoImage(self):
        frameRGB = self.getCurrentFrameRGB()
        return ImageTk.PhotoImage(image=Image.fromarray(frameRGB).resize((self.sizeX, self.sizeY), Image.ANTIALIAS))

    def getNextFramePhotoImage(self):
        self.grab()
        return self.getCurrentFramePhotoImage()
