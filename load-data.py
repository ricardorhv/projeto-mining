import pandas as pd
from sqlalchemy import create_engine

data_url = "./data.xls"

engine = create_engine("postgresql://postgres:root@localhost:5432/project-mining")

df = pd.read_excel(data_url).dropna()
df.to_sql("corn_price", engine, if_exists='replace', index=False)

print("Executed with success")
