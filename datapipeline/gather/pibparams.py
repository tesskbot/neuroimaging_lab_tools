
# coding: utf-8

# In[84]:

import pandas as pd
import glob
import os, sys
from tools import common_funcs as cf


# In[87]:

def pibparams_run(path_pib, pibrename, outdir, pibcutoff):
    """Reads data from the spreadsheet, does some calculations, and 
    returns a Pandas dataframe with PIB data.
    
    Parameters
    ----------
    path_pib : string
        String of full path to *.xls
    pibrename : dict
        Dictionary of name:rename pairs, where the keys are columns in the 
        PIB spreadsheet and values are what to rename the keys to
    outdir : string
        Full path where final dataframe will be saved
    pibcutoff : float
        PIB cutoff value
    
    Returns
    -------
    pib_df : pandas dataframe
        Dataframe containing all PIB data
    """

    #read in pib data from old sheet
    pib_old = pd.read_excel(path_pib, sheetname='i')
    #read in PIB data from longitudinal timepoints
    pib_long = pd.read_excel(path_pib, sheetname='j')
    #concatenate PIB tables
    pib_df = pd.concat([pib_long, pib_old])
    pib_df = pib_df[pibrename.keys()]
    pib_df.rename(columns=pibrename, inplace=True)

    #make binary PIB value
    pib_df['PIB_Pos'] = pib_df['PIB_Index'].apply(lambda x: 1 if x >= pibcutoff else 0)

    #calculate rate of change of PIB_Index in years
    pib_df = cf.rate_of_change(pib_df, 'codea', 'PIB_Tp', 'PIB_Scandate', 
                               'PIB_Index', 'PIB_sl')

    #make column for the age at which PIB positivity appears
    pib_df.sort(columns=['codea','PIB_Tp'], inplace=True)

    #calculate age of PIB positivity
    pib_df['PIB_agepos'] = float('nan')
    pib_df = pib_df.groupby(by='codea')
    pib_df = pib_df.apply(f)
    
    cf.save_xls_and_pkl(pib_df, 'pibparams', outdir)
    
    return pib_df


# In[86]:

#calculate age of PIB positivity
def f(group):
    pos = group[group['PIB_Pos'] == 1]
    if len(pos) > 0:
        agepos = min(pos['PIB_Age'])
        group.ix[:,'PIB_agepos'] = agepos
    return group

