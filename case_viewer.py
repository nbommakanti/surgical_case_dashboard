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
minimums_plot = st.beta_container()
minimums_data = st.beta_container()
all_data = st.beta_container()

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
        1. Expand or collapse any options (denoted with an underlined `+` or `-`) and adjust them as you see fit
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
        
    with minimums_plot:
        st.write('### Minimums')
        st.write('Here is your progress toward the ACGME minimum requirements:')
        chart_minimums = plot_minimums(df, mins)
        st.altair_chart(chart_minimums, use_container_width=True)

    with minimums_data:
        # Minimums data
        st.write('### Tables')
        st.write('Here is a table with your progress toward the minimum requirements:')
        minimums = get_minimums(df, mins)
        st.write(minimums.set_index('Category'))

    with all_data:
        # Filtering options
        with st.beta_expander('', expanded=True):
            # with st.form(key='options'):
            # the new st.form is not yet supported on streamlit sharing. commenting this out for now (this means the table will throw an error temporarily when selecting dates)
            # Input for column selection
            useful_cols = [
                'ProcedureDate', 'ResidentRole', 'AreaDesc',
                'TypeDesc', 'DefinedCategories', 'CPTDesc', 'YearOfCase'
            ]
            columns = st.multiselect(
                'Columns', 
                options=list(df_role.columns),
                default=useful_cols
            )
            filter_cols = st.beta_columns(4)
            with filter_cols[0]:
                first_date = df['ProcedureDate'].min()
                last_date = df['ProcedureDate'].max()
                date_range = st.date_input(
                    label='Dates',
                    value=[first_date, last_date],
                    min_value=first_date,
                    max_value=last_date,
                )
            date_range = pd.to_datetime(date_range)
            with filter_cols[1]:
                filter_term = st.text_input(
                    label='Filter')
            with filter_cols[2]:
                filter_ResidentRole = st.multiselect(
                    label='Role',
                    options=['Primary', 'Assistant'],
                    default=['Primary', 'Assistant']
                )
            with filter_cols[3]:
                case_years = df_role['YearOfCase'].unique().tolist()
                filter_YearOfCase = st.multiselect(
                    label='Case Year', 
                    options=case_years,
                    default=case_years,
                )
                # submitted = st.form_submit_button('Apply Selections')
        
        # Filter by role, case year, procedure date, and selected columns
        output = (df
                    .loc[lambda x: x['ResidentRole'].isin(filter_ResidentRole)]
                    .loc[lambda x: x['YearOfCase'].isin(filter_YearOfCase)]
                    .loc[lambda x: x['ProcedureDate'] >= date_range[0]]
                    .loc[lambda x: x['ProcedureDate'] <= date_range[1]]
                    .loc[:, columns]
        )

        # Filter by search term(s)
        mask = output.apply(lambda row: row.astype(str).str.contains(filter_term, case=False).any(), axis=1)
        output = output.loc[mask]

        # Change datetime format, sort (reverse chronological), and move to index for convenient viewing
        output['ProcedureDate'] = output['ProcedureDate'].dt.strftime(
            # '%b %d, %Y' # e.g. Apr 27, 2021. st.dataframe() doesn't sort these strings correctly when clicking column headers
            '%Y-%m-%d'
        )
        output = output.set_index('ProcedureDate').sort_index(ascending=False)

        # Display data
        st.write("""
            Here is all of your case log data:
            """)
        st.write(output)

# https://github.com/streamlit/streamlit/issues/972
hide_footer_style = """
<style>
.reportview-container .main footer {visibility: hidden;}    
"""
st.markdown(hide_footer_style, unsafe_allow_html=True)
