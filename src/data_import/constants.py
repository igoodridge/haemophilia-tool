#Constants containing information on the sdtm domains

#Categories
CATEGORIES = ['bleeds', 'dose', 'meds']

### Bleeds ###
 
#CE domain (e.g. Explorer Trials: nn7415)
CE_COLS = ['STUDYID', 'USUBJID', 'CESPID', 'CETERM', 'CECAT', 'CELOC', 'CELAT', 'CESEV', 'CESTDTC', 'CEENDTC', 'CESTDY', 'CEENDY']
CE_DATES = ['CESTDTC', 'CEENDTC']
CE_RENAME_COLS ={'CETERM':'TERM', 'CECAT':'CATEGORY', 'CELOC':'BLEED_LOCATION', 'CELAT':'LATERAL_POSITION', 'CESEV':'BLEED_SEVERITY', 
                  'CESTDTC':'BLEED_START_DATE', 'CEENDTC':'BLEED_STOP_DATE', 'CESTDY':'BLEED_START_DAY', 'CEENDY':'BLEED_END_DAY', 'CESPID':'BLEED_ID'}

#SUPPCE domain
SUPPCE_COLS = ['STUDYID', 'USUBJID', 'IDVARVAL', 'QNAM', 'QVAL']
SUPPCE_RENAME_COLS = {'IDVARVAL':'BLEED_ID'}

#XB domain (e.g. Frontier Trials: nn7769)
XB_COLS = ['STUDYID', 'USUBJID', 'XBREFID', 'XBTERM', 'XBCAT', 'XBLOC', 'XBLAT', 'XBSEV', 'XBSTDTC', 'XBENDTC']
#XBSTDY and XBENDY NULL for at least 4514 and 4516
XB_DATES = ['XBSTDTC', 'XBENDTC']
XB_RENAME_COLS  ={'XBTERM':'TERM', 'XBCAT':'CATEGORY', 'XBLOC':'BLEED_LOCATION', 'XBLAT':'LATERAL_POSITION', 'XBSEV':'BLEED_SEVERITY', 
                  'XBSTDTC':'BLEED_START_DATE', 'XBENDTC':'BLEED_STOP_DATE', 'XBREFID':'BLEED_ID'}

FAXB_COLS = ['STUDYID', 'USUBJID', 'FAREFID', 'FAOBJ', 'FACAT', 'FATESTCD', 'FAORRES']
FAXB_RENAME_COLS = {'FAREFID':'BLEED_ID'}


### PPX Doses ###
EC_COLS = ['STUDYID', 'USUBJID', 'ECTRT', 'ECSCAT', 'ECDOSE', 'ECSTDTC', 'ECENDTC', 'ECSTDY', 'ECENDY']
EC_DATES = ['ECSTDTC', 'ECENDTC']
EC_RENAME_COLS = {'ECTRT':'DRUG', 'ECDOSE':'DOSE', 'ECSTDTC':'START_DATE_TIME', 'ECENDTC':'STOP_DATE_TIME', 'ECSTDY':'STUDY_DAY_START', 'ECENDY':'STUDY_DAY_END'}

### Concomitant medication ###
CM_COLS = ['STUDYID', 'USUBJID', 'CMTRT', 'CMREFID', 'CMSPID', 'CMDECOD', 'CMCAT', 'CMSCAT', 'CMCLAS', 'CMDOSE', 'CMDOSU' , 'CMDOSRGM', 'CMSTDTC', 'CMENDTC', 'CMDOSFRQ']
#start date NULL for some trials; start and end date same for others; take just end date
CM_DATES = ['CMENDTC']
CM_RENAME_COLS = {'CMDOSRGM':'HAEM_MED_TRT_TYPE', 'CMTRT':'HAEM_MED_DRUG', 'CMSCAT':'HAEM_MED_TRT_CATEGORY', 'CMENDTC':'HAEM_MED_DATE', 'CMDOSE':'HAEM_MED_DOSE', 'CMDOSU':'UNITS'}

#Demography

DM_COLS = ['STUDYID', 'USUBJID', 'SUBJID', 'ARMCD', 'COUNTRY']


#specify colors for data categories

CATEGORY_INFO = {'bleeds': {'color':'#EF553B'},
                 'meds': {'color': '#636EFA'},
                 'dose': {'color': '#636EFA'}}

# Key information for each SDTM domain and default data filter rules
SDTM_DOMAIN_INFO = {'ce': {'key': 'USUBJID', 
                           'columns': CE_COLS, 
                           'datecolumns': CE_DATES,
                           'default_rules': [{'filtercolumn':'CECAT', 'filtertype':'=', 'filter':'BLEEDING'}],
                           'rename':CE_RENAME_COLS,
                           },
                    'xb': {'key': 'USUBJID', 
                           'columns': XB_COLS, 
                           'datecolumns': XB_DATES, 
                           'default_rules': [{'filtercolumn':'XBTERM', 'filtertype': '=', 'filter':'BLEEDING EPISODES'}], 
                           'rename':XB_RENAME_COLS,
                           },
                    'cm': {'key': 'USUBJID', 
                            'columns': CM_COLS, 
                            'datecolumns': CM_DATES, 
                            'default_rules': [{
                                   'filtercolumn':'CMCAT', 
                                   'filtertype': '=',
                                   'filter':'HAEMOPHILIA CONCOMITANT MEDICATION'}],
                            'rename':CM_RENAME_COLS,
                            },
                    'ec': {'key': 'USUBJID', 
                        'columns': EC_COLS, 
                        'datecolumns': EC_DATES,
                        'color': None, 
                        'default_rules': [{
                            'filtercolumn':'ECSCAT', 
                            'filtertype': '=',
                            'filter':['EDIARY', 'FIRST DOSE', 'ACTUAL DOSE']}],
                        'rename':EC_RENAME_COLS,
                        },
                    'faxb' : {'key':'USUBJID',
                              'mergekey': ['STUDYID', 'USUBJID', 'BLEED_ID'],
                              'columns': FAXB_COLS,
                              'datecolumns': None,
                              'color': None,
                              'default_rules': [{
                                   'filtercolumn': 'FACAT',
                                   'filtertype':'=',
                                   'filter': 'BLEEDING'}], 
                              'rename': FAXB_RENAME_COLS},
                    'suppce' : {'key':'USUBJID',
                                'mergekey': ['STUDYID', 'USUBJID', 'BLEED_ID'],
                              'columns': SUPPCE_COLS,
                              'datecolumns': None,
                              'color': None,
                              'default_rules' : [{
                                   'filtercolumn': None,
                                   'filtertype': None,
                                   'filter': None}], 
                              'rename': SUPPCE_RENAME_COLS},
                }
    

