#!/homes/dsuveges/anaconda3/bin/python

# load virtual env... just the usual
import pandas as pd
import argparse

# we don't want to get warnings. It works.
pd.options.mode.chained_assignment = None 

# Function to find and annotate top association:
def find_top_association(chrom):
    global input_df
    global window

    test_df = input_df.loc[input_df.chromosome == chrom]
    test_df.loc[:,'pvalue'] = test_df['pvalue'].astype(float) # changing type of p-value column
    test_df.loc[:,'bp_location'] = test_df['bp_location'].astype(float) # changing type of position column

    # sorting rows by p-value:
    for index in test_df.sort_values(['pvalue']).index:
        
        # Check if the index has 'false' or 'review' flag:
        if test_df.loc[index]['isTopAssociation'] == 'false' or \
            test_df.loc[index]['isTopAssociation'] == 'REQUIRES REVIEW':
            continue
        # Excluding sub significant variants.
        elif test_df.loc[index]['pvalue'] > 1.0e-5:
            test_df.loc[index, 'isTopAssociation'] = 'false'
            continue
        # We have found a top snp!
        else:
            pos = test_df.loc[index]['bp_location']
            # Setting false flag for ALL variants within the window.
            test_df.loc[test_df[abs( test_df.bp_location - pos ) <= window].index,'isTopAssociation'] = 'false'
            
            # If there are multiple variants with the same p-value, request review, othervise it's a true peak.
            if len(test_df.loc[test_df['pvalue'] == test_df.loc[index]['pvalue']].chromosome) > 1:
                test_df.loc[ test_df['pvalue'] == test_df.loc[index]['pvalue'], 'isTopAssociation'] = 'REQUIRES REVIEW'
            else:
                test_df.loc[ test_df['pvalue'] == test_df.loc[index]['pvalue'], 'isTopAssociation'] = 'true'

    # Modifying the original dataframe: 
    input_df.loc[ test_df.index, 'isTopAssociation'] = test_df.isTopAssociation

if __name__ == '__main__':

    # Parsing commandline arguments
    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser(description='This script finds the most significant association within a defined range (100kbp by default).')

    parser.add_argument('-f', '--input', help='Input file name with table of associations.')
    parser.add_argument('-o', '--output', help='Output file name.')
    parser.add_argument('-w', '--window', default=100000, help='Window size.', type = int)

    args = parser.parse_args()

    inputFile = args.input
    outputFile = args.output
    window = args.window

    # Reading input file into pandas dataframe:
    input_df = pd.read_csv(inputFile, sep="\t", dtype = str)
    
    # Checking header:
    if not pd.Series(['RS_ID', 'pvalue', 'chromosome', 'bp_location']).isin(input_df.columns).all():
        raise Exception('[Error] Not all required columns were found in the file header. Required columns: "RS_ID", "pvalue", "chromosome", "bp_location"')

    input_df['isTopAssociation'] = ''

    # finding peaks for each chromosome
    for chromosme in input_df.chromosome.unique():
        find_top_association(chromosme)

    # Saving the modified table into a tab separated file:
    input_df.to_csv(outputFile, sep="\t", index= False)