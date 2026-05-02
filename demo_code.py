import os

def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    return db.execute(query)

def divide(a, b):
    return a / b

password = "admin123"
api_key = "sk-hardcoded-key"
