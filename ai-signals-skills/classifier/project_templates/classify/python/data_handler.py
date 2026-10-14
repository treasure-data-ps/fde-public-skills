import pandas as pd
import pytd
import pytd.pandas_td as td
import logging

logger = logging.getLogger(__name__)


class DataHandler:
    """Handles data loading from and saving to Treasure Data."""

    def __init__(self, apikey, database, endpoint="https://api.treasuredata.com/"):
        self.apikey   = apikey
        self.database = database
        self.endpoint = endpoint

    def read_data(self, src_table, session_id):
        """
        Read raw data from Treasure Data, filtered by session_id.

        session_id is the single run identifier — it's set in the Digdag
        _env block and used consistently for both reading and writing.
        """
        logger.info("Starting data extraction from Treasure Data")

        try:
            con    = td.connect(apikey=self.apikey, endpoint=self.endpoint)
            engine = td.create_engine(f"presto:{self.database}", con=con)
            sql    = f"SELECT * FROM {src_table} WHERE session_id = {session_id}"

            logger.info(f"Executing SQL query: {sql}")
            df = td.read_td_query(sql, engine)

            logger.info(f"Data extracted successfully - Shape: {df.shape}")
            logger.info(f"Columns: {list(df.columns)}")
            logger.info(f"Data types:\n{df.dtypes}")
            logger.info(f"Sample rows:\n{df.head()}")

            if df.empty:
                logger.warning(f"No data found for session_id = '{session_id}'")

            return df

        except Exception as e:
            logger.error(f"Error reading data: {str(e)}")
            raise

    def save_data(self, df, table_name, if_exists='append'):
        """Save DataFrame to Treasure Data."""
        logger.info(f"Saving data to Treasure Data table: {table_name}")

        try:
            client = pytd.Client(
                apikey=self.apikey,
                endpoint=self.endpoint,
                database=self.database,
                default_engine='presto'
            )

            client.load_table_from_dataframe(
                df,
                destination=table_name,
                if_exists=if_exists,
                writer='bulk_import'
            )

            logger.info(f"Data successfully saved to {table_name}")

        except Exception as e:
            logger.error(f"Error saving data to {table_name}: {str(e)}")
            raise