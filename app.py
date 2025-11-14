# app.py — VERSÃO CORRIGIDA (imports atualizados)
import os
from flask import Flask
from flask_login import LoginManager
from models import db

login_manager = LoginManager()

def create_app(config_overrides: dict = None) -> Flask:
    app = Flask(__name__, static_folder="static", template_folder="templates")
    
    # Configurações
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', '6876fa3af4282168d656b2c6a4d7ffb8')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///saborexpress.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    if config_overrides:
        app.config.update(config_overrides)

    # Inicializar extensões
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'

    # Registrar blueprints - IMPORTAR DOS ARQUIVOS CORRETOS
    from routes.auth import auth_bp
    from routes.main import main_bp  
    from routes.admin import admin_bp
    from routes.views import roteamento_bp  # MUDANÇA AQUI!

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(roteamento_bp, url_prefix='/admin/roteamento')

    # User loader DENTRO do app context
    @login_manager.user_loader
    def load_user(user_id):
        from models import User  # Import aqui para evitar circular
        try:
            return User.query.get(int(user_id))
        except Exception:
            return None

    return app

# Criar app instance
app = create_app()

# Criar tabelas
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    debug_mode = os.getenv('FLASK_DEBUG', '1') == '1'
    port = int(os.getenv('PORT', 5000))
    app.run(debug=debug_mode, port=port, host='0.0.0.0')