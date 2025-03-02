from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from . import db
from .models import User, Property, Proposal, Activity, VisitAgreement
from .forms import (
    RegistrationForm,
    LoginForm,
    PropertyForm,
    ProposalForm,
    ForgotPasswordForm,
    UpdateProfileForm
)
from app import db, oauth
from flask_wtf.file import FileAllowed, FileSize
from datetime import datetime
import os
import requests

# Cria o Blueprint 'main'
main = Blueprint('main', __name__)

# Constantes para roles
ADMIN_ROLE = 'admin'
USER_ROLE = 'user'

# Função para verificar extensões permitidas
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

# Filtro personalizado para formatar moeda
@main.app_template_filter('format_currency')
def format_currency(value):
    return f"R${value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# Rota principal
@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Número de itens por página
    properties = Property.query.paginate(page=page, per_page=per_page, error_out=False)
    return render_template('index.html', properties=properties)

# Registro de usuário
@main.route('/register', methods=['GET', 'POST'])
def register():
    """
    Rota para o cadastro de novos usuários.
    """
    # Redireciona o usuário para a página inicial se já estiver autenticado
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    # Instância do formulário de registro
    form = RegistrationForm()

    # Validação do formulário ao submeter
    if form.validate_on_submit():
        try:
            # Verifica se o email ou usertitle já estão cadastrados
            existing_user = User.query.filter(
                (User.email == form.email.data) | (User.usertitle == form.usertitle.data)
            ).first()

            if existing_user:
                flash('E-mail ou nome de usuário já cadastrados.', 'danger')
                return redirect(url_for('main.register'))

            # Cria um novo usuário com os dados do formulário
            user = User(
                name=form.name.data,
                usertitle=form.usertitle.data,
                email=form.email.data,
                user_profile=form.user_profile.data
            )

            # Hasha a senha antes de salvar no banco de dados
            user.set_password(form.password.data)

            # Salva o novo usuário no banco de dados
            db.session.add(user)
            db.session.commit()

            # Exibe uma mensagem de sucesso e redireciona para a página de login
            flash('Cadastro realizado com sucesso! Faça login para continuar.', 'success')
            return redirect(url_for('main.login'))

        except Exception as e:
            # Em caso de erro, reverte a transação e exibe uma mensagem de erro
            db.session.rollback()
            flash(f'Ocorreu um erro ao criar sua conta: {str(e)}', 'danger')

    # Renderiza o formulário de registro
    return render_template('register.html', form=form)
# Login de usuário
@main.route('/login', methods=['GET', 'POST'])
def login():
    """
    Rota para login tradicional (e-mail e senha) e redirecionamento para login com Google.
    """
    # Redireciona o usuário para o dashboard se já estiver autenticado
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    form = LoginForm()

    # Processa o formulário de login tradicional
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            next_page = request.args.get('next') or url_for('main.dashboard')
            return redirect(next_page)
        else:
            flash('Login falhou. Verifique seu e-mail e senha.', 'danger')

    return render_template('login.html', form=form)


@main.route('/google-login')
def google_login():
    """
    Rota para iniciar o processo de login com Google.
    """
    redirect_uri = url_for('main.authorize', _external=True)  # Use 'main.authorize' aqui
    return oauth.google.authorize_redirect(redirect_uri)


@main.route('/authorize')
def authorize():
    """
    Callback do Google OAuth para finalizar o login.
    """
    try:
        token = oauth.google.authorize_access_token()
        user_info = oauth.google.parse_id_token(token)

        # Verifica se o usuário já existe no banco de dados
        user = User.query.filter_by(email=user_info['email']).first()

        if not user:
            # Cria um novo usuário se não existir
            user = User(
                name=user_info.get('name'),
                usertitle=user_info.get('email').split('@')[0],  # Usa parte do email como username
                email=user_info.get('email'),
                profile_picture=user_info.get('picture')  # Salva a foto de perfil do Google
            )
            db.session.add(user)
            db.session.commit()

        # Loga o usuário no sistema
        login_user(user)
        flash('Login realizado com sucesso!', 'success')
        return redirect(url_for('main.dashboard'))  # Redireciona para o dashboard

    except Exception as e:
        flash(f'Ocorreu um erro durante o login: {str(e)}', 'danger')
        return redirect(url_for('main.login'))  # Redireciona para a página de login
        
# Recuperação de senha
@main.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    # Se o usuário já estiver autenticado, redirecione para a página inicial
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()

        if user:
            # Gera um token único e envia um e-mail com o link de recuperação
            token = generate_reset_token(user)
            send_reset_email(user, token)
            flash('Um e-mail de recuperação foi enviado para sua caixa de entrada.', 'info')
            return redirect(url_for('main.login'))
        else:
            flash('Este e-mail não está registrado em nosso sistema.', 'danger')

    return render_template('forgot_password.html', form=form)
# configurações
@main.route('/settings', methods=['GET', 'POST'])
def settings():
    form = SettingsForm()

    if form.validate_on_submit():
        # Atualiza as informações do usuário
        current_user.username = form.username.data
        current_user.email = form.email.data

        # Salva a foto de perfil, se fornecida
        if form.profile_picture.data:
            # Processamento da imagem (ex.: salvar no servidor)
            pass

        current_user.user_type = form.user_type.data
        db.session.commit()

        flash("Suas configurações foram atualizadas com sucesso!", "success")
        return redirect(url_for('main.settings'))

    # Preenche o formulário com os dados atuais do usuário
    form.username.data = current_user.username
    form.email.data = current_user.email
    form.user_type.data = current_user.user_type

    return render_template('settings.html', form=form)
    
# Perfil do usuário
@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm()

    if form.validate_on_submit():
        try:
            # Atualizar nome, título e email
            current_user.name = form.name.data
            current_user.usertitle = form.usertitle.data
            current_user.email = form.email.data
            current_user.phone = form.phone.data if form.phone.data else None

            # Processar upload da foto de perfil
            if form.profile_pic.data:
                upload_folder = current_app.config['UPLOAD_FOLDER_PROFILE']
                if not os.path.exists(upload_folder):
                    os.makedirs(upload_folder)

                # Remover foto antiga se existir
                if current_user.profile_picture:
                    old_file = os.path.join(upload_folder, current_user.profile_picture)
                    if os.path.exists(old_file):
                        os.remove(old_file)

                # Salvar nova foto
                filename = secure_filename(form.profile_pic.data.filename)
                file_path = os.path.join(upload_folder, filename)
                form.profile_pic.data.save(file_path)
                current_user.profile_picture = filename

            # Atualizar senha se fornecida
            if form.password.data:
                current_user.set_password(form.password.data)

            # Commit das alterações no banco de dados
            db.session.commit()
            flash('Perfil atualizado com sucesso!', 'success')
            return redirect(url_for('main.profile'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar o perfil: {str(e)}', 'danger')

    # Preencher o formulário com os dados atuais do usuário
    form.name.data = current_user.name
    form.usertitle.data = current_user.usertitle
    form.email.data = current_user.email
    form.phone.data = current_user.phone if hasattr(current_user, 'phone') else None

    return render_template('profile.html', form=form)

# Dashboard do usuário
@main.route('/dashboard')
@login_required
def dashboard():
    property_count = Property.query.filter_by(user_id=current_user.id).count()
    proposal_count = Proposal.query.filter_by(receiver_id=current_user.id).count()
    connection_count = Proposal.query.filter_by(sender_id=current_user.id).count()
    recent_activities = Activity.query.filter_by(user_id=current_user.id).order_by(Activity.timestamp.desc()).limit(5).all()
    
    return render_template(
        'dashboard.html',
        property_count=property_count,
        proposal_count=proposal_count,
        connection_count=connection_count,
        recent_activities=recent_activities
    )

# Adicionar imóvel
@main.route('/add-property', methods=['GET', 'POST'])
@login_required
def add_property():
    form = PropertyForm()
    if form.validate_on_submit():
        try:
            # Garante que o diretório de upload existe
            if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
                os.makedirs(current_app.config['UPLOAD_FOLDER'])

            # Processa as fotos enviadas
            photo_paths = []
            if form.photos.data:
                for file in form.photos.data:
                    if file and hasattr(file, 'filename') and allowed_file(file.filename):
                        filename = secure_filename(file.filename)
                        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                        file.save(save_path)
                        photo_paths.append(filename)
                        current_app.logger.info(f"Foto salva: {save_path}")

            # Cria uma nova instância de Property
            new_property = Property(
                title=form.title.data,
                location=form.location.data,
                price=form.price.data,
                property_type=form.property_type.data,
                status=form.status.data,
                bedrooms=form.bedrooms.data,
                bathrooms=form.bathrooms.data,
                total_area=form.total_area.data,
                description=form.description.data,
                photos=','.join(photo_paths) if photo_paths else None,
                user_id=current_user.id
            )

            # Adiciona o imóvel ao banco de dados
            db.session.add(new_property)
            db.session.commit()

            flash('Imóvel cadastrado com sucesso!', 'success')
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao cadastrar: {str(e)}', 'danger')
            current_app.logger.error(f"Erro ao cadastrar imóvel: {str(e)}")
    
    return render_template('add_property.html', form=form)

# Listar imóveis do usuário
@main.route('/my-properties')
@login_required
def my_properties():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    properties = Property.query.filter_by(user_id=current_user.id).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('my_properties.html', properties=properties)

# Excluir imóvel
@main.route('/delete-property/<int:id>', methods=['POST'])
@login_required
def delete_property(id):
    property = Property.query.get_or_404(id)

    # Verificar se o imóvel pertence ao usuário logado
    if property.user_id != current_user.id:
        flash('Você não tem permissão para excluir este imóvel.', 'danger')
        return redirect(url_for('main.my_properties'))

    try:
        # Excluir fotos associadas ao imóvel (se houver)
        if property.photos:
            for photo in property.photos.split(','):
                photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], photo)
                if os.path.exists(photo_path):
                    os.remove(photo_path)
                    current_app.logger.info(f"Foto excluída: {photo_path}")

        # Excluir o imóvel do banco de dados
        db.session.delete(property)
        db.session.commit()

        flash('Imóvel excluído com sucesso!', 'success')
        current_app.logger.info(f"Imóvel excluído: ID={id}, Título={property.title}")
    except FileNotFoundError as e:
        db.session.rollback()
        flash('Erro ao excluir fotos do imóvel. Por favor, tente novamente.', 'danger')
        current_app.logger.error(f"Erro ao excluir fotos: {str(e)}")
    except Exception as e:
        db.session.rollback()
        flash(f'Ocorreu um erro ao excluir o imóvel: {str(e)}', 'danger')
        current_app.logger.error(f"Erro ao excluir imóvel: ID={id}, Erro={str(e)}")

    return redirect(url_for('main.my_properties'))

# Logout
@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da sua conta com sucesso.', 'info')
    return redirect(url_for('main.index'))

# Excluir conta
@main.route('/delete_account', methods=['POST'])
@login_required
def delete_account():
    if request.form.get('confirmation') != 'confirm':
        flash('Exclusão de conta cancelada.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    try:
        db.session.delete(current_user)
        db.session.commit()
        flash('Sua conta foi excluída com sucesso.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir sua conta: {str(e)}', 'danger')
        current_app.logger.error(f"Erro ao excluir conta: {str(e)}")
    
    return redirect(url_for('main.index'))

# Listar usuários (apenas para admin)
@main.route('/users')
@login_required
def users():
    if current_user.role != ADMIN_ROLE:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    users_list = User.query.all()
    return render_template('users.html', users=users_list)

# Alterar papel do usuário (apenas para admin)
@main.route('/change_role/<int:user_id>', methods=['POST'])
@login_required
def change_role(user_id):
    if current_user.role != ADMIN_ROLE:
        flash('Acesso negado.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role')
    if new_role in [ADMIN_ROLE, USER_ROLE]:
        try:
            user.role = new_role
            db.session.commit()
            flash(f'Perfil de {user.usertitle} atualizado.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar o perfil: {str(e)}', 'danger')
            current_app.logger.error(f"Erro ao atualizar perfil: {str(e)}")
    else:
        flash('Role inválida.', 'danger')
    
    return redirect(url_for('main.users'))

# Propostas recebidas
@main.route('/received_proposals')
@login_required
def received_proposals():
    proposals = Proposal.query.filter_by(receiver_id=current_user.id).all()
    return render_template('received_proposals.html', proposals=proposals)

# Enviar proposta
@main.route('/send_proposal', methods=['GET', 'POST'])
@login_required
def send_proposal():
    form = ProposalForm()
    form.property_id.choices = [(prop.id, prop.title) for prop in Property.query.all()]

    if form.validate_on_submit():
        try:
            property_id = form.property_id.data
            property = Property.query.get(property_id)

            if not property:
                flash('Imóvel inválido ou não encontrado.', 'danger')
                return redirect(url_for('main.send_proposal'))

            if not property.user_id:
                flash('Este imóvel não tem um proprietário associado.', 'danger')
                return redirect(url_for('main.send_proposal'))

            proposal = Proposal(
                message=form.message.data,
                status='pending',
                property_id=property_id,
                sender_id=current_user.id,
                receiver_id=property.user_id
            )

            db.session.add(proposal)
            db.session.commit()

            flash('Proposta enviada com sucesso!', 'success')
            return redirect(url_for('main.dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao enviar proposta: {str(e)}', 'danger')
            current_app.logger.error(f"Erro ao enviar proposta: {str(e)}")
            return redirect(url_for('main.send_proposal'))

    return render_template('send_proposal.html', form=form)

# Editar imóvel
@main.route('/edit-property/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_property(id):
    property = Property.query.get_or_404(id)

    if property.user_id != current_user.id:
        flash('Você não tem permissão para editar este imóvel.', 'danger')
        return redirect(url_for('main.my_properties'))

    form = PropertyForm(obj=property)

    if form.validate_on_submit():
        try:
            photo_paths = []
            if form.photos.data:
                for photo in form.photos.data:
                    if photo and hasattr(photo, 'filename') and allowed_file(photo.filename):
                        filename = secure_filename(photo.filename)
                        save_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                        photo.save(save_path)
                        photo_paths.append(filename)
                        current_app.logger.info(f"Foto salva: {save_path}")
            
            property.title = form.title.data
            property.location = form.location.data
            property.price = form.price.data
            property.property_type = form.property_type.data
            property.status = form.status.data
            property.bedrooms = form.bedrooms.data
            property.bathrooms = form.bathrooms.data
            property.total_area = form.total_area.data
            property.description = form.description.data
            property.photos = ','.join(photo_paths) if photo_paths else property.photos

            db.session.commit()
            flash('Imóvel atualizado com sucesso!', 'success')
            return redirect(url_for('main.my_properties'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro ao atualizar o imóvel: {str(e)}', 'danger')
            current_app.logger.error(f"Erro ao atualizar imóvel: {str(e)}")

    return render_template('edit_property.html', form=form, property=property)

# Dashboard específico para corretores
@main.route('/dashboard/corretor')
@login_required
def dashboard_corretor():
    return render_template('dashboard_corretor.html')

# Dashboard específico para construtoras
@main.route('/dashboard/construtora')
@login_required
def dashboard_construtora():
    return render_template('dashboard_construtora.html')

# Excluir foto específica de um 
# Excluir foto específica de um imóvel
@main.route('/delete_photo/<int:property_id>/<string:photo_name>', methods=['POST'])
@login_required
def delete_photo(property_id, photo_name):
    """
    Rota para excluir uma foto específica de um imóvel.
    """
    # Buscar o imóvel pelo ID
    property = Property.query.get_or_404(property_id)

    # Verificar se o imóvel pertence ao usuário logado
    if property.user_id != current_user.id:
        flash('Você não tem permissão para excluir esta foto.', 'danger')
        return redirect(url_for('main.my_properties'))

    try:
        # Construir o caminho completo do arquivo
        photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], photo_name)

        # Excluir o arquivo do sistema de arquivos, se existir
        if os.path.exists(photo_path):
            os.remove(photo_path)
            current_app.logger.info(f"Foto excluída: {photo_path}")
        else:
            flash('A foto não foi encontrada no servidor.', 'warning')

        # Remover a foto da lista de fotos do imóvel
        photos_list = property.photos.split(',') if property.photos else []
        photos_list = [p for p in photos_list if p != photo_name]
        property.photos = ','.join(photos_list) if photos_list else None

        # Salvar as alterações no banco de dados
        db.session.commit()

        flash('Foto excluída com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao excluir a foto: {str(e)}', 'danger')
        current_app.logger.error(f"Erro ao excluir foto: {str(e)}")

    # Redirecionar de volta para a página de edição do imóvel
    return redirect(url_for('main.edit_property', id=property_id))

# Sistema de match aprimorado
@main.route('/match')
@login_required
def match():
    # Obter parâmetros de filtro da URL
    location = request.args.get('location', '')
    property_type = request.args.get('property_type', '')
    min_price = request.args.get('min_price', 0, type=float)
    max_price = request.args.get('max_price', 1000000000, type=float)
    page = request.args.get('page', 1, type=int)  # Página atual

    # Construir a consulta com base nos filtros
    query = Property.query.filter(Property.status == 'available')
    if location:
        query = query.filter(Property.location.ilike(f"%{location}%"))
    if property_type:
        query = query.filter(Property.property_type == property_type)
    if min_price or max_price:
        query = query.filter(Property.price.between(min_price, max_price))

    # Ordenar os resultados por preço (opcional)
    query = query.order_by(Property.price.asc())

    # Paginar os resultados
    matches = query.paginate(page=page, per_page=9, error_out=False)  # 9 itens por página

    return render_template('match.html', matches=matches)

# Assinatura Eletrônica
@main.route('/sign_agreement/<int:agreement_id>', methods=['GET', 'POST'])
@login_required
def sign_agreement(agreement_id):
    agreement = VisitAgreement.query.get_or_404(agreement_id)
    if request.method == 'POST':
        signature = request.form['signature']

        # Chama API de assinatura eletrônica
        api_url = "https://api.docusign.com/signature"
        headers = {"Authorization": "Bearer YOUR_API_KEY"}
        payload = {
            "document_id": agreement.id,
            "signature": signature
        }
        response = requests.post(api_url, headers=headers, json=payload)

        if response.status_code == 200:
            agreement.signature = signature
            agreement.agreement_signed = True
            db.session.commit()
            flash("Termo assinado com sucesso!", "success")
            return redirect(url_for('view_agreement', agreement_id=agreement.id))
        else:
            flash("Erro ao assinar o termo. Tente novamente.", "error")

    return render_template('sign_agreement.html', agreement=agreement)
    # Define a rota '/forgot-password' dentro do Blueprint 'main'