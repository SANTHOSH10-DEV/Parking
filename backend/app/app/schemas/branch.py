from pydantic import BaseModel
from enum import Enum


class ListBranch(str, Enum):
    covai = "covai"
    sathy = "sathy"
    mettupalayam = "mettupalayam"
    valparai = "valparai"