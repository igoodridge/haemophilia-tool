import pandas as pd
import os
from sas7bdat import SAS7BDAT
from src.data_import.constants import CE_COLS, CE_DATES
###from constants import CE_COLS, CE_DATES
import platform
from sshfs import SSHFileSystem
import io

#Function to get sdtm data from P drive and select only required columns and convert date columns to datetime
#NOTE must run: sudo mount -t drvfs P: /mnt/projstat in linux before being able to use P: drive

def get_sdtm_data(fs, trial: str, domain: str, columns: list = None, datecolumns: list = None, sortby: list = None) -> pd.DataFrame:
    trial = trial.lower().strip()
    project = trial.split('-')[0]


    #If not running on server then connect to P drive as below:
    if fs is None:
            
        if platform.system() == 'Linux':
            sdtm_file = f'/mnt/projstat/{project}/{trial}/current/dm/data/sdtm/{domain}.sas7bdat'
        elif platform.system() == 'Windows':
            sdtm_file = f'P:\\{project}\\{trial}\\current\\dm\\data\\sdtm\\{domain}.sas7bdat'

        print('path: ', sdtm_file)

        df = SAS7BDAT(sdtm_file).to_data_frame()

    #Connect to P drive over network:
    else:

        path = f'/projstat/{project}/{trial}/current/dm/data/sdtm/{domain}.sas7bdat'

        with fs.open(path) as stream:
            df = pd.read_sas(io.BytesIO(stream.read()), format='sas7bdat', encoding='iso-8859-1')
    
    if columns is not None:
        df = df.reindex(columns=columns)
    if datecolumns is not None:
        for col in datecolumns:
            df[col] = pd.to_datetime(df[col], format='%Y-%m-%dT%H:%M')
    if sortby is not None:
        df = df.sort_values(by=sortby)
    return df


    


if __name__ == '__main__':
    ce = get_sdtm_data(None, 'nn7415-4307', 'ce', columns=CE_COLS, datecolumns=CE_DATES, sortby=['USUBJID'])
    if type(ce) == pd.DataFrame:
        print(ce)
    else:
        print('Data is not being imported correctly.')

    cm = get_sdtm_data(None, 'nn7769-4513mad', 'cm')
    print(cm.head())
    print(cm.columns.values)


