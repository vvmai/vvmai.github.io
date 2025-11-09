import streamlit as st
import pandas as pd
import geopandas as gpd
import plotly.express as px
import matplotlib.pyplot as plt
import contextily as cx

# Import custom modules
from data_loaders import (
    get_nyc_geo, get_ridership, get_nyc_stations, get_nyc_lines,
    get_nyc_mta_network, get_nyc_trees, get_nyc_restaurants, CRS_GEO
)
from nyc_analysis import (
    build_subway_network_graph, calculate_station_centrality,
    calculate_station_ridership, calculate_combined_centrality,
    add_metric_to_hexgrid, normalize_metric
)

st.set_page_config(layout="wide")
config = {'scrollZoom': True}

# Constants
H3_RESOLUTION = 9
CENTRALITY_PERCENTILE = 0.95


def create_network_visualization(nyc_mta_network):
    """Create and save the NYC MTA network visualization."""
    ax = nyc_mta_network.set_geometry('geometry')[['line', 'geometry']]\
        .drop_duplicates()\
        .plot('line', legend=True, figsize=(10, 10))
    nyc_mta_network.set_geometry('start_coords')[['start_coords']]\
        .drop_duplicates()\
        .plot(color='red', ax=ax, markersize=5)
    cx.add_basemap(ax, crs=nyc_mta_network.crs, alpha=0.5)
    ax.figure.savefig('nyc_mta_network.png', bbox_inches='tight')
    return ax


def create_choropleth_map(X, color_col, color_scale=None, quantile_cap=0.95):
    """
    Create a Plotly choropleth mapbox visualization.

    Args:
        X: GeoDataFrame with data to plot
        color_col: Column name for color mapping
        color_scale: Optional color scale name
        quantile_cap: Percentile to cap the color range

    Returns:
        Plotly figure object
    """
    fig = px.choropleth_mapbox(
        X,
        geojson=X.geometry,
        color=color_col,
        opacity=0.5,
        locations=X.index,
        mapbox_style='open-street-map',
        center={"lat": 40.7, "lon": -73.95},
        zoom=11,
        height=600,
        width=900,
        range_color=(0, X[color_col].quantile(quantile_cap)),
    )
    fig.update_traces(marker_line_width=0)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0))

    if color_scale:
        fig.update_layout(coloraxis={'colorscale': color_scale})

    return fig


def main():
    """Main application logic."""
    # Introduction
    st.markdown("""In the Summer of 2024, my lease was up. Instead of looking for an apartment,
                I procrastinated by making a map of NYC's most desirable neighborhoods,
                which is universally agreed to consist of three things:
                
1. Subways
2. Trees
3. Food
                
                """)

    # Section 1: Subways
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

    # Load and process data with progress indication
    with st.spinner('Loading subway network data...'):
        nyc_stations = get_nyc_stations()
        nyc_lines = get_nyc_lines(nyc_stations)
        ridership = get_ridership()
        nyc_mta_network = get_nyc_mta_network(nyc_lines, nyc_stations, ridership)

    # Create network visualization
    create_network_visualization(nyc_mta_network)
    col1, col2, col3 = st.columns([0.25, 0.5, 0.25])
    col2.image('data/nyc_mta_network.png', use_container_width=True,
               caption="NYC subway system represented as a graph.")

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

    # Calculate centrality metrics
    G = build_subway_network_graph(nyc_mta_network)
    centrality_df = calculate_station_centrality(G, nyc_stations)
    station_ridership = calculate_station_ridership(nyc_stations, ridership)
    station_centrality = calculate_combined_centrality(station_ridership, centrality_df)

    # Display results
    col1, col2 = st.columns([0.3, 0.7])

    with col1:
        st.dataframe(
            station_centrality.rename(columns={
                'station_name': 'Station Name',
                'centrality_metric': 'Centrality Score'
            }),
            hide_index=True
        )

    with col2:
        nyc_connectivity = nyc_stations[['station_name', 'coords']]\
            .drop_duplicates()\
            .merge(station_centrality, on='station_name')
        nyc_connectivity = gpd.GeoDataFrame(nyc_connectivity, geometry='coords', crs=CRS_GEO)

        nyc_geo = get_nyc_geo()
        X = add_metric_to_hexgrid(
            nyc_geo,
            nyc_connectivity,
            'centrality_metric',
            h3_resolution=H3_RESOLUTION,
            smoothing_weights=[4, 3, 2, 1]
        )

        fig = create_choropleth_map(X, 'centrality_metric', quantile_cap=CENTRALITY_PERCENTILE)
        st.plotly_chart(fig, theme=None)

        st.markdown("""*Note: The centrality score is on a scale of 0-1, but because the data is highly skewed towards Manhattan,
                    I plotted the color range to max out at the 95th percentile.*
                    """)

    st.markdown("""Clearly, NYC proper itself is very well-connected. But there are many pockets in the outer boroughs
                that are *relatively* well-connected. This is even more relevant if you actually *want* to stay away
                from the hustle and bustle while being able to get to other parts of the city quickly.
                """)

    # Section 2: Trees
    st.markdown("## 2 Trees")
    st.markdown("""Kind of insane that there's a decadal census of each sidewalk tree in NYC (including data about individual health, diameter, and species.)
                This census doesn't include trees inside parks, so this map doesn't necessarily show proximity to nearby public green spaces, but
                moreso the overall green-ness of just walking around a neighborhood.""")

    with st.spinner('Processing tree data...'):
        nyc_trees = get_nyc_trees()
        X = X.sjoin(nyc_trees, how='left').drop('index_right', axis=1)
        X['trees'] = X.groupby([X.index, 'geometry']).tree_id.transform('count')
        X['trees'] = X['trees'].fillna(0)

        # Keep necessary columns and normalize
        cols = ['index', 'shape_area', 'shape_leng', 'geometry', 'centrality_metric', 'trees']
        X = X[cols].drop_duplicates()
        X = normalize_metric(X, 'trees')
        X['trees'] = X[['trees']].h3.k_ring_smoothing(weights=[2, 1])['trees']

    fig = create_choropleth_map(X, 'trees', color_scale='greens', quantile_cap=CENTRALITY_PERCENTILE)
    st.plotly_chart(fig, theme=None)
    st.markdown("*Note: tree counts have been normalized to a score of between 0-1.*")

    # Section 3: Restaurants
    st.markdown("## 3 Restaurants")
    st.markdown("""I grabbed the list of all restaurants that had an inspection between 2023-2024 and new restaurants not yet inspected.""")

    with st.spinner('Processing restaurant data...'):
        nyc_rest = get_nyc_restaurants()
    X = X[cols].drop_duplicates()
    X = X.sjoin(nyc_rest, how='left').drop('index_right', axis=1)
    X['restaurants'] = X.groupby([X.index, 'geometry']).address.transform('nunique')
    X['restaurants'] = X['restaurants'].fillna(0)

    cols.append('restaurants')
    X = X[cols].drop_duplicates()
    X = normalize_metric(X, 'restaurants')
    X['restaurants'] = X[['restaurants']].h3.k_ring_smoothing(weights=[0, 3, 2, 1])['restaurants']

    fig = create_choropleth_map(X, 'restaurants', quantile_cap=CENTRALITY_PERCENTILE)
    st.plotly_chart(fig, theme=None)

    # Overall Score
    st.markdown("## Overall score")
    st.markdown("""
    Since the # of the trees happened to distinguish well the residential areas, I ended up weighing it twice as much as the other two
                in order to break up the Manhattan monolith.
    """)
    X['overall_score'] = (2 * X['trees'] + 0.5 * X['centrality_metric'] + 0.5 * X['restaurants']) / 3

    fig = create_choropleth_map(X, 'overall_score', color_scale='rdylgn', quantile_cap=CENTRALITY_PERCENTILE)
    st.plotly_chart(fig, theme=None)

    # Summary
    st.markdown("## Summary")
    st.markdown("""
    To be honest, I don't know how useful of an exercise this was. It mostly just confirmed my intuitions about
    where the best neighborhoods are (LIC, Williamsburg, Dumbo, Forest Hills, Bushwick, etc.) You might also
    notice that it inflates Manhattan's score a lot, since the city proper ranks high on all 3 metrics.
    Maybe in the future, I'll add a penalty for something like commerciality (Midtown/Chelsea is great
    for work and shopping... but who wants to live there?) or affordability.
    """)

    # Appendix
    st.markdown("## Appendix")
    st.markdown("""
    1. NYC 2015 tree census: https://data.cityofnewyork.us/Environment/2015-Street-Tree-Census-Tree-Data/uvpi-gqnh/about_data
    2. NYC 2023 ridership: https://data.ny.gov/Transportation/MTA-Subway-Origin-Destination-Ridership-Estimate-2/jsu2-fbtj
    3. NYC subway stations shapefile: https://data.ny.gov/Transportation/MTA-Subway-Stations/39hk-dx4f/about_data
    4. NYC subway lines shapefile: https://geo.nyu.edu/catalog/nyu-2451-34758
    5. NYC shapefile: https://data.cityofnewyork.us/City-Government/Borough-Boundaries/tqmj-j8zm
    6. NYC restaurants: https://data.cityofnewyork.us/Health/DOHMH-New-York-City-Restaurant-Inspection-Results/43nn-pn8j/about_data
    """)


if __name__ == "__main__":
    main()
