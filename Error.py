#-------------------------------------------------------------------------------
# Name:        Error
# Purpose:     Handling error functionalities
#
# Author:      St?phane
#
# Created:     07/02/2017
# Copyright:   (c) St?phane 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

FUZZ = 0.000001
class cError(Exception):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

#Throws an error
def ERROR( errorMessage ):
    raise cError( errorMessage )

#If not true, throws an error
def REQUIRE( boolTest, errorMessage ):
    if not boolTest:
        ERROR( errorMessage )

