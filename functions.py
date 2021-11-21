import pandas as pd
import altair as alt

def plot_cases(df_role, n_max):
    '''Create interactive 2-panel plot to visualize cases overview and case breakdown.'''
    selector = alt.selection_multi(empty='all', fields=['AreaDesc'])

    bars_area = alt.Chart(df_role).mark_bar().encode(
        x=alt.X('count()', title=None),
        y=alt.Y('AreaDesc', title=None, sort=alt.Order(field='AreaDesc')),
        color=alt.condition(
            selector,
            'AreaDesc',
            alt.value('lightgray'),
            title='Area'
        ),
        tooltip=[
            alt.Tooltip('AreaDesc', title='Category'),
            alt.Tooltip('count()', title='Count')]
    ).properties(
        title='Number of Cases, by Area'
    )

    text_area = bars_area.mark_text(
        align='left',
        baseline='middle',
        dx=3,
    ).encode(
        text='count()'
    )

    bars_type = alt.Chart(df_role).mark_bar().encode(
        # x=alt.X('count()', title=None, scale=alt.Scale(domain=[0, n_max])),
        x=alt.X('count()', title=None),
        y=alt.Y('TypeDesc', title=None, sort=alt.Order(field='AreaDesc')),
        color='AreaDesc',
        tooltip=[
            alt.Tooltip('TypeDesc', title='Type'),
            alt.Tooltip('AreaDesc', title='Category'),
            alt.Tooltip('count()', title='Count'),
        ]
    ).properties(
        title='Number of Cases, by Type',
    ).transform_filter(
        selector
    )

    text_type = bars_type.mark_text(
        align='left',
        baseline='middle',
        dx=3,
    ).encode(
        text='count()'
    )

    chart_area = alt.layer(bars_area, text_area).add_selection(selector)
    chart_type = alt.layer(bars_type, text_type)
    chart = chart_area | chart_type
    return chart

def plot_timeline(df_role):
    '''Create interactive case timeline.'''
    selection = alt.selection_interval(bind='scales')
    selection2 = alt.selection_multi(fields=['AreaDesc'], bind='legend')
    chart = alt.Chart(df_role).mark_bar().encode(
        x=alt.X(
            'ProcedureDate',
            title='',
        ),
        y=alt.Y('count(AreaDesc)', title='Number of Cases'),
        color=alt.Color('AreaDesc', title='Area'),
        tooltip=['ProcedureDate'],
        opacity=alt.condition(selection2, alt.value(1), alt.value(0.2)),
    ).add_selection(
        selection, selection2
    )
    return chart

def plot_minimums(df, mins):
    '''
    Create bar plot showing progress toward minimum requirements. Green bars denote cases completed, red lines denote the minimum threshold. The highest value is displayed (either the case count in green or the minimum threshold in red).
    '''
    minimums = get_minimums(df, mins)

    minimums['display'] = minimums[['Total', 'Minimum']].max(axis=1)

    base = alt.Chart(minimums).encode(
        y=alt.Y('Category', title=None),
    )
    bars = base.mark_bar(opacity=0.7, color='green').encode(
        x=alt.X('Total', title=None),
        tooltip=[alt.Tooltip('Total', title='Number of cases')]
    )
    ticks = base.mark_tick(color='#e45756').encode(
        x=alt.X('Minimum', title=None),
        tooltip=[alt.Tooltip('Minimum', title='Minimum requirement')]
    )
    text_cases = bars.mark_text(
        align='left',
        baseline='middle',
        dx=3,
        color='green',
    ).encode(
        text=alt.condition(
            # alt.datum.Total == alt.datum.display,
            alt.datum.Total >= alt.datum.Minimum,
            'Total:Q', alt.value('')
        )
    )
    text_minimums = ticks.mark_text(
        align='left',
        baseline='middle',
        dx=3,
        color='#e45756',
    ).encode(
        text=alt.condition(
            # alt.datum.Minimum == alt.datum.display,
            alt.datum.Minimum > alt.datum.Total,
            'Minimum:Q', alt.value('')
        )
    )
    chart = bars + ticks + text_cases + text_minimums
    return chart

def read_and_clean_data(uploaded_file):
    '''
    Read and clean data. Currently replacing "Surgeon" with "Primary" - can consider reversing this in the future.
    '''
    df = pd.read_csv(
        uploaded_file, parse_dates=['ProcedureDate'])
    df['ResidentRole'] = df['ResidentRole'].map(
        {'Surgeon': 'Primary', 'Assistant': 'Assistant'})
    return df

def get_information(df, role):
    '''Extract case information for display in the Overview section.'''
    n_cases = df.value_counts('ResidentRole')
    n_surgeries = df[['ResidentRole', 'CaseID', 'ProcedureDate']
                ].drop_duplicates().value_counts('ResidentRole')
    df_role = df[df['ResidentRole'] == role]
    n_max = df_role.groupby('AreaDesc')['AreaDesc'].count().max()
    return df_role, n_cases, n_surgeries, n_max
        
def get_minimums(df, mins):
    '''Calculate progress toward the minimum requirements.'''
    # Note the ACGME download adds ", Oculoplastics and Orbit" to the "DefinedCategories" column for "Ptosis/blepharoplasty", "Eyelid Laceration", and "Chalazion Excision" (e.g. "Oculoplastic and Orbit - Ptosis/blepharoplasty, Oculoplastic and Orbit"). This causes these entries to not match with the minimums table

    # So, let's only keep the data before the comma
    df['DefinedCategories'] = (
        df['DefinedCategories']
        .str
        .split(',', expand=True)[0]
    )

    # The ACGME download separates Oculoplastic and Orbit from Chalazion, Eyelid, and Ptosis, but the overarching category should contain all data (this is what the ACGME Ophthalmology Minimum report does as well)
    # So, let's add those numbers back into the total category
    # We'll have to do this in separate steps, given the above

    # First, calculate minimums
    minimums = (df
                .value_counts(['DefinedCategories', 'ResidentRole'])
                .unstack()
                .rename_axis('', axis='columns')
                .reset_index()
                )

    # Next calculate the totals across all oculoplastics
    totals = (minimums[minimums['DefinedCategories']
                    .str
                    .contains('Oculoplastic and Orbit')]
            # .contains('Oculoplastic and Orbit')][['Assistant', 'Primary']]
            .sum(axis=0)
            )

    # Now let's correct the counts
    # Add this new row, remove the old row, then rename
    minimums = minimums.append(totals, ignore_index=True)
    minimums = minimums.query("DefinedCategories != 'Oculoplastic and Orbit'").copy()
    minimums.loc[minimums['DefinedCategories'] == totals[0],
                'DefinedCategories'] = 'Oculoplastic and Orbit'

    # Now we can merge with the minimums table and clean the output
    minimums = (minimums
                .merge(mins, how='right')
                .fillna(0)
                )

    for col in 'Assistant', 'Primary':
        minimums[col] = minimums[col].astype(int)
    minimums['Total'] = minimums['Primary'] + minimums['Assistant']
    minimums = minimums[['Category', 'Primary',
                        'Assistant', 'Total', 'Minimum']]
    return minimums
