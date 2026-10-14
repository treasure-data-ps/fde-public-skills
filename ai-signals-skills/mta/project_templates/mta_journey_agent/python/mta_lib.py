import sys
import os
import pytd
import pandas as pd
import numpy as np
import tdclient


#pip-install marketing_attribution_models
os.system(f"{sys.executable} -m pip install td-ml-mta")

save_tables_in_td=os.environ['save_tables_in_td']
td_api_server=os.environ['TD_API_SERVER']
td_api_key=os.environ['TD_API_KEY']
database=os.environ['SINK_DB']
shapley_table='mta_shapely_input_table'
user_id_col=os.environ['user_id_col']
time_col=os.environ['time_col'] 
channel_colname=os.environ['channel_colname']
conversion_col_name=os.environ['conversion_col_name']
group_channels_by_id_list=[user_id_col]

from td_ml_mta import *

  
  