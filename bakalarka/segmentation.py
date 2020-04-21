import cv2 as cv
from segmentBlack import SegmentBlack
from segmentWhite import SegmentWhite


class Segmentation:
    blackKeysYBound = None

    def __init__(self, main):
        self.main = main
        self.segmentBlack = SegmentBlack(self)
        self.segmentWhite = SegmentWhite(self)
        self._mapKeys()
        cv.waitKey(0)

    def _mapKeys(self):
        self.segmentBlack.mapBlackKeys()
        self.segmentWhite.mapWhiteKeys()

    @staticmethod
    def getColorsFromFile(filename='colors.txt'):
        with open(filename, 'r') as f:
            result = [map(int, i.split(' ')) for i in f.read().split('\n')]
            return result

    @staticmethod
    def filterContours(contours):
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
    def showSegmentedKeys(img, window):
        cv.imshow(window, img)

    @staticmethod
    def getNonZeroPoints(image):
        result = []
        for i in range(len(image)):
            for j in range(len(image[0])):
                if any(image[i, j]):
                    result.append((j, i))
        return result
