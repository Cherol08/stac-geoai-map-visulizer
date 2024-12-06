from flask import Flask, jsonify, render_template, request
import pandas as pd
import geopandas as gpd
import json
from shapely.geometry import shape

# import requests --- use requests model to make calls to geoserver 
## add some buttons to make the traffic and footfall layers visible.
## 

app = Flask(__name__)

# Load geospatial data and return a GeoPandas GeoDataFrame
def load_geospatial_data(file_path):
    # Load the JSON file
    with open(file_path, 'r') as f:
        raw_data = json.load(f)

    # Extract features
    features = raw_data['features']

    # Normalize properties into a DataFrame
    data = pd.json_normalize(features)

    # Convert geometry into GeoJSON-compatible format
    data['geometry'] = [shape(feature['geometry']) for feature in features]

    # Convert to GeoPandas GeoDataFrame
    gdf = gpd.GeoDataFrame(data, geometry='geometry')

    # Serialize geometry to GeoJSON format for Flask
    gdf['geometry'] = gdf['geometry'].apply(lambda geom: geom.__geo_interface__)

    return gdf

# MAP
@app.route('/map')
def get_map():
    return render_template('map.html')

# STAC Catalogue endpoint
@app.route('/stac/catalogue')
def stac_catalog():
    catalogue = {
        "stac_version": "1.0.0",
        "id": "example-catalog",
        "description": "This STAC catalog contains a collection of footfall and traffic data",
        "links": [
            {
                "rel": "child",
                "href": "/stac/collections/geospatial",
                "type": "application/json",
                "title": "Geospatial Data Collection"
            }
        ]
    }
    return render_template('catalogue.html', catalogue=catalogue)


# STAC Collection endpoint
@app.route('/stac/collections')
def stac_collection():
    collection = {
        "stac_version": "1.0.0",
        "id": "geospatial-data",
        "description": "A collection of geospatial data",
        "extent": {
            "spatial": {"bbox": [[-180.0, -90.0, 180.0, 90.0]]},
            "temporal": {"interval": [["2023-01-01T00:00:00Z", None]]}
        },
        "license": "CC-BY-4.0",
        "links": [
            {
                "rel": "item",
                "href": "/stac/collections/footfall/items",
                "type": "application/json",
                "title": "Footfall Data Items",
                "fields": """
                        h3_index => ignore, it is just an id\n
                        ff_rivil: total footfall mall only,\n
                        ffc_rivil: total footfall competitors only,\n
                        ffmc_rivil:total footfall mall and competitors,\n
                        ff_morning_rivil: morning footfall mall,\n
                        ff_midday_rivil:midday footfall mall,\n
                        ff_afternoon_rivil:afternoon footfall mall,\n
                        ff_evening_rivil:evening footfall mall,\n
                        ffc_morning_rivil:morning footfall competitors,\n
                        ffc_midday_rivil:midday footfall competitors ,\n
                        ffc_afternoon_rivil:afternoon footfall competitors,\n
                        ffc_evening_rivil:evening footfall competitors,\n
                        ff_morning_rivil_1 => ignore\n
                        ff_midday_rivil_1=> ignore,\n
                        ffc_week_rivil:weekday footfall competitors,\n
                        ffc_weekend_rivil:weekend footfall competitors,\n
                        income_class: dominant income class,\n
                        ff_week_rivil:weekday footfall mall,\n
                        ff_weekend_rivil:weekend footfall mall\n
                    """
            },
            {
                "rel": "item",
                "href": "/stac/collections/traffic/items",
                "type": "application/json",
                "title": "Traffic Data Items",
                "fields": """"
                        netw_id:identifier for individual road segment,\n
                        day: day of week\n
                        avg_traffic_den: average daily traffic density,\n
                        avg_hits: average daily traffic count,\n
                        total_hits:total traffic count for period,\n
                        day_num => ignore,\n
                        daily_ts:timestamp start of day,\n
                        cars_label: => ignore\n
                        avg_actual_hits: => ignore\n
                    """
            }
        ]
    }
    return render_template('collections.html', collections=collection)

# STAC Items endpoint
@app.route('/stac/collections/footfall/items')
def stac_items():
    # Load geospatial data
    gdf = load_geospatial_data('3-mtn_rivonia_ff_dataset.json')
    
    items = []
    for _, row in gdf.iterrows():
        items.append({
            "type": "Feature",
            "stac_version": "1.0.0",
            "id": row.get('FID', 'unknown-id'),
            "geometry": row['geometry'],
            "properties": {
                "h3_index": row.get('h3_index', None),
                "total_pop": row.get('total_pop', None),
                "income_class": row.get('income_class', None),
                "datetime": "2023-01-01T00:00:00Z"
            },
            "links": [],
            "fields": """"
                        'h3_index' => ignore, it is just an id
                        'ff_rivil': total footfall mall only,
                        'ffc_rivil': total footfall competitors only,
                        'ffmc_rivil':total footfall mall and competitors,
                        'ff_morning_rivil': morning footfall mall,
                        'ff_midday_rivil':midday footfall mall,
                        'ff_afternoon_rivil':afternoon footfall mall,
                        'ff_evening_rivil':evening footfall mall,
                        'ffc_morning_rivil':morning footfall competitors,
                        'ffc_midday_rivil':midday footfall competitors ,
                        'ffc_afternoon_rivil':afternoon footfall competitors,
                        'ffc_evening_rivil':evening footfall competitors,
                        'ff_morning_rivil_1' => ignore
                        'ff_midday_rivil_1'=> ignore,
                        'ffc_week_rivil':weekday footfall competitors,
                        'ffc_weekend_rivil':weekend footfall competitors,
                        'income_class': dominant income class,
                        'ff_week_rivil':weekday footfall mall,
                        'ff_weekend_rivil':weekend footfall mall
                    """            
        })

    return jsonify({
        "type": "FeatureCollection",
        "features": items
    })


# STAC Items for Traffic Data
@app.route('/stac/collections/traffic/items')
def stac_traffic_items():
    # Load traffic data
    gdf = load_geospatial_data('5-2-mtn_rivonia_geom_traffic.json')  # Replace with your traffic data file path
    
    items = []
    for _, row in gdf.iterrows():
        items.append({
            "type": "Feature",
            "stac_version": "1.0.0",
            "id": row.get('road_id', 'unknown-id'),
            "geometry": row['geometry'],
            "properties": {
                "traffic_flow": row.get('traffic_flow', None),
                "traffic_density": row.get('traffic_density', None),
                "datetime": "2023-01-01T00:00:00Z"
            },
            "links": [],
            "fields": """"
                        'netw_id':identifier for individual road segment,
                        'day': day of week
                        'avg_traffic_den': average daily traffic density,
                        'avg_hits': average daily traffic count,
                        'total_hits':total traffic count for period,
                        'day_num' => ignore,
                        'daily_ts':timestamp start of day,
                        'cars_label': => ignore
                        'avg_actual_hits': => ignore
                    """
        })

    return jsonify({
        "type": "FeatureCollection",
        "features": items
    })

# Main page for map visualization
@app.route('/', methods=['GET', 'POST'])
def index():
    result = ""
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        if query:
            # Simulate a result based on the query (replace with actual logic)
            result = f"Search results for: '{query}'"
    return render_template('home.html', result=result)


if __name__ == '__main__':
    app.run(debug=True)
