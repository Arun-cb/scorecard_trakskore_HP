# import numpy as np
import pandas as pd
import snowflake.connector
from ydata_profiling import ProfileReport
from datetime import datetime

connectionstr = snowflake.connector.connect(
    user='REVANRUFUS',
    password='Revan@062797',
    account='vi82049.ap-southeast-1'
    )

datacursor = connectionstr.cursor()

datacursor.execute("select * from smpledb.public.agents")
headercolumn= [col[0] for col in datacursor.description]

rowstofetch  = datacursor.fetchall()

df = pd.DataFrame(rowstofetch, columns=headercolumn)


profileData = ProfileReport(df, title='Snoflake Report')

profileData.to_file("your_report.html")

