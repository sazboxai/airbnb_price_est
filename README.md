# Airbnb Price Estimation

## Project Overview
This project aims to help Airbnb hosts estimate the optimal listing price based on various property characteristics such as location, size, amenities, and more. By analyzing pre-scraped data from Airbnb, the model provides hosts with data-driven price recommendations to maximize their listing's profitability while staying competitive in the market.

## Key Features
- **Data Analysis**: Leverages Airbnb data to understand key factors influencing listing prices.
- **Predictive Modeling**: Uses machine learning models to predict the best price for a new listing given its characteristics.
- **User Input**: Hosts can input details about their property and receive a recommended price based on similar listings.
- **Interpretable Results**: Explains the importance of different features (location, number of bedrooms, amenities, etc.) in determining the price.

## Data Source
The dataset used for this project is pre-scraped Airbnb listing data, including:
- Property location (city, neighborhood)
- Number of bedrooms and bathrooms
- Amenities (Wi-Fi, pool, parking, etc.)
- Historical price information

*Note: The dataset is not included in this repository due to privacy and scraping policies but can be recreated using publicly available Airbnb data.*

## Approach
1. **Data Cleaning and Preprocessing**: Handling missing data, feature engineering (e.g., creating new features from amenities), and normalization.
2. **Exploratory Data Analysis (EDA)**: Visualizing and identifying trends in listing prices based on location, property size, and other factors.
3. **Model Selection**: Several machine learning algorithms where tested, including Beta regression, random forest and KNN, with cross-validation to ensure accuracy.
4. **Price Prediction**: The model predicts the best listing price for new properties based on their input features.
5. **Model Interpretability**: Feature importance analysis to explain which factors have the most impact on pricing decisions.

## Technologies Used
- **Python**: For data analysis and model development.
- **scikit-learn**: Machine learning model implementation.
- **pandas**: Data manipulation and preprocessing.
- **matplotlib & seaborn**: Data visualization.
- **statsmodels** : Beta regression 

## How to Use
1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/airbnb-price-estimation.git
   cd airbnb-price-estimation


2. **Install Requirements**:
   ```bash
pip install -r requirements.txt
