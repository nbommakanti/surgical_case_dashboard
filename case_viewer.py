import numpy as np
import streamlit as st
import pandas as pd
import altair as alt
from functions import plot_cases, plot_minimums, plot_timeline, read_and_clean_data, get_information, get_minimums

st.set_page_config(layout='wide', initial_sidebar_state='collapsed')

# Set app layout
header = st.beta_container()
sidebar = st.sidebar
expander1 = st.beta_expander('', expanded=True)
overview = st.beta_container()
timeline = st.beta_container()
minimums = st.beta_container()
data = st.beta_container()

# Generate app elements
with header:
    st.write('# Case Viewer')

with sidebar:
    st.write('## Useful links')
    st.markdown("""
    - [ACGME Login](https://apps.acgme-i.org/connect/login)
    - [ACGME Case Log Information](https://www.acgme.org/Portals/0/PFAssets/ProgramResources/OPH_CaseLogInfo.pdf?ver=2021-03-15-133325-270)
    """)

uploaded_file = expander1.file_uploader('Choose a file')

if uploaded_file is not None: # Only run once file is uploaded
    df = read_and_clean_data(uploaded_file)
    mins = pd.read_csv('./minimums.csv')

    with expander1:
        role = st.selectbox(label='Select role', options=['Primary', 'Assistant'])

    header.write(f'## {role} Surgeon')

    with overview:
        df_role, n_cases, n_surgeries, n_max = get_information(df, role)

        st.write('### Overview')
        st.write(
            f""" As *{role.lower()}* surgeon, you completed **{n_cases[role]}** cases
            (**{n_surgeries[role]}** unique procedures or surgeries)!"""
            )
        st.write('Here\'s your case breakdown by area and type (try clicking the bars on the left):')
        chart_cases = plot_cases(df_role, n_max)
        st.altair_chart(chart_cases, use_container_width=True)

    with timeline:
        st.write('### Timeline')
        chart_timeline = plot_timeline(df_role)
        st.altair_chart(chart_timeline, use_container_width=True)

    with minimums:
        st.write('### Minimums')
        st.write('Here is your progress toward the ACGME minimum requirements:')
        chart_minimums = plot_minimums(df, mins)
        st.altair_chart(chart_minimums, use_container_width=True)

    with data:
        st.write('### Tables')
        with st.beta_expander(''):
            show_table = st.checkbox('Show minimums table', value=True)
        if show_table:
            st.write('Here is a table with your progress toward the minimum requirements:')
            minimums = get_minimums(df, mins)
            st.write(minimums.set_index('Category'))
        with st.beta_expander(''):
            show_data = st.checkbox('Show all data', value=True)
            useful_cols = [
                'ProcedureDate', 'ResidentRole', 'AreaDesc',
                'TypeDesc', 'DefinedCategories', 'CPTDesc', 'YearOfCase'
            ]
            columns = st.multiselect(
                'Select columns', 
                options=list(df_role.columns),
                default=useful_cols)
        if show_data:
            st.write('Here is all your case log data. You can select different columns and (later) filter by type and date!')
            st.write(df_role[columns])

# https://github.com/streamlit/streamlit/issues/972
hide_footer_style = """
<style>
.reportview-container .main footer {visibility: hidden;}    
"""
st.markdown(hide_footer_style, unsafe_allow_html=True)
