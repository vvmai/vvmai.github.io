import streamlit as st

pg = st.navigation([st.Page("About.py"),
                    st.Page("pages/Puppy weight calculator.py"),
                    st.Page("pages/Slim Jim percentage.py"),
                    st.Page("pages/Plotting my next move.py"),
                    st.Page("pages/Is grad school worth it?.py"),
                    st.Page("pages/A special case of the inspection paradox.py"),
                    ])

pg.run()