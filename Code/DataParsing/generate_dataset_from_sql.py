"""Generate datasets from the QICKD SQL dump files."""

# Python imports.
from collections import defaultdict
import datetime
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

    #-------------------------------------#
    # Parse and Validate Input Parameters #
    #-------------------------------------#
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

    # Check that the rebase year is correct (if present).
    rebaseYear = datetime.datetime.strptime("1950", "%Y")
    try:
        rebaseYear = datetime.datetime.strptime(parsedArgs["Year0"], "%Y")
    except ValueError:
        # There was a problem creating the rebase year datetime object.
        errorsFound.append(
            "Could not convert rebase year {0:s} into a YYYY format year.".format(parsedArgs["Year0"]))

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


    #--------------------------------------#
    # Extract the Data from the SQL Files  #
    #--------------------------------------#
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
                if count > 1000:
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

    #------------------------------------------------------#
    # Create the Different Patient History Representations #
    #------------------------------------------------------#
    # Setup the cleaned dataset files.
    fileCountMatrix = os.path.join(dirResults, "CountMatrix.tsv")
    fileCountSumOverTime = os.path.join(dirResults, "CountsSummedOverTime.tsv")
    fileBinarySumOverTime = os.path.join(dirResults, "CountsSummedOverTime_Binary.tsv")
    fileCountSumOverTimeRebased = os.path.join(dirResults, "CountsSummedOverTime_Rebased.tsv")
    fileBinarySumOverTimeRebased = os.path.join(dirResults, "CountsSummedOverTime_Rebased_Binary.tsv")
    fileCountPerTimePoint = os.path.join(dirResults, "CountsPerTimePoint.tsv")
    fileBinaryPerTimePoint = os.path.join(dirResults, "CountsPerTimePoint_Binary.tsv")
    fileCountPerTimePointRebased = os.path.join(dirResults, "CountsPerTimePoint_Rebased.tsv")
    fileBinaryPerTimePointRebased = os.path.join(dirResults, "CountsPerTimePoint_Rebased_Binary.tsv")

    # Record the different representations of the patient histories.
    with open(fileCountMatrix, 'w') as fidCountMatrix, \
            open(fileCountSumOverTime, 'w') as fidCountSumOverTime, \
            open(fileBinarySumOverTime, 'w') as fidBinarySumOverTime, \
            open(fileCountSumOverTimeRebased, 'w') as fidCountSumOverTimeRebased, \
            open(fileBinarySumOverTimeRebased, 'w') as fidBinarySumOverTimeRebased, \
            open(fileCountPerTimePoint, 'w') as fidCountPerTimePoint, \
            open(fileBinaryPerTimePoint, 'w') as fidBinaryPerTimePoint, \
            open(fileCountPerTimePointRebased, 'w') as fidCountPerTimePointRebased, \
            open(fileBinaryPerTimePointRebased, 'w') as fidBinaryPerTimePointRebased:
        # Write out the headers.
        separatedCounts = '\t'.join(uniqueCodes)
        countMatrixHeader = "PatientID\tDOB\tMale\t{0:s}\n".format(separatedCounts)
        fidCountMatrix.write(countMatrixHeader)
        sumOverTimeHeader = "PatientID\tDOB\tMale\tDate\t{0:s}\n".format(separatedCounts)
        fidCountSumOverTime.write(sumOverTimeHeader)
        fidBinarySumOverTime.write(sumOverTimeHeader)
        fidCountPerTimePoint.write(sumOverTimeHeader)
        fidBinaryPerTimePoint.write(sumOverTimeHeader)
        rebasedSumOverTimeHeader = "PatientID\tDOB\tMale\tDaysAfterJan_{0:s}\t{1:s}\n".format(
            rebaseYear.strftime("%Y"), separatedCounts)
        fidCountSumOverTimeRebased.write(rebasedSumOverTimeHeader)
        fidBinarySumOverTimeRebased.write(rebasedSumOverTimeHeader)
        fidCountPerTimePointRebased.write(rebasedSumOverTimeHeader)
        fidBinaryPerTimePointRebased.write(rebasedSumOverTimeHeader)

        # Generate each patient's code vector(s).
        for patientID in sorted(patientHistories):
            history = patientHistories[patientID].split(';')[:-1]  # Strip off final ';' from the history string.

            # Determine the codes that were assigned at each time point.
            codesAtTimePoint = defaultdict(list)
            for i in history:
                # For each code association, record that the time point was associated with the code.
                code, date = i.split(',')  # Split the code from the date.
                date = datetime.datetime.strptime(date, "%Y-%m-%d")  # Convert YYYY-MM-DD date to datetime object.
                codesAtTimePoint[date].append(code)

            # Sort the dates when a patient was associated with a code in order from oldest to newest.
            sortedDates = sorted(codesAtTimePoint)

            # Determine the code counts for each representation of the history.
            sumCodeCounts = dict([(i, 0) for i in uniqueCodes])  # Cumulative count of codes seen up to this time point.
            for i in sortedDates:
                daysAfterYear0 = i - rebaseYear  # Determine when this association occured in days after year 0.
                timePointCounts = dict([(i, 0) for i in uniqueCodes])  # Code association count at this time point.
                for j in codesAtTimePoint[i]:
                    sumCodeCounts[j] += 1
                    timePointCounts[j] += 1

                    # Write out the patient's current cumulative medical history in both count and binary formats.
                    fidCountSumOverTime.write("{0:s}\t{1:s}\t{2:s}\t{3:s}\t{4:s}\n".format(
                        patientID, patientDemographics[patientID]["DOB"], patientDemographics[patientID]["Male"],
                        i.strftime("%Y-%m-%d"), '\t'.join([str(sumCodeCounts[i]) for i in uniqueCodes])))
                    fidBinarySumOverTime.write("{0:s}\t{1:s}\t{2:s}\t{3:s}\t{4:s}\n".format(
                        patientID, patientDemographics[patientID]["DOB"], patientDemographics[patientID]["Male"],
                        i.strftime("%Y-%m-%d"), '\t'.join(['1' if sumCodeCounts[i] > 0 else '0' for i in uniqueCodes])))

                    # Write out the patient's current cumulative medical history in both count and binary formats
                    # after rebasing the year.
                    fidCountSumOverTimeRebased.write("{0:s}\t{1:s}\t{2:s}\t{3:d}\t{4:s}\n".format(
                        patientID, patientDemographics[patientID]["DOB"], patientDemographics[patientID]["Male"],
                        daysAfterYear0.days, '\t'.join([str(sumCodeCounts[i]) for i in uniqueCodes])))
                    fidBinarySumOverTimeRebased.write("{0:s}\t{1:s}\t{2:s}\t{3:d}\t{4:s}\n".format(
                        patientID, patientDemographics[patientID]["DOB"], patientDemographics[patientID]["Male"],
                        daysAfterYear0.days, '\t'.join(['1' if sumCodeCounts[i] > 0 else '0' for i in uniqueCodes])))

                    # Write out the patient's medical history for this date in both count and binary formats.
                    fidCountPerTimePoint.write("{0:s}\t{1:s}\t{2:s}\t{3:s}\t{4:s}\n".format(
                        patientID, patientDemographics[patientID]["DOB"], patientDemographics[patientID]["Male"],
                        i.strftime("%Y-%m-%d"), '\t'.join([str(timePointCounts[i]) for i in uniqueCodes])))
                    fidBinaryPerTimePoint.write("{0:s}\t{1:s}\t{2:s}\t{3:s}\t{4:s}\n".format(
                        patientID, patientDemographics[patientID]["DOB"], patientDemographics[patientID]["Male"],
                        i.strftime("%Y-%m-%d"),
                        '\t'.join(['1' if timePointCounts[i] > 0 else '0' for i in uniqueCodes])))

                    # Write out the patient's medical history for this date in both count and binary formats
                    # after rebasing the year.
                    fidCountPerTimePointRebased.write("{0:s}\t{1:s}\t{2:s}\t{3:d}\t{4:s}\n".format(
                        patientID, patientDemographics[patientID]["DOB"], patientDemographics[patientID]["Male"],
                        daysAfterYear0.days, '\t'.join([str(timePointCounts[i]) for i in uniqueCodes])))
                    fidBinaryPerTimePointRebased.write("{0:s}\t{1:s}\t{2:s}\t{3:d}\t{4:s}\n".format(
                        patientID, patientDemographics[patientID]["DOB"], patientDemographics[patientID]["Male"],
                        daysAfterYear0.days, '\t'.join(['1' if timePointCounts[i] > 0 else '0' for i in uniqueCodes])))

            # Write out the vector for the counts of all codes in the patient's history.
            fidCountMatrix.write("{0:s}\t{1:s}\t{2:s}\t{3:s}\n".format(
                patientID, patientDemographics[patientID]["DOB"], patientDemographics[patientID]["Male"],
                '\t'.join([str(sumCodeCounts[i]) for i in uniqueCodes])))
