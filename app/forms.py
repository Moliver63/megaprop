from flask_wtf import FlaskForm
from wtforms import (
    StringField,
    PasswordField,
    SelectField,
    SubmitField,
    DecimalField,
    IntegerField,
    TextAreaField,
    FileField,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    NumberRange,
    Optional,
    ValidationError,
)
from flask_wtf.file import FileAllowed
from .models import User  # Importe o modelo User para validação de unicidade

# Formulário de Registro
class RegistrationForm(FlaskForm):
    name = StringField('Nome Completo', validators=[DataRequired()])
    usertitle = StringField(
        'Nome de Usuário',
        validators=[DataRequired(), Length(min=3, max=80)]
    )
    email = StringField('E-mail', validators=[DataRequired(), Email()])
    password = PasswordField(
        'Senha',
        validators=[
            DataRequired(),
            Length(min=6, message="A senha deve ter pelo menos 6 caracteres.")
        ]
    )
    confirm_password = PasswordField(
        'Confirmar Senha',
        validators=[
            DataRequired(),
            EqualTo('password', message="As senhas devem coincidir.")
        ]
    )
    role = SelectField(
        'Função',
        choices=[('user', 'Usuário'), ('admin', 'Administrador')],
        default='user'
    )
    submit = SubmitField('Registrar')

    def validate_usertitle(self, usertitle):
        user = User.query.filter_by(usertitle=usertitle.data).first()
        if user:
            raise ValidationError("Este nome de usuário já está em uso.")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError("Este e-mail já está registrado.")

# Formulário de Login
class LoginForm(FlaskForm):
    email = StringField(
        'E-mail',
        validators=[
            DataRequired(message="O e-mail é obrigatório."),
            Email(message="Insira um e-mail válido.")
        ]
    )
    password = PasswordField(
        'Senha',
        validators=[
            DataRequired(message="A senha é obrigatória.")
        ]
    )
    submit = SubmitField('Entrar')

# Formulário para Cadastro ou Edição de Imóveis
class PropertyForm(FlaskForm):
    title = StringField(
        'Título do Imóvel',
        validators=[DataRequired(message="Insira o título do imóvel.")]
    )
    location = StringField(
        'Localização',
        validators=[DataRequired(message="Insira a localização.")]
    )
    price = DecimalField(
        'Preço',
        validators=[
            DataRequired(message="Insira um preço válido."),
            NumberRange(min=0, message="O preço não pode ser negativo.")
        ]
    )
    property_type = SelectField(
        'Tipo de Imóvel',
        choices=[
            ('casa', 'Casa'),
            ('apartamento', 'Apartamento'),
            ('terreno', 'Terreno'),
            ('comercial', 'Comercial')
        ],
        validators=[DataRequired(message="Selecione o tipo de imóvel.")]
    )
    status = SelectField(
        'Status',
        choices=[
            ('venda', 'À Venda'),
            ('aluguel', 'Para Alugar'),
            ('vendido', 'Vendido')
        ],
        validators=[DataRequired(message="Selecione o status.")]
    )
    bedrooms = IntegerField(
        'Número de Quartos',
        validators=[
            DataRequired(message="Insira o número de quartos."),
            NumberRange(min=1, message="O número de quartos deve ser pelo menos 1.")
        ]
    )
    bathrooms = IntegerField(
        'Número de Banheiros',
        validators=[
            DataRequired(message="Insira o número de banheiros."),
            NumberRange(min=1, message="O número de banheiros deve ser pelo menos 1.")
        ]
    )
    total_area = IntegerField(
        'Área Total (m²)',
        validators=[
            DataRequired(message="Insira a área total."),
            NumberRange(min=1, message="A área total deve ser maior que zero.")
        ]
    )
    photos = FileField(
        'Fotos do Imóvel',
        validators=[
            FileAllowed(['jpg', 'png', 'gif'], 'Apenas imagens são permitidas!')
        ],
        render_kw={"multiple": True}
    )
    description = TextAreaField(
        'Descrição',
        validators=[
            DataRequired(message="Insira uma descrição."),
            Length(min=10, message="A descrição deve ter pelo menos 10 caracteres.")
        ]
    )
    submit = SubmitField('Salvar e Publicar')

# Formulário de Recuperação de Senha
class ForgotPasswordForm(FlaskForm):
    email = StringField(
        'E-mail',
        validators=[
            DataRequired(message="O e-mail é obrigatório."),
            Email(message="Insira um e-mail válido.")
        ]
    )
    submit = SubmitField('Enviar E-mail de Recuperação')

# Formulário para Envio de Propostas
class ProposalForm(FlaskForm):
    user_type = SelectField(
        'Tipo de Usuário',
        choices=[
            ('corretor', 'Corretor'),
            ('imobiliaria', 'Imobiliária'),
            ('construtora', 'Construtora'),
            ('empreiteiro', 'Empreiteiro')
        ],
        validators=[DataRequired(message="Selecione o tipo de usuário.")]
    )
    proposal_type = SelectField(
        'Tipo de Proposta',
        choices=[
            ('compra', 'Compra'),
            ('venda', 'Venda'),
            ('aluguel', 'Aluguel'),
            ('parceria', 'Parceria'),
            ('execucao', 'Execução de Obra')
        ],
        validators=[DataRequired(message="Selecione o tipo de proposta.")]
    )
    property_id = SelectField(
        'Selecione o Imóvel (Opcional)',
        coerce=int,
        validators=[Optional()]
    )
    amount = DecimalField(
        'Valor da Proposta',
        places=2,
        validators=[
            DataRequired(message="Insira o valor da proposta."),
            NumberRange(min=1, message="O valor da proposta deve ser maior que zero.")
        ]
    )
    message = TextAreaField(
        'Mensagem',
        validators=[
            DataRequired(message="Insira uma mensagem."),
            Length(min=10, message="A mensagem deve ter pelo menos 10 caracteres.")
        ],
        render_kw={"rows": 4}
    )
    attachment = FileField(
        'Anexar Documento (Opcional)',
        validators=[
            Optional(),
            FileAllowed(['pdf', 'docx', 'txt'], 'Apenas documentos são permitidos!')
        ]
    )
    submit = SubmitField('Enviar Proposta')

#class UpdateProfileForm(FlaskForm):

class UpdateProfileForm(FlaskForm):
    name = StringField(
        'Nome Completo',
        validators=[DataRequired(message="O nome é obrigatório.")]
    )
    usertitle = StringField(
        'Nome de Usuário',
        validators=[
            DataRequired(message="O nome de usuário é obrigatório."),
            Length(min=2, max=20, message="Deve ter entre 2 e 20 caracteres.")
        ]
    )
    email = StringField(
        'E-mail',
        validators=[
            DataRequired(message="O e-mail é obrigatório."),
            Email(message="Insira um e-mail válido.")
        ]
    )
    phone = StringField(
        'Telefone (opcional)',
        validators=[
            Optional(),
            Length(max=15, message="O número de telefone deve ter no máximo 15 caracteres.")
        ]
    )
    profile_pic = FileField(
        'Foto de Perfil',
        validators=[
            Optional(),
            FileAllowed(['jpg', 'jpeg', 'png'], 'Apenas imagens são permitidas!')
        ]
    )
    password = PasswordField(
        'Nova Senha (opcional)',
        validators=[
            Optional(),
            Length(min=6, message="A senha deve ter pelo menos 6 caracteres.")
        ]
    )
    submit = SubmitField('Atualizar Perfil')
   
class UpdateProfileForm(FlaskForm):
    name = StringField(
        'Nome Completo',
        validators=[DataRequired(message="O nome é obrigatório.")]
    )
    usertitle = StringField(
        'Nome de Usuário',
        validators=[
            DataRequired(message="O nome de usuário é obrigatório."),
            Length(min=2, max=20, message="Deve ter entre 2 e 20 caracteres.")
        ]
    )
    email = StringField(
        'E-mail',
        validators=[
            DataRequired(message="O e-mail é obrigatório."),
            Email(message="Insira um e-mail válido.")
        ]
    )
    phone = StringField(
        'Telefone (opcional)',
        validators=[
            Optional(),
            Length(max=15, message="O número de telefone deve ter no máximo 15 caracteres.")
        ]
    )
    profile_pic = FileField(
        'Foto de Perfil',
        validators=[
            Optional(),
            FileAllowed(['jpg', 'jpeg', 'png'], 'Apenas imagens são permitidas!')
        ]
    )
    password = PasswordField(
        'Nova Senha (opcional)',
        validators=[
            Optional(),
            Length(min=6, message="A senha deve ter pelo menos 6 caracteres.")
        ]
    )
    submit = SubmitField('Atualizar Perfil')

    def validate_usertitle(self, usertitle):
        if usertitle.data != current_user.usertitle:
            user = User.query.filter_by(usertitle=usertitle.data).first()
            if user:
                raise ValidationError("Este nome de usuário já está em uso.")

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError("Este e-mail já está cadastrado.")