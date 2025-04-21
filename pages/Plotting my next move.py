import h3
import h3pandas
import pandas as pd
import plotly.graph_objects as go
import geopandas as gpd
import contextily as cx
from shapely.geometry import Polygon
import plotly.express as px
from shapely.wkt import loads
import networkx as nx
import itertools as it
import numpy as np
from sklearn.preprocessing import RobustScaler
import streamlit as st
import h3
import h3pandas
import pandas as pd
import plotly.graph_objects as go
import geopandas as gpd
import contextily as cx
from shapely.geometry import Polygon, LineString, Point, MultiLineString, MultiPoint
import plotly.express as px
from shapely.wkt import loads
import networkx as nx
import itertools as it
import numpy as np
import shapely
from pyproj import Geod
from shapely import ops, geometry
import re
import matplotlib.pyplot as plt
import matplotlib
config = {'scrollZoom': True}

st.set_page_config(layout="wide")
config = {'scrollZoom': True}

crs_geo = "EPSG:4326"
crs_proj = "3763"

def split_linestring(linestring, points):
    """Splits a LineString into segments using a set of points."""

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

@st.cache_data
def get_nyc_geo():
    return gpd.read_file("https://data.cityofnewyork.us/resource/gthc-hcne.geojson")

@st.cache_data
def get_ridership():
    # ridership = pd.read_csv("data/MTA_Subway_Origin-Destination_Ridership_Estimate__2024_20241211.csv")
    ridership = pd.read_csv ("data/ridership_2024.csv")
    # ridership = ridership[['Timestamp', 'Origin Latitude', 'Origin Longitude', "Estimated Average Ridership"]].rename(columns={'Estimated Average Ridership': 'ridership', 'Origin Latitude': 'latitude', 'Origin Longitude': 'longitude'})
    # ridership['Timestamp'] = pd.to_datetime(ridership['Timestamp'])
    # ridership['year'] = ridership['Timestamp'].dt.year
    # ridership = ridership.groupby(['year', 'latitude', 'longitude'])['ridership'].sum().reset_index()
    # ridership['ridership_coords'] = gpd.points_from_xy(ridership['longitude'], ridership['latitude'])
    ridership['ridership_coords'] = ridership['ridership_coords'].apply(loads)
    ridership = gpd.GeoDataFrame(ridership, geometry='ridership_coords', crs=crs_geo)
    # ridership.to_csv("data/ridership_2024.csv", index=False)
    return ridership

def get_nyc_lines(nyc_stations):
    nyc_lines = gpd.read_file("data/routes_nyc_subway_may2016.shp")
    nyc_lines = nyc_lines.to_crs(crs_geo)[['route_shor', 'geometry']].set_geometry('geometry').rename(columns={'route_shor':'line'})
    nyc_lines = nyc_lines[~nyc_lines['line'].isin(['S', 'SIR'])].explode()
    nyc_lines = nyc_lines.merge(nyc_stations.groupby('line_name').coords.apply(list).reset_index(), left_on='line', right_on='line_name')
    nyc_lines['segments'] = nyc_lines.apply(lambda x: split_linestring(x.geometry, x.coords), axis=1)
    nyc_lines = nyc_lines.explode('segments')
    nyc_lines["start_coords"] = shapely.get_point(nyc_lines.segments, 0)
    nyc_lines["end_coords"] = shapely.get_point(nyc_lines.segments, -1)
    return nyc_lines

@st.cache_data
def get_nyc_stations():
    nyc_stations = pd.read_csv("data/MTA_Subway_Stations_20241202.csv")\
        [['Daytime Routes', 'Georeference', 'Stop Name']]\
        .rename(columns={'Georeference': 'coords',
                        'Daytime Routes': 'line_name',
                        'Stop Name': 'station_name'})
    nyc_stations['coords'] = nyc_stations['coords'].apply(loads)
    nyc_stations = nyc_stations[nyc_stations['line_name']!='SIR']

    nyc_stations['line_name'] = nyc_stations.line_name.apply(lambda x: x.split(' '))
    nyc_stations = gpd.GeoDataFrame(nyc_stations, geometry='coords', crs=crs_geo)
    nyc_stations = nyc_stations.explode('line_name').drop_duplicates()
    return nyc_stations

def get_nyc_mta_network(nyc_lines, nyc_stations, ridership):
    nyc_mta_network = gpd.sjoin_nearest(nyc_lines.set_geometry('start_coords').set_crs(crs_geo).to_crs(crs_proj), nyc_stations.to_crs(crs_proj).add_suffix('_start').set_geometry('coords_start'), how='left')\
        .to_crs(crs_geo).drop('index_right', axis=1)
    nyc_mta_network = nyc_mta_network[nyc_mta_network['line_name_start']==nyc_mta_network['line']]
    nyc_mta_network = gpd.sjoin_nearest(nyc_mta_network.set_geometry('end_coords').set_crs(crs_geo).to_crs(crs_proj), nyc_stations.to_crs(crs_proj).add_suffix('_end').set_geometry('coords_end'), how='left')\
        .to_crs(crs_geo).drop('index_right', axis=1)
    nyc_mta_network = nyc_mta_network[nyc_mta_network['line']==nyc_mta_network['line_name_end']]
    nyc_mta_network = nyc_mta_network[nyc_mta_network['station_name_end']!=nyc_mta_network['station_name_start']]

    return nyc_mta_network

nyc_stations = get_nyc_stations()
nyc_lines = get_nyc_lines(nyc_stations)
ridership = get_ridership()

st.markdown("""In the Summer of 2024, my lease was up. Instead of looking for an apartment,
            I procrastinated by making a map of NYC's most desirable neighborhoods,
            which is universally agreed to consist of three things:

1. Subways
2. Trees
3. Food
            """)

st.markdown("## 1 Subways")
st.markdown("""If you know me, you know that I am lazy.
            I am willing to walk 11 mins *max* from my apartment to the subway.
            That said, if the walk happens to pass by multiple coffee shops and
            the station can get me downtown in 20 mins, I may be willing to go a little farther... clearly,
            even my basest instincts recognize there is some nuance to what it means to be
            'well-connected'. 
            """)

st.markdown("""
            A subway station can be valuable in two ways: 1) It can get you to a desirable place,
            and 2) It *is* the desirable place.
            """)

st.markdown("""Number 1 hints at some graph shenanigans going on here. If you can capture the NYC subway system in the form of
            a graph, where each node is a subway station and each edge is the subway line(s) which connect them,
            then you can calculate the eigenvector centrality metric for each node (i.e. station), which is exactly what I did below.""")

nyc_mta_network = get_nyc_mta_network(nyc_lines, nyc_stations, ridership)

ax = nyc_mta_network.set_geometry('geometry')[['line', 'geometry']].drop_duplicates().plot('line', legend=True, figsize=(10, 10))
nyc_mta_network.set_geometry('start_coords')[['start_coords']].drop_duplicates().plot(color='red', ax=ax, markersize=5)
cx.add_basemap(ax, crs=nyc_mta_network.crs, alpha=0.5)
ax.figure.savefig('nyc_mta_network.png', bbox_inches='tight') 
col1, col2, col3 = st.columns([0.25, 0.5, 0.25])
col2.image('data/nyc_mta_network.png', use_container_width=True, caption="NYC subway system represented as a graph.")

st.markdown("""Intuitively, the eigenvector centrality answers the question: is this station connected to other stations that are themselves well-connected?
            In order words, it is not enough for one station to be connected to many other stations -- the other stations must themselves
            be well-connected.""")

st.markdown("""Number 2 is a bit more straightforward. To measure whether the node (station) itself is desirable, I use ridership.
            The more people swipe into this station, the more desirable it is (either because
            many people live nearby or because many people get off here and later swipe back through to get home.)
            The final centrality score is an equal weighted average of ridership and centrality.*
            """)

st.markdown("""*For the nitpicky reader, I would much rather have calculated a node-weighted eigenvector
            centrality score to begin with, but this gets me 90% of the way there and runs out-of-the-box, and that's good enough for me.""")

G = nx.Graph()

edges = nyc_mta_network[['station_name_start', 'station_name_end', 'segments']].drop_duplicates()
edges['distance'] = round(edges.segments.apply(lambda x: Geod(ellps="WGS84").geometry_length(x))/1609, 1)

for row in edges.values:
    from_station = row[0]
    to_station = row[1]
    G.add_node(from_station)
    G.add_node(to_station)
    G.add_edge(from_station, to_station)
    

centrality = nx.eigenvector_centrality(G)
centrality_df = pd.DataFrame({'station_name': centrality.keys(), 'centrality': centrality.values()})
centrality_df['centrality'] = centrality_df['centrality']
centrality_df = nyc_stations.merge(centrality_df, on='station_name', how='left').fillna(0)

centrality_df = centrality_df[['station_name', 'centrality']].drop_duplicates()
station_ridership = gpd.sjoin_nearest(nyc_stations.set_geometry('coords').to_crs(crs_proj), ridership.set_geometry('ridership_coords').to_crs(crs_proj), max_distance=350, how='left').to_crs(crs_geo).drop('index_right', axis=1).fillna(0)[['station_name', 'ridership']].drop_duplicates()
station_ridership['ridership'] = (station_ridership['ridership'] - station_ridership['ridership'].min())/(station_ridership['ridership'].max() - station_ridership['ridership'].min())
station_ridership = station_ridership.groupby('station_name').ridership.sum().reset_index()
station_centrality = station_ridership.merge(centrality_df, on='station_name', how='left')
station_centrality['centrality_metric'] = (0.5*station_centrality['ridership']+0.5*station_centrality['centrality']/2)
station_centrality['centrality_metric'] = round((station_centrality['centrality_metric'] - station_centrality['centrality_metric'].min())/(station_centrality['centrality_metric'].max() - station_centrality['centrality_metric'].min()),3)
station_centrality = station_centrality[['station_name', 'centrality_metric']].sort_values(by='centrality_metric', ascending=False)

col1, col2 = st.columns([0.3, 0.7])

with col1:
    st.dataframe(station_centrality.rename(columns={'station_name': 'Station Name',
                                                    'centrality_metric': 'Centrality Score'}),
                hide_index=True)

with col2:
    cols = ['index', 'shape_area', 'shape_leng',
        'geometry', 'station_name']

    nyc_connectivity = nyc_stations[['station_name', 'coords']].drop_duplicates().merge(station_centrality, on='station_name')
    nyc_connectivity = gpd.GeoDataFrame(nyc_connectivity, geometry='coords', crs=crs_geo)

    nyc_geo = get_nyc_geo()
    nyc_geo = gpd.GeoDataFrame(nyc_geo, geometry='geometry', crs=crs_geo)
    nyc_geo = nyc_geo.h3.polyfill_resample(9).h3.h3_to_geo_boundary()
    X = nyc_geo.sjoin(nyc_connectivity, how='left').drop('index_right', axis=1)
    X['centrality_metric'] = X.groupby([X.index, 'geometry']).centrality_metric.transform('max')
    X['centrality_metric'] = X['centrality_metric'].fillna(0)

    cols += ['centrality_metric']
    X = X[cols].drop_duplicates()
    X['centrality_metric'] = X[['centrality_metric']].h3.k_ring_smoothing(weights=[4, 3, 2, 1])['centrality_metric']

    fig = px.choropleth_mapbox(X,
        geojson=X.geometry, 
        color='centrality_metric',
        opacity=0.5,
        locations=X.index,
        mapbox_style='open-street-map',
        center={"lat": 40.7, "lon": -73.95},
        zoom=11,
        height=600,
        width=900,
        range_color=(0, X.centrality_metric.quantile(0.95)),
    )
    fig.update_traces(marker_line_width=0)
    fig.update_layout(
    margin=dict(l=0, r=0, t=0, b=0),
    )

    st.plotly_chart(fig, theme=None)

    st.markdown("""*Note: The centrality score is on a scale of 0-1, but because the data is highly skewed towards Manhattan,
                I plotted the color range to max out at the 95th percentile.*
                """)

st.markdown("""Clearly, NYC proper itself is very well-connected. But there are many pockets in the outer boroughs
            that are *relatively* well-connected. This is even more relevant if you actually *want* to stay away
            from the hustle and bustle while being able to get to other parts of the city quickly.
            """)

st.markdown("## 2 Trees")
st.markdown("""Kind of insane that there's a decadal census of each sidewalk tree in NYC (including data about individual health, diameter, and species.)
            This census doesn't include trees inside parks, so this map doesn't necessarily show proximity to nearby public green spaces, but
            moreso the overall green-ness of just walking around a neighborhood.""")
# nyc_trees = pd.read_csv("data/2015_Street_Tree_Census_-_Tree_Data_20241215.csv")
nyc_trees = pd.read_csv("data/nyc_trees.csv")
# nyc_trees = nyc_trees[['latitude', 'longitude', 'tree_id']].drop_duplicates()
# nyc_trees['trees_coords'] = gpd.points_from_xy(nyc_trees['longitude'], nyc_trees['latitude'])
nyc_trees['trees_coords'] = nyc_trees['trees_coords'].apply(loads)
nyc_trees = gpd.GeoDataFrame(nyc_trees, geometry='trees_coords', crs=crs_geo)
# nyc_trees.to_csv("data/nyc_trees.csv", index=False)

X = X.sjoin(nyc_trees, how='left').drop('index_right', axis=1)
X['trees'] = X.groupby([X.index, 'geometry']).tree_id.transform('count')
X['trees'] = X['trees'].fillna(0)

cols += ['trees']
X = X[cols].drop_duplicates()
X['trees'] = (X['trees'] - X['trees'].min())/(X['trees'].max() - X['trees'].min())
X['trees'] = X[['trees']].h3.k_ring_smoothing(weights=[2, 1])['trees']

fig = px.choropleth_mapbox(X,
    geojson=X.geometry, 
    color='trees',
    opacity=0.5,
    locations=X.index,
    mapbox_style='open-street-map',
    center={"lat": 40.7, "lon": -73.95},
    zoom=11,
    height=600,
    width=900,
    range_color=(0, X.trees.quantile(0.95)),
)
fig.update_traces(marker_line_width=0)
fig.update_layout(
margin=dict(l=0, r=0, t=0, b=0),
coloraxis = {'colorscale':'greens'})

st.plotly_chart(fig, theme=None)
st.markdown("*Note: tree counts have been normalized to a score of between 0-1.*")
st.markdown("## 3 Restaurants")
st.markdown("""I grabbed the list of all restaurants that had an inspection between 2023-2024 and new restaurants not yet inspected.""")
# nyc_rest = pd.read_csv("data/DOHMH_New_York_City_Restaurant_Inspection_Results_20241215.csv")
nyc_rest = pd.read_csv("data/nyc_rest.csv")
# nyc_rest['GRADE DATE'] = pd.to_datetime(nyc_rest['GRADE DATE'], format='%m/%d/%Y')
# nyc_rest = nyc_rest[['STREET', 'ZIPCODE', 'BUILDING', 'GRADE DATE', 'Latitude', 'Longitude']].drop_duplicates().dropna()
# nyc_rest['address'] = nyc_rest.apply(lambda x: x.BUILDING + x.STREET + str(x.ZIPCODE), axis=1)
# nyc_rest = nyc_rest[(nyc_rest['GRADE DATE'].dt.year>=2023) | (nyc_rest['GRADE DATE'].dt.year==1900)]
# nyc_rest['rest_coords'] = gpd.points_from_xy(nyc_rest['Longitude'], nyc_rest['Latitude'])
nyc_rest['rest_coords'] = nyc_rest['rest_coords'].apply(loads)
# nyc_rest = nyc_rest[['address', 'rest_coords']].drop_duplicates().dropna()
nyc_rest = gpd.GeoDataFrame(nyc_rest, geometry='rest_coords', crs=crs_geo)
# nyc_rest.to_csv("data/nyc_rest.csv", index=False)


X = X[cols].drop_duplicates()
X = X.sjoin(nyc_rest, how='left').drop('index_right', axis=1)
X['restaurants'] = X.groupby([X.index, 'geometry']).address.transform('nunique')
X['restaurants'] = X['restaurants'].fillna(0)

cols += ['restaurants']
X = X[cols].drop_duplicates()
X['restaurants'] = (X['restaurants'] - X['restaurants'].min())/(X['restaurants'].max() - X['restaurants'].min())
X['restaurants'] = X[['restaurants']].h3.k_ring_smoothing(weights=[0, 3, 2, 1])['restaurants']


fig = px.choropleth_mapbox(X,
    geojson=X.geometry, 
    color='restaurants',
    opacity=0.5,
    locations=X.index,
    mapbox_style='open-street-map',
    center={"lat": 40.7, "lon": -73.95},
    zoom=11,
    height=600,
    width=900,
    range_color=(0, X.restaurants.quantile(0.95)),
)
fig.update_traces(marker_line_width=0)

fig.update_layout(
margin=dict(l=0, r=0, t=0, b=0),
)

st.plotly_chart(fig, theme=None)

st.markdown("## Overall score")
st.markdown("""
Since the # of the trees happened to distinguish well the residential areas, I ended up weighing it twice as much as the other two
            in order to break up the Manhattan monolith. 
""")
X['overall_score'] = (2*X['trees'] + 0.5*X['centrality_metric'] + 0.5*X['restaurants'])/3

fig = px.choropleth_mapbox(X,
    geojson=X.geometry, 
    color='overall_score',
    opacity=0.5,
    locations=X.index,
    mapbox_style='open-street-map',
    center={"lat": 40.7, "lon": -73.95},
    zoom=10.5,
    height=600,
    width=900,
    range_color=(0, X.overall_score.quantile(0.95)),
)
fig.update_traces(marker_line_width=0)
fig.update_layout(
margin=dict(l=0, r=0, t=0, b=0),
coloraxis = {'colorscale':'rdylgn'}
)

st.plotly_chart(fig, theme=None)

st.markdown("## Summary")
st.markdown("""
To be honest, I don't know how useful of an exercise this was. It mostly just confirmed my intuitions about
where the best neighborhoods are (LIC, Williamsburg, Dumbo, Forest Hills, Bushwick, etc.) You might also
notice that it inflates Manhattan's score a lot, since the city proper ranks high on all 3 metrics. 
Maybe in the future, I'll add a penalty for something like commerciality (Midtown/Chelsea is great
for work and shopping... but who wants to live there?) or affordability.
""")

st.markdown("## Appendix")
st.markdown("""
1. NYC 2015 tree census: https://data.cityofnewyork.us/Environment/2015-Street-Tree-Census-Tree-Data/uvpi-gqnh/about_data
2. NYC 2023 ridership: https://data.ny.gov/Transportation/MTA-Subway-Origin-Destination-Ridership-Estimate-2/jsu2-fbtj
3. NYC subway stations shapefile: https://data.ny.gov/Transportation/MTA-Subway-Stations/39hk-dx4f/about_data
4. NYC subway lines shapefile: https://geo.nyu.edu/catalog/nyu-2451-34758
5. NYC shapefile: https://data.cityofnewyork.us/City-Government/Borough-Boundaries/tqmj-j8zm
6. NYC restaurants: https://data.cityofnewyork.us/Health/DOHMH-New-York-City-Restaurant-Inspection-Results/43nn-pn8j/about_data
""")

