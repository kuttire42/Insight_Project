# HomeSpotter
Web-app that Curates home-listings by Visual Style using Deep Learning

## What does the App do?
User uploads a picture of a home (image of the outside of a home) that they really like. The app returns home-listings
in the Seattle are have a similar visual style as the uploaded picture.

Note that the returned listings are static listings that were downloaded from Redfin in May-June 2020. The app is
not intended to be a stand-alone app. Rather it is intended to be a POC for a feature that home-listing search engines
could incorporate.

## Functional Building Blocks

- Creates image embeddings for each home-listings
- When the user uploads a picture, creates a image embedding for the uploaded picture
- Finds the most similar home-listing by comparing the image embedding of the uploaded picture with the
image-embeddings of the home-listings.
- Image embeddings are created as follows
-- Transfer learning from a pre-trained Resnet50 architecture is used
-- A classifier for classifying between different home-styles is built on top of the Resnet50. The output of the second
last layer of Resnet50 is used as an input to the classifier.
-- Although we build a classifier, we do not use the output of the classifier. Instead, we use the output of the second
last layer as the Image embedding.

## Packages used

- Streamlit
- Sklearn
- Tensorflow (and Tensorflow keras)
- Pillow

## More information
More information about the App can be found in the slides at https://bit.ly/rm_insight20b_42
The app is hosted at: http://www.datastory.work:8501/
A demo of the app is available at https://youtu.be/qbgyS_FKa8g

## Description of Folders

- data: Contains data used for training/testing the recommendation model as well as home-listings used for
recommendations
- notebooks: Contains notebooks used to build and test the recommendation model
- scripts: Contains scripts for scraping images from google as well as splitting images in to training and test
sets
-visual_home_finder: Contains source code for the Streamlit app HomeSpotter

