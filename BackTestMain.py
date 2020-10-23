###############################################################################
#                     Back test : short call delta hedeged 
#                               MONESTIER - RAHIS 
#                                     M2 EIF 
#
###############################################################################
#Instructions : 
# *** Bien vérifier le remplissage du fichier PARAMETERS.xlsx
# *** Vérifier le WorkingDirectory 
#

###############################################################################

# libraries
print('0%  - Libraries are being imported')
import pandas as pd
import matplotlib as mp
from datetime import datetime
import math
import numpy as np
import seaborn as sns 
import os
import BloomImport #Script d'import Bloomberg
#Hide copy warnings
pd.options.mode.chained_assignment = None 

#Import des paramètres
Params = pd.read_excel('Parameters.xlsx' , index_col=0,header=1)

#Imports Bloomberg selon le paramètre choisi dans le fichier Parameters
if bool(Params['P']['importBloom']) == True :
   print('6%  - Bloomberg data are being imported')
   BloomImport.RunBDH(Params['P'][['SYYYY','SMM','SDD','EYYYY','EMM','EDD']]) 


### I - Data (excel imports) and parameters 

# specific dates 

DateDelete = datetime(2019,5,1) # holiday to be deleted 

Sylvester = datetime(2018,12,31) # holiday delta mid to be filled 


print('12% - Excel dataframes are being imported')
# options (names) import 

thirdfriday = pd.read_excel('Dataframes/output_THIRDFRIDAY.xlsx')
thirdfriday.set_index(thirdfriday['Date'], drop=True,inplace=True) # dates as index 



# options (px last) import 
sorted_data_PXLAST = pd.read_excel('Dataframes/output_OPTPRICE.xlsx')    
sorted_data_PXLAST.set_index(sorted_data_PXLAST['date'], drop=True,inplace=True) # dates as index
#sorted_data_PXLAST = sorted_data_PXLAST.drop([DateDelete]) # delete holiday 


# options (delta mid) import 
sorted_data_MID = pd.read_excel('Dataframes/output_DELTAMID.xlsx')

#Manipulation des dates : la date du 31/12/2018 n'est pas extraite pas Bloomberg, nous devons l'ajout manuellement
#Ligne additionnelle
sorted_data_MID = pd.concat([pd.DataFrame({'date':Sylvester,thirdfriday['Call'][0]: 0.324}, index=[0]),sorted_data_MID.iloc[:]], sort=False).reset_index(drop=True) #Ajout de la ligne
sorted_data_MID.set_index('date', drop=True,inplace=True) #Nous mettons les dates en index


# futures (px last) import 
Futures_Price = pd.read_excel('Dataframes/output_FUTPRICE.xlsx')
Futures_Price.set_index(Futures_Price['date'], drop=True,inplace=True)

# indices import 
Indices_Price = pd.read_excel('Dataframes/output_INDICES.xlsx')
Indices_Price.set_index('date', drop=True,inplace=True)


# indices risk and return 
IndexNames= Indices_Price.columns

#Fonction qui retourne une liste avec les données des indices
def CalcIndex(Index_Name):
    Index_Prices=Indices_Price[Index_Name]
    Index_Return= Index_Prices.pct_change()
    Index_Return[0]=0
    Index_Annualized_Return = ((Index_Prices.tail(1)/Index_Prices[0])**(252/len(Index_Prices))-1).iloc[0]
    Index_Annualized_Risk = np.std(Index_Return)*math.sqrt(252) 
    return{'Name':Index_Name,'Return':Index_Return,'Annualized_Return':Index_Annualized_Return,'Annualized_Risk':Index_Annualized_Risk}

#Création d'un dictionnaire avec les données des indices : Rendements, Risque, Nom et moy des rendements
print('18% - Compution of index data')
IndexData= {}

for idx in IndexNames:
    IndexData[idx]=(CalcIndex(idx))



# parameters 
print('24% - Starting BackTest')
InitInvest = Params['P']['InitInvest'] # initial investment 
Not = Params['P']['Not']  # invested notional 
Tick = Params['P']['Tick']  # tick 
TransFees = Params['P']['TransFees']  # fees 
StartDate = sorted_data_PXLAST.index[0] # initial date 
EndDate = thirdfriday.index[-1] # last date (maturity of the last option) # datetime(2019,10,9) pour tester avec prof 
RiskFreeRate =  Params['P']['RiskFreeRate'] 


# backtest function 

def BackTest(InitInvest, Not, Tick, TransFees, StartDate, EndDate, WithHedge):

    # create portfolio df  

    Portfolio = pd.DataFrame(columns=['NB_CALL','SC_NOT','PNL_CALL','PERF_CALL','PERF_CALL_CONTRIB','NEXT_CALL','NB_FUT','FUT_NOT','PNL_FUT','PERF_FUT','PERF_FUT_CONTRIB','DELTA_HEDGE', 'VAL_PF','PF_RETURNS','PF_COMPOUNDED_RETURNS'],index = sorted_data_MID.index[sorted_data_MID.index>=StartDate] & sorted_data_MID.index[sorted_data_MID.index<=EndDate]) 

    # init (fill first row = first date)

    Portfolio['VAL_PF'][StartDate] = InitInvest # val ptf 

    Portfolio['NB_CALL'][StartDate] = -round(Portfolio['VAL_PF'][StartDate]*Not/Indices_Price['SX5E Index'][StartDate]/Tick,0) # nb call 

    Portfolio['PNL_CALL'][StartDate] = 0 # pnl call 

    Portfolio['PERF_CALL'][StartDate] = 0 # perf call 

    Portfolio['PERF_CALL_CONTRIB'][StartDate] = 100 # perf call contrib to ptf perf 

    Portfolio['NEXT_CALL']=thirdfriday['Call'].shift(-1) # next call name 

    Portfolio['NEXT_CALL'][StartDate]=thirdfriday['Call'][0]

    Portfolio["NEXT_CALL"].fillna( method ='ffill', inplace = True) # fill next call names 

    Portfolio['SC_NOT'][StartDate] = Portfolio['NB_CALL'][StartDate]*Tick*Indices_Price['SX5E Index'][StartDate]/Portfolio['VAL_PF'][StartDate] # short call not

    if WithHedge == 1: # hedging 

        Portfolio['DELTA_HEDGE'][StartDate] = -Portfolio['SC_NOT'][StartDate]*sorted_data_MID[thirdfriday['Call'][0]][StartDate] # delta hedge 

        Portfolio['NB_FUT'][StartDate] = round(Portfolio['VAL_PF'][StartDate]*Portfolio['DELTA_HEDGE'][StartDate]/Futures_Price['VG1 Index'][StartDate]/Tick,0) # nb fut 

        Portfolio['PNL_FUT'][StartDate] = 0 # pnl fut 

        Portfolio['PERF_FUT'][StartDate] = 0 # perf fut 

        Portfolio['PERF_FUT_CONTRIB'][StartDate] = 100 # perf fut contrib to ptf perf 

        Portfolio['FUT_NOT'][StartDate] = Portfolio['NB_FUT'][StartDate]*Tick*Indices_Price['SX5E Index'][StartDate]/Portfolio['VAL_PF'][StartDate] # short fut not 

    else: # no hedging 

        Portfolio['DELTA_HEDGE'][StartDate] = 0

        Portfolio['NB_FUT'][StartDate] = 0

        Portfolio['PNL_FUT'][StartDate] = 0 

        Portfolio['PERF_FUT'][StartDate] = 0 

        Portfolio['PERF_FUT_CONTRIB'][StartDate] = 0

        Portfolio['FUT_NOT'][StartDate] = 0

    roll = 1

    # loop to fill df  

    for dd in Portfolio.index[Portfolio.index>StartDate]:

        if roll == 1: # in case of rool : take in account transaction fees 

            Portfolio['PNL_CALL'].loc[dd]=Portfolio['NB_CALL'][StartDate]*Tick*(sorted_data_PXLAST[Portfolio['NEXT_CALL'][StartDate]][dd]-sorted_data_PXLAST[Portfolio['NEXT_CALL'][StartDate]][StartDate])*(1-TransFees) # pnl call with transaction fees

        else:

            Portfolio['PNL_CALL'].loc[dd]=Portfolio['NB_CALL'][StartDate]*Tick*(sorted_data_PXLAST[Portfolio['NEXT_CALL'][StartDate]][dd]-sorted_data_PXLAST[Portfolio['NEXT_CALL'][StartDate]][StartDate]) # pnl call without transaction fees 

        if WithHedge == 1: # hedging

            Portfolio['PNL_FUT'].loc[dd] = Portfolio['NB_FUT'][StartDate] * Tick * (Futures_Price['VG1 Index'][dd]-Futures_Price['VG1 Index'][StartDate])*(1-TransFees) # pnl fut 

        else: # no hedging 

            Portfolio['PNL_FUT'].loc[dd] = 0

        Portfolio['VAL_PF'].loc[dd] = Portfolio['VAL_PF'][StartDate] + Portfolio['PNL_CALL'][dd]+ Portfolio['PNL_FUT'][dd] # val ptf

        Portfolio['PERF_CALL'].loc[dd] = Portfolio['PNL_CALL'][dd]/Portfolio['VAL_PF'][StartDate] # perf call

        Portfolio['PERF_CALL_CONTRIB'].loc[dd] = Portfolio['PERF_CALL_CONTRIB'][StartDate]*(1+Portfolio['PNL_CALL'][dd]/Portfolio['VAL_PF'][StartDate]) # perf call contrib to ptf perf         

        if WithHedge == 1: # hedging

            Portfolio['PERF_FUT'].loc[dd] = Portfolio['PNL_FUT'][dd]/Portfolio['VAL_PF'][StartDate] # perf fut

            Portfolio['PERF_FUT_CONTRIB'][dd] = Portfolio['PERF_FUT_CONTRIB'][StartDate]*(1+Portfolio['PNL_FUT'][dd]/Portfolio['VAL_PF'][StartDate]) # perf fut contrib to ptf perf 

        else: # no hedging 

            Portfolio['PERF_FUT'].loc[dd] = 0

            Portfolio['PERF_FUT_CONTRIB'].loc[dd] = 0

        if  Portfolio['NEXT_CALL'].loc[dd] ==  Portfolio['NEXT_CALL'][StartDate]: # in case of roll 

            Portfolio['NB_CALL'].loc[dd]=Portfolio['NB_CALL'][StartDate] # nb call (= previous date nbr call if next call is still the same)

            roll = 0

        else:

            Portfolio['NB_CALL'].loc[dd]=-round(Portfolio['VAL_PF'][dd]*Not/Indices_Price['SX5E Index'][dd]/Tick,0) # nb call (if previous call is at maturity)

            roll = 1

        Portfolio['SC_NOT'].loc[dd] = Portfolio['NB_CALL'][dd]*Tick*Indices_Price['SX5E Index'][dd]/Portfolio['VAL_PF'][dd]  # short call notional

        if WithHedge == 1: # hedging

            Portfolio['DELTA_HEDGE'].loc[dd]= -Portfolio['SC_NOT'][dd] *sorted_data_MID[Portfolio['NEXT_CALL'][dd]][dd] # delta hedge

            Portfolio['NB_FUT'].loc[dd] = round( Portfolio['VAL_PF'][dd]*Portfolio ['DELTA_HEDGE'][dd]/Futures_Price['VG1 Index'][dd]/Tick,0) # nb fut 

            Portfolio['FUT_NOT'].loc[dd]=Tick*Portfolio ['NB_FUT'][dd]*Indices_Price['SX5E Index'][dd] / Portfolio['VAL_PF'][dd] # fut notional 

        else: # no hedging 

            Portfolio['DELTA_HEDGE'].loc[dd]= 0

            Portfolio['NB_FUT'].loc[dd] = 0

            Portfolio['FUT_NOT'].loc[dd]=0

        StartDate = dd 

    

    Portfolio['PF_RETURNS'] = Portfolio['VAL_PF'].pct_change()

    Portfolio['PF_RETURNS'].iloc[0] = 0 # ptf return (1st period)

    Portfolio['PF_COMPOUNDED_RETURNS'] = (1 + Portfolio['PF_RETURNS']).cumprod()*100

    Portfolio['PF_COMPOUNDED_RETURNS'].iloc[0] = 100 # compounded returns starting from 100



    return Portfolio



### II - Short call strategy (without delta hedge) and without transaction fees 
print('30% - Starting Strategy 1')

ShortCall_WithoutHedge = BackTest(InitInvest, Not, Tick, 0, StartDate, EndDate, 0) # no transaction fees and no hedging 

ShortCall_WithoutHedge_Annualized_Return = ((ShortCall_WithoutHedge['VAL_PF'].tail(1)/ShortCall_WithoutHedge['VAL_PF'][0])**(252/len(ShortCall_WithoutHedge['VAL_PF']))-1).iloc[0]

ShortCall_WithoutHedge_Annualized_Risk = np.std(ShortCall_WithoutHedge['PF_RETURNS'])*math.sqrt(252)



### III - Short call strategy (without delta hedge) and with transaction fees 
print('36% - Starting Strategy 2')

ShortCall_WithoutHedge_Fees = BackTest(InitInvest, Not, Tick, TransFees, StartDate, EndDate, 0) # transaction fees and no hedging 

ShortCall_WithoutHedge_Fees_Annualized_Return = ((ShortCall_WithoutHedge_Fees['VAL_PF'].tail(1)/ShortCall_WithoutHedge_Fees['VAL_PF'][0])**(252/len(ShortCall_WithoutHedge_Fees['VAL_PF']))-1).iloc[0]

ShortCall_WithoutHedge_Fees_Annualized_Risk = np.std(ShortCall_WithoutHedge_Fees['PF_RETURNS'])*math.sqrt(252)



### IV - Short call strategy (with delta hedge) gross of management fees 
print('42% - Starting Strategy 3')

ShortCall_WithHedge = BackTest(InitInvest, Not, Tick, 0, StartDate, EndDate, 1) # no transaction fees and  hedging 

ShortCall_WithHedge_Annualized_Return = ((ShortCall_WithHedge['VAL_PF'].tail(1)/ShortCall_WithHedge['VAL_PF'][0])**(252/len(ShortCall_WithHedge['VAL_PF']))-1).iloc[0]

ShortCall_WithHedge_Annualized_Risk = np.std(ShortCall_WithHedge['PF_RETURNS'])*math.sqrt(252)



### V - Short call strategy (with delta hedge) and with transaction fees 
print('48% - Starting Strategy 4')

ShortCall_WithHedge_Fees = BackTest(InitInvest, Not, Tick, TransFees, StartDate, EndDate, 1) # no transaction fees and  hedging 

ShortCall_WithHedge_Fees_Annualized_Return = ((ShortCall_WithHedge_Fees['VAL_PF'].tail(1)/ShortCall_WithHedge_Fees['VAL_PF'][0])**(252/len(ShortCall_WithHedge_Fees['VAL_PF']))-1).iloc[0]

ShortCall_WithHedge_Fees_Annualized_Risk = np.std(ShortCall_WithHedge_Fees['PF_RETURNS'])*math.sqrt(252)

print('54% - Strategies done successfully')


### VI - Strategy analysis 
print('60% - Starting analysis')

import AnalysisFunctions as af  #Fichier des fonctions AnalysisFunctions.py


Metrics = pd.DataFrame(columns = ['Sharpe Ratio','VaR','BREACH_VAR','TE','MaxDrawdown',], index = ['Value'])

# fill df 

Metrics['Sharpe Ratio'] = af.SP(ShortCall_WithHedge_Fees_Annualized_Return,ShortCall_WithHedge_Fees_Annualized_Risk,RiskFreeRate) 

Metrics['VaR'] = af.VaR(ShortCall_WithHedge_Fees['PF_RETURNS'], 0.99) # value at risk 

Metrics['BREACH_VAR'] = sum(1 for item in ShortCall_WithHedge_Fees['PF_RETURNS'] if item <= Metrics['VaR'][0])/len(ShortCall_WithHedge_Fees['PF_RETURNS']) # value at risk 

Metrics['MaxDrawdown'] = af.maxDrawDown(ShortCall_WithHedge_Fees['PF_COMPOUNDED_RETURNS']) # max dd

Metrics['TE'] = af.TE(ShortCall_WithHedge_Fees['PF_RETURNS'],IndexData['LEGATREH Index']['Return']) # bench = Bloomberg Barclays Global-Aggregate Total Return Index


#Sauvegarder les métriques en image grâce à un HEATPLOT

mp.pyplot.clf()

mp.pyplot.figure(facecolor='w', edgecolor='k')

sns.heatmap(Metrics.head(), annot=True, cmap='Pastel1', cbar=False)

mp.pyplot.savefig('Graphs/Metrics.jpg',format='jpg',quality=100, dpi=300)

mp.pyplot.clf()

print('66% - Analysis done')


### IV - Conclusion  : PLOTS

print('72% - Starting creation of plots')

print('78% - Plot1')
# without hedging 

mp.pyplot.plot(ShortCall_WithoutHedge['PF_COMPOUNDED_RETURNS'],color = 'red',linewidth = 0.5)

mp.pyplot.plot(ShortCall_WithoutHedge_Fees['PF_COMPOUNDED_RETURNS'],color = 'blue',linewidth = 0.5,linestyle = 'dashed')

mp.pyplot.legend(['Short Calls Gross of transaction fees','Short Calls Gross incl. transaction fees'])

mp.pyplot.title('Portfolio without hedge')

mp.pyplot.tick_params(axis='x', which='major', labelsize=6)

mp.pyplot.ylabel('Returns')

mp.pyplot.savefig('Graphs/pfnohedge.jpg',format='jpg',quality=100, dpi=300)

mp.pyplot.clf()


print('84% - Plot2')
# with hedging 

mp.pyplot.plot(ShortCall_WithHedge_Fees['PF_COMPOUNDED_RETURNS'],color = 'red',linewidth = 1, alpha = 0.2)

mp.pyplot.plot(ShortCall_WithHedge['PF_COMPOUNDED_RETURNS'],color = 'red',linewidth = 1)

mp.pyplot.plot(ShortCall_WithHedge['PERF_CALL_CONTRIB'],color = 'green',linewidth = 1)

mp.pyplot.plot(ShortCall_WithHedge['PERF_FUT_CONTRIB'],color = 'blue',linewidth = 1)

mp.pyplot.title('BackTest Short Call Delta Hedged strategy')

mp.pyplot.legend(['Short Calls Delta Hedged (Incl. Fees)','Short Calls Delta Hedged (Gross of Fees)','Short Calls Perf Contrib', 'Long Futures Perf Contrib'],prop={'size':6})

mp.pyplot.tick_params(axis='x', which='major', labelsize=6)

mp.pyplot.ylabel('Returns')

mp.pyplot.savefig('Graphs/pfWithhedge.jpg',format='jpg',quality=100, dpi=300)

mp.pyplot.clf()

print('90% - Plot3')
# risk/return by asset class 

mp.pyplot.scatter(ShortCall_WithHedge_Annualized_Risk,ShortCall_WithHedge_Annualized_Return)

mp.pyplot.scatter(ShortCall_WithHedge_Fees_Annualized_Risk,ShortCall_WithHedge_Fees_Annualized_Return)

for idx in ['LEGATREH Index','HFRXEHE Index','ERIXITEU Index','ITRXTX5I Index','RX1 Comdty']:
    mp.pyplot.scatter(IndexData[idx]['Annualized_Risk'],IndexData[idx]['Annualized_Return'])
    
mp.pyplot.legend(['Short Calls Delta Hedged (Incl. Fees)','Short Calls Delta Hedged (Gross of Fees)','BB Global-Aggregate Total Return Index','HFRX Equity Hedge EUR','Main','Xover','Euro Bund Futures Price'])

mp.pyplot.tick_params(axis='x', which='major', labelsize=6)

mp.pyplot.xlabel('Annualized Volatility')

mp.pyplot.ylabel('Annualized Return')

mp.pyplot.title('Risk / Return by asset class')

mp.pyplot.savefig('Graphs/riskret.jpg',format='jpg',quality=100, dpi=300)

mp.pyplot.clf()

print('96% - Plot4')
# backtesting VaR

ShortCall_WithHedge_Fees_VaR = pd.DataFrame(columns=['VAR'],index = ShortCall_WithHedge_Fees.index)

ShortCall_WithHedge_Fees_VaR['VAR'][0] = Metrics['VaR']

ShortCall_WithHedge_Fees_VaR['VAR'].fillna(method ='ffill', inplace = True) # fill VaR 

mp.pyplot.plot(ShortCall_WithHedge_Fees['PF_RETURNS'],color = 'blue',linewidth = 1, alpha = 1)

mp.pyplot.plot(ShortCall_WithHedge_Fees_VaR,color = 'red',linewidth = 1)

mp.pyplot.legend(['Ptf Returns','VaR'])

mp.pyplot.title('VaR 99 Backtesting')

mp.pyplot.tick_params(axis='x', which='major', labelsize=6)

mp.pyplot.ylabel('Returns')

mp.pyplot.savefig('Graphs/btVaR.jpg',format='jpg',quality=100, dpi=300)

mp.pyplot.clf()
#END
print('-------------------')
print('-----  100% -------')
print('BackTest program DONE')
print('Output saved in '+ os.getcwd() + '/Graphs' )
print('-------------------')

