from . import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    """
    Representa os usuários do sistema.
    """
    __tablename__ = 'user'

    # === Campos principais ===
    id = db.Column(db.Integer, primary_key=True, comment="ID único do usuário")
    name = db.Column(db.String(100), nullable=False, comment="Nome completo do usuário")
    usertitle = db.Column(
        db.String(80), unique=True, nullable=False, index=True, comment="Nome de usuário"
    )
    email = db.Column(
        db.String(120), unique=True, nullable=False, index=True, comment="E-mail do usuário"
    )
    password_hash = db.Column(
        db.String(200), nullable=False, comment="Senha hashada do usuário"
    )
    role = db.Column(
        db.String(50), nullable=False, default='user', comment="Papel: admin, user, corretor, etc."
    )
    user_profile = db.Column(
        db.String(50), nullable=False, default='individual', comment="Perfil: individual, empresa, etc."
    )
    preferred_locations = db.Column(
        db.String(500), nullable=True, comment="Locações preferidas pelo usuário"
    )
    phone = db.Column(db.String(20), nullable=True, comment="Número de telefone do usuário")
    profile_picture = db.Column(
        db.String(200), nullable=True, comment="URL da foto de perfil do usuário"
    )
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, comment="Data de criação do usuário"
    )
    last_login = db.Column(
        db.DateTime, nullable=True, comment="Último login do usuário"
    )

    # === Relacionamentos ===
    properties = db.relationship(
        'Property', back_populates='owner', lazy='dynamic', cascade='all, delete-orphan'
    )
    sent_proposals = db.relationship(
        'Proposal', foreign_keys='Proposal.sender_id', back_populates='sender'
    )
    received_proposals = db.relationship(
        'Proposal', foreign_keys='Proposal.receiver_id', back_populates='receiver'
    )
    activities = db.relationship(
        'Activity', back_populates='user', lazy='dynamic'
    )
    matches = db.relationship(
        'Match', foreign_keys='Match.user_id', back_populates='user'
    )
    received_matches = db.relationship(
        'Match', foreign_keys='Match.matched_user_id', back_populates='matched_user'
    )
    notifications = db.relationship(
        'Notification', back_populates='user', lazy='dynamic'
    )

    # === Métodos para gerenciamento de senha ===
    def set_password(self, password):
        """
        Define a senha do usuário usando hashing.
        """
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        """
        Verifica se a senha fornecida corresponde à senha armazenada.
        """
        return check_password_hash(self.password_hash, password)

    # === Métodos auxiliares ===
    def get_active_properties(self):
        """
        Retorna os imóveis ativos do usuário.
        """
        return self.properties.filter(
            Property.status.in_(['available', 'negotiation'])
        ).order_by(Property.created_at.desc())

    def get_match_suggestions(self, limit=10):
        """
        Retorna sugestões de imóveis com base nas preferências de localização do usuário.
        """
        if not self.preferred_locations:
            return []
        return Property.query.filter(
            Property.location.ilike(f'%{self.preferred_locations}%'),
            Property.status == 'available'
        ).limit(limit).all()

    # === Representação do objeto ===
    def __repr__(self):
        return f'<User {self.usertitle}>'
        
class Property(db.Model):
    """
    Representa imóveis com suporte a geolocalização e tags.
    """
    __tablename__ = 'property'
    __table_args__ = (
        db.Index('idx_property_location', 'location'),
        db.Index('idx_property_price', 'price'),
        db.Index('idx_property_status', 'status'),
        {'extend_existing': True}
    )

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    property_type = db.Column(db.String(50), nullable=False)  # Tipo: casa, apartamento, terreno, etc.
    status = db.Column(db.String(50), nullable=False, default='available')  # Status: available, negotiation, sold
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Integer)
    total_area = db.Column(db.Float)
    photos = db.Column(db.String(500))  # Fotos separadas por vírgula
    tags = db.Column(db.String(500))  # Tags de busca separadas por vírgula
    geo_location = db.Column(db.String(100))  # Formato: 'lat,lng'
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relacionamentos
    owner = db.relationship('User', back_populates='properties')
    proposals = db.relationship('Proposal', back_populates='property', lazy='dynamic')
    matches = db.relationship('Match', back_populates='property')

    def get_photos_list(self):
        """Retorna uma lista das fotos do imóvel."""
        return self.photos.split(',') if self.photos else []

    def add_photo(self, filename):
        """Adiciona uma nova foto ao imóvel."""
        photos_list = self.get_photos_list()
        photos_list.append(filename)
        self.photos = ','.join(photos_list)

    def remove_photo(self, filename):
        """Remove uma foto do imóvel."""
        photos_list = self.get_photos_list()
        if filename in photos_list:
            photos_list.remove(filename)
            self.photos = ','.join(photos_list) if photos_list else None

    def __repr__(self):
        return f'<Property {self.title}>'

class Proposal(db.Model):
    """
    Sistema completo de propostas com tipos e validade.
    """
    __tablename__ = 'proposal'
    __table_args__ = (
        db.Index('idx_proposal_status', 'status'),
        {'extend_existing': True}
    )

    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.Text, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pending')  # Status: pending, accepted, rejected
    proposal_type = db.Column(db.String(50), nullable=False, default='buy')  # Tipo: buy, rent, exchange
    terms = db.Column(db.Text)
    expiration_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relacionamentos
    property = db.relationship('Property', back_populates='proposals')
    sender = db.relationship('User', foreign_keys=[sender_id], back_populates='sent_proposals')
    receiver = db.relationship('User', foreign_keys=[receiver_id], back_populates='received_proposals')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if self.amount <= 0:
            raise ValueError("Proposal amount must be positive")

    def __repr__(self):
        return f'<Proposal {self.id} - {self.status}>'

class Match(db.Model):
    """
    Sistema de matches entre usuários e propriedades.
    """
    __tablename__ = 'match'

    id = db.Column(db.Integer, primary_key=True)
    match_type = db.Column(db.String(50), nullable=False)  # Tipo: property, user, interest
    status = db.Column(db.String(50), nullable=False, default='pending')  # Status: pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    matched_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'))

    # Relacionamentos
    user = db.relationship('User', foreign_keys=[user_id], back_populates='matches')
    matched_user = db.relationship('User', foreign_keys=[matched_user_id], back_populates='received_matches')
    property = db.relationship('Property', back_populates='matches')

    def __repr__(self):
        return f'<Match {self.match_type} - {self.status}>'

class Notification(db.Model):
    """
    Sistema de notificações em tempo real.
    """
    __tablename__ = 'notification'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)  # Tipo: proposal, match, system
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'))

    # Relacionamentos
    user = db.relationship('User', back_populates='notifications')
    property = db.relationship('Property')

    def mark_as_read(self):
        """Marca a notificação como lida."""
        self.is_read = True
        db.session.commit()

    def __repr__(self):
        return f'<Notification {self.notification_type}>'

class Activity(db.Model):
    """
    Registra atividades dos usuários no sistema.
    """
    __tablename__ = 'activity'

    id = db.Column(db.Integer, primary_key=True)
    activity_type = db.Column(db.String(50), nullable=False)  # Tipo: login, logout, update_profile, etc.
    description = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))  # Endereço IP do usuário

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', back_populates='activities')

    def __repr__(self):
        return f'<Activity {self.id} - {self.timestamp}>'

class VisitAgreement(db.Model):
    """
    Representa termos de visita com assinatura eletrônica.
    """
    __tablename__ = 'visit_agreement'

    id = db.Column(db.Integer, primary_key=True)
    property_id = db.Column(db.Integer, db.ForeignKey('property.id'), nullable=False)
    visiting_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    property_owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    visit_date = db.Column(db.DateTime, nullable=False)
    agreement_signed = db.Column(db.Boolean, default=False)  # Indica se o termo foi assinado
    signature = db.Column(db.String(300))  # Armazena a assinatura eletrônica
    terms_text = db.Column(db.Text, nullable=False)  # Texto do termo de responsabilidade
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamentos
    property = db.relationship('Property', backref=db.backref('visit_agreements', lazy=True))
    visiting_user = db.relationship('User', foreign_keys=[visiting_user_id], backref=db.backref('visit_agreements_as_visitor', lazy=True))
    property_owner = db.relationship('User', foreign_keys=[property_owner_id], backref=db.backref('visit_agreements_as_owner', lazy=True))

    def __repr__(self):
        return f'<VisitAgreement {self.id} - {self.visit_date}>'