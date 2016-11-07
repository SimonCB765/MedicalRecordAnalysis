"""Function to shard a large dataset file into multiple smaller ones."""


def main(fileDataset, dirOutput, fileIgnoreColumns, datapointsPerFile, isDataSequence):
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

    """

    pass
