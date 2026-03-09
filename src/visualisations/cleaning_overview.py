#Import packages
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import date

def create_check_overview_figure(columns, counts, total_records):
    """Creates a bar chart, with % of records as y-axis and type of error on x-axis showing the proportion
    of the different types of errors."""

    percent_list = []
    for count in counts:
        percent = count/total_records*100
        percent = round(percent, 1)
        percent_list.append(percent)

    #Create figure
    fig = px.bar(x=columns, y=percent_list, labels=['Data Checks', '% of Records'])

    #Custom data for hover
    customdata = np.stack(counts)

    #Hover data temmplate
    hovertemp = "<b>%{x}: %{y} % <br> <br>"
    hovertemp += "<b>No. affected records: </b> %{customdata} <br>"
    hovertemp += f"<b>Total no. records: </b>{total_records}<br>"

    #Add hover data
    fig.update_traces(
        patch={
        'customdata':customdata,
        'hovertemplate':hovertemp
        }
    )

    #Add axis labels
    fig.update_layout(
        xaxis_title='Data Checks',
        yaxis_title='% of records',
    )

    return fig


def create_percent_clean(df: pd.DataFrame):
    """Creates a pie chart showing proportions of records with 0, 1, 2 errors etc. 
    0 represents data with no errors."""


    df['ERRORS'] = np.where(df['ERROR_COUNT']>0, 'ERRORS', 'NO ERRORS')
    #df = df['ERROR_COUNT'].value_counts().rename_axis('NUMBER OF ERRORS').reset_index(name='NUMBER OF RECORDS')
    df = df['ERRORS'].value_counts().rename_axis('ERRORS').reset_index(name='NUMBER OF RECORDS')

    #In case all records have errors e.g. in fake_data
    if 'NO ERRORS' not in df['ERRORS']:
        df.loc[len(df.index)] = ['NO ERRORS', 0]
        
    total_records = df['NUMBER OF RECORDS'].sum()

    no_error_records = df.loc[df['ERRORS']=='NO ERRORS', 'NUMBER OF RECORDS'].values[0]
    percent_clean = no_error_records/total_records
    if percent_clean >= 0.8:
        error_color = 'EAEFCB'
    elif percent_clean >= 0.6:
        error_color = '#FDEE87'
    else:
        error_color = '#E55451'

    colors = {'NO ERRORS': '#40A260', 'ERRORS': error_color}


    fig = px.pie(
        df, 
        values='NUMBER OF RECORDS', 
        names='ERRORS',
        color='ERRORS',
        color_discrete_map=colors,
        title='% listings with and without errors')
    
    fig.update_layout(
        margin=dict(l=40, r=20, t=40, b=0)
    )

    fig.update_layout(legend=dict(
    orientation="h",
    yanchor="bottom",
    y=0.95,
    xanchor="right",
    x=1
))      


    return fig



def get_worst_subjects(df: pd.DataFrame, blinded: bool, fake: bool) -> pd.DataFrame:
    """Returns dataframe containing subjects with top 3 highest number of records containing errors."""

    if blinded or fake:
        subj = 'USUBJID'
    else:
        subj = 'SUBJID'

    df = df.groupby(by=['STUDYID', subj])['ERROR_COUNT'].apply(lambda x: (x>0).count()).reset_index(name='NO. RECORDS WITH ERRORS')
    df = df.drop(columns='STUDYID')

    return df.nlargest(3, 'NO. RECORDS WITH ERRORS')
