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

basePath = "D:\IT\Library\Python\Data"
sportID = "Tennis"
competitionID = "Dummy"
repoPath = basePath + "\\" + sportID + "\\" + competitionID
pathFileOut = basePath + "\\" + sportID + "\\Data_" + sportID + "_" + competitionID
repoGitPath = basePath + "\\" + sportID + "\\" +  "Dummy"


class cStrategy:
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
                                                         n_cpu = -1, 
                                                         penalty = 'l2', 
                                                         smart_guess = True,
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
        
        regressor_base = reg.cLinearRegression_logit( center = False,
                                 reduce = False,
                                 normalize = False,
                                 fit_intercept = True,
                                 colsToStandardize = [],
                                 transformCategorical = False,
                                 categoricalCols = [],
                                 n_cpu = -1, 
                                 penalty = 'l2', 
                                 smart_guess = False,
                                 multi_class = 'ovr',
                                 adjustNaN = True,
                                 dimReduc = None,
                                 nDimReduc = -1,
                                 ruleOfTen = False,
                                 usePolynomialFeature = False,
                                 nPolynomialDegree = 2,
                                 colsToPoly = [])
        
        regressor_stand = reg.cLinearRegression_logit( center = True,
                                 reduce = True,
                                 normalize = False,
                                 fit_intercept = True,
                                 colsToStandardize = [],
                                 transformCategorical = False,
                                 categoricalCols = [],
                                 n_cpu = -1, 
                                 penalty = 'l2', 
                                 smart_guess = False,
                                 multi_class = 'ovr',
                                 adjustNaN = True,
                                 dimReduc = None,
                                 nDimReduc = -1,
                                 ruleOfTen = False,
                                 usePolynomialFeature = False,
                                 nPolynomialDegree = 2,
                                 colsToPoly = [])
        
        regressor_base_dimReduc_trunc = reg.cLinearRegression_logit( center = False,
                                 reduce = False,
                                 normalize = False,
                                 fit_intercept = True,
                                 colsToStandardize = [],
                                 transformCategorical = False,
                                 categoricalCols = [],
                                 n_cpu = -1, 
                                 penalty = 'l2', 
                                 smart_guess = False,
                                 multi_class = 'ovr',
                                 adjustNaN = True,
                                 dimReduc = 'TruncSVD',
                                 nDimReduc = 15,
                                 ruleOfTen = False,
                                 usePolynomialFeature = False,
                                 nPolynomialDegree = 2,
                                 colsToPoly = [])
        
        regressor_stand_dimReduc_trunc = reg.cLinearRegression_logit( center = True,
                                 reduce = True,
                                 normalize = False,
                                 fit_intercept = True,
                                 colsToStandardize = [],
                                 transformCategorical = False,
                                 categoricalCols = [],
                                 n_cpu = -1, 
                                 penalty = 'l2', 
                                 smart_guess = False,
                                 multi_class = 'ovr',
                                 adjustNaN = True,
                                 dimReduc = 'TruncSVD',
                                 nDimReduc = 15,
                                 ruleOfTen = False,
                                 usePolynomialFeature = False,
                                 nPolynomialDegree = 2,
                                 colsToPoly = [])
        
        regressor_base_dimReduc_PCA = reg.cLinearRegression_logit( center = False,
                         reduce = False,
                         normalize = False,
                         fit_intercept = True,
                         colsToStandardize = [],
                         transformCategorical = False,
                         categoricalCols = [],
                         n_cpu = -1, 
                         penalty = 'l2', 
                         smart_guess = False,
                         multi_class = 'ovr',
                         adjustNaN = True,
                         dimReduc = 'PCA',
                         nDimReduc = 15,
                         ruleOfTen = False,
                         usePolynomialFeature = False,
                         nPolynomialDegree = 2,
                         colsToPoly = [])
        
        regressor_stand_dimReduc_PCA = reg.cLinearRegression_logit( center = True,
                                 reduce = True,
                                 normalize = False,
                                 fit_intercept = True,
                                 colsToStandardize = [],
                                 transformCategorical = False,
                                 categoricalCols = [],
                                 n_cpu = -1, 
                                 penalty = 'l2', 
                                 smart_guess = False,
                                 multi_class = 'ovr',
                                 adjustNaN = True,
                                 dimReduc = 'PCA',
                                 nDimReduc = 15,
                                 ruleOfTen = False,
                                 usePolynomialFeature = False,
                                 nPolynomialDegree = 2,
                                 colsToPoly = [])

        regressor_base_dimReduc_trunc_ruleOfTen = reg.cLinearRegression_logit( center = False,
                                 reduce = False,
                                 normalize = False,
                                 fit_intercept = True,
                                 colsToStandardize = [],
                                 transformCategorical = False,
                                 categoricalCols = [],
                                 n_cpu = -1, 
                                 penalty = 'l2', 
                                 smart_guess = False,
                                 multi_class = 'ovr',
                                 adjustNaN = True,
                                 dimReduc = 'TruncSVD',
                                 nDimReduc = 15,
                                 ruleOfTen = True,
                                 usePolynomialFeature = False,
                                 nPolynomialDegree = 2,
                                 colsToPoly = [])
        
        regressor_stand_dimReduc_trunc_ruleOfTen = reg.cLinearRegression_logit( center = True,
                                 reduce = True,
                                 normalize = False,
                                 fit_intercept = True,
                                 colsToStandardize = [],
                                 transformCategorical = False,
                                 categoricalCols = [],
                                 n_cpu = -1, 
                                 penalty = 'l2', 
                                 smart_guess = False,
                                 multi_class = 'ovr',
                                 adjustNaN = True,
                                 dimReduc = 'TruncSVD',
                                 nDimReduc = 15,
                                 ruleOfTen = True,
                                 usePolynomialFeature = False,
                                 nPolynomialDegree = 2,
                                 colsToPoly = [])
        
        regressor_base_dimReduc_PCA_ruleofTen = reg.cLinearRegression_logit( center = False,
                                                 reduce = False,
                                                 normalize = False,
                                                 fit_intercept = True,
                                                 colsToStandardize = [],
                                                 transformCategorical = False,
                                                 categoricalCols = [],
                                                 n_cpu = -1, 
                                                 penalty = 'l2', 
                                                 smart_guess = False,
                                                 multi_class = 'ovr',
                                                 adjustNaN = True,
                                                 dimReduc = 'PCA',
                                                 nDimReduc = 15,
                                                 ruleOfTen = True,
                                                 usePolynomialFeature = False,
                                                 nPolynomialDegree =2,
                                                 colsToPoly = [])
        
        regressor_stand_dimReduc_PCA_ruleOfTen = reg.cLinearRegression_logit( center = True,
                                 reduce = True,
                                 normalize = False,
                                 fit_intercept = True,
                                 colsToStandardize = [],
                                 transformCategorical = False,
                                 categoricalCols = [],
                                 n_cpu = -1, 
                                 penalty = 'l2', 
                                 smart_guess = False,
                                 multi_class = 'ovr',
                                 adjustNaN = True,
                                 dimReduc = 'PCA',
                                 nDimReduc = 15,
                                 ruleOfTen = True,
                                 usePolynomialFeature = False,
                                 nPolynomialDegree = 2,
                                 colsToPoly = [])
        
        regressorDict = { 'base':regressor_base, 
                         'stand':regressor_stand, 
                         'base_truncSVD_15':regressor_base_dimReduc_trunc,
                         'stand_truncSVD_15':regressor_stand_dimReduc_trunc, 
                         'base_PCA_15':regressor_base_dimReduc_PCA,
                         'stand_PCA_15':regressor_stand_dimReduc_PCA,
                         'base_trunc_ruleOfTen':regressor_base_dimReduc_trunc_ruleOfTen ,
                         'stand_trunc_ruleofTen':regressor_stand_dimReduc_trunc_ruleOfTen, 
                         'base_PCA_ruleOfTen':regressor_base_dimReduc_PCA_ruleofTen ,
                         'stand_PCA_ruleofTen':regressor_stand_dimReduc_PCA_ruleOfTen }
        
        myProb = {}
        for key in regressorDict:
            col1 = str(key) +'_p1'
            col2 = str(key) +'_p2'
            col3 = str(key) +'_score1'
            col4 = str(key) +'_score2'
            myProb[col1] = []
            myProb[col2] = []
            myProb[col3] = []
            myProb[col4] = []
        for date_i in MathUtils.dateVec(self._startDate, self._endDate, timedelta(days=1)):
            myProb = self._generateProbas_date( date_i, timeColumnID, regressorDict, myProb )
       
        
        aa = pathFileOut + '_probas'
        bb = pathFileOut + '_sumUp'
        myProbDf= pd.DataFrame()
        for key in myProb:
            myProbDf[key] = myProb[key]
        myProbDf.to_csv(aa, sep = ",", header=True, index=False, encoding='utf-8')
        
        sumUp = pd.DataFrame()
        for key in regressorDict:
            col1 = str(key) +'_p1'
            col2 = str(key) +'_p2'
            col3 = str(key) +'_score1'
            col4 = str(key) +'_score2'  
            spread = np.subtract(myProb[col1], myProb[col2])
            spread = np.abs(spread) 

            mean = np.mean( spread )
            maxVal = np.mean(spread)
            stddev = np.std( spread )
            
            meanSc1 = np.mean( myProb[col3] )
            maxValSc1 = np.mean(myProb[col3])
            stddevSc1 = np.std( myProb[col3] )
            
            meanSc2 = np.mean( myProb[col4] )
            maxValSc2 = np.mean(myProb[col4])
            stddevSc2 = np.std( myProb[col4] )
            
            sumUp[key] = [mean, maxVal, stddev,
                         meanSc1, maxValSc1, stddevSc1,
                         meanSc2, maxValSc2, stddevSc2 ]

        sumUp.to_csv(bb, sep = ",", header=True, index=False, encoding='utf-8') 

#    
    #private
    #generate a table woth all the probas day by day.
    #probas for a given date
    def _generateProbas_date(self, date_i, timeColumnID, regressorDict, myProb ):
        baseData = self._histData.getData()
        
        #no game this day, we can skip
        df_date = baseData[baseData[timeColumnID] == date_i ]
        if df_date.shape[0] == 0:
            return myProb
        print(   date_i )
#        aa = pathFileOut + '_player1'
#        bb = pathFileOut + '_player2'
        scoreID = self._histData.getScoreColumnID()
        minSample = 30
        count = 0

            
        for i, row in df_date.iterrows():
            player1_ID = row['player1_name']
            player2_ID = row['player2_name']
         
#            tourneyId = row['tourney_name']
#            if ' CH' in tourneyId or count > 0:
#                continue

            
            count = count + 1
            print( count )

            player1_data = self._histData.extractPastData( date_i , player1_ID, player2_ID, True, minSample )
            player2_data = self._histData.extractPastData( date_i , player2_ID, player1_ID, True, minSample )
            if player1_data['df'].shape[0] < minSample or player2_data['df'].shape[0] < minSample:
                continue

            for key, regressor in regressorDict.items():
                res1 = self.getProbas_player( player1_data, regressor, scoreID, True )
                res2 = self.getProbas_player( player2_data, regressor, scoreID, True )
                p1 = res1['prob']
                score1 = res1['score']
                p2 = res2['prob']
                score2 = res2['score']
                col1 = str(key) +'_p1'
                col2 = str(key) +'_p2'
                col3 = str(key) +'_score1'
                col4 = str(key) +'_score2'
                myProb[col1].append( p1[0][0] )
                myProb[col2].append( p2[0][1] )
                myProb[col3].append( score1 )
                myProb[col4].append( score2 )
#            count += 1
#            print( count )
#            player1_data['df'].to_csv(aa, sep = ",", header=True, index=False, encoding='utf-8')
#            player2_data['df'].to_csv(bb, sep = ",", header=True, index=False, encoding='utf-8') 
#            a[1] = 10
        return myProb

    def getProbas_player(self, playerData, regressor, scoreID, getScore ):
        #we read the data dictionary
        df= playerData['df']
        df_Today = playerData['X']
        timeVec = playerData['Time']
        categoricalIndex = playerData['CategoricalIndex']
        colToStandardize = playerData['ColToStandardize']
        regressor.setCatAnddStandardizeCols( colToStandardize, categoricalIndex, colToStandardize)
        
        #we get the x and y
        cols = df.columns.drop( scoreID )
        length = df.shape[0]
        length2= len( cols )
        y = df[scoreID].values.reshape( length )
        X = df[cols].values.reshape( length, length2 )
        X_today = df_Today[cols].values.reshape( 1, length2 )  

        #we run the regression
        
        score = 0
        regressor.calibrate(  X,  y )
        if getScore:
            score = regressor.getScore(X, y) 
        return { 'prob': regressor.predict( X_today ), 'score':score }
        
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
    startTime =time.time()
    importOne = False
    importGit = True
    loadChallenge = False
    loadFutures = False
    doParseTime = False
    myHistData = hist.cHistTennisData( repoPath, repoGitPath, competitionID, importOne,
                        importGit, loadChallenge, loadFutures, doParseTime )

#    myHistData.exportData( pathFileOut )
    
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

    startDate = datetime(2015, 1, 1)
    endDate = datetime(2017, 1, 1)
    
    myStrategy = cStrategy( myHistData,
                             modelType,
                             strategyName,
                             startDate,
                             endDate,
                             myWeightParam,              
                             n_cpu = -1 )


    myStrategy.runStrategy()
#    myHistData.exportData( pathFileOut )
    finalTime=time.time()-startTime
    print( finalTime )
    print( 'Job done in cStrategy' )
    
except err.cError as e:
    print( 'An error occured:', e.value )
