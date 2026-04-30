# Test file dengan beberapa bug sengaja
def get_user(user_id):
    query = "SELECT * FROM users WHERE id = " + user_id
    return db.execute(query)

def calculate(a, b):
    return a / b

api_key = "sk-hardcoded-key-123"
