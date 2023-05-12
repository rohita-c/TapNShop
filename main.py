import pandas as pd
import random
import datetime
import calendar
from datetime import date
from typing import List
from sqlalchemy.orm import Session 
import crud, models, schemas
from database import SessionLocal, engine   
from fastapi import FastAPI, Request, Depends, Form, Body
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import plotly.graph_objects as go
from sqlalchemy import func, and_

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

payment_methods = ['GPay', 'PayTM', 'Cash', 'Phonepe']
menu = pd.read_csv("Menu.csv")
items = menu['Item'].values.tolist()
costs = menu['Cost'].values.tolist()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally: 
        db.close()

@app.get("/add_purchase")
async def purchase_form(request: Request):

    return templates.TemplateResponse("new_purchase.html", {"request": request, "pay_meth": payment_methods,"menu": {items[i]:costs[i] for i in range(len(items))}})

@app.get("/getPlot/{plot_name}")
async def givePlot(plot_name: str):
    return FileResponse("templates/plots/"+plot_name+".html")

@app.post("/submit_purchase/")
async def submit_purchase(request: Request, db: Session=Depends(get_db), id: str=Form(), cname: str=Form(), sel_items: List[str]=Form(), cost: str=Form(), pay_meth: str=Form()):
    for item in sel_items:
        tmp = item.split(": ")
        newp = models.Gazebo(id=id, cname=cname, item=tmp[0], cost=int(tmp[1]), pdate=date.today(), pay_meth=pay_meth)
        db.add(newp)
        db.commit()
        db.refresh(newp)

    cnames = db.query(models.Gazebo.cname).all()
    ids = db.query(models.Gazebo.id).all()
    items = db.query(models.Gazebo.item).all()
    costs = db.query(models.Gazebo.cost).all()
    pay_meth = db.query(models.Gazebo.pay_meth).all()
    cnames_, ids_, items_, costs_, pay_ = [], [], [], [], []
    for i in range(len(cnames)):
        cnames_.append(cnames[i][0])
        ids_.append(ids[i][0])
        costs_.append(costs[i][0])
        items_.append(items[i][0])
        pay_.append(pay_meth[i][0])

    cnames_.reverse()
    ids_.reverse()
    costs_.reverse()
    items_.reverse()
    pay_.reverse()

    return templates.TemplateResponse("home.html", {"request": request, "cnames": cnames_, "ids": ids_, 
                                        "items": items_, "costs": costs_, "pay_meth": pay_})

@app.get("/download")
async def download(request: Request, db: Session = Depends(get_db)):
    cnames = db.query(models.Gazebo.cname).all()
    ids = db.query(models.Gazebo.id).all()
    items = db.query(models.Gazebo.item).all()
    pdate = db.query(models.Gazebo.pdate).all()
    costs = db.query(models.Gazebo.cost).all()
    pay_meth = db.query(models.Gazebo.pay_meth).all()
    cnames_, ids_, items_, costs_, pay_, pdate_ = [], [], [], [], [], []
    for i in range(len(cnames)):
        cnames_.append(cnames[i][0])
        ids_.append(ids[i][0])
        costs_.append(costs[i][0])
        items_.append(items[i][0])
        pay_.append(pay_meth[i][0])
        pdate_.append(pdate[i][0])
    sales_df = pd.DataFrame(columns=['ID', 'Customer Name', 'Item', 'Cost', 'Purchase Date', 'Payment Method'])
    sales_df['ID'] = ids_
    sales_df['Customer Name'] = cnames_
    sales_df['Item'] = items_
    sales_df['Cost'] = costs_
    sales_df['Payment Method'] = pay_
    sales_df['Purchase Date'] = pdate_
    sales_df.to_csv('Sales.csv', index=False)
    return FileResponse('Sales.csv')

@app.post("/delete_purchase", response_class=JSONResponse)
async def deletepurchase(request: Request, db: Session=Depends(get_db), curr_id: str=Body(), curr_item: str=Body(), curr_cost: str=Body(), curr_pay_meth: str=Body()):
    # print(curr_cost)

    return {"message": "Successfully deleted. Refresh to view changes."}

@app.get("/analyse_sales")
async def analyseSales(request: Request, db: Session=Depends(get_db)):

    #Weekly analysis of sales
    today = date(2023, 3, 25)
    dates_ = [today + datetime.timedelta(days=i) for i in range(0 - today.weekday(), 7 - today.weekday())]
    dates = [i.strftime("%d-%m-%Y") for i in dates_]
    sales_count = [db.query(models.Gazebo).filter(models.Gazebo.pdate==i).count() for i in dates_]
    
    fig = go.Figure([go.Bar(x=dates, y=sales_count)])
    fig.update_layout(title="Weekly sales", xaxis_title="Dates", yaxis_title="Total sales")
    fig.write_html("templates\plots\weekly_sales.html")

    #Revenue of past month
    num_days = calendar.monthrange(today.year, today.month)[1]
    this_month_dates = [date(today.year, today.month, day) for day in range(1, num_days+1)]
    x = [i.strftime("%d-%m-%Y") for i in this_month_dates]
    y = [db.query(models.Gazebo.cost).filter(models.Gazebo.pdate==i).all() for i in this_month_dates]
    y = [[sum(i[0] for i in j)] for j in y]
    y = [i[0] for i in y]
    # print(y)
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=x, y=y, mode='lines+markers'))
    fig1.update_layout(title="Revenue of past month", xaxis_title="Dates", yaxis_title="Sales per day", xaxis = dict(tickmode='array', tickvals=[i for i in range(0, len(x), 7)]))
    fig1.update_xaxes(tickangle=30)
    fig1.write_html('templates\plots\pastmonth_revenue.html')

    #Which product sells how much
    costs_per_item = []
    for item in items:
        tmp = [db.query(models.Gazebo.cost).filter(models.Gazebo.item==item).all()]
        tmp = [[sum(i[0] for i in j) for j in tmp]]
        costs_per_item.append(tmp[0])
    costs_per_item = [i[0] for i in costs_per_item]
    labels = [val for (_, val) in sorted(zip(costs_per_item, items), key=lambda x: x[0], reverse=True)]
    labels = labels[:10]
    costs_per_item = sorted(costs_per_item, reverse=True)[:10]
    # print(costs_per_item)
    # print(labels)
    fig2 = go.Figure(data=[go.Pie(labels=labels, values=costs_per_item, hole=.2)])
    fig2.update_layout(title="Top 10 Products")
    fig2.update_traces(textfont_size=10)
    fig2.write_html('templates\plots\which_prod_howmuch.html')

    #Sales grouped by payment methods
    unique_dates_ = [i[0] for i in db.query(models.Gazebo.pdate).distinct()]
    unique_dates = [i.strftime("%d-%m-%Y") for i in unique_dates_]
    if len(unique_dates) > 31:
        unique_dates = unique_dates[:-31]
        unique_dates_ = unique_dates_[:-31]

    cash_sum, gpay_sum, paytm_sum = 0, 0, 0
    pd1, pd2, pd3 = [], [], []
    # print(unique_dates_)
    for d in unique_dates_:
        # print(d)
        cash_sum = sum([i[0] for i in db.query(models.Gazebo.cost).filter(and_(models.Gazebo.pay_meth=='Cash', models.Gazebo.pdate==d))])
        gpay_sum += sum([i[0] for i in db.query(models.Gazebo.cost).filter(and_(models.Gazebo.pay_meth=='GPay', models.Gazebo.pdate==d))])
        paytm_sum += sum([i[0] for i in db.query(models.Gazebo.cost).filter(and_(models.Gazebo.pay_meth=='PayTM', models.Gazebo.pdate==d))])
        pd1.append(cash_sum)
        pd2.append(gpay_sum)
        pd3.append(paytm_sum)
    
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(x=unique_dates, y=pd1))
    fig3.add_trace(go.Scatter(x=unique_dates, y=pd2))
    fig3.add_trace(go.Scatter(x=unique_dates, y=pd3))
    fig3.update_layout(title="Trend of payment methods", xaxis = dict(tickmode='array', tickvals=[i for i in range(0, len(x), 7)]))
    fig3.update_xaxes(tickangle=30)
    fig3.write_html('templates\plots\salesby_paymeth.html')



    return templates.TemplateResponse("analysis.html", {"request": request})

@app.get("/")
async def homepage(request: Request, db: Session = Depends(get_db)):
    cnames = db.query(models.Gazebo.cname).all()
    ids = db.query(models.Gazebo.id).all()
    items = db.query(models.Gazebo.item).all()
    costs = db.query(models.Gazebo.cost).all()
    pay_meth = db.query(models.Gazebo.pay_meth).all()
    cnames_, ids_, items_, costs_, pay_ = [], [], [], [], []
    for i in range(len(cnames)):
        cnames_.append(cnames[i][0])
        ids_.append(ids[i][0])
        costs_.append(costs[i][0])
        items_.append(items[i][0])
        pay_.append(pay_meth[i][0])
        
    cnames_.reverse()
    ids_.reverse()
    costs_.reverse()
    items_.reverse()
    pay_.reverse()
    return templates.TemplateResponse("home.html", {"request": request, "cnames": cnames_, "ids": ids_, 
                                        "items": items_, "costs": costs_, "pay_meth": pay_})

