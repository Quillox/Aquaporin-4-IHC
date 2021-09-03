# "This script will make a DataFrame from all the .xlxs files in the given directory and make the plots with the desired filters."

# Dependencies:

# Pandas, Matplotlib, Numpy, Scipy, Pingouin (conda install -c conda-forge pingouin), pip install SciencePlots (Matplotlib style)

#TODO add logging

"""
	Using the line plot tool form imageJ and the send to excel plugin, we can make
	an excel file that contains the data from the plot profile tool. There is one
	excel file per .lif file, containing the data from all the images in that .lif.
	You may choose the regions, genotype and the sex that appear in the plot, so
	long as you know the naming scheme used when naming the images acquired during the microscopy
"""

import os
import sys
import warnings
import logging

__author__ = "David Parker"
__version__ = "1.0.0"
__title__ = "Plot_All"
__license__ = "GPLv3"
__author_email__ = "david.parker@unifr.ch"

def parseArgs():
	"""Parse command line arguments"""
	
	import argparse
	
	try:
		parser = argparse.ArgumentParser(
				description='Make plots from excel files in directory') 
		
		parser.add_argument('-p',
							'--path',
							action='store',
							required=True,
							help='The path to the directory with the excel files.')
		parser.add_argument('-v',
							'--verbose',
							action='count',
							default=0,
							help='Verbose behaviour, printing parameters of the script.')
		parser.add_argument('-r',
							'--regions',
							nargs="*", # 0 or more values expected => creates a list
							type=str,
							default=['DorCX','Thal', 'Hypo', 'SCN'],
							help='List with the desired regions to plot. Defaults to : DorCX Thal Hypo SCN')
		parser.add_argument('-g',
							'--genotypes',
							nargs="*",
							type=str,
							default=['TPer2KO', 'Per2flfl'],
							help='The genotypes to plot. Choose from Per2flfl or TPer2KO')
		parser.add_argument('-s', #TODO add this 
							'--sex',
							action='store',
							default=False,
							help='The sex you wish to plot. Choose from f or m. Leave blank to combine both')
		parser.add_argument('-x',
							'--excel',
							action='store_true',
							#default=False,
							help='Choose to write the different stages of the data processing to excel files.')
		parser.add_argument('-t',
							'--tex',
							action='store_true',
							#default=False,
							help='Choose to write the different stages of the data processing to tex files.')
	except:
		print("An exception occurred with argument parsing. Check your provided options.")
		traceback.print_exc()

	return parser.parse_args()

# Place all the functions here

# MATLAB's tic toc equivalent (From user:4191389 Benben on SO)
import time
def TicTocGenerator():
	# Generator that returns time differences
	ti = 0           # initial time
	tf = time.time() # final time
	while True:
		ti = tf
		tf = time.time()
		yield tf-ti # returns the time difference
TicToc = TicTocGenerator() # create an instance of the TicTocGen generator
# This will be the main function through which we define both tic() and toc()
def toc(tempBool=True):
	# Prints the time difference yielded by generator instance TicToc
	tempTimeInterval = next(TicToc)
	if tempBool:
		print( "Elapsed time: %f seconds.\n" %tempTimeInterval )
def tic():
	# Records a time in TicToc, marks the beginning of a time interval
	toc(False)

# (From user:8394915 cheersmate on SO)
def barplot_annotate_brackets(num1, num2, data, center, height, ax, yerr=None, dh=.05, barh=.05, fs=None, maxasterix=None):
	""" 
	Annotate barplot with p-values.
	Ty cheersmate from SO
	https://stackoverflow.com/questions/11517986/indicating-the-statistically-significant-difference-in-bar-graph

	:param num1: number of left bar to put bracket over
	:param num2: number of right bar to put bracket over
	:param data: string to write or number for generating asterixes
	:param center: centers of all bars (like plt.bar() input)
	:param height: heights of all bars (like plt.bar() input)
	:param yerr: yerrs of all bars (like plt.bar() input)
	:param dh: height offset over bar / bar + yerr in axes coordinates (0 to 1)
	:param barh: bar height in axes coordinates (0 to 1)
	:param fs: font size
	:param maxasterix: maximum number of asterixes to write (for very small p-values)
	"""

	import matplotlib.pyplot as plt

	if type(data) is str:
		text = data
	else:
		# * is p < 0.05
		# ** is p < 0.005
		# *** is p < 0.0005
		# etc.
		text = ''
		p = .05

		while data < p:
			text += '*'
			p /= 10.

			if maxasterix and len(text) == maxasterix:
				break

		if len(text) == 0:
			text = 'n. s.'

	lx, ly = center[num1], height[num1]
	rx, ry = center[num2], height[num2]

	if yerr:
		ly += yerr[num1]
		ry += yerr[num2]

	ax_y0, ax_y1 = plt.gca().get_ylim()
	dh *= (ax_y1 - ax_y0)
	barh *= (ax_y1 - ax_y0)

	y = max(ly, ry) + dh

	barx = [lx, lx, rx, rx]
	bary = [y, y+barh, y+barh, y]
	mid = ((lx+rx)/2, y+barh)

	ax.plot(barx, bary, c='black')

	kwargs = dict(ha='center', va='bottom')
	if fs is not None:
		kwargs['fontsize'] = fs

	ax.text(*mid, text, **kwargs)

def fct_name(var1, var2, verbose):
	"""Fct that checks the input data"""
	# import packages

	# Do a little sanity checking:

	if verbose > 0: print("what the fct/loop is doing")

	# check your input data
	a = 1
	if a != 1:
		sys.stderr.write("data makes no sense, check your data")
		sys.exit(1)

	return a

def make_big_DataFrame(path, verbose):
	"""
		Fct that makes one big DataFrame with all the excel files in the directory.
	"""
	import os
	import warnings
	import pandas as pd
	import traceback

	if verbose > 0: print("##############################################\n")
	if verbose > 0: tic()

	big_df = []
	with os.scandir(path=path) as it:
		if verbose > 0: print('Scanning directory at ' + path +'\n')
		for entry in it:
			if entry.name.endswith(".xlsx") and entry.is_file():
				if verbose > 0: print('\tFound .xlsx file : importing data from', entry.name)
				# Import data
				warnings.simplefilter("ignore") # To suppress an annoying openpyxl warning
				df = pd.read_excel(path + entry.name,
					header=[0,1],
					dtype='float64')
				warnings.simplefilter("default")
				# Clean data
				if verbose > 0: print("\t\tRemoving empty columns")
				df.dropna(axis=1, how='all', inplace=True) # Remove empty columns
				if verbose > 0: print("\t\tAppending to master DataFrame\n")
				big_df.append(df)
	if verbose > 0: toc()
	if verbose > 0: print("##############################################\n")

	return pd.concat(big_df, axis=1, verify_integrity=True, copy=False)

def merge_on_distance(df, verbose, bins):
	"""
		Fct that takes all the unique (distance, value) pairs and
		makes a dataframe with one distance column containing all the 
		unique distances, and then all the values as the rest of the 
		columns, lined up to their corresponding distance.
		Many thanks to /u/sarrysyst

		An alternative is to use numpy.interp
		https://numpy.org/doc/stable/reference/generated/numpy.interp.html
	"""

	import pandas as pd
	import numpy as np
	from functools import reduce
	
	if verbose > 0: tic()
	if verbose > 0: print("##############################################\n")
	if verbose > 0: print("Beginning merging on distance process :")

	# Make list with the data split by level 0 header
	if verbose > 0: print("\tSplitting dataframe by image into list")
	df_list_small = []
	names = list(set(df.columns.get_level_values(0).tolist()))
	for name in names:
		df_list_small.append(pd.concat({name: df[name]}, axis=1).dropna(how='all', axis=0))
		if verbose > 1: print("\t\t", name)
	# get all unique distances into a separate dataframe
	if verbose > 0: print("\tRetrieving and sorting unique distances")
	# The np.sort step is CRUCIAL !
	unique_dists = pd.unique(df.filter(regex='Dist').values.ravel('K')) #.ravel makes a list from the values.  the K option describes how the values are stored in memory
	df_distances_big = pd.DataFrame({'dist':np.sort(unique_dists)})
	df_merged_small_list = [df_distances_big]

	# Start by merging all the smaller dfs in the list on their distances
	if verbose > 0: print("\tMerging dataframes in list")
	for df_small in df_list_small:

		# distance columns need to have the same column names to use merge later on
		col_names = []
		for i, col in enumerate(df_small.columns):
			if i % 2 == 0:
				col_names.append('dist')
			else:
				col_names.append(col)
		df_small.columns = col_names

		# get all unique distances into a separate dataframe
		df_distances_small = pd.DataFrame(df_small.iloc[:,::2].stack().unique(), columns=['dist'])
		# create list of dataframe slices of each individual dist/val pairs
		pairs_small = [df_distances_small] + [df_small.iloc[:,i:i+2] for i in range(0, len(df_small.columns), 2)]
		
		# merge individual slices on df_distances which has all unique distance values
		df_merged_small = reduce(lambda  left, right: pd.merge(left, right, on=['dist'],  how='outer'), pairs_small)

		# this part is optional to reduce the distances into set bins, adjust the range and stepsize to fit your needs
		df_resampled_small = df_merged_small.groupby(pd.cut(df_merged_small["dist"], np.arange(-15, 15+0.5, 0.5), include_lowest=True)).mean()
		df_resampled_small.drop(columns=['dist'], axis=1, inplace=True)

		# Append the merged df to the list
		df_merged_small_list.append(df_merged_small.dropna(how='all', axis=0))

	# Not sure if I need to leave this line..
	df_master_list = df_merged_small_list.insert(0,df_distances_big)

	# merge the smaller merged dfs onto the sorted list of unique distances
	if verbose > 0: print("\tMerging merged dataframes on unique distances into masterframe")
	df_merged_big = reduce(lambda  left, right: pd.merge(left, right, on=['dist'],  how='outer'), df_merged_small_list)

	#df_merged_big.to_excel('NotBineed_Raw_data.xlsx')

	# this part is optional to reduce the distances into set bins, adjust the range and stepsize to fit your needs
	# !!! This introduces error : taking the mean of the values in the bin is not good, its not an iterpolation. it also changes the distance values of the intensity values.
	# 		some columns are modified, while others aren't
	df_resampled_big = df_merged_big.groupby(pd.cut(df_merged_big["dist"], np.arange(-15, 15+0.5, 0.25), include_lowest=True)).mean()
	# this doesnt work : df_resampled_big.drop(columns=['dist'], axis=1, inplace=True)

	if verbose > 0: print("\n")
	if verbose > 0: toc()
	if verbose > 0: print("\n##############################################\n")

	if bins :
		return df_resampled_big #this one has bins
	if not bins :
		return df_merged_big # no bins

def make_std_long(df, verbose, path, write_excel, tex):
	'''
	This takes the output of the merge_on_distance function, and processes the data into long format.
	!!! It takes only the maximum standard score from each line profile !!!
	You must also have used a very specific file naming convention when aquiring the data during the microscopy :
		file name : "XXX_sex_genotype_timepoint_XXX.lif ", in that order
		Region names in the LasX navigator : region_XXX
	The exact names for each variable must be :
		sex : "m" or "f"
		genotype : "Per2flfl" or "TPer2KO"
		timepoint : "ZT6" or "ZT18"
		region names : "DorCX" or "Thal" or "Hypo" or "SCN" 
	'''

	import pandas as pd
	import numpy as np

	if verbose > 0: tic()
	if verbose > 0: print("##############################################\n")
	if verbose > 0: print("Converting merged data to long format")
	if verbose > 0: toc()
	if verbose > 0: print("##############################################\n")

	# Extract the desired quantity from the merged data :
	def standard_score_max(col):
		return np.max(( col - np.mean(col) ) / np.std(col))

	df_std = pd.DataFrame(df.filter(regex='Value').apply(standard_score_max, raw=False, axis=0))

	# Function to split the ImageJ file name
	def split(delimiters, string, maxsplit=0):
		import re
		regexPattern = '|'.join(map(re.escape, delimiters))
		return re.split(regexPattern, str(string), maxsplit)

	# The "_" is my choice, the "/" is made by LASX when it finds the names of your regions in the navigator
	delimiters = "_", "/"

	# Converts the index of the df to type "variable:value,variable:value,..."
	def isolate_variables (index):
		variables = ['f', 'm', 'ZT6', 'ZT18', 'TPer2KO', 'Per2flfl', 'DorCX', 'Thal', 'Hypo', 'SCN']
		names = ['sex', 'genotype', 'timepoint', 'region']
		result = []
		for x in split(delimiters, index) :
			if x in variables:
				result.append(''.join(filter(str.isalnum, x)))
		return ','.join(a + ':' + b for a,b in zip(names, result))

	# Makes a column with the variable:value,variable:value,... format
	df_std['variables'] = df_std.index.map(isolate_variables)

	# Makes each variable a column and attributes the correct value to each row
	df_std_long = df_std['variables'].str.split(",", expand=True)
	cols = []
	for col in df_std_long:
		df_temp = df_std_long[col].str.split(":", expand=True)
		df_std_long[col] = df_temp[1]
		cols.append(df_temp.iloc[0, 0])
	df_std_long.columns = cols
	df_std_long['intensity'] = df_std[0]

	if write_excel :
		if verbose > 0: print("\tSaving data to " + path +'Long_data.xlsx')
		df_std_long.to_excel(path+'Long_data.xlsx')
	
	# Make df for report :
	df_std_long_counts = df_std_long.value_counts(subset=['sex', 'genotype', 'timepoint'], sort=False)
	df_std_long_counts.loc["Total"] = df_std_long_counts.sum()

	df_std_long_counts_region = df_std_long.value_counts(subset=['sex', 'genotype', 'timepoint', 'region'], sort=False)
	df_std_long_counts_region.loc["Total"] = df_std_long_counts_region.sum()

	df_std_long_counts_Only_region = df_std_long.value_counts(subset=['region'], sort=False)
	df_std_long_counts_Only_region.loc["Total"] = df_std_long_counts_Only_region.sum()

	if write_excel :
		if verbose > 0: print("\tSaving data to " + path +'Long_data.xlsx')
		df_std_long_counts.to_excel(path+'Counts.xlsx')
		df_std_long_counts_region.to_excel(path+'Counts_regions.xlsx')
		df_std_long_counts_Only_region.to_excel(path+'Counts_only_regions.xlsx')
	
	if tex :
		df_std_long_counts.to_latex(buf=path+'Counts.tex', header=True , index=True , na_rep='--',float_format="%.1f", index_names=True , bold_rows=True , longtable=True , escape=False ,multicolumn=True , multicolumn_format='c', caption='Number of blood vessels acquired for the experiment, separated by type.', label='tab:vessel_counts', position='H')
		df_std_long_counts_region.to_latex(buf=path+'Counts_regions.tex', header=True , index=True , na_rep='--',float_format="%.1f", index_names=True , bold_rows=True , longtable=True , escape=False ,multicolumn=True , multicolumn_format='c', caption='Number of blood vessels acquired for the experiment, separated by type.', label='tab:vessel_counts_regions', position='H')
		df_std_long_counts_Only_region.to_latex(buf=path+'Counts_only_regions.tex', header=True , index=True , na_rep='--',float_format="%.1f", index_names=True , bold_rows=True , longtable=True , escape=False ,multicolumn=True , multicolumn_format='c', caption='Number of blood vessels acquired for the experiment, separated by region.', label='tab:vessel_counts_only_regions', position='H')

	return df_std_long

def make_plot(df, sex, genotype, regions, verbose, path, write_excel):
	"""
		Fct that plots and saves a figure for each region.
		Each plot as day and night
	"""
	# pip install SciencePlots
	import pandas as pd
	import matplotlib.pyplot as plt
	import numpy as np

	if verbose > 0: tic()
	if verbose > 0: print("##############################################\n")
	if verbose > 0: print("Making plots :")

	# New directory to save the Boxplot data and plots
	new_dir = path+genotype+'\\'
	try:
		os.makedirs(new_dir)
	except OSError:
		if verbose > 0: print ('Failed to make directory :', new_dir, ' to store the data. It may already exist\n')
	else:
		if verbose > 0: print('Made directory :', new_dir, ' to store the data sorted by genotype\n')
	
	path = path+genotype+'\\'

	# Filter by genotype
	if verbose > 0: print("\tFiltering by genotype :", genotype)
	df = df.filter(regex=f'(?=.*{genotype})|dist').dropna(axis=0, how='all')
	
	#DONE need to do the normalisation step here, not after the mean calculations.
	# Subtract the offset and devide by the variance of the background ?

	def standard_score(col):
		"""
		 The standard score is the number of standard deviations by which the value of a raw score 
		 (i.e., an observed value or data point) is above or below the mean value 
		 of what is being observed or measured.
		 It is calculated by subtracting the population mean from an individual raw score
		 and then dividing the difference by the population standard deviation.
		 https://en.wikipedia.org/wiki/Standard_score
		"""
		return ( col - np.mean(col) ) / np.std(col)

	# Make df with the standard score
	df_standard_score = pd.DataFrame(df.filter(regex='Value').apply(standard_score, raw=True, axis=0))
	df_standard_score['dist'] = df['dist']

	# Add the mean and sem for each region and time
	if verbose > 0: print("\tComputing mean and SEM values for :")
	for region in regions:
		if verbose > 0: print("\t\t", region, 'night')
		df[region,'Mean_ZT18'] = df.filter(regex=f'(?=.*{region})(?=.*ZT18)(?=.*Value)').mean(axis=1)
		df[region,'SEM_ZT18'] = df.filter(regex=f'(?=.*{region})(?=.*ZT18)(?=.*Value)').sem(axis=1)

		if verbose > 0: print("\t\tStandard score : ", region, 'night')
		df_standard_score[region,'Mean_ZT18'] = df_standard_score.filter(regex=f'(?=.*{region})(?=.*ZT18)(?=.*Value)').mean(axis=1)
		df_standard_score[region,'SEM_ZT18'] = df_standard_score.filter(regex=f'(?=.*{region})(?=.*ZT18)(?=.*Value)').sem(axis=1)

		if verbose > 0: print("\t\t", region, 'day')
		df[region,'Mean_ZT6'] = df.filter(regex=f'(?=.*{region})(?=.*ZT6)(?=.*Value)').mean(axis=1)
		df[region,'SEM_ZT6'] = df.filter(regex=f'(?=.*{region})(?=.*ZT6)(?=.*Value)').sem(axis=1)

		if verbose > 0: print("\t\tStandard score : ", region, 'night')
		df_standard_score[region,'Mean_ZT6'] = df_standard_score.filter(regex=f'(?=.*{region})(?=.*ZT6)(?=.*Value)').mean(axis=1)
		df_standard_score[region,'SEM_ZT6'] = df_standard_score.filter(regex=f'(?=.*{region})(?=.*ZT6)(?=.*Value)').sem(axis=1)
	
	# Save the Datframe to .xlsx for reference
	if verbose and write_excel > 0: print("\n\tWriting DataFrame to :", path+'Filtered_'+genotype+'.xlsx')
	if write_excel :
		df.to_excel(path+'Filtered_'+genotype+'_data.xlsx')
		df_standard_score.to_excel(path+'Filtered_standard_score_'+genotype+'_data.xlsx')

	# Make the plots
	if verbose > 0: print("\n\tPloting data\n")

	# Figure parameters
	n_rows = len(regions)
	n_cols = 1
	figsize = (5, len(regions) * 5 + 2)
	title_font_size = 20
	plt.style.use(['science','grid'])
	plt.tight_layout(pad=0.5)

	# Line plots

	fig_line, axes_line = plt.subplots(nrows=n_rows, ncols=n_cols, figsize=figsize)
	fig_line.subplots_adjust(top=0.90)
	fig_line.suptitle('Average intensity of AQP-4 staining for ' + genotype + ' mice.', fontsize=title_font_size)

	for ax, region in zip(axes_line.flatten(), regions):
		ax.grid()
		ax.plot(df['dist'], df[region,'Mean_ZT18'], 'r', linestyle='', marker='.', label='ZT18')
		ax.fill_between(df['dist'], df[region,'Mean_ZT18'] - df[region,'SEM_ZT18'], df[region,'Mean_ZT18'] + df[region,'SEM_ZT18'], color='r', alpha=0.5)
		ax.plot(df['dist'], df[region,'Mean_ZT6'], 'g', linestyle='', marker='.', label='ZT6')
		ax.fill_between(df['dist'], df[region,'Mean_ZT6'] - df[region,'SEM_ZT6'], df[region,'Mean_ZT6'] + df[region,'SEM_ZT6'], color='g', alpha=0.5)
		ax.set(title=region, xlabel='Distance ($\mu$m)', ylabel=('Intensity (A.U)'))
		ax.grid()
		ax.legend()
	
	plt.savefig(path + genotype + '_mice_' + 'LinePlot.pdf')
	plt.close()

	if verbose > 0: print('\tSaved Line plot as', path + genotype + '_mice_' + 'LinePlot.pdf\n')

	# Line Standard score plot

	fig_standard_score, axes_standard_score = plt.subplots(nrows=n_rows, ncols=n_cols, figsize=figsize)
	# fig_standard_score.subplots_adjust(hspace=0.1)
	# fig_standard_score.suptitle('Average intensity of AQP-4 staining for ' + genotype + ' mice.\nStandard score', fontsize=title_font_size)

	for ax, region in zip(axes_standard_score.flatten(), regions):
		ax.grid()
		ax.plot(df_standard_score['dist'], df_standard_score[region,'Mean_ZT18'], 'r', linestyle='', marker='.', label='ZT18')
		ax.fill_between(df_standard_score['dist'], df_standard_score[region,'Mean_ZT18'] - df_standard_score[region,'SEM_ZT18'], df_standard_score[region,'Mean_ZT18'] + df_standard_score[region,'SEM_ZT18'], color='r', alpha=0.5)
		ax.plot(df_standard_score['dist'], df_standard_score[region,'Mean_ZT6'], 'g', linestyle='', marker='.', label='ZT6')
		ax.fill_between(df_standard_score['dist'], df_standard_score[region,'Mean_ZT6'] - df_standard_score[region,'SEM_ZT6'], df_standard_score[region,'Mean_ZT6'] + df_standard_score[region,'SEM_ZT6'], color='g', alpha=0.5)
		ax.set(title=region, xlabel='Distance ($\mu$m)', ylabel=('Intensity (STD)'))
		ax.grid()
		ax.legend()
	
	plt.savefig(path + genotype + '_mice_' + 'LinePlot_standard_score.pdf')
	plt.close()

	if verbose > 0: print('\tSaved Line plot as', path + genotype + '_mice_' + 'LinePlot_standard_score.pdf\n')


	# Line plots minus the background

	# Function that subtracts the mean of the 1st and last 3rd from the array
	def substract_background(col):
		return col - np.mean(col[list(list(range(0,round(len(col)*1/3))) + list(range(round(len(col)*2/3), len(col))))])

	df_Back_Sub = pd.DataFrame(df.filter(regex='Mean|SEM').apply(substract_background, raw=True, axis=0))
	df_Back_Sub['dist'] = df['dist']

	fig_line_backsub, axes_line_backsub = plt.subplots(nrows=n_rows, ncols=n_cols, figsize=figsize)
	fig_line_backsub.subplots_adjust(top=0.90)
	fig_line_backsub.suptitle('Average intensity of AQP-4 staining for ' + genotype + ' mice.\nMinus the background', fontsize=title_font_size)

	for ax, region in zip(axes_line_backsub.flatten(), regions):
		ax.grid()
		ax.plot(df_Back_Sub['dist'], df_Back_Sub[region,'Mean_ZT18'], 'r', linestyle='', marker='.', label='ZT18')
		ax.fill_between(df_Back_Sub['dist'], df_Back_Sub[region,'Mean_ZT18'] - df_Back_Sub[region,'SEM_ZT18'], df_Back_Sub[region,'Mean_ZT18'] + df_Back_Sub[region,'SEM_ZT18'], color='r', alpha=0.5)
		ax.plot(df_Back_Sub['dist'], df_Back_Sub[region,'Mean_ZT6'], 'g', linestyle='', marker='.', label='ZT6')
		ax.fill_between(df_Back_Sub['dist'], df_Back_Sub[region,'Mean_ZT6'] - df_Back_Sub[region,'SEM_ZT6'], df_Back_Sub[region,'Mean_ZT6'] + df_Back_Sub[region,'SEM_ZT6'], color='g', alpha=0.5)
		ax.set(title=region, xlabel='Distance ($\mu$m)', ylabel=('Intensity (A.U)'))
		ax.grid()
		ax.legend()
	
	plt.savefig(path + genotype + '_mice_' + '_BackGroundSub_LinePlot.pdf')
	plt.close()

	if verbose > 0: print('\tSaved Line plot with background subtracted as', path + genotype + '_mice_' + '_BackGroundSub_LinePlot.pdf\n')

	# Boxplots
	# DONE Each dot in the box plot is an individual blood vessel, not the average of all the vessels.
	# DONE Add statistical analysis

	# Function that subtracts the mean of the 1st and last 3rd from the array and returns the max
	def substract_background_max(col):
		return np.max(col - np.mean(col[list(list(range(0,round(len(col)*1/3))) + list(range(round(len(col)*2/3), len(col))))]))

	def standard_score_max(col):
		return np.max(( col - np.mean(col) ) / np.std(col))
	
	# Retrives the values for the boxplot
	df_values = pd.DataFrame(df.filter(regex='Value').apply(substract_background_max, raw=False, axis=0)).T
	df_values_standard_score = pd.DataFrame(df.filter(regex='Value').apply(standard_score_max, raw=False, axis=0)).T

	# Make a multiindexed df for the boxplot
	iterables = [regions, ['ZT6', 'ZT18']]
	index = pd.MultiIndex.from_product(iterables, names=["region", "time"])

	# Fills the df with the correct data for each region and time point
	df_box = pd.DataFrame(index=index).T
	for region in regions:
		df_box[region, 'ZT6'] = pd.Series(df_values.filter(regex=f'(?=.*ZT6)(?=.*{region})').iloc[0].values)
		df_box[region, 'ZT18'] = pd.Series(df_values.filter(regex=f'(?=.*ZT18)(?=.*{region})').iloc[0].values)

	df_box_standard_score = pd.DataFrame(index=index).T
	for region in regions:
		df_box_standard_score[region, 'ZT6'] = pd.Series(df_values_standard_score.filter(regex=f'(?=.*ZT6)(?=.*{region})').iloc[0].values)
		df_box_standard_score[region, 'ZT18'] = pd.Series(df_values_standard_score.filter(regex=f'(?=.*ZT18)(?=.*{region})').iloc[0].values)


	def min_max_rescale(x):
		#TODO make this rescale with the extrema of the entire group, not inside each one.
		return (x-x.min())/(x.max()-x.min())

	# Apply min-max normalization. Gives values between 0 and 1
	# df_box = df_box.apply(min_max_rescale, axis=0)

	# BoxPlots background sub
	fig_Box, axes_Box = plt.subplots(nrows=n_rows, ncols=n_cols, figsize=figsize)
	fig_Box.subplots_adjust(top=0.90)
	fig_Box.suptitle('Average intensity of AQP-4 staining for ' + genotype + ' mice.\nBackground substracted', fontsize=title_font_size)

	# Dataframe for storing statistical data
	df_box_stats = pd.DataFrame(data=None, index=['statistic', 'pvalue'], columns=regions)

	for ax, region in zip(axes_Box.flatten(), regions):
		df_box[region].boxplot(ax=ax, )
		ax.set(title=region, xlabel='Time point', ylabel=('Intensity (A.U)'))
		#ax.legend()

		# Statistical analysis
		# TODO find out why the p-value changes when running twice on the same data
		from scipy import stats

		if verbose > 0: print('\tPerforming statistical analysis on the region : ' + region)

		region_stats = stats.ttest_ind(df_box[region, 'ZT6'].dropna(), df_box[region, 'ZT18'].dropna(), axis=0, equal_var=False, nan_policy='raise', alternative='greater')
		df_box_stats.loc['statistic', region] = region_stats.statistic
		df_box_stats.loc['pvalue', region] = region_stats.pvalue
		if verbose > 0: print(region_stats) #TODO Make sure the stats and pvalue are the right way around

		# Annotate the boxplots
		height = np.max(df_box[region].max(axis=1))*np.ones(len(regions))
		bars = np.arange(len(regions))
		barplot_annotate_brackets(1, 2, region_stats.pvalue, bars, height, ax)

	plt.savefig(path + genotype + '_mice_' + 'Box_Plot_background_subed.pdf')
	plt.close()

	if verbose > 0: print('\tSaved Box plot with background subtracted as', path + genotype + '_mice_' + 'Box_Plot_background_subed.pdf\n')

	if write_excel : df_box.to_excel(path + 'Boxplot_' + genotype + '_data.xlsx')
	if write_excel : df_box_stats.to_excel(path + 'df_box_stats_background_sub' + genotype + '_data.xlsx')

	# BoxPlots Standard score
	fig_Box_standard_score, axes_Box_standard_score = plt.subplots(nrows=n_rows, ncols=n_cols, figsize=figsize)
	fig_Box_standard_score.subplots_adjust(top=0.90)
	fig_Box_standard_score.suptitle('Average intensity of AQP-4 staining for ' + genotype + ' mice\nStandard Score.', fontsize=title_font_size)

	# Dataframe for storing statistical data
	df_box_stats_std = pd.DataFrame(data=None, index=['statistic', 'pvalue'], columns=regions)

	for ax, region in zip(axes_Box_standard_score.flatten(), regions):
		df_box_standard_score[region].boxplot(ax=ax, )
		ax.set(title=region, xlabel='Time point', ylabel=('Intensity (STD)'))
		#ax.legend()

		# Statistical analysis
		# TODO find out why the p-value changes when running twice on the same data
		from scipy import stats

		if verbose > 0: print('\tPerforming statistical analysis on the region : ' + region)

		region_stats = stats.ttest_ind(df_box_standard_score[region, 'ZT6'].dropna(), df_box_standard_score[region, 'ZT18'].dropna(), axis=0, equal_var=False, nan_policy='raise', alternative='greater')
		df_box_stats_std.loc['statistic', region] = region_stats.statistic
		df_box_stats_std.loc['pvalue', region] = region_stats.pvalue
		if verbose > 0: print(region_stats) #TODO Make sure the stats and pvalue are the right way around

		# Annotate the boxplots
		height = np.max(df_box_standard_score[region].max(axis=1))*np.ones(len(regions))
		bars = np.arange(len(regions))
		barplot_annotate_brackets(1, 2, region_stats.pvalue, bars, height, ax)

	plt.savefig(path + genotype + '_mice_' + 'Box_Plot_standard_score.pdf')
	plt.close()

	if verbose > 0: print('\n\tSaved Box plot with standard scores as', path + genotype + '_mice_' + 'Box_Plot_standard_score.pdf\n')

	if write_excel : df_box_standard_score.to_excel(path + 'Boxplot_standard_score_' + genotype + '_data.xlsx')
	if write_excel : df_box_stats_std.to_excel(path + 'df_box_stats_std_' + genotype + '_data.xlsx')

	if verbose > 0: toc()
	if verbose > 0: print("##############################################\n")

	return(0)

def make_boxplots(df, sex, regions, verbose, path, write_excel, tex):
	"""
		Fct that plots and saves a figure for each region.
		Each plot as day and night or genotype
	"""
	# pip install SciencePlots
	import pandas as pd
	import matplotlib.pyplot as plt
	import numpy as np
	#import pingouin as pg

	if verbose > 0: tic()
	if verbose > 0: print("##############################################\n")
	if verbose > 0: print("Making box plots for ANOVA :")

	# New directory to save the Boxplot data and plots
	new_dir = path+'ANOVA'+'\\'
	try:
		os.makedirs(new_dir)
	except OSError:
		if verbose > 0: print ('Failed to make directory :', new_dir, ' to store the Boxplots. It may already exist\n')
	else:
		if verbose > 0: print('Made directory :', new_dir, ' to store the BoxPlots\n')
	
	path_box = path+'ANOVA'+'\\'

	# Genotypes to use with the regex filters
	genotypes = {'KO':'TPer2KO', 'CO':'Per2flfl'}

	# Filter by genotype
	if verbose > 0: print("\tFiltering by genotype and or time point :")

	# Separate either by time point (ZT6/ZT18) or by genotype (KO/CO)
	df_CO = df.filter(regex=f'(?=.*{genotypes["CO"]})|dist').dropna(axis=0, how='all')
	df_KO = df.filter(regex=f'(?=.*{genotypes["KO"]})|dist').dropna(axis=0, how='all')
	df_ZT6 = df.filter(regex=f'(?=.*ZT6)|dist').dropna(axis=0, how='all')
	df_ZT18 = df.filter(regex=f'(?=.*ZT18)|dist').dropna(axis=0, how='all')

	# Save Datframes to .xlsx for reference
	if verbose and write_excel > 0: print("\n\tWriting DataFrame to :", path_box+'DataFrame_BoxPlots_CO_KO_ZT18_ZT6_data.xlsx')
	if write_excel :
		df_CO.to_excel(path_box+'DataFrame_BoxPlots_CO_data.xlsx')
		df_KO.to_excel(path_box+'DataFrame_BoxPlots_KO_data.xlsx')
		df_ZT6.to_excel(path_box+'DataFrame_BoxPlots_ZT6_data.xlsx')
		df_ZT18.to_excel(path_box+'DataFrame_BoxPlots_ZT18_data.xlsx')

	def standard_score_max(col):
		return np.max(( col - np.mean(col) ) / np.std(col))
	
	# Retrives the values for the boxplot
	df_CO_std = pd.DataFrame(df_CO.filter(regex='Value').apply(standard_score_max, raw=False, axis=0)).T
	df_KO_std = pd.DataFrame(df_KO.filter(regex='Value').apply(standard_score_max, raw=False, axis=0)).T
	df_ZT6_std = pd.DataFrame(df_ZT6.filter(regex='Value').apply(standard_score_max, raw=False, axis=0)).T
	df_ZT18_std = pd.DataFrame(df_ZT18.filter(regex='Value').apply(standard_score_max, raw=False, axis=0)).T

	# Make 2 multiindexed dfs for the boxplots
	iterables_time_points = [regions, ['ZT6', 'ZT18']]
	index_time_points = pd.MultiIndex.from_product(iterables_time_points, names=["region", "time"])

	iterables_genotypes = [regions, [genotypes['CO'], genotypes['KO']]]
	index_genotypes = pd.MultiIndex.from_product(iterables_genotypes, names=["region", "genotype"])

	# Fills the dfs with the correct data for each region and time point
	df_box_CO = pd.DataFrame(index=index_time_points).T
	for region in regions:
		df_box_CO[region, 'ZT6'] = pd.Series(df_CO_std.filter(regex=f'(?=.*ZT6)(?=.*{region})').iloc[0].values)
		df_box_CO[region, 'ZT18'] = pd.Series(df_CO_std.filter(regex=f'(?=.*ZT18)(?=.*{region})').iloc[0].values)
	
	df_box_KO = pd.DataFrame(index=index_time_points).T
	for region in regions:
		df_box_KO[region, 'ZT6'] = pd.Series(df_KO_std.filter(regex=f'(?=.*ZT6)(?=.*{region})').iloc[0].values)
		df_box_KO[region, 'ZT18'] = pd.Series(df_KO_std.filter(regex=f'(?=.*ZT18)(?=.*{region})').iloc[0].values)
	
	df_box_ZT6 = pd.DataFrame(index=index_genotypes).T
	for region in regions:
		df_box_ZT6[region, genotypes['CO']] = pd.Series(df_ZT6_std.filter(regex=f'(?=.*{genotypes["CO"]})(?=.*{region})').iloc[0].values)
		df_box_ZT6[region, genotypes['KO']] = pd.Series(df_ZT6_std.filter(regex=f'(?=.*{genotypes["KO"]})(?=.*{region})').iloc[0].values)
	
	df_box_ZT18 = pd.DataFrame(index=index_genotypes).T
	for region in regions:
		df_box_ZT18[region, genotypes['CO']] = pd.Series(df_ZT18_std.filter(regex=f'(?=.*{genotypes["CO"]})(?=.*{region})').iloc[0].values)
		df_box_ZT18[region, genotypes['KO']] = pd.Series(df_ZT18_std.filter(regex=f'(?=.*{genotypes["KO"]})(?=.*{region})').iloc[0].values)

	# Master DataFrame for boxplots
	df_box_ZT6.columns = pd.MultiIndex.from_product(df_box_ZT6.columns.levels + [['ZT6']], names=["region", "genotype", "timepoint"])
	df_box_ZT18.columns = pd.MultiIndex.from_product(df_box_ZT18.columns.levels + [['ZT18']], names=["region", "genotype", "timepoint"])
	df_box_master = pd.concat([df_box_ZT6, df_box_ZT18], axis=1).swaplevel('timepoint', 'genotype', axis=1)

	# Save Datframe to .xlsx for reference
	if verbose and write_excel > 0: print("\n\tWriting Master Box DataFrame to :", path_box+'DataFrame_BoxPlots_MASTER.xlsx')
	if write_excel :
		df_box_master.to_excel(path_box+'DataFrame_BoxPlots_MASTER.xlsx')
	# df_box_master.to_latex(buf=’path_box+"DataFrame_BoxPlots_MASTER.tex", header=True , index=True , na_rep=’--’,float_format="%.1f", index_names=True , bold_rows=True , longtable=True , escape=False ,multicolumn=True , multicolumn_format=’c’, caption=’Data  acquired  from  themultimeter  during  the   potential  measurements  between  the  quinhydrone  andferrocyante  solutions , at  three  different  temperatures ’, label=’tab:exp18_data ’,position=’H’)

	# Make the BoxPlots

	# New directory to save the Boxplot stats
	new_dir_stats = path_box+'Stats'+'\\'
	try:
		os.makedirs(new_dir_stats)
	except OSError:
		if verbose > 0: print ('Failed to make directory :', new_dir_stats, ' to store the Boxplots stats. It may already exist\n')
	else:
		if verbose > 0: print('Made directory :', new_dir_stats, ' to store the BoxPlots stats\n')
	
	path_box_stats = path_box+'Stats'+'\\'

	# Figure parameters
	n_rows = 2
	n_cols = 2
	figsize = (12,12)
	title_font_size = 20
	plt.style.use(['science','grid'])
	plt.tight_layout(pad=0.5)

	# One subplot per region. Each subplot with 4 boxes ZT6 (CO+KO) and ZT18 (CO+KO)
	fig_Box, axes_Box = plt.subplots(nrows=n_rows, ncols=n_cols, figsize=figsize)
	fig_Box.subplots_adjust(top=0.90)
	fig_Box.suptitle('Maximum intensity of AQP-4 staining\nStandard Score.', fontsize=title_font_size)

	# Old t-test
	#Dataframe for storing statistical data
	#df_box_stats = pd.DataFrame(data=None, index=['statistic', 'pvalue'], columns=regions)

	# List to store the dfs created in the loop
	list_df_box_var_timepoint = list()
	list_df_box_var_genotype = list()
	list_df_box_normal = list()

	list_df_box_anova_stats = list()
	list_df_box_anova_data = list()

	for ax, region in zip(axes_Box.flatten(), regions):
		df_box_master[region].boxplot(ax=ax) #TODO is this the correct data ? check with the raw numbers
		ax.set(title=region, xlabel='Time point and genotype', ylabel=('Intensity (STD)'))

		# Statistical analysis
		if verbose > 0: print('\n\tPerforming statistical analysis on the region : ' + region)

		import pingouin as pg

		#TODO Test if the groups are normally distributed.
		# pingouin.homoscedasticity(data, dv=None, group=None, method='levene', alpha=0.05)
		# pg.normality(data, method='normaltest', alpha=0.05).round(3)
		# when the groups have unequal variances, it is best to use the Welch ANOVA (pingouin.welch_anova())

		# Reshape the dataframe to remove the multi level column names
		df_box_anova = df_box_master[region].stack(level=[0,1]).reset_index(level=['timepoint', 'genotype']).rename(columns={0: "intensity"})
		list_df_box_anova_data.append(df_box_anova)

		# Test for equal variance
		df_box_var_timepoint = pg.homoscedasticity(df_box_anova, dv='intensity', group='timepoint', method='levene', alpha=0.05)
		df_box_var_genotype = pg.homoscedasticity(df_box_anova, dv='intensity', group='genotype', method='levene', alpha=0.05)
		if verbose > 0: print('\t\tTimepoint :\n', df_box_var_timepoint, '\n')
		if verbose > 0: print('\t\tGenotype :\n', df_box_var_genotype)

		list_df_box_var_timepoint.append(df_box_var_timepoint)
		list_df_box_var_genotype.append(df_box_var_genotype)

		# Test for normality
		if df_box_master[region].count().min() > 7:
			df_box_normal = pg.normality(df_box_master[region], method='normaltest', alpha=0.05) # Needs >8 values
			if verbose > 0: print('\t\tNormality test :\n', df_box_normal)
			list_df_box_normal.append(df_box_normal)

		# Print warining if the data does not have equal varinance or if not normal
		if not df_box_var_timepoint['equal_var'].all():
			if verbose > 0: print('\n\t\t########################################################\\n\t\tWARNING : ', region, ' data between timepoints does not have equal variance. ANOVA is not accurate !\n', df_box_var_timepoint, '\n\t\t########################################################\n' )
			#ax.set(title=region + '\nANOVA is not accurate :\ndata between timepoints does not have equal variance', xlabel='Time point and genotype', ylabel=('Intensity (STD)'))
		
		if not df_box_var_genotype['equal_var'].all():
			if verbose > 0: print('\n\t\t########################################################\n\t\tWARNING : ', region, ' data between genotypes does not have equal variance. ANOVA is not accurate !\n', df_box_var_genotype, '\n\t\t########################################################\n' )

		if not df_box_normal['normal'].all():
			if verbose > 0: print('\n\t\t########################################################\n\t\tWARNING : ', region, ' data is not normally distributed. ANOVA is not accurate !\n', df_box_normal, '\n\t\t########################################################\n' )
			ax.set(title=region + '\nANOVA not accurate, data not normally distributed', xlabel='Time point and genotype', ylabel=('Intensity (STD)'))

		# Perform the two-way ANOVA
		#TODO Is a Welch ANOVA better ?
		df_box_anova_stats = df_box_anova.anova(dv='intensity', between=['timepoint', 'genotype'], ss_type=2, detailed=True, effsize='np2')
		list_df_box_anova_stats.append(df_box_anova_stats)

		# Annotate the boxplots
		#height = np.max(df_box_master[region].max(axis=1))*np.ones(len(regions))
		#bars = np.arange(len(regions))
		#barplot_annotate_brackets(1, 2, region_stats.pvalue, bars, height, ax)

		# OLD t-test
		# region_stats = stats.ttest_ind(df_box_ZT6[region, genotypes['CO']].dropna(), df_box_ZT6[region, genotypes['KO']].dropna(), axis=0, equal_var=False, nan_policy='raise', alternative='greater')
		# df_box_stats.loc['statistic', region] = region_stats.statistic
		# df_box_stats.loc['pvalue', region] = region_stats.pvalue
		# print(region_stats) #TODO Make sure the stats and pvalue are the right way around
	

	plt.savefig(path_box + 'df_box_master.pdf')
	plt.close()

	if verbose > 0: print('\nSaved Box plot with standard scores as', path_box + 'df_box_master.pdf\n')

	# Concat the data from the equal variance tests :
	df_box_var_timepoint = pd.concat(list_df_box_var_timepoint, keys=regions, axis=1)
	df_box_var_genotype = pd.concat(list_df_box_var_genotype, keys=regions, axis=1)
	df_box_var = pd.concat([df_box_var_timepoint,df_box_var_genotype], keys=['timepoint', 'genotype'])

	# Concat the data from the normailty tests :
	df_box_normal = pd.concat(list_df_box_normal, keys=regions)

	# Concat the data from the ANOVA tests :
	df_box_anova_data = pd.concat(list_df_box_anova_data, keys=regions, axis=0)
	df_box_anova_stats = pd.concat(list_df_box_anova_stats, keys=regions)

	# Save the data
	if verbose > 0: print('\nSaving Box plot data and stats to', path_box_stats, '\n')
	if write_excel : df_box_var.to_excel(path_box_stats + 'df_box_var_stats.xlsx')
	if write_excel : df_box_normal.to_excel(path_box_stats + 'df_box_normal_stats.xlsx')
	if write_excel : df_box_anova_stats.to_excel(path_box_stats + 'df_box_anova_stats.xlsx')
	if write_excel : df_box_anova_data.to_excel(path_box_stats + 'df_box_anova_data.xlsx')

	if tex : df_box_var.to_latex(buf=path_box_stats+'df_box_var.tex', header=True , index=True , na_rep='--', float_format="%.4f", index_names=True , bold_rows=True , longtable=True , escape=False ,multicolumn=True , multicolumn_format='c', caption='Equal variance test done one the data for the ANOVA.', label='tab:ANOVA_eq_var', position='H')
	if tex : df_box_normal.to_latex(buf=path_box_stats+'df_box_normal.tex', header=True , index=True , na_rep='--', float_format="%.4f", index_names=True , bold_rows=True , longtable=True , escape=False ,multicolumn=True , multicolumn_format='c', caption='Normality test done one the data for the ANOVA.', label='tab:ANOVA_normal', position='H')
	if tex : df_box_anova_stats.to_latex(buf=path_box_stats+'df_box_anova_stats.tex', header=True , index=True , na_rep='--', float_format="%.4f", index_names=True , bold_rows=True , longtable=True , escape=False ,multicolumn=True , multicolumn_format='c', caption='Resulsts of the ANOVA, separated by region.', label='tab:ANOVA_stats', position='H')
	if tex : df_box_anova_data.to_latex(buf=path_box_stats+'df_box_anova_data.tex', header=True , index=True , na_rep='--', float_format="%.4f", index_names=True , bold_rows=True , longtable=True , escape=False ,multicolumn=True , multicolumn_format='c', caption='Data used for the ANOVA', label='tab:ANOVA_data', position='H')


	if verbose > 0: toc()
	if verbose > 0: print("##############################################\n")

	# Print the results
	if verbose > 0: print('Results from the two-way ANOVA on the data :\n\n', df_box_anova_stats)
	if verbose > 0: print("\n'Source': Factor names\n'SS': Sums of squares\n'DF': Degrees of freedom\n'MS': Mean squares\n'F': F-values\n'p-unc': uncorrected p-values\n'np2': Partial eta-square effect sizes")
	if verbose > 0: print("\n##############################################\n")

	return(0)

def make_boxplots_long (df, regions, verbose, path, write_excel, tex):
	'''
	Takes the dataframe output from make_std_long and makes 
	a boxplot comparing the sexs at each region in regions
	Uses the function barplot_annotate_brackets
	It makes plottin easier :
	df.groupby('region').boxplot(column='intensity', by=['genotype', 'sex'], figsize=(15,15))
	but you have no control to annotate each subplot seperatly since there is no loop
	'''

	# pip install SciencePlots
	import pandas as pd
	import matplotlib.pyplot as plt
	import numpy as np
	from scipy import stats
	import seaborn as sns

	if verbose > 0: tic()
	if verbose > 0: print("##############################################\n")
	if verbose > 0: print("Making box plots to compare sexes :")

	# Figure parameters
	n_rows = 2
	n_cols = 2
	figsize = (10,8)
	title_font_size = 20
	plt.style.use(['science','grid'])
	plt.tight_layout(pad=0.5)

	# New directory to save the Boxplot data and plots
	new_dir = path+'Long'+'\\'
	try:
		os.makedirs(new_dir)
	except OSError:
		if verbose > 0: print ('Failed to make directory :', new_dir, ' to store the Boxplots. It may already exist\n')
	else:
		if verbose > 0: print('Made directory :', new_dir, ' to store the BoxPlots\n')
	
	path_box = path+'Long'+'\\'

	# Make violin plots with all the data
	fig_violin, axes_violin = plt.subplots(nrows=1, ncols=1, figsize=(6,6))
	# fig_violin.subplots_adjust(hspace=1)
	fig_violin.suptitle('Maximum intensity of AQP-4 staining\nStandard Score.', fontsize=title_font_size)

	axes_violin = sns.violinplot(data=df, x='genotype', hue='timepoint', y='intensity', split=True, inner='quartile', palette=({'ZT18':'r', 'ZT6':'g'})) #, figsize=(10,10))

	plt.savefig(path_box + 'ViolinPlot.pdf')
	plt.close()

	# # This unfortunatly doesnt work "groupby"
	# # Violin separated by region
	# fig_violin_region, axes_violin_region = plt.subplots(nrows=1, ncols=1, figsize=(6,6))
	# # fig_violin.subplots_adjust(hspace=1)
	# fig_violin.suptitle('Maximum intensity of AQP-4 staining\nStandard Score.', fontsize=title_font_size)

	# axes_violin_region = sns.violinplot(data=df.groupby('region'), x='genotype', hue='timepoint', y='intensity', split=True, inner='quartile', palette=({'ZT18':'r', 'ZT6':'g'})) #, figsize=(10,10))

	# plt.savefig(path_box + 'ViolinPlot_regions.pdf')
	# plt.close() 

	# # Set the region column as an index to be able to select data by region
	# df.set_index(keys='region', append=True,  inplace=True)

	# # One subplot comparing sex per region
	# fig_Box_sex, axes_Box_sex = plt.subplots(nrows=n_rows, ncols=n_cols, figsize=figsize)
	# fig_Box_sex.subplots_adjust(top=0.90)
	# fig_Box_sex.suptitle('Maximum intensity of AQP-4 staining\nStandard Score.', fontsize=title_font_size)

	# # Old t-test
	# #Dataframe for storing statistical data
	# df_box_sex_stats = pd.DataFrame(data=None, index=['statistic', 'pvalue'], columns=regions)

	# for ax, region in zip(axes_Box_sex.flatten(), regions):
	# 	df.T.swaplevel(axis=1)[region].T.boxplot(column=['intensity'], by=['genotype', 'sex'], ax=ax) #TODO is this the correct data ? check with the raw numbers
	# 	ax.set(title=region, xlabel='Sex', ylabel=('Intensity (STD)'))

	# 	# Statistical analysis
	# 	if verbose > 0: print('\n\tPerforming statistical analysis on the region : ' + region)

	# 	# t-test
	# 	# Get the correct columns
	# 	df_m = df.T.swaplevel(axis=1)[region].T.set_index('sex', append=True).T.swaplevel(axis=1)['m'].T['intensity']
	# 	df_f = df.T.swaplevel(axis=1)[region].T.set_index('sex', append=True).T.swaplevel(axis=1)['f'].T['intensity']

	# 	from scipy import stats
	# 	region_stats = stats.ttest_ind(df_m.dropna(), df_f.dropna(), axis=0, equal_var=False, nan_policy='raise', alternative='two-sided')
	# 	df_box_sex_stats.loc['statistic', region] = region_stats.statistic
	# 	df_box_sex_stats.loc['pvalue', region] = region_stats.pvalue
	# 	if verbose : print('\t',region_stats, '\n') #TODO Make sure the stats and pvalue are the right way around

	# 	# Annotate the boxplots
	# 	height = np.max(df.T.swaplevel(axis=1)[region].T['intensity'].max())*np.ones(len(regions))
	# 	bars = np.arange(len(regions))
	# 	barplot_annotate_brackets(1, 2, region_stats.pvalue, bars, height, ax)

	# fig_Box_sex.suptitle('Maximum intensity of AQP-4 staining\nStandard Score.', fontsize=title_font_size)
	# plt.savefig(path_box + 'Box_Plot_Sex.pdf')
	# plt.close()

	sex_dir = path_box+'Sex'+'\\'
	try:
		os.makedirs(sex_dir)
	except OSError:
		if verbose > 0: print ('Failed to make directory :', sex_dir, ' to store the Boxplots. It may already exist\n')
	else:
		if verbose > 0: print('Made directory :', sex_dir, ' to store the BoxPlots\n')
	
	path_sex = sex_dir

	#Dataframe for storing statistical data
	df_box_sex_stats = pd.DataFrame(data=None, index=['statistic', 'pvalue'], columns=regions)

	for region in regions:
		# Iterate through the regions
		df_sex = df[df['region'] == region]    

		# Group the data to your liking
		grouped = df_sex.groupby('genotype')

		# Figure out number of rows needed for 2 column grid plot
		# Also accounts for odd number of plots
		import math
		nrows = int(math.ceil(len(grouped)/2.))

		#Setup Subplots
		fig, axs = plt.subplots(nrows,2, figsize=(10,5))
		
		for (name, df_sex), ax in zip(grouped, axs.flat):
			# t-test
			# Get the correct columns
			df_m = df_sex.set_index('sex', append=True).T.swaplevel(axis=1)['m'].T['intensity']
			df_f = df_sex.set_index('sex', append=True).T.swaplevel(axis=1)['f'].T['intensity']

			from scipy import stats
			region_stats = stats.ttest_ind(df_m.dropna(), df_f.dropna(), axis=0, equal_var=False, nan_policy='raise', alternative='two-sided')
			df_box_sex_stats.loc['statistic', region] = region_stats.statistic
			df_box_sex_stats.loc['pvalue', region] = region_stats.pvalue

			# Plot
			df_sex.boxplot(column=['intensity'], by=['genotype', 'sex'], ax=ax)

			# Annotate the boxplots
			height = np.max(df['intensity'].max())*np.ones(len(regions))
			bars = np.arange(len(regions))
			barplot_annotate_brackets(1, 2, region_stats.pvalue, bars, height, ax)

			# Subplot title
			ax.set_title(region)
			ax.set_ylabel('Intensity (STD)')

		plt.savefig(path_sex+'Sex_'+region+'.pdf')

	df_box_sex_stats
    

	if verbose > 0: print('\n\tSaved Box plot with standard scores as', path_sex+'Sex_'+region+'.pdf\n')

	if tex : df_box_sex_stats.to_latex(buf=path_sex+'df_box_sex_stats.tex', header=True , index=True , na_rep='--', index_names=True , bold_rows=True , longtable=True , escape=False ,multicolumn=True , multicolumn_format='c', caption='Results of the t-test done between the sexes.', label='tab:sex_stats', position='H')

	if write_excel : df_box_sex_stats.to_excel(path_sex + 'df_box_sex_stats_data.xlsx')

	# # One subplot per region with violin plots this time
	# fig_violin_region, axes_violin_region = plt.subplots(nrows=n_rows, ncols=n_cols, figsize=figsize)
	# fig_violin_region.subplots_adjust(top=0.90)
	# fig_violin_region.suptitle('Maximum intensity of AQP-4 staining\nStandard Score.', fontsize=title_font_size)

	# for ax, region in zip(axes_violin_region.flatten(), regions):
	# 	ax = sns.violinplot(data=df.T.swaplevel(axis=1)[region].T, x='genotype', hue='timepoint', y='intensity', split=True, inner='quartile', palette=({'ZT18':'r', 'ZT6':'g'}))
	# 	# ax.set(title=region, xlabel='Sex', ylabel=('Intensity (STD)'))

	# fig_violin_region.suptitle('Maximum intensity of AQP-4 staining\nStandard Score.', fontsize=title_font_size)
	# plt.savefig(path_box + 'Violin_regions.pdf')
	# plt.close()

	if verbose > 0: toc()
	if verbose > 0: print("##############################################\n")

	return 0

########################################################

def main():
	"""Make plots from excel files in directory."""

	# Parse arguments
	args = parseArgs()

	# Convert object elements to standard variables for functions
	path = args.path + '\\' # Useful when coping path from win explorer
	regions = args.regions 
	verbose = args.verbose
	genotypes = args.genotypes
	sex = args.sex
	write_excel = args.excel
	tex = args.tex

	if verbose > 0: tic()
	if verbose > 0: print("\n\n##############################################\n")

	# Make directory to save results
	new_dir = path+'Data_and_Plots'+'\\'
	try:
		os.makedirs(new_dir)
	except OSError:
		if verbose > 0: print ('Failed to make directory :', new_dir, ' to store the results. It may already exist\n')
	else:
		if verbose > 0: print('Made directory :', new_dir, ' to store the results\n')
	
	# Start calling functions to do the heavy lifting

	df_raw = make_big_DataFrame(path, verbose)
	if verbose > 0 and write_excel > 0: print('Saving raw data\n')
	if write_excel : df_raw.to_excel(new_dir+'Raw_data.xlsx')

	# Merge with bins
	df_merged_bins = merge_on_distance(df_raw, verbose, bins=True)
	if verbose and write_excel > 0: print('Saving merged data\n')
	if write_excel : df_merged_bins.to_excel(new_dir+'Merged_bins.xlsx')

	# Merge without bins
	df_merged_no_bins = merge_on_distance(df_raw, verbose, bins=False)
	if verbose and write_excel > 0: print('Saving merged data\n')
	if write_excel : df_merged_no_bins.to_excel(new_dir+'Merged_no_bins.xlsx')

	df_std_long = make_std_long(df_merged_no_bins, verbose, new_dir, write_excel, tex)

	for genotype in genotypes:
		if verbose : print('\n\n\n#############################',genotype)
		make_plot(df_merged_bins, sex, genotype, regions, verbose, new_dir, write_excel)
	#make_plot(df_merged, sex, genotypes, regions, verbose, new_dir, write_excel)

	# New directory to save the Boxplot data and plots
	box_dir = new_dir+'BoxPlots'+'\\'
	try:
		os.makedirs(new_dir)
	except OSError:
		if verbose > 0: print ('Failed to make directory :', box_dir, ' to store the Boxplots. It may already exist\n')
	else:
		if verbose > 0: print('Made directory :', box_dir, ' to store the BoxPlots\n')

	make_boxplots(df_merged_no_bins, sex, regions, verbose, box_dir, write_excel, tex)

	make_boxplots_long(df_std_long, regions, verbose, box_dir, write_excel, tex)

	
if __name__ == '__main__':
	import time
	start_time = time.time()
	main()
	print("\nTotal running time: {:.3f} seconds.".format(time.time() - start_time))