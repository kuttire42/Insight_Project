"""
HomeSpotter Webapp using Streamlit
"""

import streamlit as st
import config, utilities
import streamlit_utilities as str_util
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import Model, load_model
from PIL import Image

@st.cache
def read_listings():
    """
    Loads home-listings and returns them as a dataframe
    :return: A homelisting dataframe which includes feature embeddings for the home listings
    """
    home_listings_df = pd.read_csv(config.FEATURE_FILE, index_col=0)
    home_listings_df['home_feature'] = home_listings_df.home_feature.apply(utilities.str_to_array)
    home_listings_df['resnet_feature'] = home_listings_df.resnet_feature.apply(utilities.str_to_array)
    home_listings_df = home_listings_df.rename(columns={"URL (SEE http://www.redfin.com/buy-a-home/comparative-market-analysis FOR INFO ON PRICING)": "url",
                                                        "LATITUDE": 'lat',
                                                        "LONGITUDE": 'lon'})
    return home_listings_df


@st.cache
def read_model():
    """
    Loads and returns the Keras model to generate feature embeddings
    :return: Keras model to generate feature embeddings
    """
    # Load our home-style feature model
    home_model = load_model(os.path.sep.join([config.MODEL_PATH, config.MODEL_NAME]))

    # Get home-style features from the model
    home_feature_model = Model(inputs=home_model.input,
                               outputs=home_model.get_layer('dense_4').output)

    return home_feature_model


@st.cache
def get_features_for_image(image_file_name, home_feature_model):
    """
    Returns the feature embeddings for an image using the home_feature_model
    :param image_file_name: Image file (in .jpg or other file formats)
    :param home_feature_model: Keras model to generate feature embeddings
    :return: feature embeddings for the image
    """
    image_pil = Image.open(image_file_name)
    image_pil = image_pil.resize((224, 224))
    image_array = image.img_to_array(image_pil)
    image_array = np.expand_dims(image_array - config.IMG_MEAN, axis=0)  # Shape = (1,222,224,3)
    image_feature = np.ravel(home_feature_model.predict(image_array)).tolist()
    return image_feature

@st.cache
def get_similarities_with_other_listings(home_img_file, home_feature_model, home_listings_df):
    """
    Returns the similarity of the home image with other home listings
    :param home_img_file: Image file (in .jpg or other file formats)
    :param home_feature_model: Keras model to generate feature embeddings
    :param home_listings_df: Homelisting dataframe which includes feature embeddings for the home listings
    :return: A 1-D numpy array of similarity values
    """
    home_embedding = get_features_for_image(home_img_file, home_feature_model)
    return (np.ravel(cosine_similarity(np.reshape(home_embedding, [1, -1]),
                               np.vstack(home_listings_df.home_feature))))


@st.cache
def get_home_stats(listings_df):
    """
    :param listings_df: Dataframe containing home listings
    :return: Returns a dictionary with various home stats
    """
    home_stats = {}
    home_stats['Avg Days on Market'] = listings_df['DAYS ON MARKET'].mean()
    home_stats['Earliest Year Built'] = listings_df['YEAR BUILT'].min()
    home_stats['Latest Year Built'] = listings_df['YEAR BUILT'].max()
    home_stats['Min Price'] = listings_df['PRICE'].min()
    home_stats['Max Price'] = listings_df['PRICE'].max()
    return home_stats

def main():

    go_to_homepage = st.sidebar.button("Go to Home-page")
    similarity_value = st.sidebar.slider('Home Similarity Threshold', 0.0, 1.0, config.SIMILARITY_DEFAULT)

    st.title('HomeSpotter')

    # Load up the model and listings information at the beginning itself
    home_model = read_model()
    home_listings_df = read_listings()

    # User uploads picture
    uploaded_file = st.file_uploader("Upload Home Image...", type="jpg")

    if uploaded_file is not None:

        #home_image = image.load_img(uploaded_file)

        # Get feature embedding for uploaded home with other listings
        home_similarities = get_similarities_with_other_listings(uploaded_file,
                                                                 home_model,
                                                                 home_listings_df)

        # Only show listings with similarity above user-selected threshold
        filtered_indices = np.ravel(np.argwhere(home_similarities > similarity_value))
        home_similarities_filtered = home_similarities[filtered_indices]
        sorted_similarity_arg = np.ravel(np.flip(np.argsort(home_similarities_filtered)))
        filtered_indices = filtered_indices[sorted_similarity_arg]
        home_similarities_filtered = home_similarities_filtered[sorted_similarity_arg]

        home_stats = get_home_stats(home_listings_df.iloc[filtered_indices, :])
        plt.figure()
        plt.hist(home_listings_df.iloc[filtered_indices, :].loc[:, 'PRICE'].values, 20)
        plt.xlabel('Home Prices')
        plt.ylabel('Number of Houses')
        plt.savefig('temp_fig.jpg')

        # Plot the uploaded picture along with some statistics of similar houses
        str_util.set_block_container_style()
        with str_util.Grid("1 1 1", color=str_util.COLOR, background_color=str_util.BACKGROUND_COLOR) as grid:
            grid.cell(
                class_="a",
                grid_column_start=1,
                grid_column_end=2,
                grid_row_start=1,
                grid_row_end=2,
            ).image_from_iostream(uploaded_file, image_size=350)
            grid.cell("b", 2, 4, 1, 2).print_home_stats(home_stats)
            grid.cell("c", 4, 5, 1, 2).image_from_file('temp_fig.jpg', image_size=350)

        # Plot a map with the selected home-listings
        st.map(home_listings_df.iloc[filtered_indices, :].loc[:, ['lat', 'lon']])

        # Give details of each selected home-listing
        for iv, ii in enumerate(filtered_indices):

            # Remove the same house listing
            if abs(home_similarities_filtered[iv] - 1.0) <= 1e-10:
                continue
            similar_home_index = home_listings_df.index[ii]
            type(similar_home_index)
            similar_home_file = os.path.sep.join([config.LISTINGS_PATH, similar_home_index+'.jpg'])
            #similar_home_img = image.load_img(similar_home_file, target_size=(224,224))
            #st.image(similar_home_img)

            with str_util.Grid("1 1 1 1", color=str_util.COLOR, background_color=str_util.BACKGROUND_COLOR) as grid:
                grid.cell(
                    class_="a",
                    grid_column_start=1,
                    grid_column_end=2,
                    grid_row_start=1,
                    grid_row_end=2,
                ).image_from_file(similar_home_file)
                grid.cell("b", 2, 4, 1, 2).print_home_details(home_listings_df.iloc[ii, :])

if __name__ == "__main__":
    main()