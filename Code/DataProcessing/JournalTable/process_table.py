"""Process a journal table into a format that is quicker to read."""

# Python imports.
from collections import defaultdict
import datetime
import logging
import os
import sys

# User imports.
from . import parse_patient_entry

# Globals.
LOGGER = logging.getLogger(__name__)


def main(dirSQLFiles, dirProcessedData):
    """Process a journal and patient table and convert them to a more standardised TSV format.

    :param dirSQLFiles:         The location of the directory containing the SQL files of the patient data.
    :type dirSQLFiles:          str
    :param dirProcessedData:    The location to save the processed journal table data.
    :type dirProcessedData:     str

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

    LOGGER.info("Starting journal table pre-processing.")

    # Extract the patient demographics of interest.
    filePatientDemographics = os.path.join(dirProcessedData, "PatientDemographics.tsv")
    with open(filePatientTable, 'r') as fidPatientTable, open(filePatientDemographics, 'w') as fidDemographics:
        fidDemographics.write("PatientID\tDOB\tGender\n")
        for line in fidPatientTable:
            if line.startswith("insert"):
                # Found a line containing patient details.
                line = line[84:]  # Strip of the SQL insert syntax at the beginning.
                line = line[:-3]  # Strip off the ");\n" at the end.
                chunks = line.split(',')
                patientID = chunks[0]
                DOB = chunks[1]
                patientGender = 'M' if chunks[3] == '1' else 'F'  # A '1' indicates a male and a '0' a female.
                fidDemographics.write("{:s}\t{:s}\t{:s}\n".format(patientID, DOB, patientGender))

    # Convert the journal table into a standard format, ignoring any entries that are missing either a patient ID or
    # a code.
    fileProcessedJournal = os.path.join(dirProcessedData, "JournalTable.tsv")
    numEvents = 0
    numValidEvents = 0
    uniqueCodes = set()  # The codes used in the dataset.
    uniquePatients = set()  # The patients in the dataset.
    codeAssociatedValues = defaultdict(lambda: {"Val1": False, "Val2": False})  # Value types associated with codes.
    currentPatient = None  # The ID of the patient who's record is currently being built.
    patientHistory = defaultdict(list)  # The data for the current patient.
    with open(fileJournalTable, 'r') as fidJournalTable, open(fileProcessedJournal, 'w') as fidProcessed:
        fidProcessed.write("PatientID\tCode\tDate\tYear\tVisitNumber\tVal1\tVal2\tFreeText\n")
        for line in fidJournalTable:
            if line.startswith("insert"):
                # The line contains information about a row in the journal table.
                numEvents += 1
                entries = parse_patient_entry.main(line)
                patientID = entries[0]
                code = entries[1]
                date = datetime.datetime.strptime(entries[2], "%Y-%m-%d")  # Convert YYYY-MM-DD date to datetime.

                if patientID and code:
                    # The entry is valid as it has both a patient ID and code recorded for it.
                    numValidEvents += 1
                    uniqueCodes.add(code)
                    uniquePatients.add(patientID)
                    codeAssociatedValues[code]["Val1"] |= float(entries[3]) != 0
                    codeAssociatedValues[code]["Val2"] |= float(entries[4]) != 0

                    if patientID != currentPatient and currentPatient:
                        # A new patient has been found and this is not the first line of the file, so record the old
                        # patient and reset the patient data for the new patient.

                        # Write out the patient's history sorted by date from oldest to newest.
                        visitNumber = -1
                        for i in sorted(patientHistory):
                            visitNumber += 1
                            for j in patientHistory[i]:
                                j.insert(3, j[2][:4])
                                j.insert(4, str(visitNumber))
                                fidProcessed.write("{:s}\n".format('\t'.join(j)))

                        # Reset the history for the next patient.
                        patientHistory.clear()
                    currentPatient = patientID

                    # Add the entry to the patient's history.
                    patientHistory[date].append(entries)

    # Log statistics about the dataset.
    LOGGER.info("{:d} events found in the dataset.".format(numEvents))
    LOGGER.info("{:d} valid events found in the dataset.".format(numValidEvents))
    LOGGER.info("{:d} unique patients found in the dataset.".format(len(uniquePatients)))
    LOGGER.info("{:d} unique codes found in the dataset.".format(len(uniqueCodes)))

    # Write out the codes in the dataset.
    uniqueCodes = sorted(uniqueCodes)
    fileCodes = os.path.join(dirProcessedData, "Codes.txt")
    with open(fileCodes, 'w') as fidCodes:
        fidCodes.write("Code\tHasVal1Value\tHasVal2Value\n")
        for i in uniqueCodes:
            fidCodes.write(
                "{:s}\t{:d}\t{:d}\n".format(i, codeAssociatedValues[i]["Val1"], codeAssociatedValues[i]["Val2"])
            )

    # Write out statistics of the dataset.
    fileStats = os.path.join(dirProcessedData, "Statistics.txt")
    with open(fileStats, 'w') as fid:
        fid.write("{:d} events found in the dataset.\n".format(numEvents))
        fid.write("{:d} valid events found in the dataset.\n".format(numValidEvents))
        fid.write("{:d} unique patients found in the dataset.\n".format(len(uniquePatients)))
        fid.write("{:d} unique codes found in the dataset.\n".format(len(uniqueCodes)))
