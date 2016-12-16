"""Function to record the data about a patient in multiple formats."""

# Python imports.
from collections import defaultdict

# User imports.
from Utilities import calculate_age


def main(patientID, patientData, patientDOB, patientGender, outputFiles, uniqueCodes):
    """Save the history of a given patient in all the desired formats.

    :param patientID:       The ID of the patient.
    :type patientID:        str
    :param patientData:     The patient's history. Each entry will contain a dictionary recording a patient-code as:
                                {"Code": code, "Date": date, "Val1": value1, "Val2": value2}
    :type patientData:      list[dict[str, str]]
    :param patientDOB:      The patient's date of birth.
    :type patientDOB:       datetime.datetime
    :param patientGender:   The gender of the patient ('M' or 'F').
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
            open(outputFiles["RawData"]["History"], 'a') as fidRawHist, \
            open(outputFiles["RawData"]["Visits_NC"], 'a') as fidRawVisNC, \
            open(outputFiles["RawData"]["Visits_C"], 'a') as fidRawVisC, \
            open(outputFiles["RawData"]["Years_NC"], 'a') as fidRawYearNC, \
            open(outputFiles["RawData"]["Years_C"], 'a') as fidRawYearC:

        # Sort the dates when a patient was associated with a code in order from oldest to newest.
        sortedDates = sorted({i["Date"] for i in patientData})

        # Determine the (potentially multiple) associations present at each time point.
        timePoints = defaultdict(list)
        for i in patientData:
            timePoints[i["Date"]].append(i)

        # Determine the age of the patient when the final association was recorded.
        finalAge = calculate_age.main(patientDOB, sortedDates[-1], True)

        # Generate the code count and binary indicator data for the patient.
        sumCodeCounts = defaultdict(int)  # Cumulative count of codes seen in the patient's record.
        yearCodeCounts = {}  # Record of the cumulative count of codes seen during each year.
        for i in sortedDates:
            # Calculate the age of the patient at this time point.
            ageAtTimePoint = calculate_age.main(patientDOB, i, True)
            ageInYears = calculate_age.main(patientDOB, i, False)  # Get the age of the patient in years.

            # If the patient's age has increased since the last time point, then add a new year record.
            if ageInYears not in yearCodeCounts:
                yearCodeCounts[ageInYears] = defaultdict(int)

            # Create the record for this time point.
            timePointCounts = defaultdict(int)

            # Identify the codes that were associated with the patient during this time point.
            codesDuringTimePoint = [j["Code"] for j in timePoints[i]]

            # Update the code count records.
            for j in codesDuringTimePoint:
                sumCodeCounts[j] += 1
                yearCodeCounts[ageInYears][j] += 1
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
                patientID, ageAtTimePoint, patientGender,
                '\t'.join([str(1 if timePointCounts[j] > 0 else -1) for j in uniqueCodes])
            ))
            fidBinVisC.write("{0:s}\t{1:.2f}\t{2:s}\t{3:s}\n".format(
                patientID, ageAtTimePoint, patientGender,
                '\t'.join([str(1 if sumCodeCounts[j] > 0 else -1) for j in uniqueCodes])
            ))

        # Write out the cumulative and non-cumulative year datasets.
        sumYearCounts = defaultdict(int)  # Cumulative counts of codes across years.
        for i in sorted(yearCodeCounts):
            for j in yearCodeCounts[i]:
                # Add the total number of associations between the patient and code j in year i to the cumulative total.
                sumYearCounts[j] += yearCodeCounts[i][j]

            # Record the data.
            fidCountYearNC.write("{0:s}\t{1:.2f}\t{2:s}\t{3:s}\n".format(
                patientID, i, patientGender, '\t'.join([str(yearCodeCounts[i][j]) for j in uniqueCodes])
            ))
            fidCountYearC.write("{0:s}\t{1:.2f}\t{2:s}\t{3:s}\n".format(
                patientID, i, patientGender, '\t'.join([str(sumYearCounts[j]) for j in uniqueCodes])
            ))
            fidBinYearNC.write("{0:s}\t{1:.2f}\t{2:s}\t{3:s}\n".format(
                patientID, i, patientGender,
                '\t'.join([str(1 if yearCodeCounts[i][j] > 0 else -1) for j in uniqueCodes])
            ))
            fidBinYearC.write("{0:s}\t{1:.2f}\t{2:s}\t{3:s}\n".format(
                patientID, i, patientGender, '\t'.join([str(1 if sumYearCounts[j] > 0 else -1) for j in uniqueCodes])
            ))

        # Write out the entire history datasets.
        fidCountHist.write("{0:s}\t{1:.2f}\t{2:s}\t{3:s}\n".format(
            patientID, finalAge, patientGender, '\t'.join([str(sumCodeCounts[i]) for i in uniqueCodes])
        ))
        fidBinHist.write("{0:s}\t{1:.2f}\t{2:s}\t{3:s}\n".format(
            patientID, finalAge, patientGender, '\t'.join([str(1 if sumCodeCounts[i] > 0 else -1) for i in uniqueCodes])
        ))
