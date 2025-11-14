# popular_dados.py
import sys
import os

# Adicione o diretório raiz ao path do Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import Categoria, Produto

def popular_dados():
    """Popula o banco com categorias e produtos de exemplo"""
    
    print("🚀 Iniciando população do banco de dados...")
    
    # Primeiro, criar categorias
    categorias = [
        Categoria(nome="Lanches", descricao="Hambúrgueres artesanais e sanduíches"),
        Categoria(nome="Acompanhamentos", descricao="Porções e complementos"),
        Categoria(nome="Bebidas", descricao="Refrigerantes, sucos e milkshakes"),
        Categoria(nome="Sobremesas", descricao="Doces e sobremesas especiais")
    ]
    
    for categoria in categorias:
        # Verificar se a categoria já existe
        existe = Categoria.query.filter_by(nome=categoria.nome).first()
        if not existe:
            db.session.add(categoria)
    
    db.session.commit()
    print("✅ Categorias criadas!")
    
    # Agora criar produtos
    produtos = [
        # Lanches
        Produto(
            nome="Mega Burger",
            descricao="Pão brioche, hambúrguer 180g artesanal, queijo cheddar, bacon crocante, alface fresca, tomate e molho especial da casa",
            preco=29.90,
            imagem="chicken-supreme.jpg",
            categoria_id=1,
            destaque=True,
            tags="carne,queijo,bacon",
            ativo=True
        ),
        Produto(
            nome="Chicken Supreme",
            descricao="Sanduíche de frango empanado crocante, queijo prato, alface americana, tomate e maionese temperada",
            preco=24.90,
            imagem="chicken-supreme.jpg", 
            categoria_id=1,
            destaque=True,
            tags="frango,empanado",
            ativo=True
        ),
        Produto(
            nome="Burger Clássico",
            descricao="O tradicional: pão australiano, hambúrguer 150g, queijo, alface, tomate e molho barbecue",
            preco=22.90,
            imagem="default.jpg",
            categoria_id=1,
            destaque=False,
            tags="carne,classico",
            ativo=True
        ),
        
        # Acompanhamentos
        Produto(
            nome="Batata Frita Crocante",
            descricao="Porção generosa de batata frita crocante temperada com ervas finas e sal marinho",
            preco=15.90,
            imagem="batata-frita.jpg",
            categoria_id=2,
            destaque=True,
            tags="batata,porcao",
            ativo=True
        ),
        Produto(
            nome="Onion Rings",
            descricao="Anéis de cebola empanados e fritos, crocantes por fora e macios por dentro. Acompanha molho barbecue",
            preco=12.90,
            imagem="onion-rings.jpg",
            categoria_id=2,
            destaque=False,
            tags="cebola,empanado",
            ativo=True
        ),
        
        # Bebidas
        Produto(
            nome="Milkshake de Chocolate",
            descricao="Milkshake cremoso de chocolate belga com calda e chantilly. 400ml",
            preco=18.90,
            imagem="milkshake.jpg",
            categoria_id=3,
            destaque=True,
            tags="chocolate,sobremesa",
            ativo=True
        ),
        Produto(
            nome="Refrigerante Lata",
            descricao="Refrigerante em lata 350ml - escolha entre Coca-Cola, Guaraná Antarctica ou Fanta Laranja",
            preco=6.90,
            imagem="refrigerante.jpg",
            categoria_id=3,
            destaque=False,
            tags="refri,lata",
            ativo=True
        )
    ]
    
    for produto in produtos:
        # Verificar se o produto já existe para evitar duplicatas
        existe = Produto.query.filter_by(nome=produto.nome).first()
        if not existe:
            db.session.add(produto)
            print(f"➕ Adicionando: {produto.nome}")
        else:
            print(f"⏭️  Pulando (já existe): {produto.nome}")
    
    db.session.commit()
    print("✅ Produtos criados!")
    print(f"📦 Total de categorias: {len(categorias)}")
    print(f"🍔 Total de produtos: {len(produtos)}")
    
    # Listar produtos criados
    produtos_criados = Produto.query.all()
    print("\n📋 Produtos no banco:")
    for p in produtos_criados:
        print(f"  - {p.nome} (R$ {p.preco:.2f}) - {p.categoria.nome}")

if __name__ == "__main__":
    with app.app_context():
        popular_dados()