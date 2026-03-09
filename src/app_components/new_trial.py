import dash_bootstrap_components as dbc
from dash import Input, Output, State, html, dcc, callback_context
import pandas as pd
import dash
import re

from app import app

from src.data_import.constants import CM_COLS, CE_COLS, XB_COLS, EC_COLS

#Creates form for configuring new trials


### Form Element ###

#Input box for trial
trial_input = dbc.Row(
    [
        dbc.Label("Trial", html_for="input-form-trial", width=3),
        dbc.Col(
            dbc.Input(
                type="text", 
                id="input-form-trial", 
                placeholder="NN1234-5678",
                required=True,
                pattern="^[Nn][Nn][0-9][0-9][0-9][0-9]\-[0-9][0-9][0-9][0-9].*",
            ),
            width=6,
        ),
    ],
    className="mb-3",
)

#Input bos for trial name
trial_name_input = dbc.Row(
    [
        dbc.Label("Trial Name", html_for="input-form-trial-name", width=3),
        dbc.Col(
            dbc.Input(
                type="text", 
                id="input-form-trial-name", 
                placeholder="Trial name e.g. Explorer 8",
            ),
            width=6,
        ),
    ],
    className="mb-3",
)

#Blinding checkbox
switches = dbc.Row(
    [
        dbc.Label("Is the trial currently blinded?", html_for="input-form-blinded"),
        dbc.Col([
                dbc.RadioItems(
                id='input-form-blinded',
                options=[
                        {'label': 'Blinded', 'value':True},
                        {'label': 'Unblinded', 'value':False},
                        ], 
                value=True,
                inline=False,
                ),
                ], 
            width=4),
        html.Br(),
        dbc.FormText('This option will not unblind blinded data, it just ensures that the visualisations will be displayed correctly for blinded trials.'),
    ]
)


#Dropdown to choose bleeding episode sdtm domains
sdtm_domains = dbc.Row(
    [dbc.Col([
            dbc.Card([
                #dbc.CardHeader(dbc.Label('Bleeding episode domains', html_for='input-form-bleed-domains')),
                dbc.CardBody([
                    html.H5("Bleeding episode domains", className="card-title"),
                    html.Hr(),
                    dcc.Dropdown(
                        id="input-form-bleed-domains",
                        options=['xb and faxb', 'ce and suppce'],
                        value='xb and faxb',
                        ),
                    dbc.FormText('Most trials now have bleeding episode data in the xb and faxb domains, however some trials still have it in ce and suppce.'),
                ])
            ])
            ],
        ),
    ],
    className="mb-3",
)


#Haemostatic medication data filter rules
haem_med_sdtm_accodion = dbc.Card([
    dbc.CardBody([
    html.H5("Data Filters", className="card-title"),
    html.Hr(),
    dbc.Row([
    dbc.Col(dbc.Label('Column'), width=2),
    dbc.Col(dbc.Label('Operator'), width=2),
    dbc.Col(dbc.Label('Filter'), width=2),
    dbc.Col([
            html.Div(dbc.Button('Add Option', id='options', color='secondary', outline=True), className="d-grid gap-2"),
            dbc.Collapse(
                id='options-collapse',
                children=[
                dbc.InputGroup([
                    dbc.Input(id='input-option', type='text', value=''),
                    dbc.Button('Add', id='add-option', color='info')
                ]),
                html.Br(),
                ],
            is_open=False,
            )
        ], width=3)
    ]),
    
dbc.Row(
    [dbc.Col([
            dcc.Dropdown(
                id="input-form-hm-filter", 
                options = CM_COLS,
                value='CMCAT'
            )],
            width=2,
    ),
    dbc.Col([
            dcc.Dropdown(
                id="input-form-hm-filter-operator", 
                options = ['=', 'not contain'],
                value='='
            )],
            width=2,
    ),
    dbc.Col([
        dcc.Dropdown(
            id="input-form-hm-filter-dropdown", 
            options=['HAEMOPHILIA CONCOMITANT MEDICATION', 'GENERAL', 'HAEMOPHILIA TREATMENT AND BLEED HISTORY'],
            value=['HAEMOPHILIA CONCOMITANT MEDICATION'],
            multi=True,
        ),
        ],
        width=5,
    ),
    dbc.Col([
    html.Div(dbc.Button('Add Rule', id='add-rule', n_clicks=0, color='success'), className="d-grid gap-2"),
        ],
        width=3),
    ],
    className="mb-3",
),

 dbc.Row([
        dbc.Col([
            html.Br(),
            dbc.Label('Selected Rules'),
            html.Div(id='datatable', children=dbc.Table.from_dataframe(pd.DataFrame.from_records([]))
                              ),
            dbc.Button('Clear All', id='clear-rules', n_clicks=0, color='danger', outline=True)
            ])
        ]),    

    #store rules
    dcc.Store(id='haem-med-sdtm-rules', data=[{'filtercolumn': 'CMCAT', 'filtertype': '=', 'filter': ['HAEMOPHILIA CONCOMITANT MEDICATION']}]),

    ])])


#Bleeding episode data filter rules
bleed_sdtm_accodion = dbc.Card([
    #dbc.CardHeader(dbc.Label('Data Filters')),
    dbc.CardBody([
    html.H5("Data Filters", className="card-title"),
    html.Hr(),
    dbc.Row([
    dbc.Col(dbc.Label('Column'), width=2),
    dbc.Col(dbc.Label('Operator'), width=2),
    dbc.Col(dbc.Label('Filter'), width=2),
    dbc.Col([
            html.Div(dbc.Button('Add Option', id='options-bleed', color='secondary', outline=True), className="d-grid gap-2"),
            dbc.Collapse(
                id='options-collapse-bleed',
                children=[
                dbc.InputGroup([
                    dbc.Input(id='input-option-bleed', type='text', value=''),
                    dbc.Button('Add', id='add-option-bleed', color='info')
                ]),
                html.Br(),
                ],
            is_open=False,
            )
        ], width=3)
    ]),
    
dbc.Row(
    [dbc.Col([
            dcc.Dropdown(
                id="input-form-bleed-filter", 
                options = XB_COLS,
                value='XBTERM'
            )],
            width=2,
    ),
    dbc.Col([
            dcc.Dropdown(
                id="input-form-bleed-filter-operator", 
                options = ['=', 'not contain'],
                value='='
            )],
            width=2,
    ),
    dbc.Col([
        dcc.Dropdown(
            id="input-form-bleed-filter-dropdown", 
            options=['BLEEDING EPISODES', 'BLEEDING'],
            value=['BLEEDING EPISODES'],
            multi=True,
        ),
        ],
        width=5,
    ),
    dbc.Col([
    html.Div(dbc.Button('Add Rule', id='add-rule-bleed', n_clicks=0, color='success'), className="d-grid gap-2"),
        ],
        width=3),
    ],
    className="mb-3",
),

 dbc.Row([
        dbc.Col([
            html.Br(),
            dbc.Label('Selected Rules'),
            html.Div(id='datatable-bleed'),
            dbc.Button('Clear All', id='clear-rules-bleed', n_clicks=0, color='danger', outline=True)
            ])
        ]),    

    #store rules
    dcc.Store(id='bleed-sdtm-rules', data=[{'filtercolumn': 'XBTERM', 'filtertype': '=', 'filter': ['BLEEDING EPISODES']}]      
              ),

  ])
])

#Doses data filter rules
dose_sdtm_accodion = dbc.Card([
    dbc.CardBody([
    html.H5("Data Filters", className="card-title"),
    html.Hr(),
    dbc.Row([
    dbc.Col(dbc.Label('Column'), width=2),
    dbc.Col(dbc.Label('Operator'), width=2),
    dbc.Col(dbc.Label('Filter'), width=2),
    dbc.Col([
            html.Div(dbc.Button('Add Option', id='options-dose', color='secondary', outline=True), className="d-grid gap-2"),
            dbc.Collapse(
                id='options-collapse-dose',
                children=[
                dbc.InputGroup([
                    dbc.Input(id='input-option-dose', type='text', value=''),
                    dbc.Button('Add', id='add-option-dose', color='info')
                ]),
                html.Br(),
                ],
            is_open=False,
            )
        ], width=3)
    ]),
    
dbc.Row(
    [dbc.Col([
            dcc.Dropdown(
                id="input-form-dose-filter", 
                options = EC_COLS,
                value='ECSCAT'
            )],
            width=2,
    ),
    dbc.Col([
            dcc.Dropdown(
                id="input-form-dose-filter-operator", 
                options = ['=', 'not contain'],
                value='='
            )],
            width=2,
    ),
    dbc.Col([
        dcc.Dropdown(
            id="input-form-dose-filter-dropdown", 
            options=['EDIARY', 'FIRST DOSE', 'ACTUAL DOSE', 'PRESCRIBED DOSE', 'LAST DOSE BEFORE VISIT'],
            value=['EDIARY', 'FIRST DOSE', 'ACTUAL DOSE'],
            multi=True,
        ),
        ],
        width=5,
    ),
    dbc.Col([
    html.Div(dbc.Button('Add Rule', id='add-rule-dose', n_clicks=0, color='success'), className="d-grid gap-2"),
        ],
        width=3),
    ],
    className="mb-3",
),

 dbc.Row([
        dbc.Col([
            html.Br(),
            dbc.Label('Selected Rules'),
            html.Div(id='datatable-dose'),
            dbc.Button('Clear All Rules', id='clear-rules-dose', n_clicks=0, color='danger', outline=True)
            ])
        ]),    

    #store rules
    dcc.Store(id='dose-sdtm-rules', data=[{'filtercolumn': 'ECSCAT', 'filtertype': '=', 'filter': ['EDIARY', 'FIRST DOSE', 'ACTUAL DOSE']}]),

  ])
])


sdtm_accordion = html.Div(
    dbc.Accordion(
    [
    dbc.AccordionItem(
        [sdtm_domains,
         bleed_sdtm_accodion
            ],
        title='Bleeding episodes'
        ),
    dbc.AccordionItem(
        [haem_med_sdtm_accodion],        
        title='Haemostatic Medication'
        ),
    dbc.AccordionItem(
        [dose_sdtm_accodion],
        title='Trial Drug Doses'
        ),
    ],flush=True,
    start_collapsed=True,
    )
)





### Form ###

form = html.Div([
    dbc.FormText('This form can be used to setup new trials or alter the configuration of existing trials. '),
     dbc.FormText('It is possible to submit a new trial by just inputting the trial ID, however it is recommended to go through the configuration below to specify trial blinding, sdtm domains and whether any filters must be applied.'),
     dbc.FormText(' The default values are populated within the form for your convenience.'),
    html.Br(),
    html.Br(),
    html.Br(),
    trial_input,
    trial_name_input,
    dbc.Accordion(
    [
            dbc.AccordionItem(
                [switches],
                title='Blinding',
                ),
             dbc.AccordionItem(
                [sdtm_accordion],
                title='Configure SDTM Domains',
                ),
            
    ], flush=True,
    start_collapsed=True,
    always_open=False,
    )
])


### Pop-up window ###

modal = html.Div(
    [
        # dbc.Button("Add New Trial", id="add-new-trial-open", className="me-1", n_clicks=0),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle("Setup Trial")),
                            dbc.ModalBody(form),
                dbc.ModalFooter(
                    dbc.Button(
                        "Submit", id="add-new-trial-submit", n_clicks=0, #disabled=True,
                    )
                ),
            ],
            id="modal",
            size='xl',
            scrollable=True,
            is_open=False,
        ),
    ]
)


##### Callbacks #####


## Trial input

# Validation for new trial input: 
# checks to see whether trial ID has correct format of nn1234-5678
@app.callback(
    [Output('input-form-trial', 'valid'),
    Output('input-form-trial', 'invalid')],
    [Input("input-form-trial", "value")],
    [State('input-form-trial', 'pattern')])
def write_text(value, pattern):
    patt = re.compile(pattern)

    if not value:
        return dash.no_update, dash.no_update

    #Check if trial has correct format
    if bool(patt.match(value)) is True:
        return True, False
    else:
        return False, True
    
## Configure SDTM domains
    
    
# Updates options for data filters based on SDTM bleed domains selected
@app.callback(
    [Output("input-form-bleed-filter", 'options'),
     Output("input-form-bleed-filter", 'value'),
    Output('input-form-bleed-filter-dropdown', 'value')],
    Input('input-form-bleed-domains', 'value'),
        )
def change_options_based_on_sdtm_bleed_domains(bleed_domains):
    if bleed_domains == 'xb and faxb':
        columns = XB_COLS
        default_column = 'XBTERM'
        default_filter = 'BLEEDING EPISODES'
    elif bleed_domains == 'ce and suppce':
        columns = CE_COLS
        default_column = 'CECAT'
        default_filter = 'BLEEDING'
    return [columns, default_column, default_filter]



# SDTM domain filters

# Each filter dropdown is flexible so users can add more options to filter the data
# Callbacks to open the options collapse are below:

#Callback to open new_trial bleed options collapse
@app.callback(
    Output("options-collapse-bleed", "is_open"),
    [Input("options-bleed", "n_clicks")],
    [State("options-collapse-bleed", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


#Callback to open new_trial haem med options collapse
@app.callback(
    Output("options-collapse", "is_open"),
    [Input("options", "n_clicks")],
    [State("options-collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

#Callback to open new_trial bleed options collapse
@app.callback(
    Output("options-collapse-dose", "is_open"),
    [Input("options-dose", "n_clicks")],
    [State("options-collapse-dose", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

#Adds the option to the filter dropdown for haem med
@app.callback(
    Output('input-form-hm-filter-dropdown', 'options'),
    [Input('add-option', 'n_clicks')],
    [State('input-option', 'value'),
     State('input-form-hm-filter-dropdown', 'options')],
)
def callback(n_clicks, new_value, current_options):
    if not n_clicks:
        return current_options
    if new_value != '':
        current_options.append(new_value)
    return current_options

#Adds the option to the filter dropdown for bleeds
@app.callback(
    Output('input-form-bleed-filter-dropdown', 'options'),
    [Input('add-option-bleed', 'n_clicks')],
    [State('input-option-bleed', 'value'),
     State('input-form-bleed-filter-dropdown', 'options')],
)
def callback(n_clicks, new_value, current_options):

    if not n_clicks:
        return current_options
    if new_value != '':
        current_options.append(new_value)
    return current_options

#Adds the option to the filter dropdown for dose
@app.callback(
    Output('input-form-dose-filter-dropdown', 'options'),
    [Input('add-option-dose', 'n_clicks')],
    [State('input-option-dose', 'value'),
     State('input-form-dose-filter-dropdown', 'options')],
)
def callback(n_clicks, new_value, current_options):

    if not n_clicks:
        return current_options
    if new_value != '':
        current_options.append(new_value)
    return current_options

#Callback to add rules to haemostatic medication data import
@app.callback(
        [Output('haem-med-sdtm-rules', 'data'),
         Output('datatable', 'children')],
        [Input('add-rule', 'n_clicks'),
        Input('clear-rules', 'n_clicks')],
        [State("input-form-hm-filter", 'value'),
         State('input-form-hm-filter-operator', 'value'),
         State('input-form-hm-filter-dropdown', 'value'),
         State('haem-med-sdtm-rules', 'data')]
)
def add_new_rule(add_rule, clear_rules, column, operator, values, rules):

    button_clicked = callback_context.triggered[0]['prop_id'].split('.')[0]

    if button_clicked == 'add-rule':
        new_rule = {'filtercolumn': column, 'filtertype': operator, 'filter': values}
        if new_rule not in rules:
            rules.append(new_rule)
    elif button_clicked == 'clear-rules':
        rules = []

    print(rules)   
    #create dataframe to display to user
    df = pd.DataFrame.from_records(rules)
    table = dbc.Table.from_dataframe(df)

    return [rules, table]


#Callback to add rules to bleed data import
@app.callback(
        [Output('bleed-sdtm-rules', 'data'),
         Output('datatable-bleed', 'children')],
        [Input('add-rule-bleed', 'n_clicks'),
        Input('clear-rules-bleed', 'n_clicks'),
        Input('input-form-bleed-domains', 'value')],
        [State("input-form-bleed-filter", 'value'),
         State('input-form-bleed-filter-operator', 'value'),
         State('input-form-bleed-filter-dropdown', 'value'),
         State('bleed-sdtm-rules', 'data')]
)
def add_new_rule(add_rule, clear_rules, sdtm_domains, column, operator, values, rules):

    button_clicked = callback_context.triggered[0]['prop_id'].split('.')[0]

    if button_clicked == 'input-form-bleed-domains':
        if sdtm_domains == 'xb and faxb':
            rules = [{'filtercolumn': 'XBTERM', 'filtertype': '=', 'filter': ['BLEEDING EPISODES']}]
        elif sdtm_domains == 'ce and suppce':
            rules = [{'filtercolumn': 'CECAT', 'filtertype': '=', 'filter': ['BLEEDING']}]
    elif button_clicked == 'add-rule-bleed':
        new_rule = {'filtercolumn': column, 'filtertype': operator, 'filter': values}
        if new_rule not in rules:
            rules.append(new_rule)
    elif button_clicked == 'clear-rules-bleed':
        rules = []
    
    #create dataframe to display to user
    df = pd.DataFrame.from_records(rules)
    table = dbc.Table.from_dataframe(df)

    return [rules, table]



#Callback to add rules to dose data import
@app.callback(
        [Output('dose-sdtm-rules', 'data'),
         Output('datatable-dose', 'children')],
        [Input('add-rule-dose', 'n_clicks'),
        Input('clear-rules-dose', 'n_clicks')],
        [State("input-form-dose-filter", 'value'),
         State('input-form-dose-filter-operator', 'value'),
         State('input-form-dose-filter-dropdown', 'value'),
         State('dose-sdtm-rules', 'data')]
)
def add_new_rule(add_rule, clear_rules, column, operator, values, rules):

    button_clicked = callback_context.triggered[0]['prop_id'].split('.')[0]


    if button_clicked == 'add-rule-dose':
        new_rule = {'filtercolumn': column, 'filtertype': operator, 'filter': values}
        if new_rule not in rules:
            rules.append(new_rule)
    if button_clicked == 'clear-rules-dose':
        rules = []

    print(rules)
    
    #create dataframe to display to user
    df = pd.DataFrame.from_records(rules)
    table = dbc.Table.from_dataframe(df)

    return [rules, table]
