"""Code to initiate the processing of the QICKD SQL files and generation of the datasets."""

# Python imports.
import argparse
import os
import shutil
import sys

# User imports.
if __package__ != "DataParsing":
    # The code was not called from within the Code directory using 'python -m DataParsing'.
    # Therefore, we need to add the top level Code directory in order to use absolute imports.
    currentDir = os.path.dirname(os.path.join(os.getcwd(), __file__))  # Directory containing this file.
    codeDir = os.path.abspath(os.path.join(currentDir, os.pardir))
    sys.path.append(codeDir)
from DataParsing import generate_dataset_from_sql


# ====================== #
# Create Argument Parser #
# ====================== #
parser = argparse.ArgumentParser(description="Generate processed datafiles from SQL database files of patients.",
                                 epilog="")

# Optional arguments.
parser.add_argument("-i", "--ignore",
                    help="The location of the file containing the codes that should be ignored and not used to create "
                         "the final datasets. Default: a file called IgnoredCodes.txt in the Data drectory.",
                    type=str)
parser.add_argument("-o", "--output",
                    help="The location of the directory to write the output files to. Default: a directory called "
                         "ProcessedData within the same directory that the SQL file directory is found.",
                    type=str)
parser.add_argument("-s", "--sqlFiles",
                    help="The location of the directory to containing the SQL files to use. Default: a directory "
                         "called QICKDDatabase/SQLData in the Data directory.",
                    type=str)
parser.add_argument("-w", "--overwrite",
                    action="store_true",
                    help="Whether the output directory should be overwritten if it exists. Default: do not overwrite.")

# ============================ #
# Parse and Validate Arguments #
# ============================ #
args = parser.parse_args()
dirCurrent = os.path.dirname(os.path.join(os.getcwd(), __file__))  # Directory containing this file.
dirTop = os.path.abspath(os.path.join(dirCurrent, os.pardir, os.pardir))
dirData = os.path.abspath(os.path.join(dirTop, "Data"))
errorsFound = []  # Container for any error messages generated during the validation.

# Validate the SQL file directory.
dirSQLFiles = os.path.join(dirData, "QICKDDatabase", "SQLData")
dirSQLFiles = args.sqlFiles if args.sqlFiles else dirSQLFiles
if not os.path.isdir(dirSQLFiles):
    errorsFound.append("The directory containing the SQL files does not exist.")

# Validate the output directory.
dirOutput = os.path.abspath(os.path.join(dirSQLFiles, os.pardir, "ProcessedData"))
dirOutput = args.output if args.output else dirOutput
overwrite = args.overwrite
if overwrite:
    try:
        shutil.rmtree(dirOutput)
    except FileNotFoundError:
        # Can't remove the directory as it doesn't exist.
        pass
    except Exception as e:
        # Can't remove the directory for another reason.
        errorsFound.append("Could not overwrite the output directory location - {0:s}".format(str(e)))
elif os.path.exists(dirOutput):
    errorsFound.append("The output directory location already exists and overwriting is not enabled.")

# Validate the code ignore file.
fileIgnoreCodes = os.path.join(dirData, "IgnoredCodes.txt")
fileIgnoreCodes = args.ignore if args.ignore else fileIgnoreCodes
if not os.path.exists(fileIgnoreCodes):
    errorsFound.append("The location of the file containing the codes to ignore does not exist.")
elif not os.path.isfile(fileIgnoreCodes):
    errorsFound.append("The location of the file containing the codes to ignore is not a file.")

# Display errors if any were found.
if errorsFound:
    print("\n\nThe following errors were encountered while parsing the input arguments:\n")
    print('\n'.join(errorsFound))
    sys.exit()

# Only create the output directory if there were no errors encountered.
try:
    os.makedirs(dirOutput, exist_ok=True)  # Attempt to make the output directory. Don't care if it already exists.
except Exception as e:
    print("\n\nThe following errors were encountered while parsing the input arguments:\n")
    print("The output directory could not be created - {0:s}".format(str(e)))
    sys.exit()

# ============================ #
# Generate the Processed Files #
# ============================ #
generate_dataset_from_sql.main(dirSQLFiles, dirOutput, fileIgnoreCodes)
