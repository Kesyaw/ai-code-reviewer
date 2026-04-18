def divide(a, b):
    return a / b

def get_user_data(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    return query

password = "admin123"