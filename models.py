from sqlalchemy import Boolean, Column, Integer, String, Date
from database import Base

class Gazebo(Base):
    __tablename__ = "gazebo"
    id = Column(String(20), primary_key=True)
    cname = Column(String(50))
    item = Column(String(50))
    cost = Column(Integer)
    pdate = Column(Date)
    pay_meth = Column(String(50))