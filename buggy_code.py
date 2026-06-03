import os

def get_user(user_id):
    # SQL Injection vulnerability
    query = "SELECT * FROM users WHERE id = " + user_id
    return db.execute(query)

def calculate_discount(price, discount):
    # Division by zero risk
    return price / discount

# Hardcoded credentials
DB_PASSWORD = "admin123"
API_SECRET = "sk-prod-hardcoded-key-xyz"
