# Notebooks to create, analyze and test classification models and image-embedding generators

## Using the pipeline with Resnet50

- home_classifer_resnet50.ipynb: Create a home-style classifier using transfer learning from Resnet50
- home_feature_generator.ipynb: Used the trained classification model to generate embeddings for home-listings as well
as test images
- home_class_clusters.ipynb: Uses PCA and t-SNE clustering of image-embeddings to visualize difference classes of homes
- home_recommender.ipynb: Uses image embeddings and cosine similarity to recommend homes. Also visualizes home
embeddings in a 2D space.
- review_incorrect_test_images.ipynb: Shows examples of incorrect home style classifications

## Using the pipeline with Autoencoders

- home_embedding_autoencoder.ipynb: Autoencoder model to directly generate home embedding
- test_autoencoder_model.ipynb: Tests the autom-embeddings from the Autoencoder model
- home_feature_generator_using_autoencoder.ipynb: Used the Autoencoder model to generate embeddings for
home-listings as well as test images
- home_recommender_using_autoencoder.ipynb: Uses image embeddings (from Autoencoder) and cosine similarity to recommend
homes. Also visualizes home
embeddings in a 2D space.


## Model using InceptionV3

- home_classifer_inceptionv3.ipynb: Create a home-style classifier using transfer learning from InceptionV3

## Archive Folder (unused scripts)

Contains random scripts used for playing and testing







