### Import packages ###
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, callback
from src.app_components import styling_constants

from app import app

### Create navigation bar as header ###

#TODO Work out why navbar 'brand' is not showing up as text in app

navbar = dbc.NavbarSimple(
    children=[
        dbc.Button('Configure Data Checks', id='configure-checks-button', n_clicks=0),
        dbc.Button("Setup Trial", id="add-new-trial-open", className="me-1", n_clicks=0),
        dbc.Button("User Information", id="open-offcanvas", n_clicks=0),
    ],
    brand="HaemophiliaTool - Unvalidated",
    brand_href="/",
    color="primary",
    dark=True,
    fluid=True,
    fixed='top',
)

