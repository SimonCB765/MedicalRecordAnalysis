"""Generate datasets from SQL dump files."""

# Python imports.
import datetime
import logging
import os
import re
import sys

# User imports.
from . import file_generator
from . import save_patient_data

# Globals.
LOGGER = logging.getLogger(__name__)


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
            chunks = line.split('\t')
            patientID = chunks[0]
            DOB = chunks[1]
            patientGender = chunks[2]
            if patientsToKeep.match(patientID) and (not patientsToIgnore.match(patientID)):
                patientData[patientID] = {"DOB": DOB, "Gender": patientGender}

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

    # Create the files to record the generated datasets in.
    outputFiles = file_generator.main(dirOutput, uniqueCodes, codeAssociatedValues)

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
            date = datetime.datetime.strptime(chunks[2], "%Y-%m-%d")  # Convert YYYY-MM-DD date to datetime.
            value1 = float(chunks[3])
            value2 = float(chunks[4])

            # Only record information about patients we're interested in.
            if patientID in patientData:
                if patientID != currentPatient and currentPatient:
                    # A new patient has been found and this is not the first line of the file, so record the old
                    # patient and reset the patient data for the new patient.

                    # Output an update.
                    patientsSaved += 1
                    if patientsSaved % 100 == 0:
                        LOGGER.info("Saved {:d} patients ({:.2f}%).".format(
                            patientsSaved, (patientsSaved / len(patientData)) * 100
                        ))

                    # Output the patient's information.
                    dateOfBirth = datetime.datetime.strptime(patientData[currentPatient]["DOB"], "%Y")
                    patientGender = patientData[currentPatient]["Gender"]
                    save_patient_data.main(
                        currentPatient, patientHistory, dateOfBirth, patientGender, outputFiles, uniqueCodes
                    )
                    patientHistory = []
                currentPatient = patientID  # Update the current patient's ID to be this patient's.

                # Add this patient-code association to the patient's history if the code is to be output.
                if code in codeAssociatedValues:
                    patientHistory.append({"Code": code, "Date": date, "Val1": value1, "Val2": value2})
        # Record the final patient's data if information about them was extracted. This wil only have occurred if the
        # patient is meant to have their data output.
        if patientHistory:
            dateOfBirth = datetime.datetime.strptime(patientData[currentPatient]["DOB"], "%Y")
            patientGender = patientData[currentPatient]["Gender"]
            save_patient_data.main(currentPatient, patientHistory, dateOfBirth, patientGender, outputFiles, uniqueCodes)