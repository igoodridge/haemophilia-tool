import pandas as pd
import numpy as np

from src.data_checks.constants import *


def get_missing_data(df: pd.DataFrame, columns: list) -> pd.DataFrame:

    """Detects null values in columns defined in list. Records with at least one 
    missing value will have 'Y' in the new 'MISSING' column."""

    df['MISSING'] = 'N'
    for col in columns:
        df['MISSING'] = np.where(df[col].isnull(), 'Y', df['MISSING'])
    return df


def get_duplicates(df: pd.DataFrame, columns: list) -> pd.DataFrame:

    """Detects duplicate records, with the columns that must be the same in order to be a 
    duplicate specified in the columns list. Returns dataframe with 'DUPLICATED' column in
    which duplicated records have a value of 'Y'."""

    no_duplicates = df.drop_duplicates(columns, keep=False)
    df = df.merge(no_duplicates, how='outer', indicator=True)
    df['DUPLICATED'] = np.where(df['_merge']=='left_only', 'Y', 'N')
    df = df.drop(columns='_merge')
    return df


def check_bleed_locations(df: pd.DataFrame) -> pd.DataFrame:

    """Detects bleeds where BLEED LOCATION does not match up with either JOINT_LOCATION or 
    BODY_PART as specified in the lists in /src/data_checks/constants.py. Adds 'LOCATION_ISSUE'
     column,  with 'Y' indicating an issue. """

    df['LOCATION_ISSUE'] = np.where((df['BLEED_LOCATION'].str.contains('JOINT'))&(~df['JOINT_LOCATION'].isin(JOINT_LOCATIONS))
        |((df['BLEED_LOCATION'].str.contains('MUSCLE'))&(~df['BODY_PART'].isin(MUSCLE_LOCATIONS)))
        |((df['BLEED_LOCATION'].str.contains('SKIN'))&(~df['BODY_PART'].isin(SKIN_LOCATIONS)))
        |((df['BLEED_LOCATION'].isin(OTHER_LOCATIONS))&((df['BODY_PART'].notnull())|(df['JOINT_LOCATION'].notnull())|(df['LATERAL_POSITION'].notnull())))
        |((~df['BLEED_LOCATION'].isin(ALL_LOCATIONS))&(df['BLEED_LOCATION'].notnull())),'Y', 'N')
    
    return df


def get_long_bleeds(df: pd.DataFrame, length=7) -> pd.DataFrame:

    """Identifies bleeds over x days in length (default 7 days). 'LONG_BLEED' column added with 'Y' as value
    when over x days."""

    df['BLEED_LENGTH'] = df['BLEED_STOP_DATE'] - df['BLEED_START_DATE'] + pd.Timedelta(days=1)
    df['LONG_BLEED'] = np.where(df['BLEED_LENGTH']>=pd.Timedelta(days=length), 'Y', 'N')
    df['BLEED_LENGTH'] = df['BLEED_LENGTH'].dt.days
    return df 



def trt_N_Y(bleeds: pd.DataFrame, meds: pd.DataFrame) -> pd.DataFrame:

    """Returns bleeds dataframe with additiion of 'TRT_N_BUT_MEDS' and 'TRT_Y_NO_MEDS' in which the 
    former shows records marked as not treated with medication during the bleeding episode, and the latter
    shows records marked as treated with no corresponding medication records. The latter is also shown in 
    the meds dataframe."""

    #If datatype of STUDYID and USUBJID columns in both dataframes are not the same, 
    # make them both type object (string)
    if bleeds['STUDYID'].dtype != meds['STUDYID'].dtype:
        meds['STUDYID'] = meds['STUDYID'].astype(object)
        bleeds['STUDYID'] = bleeds['STUDYID'].astype(object)

    if bleeds['USUBJID'].dtype != meds['USUBJID'].dtype:
        meds['USUBJID'] = meds['USUBJID'].astype(object)
        bleeds['USUBJID'] = bleeds['USUBJID'].astype(object)

    #Merge bleeds and meds dataframes
    bleeds_meds_merged = bleeds.merge(meds, how='left', on=['STUDYID', 'USUBJID', 'SUBJECT_NUM'])

    #Create new column 'IS_BETWEEN' which shows whether the haemostatic medication is 
    # given within the bleeding episode time period
    bleeds_meds_merged['IS_BETWEEN'] = np.where((bleeds_meds_merged.HAEM_MED_DATE.between(
     (bleeds_meds_merged.BLEED_START_DATE), (bleeds_meds_merged.BLEED_STOP_DATE)) |
     (bleeds_meds_merged.HAEM_MED_DATE.dt.date == bleeds_meds_merged.BLEED_START_DATE.dt.date) |
     (bleeds_meds_merged.HAEM_MED_DATE.dt.date == bleeds_meds_merged.BLEED_STOP_DATE.dt.date)
     ), True, False)
    
    
    ### Medicated Bleeds ###

    #Get medicated bleeds marked as not treated
    bleeds_meds_merged_medicated = bleeds_meds_merged.groupby(by=['STUDYID', 'USUBJID', 'BLEED_ID']).filter(
        lambda x: any(x.IS_BETWEEN==True))
    bleeds_meds_merged_medicated = bleeds_meds_merged_medicated.drop(columns=['IS_BETWEEN']).drop_duplicates(
        subset=['STUDYID', 'USUBJID', 'BLEED_ID'])
    bleeds_meds_merged_medicated['TRT_N_BUT_MEDS'] = np.where((bleeds_meds_merged_medicated['TREATYN']=='N') | (
        bleeds_meds_merged_medicated['TREATYN'].isnull()), 'Y', 'N')
    bleeds_meds_merged_medicated['TRT_Y_NO_MEDS'] = 'N'


    #Get table of meds that are given when bleed marked as not treated
    meds_marked_N_but_treated = bleeds_meds_merged.loc[(bleeds_meds_merged['IS_BETWEEN']==True) & (bleeds_meds_merged['TREATYN']=='N')]
    meds_marked_N_but_treated = meds_marked_N_but_treated.drop(columns=['BLEED_ID', 'TERM', 'CATEGORY', 'BLEED_LOCATION', 'BODY_PART', 'JOINT_LOCATION', 'LATERAL_POSITION', 'BLEED_SEVERITY', 
                                                                        'BLEED_START_DATE', 'BLEED_STOP_DATE', 'COLOR_x', 'BLEED_CAUSE', 'TREATYN', 'IS_BETWEEN'
                                                                        ])
    meds_marked_N_but_treated = meds_marked_N_but_treated.drop_duplicates()
    meds_marked_N_but_treated['TRT_N_BUT_MEDS'] = 'Y'



    ### Unmedicated Bleeds ###
    
    bleeds_meds_merged_not_medicated = bleeds_meds_merged.groupby(by=['STUDYID', 'USUBJID', 'BLEED_ID']).filter(
        lambda x: all(x.IS_BETWEEN==False))
    bleeds_meds_merged_not_medicated = bleeds_meds_merged_not_medicated.drop(columns=['HAEM_MED_DRUG', 'COLOR_y', 'CMREFID', 'CMSPID', 'CMDECOD', 'CMCAT', 'UNITS', 'HAEM_MED_TRT_TYPE', 'CMSTDTC', 'HAEM_MED_DATE', 'HAEM_MED_DOSE', 'CMCLAS', 'HAEM_MED_TRT_CATEGORY'])
    bleeds_meds_merged_not_medicated = bleeds_meds_merged_not_medicated.rename(columns={'COLOR_x':'COLOR'})
    bleeds_meds_merged_not_medicated = bleeds_meds_merged_not_medicated.drop_duplicates().drop(
        columns='IS_BETWEEN')
    bleeds_meds_merged_not_medicated['TRT_Y_NO_MEDS'] = np.where(
        bleeds_meds_merged_not_medicated['TREATYN']=='Y', 'Y', 'N')
    bleeds_meds_merged_not_medicated['TRT_N_BUT_MEDS'] = 'N'

    bleeds_meds_merged_medicated = bleeds_meds_merged_medicated.drop(columns=['COLOR_y', 'HAEM_MED_DRUG', 'CMREFID', 'CMSPID', 'CMDECOD', 'CMCAT', 'UNITS', 'HAEM_MED_TRT_TYPE', 'CMSTDTC', 'HAEM_MED_DOSE', 'HAEM_MED_DATE', 'CMCLAS', 'HAEM_MED_TRT_CATEGORY'])
    bleeds_meds_merged_medicated = bleeds_meds_merged_medicated.rename(columns={'COLOR_x':'COLOR'})


    #Merge medicated and unmedicated    
    bleeds_meds_merged = pd.concat([bleeds_meds_merged_medicated, bleeds_meds_merged_not_medicated], 
                                   ignore_index=True)
    
    #Merge meds identified in check with main meds table
    meds_marked_N_but_treated = meds_marked_N_but_treated.drop_duplicates()
    meds_marked_N_but_treated = meds_marked_N_but_treated.rename(columns={'COLOR_y':'COLOR'})
    meds = meds.merge(meds_marked_N_but_treated, how='left', indicator=True)
    meds = meds.drop(columns='_merge')
    meds['TRT_N_BUT_MEDS'] = meds['TRT_N_BUT_MEDS'].fillna('N')


    bleeds = bleeds_meds_merged

    return bleeds, meds



def meds_outside_bleeding_episodes(bleeds: pd.DataFrame, meds: pd.DataFrame) -> pd.DataFrame: 
    
    """Find medication given outside of any bleeding episode. 'OUTSIDE_BLEEDS' column will be added 
    to meds dataframe containing a 'Y' in such cases. This only detects medication which is classed
    as 'ON-DEMAND' or 'TREATMENT OF BLEEDING EPISODE.'"""

    bleeds = bleeds[['USUBJID', 'BLEED_START_DATE', 'BLEED_STOP_DATE']]
    merged = meds.merge(bleeds, how='left', on='USUBJID')
    merged['IS_BETWEEN'] = np.where(merged.HAEM_MED_DATE.between(
    (merged.BLEED_START_DATE), (merged.BLEED_STOP_DATE)), True, False)
    outside_bleeding_episodes = merged.groupby(by=['USUBJID', 'CMSPID']).filter(lambda x: all(x.IS_BETWEEN==False))
    outside_bleeding_episodes = outside_bleeding_episodes.drop(columns=['IS_BETWEEN', 'BLEED_START_DATE', 'BLEED_STOP_DATE']).drop_duplicates()
    outside_bleeding_episodes = outside_bleeding_episodes.loc[outside_bleeding_episodes['HAEM_MED_TRT_TYPE'].isin(['TREATMENT OF BLEED', 'TREATMENT OF BLEEDING EPISODE', 'ON-DEMAND', 'ON-DEMAND (TREATMENT OF BLEEDS)'])]
    meds = meds.merge(outside_bleeding_episodes, how='left', indicator=True)
    meds['OUTSIDE_BLEEDS'] = np.where(meds['_merge']=='both', 'Y', 'N')
    meds = meds.drop(columns='_merge')
    return meds


def get_missed_doses(dose: pd.DataFrame, gap: int = 7) -> pd.DataFrame:
    """Function to identify missed trial drug doses. 
    
    Arguments
    gap - allowed number of days between doses
    """
    dose_diff = dose.sort_values(by=['USUBJID', 'STOP_DATE_TIME'])
    dose_diff['DAYS_SINCE_LAST_DOSE'] = pd.to_timedelta(dose_diff.groupby('USUBJID')['STOP_DATE_TIME'].diff()) - pd.Timedelta(days=1)
    dose_diff['DAYS_SINCE_LAST_DOSE'] = pd.to_numeric(dose_diff['DAYS_SINCE_LAST_DOSE'].dt.days)

    dose_diff['MISSED_DOSES'] = np.where((dose_diff['DAYS_SINCE_LAST_DOSE'].notnull()) | (dose_diff['DAYS_SINCE_LAST_DOSE']>gap), 'Y', 'N')

    #print(dose_diff)

    return dose_diff



if __name__ == '__main__':
    # bleeds = pd.read_csv('./data/sdtm/nn7769-4513mad/nn7769-4513mad_bleeds.csv', parse_dates=['BLEED_START_DATE', 'BLEED_STOP_DATE'])
    # meds = pd.read_csv('./data/sdtm/nn7769-4513mad/nn7769-4513mad_meds.csv', parse_dates=['HAEM_MED_DATE'])
    # meds = meds_outside_bleeding_episodes(bleeds, meds)
    # meds = meds.filter(['USUBJID', 'HAEM_MED_TRT_TYPE', 'OUTSIDE_BLEEDS'])
    # print(meds.head())

    # bleed_cols = ['STUDYID', 'USUBJID', 'BLEED_START_DATE', 'BLEED_STOP_DATE', 'BLEED_ID', 'TREATYN']
    # bleed_data = {
    #     'STUDYID': [1000, 1000, 1000, 1000, 1000, 1000],
    #     'USUBJID': [101, 101, 101, 101, 101, 102],
    #     'SUBJECT_NUM': [1, 1, 1, 1, 1, 2],
    #     'BLEED_START_DATE': ['10-03-2024', '15-03-2023', '21-03-2023', '21-03-2023', '30-03-2023', '30-03-2023'],
    #     'BLEED_STOP_DATE': ['12-03-2024', '16-03-2023', '25-03-2023', '27-03-2023', '31-03-2023', '01-04-2023'],
    #     'BLEED_ID': [1, 2, 3, 4, 5, 1],
    #     'TREATYN': ['N', 'Y', 'N', 'Y', 'N', 'Y']
    # }
    # med_cols = ['STUDYID', 'USUBJID', 'HAEM_MED_DATE']
    # med_data = {
    #    'STUDYID': [1000, 1000, 1000, 1000, 1000, 1000],
    #     'USUBJID': [101, 101, 101, 101, 101, 102],
    #     'SUBJECT_NUM': [1, 1, 1, 1, 1, 2],
    #     'HAEM_MED_DATE': ['11-03-2023', '17-03-23', '23-03-2023', '30-03-2023', '30-03-2023', '31-03-2023']

    # }

    # test_bleeds = pd.DataFrame(bleed_data)
    # test_bleeds['BLEED_START_DATE'] = pd.to_datetime(test_bleeds['BLEED_START_DATE'])
    # test_bleeds['BLEED_STOP_DATE'] = pd.to_datetime(test_bleeds['BLEED_STOP_DATE'])
    # test_meds = pd.DataFrame(med_data)
    # test_meds['HAEM_MED_DATE'] = pd.to_datetime(test_meds['HAEM_MED_DATE'])

    # bleeds, meds = trt_N_Y(test_bleeds, test_meds)
    # print(bleeds)
    # print(meds)

    dose = pd.read_csv('./data/sdtm/nn7769-4513mad/nn7769-4513mad_dose.csv', parse_dates=['START_DATE_TIME', 'STOP_DATE_TIME'])
    dose_diff = get_missed_doses(dose)