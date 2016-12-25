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


def open_files(dirOutput, variablesUsed):
    """Generate the names of the cleaned dataset files to be generated.

    The intended contents of the files can be found in the README.

    :param dirOutput:       Location of the directory containing the dataset files.
    :type dirOutput:        str
    :param variablesUsed:   The codes used as variables in the dataset (plus the ID, age and gender).
    :type variablesUsed:    set
    :return:                The cleaned dataset files open for writing.
    :rtype:                 dict

    """

    # Create the file names.
    outputFileIDs = {
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

    # Write the header.
    header = "{:s}\n".format("\t".join(variablesUsed))
    for i in outputFileIDs:
        for j in outputFileIDs[i]:
            outputFileIDs[i][j].write(header)

    return outputFileIDs
