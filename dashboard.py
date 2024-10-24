import pandas as pd
import re
import folium
import h3
import dash
from dash import dcc, html
import dash_leaflet as dl
from dash.dependencies import Input, Output, State
import unicodedata


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
    dl.Map(center=[6.2442, -75.5812], zoom=12, children=[
        dl.TileLayer(),
        dl.LayerGroup(id="hex-layer"),
        dl.Marker(id="click-marker", position=[6.2442, -75.5812], draggable=True)
    ], style={'width': '100%', 'height': '500px'}, id="map", clickData=()),
    html.Div(id="click-coordinates", style={'padding': '10px', 'font-size': '18px'}),

    html.Div([
        html.Label('Latitud:'),
        dcc.Input(id='lat-input', type='number', step=0.000001, placeholder="Latitud", style={'margin-right': '10px'}),
        html.Label('Longitud:'),
        dcc.Input(id='lon-input', type='number', step=0.000001, placeholder="Longitud", style={'margin-right': '10px'}),
        html.Button('Locate', id='locate-button', n_clicks=0),
        html.Br(),
        html.Label('Número de huéspedes:'),
        dcc.Input(id='guest-input', type='number', min=1, placeholder="Número de huéspedes", style={'margin-right': '10px'}),
        html.Label('Número de camas:'),
        dcc.Input(id='beds-input', type='number', min=1, placeholder="Número de camas", style={'margin-right': '10px'}),
        html.Label('Número de baños:'),
        dcc.Input(id='bathrooms-input', type='number', min=1, placeholder="Número de baños"),
    ], style={'padding': '10px', 'font-size': '18px'}),

    html.Button('Calcular', id='calculate-button', n_clicks=0, style={'margin-top': '10px'}),
    html.Div(id="output-result", style={'padding': '20px', 'font-size': '18px'}),
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
        suggested_price = 100 + guests * 10 + beds * 5 + bathrooms * 8
        estimated_occupancy = 0.8
        estimated_revenue = suggested_price * estimated_occupancy
        nearest_neighbors = [
            "https://www.airbnb.com/rooms/1",
            "https://www.airbnb.com/rooms/2",
            "https://www.airbnb.com/rooms/3",
            "https://www.airbnb.com/rooms/4",
            "https://www.airbnb.com/rooms/5"
        ]
        return f"""
        Precio sugerido: ${suggested_price:.2f}
        Ocupación estimada: {estimated_occupancy * 100:.2f}%
        Ingresos estimados: ${estimated_revenue:.2f}
        Propiedades cercanas: {', '.join(nearest_neighbors)}
        """
    return "Esperando los inputs..."


if __name__ == '__main__':
    app.run_server(debug=True ,port=8080, host='0.0.0.0')



