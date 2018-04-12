#-------------------------------------------------------------------------------
# Name:        MathUtils
# Purpose:     Some util functions
#
# Author:      Matars
#
#
# Created:     02/04/2017
# Copyright:   (c) St?phane 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import numpy as np
import Error as err
FUZZ = err.FUZZ

#return a boolean. True if the difference is below the tolerance
def equal( a, b , tol = FUZZ ):
    if np.absolute( a - b ) < tol:
        return True
    return False

#return an array with the dates from startDate to endDate
#for a given frequency
#the endDate is include
def dateVec( startDate, endDate, freqDays ):
    currentDate = startDate
    while currentDate <= endDate:
        yield currentDate
        currentDate += freqDays
    