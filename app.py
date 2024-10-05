from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from mysql.connector import Error
import bcrypt
import base64
from io import BytesIO
import matplotlib.pyplot as plt
import matplotlib
from datetime import datetime

matplotlib.use('Agg')

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def init_db():
    conn = None
    try:
        conn = mysql.connector.connect(
            host='127.0.0.1',
            user='root',
            password='root',
            database='ocorrencias_db'
        )
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(255) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ocorrencias (
                id INT AUTO_INCREMENT PRIMARY KEY,
                titulo VARCHAR(255) NOT NULL,
                descricao TEXT NOT NULL,
                setor VARCHAR(255) NOT NULL,
                local VARCHAR(255) NOT NULL,
                gravidade ENUM('baixa', 'média', 'grave') NOT NULL,
                observacoes TEXT,
                data DATE NOT NULL
            )
        ''')
        conn.commit()
    except Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form['username']
    password = request.form['password']

    conn = None
    try:
        conn = mysql.connector.connect(
            host='127.0.0.1',
            user='root',
            password='P@ssw0rd',
            database='ocorrencias_db'
        )
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()

        if user and bcrypt.checkpw(password.encode('utf-8'), user[0].encode('utf-8')):
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return redirect(url_for('login'))
    except Error as e:
        print(f"Erro ao conectar ao MySQL: {e}")
        return redirect(url_for('login'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/index')
def index():
    if 'username' in session:
        return render_template('index.html')
    return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/register', methods=['POST'])
def register():
    if 'username' not in session:
        return redirect(url_for('login'))

    titulo = request.form['titulo']
    descricao = request.form['descricao']
    setor = request.form['setor']
    local = request.form['local']
    gravidade = request.form['gravidade']
    observacoes = request.form['observacoes']
    data = request.form['data']

    conn = None
    try:
        conn = mysql.connector.connect(
            host='127.0.0.1',
            user='root',
            password='P@ssw0rd',
            database='ocorrencias_db'
        )
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO ocorrencias (titulo, descricao, setor, local, gravidade, observacoes, data)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', (titulo, descricao, setor, local, gravidade, observacoes, data))
        conn.commit()
    except Error as e:
        print(f"Erro ao registrar ocorrência: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

    return redirect(url_for('index'))

@app.route('/ocorrencias')
def ocorrencias():
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = None
    try:
        conn = mysql.connector.connect(
            host='127.0.0.1',
            user='root',
            password='P@ssw0rd',
            database='ocorrencias_db'
        )
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM ocorrencias')
        ocorrencias = cursor.fetchall()
        
    except Error as e:
        print(f"Erro ao buscar ocorrências: {e}")
        ocorrencias = []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

    return render_template('ocorrencias.html', ocorrencias=ocorrencias)

@app.route('/delete/<int:id>')
def delete(id):
    if 'username' not in session:
        return redirect(url_for('login'))

    conn = None
    try:
        conn = mysql.connector.connect(
            host='127.0.0.1',
            user='root',
            password='P@ssw0rd',
            database='ocorrencias_db'
        )
        cursor = conn.cursor()
        cursor.execute('DELETE FROM ocorrencias WHERE id = %s', (id,))
        conn.commit()
    except Error as e:
        print(f"Erro ao excluir ocorrência: {e}")
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
    return redirect(url_for('ocorrencias'))

@app.route('/search', methods=['GET'])
def search():
    if 'username' not in session:
        return redirect(url_for('login'))

    search_date = request.args.get('date')

    conn = None
    try:
        conn = mysql.connector.connect(
            host='127.0.0.1',
            user='root',
            password='P@ssw0rd',
            database='ocorrencias_db'
        )
        cursor = conn.cursor()

        if search_date:
            cursor.execute('SELECT * FROM ocorrencias WHERE DATE(data) = %s', (search_date,))
        else:
            cursor.execute('SELECT * FROM ocorrencias')

        ocorrencias = cursor.fetchall()
    except Error as e:
        print(f"Erro ao buscar ocorrências: {e}")
        ocorrencias = []
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

    return render_template('ocorrencias.html', ocorrencias=ocorrencias)

@app.route('/charts')
def charts():
    if 'username' not in session:
        return redirect(url_for('login'))

    setor_filtro = request.args.get('setor', '')
    data_inicio = request.args.get('data_inicio', '')
    data_fim = request.args.get('data_fim', '')
    gravidade_filtro = request.args.get('gravidade', '')
    titulo_filtro = request.args.get('titulo', '')

    conn = None
    try:
        conn = mysql.connector.connect(
            host='127.0.0.1',
            user='root',
            password='P@ssw0rd',
            database='ocorrencias_db'
        )
        cursor = conn.cursor()

        # Gráfico de setores
        query = 'SELECT setor, COUNT(*) FROM ocorrencias WHERE 1=1'
        params = []

        if setor_filtro:
            query += ' AND setor = %s'
            params.append(setor_filtro)

        if data_inicio:
            query += ' AND data >= %s'
            params.append(data_inicio)

        if data_fim:
            query += ' AND data <= %s'
            params.append(data_fim)

        if gravidade_filtro:
            query += ' AND gravidade = %s'
            params.append(gravidade_filtro)

        if titulo_filtro:
            query += ' AND titulo = %s'
            params.append(titulo_filtro)

        query += ' GROUP BY setor ORDER BY COUNT(*) DESC LIMIT 10'
        cursor.execute(query, params)
        setores = cursor.fetchall()
        setores_labels = [setor[0] for setor in setores]
        setores_values = [setor[1] for setor in setores]

        fig, ax = plt.subplots(figsize=(14, 8))
        ax.bar(setores_labels, setores_values, color='#4c7aaf')
        ax.set_xlabel('Setor', fontsize=14)
        ax.set_ylabel('Quantidade', fontsize=14)
        ax.set_title('Top 10 Setores com Mais Chamados', fontsize=16)
        ax.tick_params(axis='both', which='major', labelsize=12)
        ax.set_xticklabels(setores_labels, rotation=45, ha='right')

        for i, v in enumerate(setores_values):
            ax.text(i, v + 0.5, str(v), ha='center', va='bottom', fontsize=10)

        fig.tight_layout(rect=[0, 0.1, 1, 1])
        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        setores_graph = base64.b64encode(img.getvalue()).decode('utf-8')
        plt.close()

        # Gráfico de meses
        query = 'SELECT MONTH(data), COUNT(*) FROM ocorrencias WHERE 1=1'
        params = []

        if setor_filtro:
            query += ' AND setor = %s'
            params.append(setor_filtro)

        if data_inicio:
            query += ' AND data >= %s'
            params.append(data_inicio)

        if data_fim:
            query += ' AND data <= %s'
            params.append(data_fim)

        if gravidade_filtro:
            query += ' AND gravidade = %s'
            params.append(gravidade_filtro)

        if titulo_filtro:
            query += ' AND titulo = %s'
            params.append(titulo_filtro)

        query += ' GROUP BY MONTH(data)'
        cursor.execute(query, params)
        meses = cursor.fetchall()
        meses_labels = [calendar.month_name[mes[0]] for mes in meses]
        meses_values = [mes[1] for mes in meses]

        fig, ax = plt.subplots(figsize=(14, 8))
        ax.plot(meses_labels, meses_values, marker='o', color='#4c7aaf')
        ax.set_xlabel('Mês', fontsize=14)
        ax.set_ylabel('Quantidade', fontsize=14)
        ax.set_title('Quantidade de Chamados por Mês', fontsize=16)
        ax.tick_params(axis='both', which='major', labelsize=12)

        for i, v in enumerate(meses_values):
            ax.text(i, v + 0.5, str(v), ha='center', va='bottom', fontsize=10)

        fig.tight_layout()
        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        meses_graph = base64.b64encode(img.getvalue()).decode('utf-8')
        plt.close()

        # Gráfico de títulos
        query = 'SELECT titulo, COUNT(*) FROM ocorrencias WHERE 1=1'
        params = []

        if setor_filtro:
            query += ' AND setor = %s'
            params.append(setor_filtro)

        if data_inicio:
            query += ' AND data >= %s'
            params.append(data_inicio)

        if data_fim:
            query += ' AND data <= %s'
            params.append(data_fim)

        if gravidade_filtro:
            query += ' AND gravidade = %s'
            params.append(gravidade_filtro)

        if titulo_filtro:
            query += ' AND titulo = %s'
            params.append(titulo_filtro)

        query += ' GROUP BY titulo ORDER BY COUNT(*) DESC LIMIT 10'
        cursor.execute(query, params)
        titulos = cursor.fetchall()
        titulos_labels = [titulo[0] for titulo in titulos]
        titulos_values = [titulo[1] for titulo in titulos]

        fig, ax = plt.subplots(figsize=(14, 8))
        ax.bar(titulos_labels, titulos_values, color='#4c7aaf')
        ax.set_xlabel('Título', fontsize=14)
        ax.set_ylabel('Quantidade', fontsize=14)
        ax.set_title('Top 10 Títulos de Chamados', fontsize=16)
        ax.tick_params(axis='both', which='major', labelsize=12)
        ax.set_xticklabels(titulos_labels, rotation=45, ha='right')

        for i, v in enumerate(titulos_values):
            ax.text(i, v + 0.5, str(v), ha='center', va='bottom', fontsize=10)

        fig.tight_layout(rect=[0, 0.1, 1, 1])
        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        titulos_graph = base64.b64encode(img.getvalue()).decode('utf-8')
        plt.close()

        return render_template('grafico/charts.html', 
                               setores_graph=setores_graph, 
                               meses_graph=meses_graph, 
                               titulos_graph=titulos_graph)
    except Error as e:
        print(f"Erro ao gerar gráficos: {e}")
        return redirect(url_for('index'))
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0')
