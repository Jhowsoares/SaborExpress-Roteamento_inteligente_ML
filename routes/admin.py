# routes/admin.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, send_file, current_app, make_response
from models import db, User, Produto, Categoria, Pedido, ItemPedido
from datetime import datetime
import io
import csv
from functools import wraps

admin_bp = Blueprint('admin', __name__, template_folder='templates/admin', url_prefix='/admin')

# -------------------------
# Helpers / Decorators
# -------------------------
def admin_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Acesso restrito. Faça login como administrador.', 'error')
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    return decorated

def _safe_commit():
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise

# -------------------------
# Login / Logout
# -------------------------
@admin_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    """
    Login simples de admin. Em produção substitua por verificação real.
    """
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        # Opções:
        # 1) tentar encontrar usuário administrador no banco (User.is_admin)
        # 2) fallback dev: aceitar 'admin' / 'admin'
        user = None
        try:
            user = User.query.filter_by(username=username).first()
        except Exception:
            user = None

        valid = False
        if user:
            # se tiver coluna de senha sem hash (dev), comparar diretamente;
            # se tiver hash, você deve adaptar para usar check_password_hash
            if getattr(user, 'password', None) and user.password == password:
                valid = True
        else:
            # fallback dev
            if username == 'admin' and password == 'admin':
                valid = True

        if valid:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            flash('Login realizado com sucesso.', 'success')
            return redirect(url_for('admin.admin_dashboard'))
        else:
            flash('Credenciais inválidas.', 'error')
            return redirect(url_for('admin.admin_login'))

    return render_template('admin/login.html')

@admin_bp.route('/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    flash('Desconectado do painel.', 'success')
    return redirect(url_for('admin.admin_login'))

# -------------------------
# Dashboard
# -------------------------
@admin_bp.route('/')
@admin_login_required
def admin_dashboard():
    # Estatísticas simples
    total_pedidos = Pedido.query.count()
    pedidos_24h = Pedido.query.filter(Pedido.data_pedido >= datetime.utcnow().replace(hour=0, minute=0, second=0)).count()
    total_entregadores = 0
    try:
        from models import Entregador
        total_entregadores = Entregador.query.filter_by(disponivel=True).count()
    except Exception:
        total_entregadores = 0

    # distancia média fake (se existir métrica em DB, substitua)
    distancia_media_km = None
    # últimos pedidos
    ultimos_pedidos = Pedido.query.order_by(Pedido.data_pedido.desc()).limit(8).all()

    stats = {
        'pedidos': total_pedidos,
        'pedidos_24h': pedidos_24h,
        'entregadores': total_entregadores,
        'distancia_media_km': distancia_media_km or 0
    }

    return render_template('admin/dashboard.html',
                           stats=stats,
                           ultimos_pedidos=ultimos_pedidos)

# -------------------------
# Pedidos
# -------------------------
@admin_bp.route('/pedidos')
@admin_login_required
def admin_pedidos():
    pedidos = Pedido.query.order_by(Pedido.data_pedido.desc()).all()
    return render_template('admin/pedidos.html', pedidos=pedidos)

@admin_bp.route('/pedido/<int:pedido_id>')
@admin_login_required
def admin_pedido_detalhe(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    return render_template('admin/pedido_detalhe.html', pedido=pedido)

@admin_bp.route('/pedido/<int:pedido_id>/status', methods=['POST'])
@admin_login_required
def admin_atualizar_status(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    novo_status = request.form.get('status')
    if not novo_status:
        flash('Status inválido.', 'error')
        return redirect(url_for('admin.admin_pedido_detalhe', pedido_id=pedido.id))
    pedido.status = novo_status
    try:
        _safe_commit()
        flash('Status atualizado.', 'success')
    except Exception as e:
        flash(f'Erro ao atualizar status: {e}', 'error')
    return redirect(url_for('admin.admin_pedido_detalhe', pedido_id=pedido.id))

# Exportar pedidos CSV
@admin_bp.route('/pedidos/exportar')
@admin_login_required
def exportar_pedidos_csv():
    pedidos = Pedido.query.order_by(Pedido.data_pedido.desc()).all()

    proxy = io.StringIO()
    writer = csv.writer(proxy)
    # Cabeçalho
    writer.writerow(['id', 'user_id', 'data_pedido', 'status', 'total', 'endereco_entrega'])

    for p in pedidos:
        writer.writerow([
            p.id,
            getattr(p.user, 'id', '') if getattr(p, 'user', None) else '',
            p.data_pedido.strftime('%Y-%m-%d %H:%M:%S') if p.data_pedido else '',
            p.status,
            "%.2f" % (p.total or 0),
            p.endereco_entrega or ''
        ])

    mem = io.BytesIO()
    mem.write(proxy.getvalue().encode('utf-8'))
    mem.seek(0)
    proxy.close()

    filename = f'pedidos_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
    return send_file(mem, as_attachment=True, download_name=filename, mimetype='text/csv')

# -------------------------
# Produtos
# -------------------------
@admin_bp.route('/produtos')
@admin_login_required
def admin_produtos():
    produtos = Produto.query.order_by(Produto.id.desc()).all()
    return render_template('admin/produtos.html', produtos=produtos)

@admin_bp.route('/produto/novo', methods=['GET', 'POST'])
@admin_login_required
def admin_produto_novo():
    categorias = Categoria.query.order_by(Categoria.nome).all()
    if request.method == 'POST':
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        preco = request.form.get('preco') or 0
        categoria_id = request.form.get('categoria_id') or None
        imagem = request.form.get('imagem') or None
        ativo = bool(request.form.get('ativo'))

        produto = Produto(nome=nome, descricao=descricao, preco=float(preco), imagem=imagem or '', categoria_id=(int(categoria_id) if categoria_id else None), ativo=ativo)
        db.session.add(produto)
        try:
            _safe_commit()
            flash('Produto criado.', 'success')
            return redirect(url_for('admin.admin_produtos'))
        except Exception as e:
            flash(f'Erro ao criar produto: {e}', 'error')
            return redirect(url_for('admin.admin_produto_novo'))

    return render_template('admin/produto_form.html', produto=None, categorias=categorias, form_action=url_for('admin.admin_produto_novo'))

@admin_bp.route('/produto/<int:produto_id>/editar', methods=['GET', 'POST'])
@admin_login_required
def admin_produto_editar(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    categorias = Categoria.query.order_by(Categoria.nome).all()

    if request.method == 'POST':
        produto.nome = request.form.get('nome') or produto.nome
        produto.descricao = request.form.get('descricao') or produto.descricao
        produto.preco = float(request.form.get('preco') or produto.preco)
        produto.categoria_id = int(request.form.get('categoria_id')) if request.form.get('categoria_id') else produto.categoria_id
        produto.imagem = request.form.get('imagem') or produto.imagem
        produto.ativo = bool(request.form.get('ativo'))
        try:
            _safe_commit()
            flash('Produto atualizado.', 'success')
            return redirect(url_for('admin.admin_produtos'))
        except Exception as e:
            flash(f'Erro ao atualizar produto: {e}', 'error')

    return render_template('admin/produto_form.html', produto=produto, categorias=categorias, form_action=url_for('admin.admin_produto_editar', produto_id=produto.id))

@admin_bp.route('/produto/<int:produto_id>/remover', methods=['POST'])
@admin_login_required
def admin_produto_remover(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    try:
        db.session.delete(produto)
        _safe_commit()
        flash('Produto removido.', 'success')
    except Exception as e:
        flash(f'Erro ao remover produto: {e}', 'error')
    return redirect(url_for('admin.admin_produtos'))

# -------------------------
# Pequenas rotas utilitárias
# -------------------------
@admin_bp.route('/perfil')
@admin_login_required
def admin_perfil():
    username = session.get('admin_username')
    user = None
    try:
        user = User.query.filter_by(username=username).first() if username else None
    except Exception:
        user = None
    return render_template('admin/perfil.html', user=user)
