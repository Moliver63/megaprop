import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    # Caminho do banco de dados
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f"sqlite:///{os.path.join(basedir, 'instance', 'megaprop.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')
    # Configuração do diretório de uploads
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}
# Certifique-se de que o diretório existe
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
