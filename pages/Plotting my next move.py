"""
Static version of the NYC neighborhood analysis.

The heavy geo/network pipeline (geopandas, networkx, h3pandas, contextily,
census) is pre-computed offline by prerender/prerender_nyc.py, which writes the
maps and ranking table into assets/maps/. This page only embeds those artifacts
so it runs in the browser (stlite/Pyodide) with just streamlit + pandas.
"""
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(layout="wide")

MAPS = "assets/maps"
MAP_HEIGHT = 620


def show_map(name: str):
    """Embed a pre-rendered self-contained Plotly map."""
    with open(f"{MAPS}/{name}.html", encoding="utf-8") as f:
        components.html(f.read(), height=MAP_HEIGHT, scrolling=False)


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

col1, col2, col3 = st.columns([0.25, 0.5, 0.25])
col2.image(f"{MAPS}/nyc_mta_network.png", use_container_width=True,
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

col1, col2 = st.columns([0.3, 0.7])
with col1:
    st.dataframe(pd.read_csv(f"{MAPS}/station_centrality.csv"), hide_index=True)
with col2:
    show_map("centrality")
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
show_map("trees")
st.markdown("*Note: tree counts have been normalized to a score of between 0-1.*")

# Section 3: Restaurants
st.markdown("## 3 Restaurants")
st.markdown("""I grabbed the list of all restaurants that had an inspection between 2023-2024 and new restaurants not yet inspected.""")
show_map("restaurants")

# Overall Score
st.markdown("## Overall score")
st.markdown("""
Since the # of the trees happened to distinguish well the residential areas, I ended up weighing it twice as much as the other two
            in order to break up the Manhattan monolith.
""")
show_map("overall")

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
