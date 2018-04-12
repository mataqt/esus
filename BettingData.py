#-------------------------------------------------------------------------------
# Name:        cBettingData
# Purpose:     This file contains several class which can handle the betting
#              data (either live or historical).
#
# Author:      St?phane
#
# Created:     05/02/2017
# Copyright:   (c) St?phane 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import pandas as pd
import cError as err
import matplotlib.pyplot as plt
import datetime as dt
import numpy as np
FUZZ = err.FUZZ

pathfile = "D:\IT\Library\Python\France_Scotland_Rugby_20170212.txt"
pathfileOut = "D:\IT\Library\Python\France_Scotland_Rugby_20170212_out.txt"
data = pd.read_csv(pathfile, sep=";", header = None)
#print data

class cHistBettingData:
    # class used to save and manage all the historical betting datas and information
    # about the bets quote, data and spreads over different time

    #constructor
    # _fileData: the base input containing the Betfair quotes ove time (exchange and sportbook)
    # _comission: the betfair comission in % of the gain
    # _pSportBook: probability from the betfair sportsBook
    # _pExchLay: probability ob the lay side
    # _pExcheBack: probability on the exchanege back side
    # _nBettingSolution: the nulber of team/player on which we can bet
    def __init__(self, pathfile):
        self._pathfile = pathfile
        self._fileData = pd.read_csv(pathfile, sep=";", header = 0)
        self._comission = 0.05
        self._nBettingSolution = -1
        self.transformQuote( "Sportsbook" )
        self.transformQuote( "Exchange_Lay" )
        self.transformQuote( "Exchange_Back" )

        self.probaWithComission( "Exchange_Lay", False)
        self.probaWithComission( "Exchange_Back", True )
        self.midAndSpread()

        self.sum( "Sportsbook" )
        self.sum( "Exchange_Lay" )
        self.sum( "Exchange_Back" )
        self.sum( "Mid" )
        self.sum( "Exchange_Lay_withCom" )
        self.sum( "Exchange_Back_withCom" )
        self.sum( "Mid_withCom" )

        #self.checkArbitrage()

    #this method creates the probabilities out of the quote
    def transformQuote(self, baseName ):
        n = 1
        columnName = baseName + "_" +str(n)
        while columnName in self._fileData.columns:
            n += 1
            columnName = baseName + "_" +str(n)
        if self._nBettingSolution < 0:
            self._nBettingSolution = n
        else:
            err.REQUIRE( n == self._nBettingSolution,
                        "The number of betting solution need to be the same for each book.")
        for i in range(1,n):
            columnName = baseName + "_" +str(i)
            newColumnName = baseName + "_Proba_" + str(i)
            serQuote = self._fileData[columnName]
            serProb = pd.Series( range(0, serQuote.size), None, float )
            for ind, val in serQuote.iteritems():
                if str(val).find("/")  > 0:
                    listStr = val.split("/")
                    err.REQUIRE( len( listStr ),
                                "Invalid quote. The number of string should be 2.")
                    num = float( listStr[0] )
                    den = float( listStr[1] )
                    quote = ( num + den )/ den
                    err.REQUIRE( quote >= FUZZ,
                                "The quotes must be positive.")
                    serProb[ind] = 1. / quote
                else:
                    if isinstance( val, basestring ):
                        err.REQUIRE( float(val) >= FUZZ, "The quotes must be positive.")
                        serProb[ind] = 1. / float( val )
                    else:
                        err.REQUIRE( val >= FUZZ, "The quotes must be positive.")
                        serProb[ind]= 1. / val
            self._fileData[newColumnName] = serProb

    #this method creates the mid probabilities and spread
    def midAndSpread( self ):
        backBaseName = "Exchange_Back_Proba_"
        backLayName = "Exchange_Lay_Proba_"
        self.midAndSpread_create( backBaseName, backLayName, "" )
        backBaseName = "Exchange_Back_withCom_Proba_"
        backLayName = "Exchange_Lay_withCom_Proba_"
        extraString = "withCom_"
        self.midAndSpread_create( backBaseName, backLayName, extraString )

    #this method creates the mid probabilities and spread
    def midAndSpread_create( self, baseNameBack, baseNameLay, extraString ):
        err.REQUIRE( self._nBettingSolution > 0,
                    "The number of betting solution must be positive.")
        for i in range(1,self._nBettingSolution):
            columnNameBack = baseNameBack +str(i)
            columnNameLay = baseNameLay + str(i)
            backProb = self._fileData[columnNameBack]
            layProb = self._fileData[columnNameLay]
            sizeSer = layProb.size
            midProb = pd.Series( range(0, sizeSer), None, float )
            spread = pd.Series( range(0, sizeSer), None, float )
            for ind in range(0,sizeSer):
                probaUp = backProb[ind]
                probaLow = layProb[ind]
                spread[ind]= probaUp - probaLow
                midProb[ind] = (probaUp + probaLow ) / 2.
            self._fileData["Mid_" + extraString + "Proba_" + str(i)] = midProb
            self._fileData["Spread_" + extraString+ "Proba_" + str(i)] = spread

    #this method creates the probabilities out of the quote
    def sum( self, baseName ):
        err.REQUIRE( self._nBettingSolution > 0,
                    "The number of betting solution must be positive.")
        sumProb = pd.Series( range(1, self._fileData["Time"].size + 1), None, float )
        for ind in range(0,sumProb.size):
            sumLoc = 0
            for i in range(1,self._nBettingSolution):
                columnName = baseName + "_Proba_" +str(i)
                sumLoc += self._fileData[columnName][ind]
            sumProb[ind] = sumLoc
        self._fileData[baseName +"_SumProba"] = sumProb

    #this method creates the probabilities out of the quote
    def probaWithComission( self, baseName, isBack ):
        err.REQUIRE( self._nBettingSolution > 0,
                    "The number of betting solution must be positive.")
        for i in range( 1, self._nBettingSolution ):
            columnName = baseName + "_Proba_" +str(i)
            prob = pd.Series( range(1, self._fileData["Time"].size + 1), None, float )
            baseProb = self._fileData[columnName]
            for ind in range(0,prob.size):
                profit = ( 1. / baseProb[ind] ) - 1
                if isBack:
                    profit *= (1.0 - self._comission )
                else:
                    profit /= (1.0 - self._comission )
                quote = profit + 1
                prob[ind] = 1.0 / quote
            self._fileData[baseName+"_withCom_Proba_"+str(i)] = prob

    def export(self, pathfileOut ):
        err.REQUIRE( pathfileOut != self._pathfile, "You cannot export the results to the input file" )
        self._fileData.to_csv( pathfileOut, sep=";")

    def printChart(self):
        plt.Figure()
        self.printChartSub( ["Time","Mid_Proba_1","Mid_Proba_2", "Mid_Proba_3"], doSubPlots = True )
        self.printChartSub( ["Time","Spread_Proba_1","Spread_Proba_2", "Spread_Proba_3"], doSubPlots = False  )
##        self.printChartSub( ["Time","Exchange_Back_Proba_1","Exchange_Back_Proba_2",
##                            "Exchange_Back_Proba_3"], doSubPlots = True )
##        self.printChartSub( ["Time","Exchange_Lay_Proba_1","Exchange_Lay_Proba_2",
##                                "Exchange_Lay_Proba_3"], doSubPlots = True)
        self.printChartSub( ["Time","Sportsbook_Proba_1","Sportsbook_Proba_2",
                                "Sportsbook_Proba_3"], doSubPlots = True)
        self.printChartSub( ["Time","Exchange_Back_SumProba"], doSubPlots = False )
        self.printChartSub( ["Time","Exchange_Lay_SumProba"], doSubPlots = False )
        self.printChartSub( ["Time","Sportsbook_SumProba"], doSubPlots = False )
        self.printChartSub( ["Time","Mid_SumProba"], doSubPlots = False )


        self.printChartSub( ["Time","Mid_withCom_Proba_1","Mid_withCom_Proba_2", "Mid_withCom_Proba_3"], doSubPlots = True )
        self.printChartSub( ["Time","Spread_withCom_Proba_1","Spread_withCom_Proba_2", "Spread_withCom_Proba_3"], doSubPlots = False  )

        self.printChartSub( ["Time","Exchange_Back_withCom_Proba_1","Exchange_Back_withCom_Proba_2",
                            "Exchange_Back_withCom_Proba_3"], doSubPlots = True )
        self.printChartSub( ["Time","Exchange_Lay_withCom_Proba_1","Exchange_Lay_withCom_Proba_2",
                                "Exchange_Lay_withCom_Proba_3"], doSubPlots = True)
        self.printChartSub( ["Time","Sportsbook_Proba_1","Sportsbook_Proba_2",
                                "Sportsbook_Proba_3"], doSubPlots = True)
##        self.printChartSub( ["Time","Exchange_Back_withCom_SumProba"], doSubPlots = False )
##        self.printChartSub( ["Time","Exchange_Lay_withCom_SumProba"], doSubPlots = False )
##        self.printChartSub( ["Time","Sportsbook_SumProba"], doSubPlots = False )
##        self.printChartSub( ["Time","Mid_withCom_SumProba"], doSubPlots = False )

        self.printChartSub( ["Time","Sportsbook_Proba_1","Exchange_Back_Proba_1",
                                "Exchange_Lay_Proba_1", "Mid_Proba_1",
                                 "Mid_withCom_Proba_1", "Exchange_Back_withCom_Proba_1",
                                  "Exchange_Lay_withCom_Proba_1"], doSubPlots = False)

        self.printChartSub( ["Time","Sportsbook_Proba_2","Exchange_Back_Proba_2",
                                "Exchange_Lay_Proba_2", "Mid_Proba_2",
                                 "Mid_withCom_Proba_2", "Exchange_Back_withCom_Proba_2",
                                  "Exchange_Lay_withCom_Proba_2"], doSubPlots = False)

        self.printChartSub( ["Time","Sportsbook_SumProba","Exchange_Back_SumProba",
                                "Exchange_Lay_SumProba", "Mid_SumProba",
                                 "Mid_withCom_SumProba", "Exchange_Back_withCom_SumProba",
                                  "Exchange_Lay_withCom_SumProba"], doSubPlots = False)

        self.printChartSub( ["Time","Sportsbook_Proba_3","Exchange_Back_Proba_3",
                                "Exchange_Lay_Proba_3", "Mid_Proba_3",
                                 "Mid_withCom_Proba_3", "Exchange_Back_withCom_Proba_3",
                                  "Exchange_Lay_withCom_Proba_3"], doSubPlots = False)

        self.printChartSub( ["Time","Spread_Proba_1","Spread_Proba_2", "Spread_Proba_3",
                            "Spread_withCom_Proba_1","Spread_withCom_Proba_2", "Spread_withCom_Proba_3"],
                            doSubPlots = False  )


        plt.gcf().autofmt_xdate()
        plt.show()

    def printChartSub(self, subSerie, doSubPlots):
        df = self._fileData[ subSerie ]
        df.plot()
        if doSubPlots:
            df.plot(subplots=True, figsize=(6, 6))


try:
    myRes = cHistBettingData( pathfile )
    myRes.export( pathfileOut )
    myRes.printChart()
    #print myRes._fileData
except err.cError as e:
    print 'An error occured:', e.value