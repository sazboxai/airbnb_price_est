import pandas as pd
import re
import h3
import dash
from dash import dcc, html
import dash_leaflet as dl
from dash.dependencies import Input, Output, State
import unicodedata
from estimation import estimation




# Function to check if a character is a currency symbol
def is_currency_symbol(char):
    return unicodedata.category(char) == 'Sc'

def check_crrency(input_string):
    resp= None
    string_process = ''.join(char for char in input_string if char.isalpha() or is_currency_symbol(char))
    if string_process != '':
        resp = string_process
    return resp

listings = pd.read_pickle("listings.pkl")
availability = pd.read_pickle("availability.pkl")

listings['guest_number'] = listings['guest_number'].apply(lambda x: None if x is None else int(x))
listings['number_of_beds'] = listings['number_of_beds'].apply(lambda x: None if x is None or x=='' else int(x))
listings['number_of_bathrooms'] = listings['number_of_bathrooms'].apply(lambda x: None if x is None  or x=='' else int(x))
### extracting the currency
listings['currency_price_pernight'] = listings['price_per_night'].apply(lambda x: None if x is None else  check_crrency(x) )

def transform_currency_to_number(currency_string, symbol):
    numeric_string = None
    if currency_string:
        exchange_dir = {'₹':0.012 , '€': 1.09,
                    'krSEK': 0.084, '£':1.30,
                    '₩': 0.00073}
        numeric_string = re.sub(r'[^\d.]', '', currency_string)
        numeric_string = int(float(numeric_string))
        if symbol:
            numeric_string = exchange_dir[symbol]*numeric_string
    return numeric_string


listings['price_per_night_num'] = listings.apply(lambda x: transform_currency_to_number(x['price_per_night'], x['currency_price_pernight']), axis =1  )
listings['url'] = listings['id'].apply(lambda x:  'https://www.airbnb.com/rooms/'+str(x))


shorter_range = availability[(availability['date']>'2024-10-17') ]
shorter_range =shorter_range[shorter_range['date']<'2024-11-04']


avialability_listings = shorter_range.groupby('listing_id')['availability'].mean().reset_index()
listings_summary = listings.merge(avialability_listings, left_on = 'id', right_on = 'listing_id', how='left')
listings_summary['hex'] = listings_summary.apply(lambda x:  h3.latlng_to_cell(x['latitude'], x['longitude'], 8), axis =1)

hex_data = listings_summary.groupby('hex').agg({'guest_number':'mean', 'number_of_beds':'mean',
                                     'number_of_bathrooms':'mean', 'id':'count' ,  'score':'mean' ,
                                     'price_per_night_num':'mean', 'availability':'mean'})


hex_data['occupancy']= 1- hex_data['availability']
hex_data = hex_data.reset_index()


########################### Dash board

data = hex_data.copy()
data['occupancy'] = data['occupancy'].fillna(0)

# Función para generar colores basados en la ocupación
def occupancy_to_color(occupancy):
    green = int(255 * occupancy)
    return f'rgb(0,{green},0)'  # Más verde para más ocupación

# Inicializar la aplicación Dash
app = dash.Dash(__name__)


def create_hex_layer(data):
    polygons = []
    for _, row in data.iterrows():
        boundary = h3.cell_to_boundary(row['hex'])
        color = occupancy_to_color(row['occupancy'])
        polygon = dl.Polygon(
            positions=boundary,
            color=color,
            fillColor=color,
            fillOpacity=0.5,
            id=row['hex'],
            children=[
                dl.Tooltip(f""" Occupancy: {row['occupancy']:.2f}, 
                    Guests: {row['guest_number']}, Beds: {row['number_of_beds']},
                    Baths: {row['number_of_bathrooms'] }, listings: {row['id'] }""")
            ]
        )
        polygons.append(polygon)
    return polygons


app.layout = html.Div([
html.Div(["Welcome to air_knn - Your Price Estimation Tool"], style={'backgroundColor': '#007acc', 'color': 'white', 'padding': '20px', 'textAlign': 'center'}),

html.Div([dcc.Markdown(
            """## Welcome to the Airbnb Pricing Tool

This tool is designed to help you optimize the price of your Airbnb listing based on data from recent listings. On the map below, you'll see Medellín divided into hexagons using the H3 indexing system (shoutout to Uber's [H3 library](https://uber.github.io/h3-py)!).
Brighter areas on the map indicate higher occupancy rates, signaling greater demand in those zones.

The model takes into account:
- Latitude and longitude
- Number of rooms
- Number of guests
- Bathrooms
- Beds

Based on this information, it suggests a price to help you maximize your revenue, utilizing price elasticity driven by local demand.

            """, className='Intro'),
        dcc.Markdown("""
        ## Step-by-Step Guide
        """),
        dcc.Markdown("""
        ### Step 1: Input Your Details
        * Enter the number of guests, beds, and bathrooms.
        * Provide the latitude and longitude for location-specific recommendations, or double-click on the map to select your desired position for tailored suggestions. 
        """, className='step-content'),

        dcc.Markdown("""
        ### Step 2: Submit Your Request
        * Click on the "Calculate" button.
        * Our algorithm will calculate the best estimate price for you.
        """, className='step-content'),

        dcc.Markdown("""
        ### Step 3: Review Recommendations
        * Check the calculated suggested price and estimated revenue.
        * Review the list of nearest similar listings provided.
        """, className='step-content'),
    ], style={'padding': '10px', 'margin': '10px', 'border': '1px solid #cccccc', 'borderRadius': '5px'}),

    dl.Map(center=[6.2442, -75.5812], zoom=12, children=[
        dl.TileLayer(),
        dl.LayerGroup(id="hex-layer"),
        dl.Marker(id="click-marker", position=[6.2442, -75.5812], draggable=True)
    ], style={'width': '100%', 'height': '500px'}, id="map", clickData=()),
    html.Div(id="click-coordinates", style={'padding': '10px', 'font-size': '18px'}),

    html.Div([
        html.Label('Lat:'),
        dcc.Input(id='lat-input', type='number', step=0.000001, placeholder="Latitud", style={'margin-right': '10px'}),
        html.Label('Lon:'),
        dcc.Input(id='lon-input', type='number', step=0.000001, placeholder="Longitud", style={'margin-right': '10px'}),
        html.Button('Locate', id='locate-button', n_clicks=0),
        html.Br(),
        html.Label('Guest number:'),
        dcc.Input(id='guest-input', type='number', min=1, placeholder="Guests", style={'margin-right': '10px'}),
        html.Label('Beds number:'),
        dcc.Input(id='beds-input', type='number', min=1, placeholder="Beds", style={'margin-right': '10px'}),
        html.Label('Total baths:'),
        dcc.Input(id='bathrooms-input', type='number', min=1, placeholder="Baths"),
    ], style={'padding': '10px', 'font-size': '18px'}),

    html.Button('Estimate', id='calculate-button', n_clicks=0, style={'margin-top': '10px'}),
    html.Div(id="output-result", style={'padding': '20px', 'font-size': '18px'}),

    html.Div([
        html.H3("Scan a New Area"),
        html.Div("Please fill out the form below to suggest a new area for scanning:"),

        # Input for area
        html.Div([
            html.Label('Area:'),
            dcc.Input(id='area-input', type='text', placeholder='Enter area name', style={'width': '100%'}),
        ], style={'marginBottom': '10px'}),

        # Input for name
        html.Div([
            html.Label('Your Name:'),
            dcc.Input(id='name-input', type='text', placeholder='Enter your name', style={'width': '100%'}),
        ], style={'marginBottom': '10px'}),

        # Input for email
        html.Div([
            html.Label('Email:'),
            dcc.Input(id='email-input', type='email', placeholder='Enter your email', style={'width': '100%'}),
        ], style={'marginBottom': '10px'}),

        # Submit Button
        html.Button('Submit', id='submit-button', n_clicks=0, style={'marginTop': '20px'}),

        # Placeholder for displaying acknowledgment
        html.Div(id='form-output', style={'marginTop': '20px', 'color': 'green'}),
    ], style={'padding': '20px', 'margin': '20px', 'border': '1px solid #cccccc', 'borderRadius': '5px'}),

])

@app.callback(
    Output('hex-layer', 'children'),
    Input('hex-layer', 'id')
)
def update_hex_layer(_):
    return create_hex_layer(data)

@app.callback(
    [
        Output('click-marker', 'position'),
        Output('click-coordinates', 'children'),
        Output('lat-input', 'value'),
        Output('lon-input', 'value')
    ],
    [
        Input('locate-button', 'n_clicks'),
        Input('map', 'clickData')
    ],
    [
        State('lat-input', 'value'),
        State('lon-input', 'value')
    ]
)
def update_position(locate_n_clicks, click_data, lat_input, lon_input):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update

    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if triggered_id == 'locate-button' and locate_n_clicks > 0 and lat_input is not None and lon_input is not None:
        return [lat_input, lon_input], f"Coordenadas seleccionadas: Latitud {lat_input:.6f}, Longitud {lon_input:.6f}", lat_input, lon_input

    if triggered_id == 'map' and click_data:
        lat = click_data['latlng']['lat']
        lon = click_data['latlng']['lng']
        return [lat, lon], f"Latitud: {lat}, Longitud: {lon}", lat, lon

    return dash.no_update, dash.no_update, dash.no_update, dash.no_update

@app.callback(
    Output('output-result', 'children'),
    [Input('calculate-button', 'n_clicks')],
    [State('guest-input', 'value'), State('beds-input', 'value'),
    State('bathrooms-input', 'value'), State('lat-input', 'value'),
    State('lon-input', 'value')]
)
def calculate_result(n_clicks, guests, beds, bathrooms, lat, lon):
    if n_clicks > 0 and guests and beds and bathrooms:
        estimate = estimation(listings_summary, guests, beds, bathrooms, lat, lon)
        if estimate['status'] == 200:
            suggested_price = estimate['ans']['suggested_price']
            estimated_revenue = estimate['ans']['Estimated_monthly_revenue']
            nearest_neighbors = estimate['ans']['nearest_listing']
            neighbors_links = [html.A(url, href=url, target="_blank", style={'display': 'block'}) for url in
                               nearest_neighbors]
            return html.Div([
                html.Div(f"Suggested price: ${suggested_price:.2f}"),
                html.Div(f"Estimated Revenue: ${estimated_revenue:.2f}"),
                html.H3("Similar Listings in the area", style={'margin': '20px 0', 'textAlign': 'center'}),
                html.Div(neighbors_links),
            ])

        else:
            return """There is not enough listings in that Zone to estimate a price"""
    return "Waiting inputs..."

contacts = []

@app.callback(
    Output('form-output', 'children'),
    Input('submit-button', 'n_clicks'),
    [
        dash.dependencies.State('area-input', 'value'),
        dash.dependencies.State('name-input', 'value'),
        dash.dependencies.State('email-input', 'value')
    ])


def update_output(n_clicks, area, name, email):
    if n_clicks > 0:
        contacts.append({'name':name,
                         'email':email,
                         'area':area})
        pd.DataFrame(contacts).to_csv('contacts.csv')
        return f'Thank you {name}, your request for scanning the {area} area has been recorded. We will contact you at {email}.'


if __name__ == '__main__':
    app.run_server(debug=True ,port=8080, host='0.0.0.0')



