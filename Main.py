import os

import cv2

import DetectNumber
import DetectPlate
import IRSensorThread
import UpdateSlotInPark

from threading import Thread
import threading
import pytesseract as pytess

# module level variables ##########################################################################
SCALAR_BLACK = (0.0, 0.0, 0.0)
SCALAR_WHITE = (255.0, 255.0, 255.0)
SCALAR_YELLOW = (0.0, 255.0, 255.0)
SCALAR_GREEN = (0.0, 255.0, 0.0)
SCALAR_RED = (0.0, 0.0, 255.0)

showSteps = False

def main():
    # print("\nstart \n\n")
    # frame = cv2.imread("testImg/20.jpg")  # open image
    #
    # if frame is None:  # if image was not read successfully
    #     print("\nerror: image not read from file \n\n")  # print error message to std out
    #     os.system("pause")  # pause so user can see error message
    #     return  # and exit program
    # end if
    # while True:
    #     video_capture = cv2.VideoCapture(0)
    #     if video_capture.isOpened():  # try to get the first frame
    #         rval, frame = video_capture.read()
    #     else:
    #         rval = False
    #     while rval:
    #         ret, frame = video_capture.read()
    #         listOfPossiblePlates = DetectPlate.dectecPlatesInImage(frame)
    #         if len(listOfPossiblePlates) > 0:
    #             listOfPossiblePlates.sort(key=lambda possiblePlate: len(possiblePlate.strChars), reverse=True)
    #             number = DetectNumber.detectNumberFromPlate(listOfPossiblePlates[0])
    #             print(number)
    #             # cv2.imshow("video", listOfPossiblePlates[0].imgThresh)
    #             cv2.imshow("video2", listOfPossiblePlates[0].imgStream)
    #             # cv2.imwrite("img.png",listOfPossiblePlates[0].imgThresh)
    #             # cv2.waitKey(0)
    #         else:
    #             cv2.imshow("video2", frame)
    #         # end if
    #         key = cv2.waitKey(15)
    #     # end while
    # return
    tUpdateSlot = threading.Thread(target=UpdateSlotInPark.updateAvailableSlotToDB(), args=())
    tIRSensor = threading.Thread(target=IRSensorThread.objectByIRSensorDetection(), args=())
    tUpdateSlot.start()
    tIRSensor.start()

    return


# end funtion
if __name__ == "__main__":
    main()
