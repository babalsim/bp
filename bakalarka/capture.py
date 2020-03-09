import cv2 as cv
from PIL import Image, ImageTk


class Capture(cv.VideoCapture):
    background, grayBackground = None, None
    x_start, y_start, x_end, y_end = 0, 0, 0, 0
    sizeX, sizeY = 0, 0
    x_middle, y_middle = 0, 0

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

    def removeHands(self, frame):
        for i in range(self.y_start, self.y_end):
            for j in range(self.x_start, self.x_end):
                r, g, b = map(int, frame[i][j])
                if r > 65 and g > 40 and b > 30:
                    # and max(r, g, b) - min(r, g, b) > 15
                    #  and r > g and r > b):
                    frame[i][j] = [255, 0, 0]
        return frame

    def getSubtractedFramePhotoImage(self, frame1, frame2):
        frame = frame1 - frame2
        return ImageTk.PhotoImage(image=Image.fromarray(frame).resize((self.sizeX, self.sizeY), Image.ANTIALIAS))
