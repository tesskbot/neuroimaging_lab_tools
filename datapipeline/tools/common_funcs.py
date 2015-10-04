import glob
import os, sys
import pandas as pd
import re
import nibabel as nb
import numpy as np
import time


def gzip_all(_path):
    """Recursively search path and gzip all .nii files. Return the number gzipped.
    """
    gunzipped = []
    for root, dirs, files in os.walk(_path):
        for f in files:
            if f[-4:] == '.nii':
                gunzipped.append(os.path.join(root, f))
    for f in gunzipped:
        cmd = 'gzip {}'.format(f)
        os.system(cmd)
    return len(gunzipped)


def gunzip_all(_path):
    """Recursively search path and gzip all .nii files. Return the number gzipped.
    """
    gzipped = []
    for root, dirs, files in os.walk(_path):
        for f in files:
            if f[-7:] == '.nii.gz':
                gzipped.append(os.path.join(root, f))
    for f in gzipped:
        cmd = 'gunzip {}'.format(f)
        os.system(cmd)
    return len(gzipped)


def mgz_to_nii(_path):
    """Recursively search path and convert all .mgz files to .nii.gz files.
    """
    mgzs = []
    for root, dirs, files in os.walk(_path):
        for f in files:
            if f[-4:] == '.mgz':
                mgzs.append(os.path.join(root, f))
    for f in mgzs:
        nii = f[:-3] + 'nii.gz'
        cmd = ('mri_convert {} '.format(f) + nii)
        os.system(cmd)

        
def pet_mri_date(rootpath, sub, verbose=False):
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


def pet_mri_date_batch(rootpath):
    """Given a path, this function finds subject folders there and finds 
    the date of the freesurfer processed data.

    Parameters 
    ----------
    rootpath : string
        Path where subject directories lie

    Returns
    -------
    datetbl : DataFrame
        Holds SubjID, MRI_Tp, and MRI_Scandate fields
    """
    subs, _ = _infold(rootpath)
    datetbl = pd.DataFrame(columns=['sub'], data=subs)
    datetbl['MRI_Scandate'] = float('NaN')

    for sub in subs:
        dateout = pet_mri_date(rootpath, sub)
        datetbl.loc[datetbl['sub']==sub,'MRI_Scandate'] = dateout

    datetbl['codea'] = [get_id(sub) for sub in datetbl['sub'].tolist()]
    datetbl['MRI_Tp'] = [get_tp(sub) for sub in datetbl['sub'].tolist()]

    datetbl.drop('sub', axis=1, inplace=True)
    datetbl = datetbl[datetbl['MRI_Tp'].notnull()]
    return datetbl


def extractFSvolumes(rootpath, subs, rois, FS_lut, file_aparc):
    """Extracts the volume of regions from freesurfer-processed MRI data.
    
    Parameters
    ----------
    rootpath : string
        The root directory where MRI data is housed. file_aparc is expected to be in
    rootpath/sublist[x]/mri/
    subs : list 
        list of directories in rootpath that contain data of interest
    rois : list 
        list of freesurfer regions of interest
    FS_lut : dictionary
        dictionary of freesurfer regions and their numerical values
    file_aparc : string 
        name of the file to extract volumes from
    
    Returns
    -------
    mrivols : DataFrame 
        A pandas dataframe where rows are each entry in sublist and columns are entries in roi
    """
    mrivols = pd.DataFrame(subs, columns = ['SubjCode'])
    mrivols['fullpath'] = ['%s%s/mri/' % (rootpath, sub) for sub in mrivols['SubjCode'].tolist()]
    roitbl = pd.DataFrame(index=mrivols.index, columns=rois)
    mrivols = pd.concat([mrivols, roitbl], axis=1)
    for row_index, row in mrivols.iterrows():
        aparcpath = row['fullpath'] + file_aparc
        if os.path.isfile(aparcpath):
            aparc_dat = preproc_aparc(aparcpath)
            for roi in rois:
                row[roi] = get_label_vol(FS_lut, roi, aparc_dat)
    return mrivols


def IDs_infold(path):
    """Extracts list of directories containing ID strings and a list of those  
    ID strings given a path.
    """
    dirs = os.listdir(path)
    subs = []
    subs_id = []
    for sub in dirs:
        _id = get_id(sub)
        if not _id == None:
            subs.append(sub)
            subs_id.append(_id)
    return subs, subs_id


def preproc_aparc(aparcpath):
    """Import and preprocess FS aparc+aseg.mgz file
    """
    #import the data
    aparc_img = nb.load(aparcpath)
    aparc_dat = aparc_img.get_data()
    #preprocess the data
    aparc_dat = aparc_dat.squeeze()
    aparc_dat[np.isnan(aparc_dat)] = 0
    return aparc_dat


def FS_make_lut(path):
    """Reads an excel file holding Freesurfer label values
    and returns a dictionary with region as the key.
    """
    fslut = pd.read_excel(path, parse_cols='A, B')
    fslut.columns = ['value', 'region']
    fslutdict = fslut.set_index('region')['value'].to_dict()
    return fslutdict


def get_id(string):
    """Find the -ID in a string and return it as a string.
    If no -ID is found then return None.
    """
    idmatch = re.search('B\d', string)
    if idmatch:
        _id = idmatch.group()
        return _id

    
def get_tp(string):
    """Find the timepoint in a string and return it as a string.
    If no timepoint is found then return None.
    """
    tpmatch = re.search('\_v(\d)', string)
    if tpmatch:
        tp = tpmatch.group(1)
        return tp


def rate_of_change(tbl, subcol, tpcol, datecol, datacol, slopecol):
    """Takes a datatable holding longintudinal data and calculates rate of change
    in years for your variable of interest. The rate of change value will be 
    added to all rows for each subject.
    
    Parameters
    ----------
    tbl: pandas DataFrame
        DataFrame must contain columns for subject, timepoint, date, and data
    subcol: string
        Name of column containing subject ID. Expects multiple rows per subject 
        ID that correspond with different timepoints
    tpcol: string
        Name of column contaning timepoint. Expects lower timepoints are earlier.
    datecol: string
        Name of column containing time data. Times must be in datetime format.
    datacol: string
        Name of column containing the data to calculate change of
    slopecol: string
        Name of column to be made that will hold the rate of change value
        
    Returns
    -------
    tbl: pandas DataFrame
        Table with additional column with the name of slopecol containing the 
        rate of change for data in datacol
    """
    
    from scipy import stats
    import math

    tbl.sort(columns=[subcol,tpcol], inplace=True)
    
    tbl[slopecol] = float('nan')
    ids = list(set(tbl[subcol]))
    
    for sid in ids:
        sid_ix = tbl[subcol] == sid
        subset = tbl.loc[sid_ix]
        
        if len(subset)<2:
            continue
        else:
            try:
                datediff = ((subset[datecol]-subset[datecol].iloc[0]).astype('timedelta64[D]'))/365.25
                slope, _, _, _, _ = stats.linregress(datediff,subset[datacol])
                if math.isnan(slope) == True:
                    continue
                else:
                    tbl.loc[sid_ix,slopecol] = slope
            except:
                continue
            
    return tbl


def max_per_sub(tbl, subcol, datacol, maxcol):
    """Takes a dataframe holding longitudinal data and extracts the maximum value
    for your variable of interest. This value will be added to all rows for each
    subject.
    
    Parameters
    ----------
    tbl: pandas DataFrame
        DataFrame must contain columns for subject and variable of interest
    subcol : string
        Name of column containing subject ID. Expects multiple rows per subject ID
    datacol : string
        Name of column containing the variable of interest
    maxcol : strong
        Name of column that will be made to hold the maximum value of your 
        variable of interest
        
    Returns
    -------
    tbl : pandas DataFrame
        Table with additional column with the name of maxcol containing the max 
        value in datacol for each subject
    """
    from scipy import stats
    import math
    
    tbl.sort(columns=[subcol,datacol], inplace=True)
    tbl[maxcol] = float('nan')
    ids = list(set(tbl[subcol]))
    
    for sid in ids:
        sid_ix = tbl[subcol] == sid
        subset = tbl.loc[sid_ix]
        
        maxval = max(subset[datacol])
        
        tbl.loc[sid_ix,maxcol] = maxval
        
    return tbl


def save_xls_and_pkl(tbl, filename, path, overwriteold=False):
    """Saves a pandas dataframe as both an excel file and a pickle file.
    Appends the date and time to the end of the filename.
    
    Parameters
    ----------
    tbl : pandas dataframe
    filename : string
        String of the base name you'd like the file to be called
    path : string
        The full path pointing to the save location
    overwriteold : boolean
        If true, delete previous version of the file, if one exists
    """
    import time
    import pickle
    import glob

    if overwriteold==True:
        oldxls = glob.glob(path+filename+'*.xls')
        oldpkl = glob.glob(path+filename+'*.pkl')
        _ = [os.remove(path) for path in oldxls]
        _ = [os.remove(path) for path in oldpkl]

    timestr = time.strftime("%Y%m%d-%H%M%S")
    tbl.to_excel('%s%s_%s.xls' %(path, filename, timestr), index=False)
    tbl.to_pickle('%s/%s_%s.pkl' %(path, filename, timestr))


def linregressTEK(tbl,x,y):
    """Performs linear regression on multiple columns within a DataFrame as the y value 
    and returns a table summarizing the results, where columns are the output of 
    stats.linregress and the rows are the columns regressed. The x value of the regression 
    is the same for all regressions. 
    
    Parameters
    ----------
    tbl : pandas DataFrame
        DataFrame where each row in an observation and columns are variables
    x : string
        Name of the column in tbl corresponding to the x value for linear regression
    y : list
        List of strings which are each the name of a column in tbl to be used as the y
        value for linear regression
        
    Returns
    -------
    lrtbl : pandas DataFrame
        DataFrame where columns are the 5-value output of stats.linregress and rows correspond
        to each regression designated by y
    """

    from scipy import stats

    lrdict = {}
    for yval in y:
        slope, intercept, r_value, p_value, std_err = stats.linregress(tbl[x],tbl[yval])
        lrdict[yval] = [slope, intercept, r_value, p_value, std_err]
    lrtbl = pd.DataFrame(lrdict).T
    lrout = ['XSslope', 'XSintercept', 'XSr_value', 'XSp_value', 'XSstd_err']
    lrtbl.columns = lrout
    return lrtbl