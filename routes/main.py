# routes/main.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from models import db, Produto, Categoria, Pedido, ItemPedido, Localizacao, User
from datetime import datetime
from decimal import Decimal

main_bp = Blueprint('main', __name__)

CART_SESSION_KEY = 'cart'   # chave na session para o carrinho


# -------------------------
# Helpers de carrinho
# -------------------------
def _get_cart() -> dict:
    """Retorna o carrinho atual da session como dict {produto_id: quantidade}"""
    cart = session.get(CART_SESSION_KEY)
    if not isinstance(cart, dict):
        cart = {}
        session[CART_SESSION_KEY] = cart
    return cart


def _save_cart(cart: dict):
    session[CART_SESSION_KEY] = cart
    session.modified = True


def _cart_items_details(cart: dict):
    """Retorna lista de dicts com produto, quantidade e subtotal"""
    items = []
    total = Decimal('0.00')
    for pid_str, qty in cart.items():
        try:
            pid = int(pid_str)
        except Exception:
            continue
        produto = Produto.query.get(pid)
        if not produto:
            continue
        quantidade = int(qty)
        subtotal = Decimal(str(produto.preco)) * quantidade
        items.append({
            'produto': produto,
            'quantidade': quantidade,
            'subtotal': float(subtotal)
        })
        total += subtotal
    return items, float(total)


# -------------------------
# Homepage / Cardápio
# -------------------------
@main_bp.route('/')
@main_bp.route('/homepage')
def homepage():
    destaques = Produto.query.filter_by(destaque=True, ativo=True).limit(6).all()
    categorias = Categoria.query.order_by(Categoria.nome).all()
    total_cart_items = sum(_get_cart().values()) if session.get(CART_SESSION_KEY) else 0
    return render_template('homepage.html', destaques=destaques, categorias=categorias, total_cart_items=total_cart_items)


@main_bp.route('/cardapio')
def cardapio():
    categoria_id = request.args.get('categoria', type=int)
    q = request.args.get('q', '').strip()
    query = Produto.query.filter_by(ativo=True)
    if categoria_id:
        query = query.filter_by(categoria_id=categoria_id)
    if q:
        query = query.filter(Produto.nome.ilike(f'%{q}%'))
    produtos = query.order_by(Produto.nome).all()
    categorias = Categoria.query.order_by(Categoria.nome).all()
    return render_template('cardapio.html', produtos=produtos, categorias=categorias, q=q, categoria_id=categoria_id)

@main_bp.route('/produto/<int:produto_id>')
def produto_detalhe(produto_id):
    """Página de detalhes do produto"""
    produto = Produto.query.get_or_404(produto_id)
    
    # Produtos relacionados (da mesma categoria)
    relacionados = Produto.query.filter(
        Produto.categoria_id == produto.categoria_id,
        Produto.id != produto.id,
        Produto.ativo == True
    ).limit(4).all()
    
    return render_template('produto_detalhe.html', 
                         produto=produto, 
                         relacionados=relacionados)

# -------------------------
# Carrinho
# -------------------------
@main_bp.route('/adicionar_carrinho/<int:produto_id>', methods=['GET', 'POST'])  # Adicione POST
def adicionar_carrinho(produto_id):
    produto = Produto.query.get_or_404(produto_id)
    cart = _get_cart()
    key = str(produto_id)
    cart[key] = cart.get(key, 0) + 1
    _save_cart(cart)
    flash(f'{"1 "+produto.nome} adicionado ao carrinho.', 'success')
    return redirect(request.referrer or url_for('main.cardapio'))


@main_bp.route('/carrinho')
def carrinho():
    cart = _get_cart()
    items, total = _cart_items_details(cart)
    return render_template('carrinho.html', items=items, total=total)


@main_bp.route('/carrinho/atualizar', methods=['POST'])
def atualizar_carrinho():
    # Espera dados no formato form: qty_<produto_id> = quantidade
    cart = {}
    for key, value in request.form.items():
        if key.startswith('qty_'):
            pid = key.replace('qty_', '')
            try:
                qty = int(value)
                if qty > 0:
                    cart[str(int(pid))] = qty
            except Exception:
                continue
    _save_cart(cart)
    flash('Carrinho atualizado.', 'success')
    return redirect(url_for('main.carrinho'))


@main_bp.route('/carrinho/remover/<int:produto_id>', methods=['POST', 'GET'])
def remover_carrinho(produto_id):
    cart = _get_cart()
    key = str(produto_id)
    if key in cart:
        del cart[key]
        _save_cart(cart)
        flash('Item removido do carrinho.', 'info')
    return redirect(url_for('main.carrinho'))


# -------------------------
# Checkout (simples)
# -------------------------
@main_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    cart = _get_cart()
    items, total = _cart_items_details(cart)
    if not items:
        flash('Seu carrinho está vazio.', 'warning')
        return redirect(url_for('main.cardapio'))

    subtotal = total
    taxa_entrega = 5.00  # Taxa fixa de entrega
    total_final = subtotal + taxa_entrega

    if request.method == 'POST':
        # Dados do cliente (simplificado)
        nome = request.form.get('nome') or 'Cliente'
        telefone = request.form.get('telefone') or ''
        endereco = request.form.get('endereco') or ''
        salvar_localizacao = request.form.get('salvar_localizacao') == 'on'

        try:
            # Criar Localizacao (não duplicamos checagem sofisticada aqui)
            local = Localizacao(nome=f'Endereço de {nome}', latitude=0.0, longitude=0.0, tipo='cliente')
            # Se você tiver lat/lon reais, substitua aqui.
            db.session.add(local)
            db.session.flush()  # garantir id

            # Criar Pedido
            pedido = Pedido(
                user_id=None,
                data_pedido=datetime.utcnow(),
                status='pendente',
                total=float(total_final),  # Usar total_final aqui
                tipo_entrega='delivery',
                endereco_entrega=endereco,
                observacoes=request.form.get('observacoes', ''),
                localizacao_entrega_id=local.id
            )
            db.session.add(pedido)
            db.session.flush()

            # Itens do pedido
            for it in items:
                produto = it['produto']
                quantidade = int(it['quantidade'])
                item = ItemPedido(
                    pedido_id=pedido.id,
                    produto_id=produto.id,
                    quantidade=quantidade,
                    preco_unitario=float(produto.preco)
                )
                db.session.add(item)

            db.session.commit()

            # Limpar carrinho
            session.pop(CART_SESSION_KEY, None)
            flash('Pedido realizado com sucesso! Acompanhe na página de pedidos.', 'success')
            return redirect(url_for('main.confirmacao_pedido', pedido_id=pedido.id))

        except Exception as e:
            db.session.rollback()
            current_app.logger.exception("Erro ao processar checkout")
            flash('Erro ao processar pedido. Tente novamente.', 'error')
            return redirect(url_for('main.carrinho'))

    # GET: renderizar checkout
    return render_template('checkout.html', 
                         items=items, 
                         total=total_final,
                         subtotal=subtotal,
                         taxa_entrega=taxa_entrega,
                         carrinho_itens=items)


@main_bp.route('/confirmacao/<int:pedido_id>')
def confirmacao_pedido(pedido_id):
    pedido = Pedido.query.get_or_404(pedido_id)
    itens = ItemPedido.query.filter_by(pedido_id=pedido.id).all()
    return render_template('confirmacao.html', pedido=pedido, itens=itens)


# -------------------------
# Inicializar dados de teste (apenas para desenvolvimento)
# -------------------------
@main_bp.route('/inicializar-dados')
def inicializar_dados():
    """
    Rota de conveniência para popular DB com categorias e produtos de exemplo.
    Use apenas em dev. Não chamada em produção.
    """
    try:
        # criar categorias se não existirem
        if Categoria.query.count() == 0:
            cat1 = Categoria(nome='Lanches', descricao='Hamburgers e acompanhamentos')
            cat2 = Categoria(nome='Bebidas', descricao='Refrigerantes e sucos')
            db.session.add_all([cat1, cat2])
            db.session.commit()
        else:
            cat1 = Categoria.query.filter_by(nome='Lanches').first() or Categoria.query.first()

        # criar produtos de exemplo
        if Produto.query.count() == 0:
            p1 = Produto(nome='X-Burguer', descricao='Delicioso X-Burguer', preco=20.0, imagem='', categoria_id=cat1.id, destaque=True)
            p2 = Produto(nome='Batata Frita', descricao='Porção média', preco=12.0, imagem='', categoria_id=cat1.id)
            p3 = Produto(nome='Coca-Cola 350ml', descricao='', preco=6.0, imagem='', categoria_id=cat2.id)
            db.session.add_all([p1, p2, p3])
            db.session.commit()

        flash('Dados de teste inicializados.', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Erro ao inicializar dados")
        flash('Erro ao inicializar dados.', 'error')

    return redirect(url_for('main.homepage'))
