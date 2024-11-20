import streamlit as st
home = st.Page("home.py", title="Shorthand Input")
instructions = st.Page("tutorial.py", title = "Shorthand Syntax")
pg = st.navigation([home, instructions])
pg.run()
#USE STREAMLIT RUN -filename.py-