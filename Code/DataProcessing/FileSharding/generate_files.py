"""Function to shard a large dataset file into multiple smaller ones."""

# Python imports.
import os

# 3rd party imports.
import numpy as np
import tensorflow as tf


def main(fileDataset, dirOutput, fileIgnoreColumns=None, datapointsPerFile=1000, isDataSequence=False, separator='\t',
         isIDColumnPresent=True):
    """Turn a file containing an entire dataset into multiple smaller files containing non-overlapping subsets of it.

    :param fileDataset:         The location of the large dataset containing all datapoints.
    :type fileDataset:          str
    :param dirOutput:           The location of the directory in which to write the smaller files.
    :type dirOutput:            str
    :param fileIgnoreColumns:   The location of the file containing the headers of the columns to ignore.
    :type fileIgnoreColumns:    str
    :param datapointsPerFile:   The number of datapoints or sequences to put in each file.
    :type datapointsPerFile:    int
    :param isDataSequence:      Whether the dataset contains sequence data.
    :type isDataSequence:       bool
    :param separator:           The separator used to split the columns in the file.
    :type separator:            str
    :param isIDColumnPresent:   Whether the first column contains the IDs of the datapoints.
    :type isIDColumnPresent:    bool

    """

    # Extract the list of columns to ignore.
    columnsToIgnore = []
    if fileIgnoreColumns:
        with open(fileIgnoreColumns, 'r') as fidCodes:
            for line in fidCodes:
                columnsToIgnore.append(line.strip())

    # Create the sharded dataset.
    with open(fileDataset, 'r') as fidDataset:
        header = ((fidDataset.readline()).strip()).split(separator)  # Get the data header.

        # Determine the indices of the headers that need to be ignored.
        columnsToIgnore = {j for i, j in enumerate(columnsToIgnore) if i in header}
        if isIDColumnPresent and not isDataSequence:
            # Add the first column (that contains the IDs of the datapoints) to the list of columns to ignore when the
            # data is not sequence data.
            columnsToIgnore |= {0}

        # Fill up each output file sequentially. The data from the large file will therefore still be sequential in
        # each small file.
        datapointsAdded = 0  # The number of datapoints added to the currently open file.
        currentFileNumber = 0  # The number of the current file having data added to it.
        fidShard = open(os.path.join(dirOutput, "Shard_{:d}.txt".format(currentFileNumber)), 'w')  # Sharded data file.
        for line in fidDataset:
            # If the current sharded file has been filled up open another file.
            if datapointsAdded == datapointsPerFile:
                fidShard.close()
                datapointsAdded = 0
                currentFileNumber += 1
                fidShard = open(os.path.join(dirOutput, "Shard_{:d}.txt".format(currentFileNumber)), 'w')

            # Write the data on the line out to the shard file.
            if isDataSequence:
                pass
            else:
                pass
            datapointsAdded += 1

        fidShard.close()  # Close the final sharded file.


def _float_feature(value):
    return tf.train.Feature(float_list=tf.train.FloatList(value=[value]))


def _int64_feature(value):
    return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))
