
# coding: utf-8

# In[1]:

import pandas as pd
import glob
import os, sys
from tools import common_funcs as cf


# In[367]:

def mergelots(bigdict, tblstojoin, joincol, how='outer'):
    """Merges multiple tables that are in a common dictionary. Does an outer join by
    default on the designated columns.
    
    Parameters
    ----------
    bigdict : dict
        Name of the dictionary containing the tables to merge
    tblstojoin : list
        List of the names of tables to merge, all of which are contained in bigdict
    joincol : list
        List of the names of columns to merge on
    how : string
        Type of merge to perform. Outer join is done by default.
    
    Returns
    -------
    bigtbl : pandas DataFrame
        DataFrame containing merged data from all tblstojoin
    """
    for tbl in tblstojoin:
        if tbl == tblstojoin[0]:
            bigtbl = bigdict[tbl].copy()
        else:
            bigtbl = bigtbl.merge(bigdict[tbl], how=how, on=joincol)
    return bigtbl


# In[359]:

def count_instances(tbl, col2count, colcounted):
    """Counts the number of replicated values in a single column of a DataFrame.
    
    Parameters
    ----------
    tbl : pandas DataFrame
    col2count : string
        Name of the column in tbl to count the contents of
    colcounted : string
        Name of column to add to tbl containing the counts of values in col2count
        
    Returns
    -------
    tbl : pandas DataFrame
        DataFrame the same as input tbl containing an extra column named colcounted
        that holds the counts of values in the col2count column
    """
    counted_ser = tbl[col2count].value_counts()
    counted_df = pd.DataFrame(counted_ser, columns=[colcounted]).reset_index()
    counted_df.rename(columns={'index':col2count},inplace=True)
    tbl = tbl.merge(counted_df,on=col2count)
    return tbl


# In[360]:

def flatten(tbl, tpcol, key, val):
    """Filters DataFrames by a particular value within a column.
    Here used to extract only rows containing first timepoint data.
    
    Parameters
    ----------
    tbl : pandas DataFrame
        DataFrame where each row in an observation
    tpcol : string
        Name of column in tbl that holds data to be filtered
    key : string
        Name of DataFrame
    val : list
        List of values to look for in tbl[tpcol] and retain
    
    Returns
    -------
    tblflat : pandas DataFrame
        DataFrame containing only rows tbl[tpcol] contains val
    tblflatnm : string
        Name of flattened tbl
    """
    tblflat = tbl[tbl[tpcol].isin(val)]
    tblflatnm = '%s_flat' %key
    return tblflat, tblflatnm


# In[361]:

def addcodes(tbl, codetbl, sicol='codea', bacol='codeb'):
    """Adds columns of subject codes to DataFrame, if they do not already exist
    
    Parameters
    ----------
    tbl : pandas DataFrame
        DataFrame where rows are observations and columns are variables. Expect 
        that either sicol or bacol already exists in this table.
    codetbl : pandas DataFrame
        2-column DataFrame listing translation between two code types
    sicol : string
        Name of column containing one type of subject code, default 'codea'
    bacol : string
        Name of column containing one type of subject code, default 'codeb'
    
    Returns
    -------
    tbl : pandas DataFrame
        tbl which now contains columns for both sicol and bacol, if not already present
    """
    
    if all(x in tbl.columns for x in [sicol, bacol]):
        return tbl
    else:
        if sicol not in tbl.columns:
            tbl = tbl.merge(codetbl, how='outer', on=bacol)
        if bacol not in tbl.columns:
            tbl = tbl.merge(codetbl, how='outer', on=sicol)
        return tbl


# In[4]:

#put all subject data into a dictionary of tables
def collect2dict(filenames, outdir):
    """Compiles multiple pickle files from the same directory into a dictionary of
    DataFrames
    
    Parameters
    ----------
    filenames : list
        List of strings corresponding to filename prefixes of pickle format in outdir
    outdir : string
        Full path of directory containing files in filenames
    
    Returns
    -------
    tbldict : dictionary
        Dictionary of pandas DataFrames where keys are filenames 
    """
    
    tbldict = {}
    for fn in filenames:
        try:
            path = max(glob.glob(outdir+fn+'*.pkl'), key=os.path.getctime)
            out = pd.read_pickle(path)
            tbldict[fn] = out
        except ValueError:
            print(fn + ' not found in ' + outdir)
    return tbldict


# In[363]:

#merge two tables with cognitive data into a single table
#and delete original tables
def cogtest_manipulation(tbldict, roc_cols):
    """Process table containing cognitive testing data
    
    Parameters
    ----------
    tbldict : dict
        Dictionary of DataFrames each containing a different type of data
    roc_cols : list
        List of strings corresponding to column names for which rate of change should be 
        calculated
    
    Returns
    -------
    tbldict : dict
        The same as input tbldict but now with new item
    """
    
    tbldict['cogtests'] = pd.merge(tbldict['cogtestdates'],tbldict['cogdata'],on=['codeb','NP_Tp'])
    
    del tbldict['cogtestdates']
    del tbldict['cogdata']
    
    for col in roc_cols:
        tbldict['cogtests'] = cf.rate_of_change(tbldict['cogtests'], 'codeb', 'NP_Tp', 
                                'NP_Date', col, '%s_sl' %col)
    
    #add column for maximum follow-up time per subject
    tbldict['cogtests'] = cf.max_per_sub(tbldict['cogtests'], 'codeb', 'NP_YrsRelBL', 'NP_Followup_Time')
    
    return tbldict


# In[364]:

def datamerge_run(filenames, outdir, roc_cols):
    """Main function to merge all data
    
    Parameters
    ----------
    filenames : list
        List of strings corresponding to filename prefixes of pickle format in outdir
    outdir : string
        Full path of directory containing files in filenames
    roc_cols : list
        List of strings corresponding to column names for which rate of change should be 
        calculated
    
    Returns
    -------
    tbldict : dict
        Dictionary of DataFrames each containing a different type of BACS data
    NPtbl : pandas DataFrame
        DataFrame where each row is a single subject's single cognitive testing session
    subjtbl : pandas DataFrame
        DataFrame where each row is a single subject
    """
    
    tbldict = collect2dict(filenames, outdir)
    tbldict = cogtest_manipulation(tbldict, roc_cols)
    
    #count number of tps
    tbldict['cogtests'] = count_instances(tbldict['cogtests'], 'codeb', 'NP_NoTps')
    tbldict['aseg_change'] = count_instances(tbldict['aseg_change'], 'codea', 'MRI_NoTps')
    tbldict['pibparams'] = count_instances(tbldict['pibparams'], 'codea', 'PIB_NoTps')
    
    new_tbldict = {}
    for key, tbl in tbldict.iteritems():
        tpcol = [s for s in tbl.columns if ('_Tp' in s)]
        if tpcol:
            tpcol = tpcol[0]
            tblflat, tblflatnm = flatten(tbl, tpcol, key, [1, '1'])
            new_tbldict[tblflatnm] = tblflat
    tbldict.update(new_tbldict)
    
    #make sure each table contains SubjID and BAC# fields
    for key, tbl in tbldict.iteritems():
        tbl = addcodes(tbl, tbldict['codetranslator'])
        tbldict[key] = tbl
    
    #merge tables
    tblstojoin = ['cogtests_flat','pibparams_flat','aseg_change_flat','fdg_metaroi_flat','subjinfo']
    joincol = ['codea','codeb']
    subjtbl = mergelots(tbldict, tblstojoin, joincol)
    
    #merge tables
    tblstojoin = ['cogtests','subjinfo','pibparams_flat','aseg_change_flat','fdg_metaroi_flat']
    joincol = ['codea','codeb']
    NPtbl = mergelots(tbldict, tblstojoin, joincol)
    
    cf.save_xls_and_pkl(subjtbl, 'subjtbl', outdir)
    cf.save_xls_and_pkl(NPtbl, 'NPtbl', outdir)
    
    return tbldict, NPtbl, subjtbl

