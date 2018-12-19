import Preprocess
import cv2
import pytesseract as pytess


def detectNumberFromPlate(plate):
    plate.imgThresh = Preprocess.preprocess(plate.imgPlate)

    plate.imgThresh = cv2.resize(plate.imgThresh, (0, 0), fx=1.6, fy=1.6)
    thresholdValue, plate.imgThresh = cv2.threshold(plate.imgThresh, 0.0, 255.0, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    return pytess.image_to_string(plate.imgThresh,"carplate")

