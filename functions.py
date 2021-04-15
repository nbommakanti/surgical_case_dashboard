import pandas as pd
import altair as alt

def plot_cases(df_role, n_max):
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
    surgeon = mins.query('WhichRole=="S"')['DefinedCategories']
    and_assistant = mins.query('WhichRole=="S+A"')['DefinedCategories']
    cases_done = (df
                .value_counts(['ResidentRole', 'DefinedCategories'])
                .reset_index(name='n')
                .query(
                    "(DefinedCategories in @surgeon & ResidentRole in 'Primary') \
            | DefinedCategories in @and_assistant")
                .groupby('DefinedCategories')
                )[['n']].sum().reset_index()

    cases_done = cases_done.merge(mins, how='right').fillna(0)
    cases_done['n'] = cases_done['n'].astype(int)
    cases_done['display'] = [max(n, M) for n, M in zip(
        cases_done['n'], cases_done['Minimum'])]
    base = alt.Chart(cases_done).encode(
        y=alt.Y('Category', title=None),
    )
    bars = base.mark_bar(opacity=0.7, color='green').encode(
        x=alt.X('n', title=None),
        tooltip=[alt.Tooltip('n', title='Number of cases')]
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
            alt.datum.n == alt.datum.display,
            'n:Q', alt.value('')
        )
    )
    text_minimums = ticks.mark_text(
        align='left',
        baseline='middle',
        dx=3,
        color='#e45756',
    ).encode(
        text=alt.condition(
            alt.datum.Minimum == alt.datum.display,
            'Minimum:Q', alt.value('')
        )
    )
    chart = bars + ticks + text_cases + text_minimums
    return chart

def read_and_clean_data(uploaded_file):
    df = pd.read_csv(
        uploaded_file, parse_dates=['ProcedureDate'])
    df['ResidentRole'] = df['ResidentRole'].map(
        {'Surgeon': 'Primary', 'Assistant': 'Assistant'})
    return df

def get_information(df, role):
    n_cases = df.value_counts('ResidentRole')
    n_surgeries = df[['ResidentRole', 'CaseID', 'ProcedureDate']
                ].drop_duplicates().value_counts('ResidentRole')
    df_role = df[df['ResidentRole'] == role]
    n_max = df_role.groupby('AreaDesc')['AreaDesc'].count().max()
    return df_role, n_cases, n_surgeries, n_max
        
def get_minimums(df, mins):
    minimums = (df
                .value_counts(['DefinedCategories', 'ResidentRole'])
                .unstack()
                .rename_axis('', axis='columns')
                .reset_index()
                .merge(mins, how='right')
                .fillna(0)
                )
    for col in 'Assistant', 'Primary':
        minimums[col] = minimums[col].astype(int)
    minimums['Total'] = minimums['Primary'] + minimums['Assistant']
    minimums = minimums[['Category', 'Primary',
                         'Assistant', 'Total', 'Minimum']]
    return minimums
