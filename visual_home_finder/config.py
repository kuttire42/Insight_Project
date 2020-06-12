"""
Contains path-names, environment variables for the project
"""

import os
import numpy as np

# Iamge Size: This can vary according to the model that is used. Resnet: 224, Inception: 229
IMAGE_SIZE = 224

# Path to original data files
ORIG_INPUT_DIR = "../data/raw/home_images"

# Defining paths to store training/ validation and test directories
BASE_PATH = "../data/processed"

TRAIN_PATH = os.path.sep.join([BASE_PATH, "training"])
VAL_PATH = os.path.sep.join([BASE_PATH, "validation"])
TEST_PATH = os.path.sep.join([BASE_PATH, "test"])

# PATH to save model
MODEL_PATH = '../visual_home_finder'

# PATH to house listings
LISTINGS_PATH = '../data/raw/house_listings'

# PATH to save home features
FEATURE_PATH = os.path.sep.join([BASE_PATH, "home_features"])

# define the amount of data that will be used training
TRAIN_SPLIT = 0.8

# the percentage of validation data will be a percentage of the
VAL_SPLIT = 0.1

# define the names of the classes
#CLASSES = ["cape_cod", "colonial", 'craftsman', 'modern', 'ranch', 'tudor', 'victorian']
CLASSES = ['craftsman', 'modern', 'ranch', 'tudor', 'victorian']

# Name of model
#MODEL_NAME = 'eighth_model_50epochs_5classes.h5'
MODEL_NAME = 'sixth_model_50epochs_5classes_redo.h5'

# Mean and STD of all the training images
IMG_MEAN = np.array([123.526794, 129.04448, 119.95359], dtype=np.float32).reshape((1, 1, 3))
IMG_STD = 62  # np.array([62.082836, 61.87381, 73.08175], dtype=np.float32).reshape((1,1,3))

# Name of CSV file with house-listing embeddings
FEATURE_FILE = os.path.sep.join([FEATURE_PATH, "home_features_model_6.csv"])

# Name of the pickle file with PCA model
PCA_MODEL = os.path.sep.join([MODEL_PATH, "home_pca.sav"])

# Name of the pickle file with TSNE model
TSNE_MODEL = os.path.sep.join([MODEL_PATH, "home_tsne.sav"])

# Name of the Pyplot figure with house class clusters
CLUSTER_PLT = os.path.sep.join([MODEL_PATH, "home_clusters_plt.sav"])

# Name of the pickle containing features dataframe of all homes for TSNE
ALL_FEATURES_DF = os.path.sep.join([MODEL_PATH, "home_features_np.sav"])

## Some default values for the web-app

# Default value for the home similarity index: controls the number of listings shown on the page
SIMILARITY_DEFAULT = 0.75
