# routes/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User

auth_bp = Blueprint('auth', __name__, template_folder='templates/auth')

# ---- Helper simples: buscar usuário por username ou email ----
def find_user_by_username_or_email(identifier: str):
    if not identifier:
        return None
    # primeiro por username
    user = User.query.filter_by(username=identifier).first()
    if user:
        return user
    # depois por e-mail
    return User.query.filter_by(email=identifier).first()


# -------------------------
# ROTA: Login (GET / POST)
# -------------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Formulário de login simples que aceita 'identifier' (username ou email) e 'password'.
    """
    if current_user and getattr(current_user, "is_authenticated", False):
        flash("Você já está logado.", "info")
        return redirect(url_for('admin.admin_dashboard') if hasattr(current_user, 'is_authenticated') else url_for('main.homepage'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember', False))

        if not identifier or not password:
            flash("Preencha usuário/e-mail e senha.", "warning")
            return render_template('auth/login.html', identifier=identifier)

        user = find_user_by_username_or_email(identifier)
        if not user:
            flash("Usuário ou e-mail não encontrado.", "danger")
            return render_template('auth/login.html', identifier=identifier)

        if not check_password_hash(user.password, password):
            flash("Senha incorreta.", "danger")
            return render_template('auth/login.html', identifier=identifier)

        # login de fato
        login_user(user, remember=remember)
        flash(f"Bem-vindo, {user.username}!", "success")

        # redirecionar para o destino anterior (next) ou dashboard
        next_url = request.args.get('next')
        if next_url:
            return redirect(next_url)
        # se tiver rota admin, enviar para dashboard admin
        try:
            return redirect(url_for('admin.admin_dashboard'))
        except Exception:
            return redirect(url_for('main.homepage'))

    # GET
    return render_template('auth/login.html')


# -------------------------
# ROTA: Logout
# -------------------------
@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Você saiu da sessão.", "info")
    return redirect(url_for('auth.login'))


# -------------------------
# ROTA: Registro (opcional/prático)
# -------------------------
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Registro básico — cria usuário com username, email e senha.
    Use apenas para testes/development; em produção adicione confirmação por e-mail e validações.
    """
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        password2 = request.form.get('password2', '')
        telefone = request.form.get('telefone', '')

        if not username or not email or not password:
            flash("Preencha usuário, e-mail e senha.", "warning")
            return render_template('auth/register.html', username=username, email=email)

        if password != password2:
            flash("As senhas não batem.", "warning")
            return render_template('auth/register.html', username=username, email=email)

        # checar existencia
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Usuário ou e-mail já cadastrado.", "danger")
            return render_template('auth/register.html', username=username, email=email)

        # criar usuário
        hashed = generate_password_hash(password)
        novo = User(username=username, email=email, password=hashed, telefone=telefone)
        db.session.add(novo)
        db.session.commit()

        flash("Conta criada com sucesso. Faça login.", "success")
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


# -------------------------
# ROTA: Editar Perfil (GET / POST)
# -------------------------
@auth_bp.route('/editar_perfil', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    """
    Permite atualizar campos públicos do usuário (nome de usuário, e-mail, telefone).
    Não altera senha aqui.
    """
    user = current_user

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        telefone = request.form.get('telefone', '').strip()

        if not username or not email:
            flash("Preencha usuário e e-mail.", "warning")
            return render_template('auth/editar_perfil.html', user=user)

        # verificação de unicidade (outros usuários)
        exists = User.query.filter((User.username == username) | (User.email == email)).filter(User.id != user.id).first()
        if exists:
            flash("Outro usuário já usa esse username ou e-mail.", "danger")
            return render_template('auth/editar_perfil.html', user=user)

        user.username = username
        user.email = email
        user.telefone = telefone
        db.session.commit()

        flash("Perfil atualizado com sucesso.", "success")
        return redirect(url_for('auth.editar_perfil'))

    # GET — renderiza form com dados
    return render_template('auth/editar_perfil.html', user=user)


# -------------------------
# ROTA: Alterar Senha (GET / POST)
# -------------------------
@auth_bp.route('/alterar_senha', methods=['GET', 'POST'])
@login_required
def alterar_senha():
    """
    Alterar senha atual do usuário — pede a senha atual e a nova (duas vezes).
    """
    user = current_user

    if request.method == 'POST':
        senha_atual = request.form.get('senha_atual', '')
        nova_senha = request.form.get('nova_senha', '')
        nova_senha2 = request.form.get('nova_senha2', '')

        if not senha_atual or not nova_senha:
            flash("Preencha a senha atual e a nova senha.", "warning")
            return render_template('auth/alterar_senha.html')

        if not check_password_hash(user.password, senha_atual):
            flash("Senha atual incorreta.", "danger")
            return render_template('auth/alterar_senha.html')

        if nova_senha != nova_senha2:
            flash("As novas senhas não coincidem.", "warning")
            return render_template('auth/alterar_senha.html')

        user.password = generate_password_hash(nova_senha)
        db.session.commit()
        flash("Senha alterada com sucesso.", "success")
        return redirect(url_for('admin.admin_dashboard'))

    return render_template('auth/alterar_senha.html')


# -------------------------
# Opcional: rota para recuperar username/email — pode ser extendida
# -------------------------
@auth_bp.route('/esqueci_senha', methods=['GET', 'POST'])
def esqueci_senha():
    """
    Rota de 'esqueci senha' placeholder. Em produção, implemente envio de e-mail com token.
    """
    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        user = find_user_by_username_or_email(identifier)
        if not user:
            flash("Usuário/e-mail não encontrado.", "warning")
            return render_template('auth/esqueci_senha.html')
        # Aqui você geraria token e enviaria email — placeholder:
        flash("Link de recuperação enviado (simulado).", "info")
        return redirect(url_for('auth.login'))

    return render_template('auth/esqueci_senha.html')
