import numpy as np
import streamlit as st
import pandas as pd
import altair as alt
from functions import plot_cases, plot_minimums, plot_timeline, read_and_clean_data, get_information, get_minimums

st.set_page_config(
    page_title='Surgical Case Dashboard',
    layout='wide', 
    initial_sidebar_state='collapsed',
    )

# Set app layout
title = st.beta_container()
sidebar = st.sidebar
expander1 = st.beta_expander('', expanded=True)
header1 = st.beta_container()
overview = st.beta_container()
timeline = st.beta_container()
header2 = st.beta_container()
minimums = st.beta_container()
data = st.beta_container()

# Generate app elements
with title:
    st.write('# Ophthalmology Surgical Case Dashboard')

with sidebar:
    st.write('## Description')
    st.write("""
        - This is a dashboard for ophthalmology residents who are interested in exploring their ACGME case log data 
    """)
    st.write('## Instructions')
    st.write("""
        1. Download your case log data in `.csv` format from the ACGME website (see below for the link)
        1. Upload your data in the "Choose a file" section
        1. Select whether you want to see your cases as *Primary* or *Assistant* surgeon
        1. Expand any options (denoted with an underlined `+`) and adjust them as you see fit
    """)
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

    with header1:
        st.write(f'## Cases as {role} Surgeon')

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

    with header2:
        st.write('## Cases as Primary and Assistant Surgeon')
        
    with minimums:
        st.write('### Minimums')
        st.write('Here is your progress toward the ACGME minimum requirements:')
        chart_minimums = plot_minimums(df, mins)
        st.altair_chart(chart_minimums, use_container_width=True)

    with data:
        # Options and output minimums data
        st.write('### Tables')
        with st.beta_expander(''):
            show_table = st.checkbox('Show Table', value=True)
        if show_table:
            st.write('Here is a table with your progress toward the minimum requirements:')
            minimums = get_minimums(df, mins)
            st.write(minimums.set_index('Category'))

        # Options and output for all data 
        with st.beta_expander(''):
            show_data = st.checkbox('Show Data', value=True)
            useful_cols = [
                'ProcedureDate', 'ResidentRole', 'AreaDesc',
                'TypeDesc', 'DefinedCategories', 'CPTDesc', 'YearOfCase'
            ]
            columns = st.multiselect(
                'Select columns', 
                options=list(df_role.columns),
                default=useful_cols)
            filter_TypeDesc = st.text_input(label='Filter `TypeDesc`')
            filter_CPTDesc = st.text_input(label='Filter `CPTDesc`')
            case_years = df_role['YearOfCase'].unique().tolist()
            # st.write(case_years.tolist())
            filter_YearOfCase = st.multiselect(
                label='Filter `YearOfCase`', 
                options=case_years,
                default=case_years,
            )
        if show_data:
            output = (df_role
                        .loc[:, columns]
                        .loc[lambda x: x['TypeDesc'].astype(str).str.contains(filter_TypeDesc, case=False)]
                        .loc[lambda x: x['CPTDesc'].astype(str).str.contains(filter_CPTDesc, case=False)]
                        .loc[lambda x: x['YearOfCase'].isin(filter_YearOfCase)]
            )
            # Change datetime format and sort (reverse chronological) for convenient viewing
            output = output.sort_values('ProcedureDate', ascending=False)
            output['ProcedureDate'] = output['ProcedureDate'].dt.strftime(
                '%b %d, %Y')
            st.write("""
                Here is all of your case log data. 
                You can select different columns and filter by procedure type and case year (expand the options above)! 
                Try clicking the column headers to sort the data or the arrow at the right to expand the table.
                """)
            st.write(output)

# https://github.com/streamlit/streamlit/issues/972
hide_footer_style = """
<style>
.reportview-container .main footer {visibility: hidden;}    
"""
st.markdown(hide_footer_style, unsafe_allow_html=True)
