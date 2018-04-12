#-------------------------------------------------------------------------------
# Name:        HistData
# Purpose:     This file contains several class which can handle the betting
#              data (either live or historical).
#
# Author:      Matars
#
# Created:     18/02/2017
# Copyright:   (c) St?phane 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import pandas as pd
import Error as err
import glob, os
import Tennis
import abc
import datetime
import math
import numpy as np

FUZZ = err.FUZZ

basePath = "D:\IT\Library\Python\Data"
sportID = "Tennis"
competitionID = "Dummy"
repoPath = basePath + "\\" + sportID + "\\" + competitionID
pathFileOut = basePath + "\\" + sportID + "\\Data_" + sportID + "_" + competitionID
repoGitPath = basePath + "\\" + sportID + "\\" +  "Dummy"


class cHistData:
	# class used to save and manage all the historical datas and information
    __metaclass__ = abc.ABCMeta
	
	# constructor
   # _ID: the (sport) ID
    def __init__(self, useWeight):
        self._useWeight = useWeight
        self._data = pd.DataFrame()
        pass

    #Public
    #Return the (sport) ID
    @abc.abstractmethod
    def getID(self):
        pass
    
    #public
    #return the classID
    def getClassID(self):
        return( 'cHistData' )
        pass
    
    #public
    #Return the time column ID
    @abc.abstractmethod
    def getTimeColumnID(self):
        pass
    
    #public
    #return the dataframe with the datas
    def getData(self):
        return self._data
    
    #public
    #export data
    def exportData( self, pathFileOut ):
        self._data.to_csv(pathFileOut, sep = ",", header=True, index=False, encoding='utf-8')
    
    #public
    #return the score (aka. y) column ID
    @abc.abstractmethod
    def getScoreColumnID(self):
        pass
    

class cHistTennisData(cHistData):
    # class used to save and manage all the historical datas and information about tennis

    #repoPath, repoGitPath: repository with datas
    # _competitionID: the competition ID
    # _data: the base datas
    def __init__(self,
                repoPath,
                repoGitPath,
                competitionID,
                importOne = True,
                importGit = True,
                loadChallenge = False,
                loadFuture = False,
                doParseTime = False ):
        cHistData.__init__(self, useWeight = False )
        self._compettionID = competitionID
        df_excel = pd.DataFrame()
        if importOne:
            os.chdir( repoPath )
            for fileID in glob.glob("*.xls"):
                df_excel = pd.concat([df_excel,self._loadData_excel( fileID )], axis=0, ignore_index=True )
            for fileID in glob.glob("*.xlsx"):
                df_excel = pd.concat([df_excel,self._loadData_excel( fileID )], axis=0, ignore_index=True )
            if importGit:                
                err.ERROR( 'The merge of the two data bases is not implemented yet ')
                df_excel = self._renameIndex_excel( df_excel )
            df_excel = self._computeProbas( df_excel )
      

        if importGit:
            if doParseTime:
                df = Tennis.readATPMatchesParseTime( repoGitPath )
            else:
                df = Tennis.readATPMatches( repoGitPath )
            self._data = pd.concat([self._data,df], axis=0, ignore_index=True )
            if loadChallenge:
                if doParseTime:
                    df = Tennis.readChall_QATPMatchesParseTime( repoGitPath )
                else:
                    df = Tennis.readChall_QATPMatches( repoGitPath )
                self._data = pd.concat([self._data,df], axis=0, ignore_index=True )
            if loadFuture:
                if doParseTime:
                    df = Tennis.readFMatchesParseTime( repoGitPath )
                else:
                    df = Tennis.readFMatches( repoGitPath )
                self._data = pd.concat([self._data,df], axis=0, ignore_index=True )
            if importOne:
                err.ERROR( 'The merge of the two data bases is not implemented yet ')
                self._renameIndex_git()
            self._adjustTimeVec()
            self._preProcessData_init()
            self._lastDate = -1 #use in extractData for performance
            self._data_lastDate = None #use in extractData for performance
            
        if importOne:
            self._data = df_excel
        
    #private
    #we adjust the time vec here
    def _adjustTimeVec(self):
        timeColID = self.getTimeColumnID()
        self._data[timeColID] =  pd.to_datetime(self._data[timeColID], format='%Y%m%d')  
        for i, rowVals in self._data.iterrows():
            roundVal= rowVals['round']
            draw_size= rowVals['draw_size']
            time = rowVals[timeColID]
            delta = 0
            err.REQUIRE( draw_size <= 128 or math.isnan(draw_size), 'Incorrect draw size' )
            if draw_size < 128:
                if roundVal == 'R64' or roundVal == 'Q3':
                    delta = 1
                elif roundVal == 'R32' or roundVal == 'Q2':
                    delta = 2
                elif roundVal == 'R16':
                    delta = 3
                elif roundVal == 'QF':
                    delta = 4
                elif roundVal == 'SF':
                    delta = 5
                elif roundVal =='F':
                    delta = 6
                elif roundVal == 'BR':
                    delta = 6
                elif roundVal == 'RR' or roundVal == 'R128' or roundVal == 'Q3' or roundVal == 'Q2' or roundVal == 'Q1' or math.isnan(draw_size):
                    delta = 0 #need to be adjusted
                else:
                    err.ERROR( 'Unknown round value')
            else:
                if roundVal == 'R128':
                    delta = 1
                elif roundVal == 'R64':
                    delta = 3
                elif roundVal == 'R32':
                    delta = 5
                elif roundVal == 'R16':
                    delta = 7
                elif roundVal == 'QF':
                    delta = 9
                elif roundVal == 'SF':
                    delta = 11
                elif roundVal =='F':
                    delta = 13
                elif roundVal == 'BR':
                    delta = 12
                elif roundVal == 'RR' or roundVal == 'Q3' or roundVal == 'Q2' or roundVal == 'Q1' or math.isnan(draw_size):
                    delta = 0 #need to be adjusted
                else:
                    err.ERROR( 'Unknown round value')
            self._data.set_value(i,timeColID,time + datetime.timedelta( days=delta) )
        self._data[timeColID] =  pd.to_datetime(self._data[timeColID], format='%Y%m%d')

    #public 
    #modify the date
    def _adjustDates( self, startDate, endDate ):
        self._data  = self._data.loc[ self._data['Date'] >= startDate,:]
        self._data = self._data.loc[ self._data['Date'] <= endDate,:]

    #private
    #need to be clean up. Load excel data
    def _loadData_excel( self, fileID ):
        xls_file = pd.ExcelFile( fileID )
        listStr = fileID.split(".")
        if listStr[0] in xls_file.sheet_names:
            df = xls_file.parse( listStr[0] )
        else:
            df = xls_file.parse( 'Sheet1' )
        return df
    
    #private
    #need to be clean up. Load excel data
    def _renameIndex_git( self ):
        for index, row in self._data.iterrows():
            dateStr = str(self._data['tourney_date'][index] ) 
            loserId = self._playerID_git(self._data['loser_name'][index] )
            winnerId = self._playerID_git(self._data['winner_name'][index] )
            
            indexString = dateStr + '_'
            if winnerId < loserId:
                indexString += winnerId + '_' + loserId
            else:
                indexString += loserId + '_' + winnerId
                    
            count = 0
            while indexString in self._data.index:
                count += 1
                indexString += str(count)
            self._data = self._data.rename(index={index: indexString })
  
    #private
    #need to be clean up. Return the initial of the player id
    def _playerID_git( self, fullName ):
        listStr  = fullName.split(" ")
        playerId = ''        
        for e in listStr:
            playerId += e[0]
            if e != listStr[-1]:
                playerId += '.'
        return playerId
    
    #private
    # compute the probas ad adjustment
    def _computeProbas( self, df_excel ):
        cols = ['B365W', 'EXW', 'LBW','PSW', 'SJW', 'UBW']
        probasW = 1.0 / df_excel[cols].astype('float64')
        maxW = probasW.min( axis = 1, skipna = True )
        averageW = probasW.mean( axis = 1, skipna = True )

        
        cols = ['B365L', 'EXL', 'LBL','PSL', 'SJL', 'UBL']
        probasL = 1.0 / df_excel[cols].astype('float64')
        maxL = probasL.min( axis = 1, skipna = True )
        averageL = probasL.mean( axis = 1, skipna = True )

        spreadCorrection = ( ( averageL + averageW ) -1.0 ) / 2.0
        averageL_corrected = averageL - spreadCorrection
        averageW_corrected = averageW - spreadCorrection
        
        cols = ['probaW1', 'probaW2', 'probaW3','probaW4', 'probaW5', 'probaW6']
        df_excel[cols] = probasW
        cols = ['probaL1', 'probaL2', 'probaL3','probaL4', 'probaL5', 'probaL6']
        df_excel[cols] = probasL
                
        df_excel['probaMaxW'] = maxW
        df_excel['probaMaxL'] = maxL
                
        df_excel['probaAvgW'] = averageW
        df_excel['probaAvgL'] = averageL
        df_excel['probaAvgW_corrected'] = averageW_corrected
        df_excel['probaAvgL_corrected'] = averageL_corrected
 
        df_excel = df_excel.loc[ df_excel['probaAvgW'].notnull(),:]
        df_excel = df_excel.loc[ df_excel['probaAvgL'].notnull(),:]

        return df_excel

    #private
    #need to be clean up. Load excel data
    def _renameIndex_excel( self, df_excel ):
        for index, row in df_excel.iterrows():
            dateStr = df_excel['Date'][index].strftime('%Y%m%d')
            loserId = self._playerID_excel( df_excel['Loser'][index] )
            winnerId = self._playerID_excel( df_excel['Winner'][index] )    
            
            indexString = dateStr + '_'
            if winnerId < loserId:
                indexString += winnerId + '_' + loserId
            else:
                indexString += loserId + '_' + winnerId
            
            count = 0
            while indexString in df_excel.index:
                count += 1
                indexString += str(count)
            df_excel = df_excel.rename(index={index: indexString })

        return df_excel
    
    #private
    #need to be clean up. Return the initial of the player id
    def _playerID_excel( self, fullName ):
        listStr  = fullName.split(" ")
        playerId = listStr[len( listStr)-1]
        listStr = listStr[:len( listStr)-1]
        
        for e in listStr:
            playerId += e[0]
            if e != listStr[-1]:
                playerId += '.'
        return playerId
     
    #Public
    #Return the (sport) ID   
    def getID( self ):
        return "Tennis"
    
    #public
    #return the classID
    def getClassID(self):
        return( 'cHistTennisData' )
        pass
    
    #public
    #return the score (aka. y) column ID       
    def getTimeColumnID(self):
        return 'tourney_date'
     
    #public
    #return the score (aka. y) column ID  
    def getScoreColumnID(self):
        return 'Winner'

    #public
    #preprocess data (dummies, drop). Standardisation is done at a later stage
    def _preProcessData_init( self ):
        # add game id
        #tourney_id and match nul could be use to create a gameid
        #treat davis cup 
        #remove extreme datas
        #handle nan values
        #regression logistic, scale and sparse data
        #• svd, pca, kernel pca
#        supprot vector machines
#        generating polynomial features
#add average to date, nb latch atp etc..., best rank ever. ratio de victoire 
#number minutes played during the tournament
#some datas are empty for a reason and should be prefill

#add the drop last dummies to avoid redundancy


        self._data['Winner'] = self._data[ 'winner_name' ]
        cols_to_drop = [ 'tourney_id', 'match_num', 'winner_id', 'loser_id',
                            'score', 'minutes', 
                            'w_df', 'w_svpt',
                            'w_1stIn', 'w_1stWon', 'w_2ndWon', 'w_SvGms',
                            'w_bpSaved', 'w_bpFaced', 
                            'l_df', 'l_svpt',
                            'l_1stIn', 'l_1stWon', 'l_2ndWon', 'l_SvGms', 
                            'l_bpSaved', 'l_bpFaced', 'w_ace', 'l_ace',
                            'winner_seed', 'loser_seed',
                            'winner_ht', 'loser_ht']

        # wace l_ace
        self._data.rename(columns={'winner_name': 'player1_name',
                                   'winner_rank': 'player1_rank',
#                                    'winner_seed': 'player1_seed',  
                                    'winner_age': 'player1_age',
                                    'winner_hand': 'player1_hand',
                                    'winner_rank_points' : 'player1_rank_points',
                                    'winner_ioc':'player1_ioc',
#                                    'winner_ht':'player1_ht',
                                    'winner_entry':'player1_entry',
                                    'loser_name': 'player2_name',
                                    'loser_rank': 'player2_rank',
#                                    'loser_seed': 'player2_seed', 
                                    'loser_age': 'player2_age',
                                    'loser_hand': 'player2_hand',
                                    'loser_rank_points' : 'player2_rank_points',
                                    'loser_ioc':'player2_ioc',
#                                    'loser_ht':'player2_ht',
                                    'loser_entry':'player2_entry'},
                                    inplace=True)


        cols_to_dummies_and_drop = []
        cols_to_dummies_init = []
        self._data.loc[self._data['tourney_name'].str.startswith('Davis Cup') , 'tourney_name' ] = 'Davis Cup'
        self._data = preProcessData( self._data, cols_to_drop, cols_to_dummies_init, cols_to_dummies_and_drop)
               
        self._cols_to_dummies_and_drop = [ 'player2_name', 'tourney_name','surface',
                                           'tourney_level', 'best_of', 'round', 'draw_size',
                                           'player1_hand', 'player2_hand', 'player1_ioc', 'player2_ioc',
                                           'player1_entry', 'player2_entry']  
        self._cols_to_switch = [ ['player1_rank', 'player2_rank'],
#                                 ['player1_seed', 'player2_seed'],
                                 ['player1_age', 'player2_age'],
                                 ['player1_hand', 'player2_hand'],
                                 ['player1_rank_points', 'player2_rank_points'],
                                 ['player1_ioc', 'player2_ioc'],
#                                 ['player1_ht', 'player2_ht']
                                 ]
        self._cols_to_switch_indexcol = [['player1_name', 'player2_name' ]]
        
        
        self._cols_to_standardize = ['player1_rank', 'player2_rank', 
#                                     'player1_seed', 'player2_seed',
                                     'player1_age', 'player2_age', 'player1_rank_points', 'player2_rank_points',
#                                     'player1_ht', 'player2_ht'
                                     ]
    
        
     
    #public
    #get the datas before a given date and preProcess them
    def extractPastData( self, date, playerID, player2_ID, doDummies = True, minSample = 30 ):
        timeColumnID = self.getTimeColumnID()
        #no need to reload the data is still the same dates
        if self._lastDate != date:
            self._lastDate = date
            self._data_lastDate = self._data.loc[self._data[timeColumnID] <= date,:]

        scoreId = self.getScoreColumnID()
        df_player = self._data_lastDate[(self._data_lastDate['player1_name'] == playerID) | (self._data_lastDate['player2_name'] == playerID) ]
        err.REQUIRE( df_player.shape[0] > 0, 'No value for the player ' + playerID + ' in the database' )
        
        #need a copy to avoid perf and memoru issues
        df_player = pd.DataFrame( df_player )
        df_player.loc[df_player[scoreId] != playerID, scoreId ] = 0
        df_player.loc[df_player[scoreId] == playerID, scoreId ] = 1
        self._switchData(df_player, playerID)
        
        categoricalColsIndex=[]
        colToStandardizeIndex=[]
        if doDummies:
            df_player = preProcessData( df_player, 
                                cols_to_drop = [], 
                                cols_to_dummies = [],
                                cols_to_dummies_and_drop = self._cols_to_dummies_and_drop )
        else:
            categoricalColsIndex = [df_player.columns.get_loc('player2_name' )]
        #we drop the const values
        if df_player.shape[0] >= minSample:
            df_player = df_player.loc[:,df_player.apply(pd.Series.nunique) != 1]
        
        #the results 
        x_player = df_player.loc[df_player[timeColumnID] == date,:]
        df_player = df_player.loc[df_player[timeColumnID] < date,:]
        time = df_player[timeColumnID]
        df_player.drop( [timeColumnID], axis = 1, inplace = True)
        x_player.drop( [timeColumnID], axis = 1, inplace = True)
        if x_player.shape[0] > 1: #several games the same day
            x_player = x_player.loc[x_player[player2_ID] == 1,:]
                         
        #we intersect the columns, to avoid those which have been dropped (const cols)
        colToStandardize_local = pd.Series(list(set(self._cols_to_standardize) & set(df_player.columns)))
        colToStandardizeIndex = [df_player.columns.drop(scoreId).get_loc(col) for col in colToStandardize_local ]
        
        return { 'df':df_player, 'X': x_player, 'Time': time,
                'CategoricalIndex' : categoricalColsIndex,
                'ColToStandardize' : colToStandardizeIndex }

    #private
    #switch the column such that all the player1 data are those we want to regress
    def _switchData(self, df, playerID):
        for cols in self._cols_to_switch:
            col2 = cols[1]
            col1 = cols[0]
            df.loc[df['player2_name'] == playerID, [col1, col2]] = df.loc[df['player2_name']  == playerID, [col2, col1]].values
        for cols in self._cols_to_switch_indexcol:
            col2 = cols[1]
            col1 = cols[0]
            df.loc[df['player2_name'] == playerID, [col1, col2]] = df.loc[df['player2_name']  == playerID, [col2, col1]].values
            

#generic function used to prepocess datas (drop, dummies etc)
def preProcessData( df, cols_to_drop, cols_to_dummies, cols_to_dummies_and_drop ):

    newDf = pd.DataFrame()
    #we dummies the column,
    #column is removed from based df
    for col in cols_to_dummies_and_drop:
        df_with_dummies = pd.get_dummies( df[ col ] )
#        err.ERROR( 'modify this' )
#        lastCol = len( df_with_dummies.columns ) - 1
#        df_with_dummies.drop( df_with_dummies.columns[lastCol], axis = 1, inplace = True )
        newDf = pd.concat([newDf,df_with_dummies], axis=1 )
        df.drop( col, axis = 1, inplace = True )
    
    for col in cols_to_dummies:
        df_with_dummies = pd.get_dummies( df[ col ] )
        newDf = pd.concat([newDf,df_with_dummies], axis=1 )
    df = pd.concat([df,newDf], axis=1 )
    df = df.groupby(df.columns, axis=1).max()
    
    # we drop the useless columns
    df.drop( cols_to_drop, axis = 1, inplace = True)
    
    return df

##do a function to arrange the shape of the score
#
try:
    importOne = True
    importGit = False
    loadChallenge = False
    loadFutures = False
    doParseTime = False
    myRes = cHistTennisData( repoPath, repoGitPath, competitionID, importOne,
                        importGit, loadChallenge, loadFutures, doParseTime )
    myRes.exportData( pathFileOut )
    print('Job done' )
except err.cError as e:
    print( 'An error occured:', e.value )