"""Generate datasets from the QICKD SQL dump files."""

# Python imports.
from collections import defaultdict
import json
import os
import re
import sys

# User imports.
from Utilities import json_to_ascii

# Globals
PYVERSION = sys.version_info[0]  # Determine major version number.


def main(fileParams):
    """Generate the datasets to use for the medical history clustering and generation.

    :param fileParams:   The location of the file containing the dataset generation arguments in JSON format.
    :type fileParams:    str

    """

    # Parse the JSON file of parameters.
    readParams = open(fileParams, 'r')
    parsedArgs = json.load(readParams)
    if PYVERSION == 2:
        parsedArgs = json_to_ascii(parsedArgs)  # Convert all unicode characters to ascii (only needed for Python < 3).
    readParams.close()

    # Check the input directory parameter is correct.
    errorsFound = []
    if "SQLDataDirectory" not in parsedArgs:
        errorsFound.append("There must be a parameter field called SQLDataDirectory.")
    elif not os.path.isdir(parsedArgs["SQLDataDirectory"]):
        errorsFound.append("The input data directory does not exist.")

    # Check the output directory parameter is correct.
    if "GeneratedDatasetDirectory" not in parsedArgs:
        errorsFound.append("There must be a parameter field called GeneratedDatasetDirectory.")
    try:
        os.makedirs(parsedArgs["GeneratedDatasetDirectory"])
    except FileExistsError:
        # Directory already exists.
        pass

    # Print error messages.
    if errorsFound:
        print("\n\nThe following errors were encountered while parsing the input parameters:\n")
        print('\n'.join(errorsFound))
        sys.exit()

    # Extract parameters.
    dirSQLFiles = parsedArgs["SQLDataDirectory"]
    dirResults = parsedArgs["GeneratedDatasetDirectory"]

    # Get the files for the SQL tables we're interested in. These would be the journal table and the patient table.
    fileJournalTable = os.path.join(dirSQLFiles, "journal.sql")
    filePatientTable = os.path.join(dirSQLFiles, "patient.sql")


    #TODO remove this
    count = 0


    # Extract the information about each patient's history. The history for each patient will be a string containing
    # all code association concatenated together. For each sasociation the code and date of assocaition are separated
    # by a comma, while the differetn assocaitions are separated by a ';'. For example:
    #   DOCA4868,1989-06-05;DOCA4868,1990-01-18;H03,1995-01-11;
    patientHistories = defaultdict(str)
    uniqueCodes = set()
    with open(fileJournalTable, 'r') as fidJournalTable:
        for line in fidJournalTable:
            rowEntry = re.match("insert into `journal`\(`id`,`code`,`date`,`value1`,`value2`,`text`\) values \(", line)
            if rowEntry:
                # The line contains information about a row in the database table.
                line = line[rowEntry.end():]  # Strip of the SQL insert syntax at the beginning.
                line = line[:-3]  # Strip off the ");\n" at the end.
                chunks = line.split(',')
                patientID = chunks[0]
                code = chunks[1][1:-1]  # The code entries are strings in the database, and are therefore enclosed in '.
                date = chunks[2][1:-1]  # The code entries are strings in the database, and are therefore enclosed in '.
                patientHistories[patientID] += "{0:s},{1:s};".format(code, date)  # Append new code association.
                uniqueCodes.add(code)

                count += 1
                if count > 10000:
                    break
    uniqueCodes = sorted(uniqueCodes)

    # Extract the patient demographics.
    patientDemographics = {}
    with open(filePatientTable, 'r') as fidPatientTable:
        for line in fidPatientTable:
            rowEntry = re.match(
                "insert into `patient`\(`id`,`dob`,`depscore`,`isMale`,`race`,`pracID`,`imd`\) values \(",
                line)
            if rowEntry:
                # The line contains information about a row in the database table.
                line = line[rowEntry.end():]  # Strip of the SQL insert syntax at the beginning.
                line = line[:-3]  # Strip off the ");\n" at the end.
                chunks = line.split(',')
                patientID = chunks[0]
                DOB = chunks[1]
                isMale = chunks[3]
                patientDemographics[patientID] = {"DOB": DOB, "Male": isMale}  # Records patient's demographics.

    # Setup the cleaned dataset files.
    fileCountMatrix = os.path.join(dirResults, "CountMatrix.tsv")

    # Record the simple patient history matrix.
    with open(fileCountMatrix, 'w') as fidCountMatrix:
        # Write out the header.
        header = "PatientID\tDOB\tMale\t{0:s}\n".format('\t'.join(uniqueCodes))
        fidCountMatrix.write(header)

        # Generate each patient's code vector.
        for patientID in patientHistories:
            codeCounts = dict([(i, 0) for i in uniqueCodes])  # Setup the record of the counts of each code.
            history = patientHistories[patientID].split(';')[:-1]  # Strip off final ';' from the history string.
            for i in history:
                # For each code association, update the count of the codes this patient is associated with.
                i = i.split(',')  # Split the code from the date.
                codeCounts[i[0]] += 1

            # Write out the patient history vector.
            fidCountMatrix.write("{0:s}\t{1:s}\t{2:s}\t{3:s}\n".format(
                patientID, patientDemographics[patientID]["DOB"], patientDemographics[patientID]["Male"],
                '\t'.join([str(codeCounts[i]) for i in uniqueCodes])))
