import cv2
import numpy as np

###################################################################################################
class PossiblePlate:

    # constructor #################################################################################
    def __init__(self):
        self.imgPlate = None
        self.imgGrayscale = None
        self.imgThresh = None
        self.imgStream = None

        self.rrLocationOfPlateInScene = None

        self.strChars = ""
    # end constructor

# end class




