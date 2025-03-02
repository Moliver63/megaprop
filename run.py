from app import create_app, db
from app.models import User  # Importa o modelo User
import os
import logging
from werkzeug.security import generate_password_hash
from flask_socketio import SocketIO  # Correção da importação do SocketIO
from flask import Flask, render_template, redirect, url_for, flash

# Configuração básica de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_database(app):
    """
    Cria o banco de dados e popula com dados iniciais, se necessário.
    """
    with app.app_context():
        # Verifica se o banco de dados já existe (apenas para SQLite)
        db_file = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        if not os.path.exists(db_file):
            logger.info("Banco de dados não encontrado. Criando um novo banco de dados...")
            try:
                db.create_all()
                logger.info("Banco de dados criado com sucesso.")
                # Popula o banco de dados com dados iniciais
                populate_database()
                logger.info("Dados iniciais adicionados ao banco de dados.")
            except Exception as e:
                logger.error(f"Erro ao criar o banco de dados: {str(e)}")
                raise  # Re-lança a exceção para evitar falhas silenciosas
        else:
            logger.info("Banco de dados já existe. Nenhuma ação necessária.")

def populate_database():
    """
    Adiciona dados iniciais ao banco de dados.
    """
    try:
        # Verifica se o usuário admin já existe
        admin_user = User.query.filter_by(email='admin@example.com').first()
        if not admin_user:
            # Cria o usuário admin inicial
            admin_user = User(
                name='Admin',
                usertitle='admin',
                email='admin@example.com',
                role='admin'
            )
            admin_user.set_password('senha_segura')  # Usa o método para definir a senha
            db.session.add(admin_user)
            db.session.commit()
            logger.info(f"Usuário admin criado: {admin_user.usertitle}")
        else:
            logger.info("Usuário admin já existe. Nenhuma ação necessária.")
    except Exception as e:
        logger.error(f"Erro ao adicionar dados iniciais ao banco de dados: {str(e)}")
        db.session.rollback()
        raise  # Re-lança a exceção para evitar falhas silenciosas
       
if __name__ == '__main__':
    # Cria a instância da aplicação Flask
    app = create_app()
    
    # Configura a chave secreta para o flash
    app.secret_key = 'sua_chave_secreta'
    
    # Inicializa o SocketIO
    socketio = SocketIO(app)
    
    # Cria o banco de dados e popula com dados iniciais
    create_database(app)
    
    # Inicia a aplicação Flask com SocketIO
    logger.info("Iniciando a aplicação Flask...")
    socketio.run(app, debug=True)  # Ativa o modo de depuração