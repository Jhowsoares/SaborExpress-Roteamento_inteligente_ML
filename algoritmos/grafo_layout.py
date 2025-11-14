# algoritmos/grafo_layout.py
from typing import List, Dict, Any
import math

class GeradorLayoutGrafo:
    """
    Gera um layout simples para o grafo de rotas a partir dos clusters
    retornados pelo otimizador. Retorna um dict com:
      - nos: lista de nós (cada nó tem id, nome, tipo, cluster, dados)
      - arestas: lista de arestas (source, target, tipo, peso)
      - local_to_node: dict localizacao_id(int) -> node_id(str)
    O layout é heurístico (círculos por cluster) e foi pensado para a visualização.
    """

    def gerar(self, clusters_otimizados: List[Dict], restaurante_id: int = 1) -> Dict[str, Any]:
        nos = []
        arestas = []
        local_to_node = {}

        # Nó do restaurante (fixo)
        rest_node = {
            "id": "restaurante",
            "nome": "Restaurante",
            "tipo": "restaurante",
            "cluster": None,
            "dados": {"localizacao_id": restaurante_id},
            # coordenadas heurísticas (apenas para layout)
            "x": 400,
            "y": 120
        }
        nos.append(rest_node)
        local_to_node[int(restaurante_id)] = rest_node["id"]

        # posição básica por cluster
        base_radius = 200
        center_x = 400
        center_y = 320

        nclusters = len(clusters_otimizados) or 1
        for ci, cluster in enumerate(clusters_otimizados):
            # posição do centro do cluster em círculo
            ang = 2 * math.pi * (ci / max(1, nclusters))
            cx = center_x + base_radius * math.cos(ang)
            cy = center_y + base_radius * math.sin(ang)

            # nó que representa o centro do cluster
            centro_id = f"centro_{ci+1}"
            nos.append({
                "id": centro_id,
                "nome": f"Centro C{ci+1}",
                "tipo": "cluster_centro",
                "cluster": ci+1,
                "dados": {"cluster": ci+1},
                "x": cx,
                "y": cy
            })

            pedidos = cluster.get("pedidos", [])
            # espalhar pedidos ao redor do centro
            step = (2 * math.pi) / max(1, len(pedidos))
            for pi, pedido in enumerate(pedidos):
                # assumimos que 'pedido' tem p.id e p.localizacao_entrega_id
                pid = getattr(pedido, "id", None) or pedido.get("id")
                loc_id = getattr(pedido, "localizacao_entrega_id", None) or pedido.get("localizacao_entrega_id")
                # node id padrão: entrega_<pedido_id>
                node_id = f"entrega_{pid}"
                r = 40 + (pi * 8)
                angp = pi * step
                nx = cx + r * math.cos(angp)
                ny = cy + r * math.sin(angp)

                nos.append({
                    "id": node_id,
                    "nome": f"Pedido {pid}",
                    "tipo": "entrega",
                    "cluster": ci+1,
                    "dados": {
                        "id": pid,
                        "localizacao_id": loc_id
                    },
                    "x": nx,
                    "y": ny
                })

                # mapear localizacao_id -> node_id (garantia)
                if loc_id is not None:
                    local_to_node[int(loc_id)] = node_id

                # aresta do centro ao pedido (visual)
                arestas.append({
                    "source": centro_id,
                    "target": node_id,
                    "tipo": "cluster_link",
                    "peso": 1
                })

            # ligar centro ao restaurante
            arestas.append({
                "source": "restaurante",
                "target": centro_id,
                "tipo": "cluster_link",
                "peso": 1
            })

        # Retorna tudo pronto
        return {
            "nos": nos,
            "arestas": arestas,
            "local_to_node": local_to_node
        }
