#### models
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
import pandas as pd
import h3

def sample_space(lat, lon, df ):
    resp = []
    current_hex = h3.latlng_to_cell(lat, lon , 8)
    sample = df[df['hex'] == current_hex]
    if len(sample)>60:
        resp = sample
    else:
        hexs_near = h3.grid_ring(current_hex)
        sample = df[df['hex'].isin(hexs_near)]
        if len(sample) >60:
            resp = sample
    return resp

def process_df(df):
    df['occupancy'] = (1-df['availability'])
    df  = df[df['price_per_night_num']>0]
    df = df[df['occupancy']>0]
    df = df[['occupancy',  'guest_number', 'number_of_beds' , 'number_of_bathrooms' , 'latitude' ,
                             'longitude' ,  'price_per_night_num', 'url' ]]
    df['number_of_beds'].fillna((df['number_of_beds'].mean()), inplace=True)
    df['number_of_bathrooms'].fillna((df['number_of_bathrooms'].mean()), inplace=True)
    df['guest_number'].fillna((df['guest_number'].mean()), inplace=True)
    df['price_per_guest'] =  df['price_per_night_num']/df['guest_number']
    return df



def estimation(df ,guests: int ,  beds: int, baths: float, lat:float, lon:float, k_neigh = 7):
    sample = sample_space(lat, lon, df )
    testknn_df = process_df(sample)
    if len(testknn_df)>28:
        ### Standarize features using standarized functino z = (x-u)/s
        scaler = StandardScaler()
        X = testknn_df[['guest_number', 'number_of_beds', 'number_of_bathrooms',
                        'latitude', 'longitude']]
        X_scaled = scaler.fit_transform(X)

        # Initialize the KNN model
        k = k_neigh  # Number of nearest neighbors
        knn = NearestNeighbors(n_neighbors=k)
        knn.fit(X_scaled)

        # inputed information
        test_values = pd.DataFrame({
            'guest_number': [guests],  # [test_df['price_per_guest'].mean()],  # Example values for each feature
            'number_of_beds': [beds],
            'number_of_bathrooms': [baths],
            'latitude': lat,
            'longitude': lon
        })
        new_listing_scaled = scaler.transform(test_values)

        # Find the k nearest neighbors
        distances, indices = knn.kneighbors(new_listing_scaled)
        neighbors = testknn_df.iloc[indices[0]]
        neighbors['revenue'] = neighbors['price_per_guest'] * neighbors['guest_number'] * neighbors['occupancy'] * 30

        top_results = neighbors.sort_values('revenue',ascending=False).head(3)

        suggested_price = top_results['price_per_guest'].mean() * guests
        est_revenue = suggested_price*top_results['occupancy'].mean()*30

        resp = {'status':200, 'ans':{'suggested_price': suggested_price ,
                                     'Estimated_monthly_revenue':est_revenue,
                                     'nearest_listing': neighbors['url'].values } }
    else:
        resp = {'status': 400, 'ans': {}}
    return resp
