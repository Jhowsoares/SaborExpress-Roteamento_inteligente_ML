# forms.py - VERSÃO SIMPLIFICADA E ORGANIZADA
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TelField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from models import User

# Validações compartilhadas
def validar_usuario_existe(form, field):
    """Valida se usuário já existe"""
    user = User.query.filter_by(username=field.data).first()
    if user:
        raise ValidationError('Este nome de usuário já está em uso.')

def validar_email_existe(form, field):
    """Valida se email já existe"""
    user = User.query.filter_by(email=field.data).first()
    if user:
        raise ValidationError('Este email já está cadastrado.')

class RegistrationForm(FlaskForm):
    """Formulário de registro de usuário"""
    username = StringField('Nome de Usuário', 
                          validators=[DataRequired(), Length(min=2, max=20), validar_usuario_existe])
    email = StringField('Email', 
                       validators=[DataRequired(), Email(), validar_email_existe])
    telefone = TelField('Telefone', 
                       validators=[DataRequired(), Length(min=10, max=15)])
    password = PasswordField('Senha', 
                            validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Senha',
                                    validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Cadastrar')

class LoginForm(FlaskForm):
    """Formulário de login"""
    email = StringField('Email', 
                       validators=[DataRequired(), Email()])
    password = PasswordField('Senha', validators=[DataRequired()])
    remember = BooleanField("Lembrar-me")
    submit = SubmitField('Login')

class ProfileForm(FlaskForm):
    """Formulário de edição de perfil"""
    username = StringField('Nome de Usuário', 
                          validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', 
                       validators=[DataRequired(), Email()])
    telefone = TelField('Telefone', 
                       validators=[DataRequired(), Length(min=10, max=15)])
    submit = SubmitField('Atualizar Perfil')

class ChangePasswordForm(FlaskForm):
    """Formulário de alteração de senha"""
    current_password = PasswordField('Senha Atual', validators=[DataRequired()])
    new_password = PasswordField('Nova Senha', 
                                validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirmar Nova Senha', 
                                    validators=[DataRequired(), EqualTo('new_password')])
    submit = SubmitField('Alterar Senha')

class CheckoutForm(FlaskForm):
    """Formulário de checkout/finalização de pedido"""
    # Informações de entrega
    nome = StringField('Nome Completo', validators=[DataRequired(), Length(max=100)])
    telefone = StringField('Telefone', validators=[DataRequired(), Length(min=10, max=15)])
    
    # Endereço
    cep = StringField('CEP', validators=[DataRequired()])
    logradouro = StringField('Logradouro', validators=[DataRequired()])
    numero = StringField('Número', validators=[DataRequired()])
    complemento = StringField('Complemento')
    bairro = StringField('Bairro', validators=[DataRequired()])
    cidade = StringField('Cidade', validators=[DataRequired()])
    estado = StringField('Estado', validators=[DataRequired()])
    
    # Observações
    instrucoes = TextAreaField('Instruções Especiais', validators=[Length(max=500)])
    
    submit = SubmitField('Finalizar Pedido')

class AdminLoginForm(FlaskForm):
    """Formulário de login administrativo"""
    username = StringField('Usuário', validators=[DataRequired()])
    password = PasswordField('Senha', validators=[DataRequired()])
    submit = SubmitField('Entrar')

class ProdutoForm(FlaskForm):
    """Formulário de cadastro/edição de produto"""
    nome = StringField('Nome do Produto', 
                      validators=[DataRequired(), Length(max=100)])
    descricao = TextAreaField('Descrição', 
                             validators=[DataRequired()])
    preco = StringField('Preço', 
                       validators=[DataRequired()])
    imagem = StringField('URL da Imagem')
    categoria_id = SelectField('Categoria', 
                              coerce=int, 
                              validators=[DataRequired()])
    destaque = BooleanField('Produto em Destaque')
    tags = StringField('Tags (separadas por vírgula)')
    ativo = BooleanField('Produto Ativo', default=True)
    submit = SubmitField('Salvar Produto')