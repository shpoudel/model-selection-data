# Data generation for training ML-based topology ranking

This repository contains the Python code to generate data using OpenDSS powerflow solution. Different radial topologies are generated using switching combinations and power flow is sovled for each topology using a load profile. The sensor measurements for each topology is extracted to "outputs" folder.

The IEEE 123-bus is modified as follows:

1. Three new switches are added, and it can be supplied from 3 new substations.
2. SW-8 is made 3-phase for generating more reconfiguration options.
3. Line.L93 is made 3-phase to incorporate change #2. 


## Running the data generator

1. From the command line execute the following commands to clone the repository

    ```console
    user@user> git clone https://github.com/shpoudel/model-selection-data
    user@user> cd model-selection-data
    ```

2. Invoke Python code from data_dss to generate switching combinations and start OpenDSS. 

    ```` console  
   user@user/model-selection-data/> cd data_dss
   user@user/model-selection-data/data_dss> python3 dss_utils.py
    ```` 
   
Different csv files are populated inside the /outputs folder.
