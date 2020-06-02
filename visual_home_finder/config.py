"""
Contains path-names, environment variables for the project
"""

import os

# Path to original data files
ORIG_INPUT_DIR = "../data/raw/home_images"

# Defining paths to store training/ validation and test directories
BASE_PATH = "../data/processed"

TRAIN_PATH = os.path.sep.join([BASE_PATH, "training"])
VAL_PATH = os.path.sep.join([BASE_PATH, "validation"])
TEST_PATH = os.path.sep.join([BASE_PATH, "test"])

# PATH to save model
MODEL_PATH = '../visual_home_finder/model'

# define the amount of data that will be used training
TRAIN_SPLIT = 0.8

# the percentage of validation data will be a percentage of the
VAL_SPLIT = 0.1

# define the names of the classes
CLASSES = ["capecod", "colonial", 'craftsman', 'modern', 'ranch', 'tudor', 'victorian']



