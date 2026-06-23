"""
Data loading functions for NYC neighborhood analysis.
All data loading functions are cached for performance.
"""
from typing import List, Optional
import streamlit as st
import pandas as pd
import geopandas as gpd
import h3pandas  # Required for .h3 accessor
import shapely
from shapely.wkt import loads
from shapely.geometry import LineString, Point


CRS_GEO = "EPSG:4326"
CRS_PROJ = "3763"


def split_linestring(linestring: LineString, points: List[Point]) -> List[LineString]:
    """
    Splits a LineString into segments using a set of points.

    Args:
        linestring: shapely LineString to split
        points: List of points to use as split locations

    Returns:
        List of LineString segments
    """
    # Sort points along the LineString
    points = sorted(points, key=lambda x: linestring.project(x))

    segments = []
    start_point = linestring.coords[0]

    for point in points:
        end_point = point.coords[0]
        segment = LineString([start_point, end_point])
        segments.append(segment)
        start_point = end_point

    # Add the last segment
    segments.append(LineString([start_point, linestring.coords[-1]]))

    return segments


@st.cache_data(show_spinner="Loading NYC boundaries...")
def get_nyc_geo() -> Optional[gpd.GeoDataFrame]:
    """
    Load NYC borough boundaries GeoJSON.

    Returns:
        GeoDataFrame with NYC boundaries or None if loading fails
    """
    try:
        return gpd.read_file("https://data.cityofnewyork.us/resource/gthc-hcne.geojson")
    except Exception as e:
        st.error(f"Failed to load NYC boundaries: {str(e)}")
        return None


@st.cache_data(show_spinner="Loading ridership data...")
def get_ridership() -> Optional[gpd.GeoDataFrame]:
    """
    Load and process NYC MTA ridership data.

    Returns:
        GeoDataFrame with ridership data and coordinates or None if loading fails
    """
    try:
        ridership = pd.read_csv("data/processed/ridership_2024.csv")
        ridership['ridership_coords'] = ridership['ridership_coords'].apply(loads)
        ridership = gpd.GeoDataFrame(ridership, geometry='ridership_coords', crs=CRS_GEO)
        return ridership
    except FileNotFoundError:
        st.error("Ridership data file not found at data/processed/ridership_2024.csv")
        return None
    except Exception as e:
        st.error(f"Failed to load ridership data: {str(e)}")
        return None


@st.cache_data(show_spinner="Loading subway stations...")
def get_nyc_stations() -> Optional[gpd.GeoDataFrame]:
    """
    Load and process NYC MTA subway stations data.

    Returns:
        GeoDataFrame with station names, lines, and coordinates or None if loading fails
    """
    try:
        nyc_stations = pd.read_csv("data/raw/MTA_Subway_Stations_20241202.csv")\
            [['Daytime Routes', 'Georeference', 'Stop Name']]\
            .rename(columns={
                'Georeference': 'coords',
                'Daytime Routes': 'line_name',
                'Stop Name': 'station_name'
            })
        nyc_stations['coords'] = nyc_stations['coords'].apply(loads)
        nyc_stations = nyc_stations[nyc_stations['line_name'] != 'SIR']

        nyc_stations['line_name'] = nyc_stations.line_name.apply(lambda x: x.split(' '))
        nyc_stations = gpd.GeoDataFrame(nyc_stations, geometry='coords', crs=CRS_GEO)
        nyc_stations = nyc_stations.explode('line_name').drop_duplicates()
        return nyc_stations
    except FileNotFoundError:
        st.error("Stations data file not found at data/raw/MTA_Subway_Stations_20241202.csv")
        return None
    except Exception as e:
        st.error(f"Failed to load stations data: {str(e)}")
        return None


def get_nyc_lines(nyc_stations: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Load and process NYC subway lines, splitting them into segments between stations.

    Args:
        nyc_stations: GeoDataFrame of NYC stations

    Returns:
        GeoDataFrame with line segments and start/end coordinates
    """
    nyc_lines = gpd.read_file("data/shapefiles/routes_nyc_subway_may2016.shp")
    nyc_lines = nyc_lines.to_crs(CRS_GEO)[['route_shor', 'geometry']]\
        .set_geometry('geometry')\
        .rename(columns={'route_shor': 'line'})
    nyc_lines = nyc_lines[~nyc_lines['line'].isin(['S', 'SIR'])].explode()
    nyc_lines = nyc_lines.merge(
        nyc_stations.groupby('line_name').coords.apply(list).reset_index(),
        left_on='line',
        right_on='line_name'
    )
    nyc_lines['segments'] = nyc_lines.apply(
        lambda x: split_linestring(x.geometry, x.coords),
        axis=1
    )
    nyc_lines = nyc_lines.explode('segments')
    nyc_lines["start_coords"] = shapely.get_point(nyc_lines.segments, 0)
    nyc_lines["end_coords"] = shapely.get_point(nyc_lines.segments, -1)
    return nyc_lines


def get_nyc_mta_network(nyc_lines: gpd.GeoDataFrame, nyc_stations: gpd.GeoDataFrame, ridership: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """
    Build the NYC MTA network by joining lines with stations.

    Args:
        nyc_lines: GeoDataFrame of subway lines
        nyc_stations: GeoDataFrame of subway stations
        ridership: GeoDataFrame of ridership data

    Returns:
        GeoDataFrame representing the complete MTA network
    """
    nyc_mta_network = gpd.sjoin_nearest(
        nyc_lines.set_geometry('start_coords').set_crs(CRS_GEO).to_crs(CRS_PROJ),
        nyc_stations.to_crs(CRS_PROJ).add_suffix('_start').set_geometry('coords_start'),
        how='left'
    ).to_crs(CRS_GEO).drop('index_right', axis=1)

    nyc_mta_network = nyc_mta_network[
        nyc_mta_network['line_name_start'] == nyc_mta_network['line']
    ]

    nyc_mta_network = gpd.sjoin_nearest(
        nyc_mta_network.set_geometry('end_coords').set_crs(CRS_GEO).to_crs(CRS_PROJ),
        nyc_stations.to_crs(CRS_PROJ).add_suffix('_end').set_geometry('coords_end'),
        how='left'
    ).to_crs(CRS_GEO).drop('index_right', axis=1)

    nyc_mta_network = nyc_mta_network[
        nyc_mta_network['line'] == nyc_mta_network['line_name_end']
    ]
    nyc_mta_network = nyc_mta_network[
        nyc_mta_network['station_name_end'] != nyc_mta_network['station_name_start']
    ]

    return nyc_mta_network


@st.cache_data(show_spinner="Loading tree census data...")
def get_nyc_trees() -> gpd.GeoDataFrame:
    """
    Load and process NYC street tree census data.

    Returns:
        GeoDataFrame with tree locations
    """
    nyc_trees = pd.read_csv("data/processed/nyc_trees.csv")
    nyc_trees['trees_coords'] = nyc_trees['trees_coords'].apply(loads)
    nyc_trees = gpd.GeoDataFrame(nyc_trees, geometry='trees_coords', crs=CRS_GEO)
    return nyc_trees


@st.cache_data(show_spinner="Loading restaurant data...")
def get_nyc_restaurants() -> gpd.GeoDataFrame:
    """
    Load and process NYC restaurant inspection data.

    Returns:
        GeoDataFrame with restaurant locations
    """
    nyc_rest = pd.read_csv("data/processed/nyc_rest.csv")
    nyc_rest['rest_coords'] = nyc_rest['rest_coords'].apply(loads)
    nyc_rest = gpd.GeoDataFrame(nyc_rest, geometry='rest_coords', crs=CRS_GEO)
    return nyc_rest
