import bcrypt
import mysql.connector

def generate_password_hash(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def insert_user(username, password):
    hashed_password = generate_password_hash(password)
    
    conn = mysql.connector.connect(
        host='127.0.0.1',
        user='root',
        password='root',
        database='ocorrencias_db'
    )
    cursor = conn.cursor()
    cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, hashed_password))
    conn.commit()
    cursor.close()
    conn.close()

if __name__ == '__main__':
    username = 'admin'
    password = 'P@ssw0rd'
    insert_user(username, password)
