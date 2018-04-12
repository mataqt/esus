# -*- coding: utf-8 -*-
"""
Created on Sat Apr  1 15:03:41 2017

@author: Stéphane
"""

import numpy as np
from sklearn.preprocessing import normalize
from sklearn import preprocessing
import datetime
import pandas as pd

#x = np.random.rand(100)*1
#
#print( x )
#print( np.mean(x) )
#print( np.var(x) )
#
#norm2 = normalize(x[:,np.newaxis], norm='l1', axis=0).ravel()
#print(x)
#print('a')
#
#print( norm2 )
#print( np.mean(norm2) )
#print( np.var(norm2) )
#
##X_scaled = preprocessing.scale(norm2)
##print('b')
##print( X_scaled )
##print( np.mean(X_scaled) )
##print( np.var(X_scaled) )
#
#

#n = 100
#y = np.random.binomial( 1, 0.15, n)
##    
#x =  np.random.rand( n ) 
#print( np.abs(np.mean(x)) )   
#print( np.abs(np.mean(x)) )   
#x=np.abs(x)
#x.append( 0 )
#print( np.std(x ))

#print(x)
#print(y)
#print( x)

#print( x[[0,2]])
#print( x[1])


#print( x[:,[1,2]])

#a = np.concatenate((x,y), axis = 0)
#print(a)
#
#
#x = [ [ 'b', 'a'] ]
#print( x[0])
#x.append( ['c','d' ])
#print(x )
#
#num_days = 3
#current_date = datetime.datetime.now()
#print( current_date )
#datetime.datetime(2013, 7, 17, 12, 44, 57, 557000)
#future_date = datetime.datetime(2013, 7, 17)
#print( future_date )
#datetime.datetime(2013, 7, 20, 12, 44, 57, 557000)
df = pd.DataFrame([[1, 2, 3], [4, 5 ,6]], columns=list('ABC'))
df2 = pd.DataFrame([[7, 8, 9], [10,11,12]], columns=list('egh'))

print('df')
print( df )
print('df2')
print(df2)
df = df.rename(index={0: 'a'})
df2 = df2.rename(index={1: 'a'})
#print( 'index')
#print( df )



test = pd.concat([df,df2], axis=1 )
print('test' )
print( test)

















