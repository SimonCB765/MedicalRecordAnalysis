# MedicalRecordAnalysis

# Datasets Generated

7 datasets are generated. For all except CountMatrix.tsv, each patient has the same number of entries as they have 
distinct dated associations.

1. CodesPerTimePoint.tsv - Each entry records the codes that were associated with the patient during the dated association.

2. CodesPerTimePoint_Rebased.tsv - Same as 1, but the date is rebased.

3. CountMatrix.tsv - Each patient has one entry that contains a vector of their entire history.

4. CountMatrix_Binary.tsv - Same as 3, but the counts are converted to binary indicators.

5. CountsSummedOverTime.tsv - Each entry records the sum of all codes associated with that patient up to and including 
the current time point.

6. CountsSummedOverTime_Binary.tsv - Each entry records whether a code has been assocated with the patient up to and 
including the current time point.

7. CountsSummedOverTime_Rebased.tsv - Same as 4, but the date is rebased.

8. CountsSummedOverTime_Rebased_Binary.tsv - Same as 5, but the date is rebased.

9. PatientDetails.tsv - The DOB, gender and disease classifications of each patient.