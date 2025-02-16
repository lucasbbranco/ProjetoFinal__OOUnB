import json
import os
from bottle import Bottle, route, run, request, response, template, static_file, redirect, TEMPLATE_PATH, abort
from bottle import get, post, put, delete
from bottle_websocket import GeventWebSocketServer
from bottle_websocket import websocket
from bottle import jinja2_template

app = Bottle()

# Configura o caminho dos templates
TEMPLATE_PATH.append(os.path.join(os.path.dirname(__file__), 'templates'))

# Simulação de banco de dados
DATABASE = 'database.json'

# Carregar dados do banco de dados
def load_db():
    try:
        with open(DATABASE, 'r', encoding='utf-8') as f:  # Lê o JSON em UTF-8
            return json.load(f)
    except FileNotFoundError:
        return {"users": [], "events": []}

# Salvar dados no banco de dados
def save_db(data):
    with open(DATABASE, 'w', encoding='utf-8') as f: 
        json.dump(data, f, indent=4, ensure_ascii=False)

# Classe base para usuários
class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def authenticate(self, password):
        return self.password == password

# Classe para eventos
class Event:
    def __init__(self, title, description, date, user):
        self.title = title
        self.description = description
        self.date = date
        self.user = user

# Relação de composição: Agenda contém eventos
class Agenda:
    def __init__(self, user):
        self.user = user
        self.events = []

    def add_event(self, event):
        self.events.append(event)

# Polimorfismo: Admin herda de User
class Admin(User):
    def __init__(self, username, password):
        super().__init__(username, password)
        self.role = "admin"

# Rota para servir arquivos estáticos
@app.route('/static/<filename:path>')
def serve_static(filename):
    return static_file(filename, root='./static')

# Rota principal
@app.route('/')
def index():
    return template('login.html')  # Renderiza a página de login como página inicial

@app.route('/login', method='GET')
def show_login():
    return template('login.html')  # Renderiza a página de login

@app.route('/login', method='POST')
def login():
    username = request.forms.get('username')
    password = request.forms.get('password')
    db = load_db()
    for user_data in db['users']:
        if user_data['username'] == username and user_data['password'] == password:
            response.set_cookie("user", username)
            return redirect('/agenda')
    return "Login falhou. Verifique suas credenciais."

# Rota de logout
@app.route('/logout')
def logout():
    response.delete_cookie("user")
    return redirect('/')

# Rota da agenda
@app.route('/agenda')
def agenda():
    user = request.get_cookie("user")
    if not user:
        return redirect('/')
    
    db = load_db()
    user_events = [event for event in db['events'] if event['user'] == user]
    
    # Renderiza o template usando o Jinja2
    return jinja2_template('agenda.html', user=user, events=user_events)

# Rota para adicionar evento
@app.route('/add_event', method='POST')
def add_event():
    user = request.get_cookie("user")
    if not user:
        print("Usuário não está logado. Redirecionando para a página inicial.")
        return redirect('/')
    
    # Captura os dados do formulário
    title = request.forms.getunicode('title')
    description = request.forms.getunicode('description')
    date = request.forms.getunicode('date')
    
    # Carrega o banco de dados
    db = load_db()
    
    # Adiciona o novo evento
    new_event = {
        "title": title,
        "description": description,
        "date": date,
        "user": user
    }
    db['events'].append(new_event)
    
    # Salva o banco de dados atualizado
    save_db(db)
    
    print(f"Novo evento adicionado: {new_event}")
    
    # Redireciona de volta para a agenda
    return redirect('/agenda')

# WebSocket para notificações em tempo real
@app.route('/websocket')
def handle_websocket():
    wsock = request.environ.get('wsgi.websocket')
    if not wsock:
        abort(400, 'Expected WebSocket request.')

    while True:
        message = wsock.receive()
        if message:
            wsock.send(f"Evento recebido: {message}")
            
@app.route('/register', method='GET')
def show_register():
    return template('register.html')

@app.route('/register', method='POST')
def register():
    username = request.forms.get('username')
    password = request.forms.get('password')
    
    
    # Carrega o banco de dados
    db = load_db()
    
    # Verifica se o usuário já existe
    for user_data in db['users']:
        if user_data['username'] == username:
            return "Usuário já existe. Escolha outro nome de usuário."
    
    # Adiciona o novo usuário
    new_user = {
        "username": username,
        "password": password
    }
    db['users'].append(new_user)
    
    # Salva o banco de dados atualizado
    save_db(db)
    
    print(f"Novo usuário registrado: {new_user}")
    
    # Redireciona para a página de login
    return redirect('/')

# Iniciar servidor
if __name__ == '__main__':
    run(app, host='localhost', port=8080, server=GeventWebSocketServer)