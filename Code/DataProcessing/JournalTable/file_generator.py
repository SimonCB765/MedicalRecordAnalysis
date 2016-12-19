"""Function to generate the files that will contain the datasets."""

# Python imports.
import os


def close_files(fileDict):
    """Close a collection of opened files.

    :param fileDict:    A dictionary containing files to close.
    :type fileDict:     dict

    """

    for i in fileDict:
        for j in fileDict[i]:
            fileDict[i][j].close()


def open_files(dirOutput):
    """Generate the names of the cleaned dataset files to be generated.

    The intended contents of the files can be found in the README.

    :param dirOutput:   Location of the directory containing the dataset files.
    :type dirOutput:    str
    :return:            The cleaned dataset files open for writing.
    :rtype:             dict

    """

    # Create the file names.
    outputFids = {
        "BinaryIndicator": {
            "History": open(os.path.join(dirOutput, "BinaryIndicator_History.tsv"), 'w'),
            "Visits": open(os.path.join(dirOutput, "BinaryIndicator_Visits.tsv"), 'w'),
            "Years": open(os.path.join(dirOutput, "BinaryIndicator_Years.tsv"), 'w')
        },
        "CodeCount": {
            "History": open(os.path.join(dirOutput, "CodeCount_History.tsv"), 'w'),
            "Visits": open(os.path.join(dirOutput, "CodeCount_Visits.tsv"), 'w'),
            "Years": open(os.path.join(dirOutput, "CodeCount_Years.tsv"), 'w')
        },
        "RawData": {
            "History": open(os.path.join(dirOutput, "RawData_History.tsv"), 'w'),
            "Visits": open(os.path.join(dirOutput, "RawData_Visits.tsv"), 'w'),
            "Years": open(os.path.join(dirOutput, "RawData_Years.tsv"), 'w')
        }
    }

    # Create the file handles.
    header = "PatientID\tAge\tGender\tNumberOfCodes\tCodeRecords\n"
    for i in outputFids:
        for j in outputFids[i]:
            outputFids[i][j].write(header)

    return outputFids
