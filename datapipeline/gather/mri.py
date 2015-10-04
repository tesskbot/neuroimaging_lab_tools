
# coding: utf-8

# In[19]:

import pandas as pd
import sys, os
from tools import common_funcs as cf
import subprocess


# In[20]:

def bacs_pet_mri_date(rootpath, sub, verbose=False):
    """Searches the recon-all.log file in the '/scripts' directory of MRI
    data processed through freesurfer to find the date of the input scan.
    
    Parameters
    ----------
    rootpath : string
        Path where the sub directory lives.
    sub : string
        Name of the directory within rootdir that refers to a subject and
        timepoint, and expected to contain /scripts/recon-all.log
    verbose : boolean
        Default False. Set to True to see failure output.
    
    Returns
    -------
    result : datetime object 
        datetime object of the date of the input MRI scan
        If no date can be found, returns None
    """
    from datetime import datetime
    import re
    
    reconlog_path = '%s%s/scripts/recon-all.log' %(rootpath, sub)
    if not os.path.isfile(reconlog_path):
        if verbose == True:
            print('No recon-all.log file found in %s' %reconlog_path)
        return
    try:
        with open(reconlog_path) as f:
            lines = f.read().splitlines()
        iline = lines[3]
        iflag = re.match('\-i\s(.*?)\s\-', iline)
        match = re.search('\d{8}', iflag.group(1))
        datematch = match.group()
    except:
        if verbose == True:
            print('No matching date-like string found in %s' %iline)
        return
    format = '%Y%m%d'
    try:
        result = datetime.strptime(datematch, format)
        return result
    except ValueError:
        if verbose == True:
            print('No date found in %s from line %s' %(datematch, iline))
        return


# In[21]:

def bacs_pet_mri_date_batch(rootpath):
    """Given a path, this function finds subject folders there and finds 
    the date of the freesurfer processed data.

    Parameters 
    ----------
    rootpath : string
        Path where subject directories lie

    Returns
    -------
    datetbl : DataFrame
        Holds codea, MRI_Tp, and MRI_Scandate fields
    """
    subs, _ = cf.lbls_infold(rootpath)
    datetbl = pd.DataFrame(columns=['sub'], data=subs)
    datetbl['MRI_Scandate'] = float('NaN')

    for sub in subs:
        dateout = bacs_pet_mri_date(rootpath, sub)
        datetbl.loc[datetbl['sub']==sub,'MRI_Scandate'] = dateout

    datetbl['codea'] = [cf.get_lbl_id(sub) for sub in datetbl['sub'].tolist()]
    datetbl['MRI_Tp'] = [cf.get_tp(sub) for sub in datetbl['sub'].tolist()]

    datetbl.drop('sub', axis=1, inplace=True)
    datetbl = datetbl[datetbl['MRI_Tp'].notnull()]
    return datetbl


# In[22]:

def extractFSasegstats(directory, outfile):
    '''Generate a command-line command to extract freesurfer
    
    Parameters
    ----------
    directory : string
        Full path to root directory of freesurfer processed data. Expect file tree
        to be directory/sub/stats/aseg.stats
    outfile : string
        Full path to directory where summary file should be saved
    
    Returns
    -------
    subs : list
        List of subjects found in the input directory
    commandlinestr : string
        String that was passed to the command line
    output : string
        Command line output
    '''
    subs, _ = cf.lbls_infold(directory)
    subs = [sub for sub in subs if 'long' not in sub]
    subpaths = ['%s%s/stats/aseg.stats' % (directory, sub) for sub in subs]
    sublist = ' '.join(subpaths)
    commandlinestr = 'asegstats2table --inputs %s --skip --tablefile %s' % (sublist, outfile)
    process = subprocess.Popen(commandlinestr.split(), stdout=subprocess.PIPE)
    output = process.communicate()[0]
    return subs, commandlinestr, output


# In[23]:

def icvcorr(tbl, rois, icvcol):
    """Corrects freesurfer calculated volumes by the intracranial volume
    
    Parameters
    ----------
    tbl : pandas DataFrame
        DataFrame with columns with names rois and icvcol
    rois : dict
        Keys are names of current columns in tbl, and corresponding values are 
        names of columns that will hold icv corrected volumes
    icvcol : string
        The name of the column holding the icv value
        
    Returns
    -------
    tbl : pandas DataFrame
        Tbl now has additional columns specified by rois.values holding icv 
        corrected volumes
    """
    for key, value in rois.iteritems():
        tbl[value] = tbl[key] / tbl[icvcol]
    return tbl


# In[29]:

def mri_run(datadir, outdir, rois):
    """Main function to collect MRI volume data
    
    Parameters
    ----------
    datadir : string
        Full path to root directory of freesurfer processed data. Expect file tree
        to be datadir/subcode/stats/aseg.stats
    outdir : string
        Full path to directory where data will be saved
    rois : list of strings
        List of freesurfer rois of interest. These volumes of these rois will be 
        inserted in aseg_change along with their rates of change
        
    Returns
    -------
    aseg_stats : pandas DataFrame
        DataFrame where each row is a scan, and columns are volumes of all
        freesurfer processed regions
    aseg_change : pandas DataFrame
        DataFrame where each row is a scan, and columns are the volumes of interest,
        their rates of change, and icv correction
    """

    #get aseg_stats data from freesurfer processed data
    outfile = '%sFS_aseg_stats.txt' %outdir
    subs, asegout, output = extractFSasegstats(datadir, outfile)
    aseg_stats = pd.read_csv(outfile, header=0, delim_whitespace=True)

    #add columns for SubjID and MRI_TP
    aseg_stats['codea'] = [cf.get_id(sub) for sub in subs]
    aseg_stats['MRI_Tp'] = [cf.get_tp(sub) for sub in subs]
    aseg_stats.drop('Measure:volume', axis=1, inplace=True)

    #get dates of MRI scans that were processed with freesurfer
    mridates = bacs_pet_mri_date_batch(datadir)

    aseg_change = pd.merge(aseg_change, mridates, on=['codea','MRI_Tp'])

    rois_icvcorr = dict([(roi, '%s_icvcorr' %roi) for roi in rois])
    
    aseg_change = icvcorr(aseg_change, rois_icvcorr, 'IntraCranialVol')

    #calculate rate of change in years
    for roi in rois:
        aseg_change = cf.rate_of_change(aseg_change, 'codea', 'MRI_Tp', 
                                    'MRI_Scandate', roi, '%s_sl' %roi)
    
    cf.save_xls_and_pkl(aseg_stats, 'aseg_stats', outdir)
    cf.save_xls_and_pkl(aseg_change, 'aseg_change', outdir)
    
    return aseg_stats, aseg_change

