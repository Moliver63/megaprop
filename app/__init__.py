from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from authlib.integrations.flask_client import OAuth  # Importa o OAuth do Authlib
import os
import logging
from sqlalchemy.exc import OperationalError
from werkzeug.utils import secure_filename
from babel.numbers import format_currency

# Configurações iniciais
db = SQLAlchemy()  # Inicializa o SQLAlchemy para gerenciar o banco de dados
login_manager = LoginManager()  # Inicializa o LoginManager para autenticação de usuários
migrate = Migrate()  # Inicializa o Migrate para gerenciar migrações do banco de dados
oauth = OAuth()  # Inicializa o OAuth para autenticação com provedores externos

def create_app():
    """
    Função de fábrica para criar e configurar a aplicação Flask.
    """
    app = Flask(__name__)

    # Configurações básicas da aplicação
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'sua_chave_secreta_aqui'  # Chave secreta para segurança
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL') or 'sqlite:///megaprop.db'  # URL do banco de dados
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Desativa o rastreamento de modificações do SQLAlchemy

    # Configuração de upload de arquivos
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static/uploads')
    PROFILE_PICS_FOLDER = os.path.join(os.getcwd(), 'static/profile_pics')

    # Garante que as pastas de upload existam
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(PROFILE_PICS_FOLDER, exist_ok=True)

    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  # Pasta para upload de arquivos gerais
    app.config['PROFILE_PICS_FOLDER'] = PROFILE_PICS_FOLDER  # Pasta para fotos de perfil
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}  # Extensões de arquivo permitidas

    # Inicialização de extensões
    db.init_app(app)  # Inicializa o SQLAlchemy com a aplicação
    login_manager.init_app(app)  # Inicializa o LoginManager com a aplicação
    migrate.init_app(app, db)  # Inicializa o Migrate com a aplicação e o banco de dados
    oauth.init_app(app)  # Inicializa o OAuth com a aplicação
    login_manager.login_view = 'main.login'  # Define a view de login para redirecionar usuários não autenticados

    # Configuração do Google OAuth
    app.config['GOOGLE_CLIENT_ID'] = '1000850630887-3jccqjga8unsr6bpfnn0qhmudkie10cm.apps.googleusercontent.com'
    app.config['GOOGLE_CLIENT_SECRET'] = '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'
    app.config['GOOGLE_AUTH_URI'] = 'https://accounts.google.com/o/oauth2/auth'
    app.config['GOOGLE_TOKEN_URI'] = 'https://oauth2.googleapis.com/token'
    app.config['GOOGLE_AUTH_PROVIDER_X509_CERT_URL'] = 'https://www.googleapis.com/oauth2/v1/certs'


    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        access_token_url='https://accounts.google.com/o/oauth2/token',
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        userinfo_endpoint='https://www.googleapis.com/oauth2/v1/userinfo',
        client_kwargs={'scope': 'openid profile email'}
    )

    # Registrar filtro Jinja2 para formatação de moeda
    @app.context_processor
    def inject_utilities():
        """
        Registra o filtro `format_currency` no contexto do Jinja2.
        """
        def format_currency_filter(value):
            """
            Filtro para formatar valores monetários.
            """
            try:
                # Tenta formatar o valor usando a biblioteca Babel
                return format_currency(value, 'BRL', locale='pt_BR')
            except Exception:
                # Caso ocorra um erro, formata manualmente
                return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        return {'format_currency': format_currency_filter}

    # Registrar Blueprints (rotas da aplicação)
    from app.routes import main  # Importa o Blueprint 'main' das rotas
    app.register_blueprint(main)  # Registra o Blueprint na aplicação

    # Configurar user loader para o Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        """
        Função para carregar um usuário a partir do ID.
        """
        from app.models import User  # Importa o modelo User
        return User.query.get(int(user_id))  # Retorna o usuário com o ID fornecido

    # Criar banco de dados se necessário
    with app.app_context():
        try:
            db.create_all()  # Cria todas as tabelas do banco de dados
        except OperationalError as e:
            logging.error(f"Erro de banco de dados: {str(e)}")  # Loga erros de banco de dados

    return app  # Retorna a aplicação configurada