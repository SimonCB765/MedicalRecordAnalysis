"""Code to initiate the processing of the QICKD SQL files and generation of the datasets."""

# Python imports.
import sys

# User imports.
from . import generate_dataset_from_sql


generate_dataset_from_sql.main(sys.argv[1])