# models.py - VERSÃO SIMPLIFICADA E ORGANIZADA
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """Modelo de usuário do sistema"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    telefone = db.Column(db.String(20))
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Categoria(db.Model):
    """Modelo de categorias de produtos"""
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)
    descricao = db.Column(db.String(200))
    
    def __repr__(self):
        return f'<Categoria {self.nome}>'

class Produto(db.Model):
    """Modelo de produtos"""
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    preco = db.Column(db.Float, nullable=False)
    imagem = db.Column(db.String(200))
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria.id'), nullable=False)
    destaque = db.Column(db.Boolean, default=False)
    tags = db.Column(db.String(200))
    ativo = db.Column(db.Boolean, default=True)
    
    categoria = db.relationship('Categoria', backref=db.backref('produtos', lazy=True))
    
    def __repr__(self):
        return f'<Produto {self.nome}>'

class Pedido(db.Model):
    """Modelo de pedidos"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    data_pedido = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pendente')
    total = db.Column(db.Float, nullable=False)
    tipo_entrega = db.Column(db.String(10), default='delivery')
    endereco_entrega = db.Column(db.Text)
    observacoes = db.Column(db.Text)
    localizacao_entrega_id = db.Column(db.Integer, db.ForeignKey('localizacao.id'))
    
    # Relacionamentos
    user = db.relationship('User', backref=db.backref('pedidos', lazy=True))
    localizacao_entrega = db.relationship('Localizacao', foreign_keys=[localizacao_entrega_id])
    
    def __repr__(self):
        return f'<Pedido {self.id} - {self.status}>'

class ItemPedido(db.Model):
    """Modelo de itens do pedido"""
    id = db.Column(db.Integer, primary_key=True)
    pedido_id = db.Column(db.Integer, db.ForeignKey('pedido.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Float, nullable=False)
    
    produto = db.relationship('Produto', backref=db.backref('itens_pedido', lazy=True))
    
    def __repr__(self):
        return f'<ItemPedido {self.quantidade}x {self.produto.nome}>'

class Localizacao(db.Model):
    """Modelo de localizações para roteamento"""
    __tablename__ = 'localizacao'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    tipo = db.Column(db.String(20))
    
    def __repr__(self):
        return f'<Localizacao {self.nome} ({self.latitude}, {self.longitude})>'

class Rota(db.Model):
    """Modelo de rotas entre localizações"""
    __tablename__ = 'rota'
    
    id = db.Column(db.Integer, primary_key=True)
    localizacao_origem_id = db.Column(db.Integer, db.ForeignKey('localizacao.id'), nullable=False)
    localizacao_destino_id = db.Column(db.Integer, db.ForeignKey('localizacao.id'), nullable=False)
    distancia_metros = db.Column(db.Integer, nullable=False)
    tempo_minutos = db.Column(db.Integer, nullable=False)
    
    origem = db.relationship('Localizacao', foreign_keys=[localizacao_origem_id], backref='rotas_saida')
    destino = db.relationship('Localizacao', foreign_keys=[localizacao_destino_id], backref='rotas_entrada')
    
    def __repr__(self):
        return f'<Rota {self.origem.nome} -> {self.destino.nome}: {self.distancia_metros}m>'

class Entregador(db.Model):
    """Modelo de entregadores"""
    __tablename__ = 'entregador'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20))
    veiculo = db.Column(db.String(50))
    disponivel = db.Column(db.Boolean, default=True)
    localizacao_atual_id = db.Column(db.Integer, db.ForeignKey('localizacao.id'))
    
    localizacao_atual = db.relationship('Localizacao', foreign_keys=[localizacao_atual_id])
    
    def __repr__(self):
        return f'<Entregador {self.nome} - {self.veiculo}>'

# Removemos as classes/funções que foram movidas para algoritmos/
# ResultadoKMeans, executar_kmeans, etc. agora estão em algoritmos/kmeans.py