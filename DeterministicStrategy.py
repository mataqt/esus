#-------------------------------------------------------------------------------
# Name:        DeterministicStrategy
# Purpose:     Perform the betting Strategy
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
#import abc

from datetime import date, datetime, timedelta
import MathUtils
import HistData as hist
import pandas as pd
import time
FUZZ = err.FUZZ

basePath = "D:\IT\Library\Python\Data"
sportID = "Tennis"
competitionID = "Dummy"
repoPath = basePath + "\\" + sportID + "\\" + competitionID
pathFileOut = basePath + "\\" + sportID + "\\Data_" + sportID + "_" + competitionID
repoGitPath = basePath + "\\" + sportID + "\\" +  "Dummy"


class cDeterministicStrategy:
    #class used to apply a betting strategy

    #the histData on which we perfor the strategy
    #strategyName: (str) the nale of the strategy, will be enhanced at a later stage
    #startDate, endDate: the period on which we perfor the strategy
    #weightParam: a weight param object
    # n_cpu: number of cpu the code can use. If -1, it will use the max number.
    # Useful when several params to regress
    def __init__(self,
                 histData,
                 modelType,
                 strategyType,
                 quantile,
                 startDate,
                 endDate ):
        self._histData = histData
        self._modelType = modelType
        self._startDate = startDate
        self._endDate = endDate
        self._quantile = 0
        self._strategyType = 0
        if modelType == 'quantile':
            self._quantile = quantile
            self._strategyType = strategyType
            if self._strategyType != 'Above' and self._strategyType != 'Below':
                err.ERROR( 'Strategytype ' + self._strategyType + ' is unkown ')
        else:
            err.ERROR( 'cStrategy not implemented for ' + self._modelType )
        err.REQUIRE( endDate >= startDate,
                    'The startDate cannot be after the endDate' )
        
        self._histData._adjustDates( startDate, endDate )
    
    #public
    #In this function, we run the betting strategy
    def runStrategy(self):
        #the strategy is run in two steps
        # 1) we generate a table with all the probabilities between startDate and endDate
        # 2) we compute the performance of the betting strategy
        df = self._histData._data
        
        Indicator = 0
        if self._strategyType == 'Above':
            Indicator = np.where ( df['probaAvgW_corrected'] >= self._quantile, 1.0, 0.0 )
        else:
            Indicator = np.where ( df['probaAvgW_corrected'] <= self._quantile, 1.0, 0.0 )
        results_avgCorr = Indicator / df['probaAvgW_corrected'] - 1.0
        results_avg = Indicator / df['probaAvgW'] - 1.0
        results_Max = Indicator / df['probaMaxW'] - 1.0
                                        
        
        strategyBaseName = self._strategyType + '_' +  str(quantile)
        print( strategyBaseName )
        
#        print( results_avgCorr.mean() )
#        print( results_avg.mean() )
        print( results_Max.mean() )
        
                             

    
    
try:
    startTime =time.time()
    importOne = True
    importGit = False
    loadChallenge = False
    loadFutures = False
    doParseTime = False
    myHistData = hist.cHistTennisData( repoPath, repoGitPath, competitionID, importOne,
                        importGit, loadChallenge, loadFutures, doParseTime )
    myHistData.exportData( pathFileOut )
    startDate = datetime(1995, 1, 1)
    endDate = datetime(2019, 1, 1)
    
    delta = 0.05
    quantiles = np.arange( delta, 0.5+delta, delta )
    strategyList = ['Above', 'Below']
    
    print( quantiles )
    
    for strategy in strategyList:
        for quantile in quantiles:
            myStrategy = cDeterministicStrategy( myHistData,
                                     'quantile',
                                     strategy,
                                     quantile,
                                     startDate,
                                     endDate )
            myStrategy.runStrategy()


#    myStrategy.runStrategy()
#    myHistData.exportData( pathFileOut )
    finalTime=time.time()-startTime
    print( 'Time' )
    print( finalTime )
    print( 'Job done in cStrategy' )
    
except err.cError as e:
    print( 'An error occured:', e.value )
