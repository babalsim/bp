import cv2 as cv
from PIL import Image, ImageTk


class Capture(cv.VideoCapture):
    background, grayBackground = None, None
    x_start, y_start, x_end, y_end = 0, 0, 0, 0
    sizeX, sizeY = 0, 0
    x_middle, y_middle = 0, 0
    flip, handFilter = None, None

    def __init__(self, filename=None):
        if filename is not None:
            super().__init__(filename)
            self.grab()
            self.setDefaultKeyArea()
        else:
            super().__init__()

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
        if self.flip.get():
            frame = cv.flip(frame, -1)
        return frame

    def getCurrentFrameCropped(self):
        frame = self.getCurrentFrame()
        cropped = frame[self.y_start:self.y_end, self.x_start:self.x_end]
        if self.handFilter.get():
            cropped = self.filterHands(cropped)
        return cropped

    def getCurrentFrameGrayCropped(self):
        return cv.cvtColor(self.getCurrentFrameCropped(), cv.COLOR_BGR2GRAY)

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

    @staticmethod
    def filterHands(frame):
        for i in range(len(frame)):
            for j in range(len(frame[0])):
                b, g, r = map(int, frame[i][j])
                if r > 95 and g > 40 and b > 20 and r > g and r > b:
                    frame[i][j] = [255, 255, 255]
        return frame

    @staticmethod
    def getSubtractedFrame(frame1, frame2):
        return frame1 - frame2

    def getSubtractedFramePhotoImage(self, frame1, frame2):
        frame = self.getSubtractedFrame(frame1, frame2)
        return ImageTk.PhotoImage(image=Image.fromarray(frame).resize((self.sizeX, self.sizeY), Image.ANTIALIAS))

    def getPhotoImageFromFrame(self, frame):
        return ImageTk.PhotoImage(image=Image.fromarray(frame).resize((self.sizeX, self.sizeY), Image.ANTIALIAS))
