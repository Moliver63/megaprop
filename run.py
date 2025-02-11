from app import create_app, db
from app.models import User  # Importe o modelo User
import os
import logging
from werkzeug.security import generate_password_hash

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
            hashed_password = generate_password_hash('senha_segura', method='pbkdf2:sha256')  # Corrigido aqui
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password=hashed_password,  # Usa o campo 'password' com hashing
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
            logger.info(f"Usuário admin criado: {admin_user.username}")
        else:
            logger.info("Usuário admin já existe. Nenhuma ação necessária.")
    except Exception as e:
        logger.error(f"Erro ao adicionar dados iniciais ao banco de dados: {str(e)}")
        db.session.rollback()
        raise  # Re-lança a exceção para evitar falhas silenciosas

if __name__ == '__main__':
    app = create_app()
    # Cria o banco de dados e popula com dados iniciais
    create_database(app)
    # Inicia a aplicação Flask
    logger.info("Iniciando a aplicação Flask...")
    app.run(debug=True)