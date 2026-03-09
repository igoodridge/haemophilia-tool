# Script contains three classes: Trial, DataCategory and SDTMDataDomain which concern data import and processing.
# Trial class should then contain the final datasets for each category.

#Import packages
import pandas as pd
import os
import platform
import numpy as np
from sas7bdat import SAS7BDAT
from datetime import datetime, date
from sshfs import SSHFileSystem
import io
import pickle
import json

#Import constants and custom functions
from src.data_import.constants import SDTM_DOMAIN_INFO, CATEGORIES, DM_COLS, CATEGORY_INFO
from src.data_import.utils import get_sdtm_data
from src.data_checks.utils import get_missing_data, get_duplicates, check_bleed_locations, get_long_bleeds, trt_N_Y, meds_outside_bleeding_episodes, get_missed_doses


#List of columns created as part of data checks
ERROR_COLS = ['MISSING', 'DUPLICATED', 'TRT_N_BUT_MEDS', 'TRT_Y_NO_MEDS', 'LONG_BLEED', 'LOCATION_ISSUE', 'OUTSIDE_BLEEDS']


#Class containing all data relevant to haemophilia trial to be used for visualisations, error checks etc.
class Trial():
    """
    Represents a trial with trial data and metadata.

    Keyword arguments:
    trial -- the full trial number e.g. nn4715-4307
    user -- user's initials e.g. isgr

    This class contains functions which bring together all data for a trial.
    Data import works by first identifying whether the trial is a dummy trial or real,
    and then whether the application is running locally or on the server. Data is then imported
    according to these rules, and merged to form the three main datasets used in the app: 
    bleeds, meds and dose. 

    The class also contains information on whether the trial is blinded, and specifies which checks 
    should be run on which datasets. 
    """

    def __init__(self, trial: str, user: str):
        self.trial = trial.lower().strip()
        self.user = user

        #Calculate project and trialid from trial
        self.project = self.trial.split('-')[0]
        self.trialid = self.trial.split('-')[1]

        self.trial_config = None

        #Check if selected trial is the test trial data
        if self.trial == 'nn1234-5678':
            self.test_data = True
            self.blinded = False
        else:
            self.test_data = False
                
        #If running on server, mount whale drive. If not on server, fs=None
        if os.environ.get('Server') is not None:
            self.server = True
            #File system, used for reading P drive data on RSConnect Server
            self.fs = SSHFileSystem(
                'whale.novo.dk',
                client_keys=[f'/homedirs/{self.user}/.ssh/id_rsa'])
        else:
            self.server = False
            self.fs = None

        self.access = self.check_access()

        #Get trial config
        self.trial_config = self.get_trial_config()

        #Get blinding of trial
        if not self.test_data:
            self.blinded = self.trial_config['blinded']

        #Manual change to ensure data not updated for one trial (when run locally)
        self.do_not_update = False
        # if self.trial == 'nn7769-4513mad':
        #     self.do_not_update = True

        #dm file contains information on each subject in trial
        self.dm = self.get_dm_data()

        #subject_num is dict of integers associated with each USUBJID in dm, used for visualisations
        self.subject_num, self.subjid_dict = self.get_subject_num()

        #subject num dict for blinded trials, used for bleed and med visualisation
        self.subject_num_fake = None

        #Initiate all datasets
        self.bleeds = None
        self.meds = None
        self.dose = None
    
    def check_access(self):
        """Checks whether user has access to this data on the P drive."""
        #Checking access when run on server (note that when run locally, after the app has saved a copy to the 
        # local repo, this will still run as if it were connecting to the P drive)
        if self.server and not self.test_data:
            path = f'/projstat/{self.project}/{self.trial}/current/dm/data/sdtm/'
            print('Checking access to the P drive....')
            try:
                details = self.fs.info(path)
                print('Access granted!')
                return True
            except FileNotFoundError:
                print('Error: No data access.')
                return False
        
        #Checking access when run locally
        if not self.server and not self.test_data:
            if platform.system() == 'Linux':
                path = f'/mnt/projstat/{self.project}/{self.trial}/current/dm/data/sdtm/'
            elif platform.system() == 'Windows':
                path = f'P:\\{self.project}\\{self.trial}\\current\\dm\\data\\sdtm\\'
            return os.path.exists(path)


    def get_trial_config(self):

        """Loads in trial config dictionary."""

        if self.test_data:
            return self.trial_config

        if self.server:
            path = f'/projstat/general/toolpool/haemophiliatool/trials.json'
            with self.fs.open(path) as stream:
                trial_dict = json.load(stream)[self.trial]
        #local
        else:
            if platform.system() == 'Linux':
                path = f'/mnt/projstat/general/toolpool/haemophiliatool/trials.json'
            elif platform.system() == 'Windows':
                path = f'P:\\general\\toolpool\\haemophiliatool\\trials.json'
            with open(path, 'r') as f:
                trial_dict = json.load(f)[self.trial]

        self.trial_config = trial_dict

        return self.trial_config

    def get_dm_data(self):
        """Imports dm domain.

        If running locally (for development purposes), a copy of this table will be saved locally, 
        for faster subsequent processing times.        
        """
        #Test data has no dm domain
        if self.test_data is True:
            self.dm = None
        
        else:
            #if running on server, collect dm domain from whale 
            if self.server is True:
                self.dm = get_sdtm_data(self.fs, self.trial, 'dm', columns=DM_COLS, sortby=['SUBJID'])
            
            #If running locally, check to see if dm file loaded in today, if not load in from P drive
            else:
                dmfilepath = f'./data/sdtm/{self.trial}/{self.trial}_dm.csv'
                if (os.path.isfile(dmfilepath) 
                    and ((datetime.fromtimestamp(os.path.getmtime(dmfilepath)).strftime('%Y-%m-%d') == date.today().strftime('%Y-%m-%d')) or self.do_not_update)):
                    self.dm = pd.read_csv(dmfilepath)
                else:
                    self.dm = get_sdtm_data(self.fs, self.trial, 'dm', columns=DM_COLS, sortby=['SUBJID'])
                    #Save file locally for quicker udata access during development
                    data_directory = f'./data/sdtm/{self.trial}/'
                    if os.path.exists(data_directory) is False:
                        os.makedirs(data_directory)
                    self.dm.to_csv(dmfilepath, index=False)
        
        return self.dm


    def get_subject_num(self) -> dict:
        """Assigns integer value to each SUBJID/USUBJID for use in visualisations."""

        if self.test_data is True:
            with open('./fake_data/NN1234-5678/NN1234-5678_subject_num.pkl', 'rb') as file:
                self.subject_num = pickle.load(file)
                self.subjid_dict = None
        
        else:
            dm = self.dm.sort_values(by='SUBJID', ascending=False)
            n = 1
            subject_num = {}
            subjid_dict = {}
            for subject in dm['USUBJID'].unique():
                subjid = dm.loc[dm['USUBJID']==subject, 'SUBJID'].values[0]
                subjid = str(subjid)
                subject = str(subject)
                subject_num[subject] = n
                subjid_dict[subjid] = n
                n+=1
            self.dm['SUBJECT_NUM'] = self.dm['USUBJID'].map(subject_num)           
            self.subject_num = subject_num
            self.subjid_dict = subjid_dict

        return self.subject_num, self.subjid_dict
    
    def load_bleed_med_data(self):
        """Loads in bleeds and meds data from the DataCategory class below."""

        print('Preparing to load data.')

        #If running test data
        if self.test_data:
            print('Loading test data.')
            self.bleeds = pd.read_csv('./fake_data/NN1234-5678/NN1234-5678_bleeds.csv', parse_dates=['BLEED_START_DATE', 'BLEED_STOP_DATE'])
            self.meds = pd.read_csv('./fake_data/NN1234-5678/NN1234-5678_meds.csv', parse_dates=['HAEM_MED_DATE'])

        #For all real data
        else:
            #If running on server:
            if self.server:
                print('Application is running on the server.')
                BleedCategory = DataCategory(self.fs, self.trial, self.trial_config, 'bleeds', self.subject_num, blinded=self.blinded)
                self.bleeds = BleedCategory.data

                #If trial is blinded, using subject_num from bleed data i.e. containing fake SUBJIDs
                if self.blinded:
                    print('Trial is blinded... Creating fake subject num dict...')
                    self.subject_num_fake = BleedCategory.fake_subject_num
                    self.meds = DataCategory(self.fs, self.trial, self.trial_config, 'meds', self.subject_num_fake, blinded=self.blinded).data
                else:
                    print('Trial is not blinded.')
                    self.meds = DataCategory(self.fs, self.trial, self.trial_config, 'meds', self.subject_num, blinded=self.blinded).data
            
            #If running locally:
            else:
                print('Application is running locally.')
                bleeds_file = f'./data/sdtm/{self.trial}/{self.trial}_bleeds.csv'
                if os.path.isfile(bleeds_file) and ((datetime.fromtimestamp(os.path.getmtime(bleeds_file)).strftime('%Y-%m-%d') == date.today().strftime('%Y-%m-%d')) or self.do_not_update is True):
                    print('Retrieving bleeds file from local repository.')
                    self.bleeds = pd.read_csv(bleeds_file, parse_dates=['BLEED_START_DATE', 'BLEED_STOP_DATE'])
                    if self.blinded:
                        print('Trial is blinded... Collecting fake subject num dict...')
                        with open(f'./data/sdtm/{self.trial}/{self.trial}_fake_subject_num.json', 'r', encoding='utf-8') as f:
                            self.subject_num_fake = json.load(f)


                else:
                    BleedCategory = DataCategory(self.fs, self.trial, self.trial_config, 'bleeds', self.subject_num, blinded=self.blinded)
                    self.bleeds = BleedCategory.data
                    if self.blinded:
                        print('Trial is blinded... Creating fake subject num dict...')
                        self.subject_num_fake = BleedCategory.fake_subject_num

                    #Save bleed data and fake subject_num dict locally
                    self.save_data_locally(self.bleeds, 'bleeds')
                    with open(f'./data/sdtm/{self.trial}/{self.trial}_fake_subject_num.json', 'w', encoding='utf-8') as f:
                            json.dump(self.subject_num_fake, f)


                
                meds_file = f'./data/sdtm/{self.trial}/{self.trial}_meds.csv'
                if os.path.isfile(meds_file) and ((datetime.fromtimestamp(os.path.getmtime(meds_file)).strftime('%Y-%m-%d') == date.today().strftime('%Y-%m-%d')) or self.do_not_update is True):
                    print('Retrieving meds file from local repository.')
                    self.meds = pd.read_csv(meds_file, parse_dates=['HAEM_MED_DATE'])

                else:
                    if self.blinded is True:
                        self.meds = DataCategory(self.fs, self.trial, self.trial_config, 'meds', self.subject_num_fake, blinded=self.blinded).data
                    else:
                        self.meds = DataCategory(self.fs, self.trial, self.trial_config, 'meds', self.subject_num, blinded=self.blinded).data
                    #Save bleed data and fake subject_num dict locally
                    self.save_data_locally(self.meds, 'meds')


        return self.bleeds, self.meds, self.subject_num_fake
    
    def get_bleed_med_data(self, 
                           bleed_missing_cols: list = ['BLEED_START_DATE', 'BLEED_STOP_DATE', 'BLEED_LOCATION', 'BLEED_SEVERITY'], 
                           bleed_duplicate_cols: list = ['USUBJID', 'BLEED_START_DATE', 'BLEED_LOCATION', 'BODY_PART', 'JOINT_LOCATION', 'LATERAL_POSITION'],
                           med_missing_cols: list = ['HAEM_MED_DATE', 'HAEM_MED_DOSE', 'HAEM_MED_TRT_TYPE'],
                           med_duplicate_cols: list = ['USUBJID', 'HAEM_MED_DATE']):
        """Specifies which data error checks to run on the datasets."""

        #Load in data
        self.bleeds, self.meds, self.subject_num_fake = self.load_bleed_med_data()

        #Define combined checks
        self.bleeds, self.meds = trt_N_Y(self.bleeds, self.meds)

        #Define all checks for bleed data
        self.bleeds = get_missing_data(self.bleeds, columns=bleed_missing_cols)
        self.bleeds = get_duplicates(self.bleeds, columns=bleed_duplicate_cols)
        self.bleeds = check_bleed_locations(self.bleeds)
        self.bleeds = get_long_bleeds(self.bleeds)


        #Define all checks for med data
        self.meds = get_missing_data(self.meds, columns=med_missing_cols)
        self.meds = get_duplicates(self.meds, columns=med_duplicate_cols)
        self.meds = meds_outside_bleeding_episodes(self.bleeds, self.meds)

        self.bleeds = self.get_error_count(self.bleeds)
        self.meds = self.get_error_count(self.meds)


        #Merge with dm data
        if self.blinded is False and self.test_data is False:
            self.bleeds = self.bleeds.merge(self.dm, on=['STUDYID', 'USUBJID', 'SUBJECT_NUM'], how='left')
            self.meds = self.meds.merge(self.dm, on=['STUDYID', 'USUBJID', 'SUBJECT_NUM'], how='left')

        return self.bleeds, self.meds, self.subject_num_fake
    

    def get_error_count(self, df, error_cols: list = ERROR_COLS):
        """Counts the number of errors in a row of a dataframe.
        
        Keyword arguments:
        error_cols -- list of columns to be taken into account. should include all columns containing Y/N for checks.
        """

        dff = df.filter(error_cols)
        df['ERROR_COUNT'] = (dff == 'Y').T.sum()
        return df
        

    def get_dose(self, 
                 missing_dose_cols: list = ['STOP_DATE_TIME', 'DOSE'], 
                 duplicate_dose_cols: list = ['USUBJID', 'STOP_DATE_TIME', 'STUDY_DAY_END'],
                 days_missed: int = 7):

        """Imports dose data using DataCategory class below. Also specifies dose checks."""

        if self.test_data is True:
            self.dose = pd.read_csv('./fake_data/NN1234-5678/NN1234-5678_dose.csv', parse_dates=['START_DATE_TIME', 'STOP_DATE_TIME'])
            self.dose['USUBJID'] = self.dose['USUBJID'].astype(str)
    
        else:

            if self.server is True:
                self.dose = DataCategory(self.fs, self.trial, self.trial_config, 'dose', self.subject_num, blinded=self.blinded).data

            #If running locally, check if dose data loaded today, if not load from P drive
            else:
                filepath = f'./data/sdtm/{self.trial}/{self.trial}_dose.csv'
                if os.path.exists(filepath) and self.do_not_update is False and datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d') == date.today().strftime('%Y-%m-%d'):
                    self.dose = pd.read_csv(filepath, parse_dates=['START_DATE_TIME', 'STOP_DATE_TIME'])
                else:
                    self.dose = DataCategory(self.fs, self.trial, self.trial_config, 'dose', self.subject_num, blinded=self.blinded).data
                    self.save_data_locally(self.dose, 'dose')

        #Define dose checks
        print('Running dose checks...')
        self.dose = get_missing_data(self.dose, columns=missing_dose_cols)
        self.dose = get_duplicates(self.dose, columns=duplicate_dose_cols)
        self.dose = get_missed_doses(self.dose, gap=days_missed)

        print('Dose checks completed.')
        
        return self.dose
    

    def save_data_locally(self, data, category):
        """Saves dataframes locally as .csv files. Only to be used when running locally."""
        #when run locally, save data in local data directory
        if self.server is False:
            data_directory = f'./data/sdtm/{self.trial}/'
            if os.path.exists(data_directory) is False:
                os.makedirs(data_directory)
            data.to_csv(f'./data/sdtm/{self.trial}/{self.trial}_{category}.csv', index=False)
            print(f'Saved {category} locally.')
        else:
            print('Cannot save file. App is running on the server.')

    def get_error_overview(self, df: pd.DataFrame, columns: list) -> dict:
        """Counts number of errors in each error column, and returns dict with number of errors per column, 
        and total number of records in table."""

        counts = []
        for col in columns:
            #count the number of errors per record (by the number of checks marked as Y)
            if 'Y' in df[col].values:
                count = df[col].value_counts()['Y']
            else:
                count = 0
            counts.append(count)

        #get the total number of records in dataset
        total_records = df.shape[0]

        overview_data = {'columns':columns, 'counts':counts, 'records':total_records}

        return overview_data


class DataCategory():
    """Imports pre-specified domains using SDTMDataDomain. If multiple for the category, will merge the two and create final dataset.
    """

    category_info = CATEGORY_INFO
    categories = CATEGORIES

    def __init__(self, fs, trial: str, trial_config: dict, category: str, subject_num: dict = None, blinded: bool = True):
        self.fs = fs
        self.trial = trial
        self.category = category
        self.subject_num = subject_num
        self.blinded = blinded

        #Trial configuration from trials.json
        self.sdtm_domain_dict = trial_config['data']

        self.sdtm_domain_rules = None
        if 'rules' in trial_config:
            self.sdtm_domain_rules = trial_config['rules']

        #Specific domain information derived from constants.py and trials.json
        self.sdtm_domain_list = None
        self.sdtm_domain = None
        self.sdtm_domain_supp = None
        self.sdtm_cols = None
        self.sdtm_datecols = None 
        self.color = self.category_info[self.category]['color']
        self.errors = None
        self.mergekey = None

        #Main function to get data for the category
        self.data = self.get_data()

        self.fake_subject_num = self.get_fake_subject_num()

        #Main function used to call all functions in class
    def get_data(self) -> pd.DataFrame:
        """Gets data from SDTMDataDomain and merges multiple domains if specified for that category.
        
        SDTM domains may vary from trial to trial for the same data, so these domains are specified for 
        each trial in trials.json
        """

        #Gets SDTM domains for the data category
        self.get_sdtm_domains()

        #Gets data from SDTMDataDomain class
        self.data = SDTMDataDomain(self.fs, self.trial, self.sdtm_domain, self.sdtm_domain_rules).sdtm_data

        #If more than one domain, merges the domains to create one dataset
        if len(self.sdtm_domain_list) == 2:
            print(f'Getting {self.sdtm_domain_supp} data...')
            self.supp_data = SDTMDataDomain(self.fs, self.trial, self.sdtm_domain_supp).sdtm_data
            self.data = self.data.merge(self.supp_data, how='left', on=self.mergekey)

        #Adds colors and subject_num to dataset
        self.add_colors()

        return self.data

    def get_sdtm_domains(self) -> str:
        """Gets the sdtm domains for the data category as specified in trials.json"""
        #get list of domains for this trial and category 
        self.sdtm_domain_list = self.sdtm_domain_dict[self.category]['domains']

        #get mergekey in case of multiple domains
        self.mergekey = self.sdtm_domain_dict[self.category]['mergekey']

        #get main sdtm domain
        self.sdtm_domain = self.sdtm_domain_list[0]

        #get supplementary sdtm domain if applicable
        if len(self.sdtm_domain_list) == 2:
            self.sdtm_domain_supp = self.sdtm_domain_list[1]

    
    def add_colors(self) -> pd.DataFrame:
        """Adds colours and also subject ID. 
        
        For blinded trials for meds and bleeds, will add fake subject ID so meds and bleeds will match, but doses will not.
        """
        self.data['USUBJID'] = self.data['USUBJID'].astype(str)

        #Maps USUBJID to SUBJECT_NUM or fake SUBJECT_NUM if blinded. Fake subject num for meds is handled in Trial class.
        if self.category != 'bleeds' or self.blinded is False:
            if self.subject_num is not None:
                self.data['SUBJECT_NUM'] = self.data['USUBJID'].map(self.subject_num)
        elif self.category == 'bleeds' and self.blinded is True:
            fake_subject_num_dict = self.get_fake_subject_num()
            self.data['SUBJECT_NUM'] = self.data['USUBJID'].map(fake_subject_num_dict)
        
        #Populates color column; typically the same for a whole category but gets changed in callbacks
        if self.color is not None:
            self.data['COLOR'] = self.color



    def get_fake_subject_num(self) -> dict:
        """Creates dict assigning fake subjid to integer, for blinded data."""
        #sort dataframe by USUBJID
        data = self.data.sort_values(by='USUBJID', ascending=False)

        #assign integer to every unique USUBJID
        n = 1
        subject_num = {}
        for subject in data['USUBJID'].unique():
            subject_num[str(subject)] = n
            n+=1

        self.fake_subject_num = subject_num

        return self.fake_subject_num


    



#Contains data and functions regarding the category of the data e.g. bleeds, dose, meds, med_hist
class SDTMDataDomain():

    """Loads in data from SDTM domains.
    
    For supplementary domains suppce and faxb, extra manipulation is carried out to change
    the layout of the data.
    """

    def __init__(self, fs, trial: str, domain: str, rules: dict = None):
        self.fs = fs
        self.trial = trial
        self.sdtm_domain = domain  

        #Dictionary of data filters for the main sdtm domains
        self.sdtm_domain_rules = rules

        #Defaults for every sdtm domain (if not supplied in rules)
        self.sdtm_domain_info = SDTM_DOMAIN_INFO[self.sdtm_domain]

        self.sdtm_data = self.get_data()


    def get_data(self) -> pd.DataFrame:
        """Main function in SDTMDataDomain used to import and manipulate SDTM data."""

        #Import SDTM data from whale drive
        self.get_sdtm_data()

        #Apply filter on data if specified for that domain (in constants.py)
        self.select_data()

        #Manipulate supplementary data
        if self.sdtm_domain == 'faxb':
            self.faxb_manipulation()
        elif self.sdtm_domain == 'suppce':
            self.suppce_manipulation()

        #Rename columns as per constants.py
        self.rename_cols()

        return self.sdtm_data

    def get_sdtm_data(self) -> pd.DataFrame:
        """Gets sdtm data from P drive and selects only required columns and convert date columns to datetime"""
        project = self.trial.split('-')[0]
        sdtm_cols = self.sdtm_domain_info['columns']
        sdtm_datecols = self.sdtm_domain_info['datecolumns']

        #if running locally
        if self.fs is None:

            if platform.system() == 'Linux':
                sdtm_file = f'/mnt/projstat/{project}/{self.trial}/current/dm/data/sdtm/{self.sdtm_domain}.sas7bdat'
            elif platform.system() == 'Windows':
                sdtm_file = f'P:\\{project}\\{self.trial}\\current\\dm\\data\\sdtm\\{self.sdtm_domain}.sas7bdat'

            print('File path: ', sdtm_file)    
        
            df = SAS7BDAT(sdtm_file).to_data_frame()
        
        #if running on server
        else:

            path = f'/projstat/{project}/{self.trial}/current/dm/data/sdtm/{self.sdtm_domain}.sas7bdat'

            with self.fs.open(path) as stream:
                df = pd.read_sas(io.BytesIO(stream.read()), format='sas7bdat', encoding='iso-8859-1')

        
        if sdtm_cols is not None:
            df = df.reindex(columns=sdtm_cols)
        if sdtm_datecols is not None:
            for col in sdtm_datecols:
                df[col] = pd.to_datetime(df[col], format='%Y-%m-%dT%H:%M')
        self.sdtm_data = df

    def select_data(self) -> pd.DataFrame:
        """Selects subset of data based on filter.
        
        Used for datasets where the SDTM domain does not purely contain the required data.
        """

        #if custom filters have been defined in trials.json then use custom rules, if not use default
        main_domains = ['xb', 'ce', 'cm', 'ec']
        if self.sdtm_domain in main_domains and self.sdtm_domain_rules is not None:
            rules = self.sdtm_domain_rules[self.sdtm_domain]
        else:
            rules = self.sdtm_domain_info['default_rules']

        #Goes through list of rules and filters the data one by one
        for rule in rules:
            filtercolumn = rule['filtercolumn']
            filtertext = rule['filter']
            if type(filtertext) == str:
                filtertext = [filtertext]
            filtertype = rule['filtertype']
            if filtercolumn is not None and filtertext is not None:
                if filtertype == '=':
                    self.sdtm_data = self.sdtm_data.loc[self.sdtm_data[filtercolumn].isin(filtertext)]
                elif filtertype == 'not contain': 
                    self.sdtm_data = self.sdtm_data.loc[~self.sdtm_data[filtercolumn].isin(rule)]
            else:
                pass


    def faxb_manipulation(self) -> pd.DataFrame:
        """Manipulates faxb data to put into usable format.
        
        Essentially pivots out table based on rules specified below to change the dimensions of the data.
        """
        faxb = self.sdtm_data
        JOINTS = ['KNEE', 'ANKLE', 'WRIST', 'FINGERS', 'ELBOW', 'SHOULDER', 'HIP', 'TOES', 'JAW']
        BODYPART = ['ARM', 'LEG', 'HAND', 'BUTTOCKS', 'HEAD/NECK', 'CHEST', 'BACK', 'STOMACH', 'FOOT']
        TESTCDS = ['XBLOCSPC', 'XBCAUS', 'XBTRTYN']
        faxb = faxb.loc[(faxb['FAOBJ']=='BLEEDING EPISODES') & (faxb['FACAT']=='BLEEDING')].drop(columns=['FAOBJ', 'FACAT'])
        faxb = faxb.loc[faxb['FATESTCD'].isin(TESTCDS)]
        faxb['BODY_PART'] = np.where(faxb['FATESTCD']=='XBLOCSPC', faxb['FAORRES'], None)
        faxb['JOINT_LOCATION'] = np.where(faxb['FATESTCD']=='XBLOCSPC', faxb['FAORRES'], None)
        faxb['BODY_PART'] = np.where(faxb['BODY_PART'].isin(BODYPART), faxb['BODY_PART'], None)
        faxb['JOINT_LOCATION'] = np.where(faxb['JOINT_LOCATION'].isin(JOINTS), faxb['JOINT_LOCATION'], None)
        faxb['BLEED_CAUSE'] = np.where(faxb['FATESTCD']=='XBCAUS', faxb['FAORRES'], None)
        faxb['TREATYN'] = np.where(faxb['FATESTCD']=='XBTRTYN', faxb['FAORRES'], None)
        faxb = faxb.groupby(by=['STUDYID', 'USUBJID', 'FAREFID']).agg({'BODY_PART':'first', 'JOINT_LOCATION':'first', 'BLEED_CAUSE':'first', 'TREATYN':'first'}).reset_index()
        self.sdtm_data = faxb

    def suppce_manipulation(self) -> pd.DataFrame:
        """Manipulates suppce data to put into usable format.
        
        Essentially pivots out table based on rules specified below to change the dimensions of the data.
        """
        suppce = self.sdtm_data
        SUPPCE_CDS = ['JOINLOC', 'BODYPART', 'BLDCAUSE', 'TREATYN']
        suppce = suppce.loc[suppce['QNAM'].isin(SUPPCE_CDS)]
        suppce['BODY_PART'] = np.where(suppce['QNAM']=='BODYPART', suppce['QVAL'], None)
        suppce['JOINT_LOCATION'] = np.where(suppce['QNAM']=='JOINLOC', suppce['QVAL'], None)
        suppce['TREATYN'] = np.where(suppce['QNAM']=='TREATYN', suppce['QVAL'], None)
        suppce['BLEED_CAUSE'] = np.where(suppce['QNAM']=='BLDCAUSE', suppce['QVAL'], None)
        suppce = suppce.groupby(by=['STUDYID', 'USUBJID', 'IDVARVAL']).agg({'BODY_PART':'first', 'JOINT_LOCATION':'first', 'BLEED_CAUSE':'first', 'TREATYN':'first'}).reset_index()
        suppce = suppce.rename(columns={'IDVARVAL':'BLEED_ID'})
        self.sdtm_data = suppce

    def rename_cols(self) -> pd.DataFrame:
        """Renames columns to set of standard columns defined in src/data_import/constants.py"""
        rename_dict = self.sdtm_domain_info['rename']
        if rename_dict is not None:
            self.sdtm_data = self.sdtm_data.rename(columns=rename_dict)
        else:
            pass


    



if __name__ == '__main__':

    Trial_4307 = Trial('nn7415-4311', 'isgr')
    bleeds, meds, subject_num = Trial_4307.get_bleed_med_data()
    print(bleeds)
    bleeds = Trial_4307.get_error_count(bleeds)





 
    

    

    

