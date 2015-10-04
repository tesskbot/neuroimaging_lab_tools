
# coding: utf-8

# In[2]:

import pandas as pd
import math
import glob
import os, sys
import re, string
import time
from tools import common_funcs as cf


# In[3]:

#calculates APOE single variable
def APOE_presence(row):
    """Compresses APOE variants into a single variable
    
    Parameters
    ----------
    row : series
        Series with fields APOE1 and APOE2
    
    Returns
    -------
    val : float
        Float is 1 if APOE4 is present, 1 if APOE4 is not present
        and NaN if APOE data is not available
    """
    
    if row['APOE1'] == 4 or row['APOE2'] == 4:
        #APOE4 is present
        val = True
    elif math.isnan(row['APOE1'])==True or math.isnan(row['APOE2'])==True:
        #APOE info is missing
        val = float('NaN')
    else:
        #APOE4 is not present
        val = False
    return val


# In[4]:

def APOE_dose(row):
    """Assigns APOE 'dose' value, which scales roughly with badness
    2/2 = 1
    2/3 = 2
    3/3 = 3
    2/4 = 4
    3/4 = 5
    4/4 = 6
    
    Parameters
    ----------
    row : series
        Series with fields APOE1 and APOE2
        
    Returns
    -------
    val : float
        Float corresponding to dose from scale above
    """
    
    if math.isnan(row['APOE1'])==True or math.isnan(row['APOE2'])==True:
        val = float('NaN')
    elif row['APOE1'] == 2 and row['APOE2'] == 2:
        val = 1
    elif (row['APOE1'] == 2 and row['APOE2'] == 3) or (row['APOE1'] == 3 and row['APOE2'] == 2):
        val = 2
    elif row['APOE1'] == 3 and row['APOE2'] == 3:
        val = 3
    elif (row['APOE1'] == 2 and row['APOE2'] == 4) or (row['APOE1'] == 4 and row['APOE2'] == 2):
        val = 4
    elif (row['APOE1'] == 3 and row['APOE2'] == 4) or (row['APOE1'] == 4 and row['APOE2'] == 3):
        val = 5
    elif row['APOE1'] == 4 and row['APOE2'] == 4:
        val = 6
    else:
        val = 0
    return val


# In[9]:

def cogtestdates_run(path_cogdates, staticrename, outdir):
    """Reads cognitive testing dates into a dataframe
    
    Parameters
    ----------
    path_cogdates : string
        Path to the excel sheets holding the dates of cognitive testing
    staticrename : dict
        Dictionary where keys are existing names of columns in the cogdates
        spreadsheet, and values are what to rename the keys
    outdir : string
        Full path where output files should be saved
    
    Returns
    -------
    testing_out : pandas DataFrame
        DataFrame holding the dates of the cognitive tests for each subject
        at each timepoint
    subjinfo : pandas DataFrame
        DataFrame holding basic subject information
    """
    
    #import data with neuropsych test dates
    cogdates = pd.read_excel(path_cogdates)
    cogdates.rename(columns=staticrename, inplace=True)
    staticcols = staticrename.values()

    #split table into basic subject variables, and ones that change with testing session
    subjinfo = cogdates[['codea'] + staticcols]
    testing = cogdates.drop(staticcols, axis=1)

    #make columns for APOE presence and dose
    subjinfo['APOE_presence'] = subjinfo.apply(APOE_presence, axis=1)
    subjinfo['APOE_dose'] = subjinfo.apply(APOE_dose, axis=1)

    #reconfigure testing table to put tp as row values
    testing_melted = pd.melt(testing, id_vars='codea', var_name='NP_Exam')

    #initiate regex statements to draw tp and test type from column names
    tp_regex = re.compile('(\d)::')
    type_regex = re.compile('::(.*)')
    refcol = testing_melted['NP_Exam'].tolist()

    #rename NP_Tp and NP_Type columns based on regex statements
    testing_melted['NP_Tp'] = [sm.group(1) for s in refcol for sm in [tp_regex.search(s)] if sm]
    testing_melted['NP_Type'] = [sm.group(1) for s in refcol for sm in [type_regex.search(s)] if sm]
    testing_melted['subtp'] = testing_melted['codea'] + testing_melted['NP_Tp'].map(str)

    pattern = re.compile('[\d\s_]+')
    testing_melted['NP_Type'] = [pattern.sub('', s) for s in testing_melted['NP_Type']]

    #reconfigure table to put tests in columns
    testing_piv = testing_melted.pivot(index='subtp', columns='NP_Type', values='value')
    testing_out = pd.merge(testing_piv.reset_index(), testing_melted, on='subtp')
    testing_out.drop(['NP_Type','subtp','value','NP_Exam'], axis=1, inplace=True)
    testing_out.drop_duplicates(inplace=True)
    testing_out.rename(columns={'AgeatSession':'NP_Age','NeuropsychExamTestDate':'NP_Date'},
                      inplace=True)
    testing_out.dropna(axis=0, subset=['NP_Date'], inplace=True)

    #add column for years relative to baseline
    timecalc = testing_out[testing_out['NP_Tp']=='1']
    timecalc.rename(columns={'NP_Age':'NP_AgeBL','NP_Date':'NP_DateBL'}, inplace=True)
    timecalc.drop(['NP_Tp'], axis=1, inplace=True)
    testing_out = pd.merge(testing_out, timecalc, on='codea')
    testing_out['NP_YrsRelBL'] = pd.to_datetime(testing_out['NP_Date'])- pd.to_datetime(testing_out['NP_DateBL'])
    testing_out['NP_YrsRelBL'] = (testing_out['NP_YrsRelBL'].astype('timedelta64[D]'))/365.25
    
    cf.save_xls_and_pkl(testing_out, 'cogtestdates', outdir)
    cf.save_xls_and_pkl(subjinfo, 'subjinfo', outdir)
    
    return testing_out, subjinfo

