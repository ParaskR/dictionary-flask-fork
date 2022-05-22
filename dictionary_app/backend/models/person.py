from sqlalchemy import Column, Date, ForeignKey, Integer, String, Table
from util.db import Base
from sqlalchemy.orm import relationship


class Person(Base):
    __tablename__ = 'person'
    id = Column(Integer, primary_key=True)
    firstName = Column(String, nullable=False)
    lastName = Column(String, nullable=False)
    dateOfBirth = Column(Date, nullable=True)
    type = Column(String, nullable=False)

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': id
    }


class User(Person):
    __tablename__ = 'user'
    id = Column(Integer, ForeignKey('person.id', ondelete="CASCADE"), primary_key=True)
    username = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)

    __mapper_args__ = {
        'polymorphic_identity': 'user',
    }
