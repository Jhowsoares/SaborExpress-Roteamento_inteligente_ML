# algoritmos/simulador.py
from .grafo import simular_a_estrela, construir_grafo
from models import db
from models import Localizacao, Rota  # ajuste caso seu nome seja diferente

class SimuladorAStarService:
    def __init__(self):
        self.passos_cache = None

    def gerar_simulacao(self, inicio_id, destino_id):
        localizacoes = Localizacao.query.all()
        localizacoes_dict = {l.id: l for l in localizacoes}

        # Arestas derivadas de rotas já registradas
        rotas = Rota.query.all()
        arestas = [
            {
                "localizacao_origem_id": r.origem_id,
                "localizacao_destino_id": r.destino_id,
                "distancia_metros": r.distancia_m
            } for r in rotas
        ]

        grafo = construir_grafo(localizacoes, arestas)

        passos = simular_a_estrela(
            grafo,
            localizacoes_dict,
            inicio_id,
            destino_id
        )

        self.passos_cache = passos
        return passos
