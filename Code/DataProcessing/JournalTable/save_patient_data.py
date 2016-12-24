"""Function to record the data about a patient in multiple formats."""

# Python imports.
from collections import defaultdict


def main(patientID, patientData, patientGender, outputFiles):
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
        code = i["Code"]
        visit = i["Visit"]
        year = i["Year"]

        # Update event records.
        binHistory.add(code)
        binVisits[visit].add(code)
        binYears[year].add(code)
        ages["Visits"][visit] = age
        countsHistory[code] += 1
        countsVisits[visit][code] += 1
        countsYears[year][code] += 1
        ages["Years"][year] = age
    finalAge = patientData[-1]["Age"]

    # Write out the patient's history information for the non-raw value representations.
    patientInfo = "{:s}:{:s}\t{:s}:{:d}\t{:s}:{:s}\t{:s}\n"
    fidBinHist.write(
        patientInfo.format(
            "_ID", patientID, "_Age", finalAge, "_Gender", patientGender,
            '\t'.join(["{:s}:1".format(i) for i in binHistory])
        )
    )
    binVisitsOutput = ""
    for i in sorted(binVisits):
        binVisitsOutput += patientInfo.format(
            "_ID", patientID, "_Age", ages["Visits"][i], "_Gender", patientGender,
            '\t'.join(["{:s}:1".format(j) for j in binVisits[i]])
        )
    fidBinVis.write(binVisitsOutput)
    binYearsOutput = ""
    for i in sorted(binYears):
        binYearsOutput += patientInfo.format(
            "_ID", patientID, "_Age", ages["Years"][i], "_Gender", patientGender,
            '\t'.join(["{:s}:1".format(j) for j in binYears[i]])
        )
    fidBinYear.write(binYearsOutput)
    fidCountHist.write(
        patientInfo.format(
            "_ID", patientID, "_Age", finalAge, "_Gender", patientGender,
            '\t'.join(["{:s}:{:d}".format(i, countsHistory[i]) for i in countsHistory])
        )
    )
    countVisitsOutput = ""
    for i in sorted(countsVisits):
        countVisitsOutput += patientInfo.format(
            "_ID", patientID, "_Age", ages["Visits"][i], "_Gender", patientGender,
            '\t'.join(["{:s}:{:d}".format(j, countsVisits[i][j]) for j in countsVisits[i]])
        )
    fidCountVis.write(countVisitsOutput)
    countYearsOutput = ""
    for i in sorted(countsYears):
        countYearsOutput += patientInfo.format(
            "_ID", patientID, "_Age", ages["Years"][i], "_Gender", patientGender,
            '\t'.join(["{:s}:{:d}".format(j, countsYears[i][j]) for j in countsYears[i]])
        )
    fidCountYear.write(countYearsOutput)

    # Write out the patient's history information for the raw value representations.
    #fidRawHist.write()
    #fidRawVis.write()
    #fidRawYear.write()
