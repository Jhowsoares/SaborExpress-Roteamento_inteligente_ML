import os
from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail, Message
from models import db
from dotenv import load_dotenv


load_dotenv()

login_manager = LoginManager()
mail = Mail()

def create_app(config_overrides: dict = None) -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # CONFIGURAÇÕES COM VARIÁVEIS DE AMBIENTE
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT'))
    app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True') == 'True'
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Configurações
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', '6876fa3af4282168d656b2c6a4d7ffb8')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///saborexpress.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if config_overrides:
        app.config.update(config_overrides)

    # Inicializar extensões
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    mail = Mail(app)

    # VERIFICAÇÃO DE CONFIGURAÇÃO
    check_configuration(app)

    # Registrar blueprints
    from routes.auth import auth_bp
    from routes.main import main_bp  
    from routes.admin import admin_bp
    from routes.views import roteamento_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(roteamento_bp, url_prefix='/admin/roteamento')

    # User loader DENTRO do app context
    @login_manager.user_loader
    def load_user(user_id):
        from models import User
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None

    return app

def check_configuration(app):
    """Verifica se as configurações críticas estão definidas"""
    missing_configs = []
    
    if not app.config.get('MAIL_USERNAME'):
        missing_configs.append('MAIL_USERNAME')
    if not app.config.get('MAIL_PASSWORD'):
        missing_configs.append('MAIL_PASSWORD')
    
    if missing_configs:
        print(" CONFIGURAÇÃO DE EMAIL INCOMPLETA:")
        for config in missing_configs:
            print(f"   - {config} não configurado")
        print(" Dica: Crie um arquivo .env com as credenciais do Mailtrap (ou do provedor desejado).")
    else:
        print(" Configuração de email verificada com sucesso!")

# Criar app
app = create_app()

# Criar tabelas
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', '1') == '1'
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=debug_mode, port=port)