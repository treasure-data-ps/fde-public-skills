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
table=os.environ['Markov_table']
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




def run_markov_model():
    
    # connect to Treasure Data client
    client = pytd.Client(apikey=td_api_key, endpoint=td_api_server, database=database,retry_post_requests=True)

    # query data from TD table
    res = client.query(f'''select * from {table} ''', engine='presto')
    data=pd.DataFrame(**res)

    # run marketing attribution model
    attributions = MAM(data,
        group_channels=False,
        channels_colname=channel_colname,
        journey_with_conv_colname=conversion_col_name,
        group_channels_by_id_list=group_channels_by_id_list,
        group_timestamp_colname=time_col,
        create_journey_id_based_on_conversion=True)

    attribution_markov = attributions.attribution_markov(transition_to_same_state=False)
    markov_attribution = attribution_markov[1]

    # turn Markov matrix into a dataframe and remove fake initiation step
    markov_df = attribution_markov[2].round(3)
    markov_df.drop(['(inicio)', '(null)'], inplace=True)
    markov_df.drop(['(inicio)', '(null)'], axis=1, inplace=True)
    markov_df['channels'] = markov_df.index

    # create dataframe for Markov removal effect
    markov_removal_effect_df = pd.DataFrame()
    markov_removal_effect_df['channels'] = attribution_markov[3].index
    markov_removal_effect_df['removal_effect'] = attribution_markov[3]['removal_effect'].values

    # merge Markov attribution and removal effect dataframes
    mta_attribution = pd.merge(markov_attribution, markov_removal_effect_df, on='channels', how='left')
    

    if save_tables_in_td.lower()=='yes':
        # write Markov model transition table and attribution table to TD
        print('-----------------------------------------')
        print('Writing Markov Model Transition Table to TD...')
        print('-----------------------------------------')
        client.load_table_from_dataframe(markov_df, 'mta_markov_transition', writer='bulk_import', if_exists='overwrite')
        client.load_table_from_dataframe(mta_attribution.round(3), 'mta_markov_attribution', writer='bulk_import', if_exists='overwrite')


run_markov_model()