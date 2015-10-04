
# coding: utf-8

# In[9]:

import pandas as pd
import os, sys
from tools import common_funcs as cf


# In[10]:

def codea_to_codeb(codetbl):
    """Creates two dictionaries that provide mappings from codea and codeb and
    vice versa.
    
    Parameters
    ----------
    codetbl : pandas DataFrame
        DataFrame with two columns named 'codea' and 'codeb' containing
        those codes
        
    Returns
    -------
    coderef_lblkey : dictionary
        Dictionary with codea as keys and codeb as values
    coderef_backey : dictionary
        Dictionary with codeb as keys and codea as values
    """
    
    #remove codes that are missing a partner
    codetbl.dropna(inplace=True)
    coderef_lblkey = pd.Series(codetbl['codea'].values,index=codetbl['codeb']).to_dict()
    coderef_backey = pd.Series(codetbl['codeb'].values,index=codetbl['codea']).to_dict()
    return coderef_lblkey, coderef_backey


# In[11]:

def codetranslator_run(codetblpath, outdir):
    """Takes an excel file as input and generates a pandas dataframe containing only
    matched pairs of codea and codeb.
    
    Parameters
    ----------
    codetblpath : string
        Hard path to the excel file holding code data. Expects two columns named 
        'codeaGRAB' and 'codeb'.
    outdir : string
        Hard path to the directory to save the output file
        
    Renames columns to 'codea' and 'codeb' and saves xls and pkl files named 'codetranslator' 
    to outdir.
    """
    
    codetblin = pd.read_excel(codetblpath)
    codetbl = codetblin[['codeaGRAB','codeb']]
    codetbl = codetbl.rename(columns={'codeaGRAB' : 'codeb'})
    
    codetbl = codetbl.dropna()

    cf.save_xls_and_pkl(codetbl, 'codetranslator', outdir)
    
    return codetbl


# In[ ]:



