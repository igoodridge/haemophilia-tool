### Import Packages ###
import dash
from dash import dcc, html, callback, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np

from app import app
from src.app_components.styling_constants import SIDEBAR_STYLE







#Configure missing data for bleeds check
bleed_data_missing_config = dbc.Row(
    dbc.Col([
    dbc.Label('Check for missing: '),
    dcc.Dropdown(
    id='bleed-missing-config',
        options=['BLEED_START_DATE', 'BLEED_STOP_DATE', 'BLEED_LOCATION', 'LATERAL_POSITION', 
         'BODY_PART', 'JOINT_LOCATION', 'BLEED_SEVERITY', 'BLEED_CAUSE', 'TREATYN'],
        multi=True, 
        searchable=True,
        value=['BLEED_START_DATE', 'BLEED_STOP_DATE', 'BLEED_LOCATION', 'BLEED_SEVERITY'],
        persistence=True, 
        persistence_type='session',
    )
    ])
)

#Configure duplicates data for meds check
bleed_data_duplicates_config = dbc.Row(
    dbc.Col([
    dbc.Label('Check for duplicate bleeds with these values in common: '),
    dcc.Dropdown(
        id='bleed-duplicate-config',
        options=['USUBJID', 'BLEED_START_DATE', 'BLEED_STOP_DATE', 'BLEED_LOCATION', 'LATERAL_POSITION', 
         'BODY_PART', 'JOINT_LOCATION', 'BLEED_SEVERITY', 'BLEED_CAUSE', 'TREATYN'],
        multi=True, 
        searchable=True,
        value=['USUBJID', 'BLEED_START_DATE', 'BLEED_LOCATION', 'BODY_PART', 'JOINT_LOCATION', 'LATERAL_POSITION'],
        persistence=True, 
        persistence_type='session'
    )
    ])
)

bleed_length_slider = html.Div([
                html.Br(),
                dbc.Label('Maximum allowed bleed length (days): ', html_for='bleed-length-slider'),
                dcc.Slider(id='bleed-length-slider', min=1, max=10, step=1, value=7),
        ])



#Configure missing data for meds check
med_data_missing_config = dbc.Row(
    dbc.Col([
    dbc.Label('Check for missing: '),
    dcc.Dropdown(
        id='med-missing-config',
        options=['HAEM_MED_DRUG', 'HAEM_MED_DATE', 'HAEM_MED_DOSE', 'UNITS', 'HAEM_MED_TRT_TYPE'],
        multi=True, 
        searchable=True,
        value=['HAEM_MED_DATE', 'HAEM_MED_DOSE'],
        persistence=True, 
        persistence_type='session'
    )
    ])
)

#Configure duplicates data for dose check
med_data_duplicates_config = dbc.Row(
    dbc.Col([
    dbc.Label('Check for duplicates with these values in common: '),
    dcc.Dropdown(
        id='med-duplicate-config',
        options=['USUBJID', 'HAEM_MED_DRUG', 'HAEM_MED_DATE', 'HAEM_MED_DOSE', 'UNITS', 'HAEM_MED_TRT_TYPE'],
        multi=True, 
        searchable=True,
        value=['USUBJID', 'HAEM_MED_DATE'],
        persistence=True, 
        persistence_type='session'
    )
    ])
)







#Configure missing data for bleeds check
dose_data_missing_config = dbc.Row(
    dbc.Col([
    dbc.Label('Check for missing: '),
    dcc.Dropdown(
    id='dose-missing-config',
        options=['ECSCAT', 'DOSE', 'START_DATE_TIME', 'STOP_DATE_TIME', 'STUDY_DAY_START', 'STUDY_DAY_END'],
        multi=True, 
        searchable=True,
        value=['STOP_DATE_TIME', 'DOSE'],
        persistence=True, 
        persistence_type='session',
    )
    ])
)

#Configure duplicates data for meds check
dose_data_duplicates_config = dbc.Row(
    dbc.Col([
    dbc.Label('Check for duplicate doses with these values in common: '),
    dcc.Dropdown(
        id='dose-duplicate-config',
        options=['USUBJID', 'ECSCAT', 'DOSE', 'START_DATE_TIME', 'STOP_DATE_TIME', 'STUDY_DAY_START', 'STUDY_DAY_END'],
        multi=True, 
        searchable=True,
        value=['USUBJID', 'STOP_DATE_TIME', 'STUDY_DAY_END'],
        persistence=True, 
        persistence_type='session'
    )
    ])
)

gap_in_doses = html.Div([
                html.Br(),
                dbc.Label('Max. allowed no. days between doses: ', html_for='dose-length-slider'),
                dbc.InputGroup([
    dbc.Input(id='dose-length-slider', type='number', min=1, max=100, step=1, value=7, persistence=True, persistence_type='local'),
    dbc.InputGroupText('days'),
                ])      
        ])




data_check_configurations = dbc.Accordion([

                dbc.AccordionItem(
                            dbc.Accordion([
                                
                                dbc.AccordionItem(bleed_data_missing_config,
                                                  title='Missing Values'),


                                dbc.AccordionItem(bleed_data_duplicates_config, 
                                                  title='Duplicate Bleeds'),


                                dbc.AccordionItem(bleed_length_slider,
                                                title='Bleed Length')

                            ],
                            flush=True,
    start_collapsed=False,
    always_open=True),
                            title='Bleeding Episodes'
                            ),

dbc.AccordionItem(
                            dbc.Accordion([
                                

                                dbc.AccordionItem(med_data_missing_config,
                                                  title='Missing Values'),

                                dbc.AccordionItem(med_data_duplicates_config, 
                                                  title='Duplicate Haem Med Doses'),

                            ],
                            flush=True,
    start_collapsed=False,),
                            title='Haemostatic Medication'
                            ),




                dbc.AccordionItem(
                            dbc.Accordion([
                                
                                dbc.AccordionItem(dose_data_missing_config,
                                                  title='Missing Values'),


                                dbc.AccordionItem(dose_data_duplicates_config, 
                                                  title='Duplicate Doses'),

                                dbc.AccordionItem(gap_in_doses,
                                                title='Gap in Doses')

                            ],
                            flush=True,
    start_collapsed=False,),
                            title='Trial Drug Doses'
                            ),


],
    start_collapsed=True,    
    always_open=True,)



offcanvas_data_checks = html.Div(
    [

        dbc.Offcanvas([
            data_check_configurations

        ]
            ,
            id="offcanvas-data-checks",
            placement='end',
            title="Configure Data Checks",
            is_open=False,
            backdrop=False,
        ),
    ]
)
