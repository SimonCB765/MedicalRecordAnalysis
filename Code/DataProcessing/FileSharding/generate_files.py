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
        columnsToIgnore = list(columnsToIgnore)

        # Fill up each output file sequentially. The data from the large file will therefore still be sequential in
        # each smaller file.
        datapointsAdded = 0  # The number of datapoints added to the currently open file.
        currentFileNumber = 0  # The number of the current file having data added to it.
        fileCurrentShard = os.path.join(dirOutput, "Shard_{:d}.txt".format(currentFileNumber))  # Name of shard file.
        fidShard = tf.python_io.TFRecordWriter(fileCurrentShard)  # The TFRecord writer.
        for line in fidDataset:
            # Process the line.
            line = (line.strip()).split(separator)

            # If the current sharded file has been filled up open another file.
            if datapointsAdded == datapointsPerFile:
                fidShard.close()
                datapointsAdded = 0
                currentFileNumber += 1
                fileCurrentShard = os.path.join(dirOutput, "Shard_{:d}.txt".format(currentFileNumber))
                fidShard = tf.python_io.TFRecordWriter(fileCurrentShard)

            # Write the data on the line out to the shard file. This involves packing the data in an Example protocol
            # buffer, serialising it and then writing it out.
            if isDataSequence:
                # The data is sequence data.
                pass
            else:
                # The data is not sequence data, so just read it into a numpy array and remove the columns that aren't
                # needed.
                data = np.asarray(line, dtype=np.float)
                mask = np.ones_like(data, dtype=np.bool)
                mask[columnsToIgnore] = False
                data = data[mask]

                # Create the Example protocol buffer
                # (https://github.com/tensorflow/tensorflow/blob/master/tensorflow/core/example/example.proto).
                example = tf.train.Example(
                    # The Example protocol buffer contains a Features protocol buffer
                    # (https://github.com/tensorflow/tensorflow/blob/master/tensorflow/core/example/feature.proto).
                    features=tf.train.Features(
                        # The Features protocol buffer contains a list of features, which are one of either a
                        # bytes_list, float_list or int64_list.
                        feature={
                            "data": _float_feature(data)
                        }
                    )
                )
                fidShard.write(example.SerializeToString())
            datapointsAdded += 1

        fidShard.close()  # Close the final sharded file.


def _bytes_feature(value):
    return tf.train.Feature(bytes_list=tf.train.BytesList(value=value))


def _float_feature(value):
    return tf.train.Feature(float_list=tf.train.FloatList(value=value))


def _int64_feature(value):
    return tf.train.Feature(int64_list=tf.train.Int64List(value=value))
