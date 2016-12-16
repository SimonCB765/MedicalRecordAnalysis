"""Generate datasets from SQL dump files."""

# Python imports.
from collections import defaultdict
import datetime
import logging
import os
import re
import sys

# User imports.
from . import file_generator
from . import parse_patient_entry
from . import save_patient_data

# Globals.
LOGGER = logging.getLogger(__name__)


def main(dirSQLFiles, dirOutput, config):
    """Generate flat file datasets by processing a set of SQL files containing patient medical data.

    Patient history data is assumed to be stored in a file called journal.sql within the SQL file directory. Within this
    file a patient's history is assumed to be recorded consecutively (i.e. a patient has all their records recorded
    one after the other with no other patient's records in between).

    :param dirSQLFiles:     The location of the directory containing the SQL files of the patient data.
    :type dirSQLFiles:      str
    :param dirOutput:       The location of the directory where the processed flat files should be saved.
    :type dirOutput:        str
    :param config:          The object containing the configuration parameters for the flat file generation.
    :type config:           JsonschemaManipulation.Configuration

    """

    # Get the files for the SQL tables we're interested in. These would be the journal table and the patient table.
    isError = False
    fileJournalTable = os.path.join(dirSQLFiles, "journal.sql")
    if not os.path.isfile(fileJournalTable):
        LOGGER.error("There is no journal.sql file within the input location supplied ({:s}).".format(fileJournalTable))
        isError = True
    filePatientTable = os.path.join(dirSQLFiles, "patient.sql")
    if not os.path.isfile(filePatientTable):
        LOGGER.error("There is no patient.sql file within the input location supplied ({:s}).".format(filePatientTable))
        isError = True
    if isError:
        print("\nErrors were found while attempting to access the input files during flat file generation.\n")
        sys.exit()

    # Determine the codes and patients to ignore/keep. If not codes to ignore are specified, then don't ignore any.
    # If no codes to keep are specified, then keep all.
    codesToIgnore = config.get_param(["DataProcessing", "CodesToIgnore"])[1]
    codesToIgnore = re.compile('|'.join(codesToIgnore)) if codesToIgnore else re.compile("a^")
    codesToKeep = config.get_param(["DataProcessing", "CodesToKeep"])[1]
    codesToKeep = re.compile('|'.join(codesToKeep)) if codesToKeep else re.compile("")
    patientsToIgnore = config.get_param(["DataProcessing", "PatientsToIgnore"])[1]
    patientsToIgnore = re.compile('|'.join(patientsToIgnore)) if patientsToIgnore else re.compile("a^")
    patientsToKeep = config.get_param(["DataProcessing", "PatientsToKeep"])[1]
    patientsToKeep = re.compile('|'.join(patientsToKeep)) if patientsToKeep else re.compile("")

    # Extract the patient demographics.
    patientData = {}
    with open(filePatientTable, 'r') as fidPatientTable:
        for line in fidPatientTable:
            if line.startswith("insert"):
                # Found a line containing patient details.
                line = line[84:]  # Strip of the SQL insert syntax at the beginning.
                line = line[:-3]  # Strip off the ");\n" at the end.
                chunks = line.split(',')
                patientID = chunks[0]
                DOB = chunks[1]
                patientGender = 'M' if chunks[3] == '1' else 'F'  # A '1' indicates a male and a '0' a female.
                patientData[patientID] = {"DOB": DOB, "Gender": patientGender}  # Records patient's demographics.

    # Identify the codes used in the dataset and whether they have any data associated with them.
    # This will cause two passes through the patient data. However, without this the entire dataset will need to be
    # stored in memory, as no patient history can be written out without knowing all the codes in the dataset.
    LOGGER.info("Now determining patients and codes in the dataset.")
    count = 0  # TODO remove this
    uniqueCodes = set()  # The codes used in the dataset.
    patientsToOutput = set()  # The patients in the dataset that should be output.
    codeAssociatedValues = defaultdict(lambda: {"Val1": False, "Val2": False})  # Value types associated with codes.
    with open(fileJournalTable, 'r') as fidJournalTable:
        for line in fidJournalTable:
            if line.startswith("insert"):
                # The line contains information about a row in the journal table.
                entries = parse_patient_entry.main(line)

                if entries:
                    # The entry on this line contained a code, so add the code to the set of unique codes if it is not
                    # being ignored.
                    patientID = entries[0]
                    code = entries[1]
                    if (patientsToKeep.match(patientID) and not patientsToIgnore.match(patientID)) and \
                            (codesToKeep.match(code) and not codesToIgnore.match(code)):
                        uniqueCodes.add(code)
                        patientsToOutput.add(patientID)
                        codeAssociatedValues[code]["Val1"] |= float(entries[3]) != 0
                        codeAssociatedValues[code]["Val2"] |= float(entries[4]) != 0

                # TODO remove this
                count += 1
                if count > 1000000:
                    break
                # TODO
    uniqueCodes = sorted(uniqueCodes)

    # Create the files to record the generated datasets in.
    outputFiles = file_generator.main(dirOutput, uniqueCodes, codeAssociatedValues)

    # Extract the information about each patient's history.
    LOGGER.info("Now generating patient histories.")
    patientsSaved = 0
    currentPatient = None  # The ID of the patient who's record is currently being built.
    patientHistory = []  # The data for the current patient.
    with open(fileJournalTable, 'r') as fidJournalTable:
        for line in fidJournalTable:
            if line[:6] == "insert":
                # The line contains information about a row in the journal table.
                entries = parse_patient_entry.main(line)

                if entries:
                    # The entry on this line contained all the information needed to record it (for example the code was
                    # not missing), so get the details of this patient-code association.
                    patientID = entries[0]
                    code = entries[1]
                    date = datetime.datetime.strptime(entries[2], "%Y-%m-%d")  # Convert YYYY-MM-DD date to datetime.
                    value1 = float(entries[3])
                    value2 = float(entries[4])

                    if patientID != currentPatient and currentPatient:
                        # A new patient has been found and this is not the first line of the file, so record the old
                        # patient and reset the patient data for the new patient.
                        if currentPatient in patientsToOutput:
                            # Only output the patient's information if they are meant to be recorded.
                            dateOfBirth = datetime.datetime.strptime(patientData[currentPatient]["DOB"], "%Y")
                            patientGender = patientData[currentPatient]["Gender"]
                            save_patient_data.main(
                                currentPatient, patientHistory, dateOfBirth, patientGender, outputFiles, uniqueCodes
                            )

                            # Output an update.
                            patientsSaved += 1
                            if patientsSaved % 100 == 0:
                                LOGGER.info("Saved {:d} patients ({:.2f}%).".format(
                                    patientsSaved, (patientsSaved / len(patientsToOutput)) * 100
                                ))
                        patientHistory = []
                    currentPatient = patientID  # Update the current patient's ID to be this patient's.

                    # Add this patient-code association to the patient's history.
                    patientHistory.append({"Code": code, "Date": date, "Val1": value1, "Val2": value2})
        # Record the final patient's data.
        if currentPatient in patientsToOutput:
            # Only output the patient's information if they are meant to be recorded.
            dateOfBirth = datetime.datetime.strptime(patientData[currentPatient]["DOB"], "%Y")
            patientGender = patientData[currentPatient]["Gender"]
            save_patient_data.main(currentPatient, patientHistory, dateOfBirth, patientGender, outputFiles, uniqueCodes)
