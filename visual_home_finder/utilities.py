"""
Common functions used by notebooks and other scripts
"""

import os
import config
import numpy as np

from tensorflow.keras.models import Model, load_model
from tensorflow.keras.applications import ResNet50
from tensorflow.keras.preprocessing import image
from PIL import Image


def home_model():
    """
    Returns the home CNN model that we built to classify home styles.
    Takes a while to load. Do not call often. Best to get the model and cache result.
    """
    # Loading our home-style feature model
    home_model_instance = load_model(os.path.sep.join([config.MODEL_PATH, config.MODEL_NAME]))

    return home_model_instance


def home_feature_model():
    """
    Returns the home feature CNN model that we built to generate home feature embeddings
    Takes a while to load. Do not call often. Best to get the model and cache result.
    """
    # Loading our home-style feature model
    home_model = load_model(os.path.sep.join([config.MODEL_PATH, config.MODEL_NAME]))

    # Get home-style features from the model
    our_feature_model = Model(inputs=home_model.input,
                               outputs=home_model.get_layer('dense_4').output)

    return our_feature_model


def resnet50_feature_model():
    """
    Returns the Resnet50 feature model that generates home feature embeddings
    Takes a while to load.  Do not call often. Best to get the model and cache result.
    """
    # Load Resnet50
    resnet_model = ResNet50()

    # Build a feature model by removing the final classification layer
    resnet_feature_model = Model(inputs=resnet_model.input,
                                 outputs=resnet_model.get_layer('avg_pool').output)

    return resnet_feature_model


def get_features_for_image(image_file_name, feature_model):
    """
    Returns the feature embeddings for an image using the home_feature_model
    :param image_file_name: Image file (in .jpg or other file formats). Can also be IObytes (directly from web)
    :param feature_model: Keras model to generate feature embeddings
    :return: feature embeddings for the image
    """

    image_pil = Image.open(image_file_name)  # We are using PIL since keras image does not support IOBytes Tensorflow
    #  2.2 onwards
    image_pil = image_pil.resize((config.IMAGE_SIZE, config.IMAGE_SIZE))
    image_array = image.img_to_array(image_pil)[..., :3]  # Some image types such as png have 4 channels (additional
    # transparency channel. Remove fourth and only keep first 3 RGB channels
    image_array = np.expand_dims(image_array - config.IMG_MEAN, axis=0)  # Shape = (1,222,224,3)
    image_feature = np.ravel(feature_model.predict(image_array)).tolist()
    return image_feature


def get_features_for_image_with_scaling(image_file_name, feature_model):
    """
    Returns the feature embeddings for an image using the home_feature_model. Instead of subtracting mean,
    this scales the image values so that its between 0 and 1
    :param image_file_name: Image file (in .jpg or other file formats). Can also be IObytes (directly from web)
    :param feature_model: Keras model to generate feature embeddings
    :return: feature embeddings for the image
    """

    image_pil = Image.open(image_file_name)  # We are using PIL since keras image does not support IOBytes Tensorflow
    #  2.2 onwards
    image_pil = image_pil.resize((config.IMAGE_SIZE, config.IMAGE_SIZE))
    image_array = image.img_to_array(image_pil)[..., :3]  # Some image types such as png have 4 channels (additional
    # transparency channel. Remove fourth and only keep first 3 RGB channels
    image_array = np.expand_dims(image_array/256, axis=0)  # Shape = (1,222,224,3)
    image_feature = np.ravel(feature_model.predict(image_array)).tolist()
    return image_feature


def str_to_array(string_numpy):
    """formatting : Conversion of String List to List

    Args:
        string_numpy (str)
    Returns:
        l (list): list of values
    """
    list_values = string_numpy.split(", ")
    list_values[0] = list_values[0][2:]
    list_values[-1] = list_values[-1][:-2]
    return list_values


