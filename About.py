import streamlit as st
st.set_page_config(layout="wide")

col1, col2 = st.columns([0.25, 0.75])

with col1:
    st.image('photos/IMG_0830.jpg', use_container_width=False,
             width=300
    )
with col2:
    st.title("Hi -- I'm Vu0ng.")
    st.markdown("I'm a prolific producer of abandoned projects. This is my attempt to commit to at least some of them. Each page you see is a win against procrastination! :blossom:")
    st.subheader("What I do and why I do")
    st.markdown("""
        Whenever I am faced with a big life decision or dilemma, I gravitate
        towards formulating it as a mathematical model. To me, the joy of doing this is not that it gives exact answers to
        life's problems (nor can it), but that it transforms them into something solvable.
        
        \nIf only every life problem has a closed form solution!
        In my mind, they do. Except when they don't. Then I cry and eat ice cream, like everyone else. :heart:
        """)
