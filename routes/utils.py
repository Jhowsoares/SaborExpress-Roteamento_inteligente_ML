# routes/utils.py - UTILS CORRETO PARA API
from flask import session, redirect, url_for, flash
from functools import wraps
from models import Localizacao, Pedido, Entregador, Rota

# ---------------------------
# Decorators
# ---------------------------
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Acesso restrito. Faça login como administrador.', 'error')
            return redirect(url_for('admin.admin_login'))
        return f(*args, **kwargs)
    return decorated

# ---------------------------
# Serializers JSON-Safe
# ---------------------------
def serialize_localizacao(loc):
    """Serializa Localizacao para JSON"""
    if not loc:
        return None
    return {
        'id': loc.id,
        'nome': loc.nome,
        'latitude': float(loc.latitude),
        'longitude': float(loc.longitude),
        'tipo': loc.tipo
    }

def serialize_pedido(pedido):
    """Serializa Pedido para JSON"""
    if not pedido:
        return None
    return {
        'id': pedido.id,
        'user_id': pedido.user_id,
        'status': pedido.status,
        'total': float(pedido.total),
        'endereco_entrega': pedido.endereco_entrega,
        'localizacao_entrega_id': pedido.localizacao_entrega_id,
        'data_pedido': pedido.data_pedido.isoformat() if pedido.data_pedido else None
    }

def serialize_entregador(entregador):
    """Serializa Entregador para JSON"""
    if not entregador:
        return None
    return {
        'id': entregador.id,
        'nome': entregador.nome,
        'veiculo': entregador.veiculo,
        'disponivel': entregador.disponivel,
        'localizacao_atual_id': entregador.localizacao_atual_id
    }

def serialize_rota(rota):
    """Serializa Rota para JSON"""
    if not rota:
        return None
    return {
        'id': rota.id,
        'origem_id': rota.localizacao_origem_id,
        'destino_id': rota.localizacao_destino_id,
        'distancia_metros': rota.distancia_metros,
        'tempo_minutos': rota.tempo_minutos
    }

def serialize_otimizador_result(resultado):
    """Serializa resultado do otimizador para JSON"""
    if not resultado:
        return {}
    
    return {
        'clusters_otimizados': resultado.get('clusters_otimizados', []),
        'metricas': resultado.get('metricas', {}),
        'parametros': resultado.get('parametros', {}),
        'data_execucao': resultado.get('data_execucao')
    }

def montar_grafo_data(localizacoes, rotas):
    """Monta estrutura de grafo para visualização"""
    nos = [serialize_localizacao(loc) for loc in localizacoes]
    arestas = [serialize_rota(rota) for rota in rotas]
    
    return {
        'nos': nos,
        'arestas': arestas
    }