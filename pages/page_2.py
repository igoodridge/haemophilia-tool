### Import Packages ###
import dash
from dash import dcc, html, dash_table, callback_context
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
from plotly import graph_objects as go
import numpy as np
import numpy as np

### Import Dash Instance ###
from app import app

from src.data_import.trial import Trial
from src.visualisations.dose import create_daily_dose_figure, create_individual_subject_dose_graph




#Cache timeout
TIMEOUT = 3600


### Page 2 Layout and Callbacks ###
layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                                html.P('Select study day range:'),
                                dcc.RangeSlider(id='slider-dose-study-day',
                                                min=0,
                                                max=200,
                                                step=100,
                                                value=[0, 120], 
                                                persistence=True,
                                                persistence_type='session',
                                               )]),
                dbc.CardBody(html.Div(dbc.Spinner(
                    dcc.Graph(id='fig-dose',
                            responsive=True,
                            #style={'height': '100%'}
                            ))),
                 style= {'overflow':'scroll'},
                )
                ],
                color='information',
                style={'height':'50vh', 'width':'100%'}
                )],
                width=12, sm=12,
            )]),

    html.Br(),

    dbc.Row([

        dbc.Col([
                dbc.Card([
                dbc.CardHeader(html.H6('Doses')),
                dbc.CardBody(html.Div(dbc.Spinner(
                dash_table.DataTable(
                        id='table-dose',
                        style_table={'overflowX':'auto'},
                        page_size=8,
                        sort_action = 'native',
                        filter_action = 'native',
                        row_selectable = 'single',
                        style_as_list_view=True,
                        export_format='xlsx',
                        style_cell={'padding': '5px'},
                        style_header={
                            'backgroundColor': 'white',
                            'fontWeight': 'bold'
                        },
                        persistence=True,
                        persistence_type='session',
                    ))),
                    style={'overflow':'scroll'}
                    )
                    ],
                    color='information',
                    style={'height':'40vh'})],
                    width=7, sm=7),

            html.Br(),
                
            dbc.Col([

                dbc.Card([
                dbc.CardHeader(html.Div(id='individual-graph-header')),
                dbc.CardBody(html.Div(dbc.Spinner(
                    dcc.Graph(id='fig-individual-subject-dose',
                            responsive=True,
                            style={'height': '100%'}
                            ))), style={'overflow':'scroll'}
                )
                ],
                color='information',
                style={'height':'40vh'}
                )
        ],
        width=5, sm=5)]
    )], fluid=True,
)




@app.callback(
    [Output('table-dose', 'data'),
     Output('table-dose', 'columns'),
     Output('fig-dose', 'figure'),
     Output('fig-dose', 'style'),
     Output('slider-dose-study-day', 'min'),
     Output('slider-dose-study-day', 'max'),
     Output('radio-filters-dose', 'value')],
    [Input('trial-dropdown', 'value'),
     Input('slider-dose-study-day', 'value'),
     Input('fig-dose', 'clickData'),
    Input('radio-filters-dose', 'value'),
    Input('reset-button', 'n_clicks'),
    Input('user', 'data'),
    Input('dummy-div-dose', 'children'),
    Input('dose-length-slider', 'value')],
    [State('store-subject-data', 'data')]
)
def update_dose_table(trial, study_day_range, clickData, datafilter, n_clicks, user, dose_data, days_missed, subject_data):


    trigger = callback_context.triggered_id

    #Dose data too large to store in browser, so load in directly
    print('Getting dose data from Trial class...')
    dose = Trial(trial, user).get_dose()

    #print('Dose dtypes: ', dose.dtypes)

    #Set height of figure based on number of subjects

    subject_num = subject_data['subject_num']
    number_of_subjects = len(subject_num.keys())
    if number_of_subjects > 20:
        style = {'height': str(number_of_subjects * 20) + 'px'}
    else:
        style = {'height': '100%'}

    #Get maximum study day
    min_study_day = dose['STUDY_DAY_END'].min()
    max_study_day = dose['STUDY_DAY_END'].max()

    #Get value of range slider
    earliest_study_day = study_day_range[0]
    latest_study_day = study_day_range[1]

    #Filter dose based on rangeslider
    dose = dose.loc[(dose['STUDY_DAY_END']>=earliest_study_day) & (dose['STUDY_DAY_END']<=latest_study_day)]  

    if trigger != 'reset-button':

        if datafilter != 'None':
            dose['COLOR'] = np.where(dose[datafilter]=='N', '#B0B0B0', dose['COLOR'])
            if datafilter == 'MISSED_DOSES':
                dose['COLOR'] = np.where(dose['DAYS_SINCE_LAST_DOSE']<=days_missed, '#B0B0B0', dose['COLOR'])
    else:
        datafilter = 'None'

    #Create figure
    fig = create_daily_dose_figure(dose, subject_num)


    if trigger != 'reset-button':

        #Only show data in table corresponding to filter
        if datafilter != 'None':
            dose = dose.loc[dose[datafilter]=='Y']
            if datafilter == 'MISSED_DOSES':
                dose = dose.loc[dose['DAYS_SINCE_LAST_DOSE']>days_missed]

        if clickData is not None:
            subject = clickData['points'][0]['customdata'][0]
            dose = dose.loc[dose['USUBJID']==str(subject)]
    
    else:
        datafilter = 'None'

    
    dose = dose.sort_values(by=['USUBJID', 'STUDY_DAY_END', 'DOSE'])
    dose = dose.reindex(columns=['STUDYID', 'USUBJID', 'ECSCAT', 'DOSE', 'START_DATE_TIME', 'STOP_DATE_TIME', 'STUDY_DAY_START', 'STUDY_DAY_END', 'DAYS_SINCE_LAST_DOSE'])

    dose.START_DATE_TIME = pd.DatetimeIndex(dose.START_DATE_TIME).strftime('%d-%b-%Y')
    dose.STOP_DATE_TIME = pd.DatetimeIndex(dose.STOP_DATE_TIME).strftime('%d-%b-%Y')

    #Get list of dictionaries with name and id of each column in table
    columns = [{'name': i, 'id': i} for i in dose.columns]
    dose_data = dose.to_dict('records')

    #print(dose.head())

    return dose_data, columns, fig, style, min_study_day, max_study_day, datafilter

@app.callback(
    [Output('fig-individual-subject-dose', 'figure'),
     Output('individual-graph-header', 'children')],
    [Input('fig-dose', 'clickData'),
    Input('user', 'data')],
    [State('trial-dropdown', 'value')]
)
def show_individual_subject_dose_graph(clickData, user, trial):

    dose = Trial(trial, user).get_dose()

    # print(clickData)

    if clickData is not None:
        subject = clickData['points'][0]['customdata'][0]
        # print('Subject: ', subject)
        # print('Type: ', type(subject))
        subject_dose = dose.loc[dose['USUBJID']==str(subject)]
        individual_dose_graph = create_individual_subject_dose_graph(subject_dose)
        header = html.P('Dose over time for subject: ' + str(subject))
    else:
        individual_dose_graph = go.Figure()
        header = html.P('Dose over time for individual subjects.')
    
    return [individual_dose_graph, header]
  