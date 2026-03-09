#Import packages
import pandas as pd
import numpy as np
from plotly import graph_objects as go
from datetime import date

from src.data_import.trial import Trial



class Figures():

    def __init__(self, trialid: str, bleeds: pd.DataFrame, meds: pd.DataFrame, subject_num: dict, subjid_dict: dict, blinded: bool):
        self.trialid = trialid
        self.bleeds = bleeds
        self.meds = meds
        self.subject_num = subject_num
        self.subjid_dict = subjid_dict

        self.blinded = blinded
        pass


    def create_bleed_figure(self):


        #For blinded trials, show fake USUBJID, for unblinded trials, show real SUBJID
        if self.blinded or self.subjid_dict is None:
            self.subject_list = list(self.subject_num.keys())
            self.subject_num_list = list(self.subject_num.values())
        else:
            self.subject_list = list(self.subjid_dict.keys())
            self.subject_num_list = list(self.subjid_dict.values())

        self.bleeds['USUBJID'] = self.bleeds['USUBJID'].astype(str)
        #self.bleeds['SUBJECT_NUM'] = self.bleeds['USUBJID'].map(self.subject_num)

        #print(self.subject_num)


        #Create figure
        fig = go.Figure()

        customdata_haem =[self.meds['USUBJID'].astype(str), self.meds['HAEM_MED_DRUG'], self.meds['HAEM_MED_DOSE'], self.meds['UNITS'], self.meds['HAEM_MED_DATE'], self.meds['COLOR']]

        #Add scatter for meds
        fig.add_trace(go.Scatter(x=self.meds['HAEM_MED_DATE'], y=self.meds['SUBJECT_NUM'], 
        mode='markers', marker_color=self.meds['COLOR'],
        marker_size=6,
        customdata=np.stack(customdata_haem, axis=-1),
        name='Medication',
        opacity=0.7))

        #Medication hover
        #hovertemp_med = "<b>Medication</b><br>"
        hovertemp_med = "<b>USUBJID: </b> %{y} <br>"
        hovertemp_med += "<b>Date: </b> %{x} <br>"
        hovertemp_med += "<b>Treatment: </b> %{customdata[1]} <br>"
        hovertemp_med += "<b>Dose: </b> %{customdata[2]} %{customdata[3]}<br>"

        fig.update_traces(name='Medication', hovertemplate=hovertemp_med
            )

        #Add lines for bleeds
        for (start, end, subject, num, trtloc, color) in zip(self.bleeds['BLEED_START_DATE'], self.bleeds['BLEED_STOP_DATE'], 
        self.bleeds['USUBJID'], self.bleeds['SUBJECT_NUM'], self.bleeds['BLEED_LOCATION'], self.bleeds['COLOR']):
            #print(start, end, subject, num, color)
            name = f"{subject}"
            fig.add_trace(go.Scatter(x=[start, end], y=[num, num],
            mode='lines', name=name, customdata = [trtloc, trtloc], marker_color=color, opacity=0.6, legendgroup='Bleed duration', showlegend=False))

        customdata_bleed = np.stack([self.bleeds['USUBJID'].astype(str), self.bleeds['BLEED_LOCATION'], self.bleeds['BLEED_ID']], axis=-1)

        #Add start for bleeds
        fig.add_trace(go.Scatter(x=self.bleeds['BLEED_START_DATE'], y=self.bleeds['SUBJECT_NUM'],
            mode='markers', name='Start of Bleed', customdata = customdata_bleed, marker_color=self.bleeds['COLOR'], opacity=0.7, 
            marker_symbol='triangle-right', marker_size=6, marker=dict(line=dict(width=1, color=self.bleeds['COLOR']))))
            #Format hovertips
        hovertemp_st = "<b>USUBJID: %{y} </b><br>"
        hovertemp_st += "<b>Start Date: </b> %{x} <br>"
        hovertemp_st += "<b>Bleed location: </b> %{customdata[1]} <br>"

        fig.update_traces(selector=dict(name='Start of Bleed'), hovertemplate=hovertemp_st
            )

        #Add end for bleeds
        fig.add_trace(go.Scatter(x=self.bleeds['BLEED_STOP_DATE'], y=self.bleeds['SUBJECT_NUM'],
            mode='markers', name='End of Bleed', customdata = customdata_bleed, marker_color=self.bleeds['COLOR'], opacity=0.7, 
            marker_symbol='triangle-left', marker_size=6, marker=dict(line=dict(width=1, color=self.bleeds['COLOR']))))
            #Format hovertips
        hovertemp_end = "<b>USUBJID: %{y} </b><br>"
        hovertemp_end += "<b>End Date: </b> %{x} <br>"
        hovertemp_end += "<b>Bleed location: </b> %{customdata[1]} <br>"

        fig.update_traces(selector=dict(name='End of Bleed'), hovertemplate=hovertemp_end
            )
    

        #Add subject number to ticks, add title, remove legend
        fig.update_layout(
            yaxis=dict(
                tickmode='array',
                tickvals=self.subject_num_list, 
                ticktext=self.subject_list,
                tickfont=dict(size=12)),
            #title=('<b>'+ self.trialid +'</b> (Trial ID: '+ self.trialid +')<br>Bleeds and haemostatic medication'+title_suffix+' '+today),
            margin=dict(t=40, b=40, l=40, r=20),
            showlegend=True,
            hoverlabel=dict(bordercolor='white') #sets both text and border color to white
        )

        fig.update_layout(legend=dict(
            orientation="h",
            yanchor="bottom",
            y=0.97,
            xanchor="right",
            x=0.98,
        ))

        
    
        #print('Figure done.')

        return fig



if __name__ == '__main__':

    Trial_4307 = Trial(trial='nn7415-4307')
    Figures_4307 = Figures(Trial_4307.trialid, Trial_4307.bleeds, Trial_4307.meds, Trial_4307.subject_num, Trial_4307.subject_list, Trial_4307.subject_num_list)
    fig = Figures_4307.create_bleed_figure()

