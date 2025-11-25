from sqlalchemy import Enum


class BlogStatus(str, Enum) :
    DRAFT="draft"