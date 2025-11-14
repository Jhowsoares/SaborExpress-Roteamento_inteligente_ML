# algoritmos/kmeans.py
import math
import numpy as np
from typing import List, Dict, Any
from models import Pedido, Localizacao

class ClusterizadorKMeans:
    """Implementa K-Means para agrupamento inteligente de entregas"""
    
    def __init__(self, n_clusters: int = None):
        self.n_clusters = n_clusters
        self.centroides = None
        
    @staticmethod
    def calcular_distancia(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcula distância em metros entre coordenadas"""
        R = 6371000
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def preparar_dados(self, pedidos: List[Pedido], localizacoes_dict: Dict[int, Localizacao]) -> np.ndarray:
        """Prepara dados dos pedidos para clustering"""
        coordenadas = []
        
        for pedido in pedidos:
            # Usar localização do pedido ou fallback para restaurante
            loc_id = getattr(pedido, 'localizacao_entrega_id', 1)
            
            if loc_id in localizacoes_dict:
                localizacao = localizacoes_dict[loc_id]
                
                # Incluir coordenadas e valor normalizado do pedido
                valor_normalizado = min(pedido.total / 100, 1.0)
                
                coordenadas.append([
                    localizacao.latitude,
                    localizacao.longitude,
                    valor_normalizado
                ])
        
        return np.array(coordenadas) if coordenadas else np.array([])
    
    def calcular_clusters_otimos(self, dados: np.ndarray, max_clusters: int = 8) -> int:
        """Calcula número ótimo de clusters usando método simplificado"""
        if len(dados) <= 1:
            return 1
        if len(dados) <= 3:
            return min(len(dados), 2)
            
        # Método simplificado: baseado na quantidade de pedidos
        # 1 cluster para até 5 pedidos, depois 1 cluster a cada 3-5 pedidos adicionais
        n_clusters = max(1, min(len(dados) // 3, max_clusters))
        return min(n_clusters, len(dados))
    
    def clusterizar(self, pedidos: List[Pedido], localizacoes_dict: Dict[int, Localizacao]) -> List[Dict]:
        """Agrupa pedidos em clusters geográficos"""
        if not pedidos:
            return []
            
        # Preparar dados
        dados = self.preparar_dados(pedidos, localizacoes_dict)
        
        if len(dados) == 0:
            return []
            
        # Determinar número de clusters
        if self.n_clusters is None:
            n_clusters = self.calcular_clusters_otimos(dados)
        else:
            n_clusters = min(self.n_clusters, len(dados))
        
        if n_clusters <= 0:
            n_clusters = 1
        
        # K-Means manual (simplificado para evitar dependência do scikit-learn)
        clusters = self._kmeans_manual(dados, pedidos, localizacoes_dict, n_clusters)
        
        return clusters
    
    def _kmeans_manual(self, dados: np.ndarray, pedidos: List[Pedido], 
                      localizacoes_dict: Dict, n_clusters: int) -> List[Dict]:
        """Implementação simplificada do K-Means"""
        # Inicializar centroides aleatórios
        np.random.seed(42)
        indices_centroides = np.random.choice(len(dados), n_clusters, replace=False)
        centroides = dados[indices_centroides, :2]  # Apenas coordenadas
        
        for _ in range(10):  # Número máximo de iterações
            # Atribuir pontos aos clusters mais próximos
            clusters = [[] for _ in range(n_clusters)]
            
            for i, ponto in enumerate(dados):
                distancias = []
                for centroide in centroides:
                    dist = self.calcular_distancia(
                        ponto[0], ponto[1], centroide[0], centroide[1]
                    )
                    distancias.append(dist)
                
                cluster_idx = np.argmin(distancias)
                clusters[cluster_idx].append(i)
            
            # Recalcular centroides
            novos_centroides = []
            for cluster_indices in clusters:
                if cluster_indices:
                    pontos_cluster = dados[cluster_indices]
                    novo_centroide = np.mean(pontos_cluster[:, :2], axis=0)
                    novos_centroides.append(novo_centroide)
                else:
                    # Manter centroide anterior se cluster vazio
                    novos_centroides.append(centroides[len(novos_centroides)])
            
            centroides = np.array(novos_centroides)
        
        # Formatar resultados
        return self._formatar_resultados(clusters, pedidos, localizacoes_dict, centroides)
    
    def _formatar_resultados(self, clusters_indices: List, pedidos: List[Pedido],
                           localizacoes_dict: Dict, centroides: np.ndarray) -> List[Dict]:
        """Formata os resultados do clustering"""
        resultados = []
        
        for cluster_id, indices in enumerate(clusters_indices):
            if not indices:
                continue
                
            pedidos_cluster = [pedidos[i] for i in indices]
            centroide = centroides[cluster_id]
            
            # Calcular métricas do cluster
            raio = self._calcular_raio_cluster(pedidos_cluster, centroide, localizacoes_dict)
            
            resultados.append({
                'cluster_id': cluster_id,
                'centroide': {
                    'latitude': float(centroide[0]),
                    'longitude': float(centroide[1])
                },
                'pedidos': pedidos_cluster,
                'pedidos_ids': [p.id for p in pedidos_cluster],
                'quantidade_pedidos': len(pedidos_cluster),
                'valor_total': sum(p.total for p in pedidos_cluster),
                'raio_km': raio / 1000,  # Converter para km
                'densidade': len(pedidos_cluster) / max(1, raio / 1000)
            })
        
        return resultados
    
    def _calcular_raio_cluster(self, pedidos: List[Pedido], centroide: np.ndarray, 
                             localizacoes_dict: Dict) -> float:
        """Calcula o raio máximo do cluster em metros"""
        if not pedidos:
            return 0
            
        centro_lat, centro_lon = centroide[0], centroide[1]
        max_distancia = 0
        
        for pedido in pedidos:
            loc_id = getattr(pedido, 'localizacao_entrega_id', 1)
            if loc_id in localizacoes_dict:
                loc = localizacoes_dict[loc_id]
                distancia = self.calcular_distancia(
                    centro_lat, centro_lon, loc.latitude, loc.longitude
                )
                max_distancia = max(max_distancia, distancia)
        
        return max_distancia

# Funções de interface com o sistema
def executar_kmeans(num_clusters: int = None, max_entregas_por_cluster: int = 5) -> Dict:
    """Função compatível com o código existente - agora usa o otimizador integrado"""
    from .otimizador_integrado import OtimizadorEntregas
    from models import Pedido, Localizacao, Entregador
    
    try:
        pedidos_pendentes = Pedido.query.filter_by(status='pendente').all()
        localizacoes = Localizacao.query.all()
        entregadores_disponiveis = Entregador.query.filter_by(disponivel=True).all()
        localizacoes_dict = {loc.id: loc for loc in localizacoes}
        
        otimizador = OtimizadorEntregas()
        resultado = otimizador.otimizar_rotas_completas(
            pedidos=pedidos_pendentes,
            localizacoes_dict=localizacoes_dict,
            entregadores=entregadores_disponiveis,
            num_clusters=num_clusters,
            max_entregas_por_cluster=max_entregas_por_cluster
        )
        
        return resultado
        
    except Exception as e:
        return {'erro': f'Erro na execução do K-Means: {str(e)}'}

def _atribuir_entregadores(clusters: List[Dict], entregadores: List, max_entregas: int) -> List[Dict]:
    """Atribui clusters aos entregadores disponíveis"""
    atribuicoes = []
    
    for i, cluster in enumerate(clusters):
        if i >= len(entregadores):
            break  # Não há mais entregadores
            
        entregador = entregadores[i]
        
        # Dividir cluster se exceder capacidade máxima
        pedidos_cluster = cluster['pedidos']
        num_grupos = max(1, len(pedidos_cluster) // max_entregas)
        
        for grupo in range(num_grupos):
            start_idx = grupo * max_entregas
            end_idx = start_idx + max_entregas
            pedidos_grupo = pedidos_cluster[start_idx:end_idx]
            
            if pedidos_grupo:
                atribuicoes.append({
                    'entregador_id': entregador.id,
                    'entregador_nome': entregador.nome,
                    'cluster_info': cluster,
                    'pedidos_ids': [p.id for p in pedidos_grupo],
                    'numero_entregas': len(pedidos_grupo),
                    'distancia_total': cluster['raio_km'] * 1000 * 2,  # Estimativa
                    'eficiencia': min(1.0, len(pedidos_grupo) / max_entregas)
                })
    
    return atribuicoes

def _calcular_metricas_otimizacao(atribuicoes: List[Dict]) -> Dict:
    """Calcula métricas de performance da otimização"""
    if not atribuicoes:
        return {}
    
    total_entregas = sum(a['numero_entregas'] for a in atribuicoes)
    total_distancia = sum(a['distancia_total'] for a in atribuicoes)
    eficiencia_media = sum(a['eficiencia'] for a in atribuicoes) / len(atribuicoes)
    
    return {
        'total_entregas': total_entregas,
        'total_distancia_km': total_distancia / 1000,
        'eficiencia_media': eficiencia_media,
        'entregas_por_rota': total_entregas / len(atribuicoes),
        'distancia_media_por_entrega': total_distancia / total_entregas if total_entregas > 0 else 0
    }

# Sistema de armazenamento simplificado (em produção usar banco)
_resultados_kmeans = {}
_ultima_execucao_id = None

def salvar_resultado_kmeans(resultado: Dict) -> str:
    """Salva resultado na memória"""
    import uuid
    from datetime import datetime
    
    execucao_id = str(uuid.uuid4())[:8]
    resultado['id'] = execucao_id
    resultado['data_execucao'] = datetime.now().isoformat()
    
    _resultados_kmeans[execucao_id] = resultado
    global _ultima_execucao_id
    _ultima_execucao_id = execucao_id
    
    print(f"💾 [DEBUG] Resultado salvo com ID: {execucao_id}")
    print(f"💾 [DEBUG] Total de resultados salvos: {len(_resultados_kmeans)}")
    
    return execucao_id

def buscar_resultado_kmeans(execucao_id: str) -> Dict:
    """Busca resultado pelo ID"""
    resultado = _resultados_kmeans.get(execucao_id)
    print(f"🔍 [DEBUG] Buscando resultado ID: {execucao_id} → Encontrado: {resultado is not None}")
    return _resultados_kmeans.get(execucao_id)

def buscar_ultimo_resultado_kmeans() -> Dict:
    """Busca o último resultado executado"""
    global _ultima_execucao_id

    if not _resultados_kmeans:
        print("🔍 [DEBUG] Nenhum resultado K-Means salvo")
        return None
    
    # Usar o ID da última execução ou buscar o mais recente
    if _ultima_execucao_id and _ultima_execucao_id in _resultados_kmeans:
        print(f"🔍 [DEBUG] Retornando última execução: {_ultima_execucao_id}")
        return _resultados_kmeans[_ultima_execucao_id]
    else:
        # Fallback: pegar o primeiro resultado disponível
        ultimo_id = list(_resultados_kmeans.keys())[-1]
        print(f"🔍 [DEBUG] Retornando resultado mais recente: {ultimo_id}")
        return _resultados_kmeans[ultimo_id]

# Manter as funções de armazenamento
_resultados_kmeans = {}

def salvar_resultado_kmeans(resultado: Dict) -> str:
    """Salva resultado na memória"""
    import uuid
    from datetime import datetime
    
    execucao_id = str(uuid.uuid4())[:8]
    resultado['id'] = execucao_id
    resultado['data_execucao'] = datetime.now().isoformat()
    
    _resultados_kmeans[execucao_id] = resultado
    return execucao_id

def buscar_resultado_kmeans(execucao_id: str) -> Dict:
    """Busca resultado pelo ID"""
    return _resultados_kmeans.get(execucao_id)

def buscar_ultimo_resultado_kmeans() -> Dict:
    """Busca o último resultado executado"""
    if not _resultados_kmeans:
        return None
    
    ultimo_id = max(_resultados_kmeans.keys())
    return _resultados_kmeans[ultimo_id]