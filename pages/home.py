### Import Packages ###
import dash
import re
from dash import dcc, html, callback, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import json
import pandas as pd


from src.visualisations.cleaning_overview import create_check_overview_figure, create_percent_clean, get_worst_subjects



# Import Dash Instance

from app import app


layout = dbc.Container([
    dbc.Row(children=[
        
        #Bleeding episode overview card
        dbc.Col(
            dbc.Card([
                    dbc.CardHeader(html.H5('Bleeding Episodes')),
                    dbc.CardBody([
                        dbc.Row(
                            html.Div(dbc.Spinner(dcc.Graph(id='fig-overview-bleed-errors')))),
                        dbc.Row([
                            dbc.Col([
                                html.P('Top 3 subjects with highest no. of records containing errors.'),
                                html.Div(dbc.Spinner(html.Div(id='bleeds-top-3-list')))],
                                width=5),
                            dbc.Col([
                                # html.P('Proportion of listings with and without errors'),
                                html.Div(dbc.Spinner(dcc.Graph(id='fig-percent-clean-bleeds')))], 
                                    width=7),
                        ], align='center')
                        ])
                    ], 
                color='information', 
                inverse=False), 
            width=4, 
            align='left'), 

        #Haemostatic medication overview card
        dbc.Col(
            dbc.Card([
                    dbc.CardHeader(html.H5('Haemostatic Medication')),
                    dbc.CardBody([
                        dbc.Row(
                        html.Div(dbc.Spinner(dcc.Graph(id='fig-overview-med-errors')))),
                        dbc.Row([
                            dbc.Col([
                                html.P('Top 3 subjects with highest no. of records containing errors.'),
                                html.Div(dbc.Spinner(html.Div(id='meds-top-3-list')))],
                                width=5),
                            dbc.Col([
                            # html.P('Proportion of listings with and without errors'),
                            html.Div(dbc.Spinner(dcc.Graph(id='fig-percent-clean-meds')))],
                                    width=7),
                            ], align='center'),
                        ])
            ],
                color='information', 
                inverse=False), 
            width=4, 
            align='left'), 


        #Doses overview card
        dbc.Col(
            dbc.Card([
                    dbc.CardHeader(html.H5('Trial Drug Doses')),
                    dbc.CardBody([
                        html.Div(dbc.Spinner(dcc.Graph(id='fig-overview-dose-errors'))),
            ])
                    ], 
                color='information', 
                inverse=False), 
            width=4, 
            align='left'), 


    
    ]),
    ], fluid=True)

@app.callback(
    [Output('fig-overview-bleed-errors', 'figure'),
    Output('fig-overview-med-errors', 'figure'),
    Output('fig-overview-dose-errors', 'figure')],
    Input('store-overview-data', 'data')
)
def create_bar_chart(data):

    fig_list = []

    for category in ['bleeds', 'meds', 'dose']:
        overview_data = data[category]
        columns = overview_data['columns']
        counts = overview_data['counts']
        total_records = overview_data['records']
        fig = create_check_overview_figure(columns, counts, total_records)
        fig_list.append(fig)
        #fig_list.append(total_records)

    return fig_list


@app.callback(
    [Output('fig-percent-clean-bleeds', 'figure'),
    Output('fig-percent-clean-meds', 'figure'),
    Output('bleeds-top-3-list', 'children'),
    Output('meds-top-3-list', 'children')],
    Input('store-bleed-med-data', 'data'),
    State('trial-dropdown', 'value')
)
def create_pie_chart(data, trial):

    if trial == 'nn1234-5678':
        fake = True
    else:
        fake = False
        
    #Blinding
    blinded = data.get('blinded')

    #Bleeds
    bleeds = pd.DataFrame(data.get('bleeds'))
    #Bleed pie chart
    fig_bleeds = create_percent_clean(bleeds)
    #Bleed top 3 SUBJs list
    bleed_top_three = get_worst_subjects(bleeds, blinded, fake)
    bleed_top_3_table = dbc.Table.from_dataframe(bleed_top_three, hover=True)

    #Med pie chart
    meds = pd.DataFrame(data.get('meds'))
    fig_meds = create_percent_clean(meds)

    #Med top 3 subjects
    med_top_three = get_worst_subjects(meds, blinded, fake)
    med_top_3_table = dbc.Table.from_dataframe(med_top_three, hover=True)

    return [fig_bleeds, fig_meds, bleed_top_3_table, med_top_3_table]




