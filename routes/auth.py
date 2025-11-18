import secrets
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from itsdangerous import URLSafeTimedSerializer
from flask_mail import Message
from models import db, User

auth_bp = Blueprint('auth', __name__, template_folder='templates/auth')


# -------------------------
# Helper: buscar usuário por username ou email
# -------------------------
def find_user_by_username_or_email(identifier: str):
    """Procura usuário por username ou email (retorna User ou None)."""
    if not identifier:
        return None
    # primeiro por username
    user = User.query.filter_by(username=identifier).first()
    if user:
        return user
    # depois por email
    return User.query.filter_by(email=identifier).first()


# -------------------------
# Tokens (itsdangerous)
# -------------------------
def generate_reset_token(email):
    """Gera um token seguro para redefinição de senha"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return serializer.dumps(email, salt='password-reset-salt')


def verify_reset_token(token, expiration=3600):
    """Verifica se o token é válido e retorna o email (ou None)"""
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt='password-reset-salt',
            max_age=expiration  # segundos (1 hora padrão)
        )
    except Exception:
        return None
    return email


# -------------------------
# ROTA: Login (GET / POST)
# -------------------------
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Se já está autenticado, redireciona de acordo com o papel
    if current_user and getattr(current_user, "is_authenticated", False):
        flash("Você já está logado.", "info")
        if getattr(current_user, "is_admin", False):
            return redirect(url_for('admin.admin_dashboard'))
        return redirect(url_for('main.homepage'))

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

        # Autentica o usuário
        login_user(user, remember=remember)
        flash(f"Bem-vindo, {user.username}!", "success")

        # Respeita next se houver
        next_url = request.args.get('next')
        if next_url:
            return redirect(next_url)

        # Redirecionamento por papel
        if getattr(user, "is_admin", False):
            return redirect(url_for('admin.admin_dashboard'))
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
# ROTA: Register (simples - ambiente de dev)
# -------------------------
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
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

        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash("Usuário ou e-mail já cadastrado.", "danger")
            return render_template('auth/register.html', username=username, email=email)

        hashed = generate_password_hash(password, method='pbkdf2:sha256')
        novo = User(username=username, email=email, password=hashed, telefone=telefone)
        db.session.add(novo)
        db.session.commit()

        flash("Conta criada com sucesso. Faça login.", "success")
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


# -------------------------
# ROTA: Editar Perfil
# -------------------------
@auth_bp.route('/editar_perfil', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    user = current_user
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        telefone = request.form.get('telefone', '').strip()

        if not username or not email:
            flash("Preencha usuário e e-mail.", "warning")
            return render_template('auth/editar_perfil.html', user=user)

        exists = User.query.filter(
            ((User.username == username) | (User.email == email))
        ).filter(User.id != user.id).first()
        if exists:
            flash("Outro usuário já usa esse username ou e-mail.", "danger")
            return render_template('auth/editar_perfil.html', user=user)

        user.username = username
        user.email = email
        user.telefone = telefone
        db.session.commit()

        flash("Perfil atualizado com sucesso.", "success")
        return redirect(url_for('auth.editar_perfil'))

    return render_template('auth/editar_perfil.html', user=user)


# -------------------------
# ROTA: Alterar Senha (usuário logado)
# -------------------------
@auth_bp.route('/alterar_senha', methods=['GET', 'POST'])
@login_required
def alterar_senha():
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

        user.password = generate_password_hash(nova_senha, method='pbkdf2:sha256')
        db.session.commit()
        flash("Senha alterada com sucesso.", "success")
        return redirect(url_for('auth.perfil'))  # redireciona para perfil (ou main.homepage)

    return render_template('auth/alterar_senha.html')


# -------------------------
# ROTA: esqueci_senha (envio de email)
# -------------------------
@auth_bp.route('/esqueci_senha', methods=['GET', 'POST'])
def esqueci_senha():
    mail = current_app.extensions.get('mail')  # recupera a extensão inicializada no app

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        user = find_user_by_username_or_email(identifier)

        # Mensagem genérica (segurança)
        flash("Se o email/usuário existir, um link de recuperação será enviado.", "info")

        if not user:
            # não revelar existência -> redireciona ao login com a mensagem genérica
            return redirect(url_for('auth.login'))

        try:
            token = generate_reset_token(user.email)
            reset_url = url_for('auth.redefinir_senha', token=token, _external=True)

            # Log do link para debug local (útil se quiser copiar direto)
            current_app.logger.info(f"Reset URL (debug): {reset_url}")

            subject = "Redefinição de Senha - Sabor Express"
            sender = current_app.config.get('MAIL_DEFAULT_SENDER') or 'no-reply@meuapp.test'

            html = render_template(
                'email/redefinir_senha.html',
                user=user,
                reset_url=reset_url,
                current_year=datetime.now().year
            )

            msg = Message(subject=subject, recipients=[user.email], html=html, sender=sender)

            if not mail:
                current_app.logger.error("Extensão 'mail' não encontrada. Verifique mail.init_app(app).")
                flash("Servidor de email não configurado. Consulte o administrador.", "danger")
                return redirect(url_for('auth.login'))

            mail.send(msg)
            current_app.logger.info(f"Email de recuperação enviado para {user.email}")
            flash("Link de recuperação enviado para seu email!", "success")
            return redirect(url_for('auth.login'))

        except Exception:
            current_app.logger.exception("Erro ao enviar email de recuperação")
            flash("Erro ao enviar email. Tente novamente mais tarde.", "danger")
            return render_template('auth/esqueci_senha.html')

    return render_template('auth/esqueci_senha.html')


# -------------------------
# ROTA: redefinir_senha
# -------------------------
@auth_bp.route('/redefinir_senha/<token>', methods=['GET', 'POST'])
def redefinir_senha(token):
    email = verify_reset_token(token)
    if not email:
        flash("Link inválido ou expirado.", "danger")
        return redirect(url_for('auth.esqueci_senha'))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Usuário não encontrado.", "danger")
        return redirect(url_for('auth.esqueci_senha'))

    if request.method == 'POST':
        nova_senha = request.form.get('nova_senha')
        confirmar_senha = request.form.get('confirmar_senha')

        if not nova_senha or not confirmar_senha:
            flash("Preencha todos os campos.", "warning")
            return render_template('auth/redefinir_senha.html', token=token)

        if nova_senha != confirmar_senha:
            flash("As senhas não coincidem.", "warning")
            return render_template('auth/redefinir_senha.html', token=token)

        if len(nova_senha) < 6:
            flash("A senha deve ter pelo menos 6 caracteres.", "warning")
            return render_template('auth/redefinir_senha.html', token=token)

        user.password = generate_password_hash(nova_senha, method='pbkdf2:sha256')
        db.session.commit()

        flash("Senha redefinida com sucesso! Faça login com a nova senha.", "success")
        return redirect(url_for('auth.login'))

    return render_template('auth/redefinir_senha.html', token=token)


# -------------------------
# ROTA: Perfil do Usuário
# -------------------------
@auth_bp.route('/perfil')
@login_required
def perfil():
    return render_template('auth/perfil.html', user=current_user)
