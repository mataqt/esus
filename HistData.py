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

basePath = "D:\IT\Library\Python\esus\Data"
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
                importExcel = True,
                importGit = True,
                loadChallenge = False,
                loadFuture = False,
                doParseTime = False ):
        cHistData.__init__(self, useWeight = False )
        self._compettionID = competitionID
        self._importExcel = importExcel
        self._importGit = importGit
        self._loadChallenge = loadChallenge
        self._loadFuture = loadFuture
        self._doParseTime = doParseTime
        self._importDatas()
        
    #private
    #import the datas and merge the dataframe
    def _importDatas(self):
        df_excel = pd.DataFrame()
        if self._importExcel:
            os.chdir( repoPath )
            for fileID in glob.glob("*.xls"):
                df_excel = pd.concat([df_excel,self._loadData_excel( fileID )], axis=0, ignore_index=True )
            for fileID in glob.glob("*.xlsx"):
                df_excel = pd.concat([df_excel,self._loadData_excel( fileID )], axis=0, ignore_index=True )
            if self._importGit:                
                err.ERROR( 'The merge of the two data bases is not implemented yet ')
#                df_excel = self._renameIndex_excel( df_excel )
            df_excel = self._computeProbas( df_excel )
      

        if self._importGit:
            if self._doParseTime:
                df = Tennis.readATPMatchesParseTime( repoGitPath )
            else:
                df = Tennis.readATPMatches( repoGitPath )
            self._data = pd.concat([self._data,df], axis=0, ignore_index=True )
            if self._loadChallenge:
                if self._doParseTime:
                    df = Tennis.readChall_QATPMatchesParseTime( repoGitPath )
                else:
                    df = Tennis.readChall_QATPMatches( repoGitPath )
                self._data = pd.concat([self._data,df], axis=0, ignore_index=True )
            if self._loadFuture:
                if self._doParseTime:
                    df = Tennis.readFMatchesParseTime( repoGitPath )
                else:
                    df = Tennis.readFMatches( repoGitPath )
                self._data = pd.concat([self._data,df], axis=0, ignore_index=True )
            if self._importExcel:
                err.ERROR( 'The merge of the two data bases is not implemented yet ')
#                self._renameIndex_git()
            self._adjustTimeVec()
            self._prepareIndicesGit()
            
        if self._importExcel:
            self._data = df_excel
            self._prepareIndicesExcel()
            

        
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
        cols = ['B365W', 'EXW', 'LBW','PSW','SJW']
        probasW = 1.0 / df_excel[cols].astype('float64')
        maxW = df_excel[cols].astype('float64').max( axis = 1, skipna = True )
        averageW = probasW.mean( axis = 1, skipna = True )

        cols = ['B365L', 'EXL', 'LBL','PSL','SJL']
        probasL = 1.0 / df_excel[cols].astype('float64')
        maxL = df_excel[cols].astype('float64').max( axis = 1, skipna = True )
        averageL = probasL.mean( axis = 1, skipna = True )

#        spreadCorrection = ( ( averageL + averageW ) -1.0 ) / 2.0
#        spreadCorrection2 = ( ( probasL + probasW ) -1.0 ) / 2.0
#
#        averageL_corrected = averageL - spreadCorrection
#        averageW_corrected = averageW - spreadCorrection
        
        cols = ['probaW1', 'probaW2', 'probaW3','probaW4','probaW5']
        df_excel[cols] = probasW
        cols = ['probaL1', 'probaL2', 'probaL3','probaL4','probaL5']
        df_excel[cols] = probasL
        
        df_excel['spread_proba1'] = ( df_excel['probaW1'] + df_excel['probaL1'] -1.0 ) / 2.0
        df_excel['spread_proba2'] = ( df_excel['probaW2'] + df_excel['probaL2'] -1.0 ) / 2.0
        df_excel['spread_proba3'] = ( df_excel['probaW3'] + df_excel['probaL3'] -1.0 ) / 2.0
        df_excel['spread_proba4'] = ( df_excel['probaW4'] + df_excel['probaL4'] -1.0 ) / 2.0
        df_excel['spread_proba5'] = ( df_excel['probaW5'] + df_excel['probaL5'] -1.0 ) / 2.0


                
        df_excel['MaxQuoteW'] = maxW
        df_excel['MaxQuoteL'] = maxL
                
        df_excel['probaAvgW'] = averageW
        df_excel['probaAvgL'] = averageL

        df_excel['diff_probaW1'] = ( df_excel['probaW1'] - df_excel['probaAvgW']  ) 
        df_excel['diff_probaW2'] = ( df_excel['probaW2'] - df_excel['probaAvgW']  ) 
        df_excel['diff_probaW3'] = ( df_excel['probaW3'] - df_excel['probaAvgW']  ) 
        df_excel['diff_probaW4'] = ( df_excel['probaW4'] - df_excel['probaAvgW']  ) 
        df_excel['diff_probaW5'] = ( df_excel['probaW5'] - df_excel['probaAvgW']  ) 

        df_excel['diff_probaL1'] = ( df_excel['probaL1'] - df_excel['probaAvgL']  ) 
        df_excel['diff_probaL2'] = ( df_excel['probaL2'] - df_excel['probaAvgL']  ) 
        df_excel['diff_probaL3'] = ( df_excel['probaL3'] - df_excel['probaAvgL']  ) 
        df_excel['diff_probaL4'] = ( df_excel['probaL4'] - df_excel['probaAvgL']  ) 
        df_excel['diff_probaL5'] = ( df_excel['probaL5'] - df_excel['probaAvgL']  ) 
        
        #shall we hanlde it differently?
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
        if self._importGit:
            return 'tourney_date'
        elif self._importExcel:
            return 'Date'
     
    #public
    #return the score (aka. y) column ID  
    def getScoreColumnID(self):
        return 'Winner'

    #public
    #rename data (dummies, drop).
    def _prepareIndicesExcel( self ):
        
        self._data.rename(columns={'Winner': 'player1_name',
                                   'Loser': 'player2_name',
                                   'AvgL' : 'player2_Avg',
                                   'AvgW' : 'player1_Avg',
                                   'LPts' : 'player2_pts',
                                   'WPts' : 'player1_pts',
                                   'LRank' : 'player2_Rank',
                                   'WRank' : 'player1_Rank',
                                   'Lsets' : 'player2_Sets',
                                   'Wsets' : 'player1_Sets',
                                   'MaxL' : 'player2_Max',
                                   'MaxW' : 'player1_Max',
                                   'L1' : 'player2_1',
                                   'L2' : 'player2_2',
                                   'L3' : 'player2_3',
                                   'L4' : 'player2_4',
                                   'L5' : 'player2_5',
                                   'W1' : 'player1_1',
                                   'W2' : 'player1_2',
                                   'W3' : 'player1_3',
                                   'W4' : 'player1_4',
                                   'W5' : 'player1_5',
                                   'probaAvgL' : 'player2_probaAvg',
                                   'probaL1' : 'player2_proba1',
                                   'probaL2' : 'player2_proba2',
                                   'probaL3' : 'player2_proba3',
                                   'probaL4' : 'player2_proba4',
                                   'probaL5' : 'player2_proba5',
                                   'MaxQuoteL' : 'player2_MaxQuote',
                                   'probaAvgW' : 'player1_probaAvg',
                                   'probaW1' : 'player1_proba1',
                                   'probaW2' : 'player1_proba2',
                                   'probaW3' : 'player1_proba3',
                                   'probaW4' : 'player1_proba4',
                                   'probaW5' : 'player1_proba5',
                                   'MaxQuoteW' : 'player1_MaxQuote',
                                   'diff_probaW1' : 'player1_diffProba1',
                                   'diff_probaW2' : 'player1_diffProba2',
                                   'diff_probaW3' : 'player1_diffProba3',
                                   'diff_probaW4' : 'player1_diffProba4',
                                   'diff_probaW5' : 'player1_diffProba5',
                                   'diff_probaL1' : 'player2_diffProba1',
                                   'diff_probaL2' : 'player2_diffProba2',
                                   'diff_probaL3' : 'player2_diffProba3',
                                   'diff_probaL4' : 'player2_diffProba4',
                                   'diff_probaL5' : 'player2_diffProba5'
                                   },
                                    inplace=True)       
        
        self._data['Winner'] = self._data['player1_name']


        self._cols_to_duplicate = {'player2_name': 'player1_name',
                                   'player1_name': 'player2_name',
                                   'player1_Avg' : 'player2_Avg',
                                   'player2_Avg' : 'player1_Avg',
                                   'player1_pts' : 'player2_pts',
                                   'player2_pts' : 'player1_pts',
                                   'player1_Rank' : 'player2_Rank',
                                   'player2_Rank' : 'player1_Rank',
                                   'player1_Sets' : 'player2_Sets',
                                   'player2_Sets' : 'player1_Sets',
                                   'player1_Max' : 'player2_Max',
                                   'player2_Max' : 'player1_Max',
                                   'player1_1' : 'player2_1',
                                   'player1_2' : 'player2_2',
                                   'player1_3' : 'player2_3',
                                   'player1_4' : 'player2_4',
                                   'player1_5' : 'player2_5',
                                   'player2_1' : 'player1_1',
                                   'player2_2' : 'player1_2',
                                   'player2_3' : 'player1_3',
                                   'player2_4' : 'player1_4',
                                   'player2_5' : 'player1_5',
                                   'player1_probaAvg' : 'player2_probaAvg',
                                   'player1_proba1' : 'player2_proba1',
                                   'player1_proba2' : 'player2_proba2',
                                   'player1_proba3' : 'player2_proba3',
                                   'player1_proba4' : 'player2_proba4',
                                   'player1_proba5' : 'player2_proba5',
                                   'player1_MaxQuote' : 'player2_MaxQuote',                                   
                                   'player2_probaAvg' : 'player1_probaAvg',
                                   'player2_proba1' : 'player1_proba1',
                                   'player2_proba2' : 'player1_proba2',
                                   'player2_proba3' : 'player1_proba3',
                                   'player2_proba4' : 'player1_proba4',
                                   'player2_proba5' : 'player1_proba5',
                                   'player2_MaxQuote' : 'player1_MaxQuote',
                                   'player2_diffProba1' : 'player1_diffProba1',
                                   'player2_diffProba2' : 'player1_diffProba2',
                                   'player2_diffProba3' : 'player1_diffProba3',
                                   'player2_diffProba4' : 'player1_diffProba4',
                                   'player2_diffProba5' : 'player1_diffProba5',
                                   'player1_diffProba1' : 'player2_diffProba1',
                                   'player1_diffProba2' : 'player2_diffProba2',
                                   'player1_diffProba3' : 'player2_diffProba3',
                                   'player1_diffProba4' : 'player2_diffProba4',
                                   'player1_diffProba5' : 'player2_diffProba5'                                   
                                   }
        
#        self._data = duplicateRows( self._data, cols=self._cols_to_duplicate )
        
        self._cols_to_drop = [ 
                                'B365W', 'EXW', 'LBW','PSW','SJW',
                              'B365L', 'EXL', 'LBL','PSL','SJL',
                                'player2_name',
                               'player1_name',
                               'player1_Avg',
                               'player2_Avg',
                               'player1_pts',
                               'player2_pts',
                               'player1_Rank',
                               'player2_Rank',
                               'player1_Sets',
                               'player2_Sets',
                               'player1_Max',
                               'player2_Max',
                               'player1_1',
                               'player1_2',
                               'player1_3',
                               'player1_4',
                               'player1_5',
                               'player2_1',
                               'player2_2',
                               'player2_3',
                               'player2_4',
                               'player2_5',
#                               'player1_probaAvg',
                               'player1_proba1',
                               'player1_proba2',
                               'player1_proba3',
                               'player1_proba4',
                               'player1_proba5',
                               'player1_MaxQuote',                                   
                               'player2_probaAvg',
                               'player2_proba1',
                               'player2_proba2',
                               'player2_proba3',
                               'player2_proba4',
                               'player2_proba5',
                               'player2_MaxQuote',
                               'ATP',
                               'Best of',
                               'Comment',
                               'Court',
                               'Date',
                               'Location',
                               'Series',
                               'Round',
                               'Surface',
                               'Tournament',
#                               'player1_diffProba1',
#                               'player1_diffProba2',
#                               'player1_diffProba3',
#                               'player1_diffProba4',
#                               'player1_diffProba5',
                               'player2_diffProba1',
                               'player2_diffProba2',
                               'player2_diffProba3',
                               'player2_diffProba4',
                               'player2_diffProba5'#,
#                               'spread_proba1',
#                               'spread_proba2',
#                               'spread_proba3',
#                               'spread_proba4',
#                               'spread_proba5'
                               ]

#        self._data = preProcessData( self._data, self._cols_to_drop, [], [] )
#

         
    #public
    #rename data (dummies, drop).
    def _prepareIndicesGit( self ):
        self._data['Winner'] = self._data[ 'winner_name' ]
        self._data.rename(columns={'winner_name': 'player1_name',
                                   'winner_rank': 'player1_rank',
                                   'winner_seed': 'player1_seed',  
                                   'winner_age': 'player1_age',
                                   'winner_hand': 'player1_hand',
                                   'winner_rank_points' : 'player1_rank_points',
                                   'winner_ioc':'player1_ioc',
                                   'winner_ht':'player1_ht',
                                   'winner_entry':'player1_entry',
                                   'w_1stIn' : 'player1_1stIn',
                                   'w_1stWon' : 'player1_1stWon',
                                   'w_2ndWon' : 'player1_2ndWon',
                                   'w_SvGms' : 'player1_SvGms',
                                   'w_ace' : 'player1_ace',
                                   'w_bpFaced' : 'player1_bpFaced',
                                   'w_bpSaved' : 'player1_bpSaved',
                                   'w_df' : 'player1_df',
                                   'w_svpt' : 'player1_svpt',
                                   'winner_id' : 'player1_id',
                                   'loser_name': 'player2_name',
                                   'loser_rank': 'player2_rank',
                                   'loser_seed': 'player2_seed', 
                                   'loser_age': 'player2_age',
                                   'loser_hand': 'player2_hand',
                                   'loser_rank_points' : 'player2_rank_points',
                                   'loser_ioc':'player2_ioc',
                                   'loser_ht':'player2_ht',
                                   'loser_entry':'player2_entry',
                                   'l_1stIn' : 'player2_1stIn',
                                   'l_1stWon' : 'player2_1stWon',
                                   'l_2ndWon' : 'player2_2ndWon',
                                   'l_SvGms' : 'player2_SvGms',
                                   'l_ace' : 'player2_ace',
                                   'l_bpFaced' : 'player2_bpFaced',
                                   'l_bpSaved' : 'player2_bpSaved',
                                   'l_df' : 'player2_df',
                                   'l_svpt' : 'player2_svpt',
                                   'loser_id' : 'player2_id'
                                   },
                                    inplace=True)
        self._data.loc[self._data['tourney_name'].str.startswith('Davis Cup') , 'tourney_name' ] = 'Davis Cup'
#        scoreId = self.getScoreColumnID()
#        self._data.loc[self._data[scoreId] != self._data['player1_name'], scoreId ] = 0
#        self._data.loc[self._data[scoreId] == self._data['player1_name'], scoreId ] = 1

        self._cols_to_duplicate = { 'player2_name': 'player1_name',
                                   'player2_rank': 'player1_rank',
                                   'player2_seed': 'player1_seed',  
                                   'player2_age': 'player1_age',
                                   'player2_hand': 'player1_hand',
                                   'player2_rank_points' : 'player1_rank_points',
                                   'player2_ioc':'player1_ioc',
                                   'player2_ht':'player1_ht',
                                   'player2_entry':'player1_entry',
                                   'player2_1stIn' : 'player1_1stIn',
                                   'player2_1stWon' : 'player1_1stWon',
                                   'player2_2ndWon' : 'player1_2ndWon',
                                   'player2_SvGms' : 'player1_SvGms',
                                   'player2_ace' : 'player1_ace',
                                   'player2_bpFaced' : 'player1_bpFaced',
                                   'player2_bpSaved' : 'player1_bpSaved',
                                   'player2_df' : 'player1_df',
                                   'player2_svpt' : 'player1_svpt',
                                   'player2_id' : 'player1_id',
                                   'player1_name': 'player2_name',
                                   'player1_rank': 'player2_rank',
                                   'player1_seed': 'player2_seed', 
                                   'player1_age': 'player2_age',
                                   'player1_hand': 'player2_hand',
                                   'player1_rank_points' : 'player2_rank_points',
                                   'player1_ioc':'player2_ioc',
                                   'player1_ht':'player2_ht',
                                   'player1_entry':'player2_entry',
                                   'player1_1stIn' : 'player2_1stIn',
                                   'player1_1stWon' : 'player2_1stWon',
                                   'player1_2ndWon' : 'player2_2ndWon',
                                   'player1_SvGms' : 'player2_SvGms',
                                   'player1_ace' : 'player2_ace',
                                   'player1_bpFaced' : 'player2_bpFaced',
                                   'player1_bpSaved' : 'player2_bpSaved',
                                   'player1_df' : 'player2_df',
                                   'player1_svpt' : 'player2_svpt',
                                   'player1_id' : 'player2_id'
                                   }
        
#        self._data = duplicateRows( self._data, cols=self._cols_to_duplicate )
        
        self._cols_to_drop = [ 'tourney_id', 'match_num', 'player1_id', 'player2_id',
                            'score', 'minutes', 
                            'tourney_name', 'tourney_level', 'round', 'tourney_date',
                            'surface',
                            'draw_size', 'best_of',
                            'player1_df', 'player1_svpt',
                            'player1_1stIn', 'player1_1stWon', 'player1_2ndWon', 'player1_SvGms',
                            'player1_bpSaved', 'player1_bpFaced', 
                            'player2_df', 'player2_svpt',
                            'player2_1stIn', 'player2_1stWon', 'player2_2ndWon', 'player2_SvGms', 
                            'player2_bpSaved', 'player2_bpFaced', 'player1_ace', 'player2_ace',
                            'player1_seed', 'player2_seed',
                            'player1_ht', 'player2_ht',
                            'player2_entry', 'player1_entry', 
                            'player1_ioc', 'player2_ioc',
                            'player1_rank', 'player2_rank', 'player1_age', 'player2_age',
                            'player1_rank_points', 'player2_rank_points',
                            'player1_hand', 'player2_hand'
                            ]


#        self._data = preProcessData( self._data, self._cols_to_drop, [], [] )
#

         
     
    #public
    #get the datas before a given date and preProcess them
    def extractPastData( self, date, player1_ID, player2_ID ):
        timeColumnID = self.getTimeColumnID()
        scoreId = self.getScoreColumnID()
        
        #need a copy to avoid perf and memoru issues
        df_date = pd.DataFrame( self._data.loc[self._data[timeColumnID] < date,:] )
        df_date = duplicateRows( df_date, cols=self._cols_to_duplicate )
        df_date.loc[df_date[scoreId] != df_date['player1_name'], scoreId ] = 0
        df_date.loc[df_date[scoreId] == df_date['player1_name'], scoreId ] = 1  
        df_date = preProcessData( df_date, self._cols_to_drop, [], [] )
        df_date.to_csv(pathFileOut  +' _dfDate', sep = ",", header=True, index=False, encoding='utf-8')


        x_game = pd.DataFrame( self._data.loc[self._data[timeColumnID] == date,:] )
        x_game  = x_game.loc[ (x_game['player1_name'] == player1_ID) & (x_game['player2_name'] == player2_ID) ]
        maxQuote1 = float(x_game['player1_MaxQuote'])
        maxQuote2 = float(x_game['player2_MaxQuote'])
        x_game = preProcessData( x_game, self._cols_to_drop, [], [] )
        x_game.to_csv(pathFileOut  +' _x_game', sep = ",", header=True, index=False, encoding='utf-8')

        return { 'df':df_date, 'X': x_game, 'player1_MaxQuote' : maxQuote1,
                'player2_MaxQuote' : maxQuote2 }



#generic function used to prepocess datas (drop, dummies etc)
def preProcessData( df, cols_to_drop, cols_to_dummies, cols_to_dummies_and_drop ):

    newDf = pd.DataFrame()
    #we dummies the column,
    #column is removed from based df
    for col in cols_to_dummies_and_drop:
        df_with_dummies = pd.get_dummies( df[ col ] )
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

#Generic fuunction
#input a pandas dataframe. 
#return a DF where the row have been duplicated and some cols have been inversed
def duplicateRows( df, cols ):
    df_duplicate = df.copy( True )
    df_duplicate.rename(columns=cols, inplace=True)
    df = pd.concat([df,df_duplicate], axis=0, ignore_index=True )
    return df

###do a function to arrange the shape of the score
##
#try:
#    importExcel = True
#    importGit = False
#    loadChallenge = False
#    loadFutures = False
#    doParseTime = False
#    myRes = cHistTennisData( repoPath, repoGitPath, competitionID, importExcel,
#                        importGit, loadChallenge, loadFutures, doParseTime )
#    myRes.exportData( pathFileOut )
#    print('Job done' )
#except err.cError as e:
#    print( 'An error occured:', e.value )