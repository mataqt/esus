#-------------------------------------------------------------------------------
# Name:        Regress
# Purpose:     Regression Models
#
# Author:      Matars
#
#
# Created:     01/04/2017
# Copyright:   (c) St?phane 2017
# Licence:     <your licence>
#-------------------------------------------------------------------------------

import numpy as np
import Error as err
import abc
import sklearn
from sklearn import linear_model
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import Imputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import PolynomialFeatures
from sklearn.decomposition import TruncatedSVD
from sklearn.decomposition import PCA
FUZZ = err.FUZZ


class cRegression:
    #class used to perform regression (mother class)
    __metaclass__ = abc.ABCMeta 
    # center: center the x parameters(bool)
    # reduce: reduce the x parameters(bool)
    # normalize: normalize the values(bool)
    # colsToStandardize: cols to standardize
    # categoricalCols: categorical cols
    # fit_intercept: do ze fit the intercept(bool)
    # n_cpu: number of cpu the code can use. If -1, it will use the max number.
    # Useful when several params to regress
    # AdjustNan: shall we transform the Nan values (to their mean, can be enhanced)
    # dimReduc: the dimension reduction method. It can be None, TruncSVD, PCA. TruncSVD is used for sparse input
    # nDimReduc: the number of cols after the dimnesion reduction
    # usePolynomialFeature: shall we generate polynomial values out of colsToPoly
    # nPolynomialDegree: the degree of the polynome
    # colsToPoly: the column on which we will apply the polynomial transformation
    def __init__(self,
                 center = True,
                 reduce = True,
                 normalize = False,
                 colsToStandardize = [],
                 transformCategorical = True,
                 categoricalCols = [],
                 fit_intercept = True,
                 n_cpu = -1,
                 adjustNaN = True,
                 dimReduc = None,
                 nDimReduc = -1,
                 usePolynomialFeature = False,
                 nPolynomialDegree = 1,
                 colsToPoly = []
                 ):
        self._center = center
        self._reduce = reduce
        self._normalize = normalize
        self._transformCategorical = transformCategorical 
        self._fit_intercept = fit_intercept
        self._n_cpu = n_cpu
        self._colsToStandardize = colsToStandardize
        self._categoricalCols = categoricalCols
        self._adjustNaN = adjustNaN
        
        self._scaler = StandardScaler( with_mean=self._center, with_std=self._reduce)#use to stand
        self._imputer = Imputer(missing_values='NaN', strategy='mean', axis=0) #Use to remove NaN
        self._model = None #The model, set up in their respective class
        self._encoder = OneHotEncoder(categorical_features='all', dtype=str,
                                      handle_unknown='error', n_values=[2, 3, 4], sparse=True)
        self._svd = None#svd, set later
        
        self._dimReduc = dimReduc
        self._nDimReduc = nDimReduc
        self._usePolynomialFeature = usePolynomialFeature
        self._nPolynomialDegree = nPolynomialDegree
        self._colsToPoly = colsToPoly
        self._poly = PolynomialFeatures(degree=self._nPolynomialDegree, interaction_only=False, 
                                        include_bias=True)
        
        err.REQUIRE( not ( self._doStandardize() and self._normalize ),
                    'You cannot standardize and normalize the values at the same Time')
        err.REQUIRE( self._dimReduc == None or self._nDimReduc > 0,
                    'The dimension reduction method is ' + str(self._dimReduc) + ' and the dimension is negative' )
        self._doTruncSVD = ( self._dimReduc == 'TruncSVD')
        self._doPCA = ( self._dimReduc == 'PCA')
        err.REQUIRE( self._dimReduc == None or self._doTruncSVD or self._doPCA ,
                    'The dimension reduction method ' + str(self._dimReduc) +' is unknown.' )
        err.REQUIRE( not self._usePolynomialFeature or self._nPolynomialDegree >0 ,
                    'When using the polynomial transformation, the degree of the polynome need to be positive' )  
    
    #public
    def setCatAnddStandardizeCols(self, colsToStandardize, categoricalCols, colsToPoly ):
        self._colsToStandardize = colsToStandardize
        self._categoricalCols = categoricalCols
        self._colsToPoly = colsToPoly
    
    #private
    #boolean: shall we standardize the value
    def _doStandardize(self):
        return ( self._center or self._reduce ) and len( self._colsToStandardize ) > 0
    
    #private
    #boolean: shall we transform categorical values
    def _doTransformCategorical(self):
        return self._transformCategorical and len( self._categoricalCols ) > 0
    
    #private
    #boolean: shall we transform categorical values
    def _doUseColsToPoly(self):
        return self._usePolynomialFeature and len( self._colsToPoly )> 0    
    #private
    #return the standardize X
    def _calibStandardize(self, X):
        return self._scaler.fit_transform( X )
 
    #private
    #function use to replace Nan values
    def _removeNaN( self, X):
        return self._imputer.fit_transform(X)
    
    #private
    #function to know if we reduce the dimension
    def _doReduceDim(self):
        return (self._dimReduc != None)
    
    #private
    #return the dimension reduction. It can be a dynamic function (see logit regression for instance)
    def _getDimensionReduction(self, X):
        nCols = X.shape[1]
        return min( self._nDimReduc, nCols )
    
    #private
    #return the standardize X
    def _reduceDim(self, X):
        nToUse = self._getDimensionReduction( X )
        if self._doTruncSVD:
            self._svd = TruncatedSVD(algorithm='arpack', n_components=nToUse)
        elif self._doPCA:
            self._svd = PCA(n_components=nToUse, svd_solver ='auto')
        else:
            err.ERROR( 'Unkown reduction dimensionality method' )
        return self._svd.fit_transform(X)
    
    #private
    #return the polynomial transform of x
    def _polynomialTransform(self, X):
        return self._poly.fit_transform(X)
        
    
    #private
    #transform the categorical data
    def _transformCatForCalib(self, X):      
        return self._encoder.fit_transform( X ).toarray()

    
    #private
    #adjust the input
    def _adjustInput(self, X):
        XtoUse = X
        if self._doTransformCategorical():
            XtoUse[self._categoricalCols] = self._transformCatForCalib( XtoUse[self._categoricalCols])
        if self._adjustNaN:
            XtoUse = self._removeNaN( XtoUse )
        
        if self._doUseColsToPoly():
            Xpoly = self._polynomialTransform( XtoUse[:,self._colsToPoly] )
            if self._doStandardize():
                Xpoly = self._calibStandardize( Xpoly )
            XtoUse = np.delete( XtoUse, self._colsToPoly, axis = 1 )
            XtoUse = np.append( XtoUse, Xpoly, axis = 1 )
        elif self._doStandardize():
            XtoUse[:,self._colsToStandardize] = self._calibStandardize( XtoUse[:,self._colsToStandardize] )
        
        if self._doReduceDim():
            XtoUse = self._reduceDim(XtoUse)
        return XtoUse
    
    #private
    #return the adjust X we use fir the regession
    def _getXtoRegress(self, X):
        XtoUse = X
        if self._adjustNaN:
            XtoUse = self._imputer.transform( XtoUse )

        if self._doTransformCategorical():
             XtoUse[self._categoricalCols] = self._encoder.transform( XtoUse[self._categoricalCols]).toarray()
        
        if self._doUseColsToPoly():
            Xpoly = self._poly.transform( XtoUse[:,self._colsToPoly] )
            if self._doStandardize():
                Xpoly = self._scaler.transform( Xpoly )
            XtoUse = np.delete( XtoUse, self._colsToPoly, axis = 1 )
            XtoUse = np.append( XtoUse, Xpoly, axis = 1 )          
        elif self._doStandardize():
            XtoUse[:,self._colsToStandardize] = self._scaler.transform( XtoUse[:,self._colsToStandardize] )  
                
        if self._doReduceDim():
            XtoUse = self._svd.transform(XtoUse)
        return XtoUse
            
    #public
    #calibrate the regression model
    # X: the data, y the params to fit
    # weight can be None, Auto or a vector
    def calibrate(self, X, y, weight = None ):
        XtoUse = self._adjustInput( X )
        self._adjustParam( XtoUse, y, weight )
        self._fitModel(XtoUse, y, weight)
        
        
    #private
    #extra adjustment of the regression model pre calibration (e;g, solver selection)
    @abc.abstractmethod
    def _adjustParam(self, X, y, weight ):
        pass
    
    #private
    def _fitModel(self, X, y, weight ):
        self._model.fit( X, y, weight )
        
    #public
    #return the residues
    def getScore(self, X, y, weight = None ):
        XtoUse = self._adjustInput( X )
        self._adjustParam( XtoUse, y, weight )      
        return self._model.score(XtoUse, y, weight )
    
    #public
    #predict the results for a given X
    def predict(self, X):
        XtoUse = self._getXtoRegress(X)
        return self._predict_class( XtoUse)
    
    #private
    #predict the results for a given X and a given class
    #the call can be different for eqch sub class (e.g, predict, predict_proba)
    def _predict_class(self, X):
        err.ERROR( 'predict_class has not been defined for ' + self.getClassID())
        pass
    
    #public
    def getParams(self):
        return self._model.get_params()
    
    #public and virtual
    #return the class ID
    def getClassID(self):
        return( 'cRegression' )
        pass

class cLinearRegression_simple(cRegression):
    # class used to perform a simple linear regression
    
    # center: center the x parameters(bool)
    # reduce: reduce the x parameters(bool)
    # normalize: normalize the values(bool)
    # colsToStandardize: cols to standardize
    # categoricalCols: categorical cols
    # fit_intercept: do ze fit the intercept(bool)
    # n_cpu: number of cpu the code can use. If -1, it will use the max number.
    # Useful when several params to regress
    # AdjustNan: shall we transform the Nan values (to their mean, can be enhanced)
    # dimReduc: the dimension reduction method. It can be None, TruncSVD, PCA
    # nDimReduc: the number of cols after the dimnesion reduction
    # usePolynomialFeature: shall we generate polynomial values out of colsToPoly
    # nPolynomialDegree: the degree of the polynome
    # colsToPoly: the column on which we will apply the polynomial transformation
    def __init__(self,
                 center = True,
                 reduce = True,
                 normalize = False,
                 colsToStandardize = [],
                 transformCategorical = True,
                 categoricalCols = [],
                 fit_intercept = True,
                 copy_X = False,
                 n_cpu = -1,
                 adjustNaN = True,
                 dimReduc = None,
                 nDimReduc = -1,
                 usePolynomialFeature = False,
                 nPolynomialDegree = 1,
                 colsToPoly = []
                 ):
        cRegression.__init__(self, 
                             center,
                             reduce, 
                             normalize,
                             colsToStandardize,
                             transformCategorical,
                             categoricalCols,
                             fit_intercept,
                             n_cpu,
                             adjustNaN,
                             dimReduc,
                             nDimReduc,
                             usePolynomialFeature,
                             nPolynomialDegree,
                             colsToPoly )
        self._model = linear_model.LinearRegression(fit_intercept, normalize, copy_X, n_cpu)

    #public and virtual
    #return the class ID
    def getClassID(self):
        return( 'cLinearRegression' )
        pass
    
    #private
    #predict the results for a given X and a given class
    def _predict_class(self, X):
        return self._model.predict( X )
        
        
class cLinearRegression_logit(cRegression):
    # class used to perform a logit linear regression
    
    # center: center the x parameters(bool)
    # reduce: reduce the x parameters(bool)
    # normalize: normalize the values(bool)
    # colsToStandardize: cols to standardize
    # categoricalCols: categorical cols
    # fit_intercept: do we fit the intercept (bool)
    # n_cpu: number of cpu the code can use. If -1, it will use the max number.
    # Useful when several params to regress
    # penalty: the loss function, 'l1' or 'l2'.
    # smart_g_ess: solution of the previous call as smart guess. Speed up?
    # multi_class: str, {‘ovr’, ‘multinomial’}, default: ‘ovr’ or ‘multinomial’. 
    # If the option chosen is ‘ovr’, then a binary problem is fit for each label. 
    # Else the loss minimised is the multinomial loss fit across the entire probability distribution. 
    #is_mutlnomial: multinomial logistic regresion
    # has_moreSamples: true if n_samples > n_features
    # AdjustNan: shall we transform the Nan values (to their mean, can be enhanced)
    # dimReduc: the dimension reduction method. It can be None, TruncSVD, PCA
    # nDimReduc: the number of cols after the dimnesion reduction
    # usePolynomialFeature: shall we generate polynomial values out of colsToPoly
    # nPolynomialDegree: the degree of the polynome
    # colsToPoly: the column on which we will apply the polynomial transformation
    def __init__(self,
                 center = True,
                 reduce = True,
                 normalize = False,
                 colsToStandardize = [],
                 transformCategorical = True,
                 categoricalCols = [],
                 fit_intercept = True,
                 n_cpu = -1, 
                 penalty = 'l2', 
                 smart_guess = True,
                 multi_class = 'ovr',
                 adjustNaN = True,
                 dimReduc = None,
                 nDimReduc = -1,
                 ruleOfTen = False,
                 usePolynomialFeature = False,
                 nPolynomialDegree = 1,
                 colsToPoly = []
                 ):
        cRegression.__init__(self, 
                             center,
                             reduce, 
                             normalize,
                             colsToStandardize,
                             transformCategorical,
                             categoricalCols,
                             fit_intercept,
                             n_cpu,
                             adjustNaN,
                             dimReduc,
                             nDimReduc,
                             usePolynomialFeature,
                             nPolynomialDegree,
                             colsToPoly )
        self._penalty = penalty
        self._smart_guess = smart_guess
        self._multi_class = multi_class
        self._ruleOfTen = ruleOfTen
        #default value
        solver = 'liblinear'
        dual = False
        class_weight=None
        random_state=None
        tol=0.0001
        C=1.0
        intercept_scaling=1
        class_weight = None
        max_iter = 50
        random_state=None
        verbose = 0
        self._model = linear_model.LogisticRegression(penalty, dual, tol, C, 
                                                  self._fit_intercept, intercept_scaling, 
                                                  class_weight, random_state, solver,
                                                  max_iter, self._multi_class, verbose, 
                                                  self._smart_guess, self._n_cpu )
    
    #public and virtual
    #return the class ID
    def getClassID(self):
        return( 'cLinearRegression' )
        pass

    #private
    #return the dimension reduction. It can be a dynamic function (see logit regression for instance)
    def _getDimensionReduction(self, X):
        if self._ruleOfTen:
            return int(X.shape[0] / 10)
        return super(cLinearRegression_logit, self)._getDimensionReduction(X)

    #private
    #extra adjustment of the regression model pre calibration (e;g, solver selection)
    @abc.abstractmethod
    def _adjustParam(self, X, y, weight ):
        newSolver = self._getSolver( y )
        newDual = self._getDual( newSolver, X )
        self._model.set_params( solver = newSolver, dual = newDual )

    #private
    #return the most efficient solver based on the input
    # return {‘newton-cg’, ‘lbfgs’, ‘liblinear’, ‘sag’}
    # For small datasets, ‘liblinear’ is a good choice, whereas ‘sag’ is faster for large ones.
    # For multiclass problems, only ‘newton-cg’, ‘sag’ and ‘lbfgs’ handle  multinomial loss;
    def _getSolver(self, y ):
        if self._penalty != 'l2':
            return 'liblinear'
        isMultinomial = ( len( y.shape ) > 1 ) and ( y.shape[1] > 0 )
        if not isMultinomial:
            return 'sag' #default choice, run speed test
        else:
            return 'newton-cg' #run speed test
        
    #private
    #return a boolean for Dual or primal formulation. 
    #False when n_samples > n_features.
    def _getDual(self, solver, X ):
        if solver == 'sag' or self._penalty != 'l2':
            return False
        nSample = X.shape[0]
        nFeature = X.shape[1]
        if nSample > nFeature:
            return False
        else:
            return True
    
    #private
    #predict the results for a given X and a given class
    def _predict_class(self, X ):
        return self._model.predict_proba( X )

#try:
##    importOne = False
##    importGit = True
##    loadChallenge = False
##    loadFutures = False
##    doParseTime = False
##    myRes = HistData.cHistTennisData( repoPath, repoGitPath, competitionID, importOne,
##                        importGit, loadChallenge, loadFutures, doParseTime )
##    myRes.exportData( pathFileOut )
##    myRes.preProcessData( )
##    myRes.exportData( pathFileOut + 'temp' )
#    n = 1000
#    y = np.random.binomial( 1, 0.45, n)
#    
#    x =  np.random.rand( n, 10 )    
#    regressor = cLinearRegression_logit( center = True,
#                                         reduce = True,
#                                         normalize = False,
#                                         fit_intercept = True,
#                                         n_cpu = -1, 
#                                         penalty = 'l2', 
#                                         smart_guess = True,
#                                         multi_class = 'ovr' )
#    print( regressor.getClassID() )
#
#                     
#    regressor.calibrate( x, y )
##
##    
#    print( regressor.getScore( x, y ) )
#    print( regressor._model.intercept_ )
#    print( regressor._model.coef_ )
#    print( 'results' )
##    
#    a =  np.random.rand( 1, 10 )
#    res = regressor.predict( a )
#    print( a )
##    
##
##    print( len(y.shape) )
#    print( 'Job done in cRegression' )
#    
#except err.cError as e:
#    print( 'An error occured:', e.value )
