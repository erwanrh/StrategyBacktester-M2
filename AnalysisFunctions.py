#                               MONESTIER -RAHIS
###############################################################################
#
#
# Ce fichier comporte des fonctions d'analyse de la performance du portefeuille 
#
#
################################################################################

import numpy as np
import math

# MaxDrawDowns

def maxDrawDown(X):

    mdd = 0

    peak = X[0]

    for x in X:

        if x > peak: 

            peak = x

        dd = (peak - x) / peak

        if dd > mdd:

            mdd = dd

    return mdd    



# VaR

def VaR(X, confidenceLevel):

    sortedReturns = X.sort_values()

    return sortedReturns.quantile(1 - confidenceLevel)



# Sharpe Ratio 

def SP(Return, Risk, RiskFreeRate):

    ratio = (Return - RiskFreeRate) / Risk

    return ratio



# Tracking Error 

def TE(Return, BenchReturn):

    ratio = np.std(Return - BenchReturn)*math.sqrt(252)

    return ratio

