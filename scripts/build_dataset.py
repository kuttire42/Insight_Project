"""
Split images from directory in to training/ validation and test data-sets
"""

from visual_home_finder import config, paths
import random
import shutil
import os

# Retrieve paths to all images and shuffle their order
image_paths = list(paths.list_images(config.ORIG_INPUT_DIR))
random.seed(13)
random.shuffle(image_paths)

# Calculate the training and test data split
i = int(len(image_paths) * config.TRAIN_SPLIT)
train_paths = image_paths[:i]
test_paths = image_paths[i:]

# Calculate the training and validation data split
i = int(len(train_paths) * config.VAL_SPLIT)
val_paths = train_paths[:i]
train_paths = train_paths[i:]

# define the datasets that we'll be building
datasets = [
    ("training", train_paths, config.TRAIN_PATH),
    ("validation", val_paths, config.VAL_PATH),
    ("testing", test_paths, config.TEST_PATH)
]

# loop over the datasets
for (dType, imagePaths, baseOutput) in datasets:

    print("[INFO] building '{}' split".format(dType))
    # if the output base output directory does not exist, create it
    if not os.path.exists(baseOutput):
        print("[INFO] 'creating {}' directory".format(baseOutput))
        os.makedirs(baseOutput)

    # loop over the input image paths
        for inputPath in imagePaths:

            # extract the filename of the input image along with class label
            filename = inputPath.split(os.path.sep)[-1]
            label = inputPath.split(os.path.sep)[-2]

            # build the path to the label directory
            labelPath = os.path.sep.join([baseOutput, label])

            # if the label output directory does not exist, create it
            if not os.path.exists(labelPath):
                print("[INFO] 'creating {}' directory".format(labelPath))
                os.makedirs(labelPath)

            # construct the path to the destination image and then copy image
            p = os.path.sep.join([labelPath, filename])
            shutil.copy2(inputPath, p)

# Display the number of files in each folder (need to install package tree for mac using brew install tree)
os.system("tree {} --filelimit 10".format(config.BASE_PATH))