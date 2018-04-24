#-------------------------------------------------------------------------------
# Name:        Strategy
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
import Regression as reg
from datetime import date, datetime, timedelta
import MathUtils
import HistData as hist
import pandas as pd
import time
FUZZ = err.FUZZ

basePath = "D:\IT\Library\Python\esus\Data"
sportID = "Tennis"
competitionID = "Dummy"
repoPath = basePath + "\\" + sportID + "\\" + competitionID
pathFileOut = basePath + "\\" + sportID + "\\Data_" + sportID + "_" + competitionID
repoGitPath = basePath + "\\" + sportID + "\\" +  "Dummy"


class cStrategy:
    #class used to apply a betting strategy

    #the histData on which we perform the strategy
    #strategyName: (str) the name of the strategy, will be enhanced at a later stage
    #startDate, endDate: the period on which we perfor the strategy
    #weightParam: a weight param object
    # n_cpu: number of cpu the code can use. If -1, it will use the max number.
    # Useful when several params to regress
    def __init__(self,
                 histData,
                 modelType,
                 strategyName,
                 startDate,
                 endDate,
                 weightParam,              
                 n_cpu = -1 ):
        self._histData = histData
        self._modelType = modelType
        self._startDate = startDate
        self._endDate = endDate
        self._weightParam = weightParam
        self._n_cpu = n_cpu
        self._regressor = reg.cRegression()
        if modelType == 'logit':
            self._regressor = reg.cLinearRegression_logit( center = True,
                                                         reduce = True,
                                                         normalize = False,
                                                         fit_intercept = True,
                                                         n_cpu = 1, 
                                                         penalty = 'l2', 
                                                         smart_guess = False,
                                                         multi_class = 'ovr' )
        else:
            err.ERROR( 'cStrategy not implemented for ' + self._modelType )
        err.REQUIRE( endDate >= startDate,
                    'The startDate cannot be after the endDate' )
    
    #public
    #In this function, we run the betting strategy
    def runStrategy(self):
        #the strategy is run in two steps
        # 1) we generate a table with all the probabilities between startDate and endDate
        # 2) we compute the performance of the betting strategy
        self._generateProbas()
        
    #private
    #generate a table woth all the probas day by day.
    #the table is used at a later stage to perform the strategies
    def _generateProbas(self):
        timeColumnID = self._histData.getTimeColumnID()
        

        myProb = {}
        myProb['Date'] = []
        myProb['player1_name'] = []
        myProb['player_name'] = []
        myProb['proba'] = []
        myProb['proba_opposite'] = []
        myProb['score'] = []
        myProb['intercept'] = []
        myProb['coef'] = []
        myProb['nIter'] = []
        for date_i in MathUtils.dateVec(self._startDate, self._endDate, timedelta(days=1)):
            myProb = self._generateProbas_date( date_i, timeColumnID, myProb )
       
        aa = pathFileOut + '_probas'
        myProbDf= pd.DataFrame.from_dict(myProb)
        myProbDf.to_csv(aa, sep = ",", header=True, index=False, encoding='utf-8')


#    
    #private
    #generate a table woth all the probas day by day.
    #probas for a given date
    def _generateProbas_date(self, date_i, timeColumnID, myProb ):
        baseData = self._histData.getData()
        
        #no game this day, we can skip
        df_date = baseData[baseData[timeColumnID] == date_i ]
        if df_date.shape[0] == 0:
            return myProb
        print(  date_i )
#        aa = pathFileOut + '_player1'
#        bb = pahFileOut + '_player2'
        scoreID = self._histData.getScoreColumnID()
#        count = 0
        for i, row in df_date.iterrows():
            player1_ID = row['player1_name']
            player2_ID = row['player2_name']
         
            datas_date = self._histData.extractPastData( date_i , player1_ID, player2_ID )

            res = self.getProbas_game( datas_date, self._regressor, scoreID )
            myProb['Date'].append( date_i )
            myProb['player1_name'].append( player1_ID )
            myProb['player_name'].append( player2_ID )
            myProb['proba'].append( res['proba'][0][0] )
            myProb['proba_opposite'].append( res['proba'][0][1] )
            myProb['score'].append( res['score'] )
            myProb['intercept'].append( res['intercept'] )
            myProb['coef'].append( res['coef'] )
            myProb['nIter'].append( res['nIter'] )
        return myProb

    def getProbas_game(self, datas_date, regressor, scoreID ):
        #we read the data dictionary
        df = datas_date['df']
        df_Today = datas_date['X']

#        regressor.setCatAnddStandardizeCols( colToStandardize, categoricalIndex, colToStandardize)
        
        #we get the x and y
        cols = df.columns.drop( scoreID )
        length = df.shape[0]
        length2= len( cols )
        y = df[scoreID].values.reshape( length )
        X = df[cols].values.reshape( length, length2 )
        X_game = df_Today[cols].values.reshape( 1, length2 )  

        #we run the regression
        regressor.calibrate(  X,  y )
        return { 'proba': regressor.predict( X_game ), 'score':regressor.getScore(X, y) , 
                'intercept' : regressor._model.intercept_ ,
                'coef' : regressor._model.coef_, 'nIter': regressor._model.n_iter_ }
        
class cWeightParam:
    #class used to generate the (time) weights of a regression
    
    #useWeight (bool): if true, we apply the weight
    #useTimeCutOff: if true, every point wich is after the time cut off will be removed from the datasets
    #startTime: the time in year after which the weights starts to decay
    #decayTime: the exponential decay speed in years, need to be positive
    #minWeight: the asyptotic weight value
    #weightCutOff: if a weight is below this value, we remove it from the dataset.
    #timeCutOff: if a point is beyond this limit, we relove it from the dataset.
    #   weight( t ) = 1.0 if t < startTime
    #   weight(t) = minWeight + ( 1.0 - minWeight * ) * exp( - (1.0 / decayTime ) * (t - startTime )  ) 
    
    def __init__(self,
                 useWeight = False,
                 useTimeCutOff = False,
                 useWeightCutOff = False,
                 startTime = 1.0,
                 decayTime = 0.25,
                 minWeight = 0.0,
                 weightCutOff = -1.0,
                 timeCutOff = 1.0 ):
        self._useWeight = useWeight
        self._useTimeCutOff = useTimeCutOff
        self._useWeightCutOff = useWeightCutOff
        self._startTime = startTime
        self._decayTime = decayTime
        self._minWeight = minWeight
        self._weightCutOff = weightCutOff
        self._timeCutOff = timeCutOff
        err.REQUIRE( self._decayTime >= -FUZZ,
                    'The DecayTime need to be postive' )
        err.REQUIRE( ( not self._useWeightCutOff ) or self._weightCutOff >= -FUZZ,
                        'The weightCutOff need to be postive when useWeightCutOff if true' )
        err.REQUIRE( ( not self._useTimeCutOff ) or self._timeCutOff >= startTime -FUZZ,
                        'The timeCutOff need to be postive when _useTimeCutOff if true' )      
         
    #public
    #Return a bool. True if <e need a weight adjustment
    def hasWeightAdjustment(self):
        return self._useWeight or self._useTimeCutOff or self._useWeightCutOff
    
    #public
    #return the weight column from the time array
    def getWeight(self, startTime, timeArr):
        err.ERROR( 'not implemented yet' )
        pass

    
try:
    startTime = time.time()
    importExcel = True
    importGit = False
    loadChallenge = False
    loadFutures = False
    doParseTime = False
    myHistData = hist.cHistTennisData( repoPath, repoGitPath, competitionID, importExcel,
                        importGit, loadChallenge, loadFutures, doParseTime )

    myHistData.exportData( pathFileOut )
    
    myWeightParam = cWeightParam(useWeight = False,
                                 useTimeCutOff = False,
                                 useWeightCutOff = False,
                                 startTime = 1.0,
                                 decayTime = 0.25,
                                 minWeight = 0.0,
                                 weightCutOff = -1.0,
                                 timeCutOff = 1.0 )
    modelType = 'logit'
    strategyName = 'dummy'    
#
    startDate = datetime(2018, 1, 11)
    endDate = datetime(2018, 1, 25)
    
    myStrategy = cStrategy( myHistData,
                             modelType,
                             strategyName,
                             startDate,
                             endDate,
                             myWeightParam,              
                             n_cpu = -1 )
#
#
    myStrategy.runStrategy()
#    
    
    
    
    finalTime = time.time() - startTime
    print( 'finalTime: ' )
    print( finalTime )
    print( 'Job done in cStrategy' )
    
except err.cError as e:
    print( 'An error occured:', e.value )
