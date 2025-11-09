import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import curve_fit
from utils import configure_page

configure_page(layout="wide", title="Puppy Weight Calculator")
st.title("Estimating mixed puppies' adult weight")

col1, col2, col3= st.columns([0.85, 1, 1])
with col1:
    st.image('photos/baby_pippy.png',
         caption="Baby Pippy on his adoption day, June 13, 2022 (3 months old)",
         width=170)
with col2:
    st.image('photos/teen_pip.png',
         caption="Awkward leggy teenage phase (6 months old)",
         width=195)
with col3:
    st.image('photos/old_pippy.png',
         caption="Old man Chip (1 year old)",
         width=220)
    
st.markdown("""When I first got Chip, I was looking for a pocketable city dog and was assured by the shelter that he was a 'Chiyorkie' mix and wouldn't grow to exceed 15 lbs.
            I knew something was up when I picked him up and he was much bigger than he had appeared in the pictures.
            When I took him to the vet that same day, he was already 11.4 lbs at 14 weeks old and underweight.
            For the next 9 months, I would become obsessed with estimating his adult weight. I checked his weight religiously and
            made the following toy model. His final adult weight is 29.5-30.0 lbs, so it turns out that a sigmoid function is pretty good
            at capturing puppies' growth (at least with N = 1 :slightly_smiling_face:.)""")

def sigmoid(x, L ,x0, k, b):
    y = L / (1 + np.exp(-k*(x-x0))) + b
    return (y)

df = pd.DataFrame(
    [
        (10.0,7),
        (14.0,11.35),
        (16.5,14.22),
        (18.0,15.4),
        (22.0,20.2),
        (23.0,21.4),
        (23.5,21.8),
        (24.0,22.2),
        (25.0,22.8),
        (26.5,23.5),
        (27.3,25.1),
        (27.4,25.9),
        (28.0,24.9),
        (28.5,24.9),
        (29.0,24.9),
        (29.7,26.4),
        (31.0,26.9),
        (32.0,27.7),
        (32.7,27.4),
        (33.0,27.5),
    ],
    columns=['age (wks)', 'weight (lbs)']
)

col1, col2 = st.columns([1, 1])
with col1:
    user_df = st.data_editor(df, num_rows='dynamic')
with col2:
    max_age_range = st.number_input(
    "Max age (wks) range to plot*",
    min_value=48,
    value=52,
    step=1,
    )
    st.markdown("*The age to reach adult size varies between breeds -- some as little as 6 months, others as many as 24!")

x = user_df['age (wks)']
y= user_df['weight (lbs)']

p0 = [max(y), np.median(x),1,min(y)]

popt, pcov = curve_fit(sigmoid, x, y,p0, method='dogbox')
x_pred = np.linspace(0, max_age_range)
y_pred = sigmoid(x_pred, *popt)

adult_weight = popt[0] + popt[-1] # lim(x->inf) = L + b 
# set container, centered plot
col1, col2, col3 = st.columns([0.2, .6, 0.2])
with col2:
    plt.scatter(user_df['age (wks)'], user_df['weight (lbs)'], label='data', alpha=0.8, s=10)
    plt.plot(x_pred, y_pred, c='red', label='pred')
    plt.axhline(y=adult_weight, color='k', linestyle='--', label=f'Adult weight = {round(adult_weight, 1)} lbs')

    plt.xlabel("Age (weeks)")
    plt.ylabel("Weight (lbs)")
    plt.title("Age vs. weight")
    plt.grid()
    plt.legend()

    plt.tight_layout()
    st.pyplot(plt.gcf(), use_container_width=True) 