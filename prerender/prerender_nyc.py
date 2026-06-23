"""
One-time generator for the static NYC "Plotting my next move" assets.

Runs the full geo/network analysis (heavy deps: geopandas, networkx, h3pandas,
contextily, census) and writes self-contained Plotly HTML maps that the stlite
site embeds. Re-run locally with the project .venv whenever the analysis changes:

    .venv/bin/python prerender/prerender_nyc.py

Outputs -> assets/maps/{centrality,trees,restaurants,overall}.html
Network PNG (already rendered) -> copied to assets/maps/nyc_mta_network.png
"""
import os
import shutil
import sys

import geopandas as gpd
import plotly.express as px
import plotly.io as pio

# Resolve repo root so the script can run from anywhere and find the data/ dir.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from data_loaders import (  # noqa: E402
    get_nyc_geo, get_ridership, get_nyc_stations, get_nyc_lines,
    get_nyc_mta_network, get_nyc_trees, get_nyc_restaurants, CRS_GEO,
)
from nyc_analysis import (  # noqa: E402
    build_subway_network_graph, calculate_station_centrality,
    calculate_station_ridership, calculate_combined_centrality,
    add_metric_to_hexgrid, normalize_metric,
)

# Importing streamlit (via data_loaders) switches Plotly's default template to
# "streamlit", whose dark colorscale would bleed into the exported maps. The
# live app avoids this with st.plotly_chart(theme=None); replicate that here.
pio.templates.default = "plotly"

OUT_DIR = os.path.join(ROOT, "assets", "maps")
H3_RESOLUTION = 9
CENTRALITY_PERCENTILE = 0.95


def create_choropleth_map(X, color_col, color_scale=None, quantile_cap=0.95):
    fig = px.choropleth_mapbox(
        X,
        geojson=X.geometry,
        color=color_col,
        opacity=0.5,
        locations=X.index,
        mapbox_style="open-street-map",
        center={"lat": 40.7, "lon": -73.95},
        zoom=11,
        height=600,
        range_color=(0, X[color_col].quantile(quantile_cap)),
    )
    fig.update_traces(marker_line_width=0)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), autosize=True)
    if color_scale:
        fig.update_layout(coloraxis={"colorscale": color_scale})
    return fig


def save(fig, name):
    path = os.path.join(OUT_DIR, f"{name}.html")
    fig.write_html(path, include_plotlyjs="cdn", full_html=True,
                   config={"scrollZoom": True, "responsive": True})
    print(f"  wrote {path}")


def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # Network PNG already rendered with contextily basemap — reuse it.
    src_png = os.path.join(ROOT, "data", "nyc_mta_network.png")
    shutil.copyfile(src_png, os.path.join(OUT_DIR, "nyc_mta_network.png"))
    print(f"  copied {src_png}")

    print("Loading subway network...")
    nyc_stations = get_nyc_stations()
    nyc_lines = get_nyc_lines(nyc_stations)
    ridership = get_ridership()
    nyc_mta_network = get_nyc_mta_network(nyc_lines, nyc_stations, ridership)

    print("Computing centrality...")
    G = build_subway_network_graph(nyc_mta_network)
    centrality_df = calculate_station_centrality(G, nyc_stations)
    station_ridership = calculate_station_ridership(nyc_stations, ridership)
    station_centrality = calculate_combined_centrality(station_ridership, centrality_df)

    # Persist the station ranking table for the static page.
    station_centrality.rename(columns={
        "station_name": "Station Name",
        "centrality_metric": "Centrality Score",
    }).to_csv(os.path.join(OUT_DIR, "station_centrality.csv"), index=False)
    print("  wrote station_centrality.csv")

    nyc_connectivity = nyc_stations[["station_name", "coords"]].drop_duplicates()\
        .merge(station_centrality, on="station_name")
    nyc_connectivity = gpd.GeoDataFrame(nyc_connectivity, geometry="coords", crs=CRS_GEO)

    nyc_geo = get_nyc_geo()
    X = add_metric_to_hexgrid(
        nyc_geo, nyc_connectivity, "centrality_metric",
        h3_resolution=H3_RESOLUTION, smoothing_weights=[4, 3, 2, 1],
    )
    save(create_choropleth_map(X, "centrality_metric", quantile_cap=CENTRALITY_PERCENTILE),
         "centrality")

    print("Processing trees...")
    nyc_trees = get_nyc_trees()
    X = X.sjoin(nyc_trees, how="left").drop("index_right", axis=1)
    X["trees"] = X.groupby([X.index, "geometry"]).tree_id.transform("count")
    X["trees"] = X["trees"].fillna(0)
    cols = ["index", "shape_area", "shape_leng", "geometry", "centrality_metric", "trees"]
    X = X[cols].drop_duplicates()
    X = normalize_metric(X, "trees")
    X["trees"] = X[["trees"]].h3.k_ring_smoothing(weights=[2, 1])["trees"]
    save(create_choropleth_map(X, "trees", color_scale="greens", quantile_cap=CENTRALITY_PERCENTILE),
         "trees")

    print("Processing restaurants...")
    nyc_rest = get_nyc_restaurants()
    X = X[cols].drop_duplicates()
    X = X.sjoin(nyc_rest, how="left").drop("index_right", axis=1)
    X["restaurants"] = X.groupby([X.index, "geometry"]).address.transform("nunique")
    X["restaurants"] = X["restaurants"].fillna(0)
    cols.append("restaurants")
    X = X[cols].drop_duplicates()
    X = normalize_metric(X, "restaurants")
    X["restaurants"] = X[["restaurants"]].h3.k_ring_smoothing(weights=[0, 3, 2, 1])["restaurants"]
    save(create_choropleth_map(X, "restaurants", quantile_cap=CENTRALITY_PERCENTILE),
         "restaurants")

    print("Computing overall score...")
    X["overall_score"] = (2 * X["trees"] + 0.5 * X["centrality_metric"] + 0.5 * X["restaurants"]) / 3
    save(create_choropleth_map(X, "overall_score", color_scale="rdylgn", quantile_cap=CENTRALITY_PERCENTILE),
         "overall")

    print("Done.")


if __name__ == "__main__":
    main()
