# routes/roteamento/views.py
from flask import (
    Blueprint, render_template, request, flash,
    redirect, url_for, session, jsonify, current_app
)
from functools import wraps
import traceback

# Import modelos e módulos principais (ajuste import se sua árvore for diferente)
from models import db, Pedido, Localizacao, Entregador, Rota
from algoritmos.kmeans import salvar_resultado_kmeans, buscar_resultado_kmeans, buscar_ultimo_resultado_kmeans
from algoritmos.otimizador_integrado import OtimizadorEntregas
from algoritmos.grafo import construir_grafo, haversine_m
from algoritmos.grafo_layout import GeradorLayoutGrafo

roteamento_bp = Blueprint('roteamento', __name__, template_folder='templates/admin/roteamento')

# ---------------------------
# Helpers / Decorators
# ---------------------------
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Por favor, faça login como administrador para acessar.', 'warning')
            return redirect(url_for('admin.admin_login') if 'admin.admin_login' in current_app.view_functions else url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

def safe_serialize_localizacao(loc):
    if loc is None:
        return None
    try:
        return {
            'id': int(getattr(loc, 'id', None)),
            'nome': getattr(loc, 'nome', None),
            'latitude': float(getattr(loc, 'latitude', 0.0)),
            'longitude': float(getattr(loc, 'longitude', 0.0)),
            'tipo': getattr(loc, 'tipo', None)
        }
    except Exception:
        return {'id': getattr(loc, 'id', None)}

def safe_serialize_pedido(p):
    if p is None:
        return None
    try:
        return {
            'id': int(getattr(p, 'id', None)),
            'user_id': getattr(p, 'user_id', None),
            'data_pedido': getattr(p, 'data_pedido').isoformat() if getattr(p, 'data_pedido', None) else None,
            'status': getattr(p, 'status', None),
            'total': float(getattr(p, 'total', 0.0) or 0.0),
            'tipo_entrega': getattr(p, 'tipo_entrega', None),
            'endereco_entrega': getattr(p, 'endereco_entrega', None),
            'observacoes': getattr(p, 'observacoes', None),
            'localizacao_entrega_id': getattr(p, 'localizacao_entrega_id', None)
        }
    except Exception:
        return {'id': getattr(p, 'id', None)}

def safe_serialize_entregador(e):
    if e is None:
        return None
    try:
        return {
            'id': int(getattr(e, 'id', None)),
            'nome': getattr(e, 'nome', None),
            'veiculo': getattr(e, 'veiculo', None),
            'disponivel': bool(getattr(e, 'disponivel', False)),
            'localizacao_atual_id': getattr(e, 'localizacao_atual_id', None)
        }
    except Exception:
        return {'id': getattr(e, 'id', None)}

# ---------------------------
# Views / Endpoints
# ---------------------------

@roteamento_bp.route('/')
@admin_required
def index():
    """Página principal do módulo de roteamento (summary + botão executar)"""
    try:
        pedidos_pendentes = Pedido.query.filter_by(status='pendente').all()
        entregadores_disponiveis = Entregador.query.filter_by(disponivel=True).all()
        resultado_kmeans = None
        try:
            resultado_kmeans = buscar_ultimo_resultado_kmeans()
        except Exception:
            resultado_kmeans = None

        return render_template(
            'admin/roteamento/index.html',
            pedidos_pendentes=pedidos_pendentes,
            entregadores_disponiveis=entregadores_disponiveis,
            resultado_kmeans=resultado_kmeans,
            ultima_otimizacao=resultado_kmeans.get('data_execucao')[:16] if resultado_kmeans and isinstance(resultado_kmeans, dict) and resultado_kmeans.get('data_execucao') else 'Nunca'
        )
    except Exception as e:
        current_app.logger.exception("Erro ao abrir index do roteamento")
        flash(f'Erro interno: {e}', 'error')
        return render_template('admin/roteamento/index.html', pedidos_pendentes=[], entregadores_disponiveis=[], resultado_kmeans=None)


@roteamento_bp.route('/executar-kmeans', methods=['POST'])
@admin_required
def executar_kmeans_route():
    """Rota de ação para executar KMeans (ponto de entrada opcional)"""
    try:
        num_clusters = int(request.form.get('num_clusters', 3))
        max_entregas = int(request.form.get('max_entregas', 5))

        # Aqui manteremos a lógica simples: reutilizar OtimizadorEntregas para executar tudo de uma vez
        pedidos = Pedido.query.filter_by(status='pendente').all()
        localizacoes = Localizacao.query.all()
        entregadores = Entregador.query.filter_by(disponivel=True).all()
        localizacoes_dict = {loc.id: loc for loc in localizacoes}

        ot = OtimizadorEntregas()
        resultado = ot.otimizar_rotas_completas(
            pedidos=pedidos,
            localizacoes_dict=localizacoes_dict,
            entregadores=entregadores,
            num_clusters=num_clusters,
            max_entregas_por_cluster=max_entregas
        )

        # salvar resultado
        exec_id = salvar_resultado_kmeans(resultado) if 'salvar_resultado_kmeans' in globals() or salvar_resultado_kmeans else None

        flash('K-Means e otimização executados com sucesso.', 'success')
        if exec_id:
            return redirect(url_for('roteamento.resultado_kmeans', execucao_id=exec_id))
        else:
            return redirect(url_for('roteamento.index'))
    except Exception as e:
        current_app.logger.exception("Erro ao executar kmeans")
        flash(f'Erro ao executar K-Means: {e}', 'error')
        return redirect(url_for('roteamento.index'))


@roteamento_bp.route('/otimizar-completo', methods=['POST'])
@admin_required
def otimizar_rotas_completas():
    """Executa otimização completa (KMeans + A*) e salva resultado"""
    try:
        num_clusters = int(request.form.get('num_clusters', 3))
        max_entregas = int(request.form.get('max_entregas', 5))

        pedidos_pendentes = Pedido.query.filter_by(status='pendente').all()
        localizacoes = Localizacao.query.all()
        entregadores_disponiveis = Entregador.query.filter_by(disponivel=True).all()
        rotas_db = Rota.query.all() if hasattr(Rota, 'query') else []

        localizacoes_dict = {loc.id: loc for loc in localizacoes}

        # Construir arestas (preferir rotas do banco, senão usar haversine)
        arestas = []
        if rotas_db:
            for r in rotas_db:
                try:
                    arestas.append({
                        'localizacao_origem_id': int(r.localizacao_origem_id),
                        'localizacao_destino_id': int(r.localizacao_destino_id),
                        'distancia_metros': float(r.distancia_metros)
                    })
                except Exception:
                    continue
        else:
            # fallback: grafo completo via haversine
            locs_list = [l for l in localizacoes if hasattr(l, 'id') and hasattr(l, 'latitude') and hasattr(l, 'longitude')]
            for a in locs_list:
                for b in locs_list:
                    if a.id == b.id:
                        continue
                    arestas.append({
                        'localizacao_origem_id': int(a.id),
                        'localizacao_destino_id': int(b.id),
                        'distancia_metros': haversine_m(a.latitude, a.longitude, b.latitude, b.longitude)
                    })

        grafo = construir_grafo(localizacoes, arestas)
        # montar container esperado pelo otimizador (compatível com sua implementação)
        local_container = {
            'locs': localizacoes_dict,
            'grafo': grafo
        }

        ot = OtimizadorEntregas()
        resultado = ot.otimizar_rotas_completas(
            pedidos=pedidos_pendentes,
            localizacoes_dict=local_container,
            entregadores=entregadores_disponiveis,
            num_clusters=num_clusters,
            max_entregas_por_cluster=max_entregas
        )

        exec_id = None
        try:
            exec_id = salvar_resultado_kmeans(resultado)
        except Exception:
            current_app.logger.warning("salvar_resultado_kmeans não disponível ou falhou")

        flash('Otimização completa executada com sucesso.', 'success')
        if exec_id:
            return redirect(url_for('roteamento.resultado_kmeans', execucao_id=exec_id))
        else:
            return redirect(url_for('roteamento.index'))

    except Exception as e:
        current_app.logger.exception("Erro na otimização completa")
        flash(f'Erro na otimização: {e}', 'error')
        return redirect(url_for('roteamento.index'))


@roteamento_bp.route('/resultado/<execucao_id>')
@admin_required
def resultado_kmeans(execucao_id):
    """Mostra resultado da otimização"""
    try:
        # Em vez de buscar do banco, vamos executar a otimização diretamente
        from models import Pedido, Localizacao, Entregador
        from algoritmos.otimizador_integrado import OtimizadorEntregas
        
        pedidos = Pedido.query.filter_by(status='pendente').all()
        localizacoes = Localizacao.query.all()
        entregadores = Entregador.query.filter_by(disponivel=True).all()
        localizacoes_dict = {loc.id: loc for loc in localizacoes}
        
        ot = OtimizadorEntregas()
        resultado = ot.otimizar_rotas_completas(
            pedidos=pedidos,
            localizacoes_dict=localizacoes_dict,
            entregadores=entregadores,
            num_clusters=min(5, len(pedidos)),
            max_entregas_por_cluster=5
        )
        
        return render_template('admin/roteamento/resultado.html', resultado=resultado)
        
    except Exception as e:
        current_app.logger.exception("Erro ao carregar resultado_kmeans")
        flash(f'Erro ao carregar resultado: {e}', 'error')
        return redirect(url_for('roteamento.index'))

@roteamento_bp.route('/visualizacao-unificada')
@admin_required
def visualizacao_unificada():
    """Página que embute mapa/grafo/métricas (iframe-based)"""
    try:
        # tenta buscar último resultado para preencher dados resumidos
        resultado = buscar_ultimo_resultado_kmeans() if 'buscar_ultimo_resultado_kmeans' in globals() else None
        tem_dados = bool(resultado)
        total_pedidos = resultado.get('parametros', {}).get('total_pedidos', 0) if resultado else 0
        total_entregadores = resultado.get('parametros', {}).get('total_entregadores', 0) if resultado else 0

        return render_template(
            'admin/roteamento/visualizacao.html',
            tem_dados=tem_dados,
            total_pedidos=total_pedidos,
            total_entregadores=total_entregadores,
            relatorio=resultado or {}
        )
    except Exception as e:
        current_app.logger.exception("Erro visualizacao_unificada")
        flash(f'Erro ao abrir visualização: {e}', 'error')
        return redirect(url_for('roteamento.index'))


@roteamento_bp.route('/mapa')
@admin_required
def mapa_rotas():

    """Mapa simplificado"""
    try:
        # Dados básicos para o mapa
        restaurante = {'lat': -23.5505, 'lng': -46.6333, 'nome': 'Sabor Express'}
        clientes = [
            {'lat': -23.5605, 'lng': -46.6433, 'nome': 'Cliente 1'},
            {'lat': -23.5405, 'lng': -46.6233, 'nome': 'Cliente 2'},
            {'lat': -23.5455, 'lng': -46.6383, 'nome': 'Cliente 3'},
        ]
        
        return render_template(
            'admin/roteamento/mapa_simple.html',  # ← Mude para o novo template
            restaurante=restaurante,
            clientes=clientes
        )
    except Exception as e:
        current_app.logger.exception("Erro mapa_rotas")
        flash(f'Erro ao abrir mapa: {e}', 'error')
        return redirect(url_for('roteamento.index'))
    

@roteamento_bp.route('/grafo')
@admin_required
def grafo_rotas():
    """Renderiza visualização de grafo (template) — os dados são carregados via /api/grafo"""
    try:
        return render_template('admin/roteamento/grafo.html', grafo_data={})
    except Exception as e:
        current_app.logger.exception("Erro grafo_rotas")
        flash(f'Erro ao abrir grafo: {e}', 'error')
        return redirect(url_for('roteamento.index'))

# @roteamento_bp.route('/grafo-interativo')
# @admin_required
# def grafo_interativo():
#     """Página com visualização interativa do grafo"""
#     try:
#         from algoritmos.visualizador_grafo import VisualizadorGrafo
#         from models import Pedido, Localizacao, Entregador
#         from algoritmos.otimizador_integrado import OtimizadorEntregas
        
#         # Executar otimização para obter dados
#         pedidos = Pedido.query.filter_by(status='pendente').all()
#         localizacoes = Localizacao.query.all()
#         entregadores = Entregador.query.filter_by(disponivel=True).all()
#         localizacoes_dict = {loc.id: loc for loc in localizacoes}
        
#         ot = OtimizadorEntregas()
#         resultado = ot.otimizar_rotas_completas(
#             pedidos=pedidos,
#             localizacoes_dict=localizacoes_dict,
#             entregadores=entregadores
#         )
        
#         # Gerar visualização
#         visualizador = VisualizadorGrafo()
#         imagem_grafo = visualizador.visualizar_rotas_otimizadas(
#             resultado.get('clusters_otimizados', []),
#             localizacoes_dict,
#             entregadores
#         )
        
#         return render_template(
#             'admin/roteamento/grafo_interativo.html',
#             imagem_grafo=imagem_grafo,
#             clusters=resultado.get('clusters_otimizados', []),
#             metricas=resultado.get('metricas', {})
#         )
        
#     except Exception as e:
#         current_app.logger.exception("Erro no grafo interativo")
#         flash(f'Erro ao gerar visualização: {e}', 'error')
#         return redirect(url_for('roteamento.index'))

@roteamento_bp.route('/grafo-interativo')
@admin_required
def grafo_interativo():
    """Página com visualização estática do grafo (formato original)"""
    try:
        from algoritmos.visualizador_grafo import VisualizadorGrafo
        from models import Pedido, Localizacao, Entregador
        from algoritmos.otimizador_integrado import OtimizadorEntregas
        
        # Executar otimização para obter dados reais
        pedidos = Pedido.query.filter_by(status='pendente').all()
        localizacoes = Localizacao.query.all()
        entregadores = Entregador.query.filter_by(disponivel=True).all()
        localizacoes_dict = {loc.id: loc for loc in localizacoes}
        
        print(f"🔧 Processando {len(pedidos)} pedidos, {len(localizacoes)} localizações...")
        
        ot = OtimizadorEntregas()
        resultado = ot.otimizar_rotas_completas(
            pedidos=pedidos,
            localizacoes_dict=localizacoes_dict,
            entregadores=entregadores
        )
        
        # Gerar visualização ESTÁTICA
        visualizador = VisualizadorGrafo(grid_size=10, fator_escala_km=0.5)
        imagem_grafo = visualizador.visualizar_rotas_otimizadas(
            resultado.get('clusters_otimizados', []),
            localizacoes_dict,
            entregadores
        )
        
        return render_template(
            'admin/roteamento/grafo_interativo.html',
            imagem_grafo=imagem_grafo,
            clusters=resultado.get('clusters_otimizados', []),
            metricas=resultado.get('metricas', {})
        )
        
    except Exception as e:
        current_app.logger.exception("Erro no grafo interativo")
        flash(f'Erro ao gerar visualização: {e}', 'error')
        return redirect(url_for('roteamento.index'))

@roteamento_bp.route('/metricas')
@admin_required
def metricas_dashboard():
    """Métricas simplificadas"""
    try:
        metricas = {
            'total_pedidos': 12,
            'pedidos_entregues': 10,
            'tempo_medio_entrega': 25.5,
            'distancia_media_km': 4.2,
            'eficiencia_entregas': 0.83
        }
        return render_template('admin/roteamento/metricas_simple.html', metricas=metricas)
    except Exception as e:
        current_app.logger.exception("Erro metricas_dashboard")
        flash(f'Erro ao carregar métricas: {e}', 'error')
        return redirect(url_for('roteamento.index'))

@roteamento_bp.route('/simular-pedidos', methods=['POST'])
@admin_required
def simular_pedidos():
    """Endpoint para criar pedidos de teste"""
    try:
        quantidade = int(request.form.get('quantidade', 5))
        # Lógica simples de simulação - você pode expandir depois
        from models import Pedido, Localizacao
        from datetime import datetime
        
        pedidos_criados = 0
        for i in range(quantidade):
            # Criar localização fake
            loc = Localizacao(
                nome=f'Cliente Teste {i+1}',
                latitude=-23.5505 + (i * 0.01),  # Coordenadas perto de SP
                longitude=-46.6333 + (i * 0.01),
                tipo='cliente'
            )
            db.session.add(loc)
            db.session.flush()
            
            # Criar pedido
            pedido = Pedido(
                user_id=None,
                data_pedido=datetime.utcnow(),
                status='pendente',
                total=50.0 + (i * 10),
                tipo_entrega='delivery',
                endereco_entrega=f'Endereço teste {i+1}',
                localizacao_entrega_id=loc.id
            )
            db.session.add(pedido)
            pedidos_criados += 1
        
        db.session.commit()
        flash(f'{pedidos_criados} pedidos de teste criados com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Erro ao simular pedidos")
        flash(f'Erro ao criar pedidos de teste: {e}', 'error')
    
    return redirect(url_for('roteamento.index'))

@roteamento_bp.route('/limpar-pedidos-pendentes', methods=['POST'])
@admin_required
def limpar_pedidos_pendentes():
    """Limpa apenas pedidos pendentes"""
    try:
        from models import Pedido
        pedidos = Pedido.query.filter_by(status='pendente').all()
        count = 0
        
        for pedido in pedidos:
            # Limpar itens do pedido primeiro (se existirem)
            from models import ItemPedido
            ItemPedido.query.filter_by(pedido_id=pedido.id).delete()
            # Deletar pedido
            db.session.delete(pedido)
            count += 1
        
        db.session.commit()
        flash(f'{count} pedidos pendentes removidos!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Erro ao limpar pedidos pendentes")
        flash(f'Erro ao limpar pedidos: {e}', 'error')
    
    return redirect(url_for('roteamento.index'))

@roteamento_bp.route('/limpar-pedidos-testes', methods=['POST'])
@admin_required
def limpar_pedidos_testes():
    """Limpa pedidos de teste (baseado no endereço)"""
    try:
        from models import Pedido, Localizacao
        # Encontrar pedidos com "teste" no endereço
        pedidos_testes = Pedido.query.filter(
            Pedido.endereco_entrega.like('%teste%') | 
            Pedido.endereco_entrega.like('%Teste%')
        ).all()
        
        count = 0
        for pedido in pedidos_testes:
            # Limpar itens
            from models import ItemPedido
            ItemPedido.query.filter_by(pedido_id=pedido.id).delete()
            # Deletar localização associada se for de teste
            if pedido.localizacao_entrega_id:
                loc = Localizacao.query.get(pedido.localizacao_entrega_id)
                if loc and 'teste' in loc.nome.lower():
                    db.session.delete(loc)
            # Deletar pedido
            db.session.delete(pedido)
            count += 1
        
        db.session.commit()
        flash(f'{count} pedidos de teste removidos!', 'success')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Erro ao limpar pedidos de teste")
        flash(f'Erro ao limpar pedidos de teste: {e}', 'error')
    
    return redirect(url_for('roteamento.index'))

@roteamento_bp.route('/limpar-pedidos', methods=['POST'])
@admin_required
def limpar_pedidos():
    """Limpa TODOS os pedidos (cuidado!)"""
    try:
        from models import Pedido, ItemPedido, Localizacao
        
        # Limpar itens primeiro
        ItemPedido.query.delete()
        
        # Limpar pedidos
        pedidos_count = Pedido.query.count()
        Pedido.query.delete()
        
        # Limpar localizações de clientes (opcional)
        Localizacao.query.filter_by(tipo='cliente').delete()
        
        db.session.commit()
        flash(f'Todos os pedidos ({pedidos_count}) foram removidos!', 'warning')
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Erro ao limpar todos os pedidos")
        flash(f'Erro ao limpar pedidos: {e}', 'error')
    
    return redirect(url_for('roteamento.index'))

@roteamento_bp.route('/api/grafo')
@admin_required
def api_grafo():
    """API para dados do grafo com dados reais da otimização - VERSÃO CORRIGIDA"""
    try:
        from models import Pedido, Localizacao, Entregador
        from algoritmos.otimizador_integrado import OtimizadorEntregas
        
        pedidos = Pedido.query.filter_by(status='pendente').all()
        localizacoes = Localizacao.query.all()
        entregadores = Entregador.query.filter_by(disponivel=True).all()
        localizacoes_dict = {loc.id: loc for loc in localizacoes}
        
        # Usar serializers existentes
        from routes.utils import serialize_localizacao, serialize_pedido
        
        nos = []
        arestas = []
        
        # Adicionar nós (localizações reais)
        for loc in localizacoes:
            nos.append(serialize_localizacao(loc))
        
        # Se temos pedidos, executar otimização para obter rotas
        if pedidos:
            ot = OtimizadorEntregas()
            resultado = ot.otimizar_rotas_completas(
                pedidos=pedidos,
                localizacoes_dict=localizacoes_dict,
                entregadores=entregadores
            )
            
            # Adicionar arestas baseadas nos clusters otimizados
            for i, cluster in enumerate(resultado.get('clusters_otimizados', [])):
                sequencia = cluster.get('sequencia_otimizada', [])
                if len(sequencia) > 1:
                    for j in range(len(sequencia) - 1):
                        arestas.append({
                            'source': sequencia[j],
                            'target': sequencia[j + 1],
                            'cluster': i + 1,
                            'tipo': 'rota_otimizada'
                        })
        
        return jsonify({
            'nos': nos,
            'arestas': arestas,
            'total_nos': len(nos),
            'total_arestas': len(arestas),
            'status': 'success'
        })
        
    except Exception as e:
        current_app.logger.error(f"Erro api_grafo: {e}")
        return jsonify({'error': 'Erro interno', 'details': str(e)}), 500

# Fim do arquivo
