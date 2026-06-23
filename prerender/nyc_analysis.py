"""
NYC neighborhood analysis functions.
Includes network analysis, centrality calculations, and metric computations.
"""
import pandas as pd
import geopandas as gpd
import networkx as nx
import h3pandas  # Required for .h3 accessor
from pyproj import Geod
from typing import Optional, List


def build_subway_network_graph(nyc_mta_network):
    """
    Build a NetworkX graph from the MTA network data.

    Args:
        nyc_mta_network: GeoDataFrame with station connections

    Returns:
        NetworkX Graph object with stations as nodes
    """
    G = nx.Graph()
    edges = nyc_mta_network[['station_name_start', 'station_name_end', 'segments']].drop_duplicates()
    edges['distance'] = round(
        edges.segments.apply(lambda x: Geod(ellps="WGS84").geometry_length(x)) / 1609,
        1
    )

    for row in edges.values:
        from_station = row[0]
        to_station = row[1]
        G.add_node(from_station)
        G.add_node(to_station)
        G.add_edge(from_station, to_station)

    return G


def calculate_station_centrality(G, nyc_stations):
    """
    Calculate eigenvector centrality for each station.

    Args:
        G: NetworkX graph of the subway network
        nyc_stations: GeoDataFrame of stations

    Returns:
        DataFrame with station names and centrality scores
    """
    centrality = nx.eigenvector_centrality(G)
    centrality_df = pd.DataFrame({
        'station_name': centrality.keys(),
        'centrality': centrality.values()
    })
    centrality_df = nyc_stations.merge(centrality_df, on='station_name', how='left').fillna(0)
    centrality_df = centrality_df[['station_name', 'centrality']].drop_duplicates()
    return centrality_df


def calculate_station_ridership(nyc_stations, ridership, max_distance=350):
    """
    Calculate normalized ridership scores for each station.

    Args:
        nyc_stations: GeoDataFrame of stations
        ridership: GeoDataFrame of ridership data
        max_distance: Maximum distance for spatial join in meters

    Returns:
        DataFrame with station names and normalized ridership scores
    """
    CRS_PROJ = "3763"
    CRS_GEO = "EPSG:4326"

    station_ridership = gpd.sjoin_nearest(
        nyc_stations.set_geometry('coords').to_crs(CRS_PROJ),
        ridership.set_geometry('ridership_coords').to_crs(CRS_PROJ),
        max_distance=max_distance,
        how='left'
    ).to_crs(CRS_GEO).drop('index_right', axis=1).fillna(0)[['station_name', 'ridership']].drop_duplicates()

    # Normalize ridership
    station_ridership['ridership'] = (
        (station_ridership['ridership'] - station_ridership['ridership'].min()) /
        (station_ridership['ridership'].max() - station_ridership['ridership'].min())
    )
    station_ridership = station_ridership.groupby('station_name').ridership.sum().reset_index()
    return station_ridership


def calculate_combined_centrality(station_ridership, centrality_df, ridership_weight=0.5):
    """
    Calculate combined centrality metric from ridership and network centrality.

    Args:
        station_ridership: DataFrame with ridership scores
        centrality_df: DataFrame with centrality scores
        ridership_weight: Weight for ridership (0-1), centrality gets (1 - weight)

    Returns:
        DataFrame with combined centrality metric, sorted by score
    """
    station_centrality = station_ridership.merge(centrality_df, on='station_name', how='left')
    station_centrality['centrality_metric'] = (
        ridership_weight * station_centrality['ridership'] +
        (1 - ridership_weight) * station_centrality['centrality'] / 2
    )

    # Normalize final metric
    station_centrality['centrality_metric'] = round(
        (station_centrality['centrality_metric'] - station_centrality['centrality_metric'].min()) /
        (station_centrality['centrality_metric'].max() - station_centrality['centrality_metric'].min()),
        3
    )
    station_centrality = station_centrality[['station_name', 'centrality_metric']]\
        .sort_values(by='centrality_metric', ascending=False)

    return station_centrality


def add_metric_to_hexgrid(nyc_geo, metric_gdf, metric_column, h3_resolution=9, smoothing_weights=None):
    """
    Add a metric to NYC hexagonal grid with optional spatial smoothing.

    Args:
        nyc_geo: GeoDataFrame of NYC boundaries
        metric_gdf: GeoDataFrame with metric data and geometry
        metric_column: Name of the metric column to add
        h3_resolution: H3 hexagon resolution
        smoothing_weights: List of weights for k-ring smoothing (e.g., [4, 3, 2, 1])

    Returns:
        GeoDataFrame with hexagonal grid and smoothed metric
    """
    # Create H3 hexagonal grid
    hexgrid = nyc_geo.h3.polyfill_resample(h3_resolution).h3.h3_to_geo_boundary()

    # Join with metric data
    X = hexgrid.sjoin(metric_gdf, how='left').drop('index_right', axis=1)
    X[metric_column] = X.groupby([X.index, 'geometry'])[metric_column].transform('max')
    X[metric_column] = X[metric_column].fillna(0)

    # Drop unnecessary columns and smooth
    cols = ['index', 'shape_area', 'shape_leng', 'geometry', metric_column]
    X = X[cols].drop_duplicates()

    if smoothing_weights:
        X[metric_column] = X[[metric_column]].h3.k_ring_smoothing(weights=smoothing_weights)[metric_column]

    return X


def normalize_metric(df, metric_column):
    """
    Normalize a metric column to 0-1 range.

    Args:
        df: DataFrame containing the metric
        metric_column: Name of column to normalize

    Returns:
        DataFrame with normalized metric
    """
    df = df.copy()
    df[metric_column] = (
        (df[metric_column] - df[metric_column].min()) /
        (df[metric_column].max() - df[metric_column].min())
    )
    return df
