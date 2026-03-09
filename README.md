# Introduction
HaemophiliaTool is a web application currently published on [RSConnect](https://connect.bifrost-prd.corp.aws.novonordisk.com/content/5b1eb8f9-82d6-453e-952f-66d6c233295e)  used for displaying and checking clinical data from haemophilia trials. This includes bleeding episodes, haemostatic medication and trial drug doses.

**For more information on how to further develop the application, please visit our [wiki page](https://dev.azure.com/novonordiskit/BOS/_wiki/wikis/Biostat%20Open%20Source%20-%20Wiki/91382/HaemophiliaTool).**

_Disclaimer: the app is still under development and has not yet been validated. It has been published to facilitate user testing._


#Repository Structure

------------

    ├── README.md          <- The top-level README for developers using this     
    │                         project.
    ├── run.py             <- script used to run the application
    ├── app.py             <- contains the app instance
    ├── index.py           <- general layout of the application (can be 
    │                         considered the 
    │                         master page)
    ├── pages              <- folder containing the pages of the application
    │   ├── home.py        <- layout for home page - consists of graphs to     
    │   │                     display current status of data
    │   ├── page_1.py      <- layout for bleeds and medication page -     
    │   │                     contains figure showing bleeds and medication 
    │   │                     and bleeds table
    │   └── page_2.py      <- layout for doses page - currently dose table 
    │                         not working, so table is blank
    │
    ├── src                <- Source code for use in this project.
    │   ├── data_import    <- Scripts to download or generate data
    │   │   ├── trial.py        <- imports data from P drive and stores in 
    │   │   │                      trial class. each trial has four 
    │   │   │                      datasets: dm, bleeds, meds and dose
    │   │   ├── utils.py        <- general functions for data import
    │   │   ├── constants.py    <- constants such as column names and 
    │   │   │                      mappings for sdtm domains
    │   │   └── fake_data.py    <- script generates fake data to be     
    │   │                          displayed in the app when no real data is 
    │   │                          being accessed
    │   │
    │   ├── data_checks    <- Scripts to turn raw data into features for 
    │   │   │                 modelling
    │   │   ├── utils.py        <- all functions for checking and     
    │   │   │                       identifying errors in data
    │   │   └── constants.py    <- constants related to checks e.g. lists 
    │   │                           for bleed location checks
    │   │
    │   ├── app_components <- Scripts to create components of the 
    │   │   │                 application such as sidebar, navigation bar, 
    │   │   │                 user information
    │   │   ├── navigation.py         <- code for navigation bar
    │   │   ├── new_trial.py          <- creates form for configuring new 
    │   │   │                            trials
    │   │   ├── configure_data_checks.py  <- creates side pane with options to 
    │   │   │                                change the way the checks work
    │   │   ├── sidebar.py            <- creates main sidebar
    │   │   ├── styling_constants.py  <- constants for sidebar and content 
    │   │   │                            styles
    │   │   └── user_guide.py         <- contains information that is 
    │   │                                displayed to user within the app
    │   │
    │   ├── visualizations  <- Scripts to create the visualisations for the 
    │   │   │                  application
    │   │   ├── bleeds.py             <- creates bleed and haemostatic 
    │   │   │                            medication graph, showing each 
    │   │   │                            individual patient 
    │   │   ├── dose.py               <- creates graph for dose dates per 
    │   │   │                            patient, and dose amount for one 
    │   │   │                            patient at a time
    │   │   └── cleaning_overview.py  <- creates overview visualisations to      
    │   │                                show status of data quality
    │   └── tmp             <- deprecated files used for initial data checks
    ├── .gitignore          <- specifies files/folders to be ignored by git
    └── requirements.txt    <- contains package requirements


Author: ISGR