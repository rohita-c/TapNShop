from sqlalchemy.orm import Session
import models, schemas
import datetime
from datetime import date

def get_purchases(db: Session, cname: str):
    return db.query(models.Gazebo).filter(models.Gazebo.cname == cname).all()

def get_last_purchase(db: Session, cname: str):
    return db.query(models.Gazebo).filter(models.Gazebo.cname == cname).first()

def get_purchase_bydate(db: Session, date_inp: date):
    return db.query(models.Gazebo).filter(models.Gazebo.pdate == date_inp).all()

def create_purchase(db: Session, purchase: schemas.GazeboCreate):
    db_purchase = models.Gazebo(id=purchase.id, cname=purchase.cname, item=purchase.item, cost=purchase.cost, pdate=purchase.date, pay_meth=purchase.pay_meth)
    db.add(db_purchase)
    db.commit()
    db.refresh(db_purchase)
    return db_purchase