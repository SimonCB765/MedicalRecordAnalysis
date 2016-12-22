"""Function to record the data about a patient in multiple formats."""

# Python imports.
from collections import defaultdict


def main(patientID, patientData, patientGender, outputFiles, bowVarMapping, rawVarMapping):
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
    :param bowVarMapping:   A mapping from variables in the bag of words representation to their indices.
    :type bowVarMapping:    dict
    :param rawVarMapping:   A mapping from variables in the raw value representation to their indices.
    :type rawVarMapping:    dict

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

    # Write out the patient's history information for the non-raw value representations.
    patientInfo = "{:s}\t{:d}:{:d},{:d}:{:s},{:s}\n"
    fidBinHist.write(
        patientInfo.format(
            patientID, bowVarMapping["_Age"], finalAge, bowVarMapping["_Gender"], patientGender,
            ','.join(["{:d}:1".format(bowVarMapping[i]) for i in binHistory])
        )
    )
    binVisitsOutput = ""
    for i in sorted(binVisits):
        binVisitsOutput += patientInfo.format(
            patientID, bowVarMapping["_Age"], ages["Visits"][i], bowVarMapping["_Gender"], patientGender,
            ','.join(["{:d}:1".format(bowVarMapping[j]) for j in binVisits[i]])
        )
    fidBinVis.write(binVisitsOutput)
    binYearsOutput = ""
    for i in sorted(binYears):
        binYearsOutput += patientInfo.format(
            patientID, bowVarMapping["_Age"], ages["Years"][i], bowVarMapping["_Gender"], patientGender,
            ','.join(["{:d}:1".format(bowVarMapping[j]) for j in binYears[i]])
        )
    fidBinYear.write(binYearsOutput)
    fidCountHist.write(
        patientInfo.format(
            patientID, bowVarMapping["_Age"], finalAge, bowVarMapping["_Gender"], patientGender,
            ','.join(["{:d}:{:d}".format(bowVarMapping[i], countsHistory[i]) for i in countsHistory])
        )
    )
    countVisitsOutput = ""
    for i in sorted(countsVisits):
        countVisitsOutput += patientInfo.format(
            patientID, bowVarMapping["_Age"], ages["Visits"][i], bowVarMapping["_Gender"], patientGender,
            ','.join(["{:d}:{:d}".format(bowVarMapping[j], countsVisits[i][j]) for j in countsVisits[i]])
        )
    fidCountVis.write(countVisitsOutput)
    countYearsOutput = ""
    for i in sorted(countsYears):
        countYearsOutput += patientInfo.format(
            patientID, bowVarMapping["_Age"], ages["Years"][i], bowVarMapping["_Gender"], patientGender,
            ','.join(["{:d}:{:d}".format(bowVarMapping[j], countsYears[i][j]) for j in countsYears[i]])
        )
    fidCountYear.write(countYearsOutput)

    # Write out the patient's history information for the raw value representations.
    #fidRawHist.write()
    #fidRawVis.write()
    #fidRawYear.write()
