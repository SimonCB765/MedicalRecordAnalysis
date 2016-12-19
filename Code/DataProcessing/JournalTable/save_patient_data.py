"""Function to record the data about a patient in multiple formats."""

# Python imports.
from collections import defaultdict


def main(patientID, patientData, patientGender, outputFiles, numCodes):
    """Save the history of a given patient in all the desired formats.

    :param patientID:       The ID of the patient.
    :type patientID:        str
    :param patientData:     The patient's history. The history will be sorted from oldest event to most recent.
                                Each entry will contain a dictionary recording a patient-code as:
                                {"Age": int, "CodeIndex": str, "Val1": float, "Val2": float, "Visit": int, "Year": int}
    :type patientData:      list[dict]
    :param patientGender:   The gender of the patient ('M' or 'F').
    :type patientGender:    str
    :param outputFiles:     The locations of the cleaned dataset files.
    :type outputFiles:      dict
    :param numCodes:        The number of codes in the dataset.
    :type numCodes:         int

    """

    # Get the file handles.
    fidBinHist = outputFiles["BinaryIndicator"]["History"]
    fidBinVis = outputFiles["BinaryIndicator"]["Visits"]
    fidBinYear = outputFiles["BinaryIndicator"]["Years"]
    fidCountHist = outputFiles["CodeCount"]["History"]
    fidCountVis = outputFiles["CodeCount"]["Visits"]
    fidCountYear = outputFiles["CodeCount"]["Years"]
    fidRawHist = outputFiles["RawData"]["History"]
    fidRawVis = outputFiles["RawData"]["Visits"]
    fidRawYear = outputFiles["RawData"]["Years"]

    # Extract the needed information about the patient's history and format it.
    binHistory = set()
    binVisits = defaultdict(set)
    binYears = defaultdict(set)
    countsHistory = defaultdict(int)
    countsVisits = defaultdict(lambda: defaultdict(int))
    countsYears = defaultdict(lambda: defaultdict(int))
    ages = {"Visits": {}, "Years": {}}
    for i in patientData:
        # Extract information about the event.
        age = i["Age"]
        codeIndex = i["CodeIndex"]
        visit = i["Visit"]
        year = i["Year"]

        # Update event records.
        binHistory.add(codeIndex)
        binVisits[visit].add(codeIndex)
        binYears[year].add(codeIndex)
        ages["Visits"][visit] = age
        countsHistory[codeIndex] += 1
        countsVisits[visit][codeIndex] += 1
        countsYears[year][codeIndex] += 1
        ages["Years"][year] = age
    finalAge = patientData[-1]["Age"]

    # Write out the patient's history information.
    patientInfo = "{:s}\t{:d}\t{:s}\t{:d}\t{:s}\n"
    fidBinHist.write(
        patientInfo.format(
            patientID, finalAge, patientGender, numCodes, ','.join(["{:s}:1".format(i) for i in binHistory])
        )
    )
    binVisitsOutput = ""
    for i in sorted(binVisits):
        binVisitsOutput += patientInfo.format(
            patientID, ages["Visits"][i], patientGender, numCodes,
            ','.join(["{:s}:1".format(j) for j in binVisits[i]])
        )
    fidBinVis.write(binVisitsOutput)
    binYearsOutput = ""
    for i in sorted(binYears):
        binYearsOutput += patientInfo.format(
            patientID, ages["Years"][i], patientGender, numCodes,
            ','.join(["{:s}:1".format(j) for j in binYears[i]])
        )
    fidBinYear.write(binYearsOutput)
    fidCountHist.write(
        patientInfo.format(
            patientID, finalAge, patientGender, numCodes, ','.join(["{:s}:1".format(i) for i in countsHistory])
        )
    )
    countVisitsOutput = ""
    for i in sorted(countsVisits):
        countVisitsOutput += patientInfo.format(
            patientID, ages["Visits"][i], patientGender, numCodes,
            ','.join(["{:s}:1".format(j) for j in countsVisits[i]])
        )
    fidCountVis.write(countVisitsOutput)
    countYearsOutput = ""
    for i in sorted(countsYears):
        countYearsOutput += patientInfo.format(
            patientID, ages["Years"][i], patientGender, numCodes,
            ','.join(["{:s}:1".format(j) for j in countsYears[i]])
        )
    fidCountYear.write(countYearsOutput)
    #fidRawHist.write()
    #fidRawVis.write()
    #fidRawYear.write()
