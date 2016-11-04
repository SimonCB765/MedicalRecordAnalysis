"""Generate datasets from the QICKD SQL dump files."""

# Python imports.
from collections import defaultdict
import datetime
import os


def main(dirSQLFiles, dirOutput):
    """Generate flat file datasets by processing a set of SQL files containing patient medical data.

    Patient history data is assumed to be stored in a file called journal.sql within the SQL file directory. Within this
    file a patient's history is assumed to be recorded consecutively (i.e. patient P has all their records recorded
    one after the other). The processed files are then generated by a single pass through the journal.sql file,
    processing each patient's record one at a time (hence the need for all of a patients record to be stored
    consecutively in the journal.sql file to enable a single pass to be used). First the raw information
    about the patient is extracted by reading a number of lines from the journal.sql file. Then the different types of
    processing are performed to generate the patient's record in the different desired formats. The patient's processed
    record is then appended to each of the files storing the processed data.

    :param dirSQLFiles:     The location of the directory containing the SQL files of the patient data.
    :type dirSQLFiles:      str
    :param dirOutput:       The location of the directory where the processed flat files should be saved.
    :type dirOutput:        str

    """

    # Get the files for the SQL tables we're interested in. These would be the journal table and the patient table.
    fileJournalTable = os.path.join(dirSQLFiles, "journal.sql")
    filePatientTable = os.path.join(dirSQLFiles, "patient.sql")
    fileDiseaseTable = os.path.join(dirSQLFiles, "disease.sql")

    # Extract the patient demographics.
    patientData = {}
    with open(filePatientTable, 'r') as fidPatientTable:
        for line in fidPatientTable:
            if line[:6] == "insert":
                # Found a line containing patient details.
                line = line[84:]  # Strip of the SQL insert syntax at the beginning.
                line = line[:-3]  # Strip off the ");\n" at the end.
                chunks = line.split(',')
                patientID = chunks[0]
                DOB = chunks[1]
                patientGender = chunks[3]  # A '1' indicates a male and a '0' a female.
                patientData[patientID] = {"DOB": DOB, "Gender": patientGender}  # Records patient's demographics.

    # Identify the codes used in the dataset. This will cause two passes through the patient data. However, without this
    # the entire dataset (just about) will need to be stored in memory, as no patient history can be written out without
    # knowing all the codes in the dataset.
    count = 0  # TODO remove this
    uniqueCodes = set()  # The codes used in the dataset.
    with open(fileJournalTable, 'r') as fidJournalTable:
        for line in fidJournalTable:
            if line[:6] == "insert":
                # The line contains information about a row in the journal table.
                entries = patient_data_parser(line)

                if entries:
                    # The entry on this line contained a code, so add the code to the set of unique codes.
                    code = entries[1]
                    uniqueCodes.add(code)

                # TODO remove this
                count += 1
                if count > 10000:
                    break
                # TODO
    uniqueCodes = sorted(uniqueCodes)

    # Create the files to record the generated datasets in.
    outputFiles = file_name_generator(dirOutput, uniqueCodes)

    count = 0  # TODO remove this
    # Extract the information about each patient's history.
    currentPatient = None  # The ID of the patient who's record is currently being built.
    patientHistory = []  # The data for the current patient.
    with open(fileJournalTable, 'r') as fidJournalTable:
        for line in fidJournalTable:
            if line[:6] == "insert":
                # The line contains information about a row in the journal table.
                entries = patient_data_parser(line)

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
                        dateOfBirth = datetime.datetime.strptime(patientData[currentPatient]["DOB"], "%Y")
                        patientGender = patientData[currentPatient]["Gender"]
                        save_patient(
                            currentPatient, patientHistory, dateOfBirth, patientGender, outputFiles, uniqueCodes
                        )
                        patientHistory = []
                    currentPatient = patientID  # Update the current patient's ID to be this patient's.

                    # Add this patient-code association to the patient's history.
                    patientHistory.append({"Code": code, "Date": date, "Val1": value1, "Val2": value2})

                # TODO remove this
                count += 1
                if count > 10000:
                    break
        # Record the final patient's data.
        dateOfBirth = datetime.datetime.strptime(patientData[currentPatient]["DOB"], "%Y")
        patientGender = patientData[currentPatient]["Gender"]
        save_patient(currentPatient, patientHistory, dateOfBirth, patientGender, outputFiles, uniqueCodes)

    # Extract the patient disease information.
    with open(fileDiseaseTable, 'r') as fidDiseaseTable:
        for line in fidDiseaseTable:
            if line[:6] == "insert":
                # Found a line containing patient disease details.
                line = line[274:]  # Strip of the SQL insert syntax at the beginning.
                line = line[:-3]  # Strip off the ");\n" at the end.
                chunks = line.split(',')
                patientID = chunks[0]
                diseases = '\t'.join(chunks[1:])
                patientData[patientID]["Disease"] = diseases

    # Write out the patient demographic and disease details.
    filePatientDetails = os.path.join(dirOutput, "PatientDetails.tsv")
    with open(filePatientDetails, 'w') as fidPatientDetails:
        # Write out the header for the patient details.
        diseaseIndicators = "COPD\tStrokeOrCerebrovascularAccident\tHeartFailure\tIschaemicHeartDiseases\t" \
            "PeripheralVascularDiseases\tTransientIschaemicAttack\tType1Diabetes\tType2Diabetes\tAccidentalFall\t" \
            "Fractures\tProteinuria\tHypertension\tDiabetes"
        patientHeader = "PatientID\tDOB\tMale\t{0:s}\n".format(diseaseIndicators)
        fidPatientDetails.write(patientHeader)
        for i in patientData:
            fidPatientDetails.write("{0:s}\t{1:s}\t{2:s}\t{3:s}\n".format(
                i, patientData[i]["DOB"], patientData[i]["Gender"], patientData[i]["Disease"]))


def calculate_age(born, comparison=None, isFraction=False):
    """Calculate the age of someone in years.

    :param born:        The date when the person was born.
    :type born:         datetime.datetime
    :param comparison:  The date to compare the birthday against (or today's date if no date is supplied).
    :type comparison:   datetime.datetime
    :param isFraction:  Whether the age should be returned as a fractional year (e.g. 35.3) or not (e.g. 35). Rounding
                            to the nearest year is always performed down.
    :type isFraction:   bool

    """

    # Get date to compare against if needed.
    if not comparison:
        comparison = datetime.datetime.today()

    # Determine if their birthday would have occurred already in the year that comparison occurs in. For example, if the
    # person was born on March 5th 1970 and the comparison date is May 12th 2010, then there birthday would already have
    # occurred. However, if the comparison is January 12th 2010, then their birthday would not already have occurred.
    birthdayOccurred = (born.month, born.day) < (comparison.month, comparison.day)

    # Get the integer number of years.
    yearsOld = comparison.year - born.year - (not birthdayOccurred)

    # Determine days until the person's next birthday.
    if birthdayOccurred:
        # The person's birthday has occurred in the comparison year, so use the year after it to determine their next
        # birthday.
        try:
            nextBirthday = born.replace(year=comparison.year + 1)
        except ValueError:
            # The patient was born on February 29th and the current year was a leap year. Therefore their
            # birthday does not 'exist' in the next year. Instead, pretend their birthday in the next year is March 1st.
            nextBirthday = born.replace(year=comparison.year + 1, month=3, day=1)
    else:
        # The person's birthday has not occurred in the comparison year, so use the comparison year to determine their
        # next birthday.
        try:
            nextBirthday = born.replace(year=comparison.year)
        except ValueError:
            # The patient was born on February 29th and the current year was a leap year. Therefore their
            # birthday does not 'exist' in the next year. Instead, pretend their birthday in the next year is March 1st.
            nextBirthday = born.replace(year=comparison.year, month=3, day=1)
    daysUntilBirthday = nextBirthday - comparison

    # Return the person's age.
    meanSecondsInYear = 365.25 * 24 * 60 * 60
    if isFraction:
        return yearsOld + ((meanSecondsInYear - daysUntilBirthday.total_seconds()) / meanSecondsInYear)
    else:
        return yearsOld


def file_name_generator(dirOutput, uniqueCodes):
    """Generate the names of the cleaned dataset files to be generated.

    The intended contents of the files can be found in the README.

    :param dirOutput:       Location of the directory containing the dataset files.
    :type dirOutput:        str
    :param uniqueCodes:     The codes that appear associated with a patient in the dataset.
    :type uniqueCodes:      list
    :return:                The locations of the cleaned dataset files.
    :rtype:                 dict

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
            "Visits_NC": os.path.join(dirOutput, "RawData_Visits_NC.tsv"),
            "Years_NC": os.path.join(dirOutput, "RawData_Years_NC.tsv")
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
            open(outputFiles["RawData"]["Visits_NC"], 'a') as fidRawVisNC, \
            open(outputFiles["RawData"]["Years_NC"], 'a') as fidRawYearNC:

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
        # TODO

    return outputFiles


def patient_data_parser(line):
    """Parse an entry in the file of the patient-code associations.

    :param line:    The line in the file to parse.
    :type line:     str
    :return:        The entries on the line. The entries will be ordered (in ascending index order) as:
                        patient id, code, date, Val1, Val2, free text
                    If the line does not contain a code, if for example the line looks like:
                        3123336,'','2004-11-01',0.0000,0.0000,null
                        then an empty list is returned.
    :rtype:         list

    """

    # The beginning of the line is expected to have the format:
    #   insert into `journal`(`id`,`code`,`date`,`value1`,`value2`,`text`) values (
    # The rest of the line will be formatted as:
    #   id,code,date,Val1,Val2,FreeText);
    # The first 75 and last 3 character are therefore stripped off to give: id,code,date,Val1,Val2,FreeText
    # The expected formats of these entries are:
    #   id - numerical patient ID value (e.g. 26044).
    #   code - clinical code as a single quoted string (e.g. 'C10E').
    #   date - the date of the association as a single quoted string (e.g. '1998-04-16').
    #   Val1 - the first float value (format .4f) associated with the code-patient pair (e.g. 120.0000).
    #   Val2 - the second float value (format .4f) associated with the code-patient pair (e.g. 45.0000).
    #   FreeText - null if there is no text associated with the code-patient pair or a single quoted string
    #       (e.g. 'ONE TO BE TAKEN FOUR TIMES A DAY').
    line = line[75:]  # Strip of the SQL insert syntax at the beginning.
    line = line[:-3]  # Strip off the ");\n" at the end.

    # Some codes are recorded with embedded data (e.g. as '2469,v=130,w=80'). In this case the code has its
    # two values recorded as part of the code (often with the two values also recorded in the correct Val1
    # and Val2 entries as well. It's also possible that the free text has commas in it (which is used as the
    # delimiter in the insert statement). Simply splitting the insert statement on a comma to get the
    # different values is therefore not feasible. Instead, the line has to be read character by character
    # to make sure that the line parsing is done correctly.
    # The data values within the code are ignored, and the Val1 and Val2 values recorded in the correct
    # place used instead.
    # Any values that are treated in a European manner with a comma in place of the decimal point will
    # cause the parsing to fail, unless they are quoted.
    entries = []
    currentEntry = ""
    inQuoteBlock = False
    for i in line:
        if i == ',' and not inQuoteBlock:
            # Found a separator and we aren't in a quote block. Therefore, record the end of the current
            # entry and initialise for the next entry.
            entries.append(currentEntry)
            currentEntry = ""
        elif i in ["'", '"']:
            # Either found the end or the start of a quote block.
            inQuoteBlock = not inQuoteBlock
        else:
            # Either current character is not a comma or we are currently in a quote block as are
            # ignoring commas.
            currentEntry += i
    entries.append(currentEntry)  # Add the final entry to the list of entries.

    # Update the code entry.
    code = entries[1].split(',')[0]  # If the code is recorded with its values, then just get the code.
    if code:
        # There was a code recorded for this association.
        entries[1] = code
    else:
        # There was no code recorded for this association. For example, the association looks like:
        # 3123336,'','2004-11-01',0.0000,0.0000,null
        entries = []

    return entries


def save_patient(patientID, patientData, patientDOB, patientGender, outputFiles, uniqueCodes):
    """Save the history of a given patient in all the desired formats.

    :param patientID:       The ID of the patient.
    :type patientID:        str
    :param patientData:     The patient's history. Each entry will contain a dictionary recording a patient-code as:
                                {"Code": code, "Date": date, "Val1": value1, "Val2": value2}
    :type patientData:      list[dict[str, str]]
    :param patientDOB:      The patient's date of birth.
    :type patientDOB:       datetime.datetime
    :param patientGender:   The gender of the patient. 1 indicates a male and 0 a female.
    :type patientGender:    str
    :param outputFiles:     The locations of the cleaned dataset files.
    :type outputFiles:      dict
    :param uniqueCodes:     The codes that appear associated with a patient in the dataset.
    :type uniqueCodes:      list

    """

    # Process the patient's record.
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
            open(outputFiles["RawData"]["Visits_NC"], 'a') as fidRawVisNC, \
            open(outputFiles["RawData"]["Years_NC"], 'a') as fidRawYearNC:

        # Sort the dates when a patient was associated with a code in order from oldest to newest.
        sortedDates = sorted({i["Date"] for i in patientData})

        # Determine the associations at each time point.
        timePoints = defaultdict(list)
        for i in patientData:
            timePoints[i["Date"]].append(i)

        # Determine the age of the patient when the final association is recorded.
        finalAge = calculate_age(patientDOB, sortedDates[-1], True)

        # Generate the code count and binary indicator data for the patient.
        sumCodeCounts = defaultdict(int)  # Cumulative count of codes seen in the patient's record.
        yearCodeCounts = {}  # Record of the cumulative count of codes seen during each year.
        for i in sortedDates:
            # Calculate the age of the patient at this time point.
            ageAtTimePoint = calculate_age(patientDOB, i, True)

            # If the patient's age has increased since the last time point, then add a new year record.
            if ageAtTimePoint not in yearCodeCounts:
                yearCodeCounts[ageAtTimePoint] = defaultdict(int)

            # Create the record for this time point.
            timePointCounts = defaultdict(int)

            # Identify the codes that were associated with the patient during this time point.
            codesDuringTimePoint = [j["Code"] for j in timePoints[i]]

            # Update the code count records.
            for j in codesDuringTimePoint:
                sumCodeCounts[j] += 1
                yearCodeCounts[ageAtTimePoint][j] += 1
                timePointCounts[j] += 1

            # Write out the visits vectors (cumulative and non-cumulative) for the current time step.
            # The cumulative counts for all time points up to and including this one are stored in sumCodeCounts.
            # The non-cumulative counts (i.e. those for just this time step) are stored in timePointCounts.
            fidCountVisNC.write("{0:s}\t{1:.2f}\t{2:s}\t{3:s}\n".format(
                patientID, ageAtTimePoint, patientGender, '\t'.join([str(timePointCounts[j]) for j in uniqueCodes])
            ))
            fidCountVisC.write("{0:s}\t{1:.2f}\t{2:s}\t{3:s}\n".format(
                patientID, ageAtTimePoint, patientGender, '\t'.join([str(sumCodeCounts[j]) for j in uniqueCodes])
            ))
            fidBinVisNC.write("{0:s}\t{1:.2f}\t{2:s}\t{3:s}\n".format(
                patientID, ageAtTimePoint, patientGender, '\t'.join([str(int(timePointCounts[j] > 0)) for j in uniqueCodes])
            ))
            fidBinVisC.write("{0:s}\t{1:.2f}\t{2:s}\t{3:s}\n".format(
                patientID, ageAtTimePoint, patientGender, '\t'.join([str(int(sumCodeCounts[j] > 0)) for j in uniqueCodes])
            ))

        # Write out the cumulative and non-cumulative year datasets.
        # TODO - go through the year dictionary in order of the ages recorded, summing the results for the cumulative

        # Write out the entire history datasets.
        fidCountHist.write("{0:s}\t{1:.2f}\t{2:s}\t{3:s}\n".format(
            patientID, finalAge, patientGender, '\t'.join([str(sumCodeCounts[i]) for i in uniqueCodes])
        ))
        fidBinHist.write("{0:s}\t{1:.2f}\t{2:s}\t{3:s}\n".format(
            patientID, finalAge, patientGender, '\t'.join([str(int(sumCodeCounts[i] > 0)) for i in uniqueCodes])
        ))
