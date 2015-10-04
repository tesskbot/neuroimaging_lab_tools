
# coding: utf-8

# In[6]:

import os, sys
import re
import difflib
from glob import glob
from copy import deepcopy
import pandas as pd
from tools import common_funcs as cf


# In[19]:

#assign appropriate row index to the subject data tables
def assign_row_index(tbldict, rowind):
    """Iterates through a dictionary of DataFrames. For each DataFrame,
    searches column names for a matching string. Deletes rows that have 
    NaN in that column. Then makes that column the table's index. 
    
    Parameters
    ----------
    tbldict : dictionary of DataFrames
    rowind : string
        This string should match one of the column names in table
        
    Returns
    -------
    tbldict : dictionary of DataFrames
        Each DataFrame now has rowind as index
    """
    
    for sess,table_cur in tbldict.iteritems():
        #find column name that matches the rowind defined above
        rowind_found = [col for col in table_cur.columns if rowind in col]
        rowind_found = rowind_found[0]
        #delete rows with NaN rowind
        table_cur = table_cur[pd.notnull(table_cur[rowind_found])]
        #set a new table index
        table_cur = table_cur.set_index(rowind_found)
        tbldict[sess] = table_cur
    return tbldict


# In[20]:

#rename all cognitive test column headers to those in the master list
def rename_columns(table, refstrings):
    """For each column header in a table, finds the nearest text match from a 
    list of strings. The column header is then replaced with the best matching
    string.
    
    Parameters
    ----------
    table : DataFrame
    refstrings : list
        Contains n strings that will be compared to each column in table
        
    Returns
    -------
    table : DataFrame
        DataFrame with column names replaced with the best matching string from
        refstrings
    """
    #initiate lists of columns
    bad = []
    good = []
    #save original data
    for test,col in table.iteritems():
        #compare the column header to the master list of cognitive tests and extract best match
        match = difflib.get_close_matches(test, refstrings, 1, 0)
        bad.append(test)
        good.extend(match)
    #assign new list to the column names
    table.columns = good
    return table


# In[8]:

def cogprep(data_list, cogtests_master, rowind='codeb', combine_this=({'trl': ['tr','tl']}), 
            invert_this=({'T_Inverted': 'T'})):
    """Process cognitive tests that need to be either combined or inverted.
    
    Parameters
    ----------
    data_list : list
        List of paths to excel sheets, each of which holds cognitive data for a
        separate testing session
    cogtests_master : list
        List of strings that are all cognitive tests that should be included in the 
        factor analysis
    rowind : string
        Name of column representing the index value. Default is 'codeb'
    combine_this : dict
        Dictionary where keys are names of columns holding summed data, and values 
        are the columns to sum
    invert_this : dict
        Dictionary where keys are names of columns holding inverted data, and values
        are the columns to invert
    
    Returns
    -------
    subjdata : dict
        Dictionary, keys are 'sessX' where X is the session number and values are
        DataFrames containing that session's cognitive data
    """
    
    #import all subject data
    subjdata = {}
    for i,tp in enumerate(data_list):
        datain = pd.read_excel(tp)
        subjdata.update({'sess%s'%(i+1): datain}) 
        
    #assign new row idices for the subject data
    subjdata = assign_row_index(subjdata, rowind)

    for sess,table_cur in subjdata.iteritems():
        #rename columns
        table_cur = rename_columns(table_cur, cogtests_master)
        #iterate over items that need to be combined
        for col_summed, col_unsummed in combine_this.iteritems():
            table_cur[col_summed] = (table_cur[col_unsummed]).sum(axis = 1)
        #iterate over items that need to be inverted
        for col_inv, col_uninv in invert_this.iteritems():
            table_cur[col_inv] = table_cur[col_uninv] * -1
            
    return subjdata


# In[40]:

def zscore(blpth, subjdata, cogtests_master):
    """Calculates Z scores for all cognitive data based on a reference dataset
    
    Parameters
    ----------
    blpth : string
        Full path to excel sheet holding cognitive data for a reference population
    subjdata : dict
        Dictionary, keys are 'sessX' where X is the session number and values are
        DataFrames containing that session's cognitive data
    cogtests_master : list
        List of strings that are all cognitive tests that should be included in the 
        factor analysis
    
    Returns
    -------
    subjdata_z : pandas DataFrame
        DataFrame containing all subject data where each row is a single subject's 
        single cognitive testing session. This data has been z-scored.
    """

    #import baseline data
    bldata_import = pd.read_excel(blpth)

    #rename cognitive test column headers based on master list
    bldata = rename_columns(bldata_import, cogtests_master)

    #calculate mean and standard deviation of baseline data for each test
    #for z score calculation
    bl_tests = bldata.columns
    bl_mean = bldata.mean(axis = 0)
    bl_std = bldata.std(axis = 0)
    
    zscored = deepcopy(subjdata)

    #iterate over session
    for sess, table_cur in zscored.iteritems():
        #iterate over cognitive test and create z scores
        for test in bl_tests:
            z1 = table_cur[test] - bl_mean[test]
            z2 = z1 / bl_std[test]
            table_cur[test] = z2

    #make cognitive data into a panel
    subjdata_z = pd.Panel.from_dict(zscored)
    #transpose so tests become the items
    subjdata_z = subjdata_z.transpose(2,1,0)
    #collapse all sessions into a single frame
    #this removes any rows that contain nan values
    subjdata_z = subjdata_z.to_frame()
    return subjdata_z


# In[61]:

def factorscores(subjdata, wpth, cogtests_master):
    """Takes z-scored cognitive data and calculates factor scores using designated
    factor weights
    
    Parameters
    ----------
    subjdata : pandas DataFrame
        DataFrame containing all subject data where each row is a single subject's 
        single cognitive testing session. Intended use is to use the output of zscore
    wpth : string
        Full path to excel file holding factor weights. Each column in this file is a 
        cognitive test, and each row is a factor.
    cogtests_master : list
        List of strings that are all cognitive tests that should be included in the 
        factor analysis
    
    Returns
    -------
    cogtests_summary : pandas DataFrame
        DataFrame where each row is a a single subject's single cognitive testing session.
        Columns are scores on each of the cognitive tests, and scores for each factor
    """

    #import weights
    weights_import = pd.read_excel(wpth)
    weights = rename_columns(weights_import, cogtests_master)
    #extract weights
    weights_tests = weights.columns
    
    #multiply scaled subject data by factor weights
    factors = {}
    for factor,i in weights.iterrows():
        subjdata_w = subjdata.copy()
        for ii,test in enumerate(weights_tests):
            subjdata_w[test] = subjdata_w[test].values * weights.ix[factor,test]
        factors.update({factor: subjdata_w})

    #initiate tables to summarize factor scores
    fc = deepcopy(factors)
    sumscores = pd.DataFrame(index = fc[0].index)

    #iterate over factors
    for wt, df in fc.items():
        #sum scores for each subject, for each session
        df['FS'] = df[weights_tests].sum(axis = 1)
        ss = df[weights_tests].sum(axis = 1)
        ss.name = wt
        sumscores = pd.concat([sumscores, ss], axis = 1)
        fc[wt] = df

    cogtests_summary = pd.merge(subjdata, sumscores, left_index=True, right_index=True)
    
    cogtests_summary.reset_index(inplace=True)
    cogtests_summary.rename(columns={'minor':'Tp',0:'F0',1:'F1',
                                 2:'F2'}, inplace=True)
    
    #simplify visit code values to numbers by removing string 'sess'
    cogtests_summary['Tp'] = cogtests_summary['Tp'].map(lambda x: x.lstrip('sess'))
    
    return cogtests_summary


# In[5]:

def factoranalysis_run(cogpth, blpth, wpth, outdir, rowind, cogtests_master, **kwargs):
    """Takes cognitive data output from filemaker pro database and applies weights from
    a factor analysis. Outputs data for each subject for each cognitive session that has
    been z scored, and the factor weights for each of those datapoints.
    
    Parameters
    ----------
    cogpth : string
        Path to folder holding excel sheets of cognitive data
    blpth : string
        Full path to excel sheet holding cognitive data for a reference population
    wpth : string
        Full path to excel file holding factor weights. Each column in this file is a 
        cognitive test, and each row is a factor.
    outdir : string
        Full path where output files should be saved
    rowind : string
        Name of column representing the index value. Default is 'codeb'
    cogtests_master : list
        List of strings that are all cognitive tests that should be included in the 
        factor analysis
    
    Returns
    -------
    subjdata : dict
        Dictionary, keys are 'sessX' where X is the session number and values are
        DataFrames containing that session's cognitive data
    subjdata_z : pandas DataFrame
        DataFrame containing all subject data where each row is a single subject's 
        single cognitive testing session. This data has been z-scored.
    cogdata : pandas DataFrame
        DataFrame where each row is a a single subject's single cognitive testing session.
        Columns are scores on each of the cognitive tests, and scores for each factor
    """
    cogglob = sorted(glob(cogpth))
    
    subjdata = cogprep(cogglob, cogtests_master)
    subjdata_z = zscore(blpth, subjdata, cogtests_master)
    cogdata = factorscores(subjdata_z, wpth, cogtests_master)

    cf.save_xls_and_pkl(cogdata, 'cogdata', outdir)
    
    return subjdata, subjdata_z, cogdata


# In[ ]:



