import json
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import Base, Order, OrderStatus, read_data

def add_order(post_url, comments, account_usernames, session_factory):
    session = session_factory()
    for comment, account_username in zip(comments, account_usernames):
        new_order = Order(post_url=post_url, comment=comment, account_username=account_username, status=OrderStatus.PENDING)
        session.add(new_order)
    session.commit()
    session.close()
    print('Orders added successfully')
