from flask import Flask, jsonify, render_template
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


# STAC Catalog endpoint
@app.route('/stac/catalog')
def stac_catalog():
    catalog = {
        "stac_version": "1.0.0",
        "id": "example-catalog",
        "description": "An example STAC catalog",
        "links": [
            {
                "rel": "child",
                "href": "/stac/collections/geospatial",
                "type": "application/json",
                "title": "Geospatial Data Collection"
            }
        ]
    }
    return jsonify(catalog)


# STAC Collection endpoint
@app.route('/stac/collections/geospatial')
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
                "title": "Footfall Data Items"
            },
            {
                "rel": "item",
                "href": "/stac/collections/traffic/items",
                "type": "application/json",
                "title": "Traffic Data Items"
            }
        ]
    }
    return jsonify(collection)


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
            "links": []
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
            "links": []
        })

    return jsonify({
        "type": "FeatureCollection",
        "features": items
    })

# Main page for map visualization
@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
