import dash_bootstrap_components as dbc
from dash import Input, Output, State, html


offcanvas = html.Div(
    [

        dbc.Offcanvas([
                html.H5('General'),
                html.H6('This application enables users to view and visualise bleed, haemostatic medication and trial drug dose data from haemophilia trials.'),
                html.H6('For each data set, error checks are performed on the data. Checks can be performed as per default, or configured to the user\'s needs (see below).'),
                html.H6('Click on individual subjects within the graphs to display subject specific data in the tables; press reset to view all subjects again.'),
                html.Br(),
                html.H5('Adding New Trials'),
                html.H6('To add a new trial, click the Setup Trial button and complete the form. Default values are populated within the form.'),
                html.H6('Please ensure the information you provide is correct as the app will not be able to load your data with the wrong information here.'),
                html.H6('You may need to reload the app to be able to see the new trial appear in the dropdown.'),
                html.Br(),
                html.H5('Configuring Current Trials'),
                html.H6('To change the configuration of a trial e.g. blinding status, data filters to include/exclude certain records from SDTM etc. \
                        can also be done via the Trial Setup form in the same way as new trials.'),
                html.Br(),
                html.H5('Configuring Data Checks'),
                html.H6('Several of the data checks can be dynamically configured e.g. to change the maximum allowed length of a bleed or \
                        to alter the definition of a duplicate. To do this, click on the Configure Data Checks button. Please note that these changes will not be permanent.' ),
                html.Br(),
                html.H5('Disclaimer'),
                html.H6('This app is still under development and has not yet been validated. Please use with caution.'),
                html.Br(),
                html.H5('Help'),
                html.H6('For assistance, please contact MUQ.'),

        ]
            ,
            id="offcanvas",
            placement='end',
            title="User Information",
            is_open=False,
        ),
    ]
)


