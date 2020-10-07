from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from authorization.database import Base


class User(Base):
    __tablename__ = 'auth_users'

    id = Column(Integer, primary_key=True)
    username = Column(String(200), nullable=False, unique=False)
    password = Column(String(200), nullable=False)
    date_registration = Column(DateTime, default=datetime.utcnow(), nullable=True)
    token = Column(String(500), nullable=False)

    def __init__(self, username=None, password=None, token=None):
        self.username = username
        self.password = password
        self.token = token

    def __repr__(self):
        return f'<User {self.id}>'
