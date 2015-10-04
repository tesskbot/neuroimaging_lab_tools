
# coding: utf-8

# In[1]:

import os, sys
from tools import common_funcs as cf
import shutil
import glob
import subprocess
import pandas as pd
import re


# In[2]:

def find_and_copy(datadir, FDG_warpfold, filenm='pn*'):
    """Searches datadir for warped FDG scans and copies them to a processing directory
    
    Parameters
    ----------
    datadir : string
        Full path of directory containing files
    FDG_warpfold : string
        Full path of directory to copy files to
    filenm : string
        General name of warped files. Default is 'pn*'
    
    Returns
    -------
    filepaths : list
        List of warped files that were copied
    warp_subs : list
        List of subject ids for the files that were copied
    """
    os.chdir(datadir)

    shellfilelist = subprocess.check_output('find . -type f -name \'%s\'' %filenm, shell=True)

    filelist = shellfilelist.split()
    filelist = [s for s in filelist if not (re.search('mr',s) or re.search('M15',s))]
    fullpathfilelist = [datadir + s[2:] for s in filelist]

    _ = [shutil.copy2(s, FDG_warpfold) for s in fullpathfilelist]
    
    filepaths = glob.glob(FDG_warpfold +'*')
    warp_subs = os.listdir(FDG_warpfold)
    
    return filepaths, warp_subs


# In[3]:

def create_masks(warp_subs, FDG_warpfold, FDG_maskfold, template):
    """For each subject in warp_subs, creates a binary mask using the 
    template and applies it over the subject. The extracted values from 
    the mask are then deposited into FDG_maskfold
    
    Parameters
    ----------
    warp_subs : list
        List of files in folder
    FDG_warpfold : string
        Full path to folder holding data
    FDG_maskfold : string
        Full path to folder that will hold processed data
    template : string
        Full path to template brain scan containing mask
    """
    pth,_ = os.path.split(template)
    
    os.chdir(FDG_warpfold)
    
    for sub in warp_subs:
        os.system('fslmaths '+sub+' -mas '+template+' '+FDG_maskfold+'mi_'+sub)


# In[4]:

def generate_values(mask_dir):
    """Extracts the mean value from each mask in the roi_mask directory. 
    Returns these values as a dict.
    
    Parameters
    ----------
    mask_dir : string
        Full path to masked data
    
    Returns
    -------
    metaroi_vals : dict
        Dictionary where keys are the filename and values are the mean
        FDG value
    """
    masklist = [mask_dir + fl for fl in os.listdir(mask_dir)]
    metaroi_vals = {}
    for mask in masklist:
        roi_value = subprocess.check_output('fslstats '+mask+' -M', shell = True)
        if 'nan' in roi_value:
            os.system('fslmaths '+mask+' -nan '+mask+'_nonan')
            roi_value = subprocess.check_output('fslstats '+mask+'_nonan -M', shell = True)
        metaroi_vals.update({mask: roi_value})
    return metaroi_vals


# In[5]:

def generate_df(metaroi_vals, outdir):
    """Generates a dataframe with the metaroi values for each subject
    
    Parameters    
    ----------
    metaroi_vals : dict
        Dictionary where keys are the filename and values are the mean
        FDG value
    outdir : string
        Full path where FDG output file should be saved
        
    Returns
    -------
    metaroi_df : pandas DataFrame
        DataFrame where each row is an FDG scan
    """
    metaroi_df = pd.DataFrame.from_dict(metaroi_vals,orient='index')
    metaroi_df.reset_index(level=0, inplace=True)
    metaroi_df.rename(columns={0:'roi_vals','index':'path'},inplace=True)
    metaroi_df['roi_vals'] = [float(x) for x in metaroi_df['roi_vals']]
    metaroi_df['codea'] = [cf.get_id(x) for x in metaroi_df['path']]
    metaroi_df = metaroi_df.rename(columns={'roi_vals':'FDG_val'})
    metaroi_df = metaroi_df.drop('path', axis=1)
    
    cf.save_xls_and_pkl(metaroi_df, 'fdg_metaroi', outdir)
    
    return metaroi_df


# In[15]:

def clean_up(fdgdirs):
    """Deletes files in the folders created by FDG processing
    
    Parameters
    ----------
    fdgdirs : list
        List of strings corresponding to paths containing data to delete
    """
    for fdgdir in fdgdirs:
        files = glob.glob(fdgdir + '*')
        for f in files:
            os.remove(f)


# In[17]:

def fdg_run(datadir, FDGfold, template, outdir, filenm, cleanup=False):
    """Main function to college FDG metaroi values
    
    Parameters    
    ----------
    datadir : string
        Full path of directory containing files
    FDGfold : string
        Full path of directory where FDG files will be copied. There
        should be two folders here named W and M
    template : string
        Full path to the metaroi mask file ex: rcomposite_ROI.nii
    outdir : string
        Full path where FDG output file should be saved
    filenm : string
        General name of warped files. Default is 'pn*'
    cleanup : boolean
        If TRUE, runs clean_up to delete files created during FDG processsing.
        Default is FALSE.
        
    Returns
    -------
    metaroi_vals : dict
        Dictionary where keys are the filename and values are the mean
        value
    metaroi_df : pandas DataFrame
        DataFrame where each row is a scan
    """
    
    if not os.path.exists(FDGfold):
        os.makedirs(FDGfold)
    FDG_warpfold = FDGfold +'W/'
    if not os.path.exists(FDG_warpfold):
        os.makedirs(FDG_warpfold)
    FDG_maskfold = FDGfold +'J/'
    if not os.path.exists(FDG_maskfold):
        os.makedirs(FDG_maskfold)
    
    filepaths, warp_subs = find_and_copy(datadir, FDG_warpfold, filenm)
    create_masks(warp_subs, FDG_warpfold, FDG_maskfold, template)
    metaroi_vals = generate_metaroi_values(FDG_maskfold)
    metaroi_df = generate_df(metaroi_vals, outdir)
    
    if cleanup==True:
        clean_up([FDG_warpfold, FDG_maskfold])
    
    return metaroi_vals, metaroi_df


# In[ ]:



