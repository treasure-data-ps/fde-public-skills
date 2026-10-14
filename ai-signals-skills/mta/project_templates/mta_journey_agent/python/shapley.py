import sys
import os
import pytd
import pandas as pd
import numpy as np
import tdclient

#pip-install marketing_attribution_models
os.system(f"{sys.executable} -m pip install marketing_attribution_models")

from marketing_attribution_models import MAM

save_tables_in_td=os.environ['save_tables_in_td']
td_api_server=os.environ['TD_API_SERVER']
td_api_key=os.environ['TD_API_KEY']
database=os.environ['SINK_DB']
table=os.environ['shapley_table']
user_id_col=os.environ['user_id_col']
time_col=os.environ['time_col'] 
channel_colname=os.environ['channel_colname']
conversion_col_name=os.environ['conversion_col_name']
group_channels_by_id_list=[user_id_col]


assert save_tables_in_td != None, "save_tables_in_td is not set"
assert td_api_server != None, "td_api_server is not set"
assert database != None, "database is not set"
assert td_api_key != None, "td_api_key is not set"
assert table != None, "table is not set"

assert user_id_col != None, "user_id_col is not set"
assert time_col != None, "time_col is not set"
assert channel_colname != None, "channel_colname is not set"
assert conversion_col_name != None, "conversion_col_name is not set"

def run_shapley_model():
    
    # connect to Treasure Data client
    client = pytd.Client(apikey=td_api_key, endpoint=td_api_server, database=database)
    res = client.query( 
        f'''select {user_id_col}, {time_col}, {conversion_col_name}, {channel_colname}  from {table} ''',
            engine='presto')
    data=pd.DataFrame(**res)
    data[conversion_col_name]=data[conversion_col_name].replace({1:True,0:False})
    
    # run marketing attribution model
    attributions = MAM(data,
        group_channels=True,
        channels_colname = channel_colname,
        journey_with_conv_colname= conversion_col_name,
        group_channels_by_id_list=group_channels_by_id_list,
        group_timestamp_colname = time_col,
        create_journey_id_based_on_conversion = True)

    shapely_lookback_window=4
    for day in range(shapely_lookback_window):
        attributions.attribution_shapley(size=day, order=True)[1]

    shap_df=attributions.attribution_all_models().filter(regex=("shap|chan"))

    shap_df=pd.melt(shap_df, ['channels'])
    shap_df['day']=shap_df['variable'].str.extract('(\d+)').astype(int)
    if save_tables_in_td.lower()=='yes':
        # write Markov model transition table and attribution table to TD
        print('-----------------------------------------')
        print('Writing Shapley Model Table to TD...')
        print('-----------------------------------------')
        client.load_table_from_dataframe(shap_df, 'mta_shapley_attribution', writer='bulk_import', if_exists='overwrite')

run_shapley_model()