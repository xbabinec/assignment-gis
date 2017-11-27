from database import DatabasePort
from flask import Flask, jsonify, render_template, request
from itertools import chain
from psycopg2.extras import DictCursor

import json
import requests


app = Flask(__name__, template_folder="./templates", static_folder="./static")
app.config['TEMPLATES_AUTO_RELOAD'] = True


@app.route("/")
def index():
    return render_template('index.html')


@app.route("/api/v1.0/hello", methods=['GET'])
def hello():
    name = request.args.get('name')
    return jsonify(get_hello(name))


@app.route("/api/v1.0/gym", methods=['GET'])
def gym_geodata():
    dist = int(request.args.get('dist'))
    street_name = request.args.get('streetName')
    street_number = request.args.get('streetNumber')
    geocode_location = geocode_address(street_name, street_number)
    gym_geodata = get_gym_geodata(dist, geocode_location)
    return jsonify(features=gym_geodata)


@app.route("/api/v1.0/pitchSport", methods=['GET'])
def pitch_sport_list():
    return jsonify(get_pitch_sport_list())


@app.route("/api/v1.0/pitch", methods=['GET'])
def pitch_getodata():
    sport_type = request.args.get('sportType')
    return jsonify(get_pitch_geodata(sport_type))


@app.route("/api/v1.0/cityAreaRunning", methods=['GET'])
def city_area_running():
    area_name = request.args.get('areaName')
    area_name = area_name.replace(' ', '&')
    area_polygon = get_city_area_geodata(area_name)
    if area_polygon:
        fts_area_name = area_polygon[0]['properties']['title']
        running_lines = get_running_geodata(fts_area_name)
        shape_collection = area_polygon + running_lines
    else:
        shape_collection = area_polygon
    return jsonify(shape_collection)


def get_city_area_geodata(areaName):
    dp = DatabasePort()
    with dp.connection_handler(commit=True,
                               cursor_factory=DictCursor) as cursor:
        query = "SELECT json_build_object(" \
                "'type', 'Feature'," \
                "'geometry', ST_AsGeoJSON(ST_Transform(way, 4326))::json," \
                "'properties', json_build_object(" \
                "   'title', name," \
                "   'fill', '#003b84'," \
                "   'fill-opacity', 0.15," \
                "   'stroke-width', 5," \
                "   'stroke-opacity', 0.9" \
                "    )" \
                ") FROM planet_osm_polygon " \
                "WHERE to_tsvector('sk', name) @@ to_tsquery('sk', %s) " \
                "ORDER BY NAME <-> %s ASC " \
                "LIMIT 1;"
        cursor.execute(query, (areaName, areaName))
        rows = list(chain(*cursor.fetchall()))
        return rows


def get_running_geodata(areaName):
    dp = DatabasePort()
    with dp.connection_handler(commit=True,
                               cursor_factory=DictCursor) as cursor:
        query = "WITH running AS (" \
                "   SELECT DISTINCT ST_Transform(line.way, 4326) AS line_way, line.highway " \
                "   FROM planet_osm_polygon AS polygon " \
                "   CROSS JOIN planet_osm_line AS line " \
                "   WHERE polygon.name = %s AND ST_Intersects(polygon.way, line.way) " \
                "   AND line.highway " \
                "   IN ('sidewalk', 'path', 'footway', 'bridleway', 'steps', 'pedestrian', 'living_street') " \
                "   ) " \
                "SELECT json_build_object(" \
                "'type', 'Feature'," \
                "'geometry', ST_AsGeoJSON(line_way)::json," \
                "'properties', json_build_object(" \
                "   'title', highway," \
                "   'description', round(ST_Length(line_way::GEOGRAPHY)) || 'm'," \
                "   'stroke', '#d1004c'," \
                "   'stroke-opacity', 0.7," \
                "   'stroke-width', 3.25" \
                "    )" \
                ") FROM running;"
        cursor.execute(query, (areaName,))
        rows = list(chain(*cursor.fetchall()))
        return rows


def get_pitch_geodata(sport_type):
    dp = DatabasePort()
    with dp.connection_handler(commit=True,
                               cursor_factory=DictCursor) as cursor:
        query = "SELECT json_build_object(" \
                "'type', 'Feature'," \
                "'geometry', ST_AsGeoJSON(ST_Transform(way, 4326))::json," \
                "'properties', json_build_object(" \
                "   'title', sport," \
                "   'description', round(ST_Area(ST_Transform(way, 4326)::GEOGRAPHY)) || ' m2'," \
                "   'fill', '#ff1462'," \
                "   'stroke', '#ff1462'," \
                "   'stroke-width', 1.5" \
                "    )" \
                ") FROM planet_osm_polygon " \
                "WHERE leisure = 'pitch' AND sport = %s"
        cursor.execute(query, (sport_type,))
        rows = list(chain(*cursor.fetchall()))
        return rows


def get_pitch_sport_list():
    dp = DatabasePort()
    with dp.connection_handler(commit=True) as cursor:
        query = "SELECT DISTINCT unnest(string_to_array(plgn.sport, ';')) " \
                "AS sport FROM planet_osm_polygon AS plgn " \
                "WHERE leisure = 'pitch' ORDER BY sport ASC;"
        cursor.execute(query)
        rows = list(chain(*cursor.fetchall()))
        return rows


def get_gym_geodata(dist, search_location):
    lat = search_location['lat']
    lng = search_location['lng']
    postgis_location = 'SRID=4326;POINT(' + str(lng) + ' ' + str(lat) + ')'
    dp = DatabasePort()
    with dp.connection_handler(commit=True,
                               cursor_factory=DictCursor) as cursor:
        query = "SELECT json_build_object(" \
                "'type', 'Feature'," \
                "'geometry', ST_AsGeoJSON(sub.geog_way)::json," \
                "'properties', json_build_object(" \
                "   'title', sub.name," \
                "   'description', coalesce(sub.leisure, sub.amenity)," \
                "   'marker-color', '#3bb2d0'," \
                "   'marker-size', 'medium'," \
                "   'marker-symbol', 'circle'" \
                "   )" \
                ") FROM (" \
                "SELECT ST_Transform(way, 4326) AS geog_way, name, leisure, amenity FROM planet_osm_point " \
                "WHERE leisure = 'fitness_centre' OR amenity = 'gym' " \
                "UNION " \
                "SELECT ST_Transform(ST_Centroid(way), 4326) AS geog_way, name, leisure, amenity FROM planet_osm_polygon " \
                "WHERE leisure = 'fitness_centre' OR amenity = 'gym' " \
                ") AS sub WHERE ST_DWithin(sub.geog_way::GEOGRAPHY, ST_GeogFromText(%s), %s);"
        cursor.execute(query, (postgis_location, dist))
        rows = list(chain(*cursor.fetchall()))
        search_location_point = {
            'type': 'Feature',
            'geometry': {
                'type': 'Point',
                'coordinates': [lng, lat]
            },
            'properties': {
                'title': 'Your location',
                'description': 'Distance to search = ' + str(dist) + 'm',
                'marker-color': '#f44274',
                'marker-size': 'large',
                'marker-symbol': 'star'
            }
        }
        rows.append(search_location_point.copy())
        return rows


def get_hello(name):
    hello_message = {
        'hello': 'world',
        'name': name
    }
    return hello_message


def geocode_address(street_name, street_number):
    street_name = street_name.replace(' ', '+')
    with open('./config/geocoding.json') as geocoding:
        geocoding_data = json.load(geocoding)
        api_key = geocoding_data['apiKey']
        geocode_uri = "https://maps.googleapis.com/maps/api/geocode/json?address=" + \
                      street_name + "+" + street_number + "+Bratislava&key=" + api_key
        json_response = requests.get(geocode_uri).json()
        location = json_response['results'][0]['geometry']['location']
        return location


if __name__ == "__main__":
    app.run()
