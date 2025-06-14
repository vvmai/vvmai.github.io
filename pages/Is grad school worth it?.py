import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import LineString

st.set_page_config(layout="wide")
st.title("Short answer: maybe.")
st.markdown("""Long answer: to model the opportunity cost of attending grad school,
            I use the following analysis...""")

years = st.number_input(
    "Years",
    min_value=1,
    value=20,
    step=1
    )

col1, col2 = st.columns(2)

with col1:
    st.header("Scenario A: stay in industry")
    current_income = st.number_input(
        "Current income ($)",
        min_value=0,
        value=75000,
        step=1,
        )

    income_growth = st.number_input(
        "Yearly income growth (%)",
        min_value=0.0,
        value=6.5,
        )

    x_range = np.linspace(0, years, years)

    def A(x, current_income, income_growth, **kwargs):
        return current_income/1000*(1+income_growth/100)**x
    
    a = A(x_range, current_income, income_growth)

    plt.figure()
    plt.plot(x_range, a, c='blue', label='A')

    plt.title("Income over time")
    plt.xlabel("Years")
    plt.ylabel("Income (in $1k)")
    plt.grid()
    st.pyplot(plt.gcf())


with col2:
    st.header("Scenario B: go to grad school")
    years_of_school = st.number_input(
        "Years of school",
        min_value=0,
        value=2,
        step=1,
        )

    grad_school_income = st.number_input(
        "Grad school income ($)",
        value=-30000,
        step=1,
        )

    grad_income_growth = st.number_input(
        "Grad school income growth (%)",
        min_value=0.0,
        value=0.0,
        )

    post_grad_income = st.number_input(
        "Post-grad income ($)",
        min_value=0,
        value=100000,
        )

    post_grad_income_growth = st.number_input(
        "Post-grad income growth (%)",
        min_value=0.0,
        value=8.5,
        )

    plt.figure()

    def B(x, grad_school_income, grad_income_growth, post_grad_income, post_grad_income_growth, years_of_school, **kwargs):
        x_school = x[x <= years_of_school]
        x_postgrad = x[x > years_of_school]

        return np.concatenate([grad_school_income/1000*(1+grad_income_growth/100)**x_school\
            , post_grad_income/1000*(1+post_grad_income_growth/100)**(x_postgrad-(years_of_school + 1))])
    

    b = B(x_range, grad_school_income, grad_income_growth, post_grad_income, post_grad_income_growth, years_of_school)
    plt.plot(x_range, b, c='red', label='B')

    plt.title("Income over time")
    plt.xlabel("Years")
    plt.ylabel("Income (in $1k)")
    plt.grid()
    st.pyplot(plt.gcf())

plt.figure()
plt.plot(x_range, np.array(a).cumsum()/100, c='blue', label='A')
plt.plot(x_range, np.array(b).cumsum()/100, c='red', label='B')

def C(x, current_income, income_growth, grad_school_income, grad_income_growth, post_grad_income, post_grad_income_growth, years_of_school):
    y = np.array(A(x, current_income, income_growth)).cumsum()/100\
    - np.array(B(x, grad_school_income, grad_income_growth, post_grad_income, post_grad_income_growth, years_of_school)).cumsum()/100

    return y

plt.title("Wealth over time")
plt.legend()
plt.xlabel("Years")
plt.ylabel("Income cumulative sum (in $100k)")
plt.grid()
st.pyplot(plt.gcf())


A_line = LineString(np.column_stack((x_range, np.array(a).cumsum()/100)))
B_line = LineString(np.column_stack((x_range, np.array(b).cumsum()/100)))

intersection = B_line.intersection(A_line)

if intersection.is_empty:
    intersection = None
elif intersection.geom_type == 'MultiPoint':
    intersection = round(intersection.geoms[0].x, 1)
elif intersection.geom_type == 'Point':
    intersection = round(intersection.x, 1)

st.markdown("The roots of A - B (opportunity cost) gives us the breakeven point (if it exists):")
c = C(x_range, current_income, income_growth, grad_school_income, grad_income_growth, post_grad_income, post_grad_income_growth, years_of_school)
plt.figure()
plt.plot(x_range, c, c='green', label='A - B')

if intersection:
    plt.axvline(x=intersection, color='k', linestyle='--', label=f"Breakeven = {intersection} years")

plt.grid()
plt.title("Opportunity cost over time")
plt.legend()
plt.xlabel("Years")
plt.ylabel("Opportunity cost (in $100k)")
st.pyplot(plt.gcf())

if intersection:
    st.markdown(f"Congratulations! Going to grad school will net positive in {intersection} years!")
else:
    st.markdown(f"No breakeven found... you'll never financially recover from this (try increasing the time horizon).")


st.markdown("""Obviously, this toy model doesn't capture the risks involved in each scenario, which can be great, depending on your situation.
            But what it does provide is some insight into the sensitivity of your
            outcomes to these limited assumptions. In my case (not pictured), the answer to the question of
            whether grad school was worth it (from a financial point of view) is a resounding NO!""")

st.markdown("""But will that stop me? Stay tuned...""")