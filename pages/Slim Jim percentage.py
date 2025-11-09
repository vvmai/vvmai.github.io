import streamlit as st
from utils import configure_page
configure_page(layout="wide", title="Slim Jim Percentage")


col1, col2, col3= st.columns([1, 2, 1])

with col1:
    sj_ct = st.number_input(
    "Number of (full-sized) Slim Jims eaten today",
    min_value=0,
    value=None,
    step=1,
    )

    body_weight = st.number_input(
    "Body weight (lbs)",
    min_value=0,
    value=None,
    step=1,
    )

    comments = {
        'You are within the safe range of Slim Jim consumption.': (0, 0.5),
        'Whoa, slow down, cowboy': (0.5, 0.9),
        'Be careful -- you are asymptotically approaching Slim Jim totality!': (0.9, 1),
    }


    if sj_ct and body_weight:
        sj_lbs = sj_ct * 0.060625
        pct = sj_lbs/(body_weight + sj_lbs)
        st.write(f"You are ~{round(100*pct, 2)}% Slim Jim.")

        for comment, range in comments.items():
            if range[0] <= pct <= range[1]:
                st.write(comment)