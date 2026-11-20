from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
class Login(BaseModel): email:str; password:str
class TicketCreate(BaseModel): category:str; subject:str=Field(min_length=3,max_length=150); description:str=Field(min_length=10,max_length=5000)
class MessageCreate(BaseModel): body:str=Field(min_length=1,max_length=5000); request_info:bool=False; expected_version:int
class Action(BaseModel): expected_version:int
class Assign(Action): assignee_id:int|None=None
class Priority(Action): priority:str; reason:str=Field(min_length=5,max_length=1000)
class Resolve(Action): note:str|None=None
class Reopen(Action): reason:str=Field(min_length=5,max_length=1000)
class SettingsUpdate(BaseModel): tat_minutes:dict[str,int]; reopen_window_days:int=Field(ge=1); max_reopens:int=Field(ge=1); auto_close_days:int=Field(ge=1)
class UserOut(BaseModel): model_config=ConfigDict(from_attributes=True); id:int; name:str; email:str; role:str
