"""Function to generate the files that will contain the datasets."""

# Python imports.
import os


def main(dirOutput, uniqueCodes, codeAssociatedValues):
    """Generate the names of the cleaned dataset files to be generated.

    The intended contents of the files can be found in the README.

    :param dirOutput:               Location of the directory containing the dataset files.
    :type dirOutput:                str
    :param uniqueCodes:             The codes that appear associated with a patient in the dataset.
    :type uniqueCodes:              list
    :param codeAssociatedValues:    A record of whether each code has value 1 or value 2 values associated with it.
    :type codeAssociatedValues:     dict[str,dict[str,bool]]
    :return:                        The locations of the cleaned dataset files.
    :rtype:                     dict

    """

    outputFiles = {
        "CodeCount": {
            "History": os.path.join(dirOutput, "CodeCount_History.tsv"),
            "Visits_NC": os.path.join(dirOutput, "CodeCount_Visits_NC.tsv"),
            "Visits_C": os.path.join(dirOutput, "CodeCount_Visits_C.tsv"),
            "Years_NC": os.path.join(dirOutput, "CodeCount_Years_NC.tsv"),
            "Years_C": os.path.join(dirOutput, "CodeCount_Years_C.tsv")
        },
        "BinaryIndicator": {
            "History": os.path.join(dirOutput, "BinaryIndicator_History.tsv"),
            "Visits_NC": os.path.join(dirOutput, "BinaryIndicator_Visits_NC.tsv"),
            "Visits_C": os.path.join(dirOutput, "BinaryIndicator_Visits_C.tsv"),
            "Years_NC": os.path.join(dirOutput, "BinaryIndicator_Years_NC.tsv"),
            "Years_C": os.path.join(dirOutput, "BinaryIndicator_Years_C.tsv")
        },
        "RawData": {
            "History": os.path.join(dirOutput, "RawData_History.tsv"),
            "Visits_NC": os.path.join(dirOutput, "RawData_Visits_NC.tsv"),
            "Visits_C": os.path.join(dirOutput, "RawData_Visits_C.tsv"),
            "Years_NC": os.path.join(dirOutput, "RawData_Years_NC.tsv"),
            "Years_C": os.path.join(dirOutput, "RawData_Years_C.tsv")
        }
    }

    # Generate the headers for the files.
    with open(outputFiles["CodeCount"]["History"], 'a') as fidCountHist, \
            open(outputFiles["CodeCount"]["Visits_NC"], 'a') as fidCountVisNC, \
            open(outputFiles["CodeCount"]["Visits_C"], 'a') as fidCountVisC, \
            open(outputFiles["CodeCount"]["Years_NC"], 'a') as fidCountYearNC, \
            open(outputFiles["CodeCount"]["Years_C"], 'a') as fidCountYearC, \
            open(outputFiles["BinaryIndicator"]["History"], 'a') as fidBinHist, \
            open(outputFiles["BinaryIndicator"]["Visits_NC"], 'a') as fidBinVisNC, \
            open(outputFiles["BinaryIndicator"]["Visits_C"], 'a') as fidBinVisC, \
            open(outputFiles["BinaryIndicator"]["Years_NC"], 'a') as fidBinYearNC, \
            open(outputFiles["BinaryIndicator"]["Years_C"], 'a') as fidBinYearC, \
            open(outputFiles["RawData"]["History"], 'a') as fidRawHist, \
            open(outputFiles["RawData"]["Visits_NC"], 'a') as fidRawVisNC, \
            open(outputFiles["RawData"]["Visits_C"], 'a') as fidRawVisC, \
            open(outputFiles["RawData"]["Years_NC"], 'a') as fidRawYearNC, \
            open(outputFiles["RawData"]["Years_C"], 'a') as fidRawYearC:

        # Create the header for the binary indicator and code count datasets.
        codeString = '\t'.join(uniqueCodes)
        header = "PatientID\tAge\tGender\t{0:s}\n".format(codeString)
        fidCountHist.write(header)
        fidCountVisNC.write(header)
        fidCountVisC.write(header)
        fidCountYearNC.write(header)
        fidCountYearC.write(header)
        fidBinHist.write(header)
        fidBinVisNC.write(header)
        fidBinVisC.write(header)
        fidBinYearNC.write(header)
        fidBinYearC.write(header)

        # Create the header for the raw data datasets.
        codeString = ""
        for i in uniqueCodes:
            if codeAssociatedValues[i]["Val1"] and codeAssociatedValues[i]["Val2"]:
                codeString += "\t{0:s}_Val1\t{0:s}_Val2".format(i)
            elif codeAssociatedValues[i]["Val1"]:
                codeString += "\t{:s}_Val1".format(i)
            elif codeAssociatedValues[i]["Val2"]:
                codeString += "\t{:s}_Val2".format(i)
            else:
                codeString += "\t{:s}".format(i)
        codeString = codeString[1:]  # Strip off initial '\t' character.
        header = "PatientID\tAge\tGender\t{0:s}\n".format(codeString)
        fidRawHist.write(header)
        fidRawVisNC.write(header)
        fidRawVisC.write(header)
        fidRawYearNC.write(header)
        fidRawYearC.write(header)

    return outputFiles
