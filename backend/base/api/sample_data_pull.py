import numpy as np
import pandas as pd
import snowflake.connector
from ydata_profiling import ProfileReport
from datetime import datetime

connectionstr = snowflake.connector.connect(
    user='PBI_USER',
    password='Admin@123',
    account='vu63469.ap-southeast-1'
    )


datacursor = connectionstr.cursor()
datacursor.execute("select * from AIRBNB.PUBLIC.DIM_CUSTOMERS limit 10")
headercolumn= [col[0] for col in datacursor.description]
rowstofetch  = datacursor.fetchall()

df = pd.DataFrame(rowstofetch, columns=headercolumn)

print(df)


