import pandas as pd
import numpy as np 
import random
import datetime
import calendar
from datetime import date
from database import SessionLocal, engine
import crud, models, schemas
from sqlalchemy.orm import Session

db = SessionLocal()

sales = pd.read_csv("Sales Dataset.csv")
menu = pd.read_csv("Menu.csv")

items = menu['Item'].values.tolist()
costs = menu['Cost'].values.tolist()
item_cost = {items[i]:costs[i] for i in range(len(items))}
pay_meths = ['GPay', 'Paytm', 'Cash', 'PhonePe']
today = date.today()
num_days = calendar.monthrange(today.year, today.month-1)[1]
this_month_dates = [date(today.year, today.month-1, day) for day in range(1, num_days+1)]
# print(item_cost)
try: 
    for idx in sales.index:
        ind = random.randint(0, len(items)-1)
        data_to_insert = models.Gazebo(id=sales['id'][idx], cname=sales['name'][idx], item=items[ind], cost=int(costs[ind]),
                                        pdate=random.choice(this_month_dates), pay_meth=random.choice(pay_meths))
        db.add(data_to_insert)
    
    db.commit()
        
finally: 
    db.close()