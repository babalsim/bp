from tkinter import messagebox
import cv2 as cv


class Cropper:
    def __init__(self, capture):
        self.capture = capture
        self.image = self.capture.getCurrentFrame()
        self.cropping = True
        self.mouseDrag = False
        self.cropKeyboard()

    def cropKeyboard(self):
        cv.namedWindow('image')
        cv.setMouseCallback('image', self.mouseCrop)
        cv.imshow('image', self.image)
        while self.cropping:
            self._refresh()

    def _refresh(self):
        i = self.image.copy()
        cv.rectangle(i, (self.capture.x_start, self.capture.y_start), (self.capture.x_end, self.capture.y_end),
                     (255, 0, 0), 2)
        cv.imshow('image', i)
        cv.waitKey(1)

    def postCropKeyboard(self):
        self.askForCrop()
        cv.destroyAllWindows()

    def askForCrop(self):
        message = messagebox.askquestion('Vystrihnutie klaviatúry', 'Je klaviatúra vystrihnutá správne')
        if message != 'yes':
            self.capture.setDefaultKeyArea()

    def fixKeyArea(self):
        if self.capture.y_start > self.capture.y_end:
            self.capture.y_start, self.capture.y_end = self.capture.y_end, self.capture.y_start
        if self.capture.x_start > self.capture.x_end:
            self.capture.x_start, self.capture.x_end = self.capture.x_end, self.capture.x_start

    def mouseCrop(self, event, x, y, flags, param):
        if event == cv.EVENT_LBUTTONDOWN:
            self._click(x, y)
        elif event == cv.EVENT_MOUSEMOVE:
            self._drag(x, y)
        elif event == cv.EVENT_LBUTTONUP:
            self._release(x, y)

    def _click(self, x, y):
        self.capture.x_start, self.capture.y_start, self.capture.x_end, self.capture.y_end = x, y, x, y
        self.mouseDrag = True

    def _drag(self, x, y):
        if self.mouseDrag:
            self.capture.x_end, self.capture.y_end = x, y

    def _release(self, x, y):
        self.mouseDrag = False
        self.cropping = False
        self.capture.x_end, self.capture.y_end = x, y
        self.fixKeyArea()
        frame = self.capture.getCurrentFrame()
        roi = frame[self.capture.y_start:self.capture.y_end, self.capture.x_start:self.capture.x_end]
        cv.imshow("Cropped", roi)
        self.postCropKeyboard()
