### Import Packages ###
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import os
from flask import request
from sshfs import SSHFileSystem
import json
import platform


# Import Dash Instance
from app import app

#Import pages and functions
from pages import home, page_1, page_2
from src.app_components import navigation, styling_constants, sidebar

# Custom Packages
from src.data_import.trial import Trial
from src.app_components.new_trial import modal
from src.app_components.user_guide import offcanvas
from src.app_components.configure_data_checks import offcanvas_data_checks


# Load in styles
CONTENT_STYLE = styling_constants.CONTENT_STYLE
SIDEBAR_STYLE = styling_constants.SIDEBAR_STYLE



###############################################################
######################### APP LAYOUT ##########################
###############################################################


app.layout = dbc.Container([
        dbc.Row([
            dbc.Col(navigation.navbar,
                    width=12)
            ]),
        dbc.Row([
            dbc.Col(sidebar.layout, 
                    width=2, sm=2),
            dbc.Col([
                    html.Div(id="page-content", 
                    style=CONTENT_STYLE),
                    html.Div(id='dummy-div'),
                    html.Div(id='dummy-div-dose', style={'display':'none'}),
                    html.Div(id='add-trial-div', children=modal),
                    html.Div(id='user-guide', children=offcanvas),
                    html.Div(id='data-checks-config', children=offcanvas_data_checks),
                    ],
                    width=10, sm=10)
            ]),
        dcc.Location(id="url"),

        html.Div(id='form-output'), #Dummy div for new trial form

        #Store data for particular trial
        dcc.Store(id='store-bleed-med-data', data=[], storage_type='session'),
        dcc.Store(id='store-subject-data', data=[], storage_type='session'),
        dcc.Store(id='user', data=[], storage_type='session'),
        dcc.Store(id='store-overview-data', data=[], storage_type='session'),
        ],
        fluid=True,
        style={'height':'100vh'})


#Callback renders page content 
@app.callback(Output("page-content", "children"), 
              Input("url", "pathname"))
def render_page_content(pathname):
    if pathname == "/":
        return home.layout
    elif pathname == "/page-1":
        return page_1.layout
    elif pathname == "/page-2":
        return page_2.layout
    return home.layout


###############################################################
####################### APP COMPONENTS ########################
###############################################################

###################### User Information #######################

#opens user information when button clicked
@app.callback(
    Output("offcanvas", "is_open"),
    Input("open-offcanvas", "n_clicks"),
    [State("offcanvas", "is_open")],
)
def toggle_offcanvas(n1, is_open):
    if n1:
        return not is_open
    return is_open


#################### Configure Data Checks #####################

#open data check configuration pane when button clicked
@app.callback(
    Output("offcanvas-data-checks", "is_open"),
    Input('configure-checks-button', "n_clicks"),
    [State("offcanvas-data-checks", "is_open")],
)
def toggle_offcanvas(n1, is_open):
    if n1:
        return not is_open
    return is_open


######################### Setup Trial ###########################

# Opens modal when Trial Setup button is clicked
@app.callback(
    Output("modal", "is_open"),
    [Input("add-new-trial-open", "n_clicks"),
     Input('add-new-trial-submit', 'n_clicks')],
    [State("modal", "is_open")],
)
def toggle_modal(n1, is_open, n_submit):
    if n1 or n_submit:
        return not is_open
    return is_open

# Returns user credentials when run on the server
def get_credentials(req):
    """
    Returns a dict containing "user" and "groups" information populated by
    the incoming request header "RStudio-Connect-Credentials".
    """
    credential_header = req.headers.get("RStudio-Connect-Credentials")
    if not credential_header:
        return {}
    return json.loads(credential_header)


# Saves the trial config dict to trials.json on P drive
@app.callback(
    Output('form-output', 'children'),
    [Input('add-new-trial-submit', "n_clicks")],
    [State('input-form-trial', 'valid'),
    State('input-form-trial', 'value'),
     State('input-form-trial-name', 'value'),
     State('input-form-blinded', 'value'),
     State('input-form-bleed-domains', 'value'),
     State('bleed-sdtm-rules', 'data'),
    State('haem-med-sdtm-rules', 'data'),
     State('dose-sdtm-rules', 'data'),
     ]
)
def submit_new_trial(n_clicks_submit, valid, 
                     trial, trialname, blinded, bleed_domains, 
                     bleed_rules, meds_rules, dose_rules,
                     ):
    if trial is not None and valid is True:
        trial = trial.strip().lower()

        if trialname is None:
            trialname = trial


        bleed_domains = bleed_domains.split(' and ')
        main_bleed_domain = bleed_domains[0]

            


        trial_config ={'trialname': trialname, 
                    'blinded': blinded,
                    'data': {'bleeds': {'domains': bleed_domains, 'mergekey': ['STUDYID', 'USUBJID', 'BLEED_ID']},
                                'meds': {'domains': ['cm'], 'mergekey':None},
                                'dose': {'domains':['ec'], 'mergekey':None},
                                'med_hist': {'domains':['mh'], 'mergekey':None},
                                },
                    'rules': {main_bleed_domain: bleed_rules,
                              'cm': meds_rules,
                              'ec': dose_rules
                              },
                    }
        trial_dict = {trial: trial_config}
                    
        print('New trial config: ', trial_dict)                  

        #If running on server, mount whale drive. If not on server, fs=None
        if os.environ.get('Server') is not None:
            print('Running on server')
            user_metadata = get_credentials(request)
            user = user_metadata.get("user")
            #File system, used for reading P drive data on RSConnect Server
            fs = SSHFileSystem(
                'whale.novo.dk',
                client_keys=[f'/homedirs/{user}/.ssh/id_rsa'])
            path = f'/projstat/general/toolpool/haemophiliatool/'
            if not fs.isdir(path):
                fs.makedir(path)
            with fs.open(f'{path}trials.json') as stream:
                current_trials = json.load(stream)
            if trial not in current_trials:
                current_trials.update(trial_dict)
            else:
                print('Trial alread in config file.')
                current_trials[trial] = trial_config
                print('Trial updated with new configurations.')
            trials = json.dumps(current_trials, indent=4)
            with fs.open(f'{path}trials.json', 'wb') as stream:
                stream.write(trials)
        else:
            #Checking access when run locally
            if platform.system() == 'Linux':
                path = f'/mnt/projstat/general/toolpool/haemophiliatool/'
            elif platform.system() == 'Windows':
                path = f'P:\\general\\toolpool\\haemophiliatool\\'
            if not os.path.exists(path):
                os.makedirs(path)

            #Creates json file with list of trials and trial names 
            with open(f'{path}trials.json', 'r') as fi:
                current_trials = json.load(fi)
            if trial not in current_trials:
                current_trials.update(trial_dict)
            else:
                print('Trial alread in config file.')
                current_trials[trial] = trial_config
                print('Trial updated with new configurations.')
            trials = json.dumps(current_trials, indent=4)
            with open(f'{path}trials.json', 'w') as fo:
                fo.write(trials)
            print('Written new trial to trials.json')

    return ""


#Callback should only be triggered on loading of app as this input has no children, or when new trial submitted in new trial form
#Updates trial dropdown to show all trials in trials.json
@app.callback(
        Output('trial-dropdown', 'options'),
        [Input('dummy-div', 'children'),
         Input('add-new-trial-submit', "n_clicks")]
)
def update_trial_dropdown(children, n_clicks_submit):

    #Load trials.json from P drive (depending on whether running on server or locally)
    #server
    if os.environ.get('Server') is not None:
        user_metadata = get_credentials(request)
        user = user_metadata.get("user")
        fs = SSHFileSystem(
            'whale.novo.dk',
            client_keys=[f'/homedirs/{user}/.ssh/id_rsa'])
        path = f'/projstat/general/toolpool/haemophiliatool/trials.json'
        with fs.open(path) as stream:
            trial_dict = json.load(stream)
    #local
    else:
        if platform.system() == 'Linux':
            path = f'/mnt/projstat/general/toolpool/haemophiliatool/trials.json'
        elif platform.system() == 'Windows':
            path = f'P:\\general\\toolpool\\haemophiliatool\\trials.json'
        with open(path, 'r') as f:
            trial_dict = json.load(f)

    #options (just include dummy data)
    options = [{'label': 'Dummy Data', 'value': 'nn1234-5678'}]

    for trial in trial_dict:
        trialname = trial_dict[trial]['trialname']
        dropdown = {'label': trialname, 'value': trial}
        options.append(dropdown)
    print('Trials in app: ', options)
    return options

@app.callback(
        Output('data-connect-attempt', 'is_open'),
        Input('trial-dropdown', 'value'),
)
def show_data_connection_attempt(trial):
        if trial != 'nn1234-5678':
            return True



###############################################################
######################### DATA IMPORT #########################
###############################################################

#Imports and stores all relevant data for selected trial
@app.callback(
    [Output('user', 'data'),
    Output('store-bleed-med-data', 'data'),
    Output('store-subject-data', 'data'),
     Output('store-overview-data', 'data'),
     Output('access-alert', 'children'),
     Output('access-alert', 'color'),
     Output('access-alert', 'is_open'),
     ],
    [Input('trial-dropdown', 'value'),
     Input('bleed-missing-config', 'value'),
    Input('bleed-duplicate-config', 'value'),
    Input('med-missing-config', 'value'),
    Input('med-duplicate-config', 'value'),
    Input('dose-missing-config', 'value'),
    Input('dose-duplicate-config', 'value'),
    Input('dose-length-slider', 'value')
     ]
)
def store_trial_data(selected_trial, bleed_missing_cols, bleed_duplicate_cols, med_missing_cols, med_duplicate_cols, dose_missing_cols, dose_duplicate_cols, days_missed_dose): 

    print('New trial selected: ', selected_trial)

    print('Getting user credentials...')

    user_metadata = get_credentials(request)
    user = user_metadata.get("user")

    print('Getting trial data...')


    trial = Trial(selected_trial, user)

    #Check is user has data access
    access = trial.access

    print('Access: ', access)

    #Alert to display if the user has data access
    if access:
        access_message = 'Access Granted!'
        access_color = 'success'
        timeout=4000
    else:
        project = selected_trial.split('-')[0]
        access_message = [html.H5('Access Denied!'),
                           html.P(f'Please apply for UNIX SCE : {project}\\{selected_trial} Read - Data Access to access this trial data.', className='mb-0')]
        access_color = 'danger'
        timeout=10000

    #If dummy data, everyone has access so do not display alert (change message/color to avoid brief display during loading)
    if selected_trial != 'nn1234-5678':
        access_alert = True
    else:
        access_alert = False
        access_message = ''
        access_color='information'

    #Input from configure data checks allows user to specify which values to search for
    bleeds, meds, subject_num_fake = trial.get_bleed_med_data(
        bleed_missing_cols, 
        bleed_duplicate_cols, 
        med_missing_cols, 
        med_duplicate_cols
        )

    dose = trial.get_dose(dose_missing_cols, dose_duplicate_cols, days_missed_dose)


    print('Getting subject data...')
    
    subject_num = trial.subject_num
    subjid_dict = trial.subjid_dict


    blinded = trial.blinded
   
    columns = ['MISSING', 'DUPLICATED', 'LOCATION_ISSUE', 'LONG_BLEED', 'TRT_N_BUT_MEDS', 'TRT_Y_NO_MEDS']


    #save bleed and subject data

    print('Assigning bleed and subject data to dict.')

    bleed_data = {'bleeds':bleeds.to_dict('records'),
                'meds': trial.meds.to_dict('records'),
                'blinded':blinded}

    subject_data = {'blinded': blinded,
                    'subject_num':subject_num,
                    'subject_num_fake':subject_num_fake,
                    'subjid_dict': subjid_dict}
    

    print('Getting overview data.')

    #Count the number of errors in that column. The if else statement avoids a KeyError if no issue in that column. 
    bleed_error_columns = ['MISSING', 'DUPLICATED', 'LOCATION_ISSUE', 'LONG_BLEED', 'TRT_N_BUT_MEDS', 'TRT_Y_NO_MEDS']
    meds_error_columns = ['MISSING', 'DUPLICATED', 'TRT_N_BUT_MEDS', 'OUTSIDE_BLEEDS']
    dose_error_columns = ['MISSING', 'DUPLICATED']

    bleed_overview_data = trial.get_error_overview(bleeds, bleed_error_columns)
    med_overview_data = trial.get_error_overview(df=meds, columns=meds_error_columns)
    dose_overview_data = trial.get_error_overview(dose, dose_error_columns)

    
    overview_data = {
        'bleeds': bleed_overview_data, 
        'meds': med_overview_data,
        'dose': dose_overview_data
        }

    print('Overview data complete.')
    print('Storing data in dcc.Store.')

    return [user, bleed_data,  subject_data, overview_data, access_message, access_color, access_alert]


