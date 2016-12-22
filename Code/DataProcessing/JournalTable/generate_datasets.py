"""Generate datasets from pre-processed SQL dump files."""

# Python imports.
import logging
import operator
import os
import re
import sys

# User imports.
from . import file_generator
from . import save_patient_data

# Globals.
LOGGER = logging.getLogger(__name__)

# Define functions for compatibility.
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

    # Create patient and code ignore/keep regular expressions.
    patientsToIgnore = config.get_param(["DataProcessing", "PatientsToIgnore"])[1]
    patientsToIgnore = re.compile('|'.join(patientsToIgnore)) if patientsToIgnore else re.compile("a^")
    patientsToKeep = config.get_param(["DataProcessing", "PatientsToKeep"])[1]
    patientsToKeep = re.compile('|'.join(patientsToKeep)) if patientsToKeep else re.compile("")
    codesToIgnore = config.get_param(["DataProcessing", "CodesToIgnore"])[1]
    codesToIgnore = re.compile('|'.join(codesToIgnore)) if codesToIgnore else re.compile("a^")
    codesToKeep = config.get_param(["DataProcessing", "CodesToKeep"])[1]
    codesToKeep = re.compile('|'.join(codesToKeep)) if codesToKeep else re.compile("")

    # Extract the patient demographics and determine which patients should be used.
    validPatientData = {}
    validCodes = set()  # Valid codes (kept and not ignored) that are contained within a valid patient's history.
    with open(filePatientData, 'r') as fidPatientData:
        _ = fidPatientData.readline()  # Strip the header.
        for line in fidPatientData:
            chunks = (line.strip()).split('\t')
            patientID = chunks[0]
            yearOfBirth = int(chunks[1][:4])
            patientGender = chunks[2]
            codesPatientHas = chunks[3].split(',')
            validCodesPatientHas = [i for i in codesPatientHas if codesToKeep.match(i) and (not codesToIgnore.match(i))]

            if patientsToKeep.match(patientID) and (not patientsToIgnore.match(patientID)) and validCodesPatientHas:
                # Only record a patient if they are to be used, not to be ignored and are associated with a code that
                # is to be kept and not ignored.
                validCodes.update(validCodesPatientHas)
                validPatientData[patientID] = {"YearOfBirth": yearOfBirth, "Gender": patientGender}

    # Create the mapping needed to map variables to their index in the bag-of-words representation.
    bowVarMapping = {}
    fidBOWVarMap = open(os.path.join(dirOutput, "BOWIndexMap.tsv"), 'w')
    for i, j in enumerate(validCodes):
        bowVarMapping[j] = i
        fidBOWVarMap.write("{:s}\t{:d}\n".format(j, i))
    bowVarMapping["_Age"] = len(validCodes)
    fidBOWVarMap.write("_Age\t{:d}\n".format(len(validCodes)))
    bowVarMapping["_Gender"] = len(validCodes) + 1
    fidBOWVarMap.write("_Gender\t{:d}\n".format(len(validCodes) + 1))
    fidBOWVarMap.close()

    # Create the mapping needed to map variables to their index in the raw data values representation.
    rawVarMapping = {}
    fidRawVarMap = open(os.path.join(dirOutput, "RawIndexMap.tsv"), 'w')
    fidRawVarMap.close()

    # Extract the information about whether codes have any values associated with them.
    codeAssociatedValues = {}
    with open(fileCodes, 'r') as fidCodes:
        _ = fidCodes.readline()  # Strip the header.
        for line in fidCodes:
            chunks = (line.strip()).split('\t')
            code = chunks[0]
            codeAssociatedValues[code] = {"Val1": bool(int(chunks[1])), "Val2": bool(int(chunks[2]))}

    # Create the files to record the generated datasets in.
    outputFiles = file_generator.open_files(dirOutput)

    # Extract the information about each patient's history.
    LOGGER.info("Now generating patient histories.")
    patientsSaved = 0
    currentPatient = None  # The ID of the patient who's record is currently being built.
    patientHistory = []  # The data for the current patient.
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

            if (patientID not in validPatientData) or (code not in validCodes):
                # Skip events that contain a patient or code that is not being used.
                continue

            if (patientID != currentPatient) and (currentPatient is not None):
                # A new patient has been found and this is not the first line of the file, so record the old
                # patient and reset the patient data for the new patient.

                # Output an update.
                patientsSaved += 1
                if patientsSaved % 1000 == 0:
                    LOGGER.info("Saved {:d} patients ({:.2f}%).".format(
                        patientsSaved, (patientsSaved / len(validPatientData)) * 100
                    ))

                # Output the patient's information.
                patientGender = validPatientData[currentPatient]["Gender"]
                save_patient_data.main(
                    currentPatient, patientHistory, patientGender, outputFiles, bowVarMapping, rawVarMapping
                )
                patientHistory = []
            currentPatient = patientID  # Update the current patient's ID to be this patient's.

            # Add this patient-code association to the patient's history.
            patientAge = year - validPatientData[patientID]["YearOfBirth"]
            patientHistory.append(
                {"Age": patientAge, "CodeIndex": code, "Val1": value1, "Val2": value2,
                 "Visit": visitNumber, "Year": year}
            )

        # Record the final patient's data if they are meant to have data extracted.
        if currentPatient in validPatientData:
            patientGender = validPatientData[currentPatient]["Gender"]
            save_patient_data.main(
                currentPatient, patientHistory, patientGender, outputFiles, bowVarMapping, rawVarMapping
            )

        # Close the open files.
        file_generator.close_files(outputFiles)
