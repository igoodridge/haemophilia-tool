### Import Packages ###
import dash
from dash import dcc, html, callback, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np

from app import app
from src.app_components.styling_constants import SIDEBAR_STYLE




#Radiobuttons for filtering data based on data checks. 
#TODO add to callback so only show on page_1 and update for page_2
radio_filters_bleeds = html.Div([
        html.P('Data Checks', className="fs-5"),
        dbc.RadioItems(
        id='radio-filters-bleeds',
        options=[
                {'label': 'None', 'value':'None', 'label_id':'radio-bleed-all'},
                {'label':'Missing Values', 'value':'MISSING', 'label_id':'radio-bleed-missing'},
                {'label':'Duplicate Records', 'value':'DUPLICATED', 'label_id':'radio-bleed-duplicated'},
                {'label':'Bleed Location Issues', 'value':'LOCATION_ISSUE', 'label_id':'radio-bleed-location-issue'},
                {'label': 'Bleed Length', 'value': 'LONG_BLEED', 'label_id':'radio-bleed-long-bleed'},
                {'label': 'TRT=N but meds given', 'value':'TRT_N_BUT_MEDS', 'label_id':'radio-bleed-trtN-meds'},
                {'label':'TRT=Y but no meds given', 'value':'TRT_Y_NO_MEDS', 'label_id':'radio-bleed-trtY-no-meds'},
                {'label': 'Meds outside bleeding episodes', 'value':'OUTSIDE_BLEEDS', 'label_id':'radio-meds-outside-bleeds'},
                ], 
        value='None',
        inline=False,
        ),
        ])




#Tooltips for radiofilters

radio_bleed_tooltips = html.Div(
    children=[
    dbc.Tooltip(
            'All data with no filters.',
            target='radio-bleed-all',
            placement='right',
            ),
        dbc.Tooltip(
            'Bleeds: where one or more of BLEED_START_DATE, BLEED_STOP_DATE or BLEED_LOCATION are null. \nMeds: where one of more of HAEM_MED_DATE_TIME, HAEM_MED_DOSE are null.',
            target='radio-bleed-missing',
            placement='right',
            trigger='hover',
            ),
        dbc.Tooltip(
            "Bleeds: where all of BLEED_START_DATE, BLEED_STOP_DATE, BLEED_LOCATION, LATERAL_POSITION are the same. \nMeds given on the same date.",
            target='radio-bleed-duplicated',
            placement='right',
            ),
        dbc.Tooltip(
            "Bleeds where BLEED_LOCATION does not match up with JOINT_LOCATION or BODY_PART e.g. BLEED_LOCATION = JOINT but JOINT_LOCATION is not a joint.",
            target='radio-bleed-location-issue',
            placement='right',
            ),
        dbc.Tooltip(
            "Default: Bleeds longer than 7 days.",
            target='radio-bleed-long-bleed',
            placement='right',
            ),
        dbc.Tooltip(
            "Data points where the bleed is marked as not treated, but where medication is given within the timeframe of a bleed.",
            target='radio-bleed-trtN-meds',
            placement='right',
            ),
        dbc.Tooltip(
            "Bleeds marked as treated, with no medication given within the timeframe of the bleed.",
            target='radio-bleed-trtY-no-meds',
            placement='right',
            ),
        dbc.Tooltip(
            "Medication given outside any bleeding episode.",
            target='radio-meds-outside-bleeds',
            placement='right',
            ),



])



radio_filters_dose= html.Div([
        html.P('Data Checks', className="fs-5"),
        dbc.RadioItems(
        id='radio-filters-dose',
        options=[
                {'label': 'None', 'value':'None', 'label_id':'radio-dose-all'},
               {'label':'Missing Values', 'value':'MISSING', 'label_id':'radio-dose-missing'},
                {'label':'Duplicate Doses', 'value':'DUPLICATED', 'label_id':'radio-dose-duplicate'},
                {'label': 'Gap in Doses', 'value': 'MISSED_DOSES', 'label_id': 'radio-dose-missed-doses'}
                ], 
        value='None',
        inline=False,
        ),
        ])



#Tooltips for radiofilters dose

radio_dose_tooltips = html.Div(
    children=[
    dbc.Tooltip(
            'All data with no filters.',
            target='radio-dose-all',
            placement='right',
            ),
        dbc.Tooltip(
            'Doses where one or more of STOP_DATE_TIME or DOSE are missing.',
            target='radio-dose-missing',
            placement='right',
        ),
        dbc.Tooltip(
            'Doses taken on the same day i.e. where both STOP_DATE_TIME and STUDY_DAY_END are the same between multiple records.',
            target='radio-dose-duplicate',
            placement='right',
        ),
        dbc.Tooltip(
            'Doses where the gap to the previous dose is more than the number of days specified in the slider. Default is 7 days.',
            target='radio-dose-missed-doses',
            placement='right',
        )
    ])




#Reset button
reset_button = dbc.Button("Reset Selections", color="primary", n_clicks=0)


#Input for date cutoffs
date_cutoffs = html.Div(children=[
                            html.Br(),
                            html.Hr(),
                            html.P('Date Cutoff', className="fs-5"),
                            dcc.DatePickerSingle(
                                id='date-picker-min',
                                placeholder='Start Date',
                                display_format='DD/MM/YY',
                                persistence=True,
                                persistence_type='local',
                                clearable=True,
                                style={"margin-left": "7px", 'margin-top':'7px', 'margin-bottom':'7px', 'margin-right':'7px'}
                            ),
                            dcc.DatePickerSingle(
                                id='date-picker-max',
                                placeholder='End Date',
                                display_format='DD/MM/YY',
                                persistence=True,
                                persistence_type='local',
                                clearable=True,
                                style={"margin-left": "7px", 'margin-top':'7px', 'margin-bottom':'7px', 'margin-right':'7px'}
                                ),
                            html.Hr(),
                            html.Br(),    
])







# Side Bar layout
layout = html.Div(
        [
        html.P("Navigation", className="fs-5"),
        html.Hr(),
        dbc.Nav(
            [
                dbc.NavLink("Home", href="/", active="exact"),
                dbc.NavLink("Bleeds and medication", href="/page-1", active="exact"),
                dbc.NavLink("Doses", href="/page-2", active="exact"),
            ],
            vertical=True,
            pills=True,
        ),
    
        html.Br(),
        html.Hr(),
        html.P('Trial', className="fs-5"),
        dcc.Dropdown(id='trial-dropdown',
                    options=[
                    {'label': 'Dummy Data', 'value':'nn1234-5678'},
                    {'label': 'Explorer 7', 'value':'nn7415-4311'},
                    {'label':'Explorer 8', 'value':'nn7415-4307'},
                    {'label':'Explorer 10', 'value':'nn7415-4616'},
                    {'label': 'Frontier 1 (MAD)', 'value':'nn7769-4513mad'},
                    {'label': 'Frontier 2', 'value': 'nn7769-4514'},
                    {'label': 'Frontier 3', 'value': 'nn7769-4516'},
                    # {'label': 'Paradigm 9', 'value': 'nn7999-4670'},
                    # {'label': 'Pathfinder 9', 'value': 'nn7088-4029'},
                    # {'label': 'Pathfinder 10', 'value': 'nn7088-4595'},
                    ],
                    value='nn1234-5678',
                    persistence=True,
                    persistence_type='local'),
        html.Br(),
        #Attempting to connect to P drive
        html.Div([dbc.Alert(id='data-connect-attempt',
                           children='Connecting to P drive...',
                           duration=4000,
                           color='primary',
                           is_open=False,
                           ),
                           ]),
        #Data Access Alert
        html.Div([dbc.Spinner(dbc.Alert(id='access-alert',
                           duration=6000,
                           is_open=False,
                           )),
                ]),
        html.Br(),
        html.Hr(),
        html.Div(id='data-filters'),
        html.Div(id='tooltips'),
        html.Br(),
        html.Div(id='reset-button', className="d-grid gap-2"),
        html.Br(),
        html.Div(id='filter-options'),
        html.Div(id='date-cutoffs')          
    ],
    style=SIDEBAR_STYLE,
    )


# Callback changes content of sidebar depending on page e.g. new trial only on home page, 
# bleed radio buttons only on bleeds page
@app.callback([Output("data-filters", "children"), 
               Output('reset-button', 'children'),
               Output('tooltips', 'children'),
               Output('date-cutoffs', 'children'),
               ], 
               [Input("url", "pathname")])
def render_page_content(pathname):
    if pathname == "/":
        return [[],  [], [], []]
    elif pathname == "/page-1":
        return [radio_filters_bleeds, reset_button, radio_bleed_tooltips, date_cutoffs]
    elif pathname == "/page-2":
        return [radio_filters_dose, reset_button, radio_dose_tooltips, date_cutoffs]
    return [[], [], [], []]

