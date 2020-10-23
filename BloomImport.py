#                               MONESTIER -RAHIS
###############################################################################
#
#
# Cette fonction importe les données utiles depuis Bloomberg et les exporte en 
# fichiers excel pour que le programme BackTest puisse les utiliser
#
#
################################################################################
#
##### INSTRUCTIONS #####
#
#   *** Vérifier que l'application bbcomm est lancée
#
#   *** Si besoin installer l'api bloomberg python : 
#  !pip install pdblp 
# 
#   *** Vérifier les dates mises en paramètre dans le fichier xslx et passer la
#       valeur de ImportBloom en TRUE pour lancer ce script
#
################################################################################

def RunBDH(Dates):
    import pandas as pd
    
    from datetime import datetime, timedelta
    
    import pdblp
    
    con = pdblp.BCon(debug=True, port=8194,timeout=5000)
    
    con.start()   
    
    #Date de début et de fin
    DateStart = datetime(Dates[0],Dates[1],Dates[2]) 
    
    DateEnd = datetime(Dates[3],Dates[4],Dates[5]) 
    
    
    # bloomberg import function 
    
    def BBG_import(Index, Start, End, Price):
    
        Import = con.bdh(Index,Price,Start.strftime('%Y%m%d'),End.strftime('%Y%m%d')) # bb import
    
        return Import.xs(Price, axis = 1, level = 1) #  keep price 
    
    
    
    # indices import (bloomberg)  
    
    SX5E_Index = BBG_import('SX5E Index',DateStart,DateEnd,'PX_LAST') # SX5E Import : Eurostoxx 50 
    
    SX5T_Index = BBG_import('SX5T Index',DateStart,DateEnd,'PX_LAST') # SX5T Import : Eurostoxx 50 incl. div
    
    LEGATREH_Index = BBG_import('LEGATREH Index',DateStart,DateEnd,'PX_LAST') # LEGATREH Import : Bloomberg Barclays Global-Aggregate Total Return Index 
    
    HFRXEHE_Index = BBG_import('HFRXEHE Index',DateStart,DateEnd,'PX_LAST') # HFRXEHE Import : HFRX Equity Hedge EUR
    
    ERIXITEU_Index = BBG_import('ERIXITEU Index',DateStart,DateEnd,'PX_LAST') # ERIXITEU Import : Main Itraxx
    
    ITRXTX5I_Index = BBG_import('ITRXTX5I Index',DateStart,DateEnd,'PX_LAST') # ITRXTX5I Import : Xover
    
    RX1_Comdty = BBG_import('RX1 Comdty',DateStart,DateEnd,'PX_LAST') # RX1 Import : Bund 10 years 
    
    
    # creation of third friday list 
    
    # we need to know the date of each month third friday to know option tickers
    
    thirdfriday = pd.DataFrame(columns = ["Date","Prix"])
    
    a = -1
    
    
    datelist = pd.date_range(start=DateStart, end=DateEnd).tolist()
    
    for d in datelist:
    
        a = a+1 
    
        if d.weekday()==4 and 15 <= d.day <= 21:
    
            if (d in SX5E_Index.index):
    
                thirdfriday = thirdfriday.append(pd.DataFrame({"Date" : [d], "Prix" :[SX5E_Index['SX5E Index'][d]]}), ignore_index=True)
    
            else:
    
                thirdfriday = thirdfriday.append(pd.DataFrame({"Date" : [d-timedelta(days=1)], "Prix" :[SX5E_Index['SX5E Index'][d-timedelta(days=1)]]}), ignore_index=True)
    
    
    
    # creation of call ticker list (option ticker according to the third fridays lists)
    
    pd.options.display.float_format ='{:,.0f}'.format
    
    thirdfriday['Strike'] = 50*round(thirdfriday['Prix'].shift(1)*1.01/50)
    
    thirdfriday['Strike'][0] = 50*round(SX5E_Index['SX5E Index'][0]*1.01/50)
    
    thirdfriday['Call'] = "SX5E "+ thirdfriday['Date'].apply(lambda x: x.strftime('%m/%d/%y')) + " C" + thirdfriday['Strike'].astype(int).map(str) + " Index"
    
    thirdfriday.to_excel('Dataframes/output_THIRDFRIDAY.xlsx', index=True) # excel export 
    
    
    
    # indices export (excel)
    
    Indices_prices = pd.concat([SX5E_Index,SX5T_Index,LEGATREH_Index,HFRXEHE_Index,ERIXITEU_Index,ITRXTX5I_Index,RX1_Comdty],axis=1)
    
    Indices_prices.to_excel('Dataframes/output_INDICES.xlsx',sheet_name='Sheet_name_1', index=True) # excel export 
    
    
    # option prices import (bloomberg) + export (excel)
    
    sorted_data_PXLAST = BBG_import(list(thirdfriday['Call']),DateStart,DateEnd,'PX_LAST') # SX5E Call prices import  
    
    sorted_data_PXLAST = sorted_data_PXLAST.reindex(columns=thirdfriday['Call']) # sort data 
    
    sorted_data_PXLAST.to_excel('Dataframes/output_OPTPRICE.xlsx', index=True) # excel export 
    
    sorted_data_MID = BBG_import(list(thirdfriday['Call']),DateStart,DateEnd,'DELTA_MID') # SX5E Call delta import  
    
    sorted_data_MID = sorted_data_MID.reindex(columns=thirdfriday['Call']) # sort data 
    
    sorted_data_MID.to_excel('Dataframes/output_DELTAMID.xlsx',sheet_name='Sheet_name_1', index=True) # excel export 
    
    
    # futures prices import (bloomberg) + export (excel)
    
    Futures_Price = BBG_import('VG1 Index',DateStart,DateEnd,'PX_LAST') # SX5E Futures prices import  
    
    Futures_Price.to_excel('Dataframes/output_FUTPRICE.xlsx',sheet_name='Sheet_name_1', index=True) # excel export 
    
    ##################
