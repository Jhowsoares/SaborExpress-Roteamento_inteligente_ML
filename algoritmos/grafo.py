# algoritmos/grafo.py
import math
import itertools
from heapq import heappush, heappop
from typing import List, Dict, Tuple, Optional, Any

class NoGrafo:
    """Representa nó no A* (contém referência ao objeto 'localizacao' original)."""
    def __init__(self, localizacao: Any, g: float = 0.0, h: float = 0.0, pai: Optional["NoGrafo"] = None):
        self.localizacao = localizacao   # objeto do domínio (deve ter .id, .latitude, .longitude)
        self.g = g                       # custo do início até aqui
        self.h = h                       # heurística (estimativa até destino)
        self.f = g + h                   # prioridade
        self.pai = pai

    def __lt__(self, other: "NoGrafo"):
        return self.f < other.f

# -------------------
# Utilities
# -------------------
def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distância Haversine em metros."""
    R = 6371000
    lat1_r, lat2_r = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def _reconstruir_caminho_ids(no: NoGrafo) -> List[int]:
    path = []
    cur = no
    while cur:
        path.append(cur.localizacao.id)
        cur = cur.pai
    return list(reversed(path))

# -------------------
# Graph builder
# -------------------
def construir_grafo(nos: Any, arestas: List[Dict], directed: bool = False,
                    peso_key: str = "distancia_metros") -> Dict[int, List[Tuple[int, float]]]:
    """
    Constroi um dicionário de adjacência.
    - nos: pode ser lista de objetos (com atributo .id) ou dict id->obj
    - arestas: lista de dicts com 'source'/'target' ou 'localizacao_origem_id'/'localizacao_destino_id'
    - retorna: {node_id: [(vizinho_id, peso), ...], ...}
    """
    grafo = {}
    # inicializa nós mesmo que não tenham arestas
    if isinstance(nos, dict):
        for nid in nos.keys():
            grafo[int(nid)] = []
    else:
        for n in nos:
            grafo[int(n.id)] = []

    for e in arestas:
        # detectar chaves
        if 'source' in e and 'target' in e:
            s = int(e['source']); t = int(e['target'])
        else:
            s = int(e.get('localizacao_origem_id')); t = int(e.get('localizacao_destino_id'))
        peso = float(e.get(peso_key, e.get('peso', 0.0)))
        grafo.setdefault(s, []).append((t, peso))
        if not directed:
            grafo.setdefault(t, []).append((s, peso))
    return grafo

# -------------------
# A* algorithm
# -------------------
def a_estrela(grafo: Dict[int, List[Tuple[int, float]]],
              localizacoes_dict: Dict[int, Any],
              inicio_id: int,
              destino_id: int,
              heuristica_func = None) -> Optional[Tuple[List[int], float]]:
    """
    A* que retorna (lista_de_ids, custo_total).
    - heuristica_func: fn(node_id_a, node_id_b) -> float (se None, usa haversine com coords no localizacoes_dict)
    - Retorno: (path_ids, cost) ou None se não houver caminho.
    """
    if inicio_id not in grafo or destino_id not in grafo:
        return None

    if heuristica_func is None:
        def heuristica(a,b):
            la = localizacoes_dict[a]; lb = localizacoes_dict[b]
            return haversine_m(la.latitude, la.longitude, lb.latitude, lb.longitude)
    else:
        heuristica = heuristica_func

    open_heap = []
    counter = itertools.count()  # para desempate estável
    inicio_local = localizacoes_dict[inicio_id]
    h0 = heuristica(inicio_id, destino_id)
    start_node = NoGrafo(inicio_local, g=0.0, h=h0, pai=None)
    heappush(open_heap, (start_node.f, next(counter), start_node))

    closed = set()
    best_g = {inicio_id: 0.0}

    while open_heap:
        _, _, current = heappop(open_heap)
        cur_id = current.localizacao.id
        if cur_id in closed:
            continue

        if cur_id == destino_id:
            return _reconstruir_caminho_ids(current), current.g

        closed.add(cur_id)

        for neighbor_id, edge_cost in grafo.get(cur_id, []):
            if neighbor_id in closed:
                continue
            tentative_g = current.g + edge_cost
            if tentative_g < best_g.get(neighbor_id, float('inf')):
                best_g[neighbor_id] = tentative_g
                neigh_local = localizacoes_dict[neighbor_id]
                h = heuristica(neighbor_id, destino_id)
                neigh_node = NoGrafo(neigh_local, g=tentative_g, h=h, pai=current)
                heappush(open_heap, (neigh_node.f, next(counter), neigh_node))

    return None

# -------------------
# Dijkstra
# -------------------
def dijkstra(grafo: Dict[int, List[Tuple[int, float]]],
             localizacoes_dict: Dict[int, Any],
             inicio_id: int,
             destino_id: int) -> Optional[Tuple[List[int], float]]:
    """
    Dijkstra que retorna (lista_de_ids, custo_total) ou None se sem caminho.
    """
    if inicio_id not in grafo or destino_id not in grafo:
        return None

    dist = {n: float('inf') for n in grafo.keys()}
    prev = {n: None for n in grafo.keys()}
    dist[inicio_id] = 0.0

    heap = []
    counter = itertools.count()
    heappush(heap, (0.0, next(counter), inicio_id))
    visited = set()

    while heap:
        d, _, u = heappop(heap)
        if u in visited:
            continue
        visited.add(u)
        if u == destino_id:
            break
        for v, w in grafo.get(u, []):
            nd = d + w
            if nd < dist.get(v, float('inf')):
                dist[v] = nd
                prev[v] = u
                heappush(heap, (nd, next(counter), v))

    if dist.get(destino_id, float('inf')) == float('inf'):
        return None

    # reconstruir caminho em ids
    path_ids = []
    cur = destino_id
    while cur is not None:
        path_ids.append(cur)
        cur = prev[cur]
    path_ids.reverse()
    return path_ids, dist[destino_id]

# -------------------
# Simulador A* (para animação)
# -------------------
def simular_a_estrela(grafo: Dict[int, List[Tuple[int, float]]],
                      localizacoes_dict: Dict[int, Any],
                      inicio_id: int,
                      destino_id: int,
                      heuristica_func = None,
                      max_steps: int = 1000) -> List[Dict]:
    """
    Retorna lista de passos para animar A*:
    Cada passo: {
        'tipo': 'inicio'|'explorar'|'concluido'|'sem_caminho',
        'no_atual': id,
        'open': [ (node_id, g, f), ... ],
        'closed': [...],
        'caminho_parcial': [...],  # ids
    }
    """
    passos = []
    if inicio_id not in grafo or destino_id not in grafo:
        return passos

    if heuristica_func is None:
        def heuristica(a,b):
            la = localizacoes_dict[a]; lb = localizacoes_dict[b]
            return haversine_m(la.latitude, la.longitude, lb.latitude, lb.longitude)
    else:
        heuristica = heuristica_func

    open_heap = []
    counter = itertools.count()
    start_local = localizacoes_dict[inicio_id]
    start_node = NoGrafo(start_local, g=0.0, h=heuristica(inicio_id, destino_id))
    heappush(open_heap, (start_node.f, next(counter), start_node))

    closed = set()
    best_g = {inicio_id: 0.0}
    steps = 0

    passos.append({
        'tipo': 'inicio',
        'no_atual': inicio_id,
        'open': [(inicio_id, 0.0, start_node.f)],
        'closed': list(closed),
        'caminho_parcial': [inicio_id]
    })

    while open_heap and steps < max_steps:
        _, _, current = heappop(open_heap)
        cur_id = current.localizacao.id
        if cur_id in closed:
            continue

        # registrar exploração
        open_list_snapshot = [(n.localizacao.id, n.g, n.f) for _,_,n in open_heap]
        passos.append({
            'tipo': 'explorar',
            'no_atual': cur_id,
            'open': open_list_snapshot,
            'closed': list(closed),
            'caminho_parcial': _reconstruir_caminho_ids(current)
        })

        if cur_id == destino_id:
            passos.append({
                'tipo': 'concluido',
                'no_atual': destino_id,
                'open': [],
                'closed': list(closed),
                'caminho_parcial': _reconstruir_caminho_ids(current),
                'custo_total': current.g
            })
            return passos

        closed.add(cur_id)

        for neighbor_id, edge_cost in grafo.get(cur_id, []):
            if neighbor_id in closed:
                continue
            tentative_g = current.g + edge_cost
            if tentative_g < best_g.get(neighbor_id, float('inf')):
                best_g[neighbor_id] = tentative_g
                neigh_local = localizacoes_dict[neighbor_id]
                h = heuristica(neighbor_id, destino_id)
                neigh_node = NoGrafo(neigh_local, g=tentative_g, h=h, pai=current)
                heappush(open_heap, (neigh_node.f, next(counter), neigh_node))
        steps += 1

    # se chegou aqui sem encontrar
    passos.append({'tipo': 'sem_caminho', 'open': [], 'closed': list(closed), 'caminho_parcial': []})
    return passos
