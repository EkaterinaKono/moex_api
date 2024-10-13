from pydantic import BaseModel, constr, Field
from datetime import datetime


class SearchData(BaseModel):
    search_security: constr(min_length=1)
    security_code: constr(min_length=1)
    date1: datetime
    date2: datetime
