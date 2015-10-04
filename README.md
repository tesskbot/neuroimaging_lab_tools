
# Postdoc work


## Index

* [Goal](#Goal)
* [Python code for data wrangling](#Python code for data wrangling)
* [R code for linear mixed-effects modeling](#R code for linear mixed-effects modeling)
* [Useful tools](#Useful tools)


## <a name="Goal"></a>Goal

My work aimed to analyze the cognitive data from the BACS cohort to understand how memory and cognition change with healthy aging, and how these changes can be predicted by PIB PET status and other neuroimaging biomarkers, lifestyle factors, and genetic factors. 


## <a name="Python code for data wrangling"></a>Python code for data wrangling

All of my python code exists both as .ipynb files (ipython/jupyter notebook files) and as .py files. The package `datapipeline` and all its functions can be run at the command line or within the ipython notebooks. To import the package contents at the command line, you may first need to point to the data using:

```python
import sys
sys.path.insert(0,'path')
```
Change the path 'path' if the location of this package has changed.

### The datapipeline package:

The `datapipeline` package contains code to find, read, and compile longitudinal cognitive data, and also some data from other modalities. The modalities that can currently be gathered are listed in the `gather` subpackage, and more submodules can be added to incoroporate different data modalities. The 'datapipeline_test' folder holds a sample of data used as input ('InData') and the output of all the `datapipeline` scripts below ('OutData') as of August 12th, 2015.

The subpackages of `datapipeline` are:

#### *gather*

The `gathermany` module serves as a front door to the gathering functions. Before running it, you must confirm/change all the paths to point to your data, and designate where you want the data saved. After that, you may run the entire notebook to gather all data modalities and merge them together into summary tables. Cells can also be run individually if you would like to import only a subset of data.

The data modalities these scripts now collect are:

* **Cognitive testing data** is exported from the database that is maintained by the lab manager. Data exports are files holding the data for each cognitive session, and a file holding basic subject information. This data is processed and factor scores are calculated using factor weights calculated previously. The cognitive data is processed using modules `cogtestdates` and `factoranalysis`.

* **PIB data** is extracted using the `pibparams` module. This reads PIB index and subject information from the PIB  directory. 

* **MRI data** calculated by freesurfer (volumes and thicknesses) is extracted from the aseg.stats file by the code in `mri`. Any number of volumes can be extracted by label name. The extraction is done in place - you simply designate the location where MRI data is stored.

* **FDG data** is extracted by the `fdg` module. This function is designed to search a parent directory for FDG data and process all of it.

Each of the modules in `gather` (except the script `gathermany`) contains a function named "*modulename*_run". This function can be called to gather data of that modality. Most other functions within the modules support the "*modulename*_run" function.

#### *merge*

The `datamerge` module takes the outputs of `gather` and combines them into summary tables. Tables can retain full longitudinal character, or they can be flattened, which compresses the table so that each row represents a single subject.

#### *analyze*

Following gathering and merging, the data is analyzed. Two notebooks exist to analyze the data in-line and create visualizations. These modules are not intended to run on the command line.

The code in `summarize` generates summary statistics and plots variables against each other so that data can be better understood. Data is visualized both cross-sectionally and longitudinally. 

No files are saved by the code in `analyze`, so these notebooks may be run in their entirety with no negative consequences. The graphs will display inline.

#### *tools*

The `common_funcs.py` module contains functions perform repeated tasks. Most commonly used is `save_xls_and_pkl` which saves pandas dataframes in both excel and pickle format, appending a timestamp onto the filename.

The `radarplot` module creates a radar chart showing the magnitude of numerous variables. It was modified from [this code](http://gist.github.com/sergiobuj/6721187) and is by no means perfect, but it can be modified to meet your needs.


## <a name="R code for linear mixed-effects modeling"></a>R code for linear mixed-effects modeling

I did linear mixed-effects modeling in R. Linear regression functions are available in some python packages (`stats`, `scikit-learn`), but they do not have built-in functions for mixed-effects modeling. R's `lmer4` package, on the other hand, does. 

### rscripts

#### *mixedmodels.R*

This script imports data into R and performs linear regression. Both standard linear regrssion (using `lmList`) and mixed-effects linear modeling (using `lmer`) are done. They are done separately for the different cognitive domains. Look at summarX files to see the model outputs and p-values.

#### *ploteffects.R*

This function takes the output of `lmer` and generates a bar plot of the fixed effects, in order of magnitude. 


## <a name="Useful tools"></a>Useful tools

### Simultaneously saving .py versions of your .ipynb files

I developed all the python code in ipython notebook and saved it concurrently as .py files, which wrote to the same directory as the ipynb files. If you'd like to do this yourself, find your `ipython_notebook_config.py` file by typing `ipython locate` in the bash command line. Then paste this code into the `ipython_notebook_config.py` file: 

```python
import os
from subprocess import check_call

c = get_config()

def post_save(model, os_path, contents_manager):
    """post-save hook for converting notebooks to .py scripts"""
    if model['type'] != 'notebook':
        return # only do this for notebooks
    d, fname = os.path.split(os_path)
    check_call(['ipython', 'nbconvert', '--to', 'script', fname], cwd=d)

c.FileContentsManager.post_save_hook = post_save
```

These instructions are from this [very helpful Stackoverflow question](https://stackoverflow.com/questions/29329667/ipython-notebook-script-deprecated-how-to-replace-with-post-save-hook).

### Get p-values for `lmer`

The `lmer` function in R does not produce p-values by default. One of many explanations for why that is the case is [here](https://stat.ethz.ch/pipermail/r-help/2006-May/094765.html), but the gist is that calculating the degrees of freedom is very difficult for multilevel regression. If you still want p-values, you can approximate them using one of a few packages listed [here](http://mindingthebrain.blogspot.com/2014/02/three-ways-to-get-parameter-specific-p.html). I used the Satterthwaite approximation. 

### z: a command line tool

Z uses "frecency," a combination of frequency and recency, to help you navigate quickly at the command line to commonly-used folders. You can learn more about it [here](https://github.com/rupa/z). To install it in your shell, enter 

```
curl -k https://raw.githubusercontent.com/rupa/z/master/z.sh -o ~/z.sh
```

at the command line. Then, in your `~/.bashrc` file on the cluster (or `~/.bash_profile` if you are installing on a local machine), add this line: 

```
. ~/z.sh
```

### Fancify your shell

If you want to make your bash shell less boring, add some color! In your `~/.bashrc` file (or `~/.bash_profile` if you are installing on a local machine), you can add some extras. The line

```
PS1="\[\e[0;35m\][\u]@\h \w\n\[\033[1;31m\]$ \[\e[0m\]"
```

will add color to your terminal and print your current path with every new line. That is super helpful if you find yourself getting lost and typing `pwd` a lot.

Adding aliases for `cd` simplifies long strings of directory changes:

```
alias ..="cd .."
alias ...="cd ../.."
alias ....="cd ../../.."
alias .....="cd ../../../.."
```

Adding an alias for ipython notebook is nice, too:

```
alias ipy="ipython notebook"
```

And just for fun:

```
alias fishie="echo '.·¯·.¯·.¸¸.·¯·.¸¸.·¯·.¯·.¸¸.·¯·.¸¸.·¯·.¯·.¸¸.·¯·.¸><(((º>'"
```




```python

```
