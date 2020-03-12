from tkinter import messagebox
import cv2 as cv


class Marker:
    def __init__(self, capture):
        self.capture = capture
        self.image = self.capture.getCurrentFrame()
        self.marking()

    def marking(self):
        cv.namedWindow('image')
        cv.setMouseCallback('image', self.mouseMark)
        cv.imshow('image', self.image)

    def postMarkKey(self):
        self.askForMark()
        cv.destroyAllWindows()

    def askForMark(self):
        message = messagebox.askquestion('Označenie klávesu', 'Je kláves označený správne')
        if message != 'yes':
            self.capture.x_middle, self.capture.y_middle = None, None

    def mouseMark(self, event, x, y, flags, param):
        if event == cv.EVENT_LBUTTONDOWN:
            self.capture.x_middle, self.capture.y_middle = x, y
            print('x', self.capture.x_middle, 'y', self.capture.y_middle)
            cv.circle(self.image, (x, y), 5, (255, 0, 0), 5)
            cv.imshow('image', self.image)
            self.postMarkKey()
