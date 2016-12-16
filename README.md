# MedicalRecordAnalysis

## Datasets Generated

The datasets generated can be split based on the type of data recorded and how the time steps are determined.
For the type of data recorded, there are two categories:

1. Code counts
    - Code counts represent a patient's history in a given time step by counting the number of times each code is associated with the patient during the time step.
    - For example, a patient's vector in a given time step may be [1, 0, 0, 2, 0] indicating that they have 1 association with code 1, 2 with code 4 and none with codes 2, 3 and 5 during the time step.
    - Patient age and gender are also included in the vector.
2. Binary indicators
    - Binary indicators represent a patient's history in a given time step by recording a 1 for codes associated with the patient during the time step and a 0 otherwise.
    - For example, a patient's vector in a given time step may be [1, 0, 0, 1, 0] indicating that they have an association with codes 1 and 4 and none with codes 2, 3 and 5 during the time step.
    - Patient age and gender are also included in the vector.

The time steps can be determined using one of three methods:

1. Entire histories - use the entire patient's history as a single time step. Patients will all have one time step.
    - Each patient in the dataset is represented by one vector.
    - Patients all have the same number of time steps (1).
    - The age recorded for the patient is the age of their last measurement.
    - This approach is not used with raw data measurements.
2. Patient visits
    - Each patient in the dataset is broken down into time steps bassed on the different dates when code were associated with them. As data is all primary care, this is essentially breaking down the history into visits to a GP (or possibly lab test results).
    - There is no expectation that patients will have the same number of time steps.
    - This approach lends itself to two subdivisions:
        1. Non-cumulative
            - Each time step is treated in isolation.
            - For example, if a patient is associated with codes 1 and 3 during their first visit and 3 and 4 during their second, then the vectors for the patient would be [1, 0, 1, 0] and [0, 0, 1, 1] (for both the code count and binary indicator methods).
        2. Cumulative
            - Values are accumulated over subsequent time steps.
            - For example, if using the visits from the non-cumulative example, the patient's vectors would be [1, 0, 1, 0] and [1, 0, 2, 1] for the code count method and [1, 0, 1, 0] and [1, 0, 1, 1] for the binary indicator method.
            - This approach is not used with raw data measurements.
3. Years
    - The history of each patient in the dataset is broken down based on the years of their life, with one time step per year. This essentially combines all data for a patient within one year to attempt to fill out the sparseness of the records.
    - There is no expectation that patients will have the same number of time steps.
    - This approach lends itself to two subdivisions:
        1. Non-cumulative
            - Each time step is treated in isolation.
            - For example, if a patient is associated with codes 1 and 3 during their first year of life and 3 and 4 during their second, then the vectors for the patient would be [1, 0, 1, 0] and [0, 0, 1, 1] (for both the code count and binary indicator methods).
        2. Cumulative
            - Values are accumulated over subsequent time steps.
            - For example, if using the codes from the non-cumulative example, the patient's vectors would be [1, 0, 1, 0] and [1, 0, 2, 1] for the code count method and [1, 0, 1, 0] and [1, 0, 1, 1] for the binary indicator method.
            - This approach is not used with raw data measurements.

Combined, these possibilities give ten datasets:

1. Code counts + Entire histories (CodeCount_History.tsv)
2. Code counts + Non-cumulative patient visits (CodeCount_Visits_NC.tsv)
3. Code counts + Cumulative patient visits (CodeCount_Visits_C.tsv)
4. Code counts + Non-cumulative years (CodeCount_Years_NC.tsv)
5. Code counts + Cumulative years (CodeCount_Years_C.tsv)
6. Binary indicators + Entire histories (BinaryIndicator_History.tsv)
7. Binary indicators + Non-cumulative patient visits (BinaryIndicator_Visits_NC.tsv)
8. Binary indicators + Cumulative patient visits (BinaryIndicator_Visits_C.tsv)
9. Binary indicators + Non-cumulative years (BinaryIndicator_Years_NC.tsv)
10. Binary indicators + Cumulative years (BinaryIndicator_Years_C.tsv)


Notes

- As the date of birth is only given by the year (i.e. it is a year of birth), all ages are calculated as if the patient's birthday was January 1st of the year they were born.