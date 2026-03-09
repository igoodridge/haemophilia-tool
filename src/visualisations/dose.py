#Import packages
import pandas as pd
import numpy as np
from plotly import graph_objects as go
from datetime import date


def create_daily_dose_figure(dose: pd.DataFrame, subject_num: dict):
    
    #Create figure
    fig = go.Figure()

    dose['STOP_DATE_TIME'] = pd.to_datetime(dose['STOP_DATE_TIME'], format='%Y-%m-%d')
    dose['START_DATE_TIME'] = pd.to_datetime(dose['START_DATE_TIME'], format='%Y-%m-%d')


    #Add data to be associated with each point e.g. to access for hovers etc. 
    custom_data = np.stack([dose['USUBJID'], 
                            dose['DOSE'], 
                            dose['START_DATE_TIME'], dose['STOP_DATE_TIME'].dt.strftime('%b %w, %Y'), 
                            dose['STUDY_DAY_START'], dose['STUDY_DAY_END'],
                            dose['SUBJECT_NUM']
                            ],
                            axis=-1)
    
    #print(dose['STUDY_DAY_START'])
    
    #Add scatter
    fig.add_trace(go.Scattergl(
        x=dose['STUDY_DAY_START'],
        y=dose['SUBJECT_NUM'],
        mode='markers', 
        name='dose',
        marker_size=4,
        marker_color=dose['COLOR'],
        customdata=custom_data,
    ))

    #PPX hover
    hovertemp = "<b>USUBJID: </b> %{y} <br>"
    hovertemp += "<b>Study day: </b> %{x} <br>"
    hovertemp += "<b>Date: </b> %{customdata[3]} <br>"
    hovertemp += "<b>Dose: </b> %{customdata[1]} <br>"

    fig.update_traces(name='dose', 
                      hovertemplate=hovertemp,
        )


    subject_list = list(subject_num.keys())
    subject_num_list = list(subject_num.values())


    #Add subject number to ticks, add title, remove legend
    fig.update_layout(
            yaxis=dict(
                tickmode='array',
                tickvals=subject_num_list, 
                ticktext=subject_list,
                tickfont=dict(size=12)),
            xaxis_title='Study Day',
            margin=dict(t=40, b=40, l=40, r=20),
            width=2000,
            #showlegend=True,

            hoverlabel=dict(bordercolor='white') #sets both text and border color to white
        )


    return fig


def create_individual_subject_dose_graph(subject_dose):

    fig = go.Figure()


    custom_data = np.stack([subject_dose['USUBJID'], 
                            subject_dose['DOSE'], 
                            subject_dose['START_DATE_TIME'], 
                            subject_dose['STUDY_DAY_START'],
                            ],
                            axis=-1)
    
    fig.add_trace(go.Scatter(
        x=subject_dose['STUDY_DAY_START'],
        y=subject_dose['DOSE'],
        mode='markers', 
        name='dose',
        marker_size=4,
        customdata=custom_data,
    ))




    #Dose hover
    hovertemp = "<b>Study day: </b> %{x} <br>"
    hovertemp += "<b>Dose: </b> %{y} <br>"
    hovertemp += "<b>Date: </b> %{customdata[2]} <br>"

    fig.update_traces(name='dose', 
                      hovertemplate=hovertemp,
        )

    fig.update_layout(
            xaxis_title='Study Day',
            yaxis_title='Dose',
            margin=dict(t=10, b=10, l=10, r=50),
            hoverlabel=dict(bordercolor='white'), #sets both hover label text and border color to white
        )
    
    return fig