### Import Packages ###
import dash
from dash import dcc, html, callback, dash_table, callback_context
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
from datetime import date


# Custom Packages
from src.visualisations.bleeds import Figures
from src.data_import.trial import Trial

# Import Dash Instance

from app import app

#Get today's date as datetime object
today = date.today()

### Page 1 Layout and Callback ###
layout = dbc.Container([
    dbc.Row([
        dbc.Col(
            dbc.Card([
                dbc.CardHeader([
                                html.H5('Bleeding episodes and haemostatic medication over time'),
                                html.Br(),
                                dcc.RangeSlider(min=2018, 
                                                max=2023, 
                                                step=0.5, 
                                                value=[2022, 2023], 
                                                persistence=True,
                                                persistence_type='session',
                                                id='slider-date',
                                                marks={2018:'2018', 
                                                        2018.5: '',
                                                        2019:'2019', 
                                                        2019.5: '',
                                                        2020:'2020', 
                                                        2020.5: '',
                                                        2021:'2021', 
                                                        2021.5: '',
                                                        2022:'2022',
                                                        2022.5: '', 
                                                        2023:'2023',
                                                       2023.5: ''}
                                                        ),
 
                                
                            ]),
                dbc.CardBody(
                        html.Div([
                                    dbc.Spinner(dcc.Graph(id='fig-bleeds',
                                                responsive=True,
                                                ))
                                ]),
                    
                 style= {'overflow':'scroll'},
                )
                ],
                color='secondary',
                style={'height':'90vh'}
                ),
                width=5, sm=6,
            ),
        dbc.Col([
                dbc.Card([
                dbc.CardHeader(html.H5('Bleeding Episodes', id='bleeding-episodes-table-header')),
                dbc.CardBody(html.Div(dbc.Spinner(
                dash_table.DataTable(
                        id='table-bleeds',
                        style_table={'overflowX':'auto'},
                        page_size=8,
                        sort_action = 'native',
                        filter_action = 'native',
                        style_as_list_view=True,
                        style_cell={'padding': '5px'},
                        style_header={
                            'backgroundColor': 'white',
                            'fontWeight': 'bold'
                        },
                        export_format='xlsx',
                        persistence=True,
                        persistence_type='session',
                    ))),
                    style={'overflow':'scroll'}),
                # dbc.CardFooter(
                #     [html.Div(
                #         children = dbc.Button('Save', id='save-bleed-data-input'),
                #         className="d-grid gap-2 d-md-flex justify-content-md-end"),
                #     html.Div(id='save-bleed-message', children=[]),
                #     ]),
                    ],
                    color='information',
                    style={'height':'44vh'}),


                    # dbc.Tooltip(
                    #         'Bleed data from ec and .',
                    #         target='radio-bleed-all',
                    #         placement='right',
                    #         ),

                html.Br(),
               
                dbc.Card([
                dbc.CardHeader(html.H5('Haemostatic Medication')),
                dbc.CardBody(html.Div(dbc.Spinner(
                dash_table.DataTable(
                        id='table-meds',
                        style_table={'overflowX':'auto'},
                        page_size=8,
                        sort_action = 'native',
                        filter_action = 'native',
                        export_format = 'xlsx',
                        style_as_list_view=True,
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
                    style={'height':'44vh'})
        ],                 
                    width=5, sm=6,
                ),    
    ]),
], fluid=True,
)


#Changes date range displayed in slider depending on trial 
@app.callback(
        [Output('slider-date', 'min'),
         Output('slider-date', 'max'),
        Output('date-picker-min', 'min_date_allowed'),
         Output('date-picker-min', 'max_date_allowed'),
        Output('date-picker-min', 'initial_visible_month'),
        Output('date-picker-max', 'min_date_allowed'),
        Output('date-picker-max', 'max_date_allowed'),
        Output('date-picker-max', 'initial_visible_month')
         ],
        [Input('store-bleed-med-data', 'data'),
         Input('slider-date', 'value'),
        Input('date-picker-min', 'date'),
        Input('date-picker-max', 'date')],
)
def update_date_range(bleed_data, slider_date_range, date_cutoff_start, date_cutoff_end):
    bleeds = pd.DataFrame(bleed_data['bleeds'])
    meds = pd.DataFrame(bleed_data['meds'])
    bleeds['BLEED_START_DATE'] = pd.to_datetime(bleeds['BLEED_START_DATE'], format='%Y-%m-%dT%H:%M:%S')
    bleeds['BLEED_STOP_DATE'] = pd.to_datetime(bleeds['BLEED_STOP_DATE'], format='%Y-%m-%dT%H:%M:%S')
    meds['HAEM_MED_DATE'] = pd.to_datetime(meds['HAEM_MED_DATE'], format='%Y-%m-%dT%H:%M:%S')
    lower_bound = bleeds['BLEED_START_DATE'].min()
    upper_bound = bleeds['BLEED_STOP_DATE'].max()
    slider_min = lower_bound.year
    slider_max = upper_bound.year
    lower_bound_str = lower_bound.strftime('%Y-%m-%d')
    upper_bound_str = upper_bound.strftime('%Y-%m-%d')
    return [slider_min, slider_max, lower_bound_str, upper_bound_str, lower_bound_str, lower_bound_str, upper_bound_str, upper_bound_str]


# #Updates the figure with the selected trial
@app.callback(
    [Output('fig-bleeds', 'figure'),
     Output('fig-bleeds', 'style')],
    [Input('trial-dropdown', 'value'),
    Input('store-bleed-med-data', 'data'),
    Input('store-subject-data', 'data'),
    Input('radio-filters-bleeds', 'value'),
    Input('slider-date', 'value'),
    Input('date-picker-min', 'date'),
    Input('date-picker-max', 'date'),
    Input('bleed-length-slider', 'value')
    ]
)
def create_figure(trial, bleed_data, subject_data, datafilter, date_range, start_date, end_date, bleed_length):  

    subject_num_fake = subject_data.get('subject_num_fake')


    blinded = subject_data.get('blinded')
    if blinded:
        subject_num = subject_num_fake
    else:
        subject_num = subject_data.get('subject_num')
    
    subjid_dict = subject_data.get('subjid_dict')
    
    #Set height of figure based on number of subjects
    number_of_subjects = len(subject_num.keys())
    if number_of_subjects > 30:
        style = {'height': str(number_of_subjects * 20) + 'px'}
    else:
        style = {'height': '100%'}

    ## Select data within date range (value 2020.5 is equivalent to 2020-06)
    # Find cutoff dates
    early_year = int(date_range[0])
    early_month = date_range[0] - early_year
    if early_month == 0.5:
        earliest_date = str(early_year) + '-06'
    else: 
        earliest_date = str(early_year)
    late_year = int(date_range[1])
    late_month = date_range[1] - late_year
    if late_month == 0.5:
        latest_date = str(late_year) + '-06'
    else:
        latest_date = str(late_year)
    
    if start_date is not None:
        start_date_object = date.fromisoformat(start_date)
        earliest_date = start_date_object.strftime('%d-%m-%Y')
    if end_date is not None:
        end_date_object = date.fromisoformat(end_date)
        latest_date = end_date_object.strftime('%d-%m-%Y')

    #Ensure correct date format (not properly saved by JSON file in dcc.Store)
    bleeds = pd.DataFrame(bleed_data.get('bleeds'))

    #print(bleeds)

    bleeds['BLEED_START_DATE'] = pd.to_datetime(bleeds['BLEED_START_DATE'], format='%Y-%m-%dT%H:%M:%S')
    bleeds['BLEED_STOP_DATE'] = pd.to_datetime(bleeds['BLEED_STOP_DATE'], format='%Y-%m-%dT%H:%M:%S')
    meds = pd.DataFrame(bleed_data.get('meds'))



    meds['HAEM_MED_DATE'] = pd.to_datetime(meds['HAEM_MED_DATE'], format='%Y-%m-%dT%H:%M:%S')



    #Filter for data between cutoffs
    bleeds = bleeds.loc[((bleeds['BLEED_START_DATE'] > earliest_date) & (bleeds['BLEED_START_DATE'] < latest_date))
                        &((bleeds['BLEED_STOP_DATE']<latest_date) | bleeds['BLEED_STOP_DATE'].isnull())]
    meds = meds.loc[(meds['HAEM_MED_DATE'] > earliest_date)&(meds['HAEM_MED_DATE']<latest_date)]


    #Highlight data corresponding to that check e.g. all bleeds with missing data will be highlighted in red; 
    # all other data will be turned grey
    if datafilter != 'None':
        if datafilter == 'LONG_BLEED' and bleed_length != 7:
            bleeds['COLOR'] = np.where(bleeds['BLEED_LENGTH']<=bleed_length, '#B0B0B0', bleeds['COLOR'])
        elif datafilter == 'OUTSIDE_BLEEDS':
            bleeds['COLOR'] = '#B0B0B0'
        else:
            bleeds['COLOR'] = np.where(bleeds[datafilter]=='N', '#B0B0B0', bleeds['COLOR'])

        if datafilter in ['MISSING', 'DUPLICATED', 'OUTSIDE_BLEEDS', 'TRT_N_BUT_MEDS']:
            #print('datafilter in list')
            meds['COLOR'] = np.where(meds[datafilter]=='N', '#B0B0B0', meds['COLOR'])
        else:
            #print('not a meds filter')
            meds['COLOR'] = '#B0B0B0'


    #print(meds.head())

    #Create figure
    figure = Figures(trial, bleeds, meds, subject_num, subjid_dict, blinded)
    fig = figure.create_bleed_figure()

    return [fig, style]



#Outputs the bleed table with date filters, check filters etc.
@app.callback(
    [Output('table-bleeds', 'data'),
     Output('table-bleeds', 'columns'),
     Output('table-meds', 'data'), 
     Output('table-meds', 'columns'),
    Output('radio-filters-bleeds', 'value')],
    [Input('store-bleed-med-data', 'data'),
     Input('trial-dropdown', 'value'),
     Input('radio-filters-bleeds', 'value'),
     Input('slider-date', 'value'),
    Input('fig-bleeds', 'clickData'),
    Input('reset-button', 'n_clicks')],
    [State('date-picker-min', 'date'),
    State('date-picker-max', 'date'),
    Input('bleed-length-slider', 'value')
    ],
)
def update_table(bleed_data, trial, datafilter, date_range, clickData, n_clicks, start_date, end_date, bleed_length):

    trigger = callback_context.triggered_id
    #print('Trigger: ', trigger)

    #print('clickData: ', clickData)

    bleed_df = pd.DataFrame(bleed_data.get('bleeds'))
    med_df = pd.DataFrame(bleed_data.get('meds'))
    blinded = bleed_data.get('blinded')

    bleed_df['USUBJID'] = bleed_df['USUBJID'].astype(str)
    med_df['USUBJID'] = med_df['USUBJID'].astype(str)

    earliest_date = str(date_range[0])
    latest_date = str(date_range[1])

    if start_date is not None:
        start_date_object = date.fromisoformat(start_date)
        earliest_date = start_date_object.strftime('%d-%m-%Y')
    if end_date is not None:
        end_date_object = date.fromisoformat(end_date)
        latest_date = end_date_object.strftime('%d-%m-%Y')

    if trigger != 'reset-button':

        if clickData is not None: 
            clickSUBJID = clickData['points'][0]['customdata'][0]
            bleed_df = bleed_df.loc[bleed_df['USUBJID']==clickSUBJID]
            med_df = med_df.loc[med_df['USUBJID']==clickSUBJID]

        bleed_df = bleed_df.loc[((bleed_df['BLEED_START_DATE'] >= earliest_date) & (bleed_df['BLEED_START_DATE'] < latest_date))&
                                ((bleed_df['BLEED_STOP_DATE']<=latest_date) | bleed_df['BLEED_STOP_DATE'].isnull())]
        med_df = med_df.loc[med_df['HAEM_MED_DATE'].between(earliest_date, latest_date)]
        if datafilter != 'None':
            if datafilter == 'LONG_BLEED' and bleed_length != 7:
                bleed_df = bleed_df.loc[bleed_df['BLEED_LENGTH']>bleed_length]
            elif datafilter == 'OUTSIDE_BLEEDS':
                bleed_df = pd.DataFrame()
            else:
                bleed_df = bleed_df.loc[bleed_df[datafilter]=='Y']

        if datafilter != 'None':
            if datafilter in ['MISSING', 'DUPLICATED', 'OUTSIDE_BLEEDS', 'TRT_N_BUT_MEDS']:
                med_df = med_df.loc[med_df[datafilter]=='Y']
            elif datafilter not in ['MISSING', 'DUPLICATED', 'OUTSIDE_BLEEDS', 'TRT_N_BUT_MEDS']:
                med_df = pd.DataFrame()
    
    else:
        datafilter = 'None'

 
    if blinded is False and trial != 'nn1234-5678':
        bleed_df = bleed_df.reindex(columns=['STUDYID', 'SUBJID', 'COUNTRY', 'BLEED_START_DATE', 'BLEED_STOP_DATE', 'BLEED_LOCATION', 'LATERAL_POSITION', 
                                                'BODY_PART', 'JOINT_LOCATION', 'BLEED_SEVERITY', 'BLEED_CAUSE', 'TREATYN', 'BLEED_LENGTH','USUBJID'])
    else:
        bleed_df = bleed_df.reindex(columns=['STUDYID', 'USUBJID', 'BLEED_START_DATE', 'BLEED_STOP_DATE', 'BLEED_LOCATION', 'LATERAL_POSITION', 'BODY_PART', 
                                                'JOINT_LOCATION', 'BLEED_SEVERITY', 'BLEED_CAUSE', 'TREATYN', 'BLEED_LENGTH'])
    if blinded is False and trial != 'nn1234-5678':
        med_df = med_df.reindex(columns=['STUDYID', 'SUBJID', 'COUNTRY', 'HAEM_MED_DRUG', 'HAEM_MED_DATE', 'HAEM_MED_DOSE', 'UNITS', 'HAEM_MED_TRT_TYPE', 'USUBJID'])
    else:
        med_df = med_df.reindex(columns=['STUDYID', 'USUBJID', 'HAEM_MED_DRUG', 'HAEM_MED_DATE', 'HAEM_MED_DOSE', 'UNITS', 'HAEM_MED_TRT_TYPE'])

    bleed_df.BLEED_START_DATE = pd.DatetimeIndex(bleed_df.BLEED_START_DATE).strftime('%d-%b-%Y')
    bleed_df.BLEED_STOP_DATE = pd.DatetimeIndex(bleed_df.BLEED_STOP_DATE).strftime('%d-%b-%Y')
    med_df.HAEM_MED_DATE = pd.DatetimeIndex(med_df.HAEM_MED_DATE).strftime('%d-%b-%Y')

    bleed_df = bleed_df.sort_values(by=['USUBJID', 'BLEED_START_DATE', 'BLEED_STOP_DATE'])
    med_df = med_df.sort_values(by=['USUBJID', 'HAEM_MED_DATE'])

    meds = med_df.to_dict('records')
    bleeds = bleed_df.to_dict('records')
    bleed_columns = [{'name': i, 'id': i, 'hideable':True} for i in bleed_df.columns]

    med_columns = [{'name': i, 'id': i, 'hideable':True} for i in med_df.columns]

    return [bleeds, bleed_columns, meds, med_columns, datafilter]


# #TODO Fix this function because it doesn't seem to work. Although it doesn't throw errors either.
# @app.callback(
#     Output('table-bleeds', 'style_data_conditional'),
#     Input('table-bleeds', 'derived_virtual_selected_rows'),
# )
# def highlight_selected_rows(selectedRows):
#     #print('Selected rows: ', selectedRows)
#     if selectedRows is None:
#         return dash.no_update
#     else:
#         return [
#             {'if': {"filter_query": f"row = {int(i)}"}, 'backgroundColor':'yellow',}
#             for i in selectedRows
#         ]
    






# @app.callback(
#     Output('table-bleeds', 'style_data_conditional'),
#     Input('table-bleeds', 'derived_virtual_selected_rows'),
# )
# def highlight_selected_rows(selectedRows):
#     #print('Selected rows: ', selectedRows)
#     if selectedRows is None:
#         return dash.no_update
#     else:
#         return [
#             {'if': {"filter_query": f"row = {int(i)}"}, 'backgroundColor':'yellow',}
#             for i in selectedRows
#         ]
    

