from pydantic import BaseModel
import datetime

class GazeboBase(BaseModel):
    id: str

class GazeboCreate(GazeboBase):
    cname: str
    item: str
    cost: str 
    pdate: datetime.date
    pay_meth: str

class Gazebo(GazeboBase):
    cname: str

    class Config:
        orm_mode = True