### Import Packages ###
import dash
import dash_bootstrap_components as dbc


### Dash Instance ###
app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.ZEPHYR],
    suppress_callback_exceptions=True,
)
