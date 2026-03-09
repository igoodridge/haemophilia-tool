import pandas as pd
import numpy as np
from itertools import cycle
import random
import os
import pickle

#Creates fake data under trial ID nn1234-5678 for bleeds, medication and dose data

#Columns for each data type
BLEED_COLS = ['STUDYID', 'USUBJID', 'BLEED_ID', 'TERM', 'CATEGORY', 'BLEED_LOCATION', 'LATERAL_POSITION', 'BLEED_SEVERITY', 'BLEED_START_DATE', 'BLEED_STOP_DATE', 'BODY_PART', 'JOINT_LOCATION', 'BLEED_CAUSE', 'TREATYN', 'COLOR']
MED_COLS = ['STUDYID', 'USUBJID', 'HAEM_MED_DRUG', 'CMDECOD', 'CMCAT', 'HAEM_MED_TRT_CATEGORY', 'CMCLAS', 'HAEM_MED_DOSE', 'UNITS', 'HAEM_MED_TRT_TYPE', 'CMSTDTC', 'HAEM_MED_DATE', 'COLOR', 'CMSPID', 'CMREFID']
DOSE_COLS = ['STUDYID', 'USUBJID', 'DRUG', 'ECSCAT', 'DOSE', 'START_DATE_TIME', 'STOP_DATE_TIME', 'STUDY_DAY_START', 'STUDY_DAY_END', 'COLOR']

#Lists for bleed location check
JOINT_LOCATIONS = ['', '', '', '', '', '', '', '', '', '', '', 'KNEE', 'KNEE JOINT', 'ANKLE', 'ANKLE JOINT', 'WRIST', 'WRIST JOINT', 'FINGERS', 'FINGER', 'ELBOW', 'ELBOW JOINT', 'SHOULDER', 'SHOULDER JOINT', 'HIP', 'HIP JOINT', 'TOE', 'TOES', 'JAW']
MUSCLE_LOCATIONS = ['ARM', 'LEG', 'HAND', 'BUTTOCK', 'BUTTOCKS', 'HEAD/NECK', 'HEAD & NECK', 'HEAD / NECK', 'CHEST', 'BACK', 'STOMACH', 'FOOT']
SKIN_LOCATIONS = ['ARM', 'LEG', 'HAND', 'BUTTOCKS', 'BUTTOCK', 'HEAD/NECK', 'HEAD / NECK',  'CHEST', 'BACK', 'STOMACH', 'FOOT']
OTHER_LOCATIONS = ['GASTROINTESTINAL','GASTROINTESTINAL SYSTEM', 'STOMACH', 'URINARY SYSTEM', 'MOUTH, GUMS OR NOSE', 'MOUTH/GUMS/NOSE', 'CENTRAL NERVOUS SYSTEM']
ALL_LOCATIONS = ['', '', 'MUSCLE', 'SKIN', 'JOINT', 'GASTROINTESTINAL', 'GASTROINTESTINAL SYSTEM', 'STOMACH', 'URINARY SYSTEM', 'MOUTH, GUMS OR NOSE', 'MOUTH/GUMS/NOSE', 'CENTRAL NERVOUS SYSTEM', 'OTHER']

BODY_PART = ['ARM', 'BACK', 'HAND', 'HEAD/NECK', 'LEG', 'FOOT', 'BUTTOCKS', '', '', '', '', '', '', '', '']

def generate_fake_dataframe(size, cols, col_names = None, intervals = None, seed = None):

    """Main function used to generate fake data. 
    Contains functions required for setting up dataframes with columns using different data types.
    Code taken from github. """
    
    categories_dict = {'all_locations': ['', '', 'MUSCLE', 'SKIN', 'JOINT', 'GASTROINTESTINAL', 'GASTROINTESTINAL SYSTEM', 'STOMACH', 'URINARY SYSTEM', 'MOUTH, GUMS OR NOSE', 'MOUTH/GUMS/NOSE', 'CENTRAL NERVOUS SYSTEM', 'OTHER'],
                       'body_part': BODY_PART,
                       'joints': JOINT_LOCATIONS,
                       'muscle': MUSCLE_LOCATIONS,
                       'skin': SKIN_LOCATIONS,
                      }
    default_intervals = {"i" : (0,10), "f" : (0,100), "c" : ("all_locations", 5), "d" : ("2020-01-01","2020-12-31")}
    rng = np.random.default_rng(seed)

    first_c = default_intervals["c"][0]
    categories_names = cycle([first_c] + [c for c in categories_dict.keys() if c != first_c])
    default_intervals["c"] = (categories_names, default_intervals["c"][1])
    
    if isinstance(col_names,list):
        assert len(col_names) == len(cols), f"The fake DataFrame should have {len(cols)} columns but col_names is a list with {len(col_names)} elements"
    elif col_names is None:
        suffix = {"c" : "cat", "i" : "int", "f" : "float", "d" : "date"}
        col_names = [f"column_{str(i)}_{suffix.get(col)}" for i, col in enumerate(cols)]

    if isinstance(intervals,list):
        assert len(intervals) == len(cols), f"The fake DataFrame should have {len(cols)} columns but intervals is a list with {len(intervals)} elements"
    else:
        if isinstance(intervals,dict):
            assert len(set(intervals.keys()) - set(default_intervals.keys())) == 0, f"The intervals parameter has invalid keys"
            default_intervals.update(intervals)
        intervals = [default_intervals[col] for col in cols]
    df = pd.DataFrame()
    for col, col_name, interval in zip(cols, col_names, intervals):
        if interval is None:
            interval = default_intervals[col]
        assert (len(interval) == 2 and isinstance(interval, tuple)) or isinstance(interval, list), f"This interval {interval} is neither a tuple of two elements nor a list of strings."
        if col in ("i","f","d"):
            start, end = interval
        if col == "i":
            df[col_name] = rng.integers(start, end, size)
        elif col == "f":
            df[col_name] = rng.uniform(start, end, size)
        elif col == "c":
            if isinstance(interval, list):
                categories = np.array(interval)
            else:
                cat_family, length = interval
                if isinstance(cat_family, cycle):
                    cat_family = next(cat_family)
                assert cat_family in categories_dict.keys(), f"There are no samples for category '{cat_family}'. Consider passing a list of samples or use one of the available categories: {categories_dict.keys()}"
                categories = rng.choice(categories_dict[cat_family], length, replace = False, shuffle = True)
            df[col_name] = rng.choice(categories, size, shuffle = True)
        elif col == "d":
            df[col_name] = rng.choice(pd.date_range(start, end), size)
    return df       




def get_subject_num(df) -> dict:
    """Creates a dictionary mapping USUBJID to a subject number (integer value for that subject)."""
    df = df.sort_values(by='USUBJID', ascending=False)
    n = 1
    n = int(n)
    subject_num = {}
    for subject in df['USUBJID'].unique():
        subject_num[subject] = n
        n+=1
        n = int(n)
    return subject_num


def add_subject_num(df: pd.DataFrame, subject_num: dict) -> pd.DataFrame:
    """Function to map the SUBJID to a subject number (as in real data)."""
    df['SUBJECT_NUM'] = df['USUBJID'].map(subject_num)
    return df

def create_fake_bleeds(size=500):
    """Creates fake dataset for bleed data. 
    Alter the size argument to determine the number of records being produced."""
    df = generate_fake_dataframe(
        size=size,
        cols='ciicccccddccccc',
        col_names=BLEED_COLS,
        intervals=[['NN1234-5678'], 
                (900000, 900050),
                (1, 100),
                ['BLEEDING EPISODES'],
                ['BLEEDING'],
                    ('all_locations', 11),
                    ['LEFT', 'RIGHT', '', '', ''],
                    ['MILD/MODERATE', 'SEVERE', '', ''],
                    ("2020-01-01","2022-12-31"),
                    ("2020-01-01","2022-12-31"),
                    ('body_part', 15),
                    ('joints', 21),
                    ['SPONTANEOUS', 'TRAUMATIC'],
                    ['Y', 'N', 'N'],
                    ['#EF553B']
                ]
            )
    df['USUBJID'] = df['USUBJID'].astype(str)
    bleed_lengths = [0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 4, 4, 4, 5, 5, 5, 5, 5, 5, 5, 6, 6, 6, 7, 8, 9, 10, 14, 17, 20, 40]
    df['GAP'] = [random.choice(bleed_lengths) for k in df.index]
    df['GAP'] = pd.to_timedelta(df['GAP'], unit='days')
    df['BLEED_STOP_DATE'] = df['BLEED_START_DATE'] + df['GAP']
    df = df.drop(columns='GAP')
    subject_num = get_subject_num(df)
    df = add_subject_num(df, subject_num)
    print(df)
    return df, subject_num


def create_fake_meds(subject_num, size=300):
    """Generates fake haem med table."""
    df = generate_fake_dataframe(
        size=size,
        cols='ciccccciccddcii',
        col_names=MED_COLS,
        intervals=[['NN1234-5678'], 
                (900000, 900050),
                ['ADVATE', 'NUWIQ', 'NOOVOSEVEN', 'FEIBA', 'ESPEROC', 'IMMUNATE'],
                [''],
                ['HAEMOPHILIA CONCOMITANT MEDICATION'],
                ['OTHER', 'STANDARD HALF-LIFE FACTOR CONCENTRATE', 'RFVIIA', 'PLASMA DERIVED FVIII', 'OTHER'],
                [''],
                (200, 400),
                ['mg'],
                ['TREATMENT OF BLEED'],
                ("2020-01-01","2022-12-31"),
                ("2020-01-01","2022-12-31"),
                ['#636EFA'],
                (0, 10000000),
                (0, 10000000)
                ]
            )
    df['USUBJID'] = df['USUBJID'].astype(str)
    df['HAEM_MED_DATE_TIME'] = df['CMSTDTC']
    df = add_subject_num(df, subject_num)
    print(df)
    return df



def create_fake_dose(subject_num, size=4800):
    """Generates fake dose table."""
    df = generate_fake_dataframe(
        size=size,
        cols='cicccddiic',
        col_names=DOSE_COLS,
        intervals=[['NN1234-5678'], 
                (900000, 900050),
                ['STUDY DRUG'],
                ['EDIARY', 'FIRST DOSE', 'INFORM'],
                [0, 0, 20, 20, 20, 20, 20, 20, 20, 20, 18, 19, 18, 19, 17, 22, 24, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, 80, 60, 20, 20, 20, 20, 20, 20, 20, 20, 20, 20, np.nan, np.nan, np.nan],
                ("2020-01-01","2020-12-31"),
                ("2020-01-01","2020-12-31"),
                (0, 50),
                (0, 50),
                ['#636EFA']
                ]
            )
    df['USUBJID'] = df['USUBJID'].astype(str)
    df['STOP_DATE_TIME'] = df['START_DATE_TIME']
    df['STUDY_DAY_END'] = df['STUDY_DAY_START']
    df = add_subject_num(df, subject_num)
    print(df)
    return df




if __name__ == '__main__':
    bleeds, subject_num = create_fake_bleeds()
    meds = create_fake_meds(subject_num)
    dose = create_fake_dose(subject_num)
    if os.path.exists('./fake_data/NN1234-5678/') is False:
        os.makedirs('./fake_data/NN1234-5678/')
    bleeds.to_csv('./fake_data/NN1234-5678/NN1234-5678_bleeds.csv', index=False)
    meds.to_csv('./fake_data/NN1234-5678/NN1234-5678_meds.csv', index=False)
    dose.to_csv('./fake_data/NN1234-5678/NN1234-5678_dose.csv', index=False)
    with open('./fake_data/NN1234-5678/NN1234-5678_subject_num.pkl', 'wb') as file:
        pickle.dump(subject_num, file)

