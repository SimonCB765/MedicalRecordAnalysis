"""Generate datasets from SQL dump files."""

# Python imports.
from collections import defaultdict
import logging
import operator
import os
import re
import sys

# Globals.
LOGGER = logging.getLogger(__name__)
if sys.version_info[0] >= 3:
    iteritems = operator.methodcaller("items")
else:
    iteritems = operator.methodcaller("iteritems")


def main(dirProcessedData, dirOutput, config):
    """Generate flat file datasets by processing a set of pre-processed journal table files.

    Patient history data is assumed to be stored in a file called JournalTable.tsv. Within this
    file a patient's history is assumed to be recorded consecutively (i.e. a patient has all their records recorded
    one after the other with no other patient's records in between).

    :param dirProcessedData:    The location of the directory containing the processed journal table files.
    :type dirProcessedData:     str
    :param dirOutput:           The location of the directory where the flat files should be saved.
    :type dirOutput:            str
    :param config:              The object containing the configuration parameters for the flat file generation.
    :type config:               JsonschemaManipulation.Configuration

    """

    # Get the files for the SQL tables we're interested in. These would be the journal table and the patient table.
    isError = False
    fileJournalTable = os.path.join(dirProcessedData, "JournalTable.tsv")
    if not os.path.isfile(fileJournalTable):
        LOGGER.error("There is no JournalTable.tsv file in the input directory ({:s}).".format(fileJournalTable))
        isError = True
    filePatientData = os.path.join(dirProcessedData, "PatientDemographics.tsv")
    if not os.path.isfile(filePatientData):
        LOGGER.error("There is no PatientDemographics.tsv file in the input directory ({:s}).".format(filePatientData))
        isError = True
    fileCodes = os.path.join(dirProcessedData, "Codes.txt")
    if not os.path.isfile(fileCodes):
        LOGGER.error("There is no Codes.txt file in the input directory ({:s}).".format(fileCodes))
        isError = True
    if isError:
        print("\nErrors were found while attempting to access the input files during flat file generation.\n")
        sys.exit()

    LOGGER.info("Starting journal table dataset generation.")

    # Extract the patient demographics and determine which patients should be used.
    patientData = {}
    patientsToIgnore = config.get_param(["DataProcessing", "PatientsToIgnore"])[1]
    patientsToIgnore = re.compile('|'.join(patientsToIgnore)) if patientsToIgnore else re.compile("a^")
    patientsToKeep = config.get_param(["DataProcessing", "PatientsToKeep"])[1]
    patientsToKeep = re.compile('|'.join(patientsToKeep)) if patientsToKeep else re.compile("")
    with open(filePatientData, 'r') as fidPatientData:
        _ = fidPatientData.readline()  # Strip the header.
        for line in fidPatientData:
            chunks = (line.strip()).split('\t')
            patientID = chunks[0]
            yearOfBirth = int(chunks[1][:4])
            patientGender = chunks[2]
            if patientsToKeep.match(patientID) and (not patientsToIgnore.match(patientID)):
                patientData[patientID] = {"YearOfBirth": yearOfBirth, "Gender": patientGender}

    # Extract the list of codes in the dataset and determine which ones should be used.
    uniqueCodes = []
    codeAssociatedValues = {}
    codesToIgnore = config.get_param(["DataProcessing", "CodesToIgnore"])[1]
    codesToIgnore = re.compile('|'.join(codesToIgnore)) if codesToIgnore else re.compile("a^")
    codesToKeep = config.get_param(["DataProcessing", "CodesToKeep"])[1]
    codesToKeep = re.compile('|'.join(codesToKeep)) if codesToKeep else re.compile("")
    with open(fileCodes, 'r') as fidCodes:
        _ = fidCodes.readline()  # Strip the header.
        for line in fidCodes:
            chunks = (line.strip()).split('\t')
            code = chunks[0]
            if codesToKeep.match(code) and (not codesToIgnore.match(code)):
                uniqueCodes.append(code)
                codeAssociatedValues[code] = {"Val1": bool(int(chunks[1])), "Val2": bool(int(chunks[2]))}

    # Generate a mapping of codes to their index in the code list.
    codeIndexMap = {j: i for i, j in enumerate(uniqueCodes)}

    # Extract the information about each patient's history.
    LOGGER.info("Now generating patient histories.")
    with open(os.path.join(dirOutput, "CodeCount_History.tsv"), 'w') as fidCountHist, \
            open(os.path.join(dirOutput, "CodeCount_Visits_NC.tsv"), 'w') as fidCountVisNC, \
            open(os.path.join(dirOutput, "CodeCount_Visits_C.tsv"), 'w') as fidCountVisC, \
            open(os.path.join(dirOutput, "CodeCount_Years_NC.tsv"), 'w') as fidCountYearNC, \
            open(os.path.join(dirOutput, "CodeCount_Years_C.tsv"), 'w') as fidCountYearC, \
            open(os.path.join(dirOutput, "BinaryIndicator_History.tsv"), 'w') as fidBinHist, \
            open(os.path.join(dirOutput, "BinaryIndicator_Visits_NC.tsv"), 'w') as fidBinVisNC, \
            open(os.path.join(dirOutput, "BinaryIndicator_Visits_C.tsv"), 'w') as fidBinVisC, \
            open(os.path.join(dirOutput, "BinaryIndicator_Years_NC.tsv"), 'w') as fidBinYearNC, \
            open(os.path.join(dirOutput, "BinaryIndicator_Years_C.tsv"), 'w') as fidBinYearC, \
            open(os.path.join(dirOutput, "RawData_History.tsv"), 'w') as fidRawHist, \
            open(os.path.join(dirOutput, "RawData_Visits_NC.tsv"), 'w') as fidRawVisNC, \
            open(os.path.join(dirOutput, "RawData_Visits_C.tsv"), 'w') as fidRawVisC, \
            open(os.path.join(dirOutput, "RawData_Years_NC.tsv"), 'w') as fidRawYearNC, \
            open(os.path.join(dirOutput, "RawData_Years_C.tsv"), 'w') as fidRawYearC:
        # Create the header for the binary indicator and code count datasets.
        codeString = '\t'.join(uniqueCodes)
        header = "PatientID\tAge\tGender\t{:s}\n".format(codeString)
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
        header = "PatientID\tAge\tGender\t{:s}\n".format(codeString)
        fidRawHist.write(header)
        fidRawVisNC.write(header)
        fidRawVisC.write(header)
        fidRawYearNC.write(header)
        fidRawYearC.write(header)

        # Start extracting the patient histories.
        patientsSaved = 0
        currentPatient = None  # The ID of the patient who's record is currently being built.
        currentVisit = 0  # The current patient's current visit number.
        currentYear = None  # The current patient's current year.
        binaryHistory, countHistory, rawHistory = _init_histories(len(uniqueCodes))
        with open(fileJournalTable, 'r') as fidJournalTable:
            _ = fidJournalTable.readline()  # Strip the header.
            for line in fidJournalTable:
                chunks = (line.strip()).split('\t')
                patientID = chunks[0]
                code = chunks[1]
                year = int(chunks[3])
                visitNumber = int(chunks[4])
                value1 = float(chunks[5])
                value2 = float(chunks[6])

                if patientsSaved > 1000:
                    break

                # Only record information about patients we're interested in.
                if patientID in patientData:
                    if (patientID != currentPatient) and (currentPatient is not None):
                        # A new patient has been found and this is not the first line of the file, so record the old
                        # patient and reset the patient data for the new patient.

                        # Output an update.
                        patientGender = patientData[currentPatient]["Gender"]
                        patientsSaved += 1
                        if patientsSaved % 100 == 0:
                            LOGGER.info("Saved {:d} patients ({:.2f}%).".format(
                                patientsSaved, (patientsSaved / len(patientData)) * 100
                            ))

                        # Output the patient's information.
                        _write_entire_history(
                            binaryHistory, currentPatient, patientGender, fidBinHist, fidBinVisNC,
                            fidBinVisC, fidBinYearNC, fidBinYearC
                        )
                        _write_entire_history(
                            countHistory, currentPatient, patientGender, fidCountHist, fidCountVisNC,
                            fidCountVisC, fidCountYearNC, fidCountYearC
                        )
                        binaryHistory, countHistory, rawHistory = _init_histories(len(uniqueCodes))

                    # Update the information about the patient currently having their history collected.
                    currentPatient = patientID
                    currentVisit = visitNumber
                    currentYear = year
                    patientAge = currentYear - patientData[currentPatient]["YearOfBirth"]

                    # Update entire history vectors.
                    for i, j in iteritems(binaryHistory):
                        if i == "Entire":
                            j[0] = patientAge
                            j[1][codeIndexMap[code]] = '1'
                        elif i.startswith("Year"):
                            j[currentYear][0] = patientAge
                            j[currentYear][1][codeIndexMap[code]] = '1'
                        else:
                            j[currentVisit][0] = patientAge
                            j[currentVisit][1][codeIndexMap[code]] = '1'

                    # Update count history vectors.
                    for i, j in iteritems(countHistory):
                        if i == "Entire":
                            j[0] = patientAge
                            j[1][codeIndexMap[code]] = str(max(int(j[1][codeIndexMap[code]]) + 1, 1))
                        elif i.startswith("Year"):
                            j[currentYear][0] = patientAge
                            j[currentYear][1][codeIndexMap[code]] = \
                                str(max(int(j[currentYear][1][codeIndexMap[code]]) + 1, 1))
                        else:
                            j[currentVisit][0] = patientAge
                            j[currentVisit][1][codeIndexMap[code]] = \
                                str(max(int(j[currentVisit][1][codeIndexMap[code]]) + 1, 1))
            # Record the final patient's data if information about them was extracted. This wil only have occurred if
            # the patient is meant to have their data output.
            if currentPatient in patientData:
                patientGender = patientData[currentPatient]["Gender"]
                _write_entire_history(
                    binaryHistory, currentPatient, patientGender, fidBinHist, fidBinVisNC, fidBinVisC,
                    fidBinYearNC, fidBinYearC
                )
                _write_entire_history(
                    countHistory, currentPatient, patientGender, fidCountHist, fidCountVisNC, fidCountVisC,
                    fidCountYearNC, fidCountYearC
                )


def _init_histories(numCodes):
    """Generate blank history records.

    :param numCodes:    The number of unique codes in the dataset.
    :type numCodes:     int
    :return:            The generated empty binary, count and raw history records.
    :rtype:             dict, dict, dict

    """

    binaryHistory = {
        "Entire": [None, ['-1'] * numCodes], "VisitNC": defaultdict(lambda: [None, ['-1'] * numCodes]),
        "VisitC": defaultdict(lambda: [None, ['-1'] * numCodes]),
        "YearNC": defaultdict(lambda: [None, ['-1'] * numCodes]),
        "YearC": defaultdict(lambda: [None, ['-1'] * numCodes]),
    }
    countHistory = {
        "Entire": [None, ['-1'] * numCodes], "VisitNC": defaultdict(lambda: [None, ['-1'] * numCodes]),
        "VisitC": defaultdict(lambda: [None, ['-1'] * numCodes]),
        "YearNC": defaultdict(lambda: [None, ['-1'] * numCodes]),
        "YearC": defaultdict(lambda: [None, ['-1'] * numCodes]),
    }
    rawHistory = {}

    return binaryHistory, countHistory, rawHistory


def _write_entire_history(history, patientID, patientGender, fidEntire, fidVisitNC, fidVisitC, fidYearNC,
                          fidYearC):
    """Write out all history information for a patient.

    :param history:         The history to output the information for.
    :type history:          dict
    :param patientID:       The ID of the patient.
    :type patientID:        str
    :param patientGender:   The gender of the patient (M or F).
    :type patientGender:    str
    :param fidEntire:       The file handle to the file to write the entire history information to.
    :type fidEntire:        _io.TextIOWrapper
    :param fidVisitNC:      The file handle to the file to write the non-cumulative visit history information to.
    :type fidVisitNC:       _io.TextIOWrapper
    :param fidVisitC:       The file handle to the file to write the cumulative visit history information to.
    :type fidVisitC:        _io.TextIOWrapper
    :param fidYearNC:       The file handle to the file to write the non-cumulative year history information to.
    :type fidYearNC:        _io.TextIOWrapper
    :param fidYearC:        The file handle to the file to write the cumulative year history information to.
    :type fidYearC:         _io.TextIOWrapper

    """

    fidEntire.write(
        "{:s}\t{:d}\t{:s}\t{:s}\n".format(
            patientID, history["Entire"][0], patientGender, '\t'.join(history["Entire"][1])
        )
    )
    visitNCOutput = ""
    for i in sorted(history["VisitNC"]):
        visitNCOutput += "{:s}\t{:d}\t{:s}\t{:s}\n".format(
            patientID, history["VisitNC"][i][0], patientGender, '\t'.join(history["VisitNC"][i][1])
        )
    fidVisitNC.write(visitNCOutput)
    visitCOutput = ""
    for i in sorted(history["VisitC"]):
        visitCOutput += "{:s}\t{:d}\t{:s}\t{:s}\n".format(
            patientID, history["VisitC"][i][0], patientGender, '\t'.join(history["VisitC"][i][1])
        )
    fidVisitC.write(visitCOutput)
    yearNCOutput = ""
    for i in sorted(history["YearNC"]):
        yearNCOutput += "{:s}\t{:d}\t{:s}\t{:s}\n".format(
            patientID, history["YearNC"][i][0], patientGender, '\t'.join(history["YearNC"][i][1])
        )
    fidYearNC.write(yearNCOutput)
    yearCOutput = ""
    for i in sorted(history["YearC"]):
        yearCOutput += "{:s}\t{:d}\t{:s}\t{:s}\n".format(
            patientID, history["YearC"][i][0], patientGender, '\t'.join(history["YearC"][i][1])
        )
    fidYearC.write(yearCOutput)
