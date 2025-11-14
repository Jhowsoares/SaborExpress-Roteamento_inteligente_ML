# algoritmos/otimizador_integrado.py
import math
from typing import List, Dict, Any, Tuple
from models import Pedido, Localizacao, Entregador
from algoritmos.kmeans import ClusterizadorKMeans

# importar utilitários do grafo
from algoritmos.grafo import (
    NoGrafo,
    a_estrela,
    dijkstra,
    simular_a_estrela,
    construir_grafo,
    haversine_m
)


class OtimizadorEntregas:
    """
    Otimizador integrado K-Means + A* (versão PRO).
    Recebe:
      - pedidos: lista de objetos Pedido
      - localizacoes_dict: pode ser:
          * dicionário simples id -> Localizacao  OR
          * dict contendo {'locs': id->Localizacao, 'grafo': grafo_adjacencia}
      - entregadores: lista de Entregador
    Retorna dicionário com 'atribuicoes', 'metricas', 'clusters_otimizados' e 'animacoes'.
    """

    def __init__(self):
        self.clusterizador = ClusterizadorKMeans()

    def _debug_localizacoes(self, localizacoes_dict: Dict):
        print("📍 [DEBUG] Localizações disponíveis:")
        # aceita tanto dict id->obj quanto dict wrapper {'locs':..., 'grafo':...}
        locs = self._extract_locs(localizacoes_dict)
        for loc_id, loc in locs.items():
            nome = getattr(loc, "nome", "Sem nome")
            tipo = getattr(loc, "tipo", "Sem tipo")
            print(f"  {loc_id} → {nome} ({tipo})")

    def _extract_locs(self, localizacoes_dict: Dict) -> Dict[int, Localizacao]:
        """Retorna o dicionário id->Localizacao a partir do parâmetro recebido."""
        if not localizacoes_dict:
            return {}
        if isinstance(localizacoes_dict, dict) and 'locs' in localizacoes_dict:
            return localizacoes_dict['locs'] or {}
        # caso seja já um dict id->Localizacao
        return localizacoes_dict

    def _extract_grafo(self, localizacoes_dict: Dict):
        """Retorna grafo se disponível."""
        if not localizacoes_dict:
            return None
        if isinstance(localizacoes_dict, dict) and 'grafo' in localizacoes_dict:
            return localizacoes_dict['grafo']
        return None

    def otimizar_rotas_completas(self, pedidos: List[Pedido],
                                 localizacoes_dict: Dict[int, Localizacao],
                                 entregadores: List[Entregador],
                                 num_clusters: int = None,
                                 max_entregas_por_cluster: int = 5) -> Dict[str, Any]:

        print(f"🔧 Otimizando {len(pedidos)} pedidos / {len(entregadores)} entregadores")

        locs_map = self._extract_locs(localizacoes_dict)
        self._debug_localizacoes({'locs': locs_map})

        # FASE 1: Clusterização com K-Means
        clusters = self.clusterizador.clusterizar(pedidos, locs_map)
        print(f"📊 K-Means criou {len(clusters)} clusters")

        clusters_otimizados = []
        animacoes = {}  # armazenar simulações (por cluster)

        # Garantir grafo (se caller não passou, construímos completo via haversine)
        grafo = self._extract_grafo(localizacoes_dict)
        if grafo is None:
            print("⚠️ [ROUTER] Nenhuma rota cadastrada — criando grafo completo via Haversine")
            # construir arestas completo (todos <-> todos)
            arestas = []
            valid_locs = [l for l in locs_map.values() if hasattr(l, 'id') and hasattr(l, 'latitude') and hasattr(l, 'longitude')]
            for a in valid_locs:
                for b in valid_locs:
                    if a.id == b.id:
                        continue
                    arestas.append({
                        'localizacao_origem_id': a.id,
                        'localizacao_destino_id': b.id,
                        'distancia_metros': haversine_m(a.latitude, a.longitude, b.latitude, b.longitude)
                    })
            grafo = construir_grafo(valid_locs, arestas)
            print(f"📡 Grafo construído: {len(grafo)} nós e {sum(len(v) for v in grafo.values())} arestas")

        # FASE 2: para cada cluster, otimizar rota com A*
        for idx, cluster in enumerate(clusters):
            try:
                rota_info, passos_anim = self._rota_com_a_estrela(cluster, {'locs': locs_map, 'grafo': grafo})
                clusters_otimizados.append(rota_info)
                # passos_anim já é uma lista — garantir serializável
                animacoes[f"cluster_{idx+1}"] = passos_anim or []
                print(f"✅ Cluster {idx+1}: {len(cluster.get('pedidos', []))} pedidos (A*)")
            except Exception as e:
                print(f"❌ Erro ao otimizar cluster {idx+1}: {e}")
                # fallback mínimo: manter cluster sem otimização
                clusters_otimizados.append({
                    **cluster,
                    'rota_ordenada': cluster.get('pedidos', []),
                    'distancia_total': 0,
                    'sequencia_otimizada': [p.id for p in cluster.get('pedidos', [])]
                })
                animacoes[f"cluster_{idx+1}"] = []

        # FASE 3: Atribuição inteligente
        atribuicoes = self._atribuir_entregadores_inteligente(clusters_otimizados, entregadores, max_entregas_por_cluster)

        # FASE 4: Métricas
        metricas = self._calcular_metricas_finais(atribuicoes)

        resultado = {
            'atribuicoes': atribuicoes,
            'metricas': metricas,
            'clusters_otimizados': clusters_otimizados,
            'animacoes': animacoes,
            'parametros': {
                'num_clusters': num_clusters,
                'max_entregas_por_cluster': max_entregas_por_cluster,
                'total_pedidos': len(pedidos),
                'total_entregadores': len(entregadores)
            }
        }

        return resultado

    def _rota_com_a_estrela(self, cluster: Dict, localizacoes_container: Dict):
        """
        Otimiza a sequência dentro do cluster usando A* (heurística haversine).
        Retorna (rota_info_dict, passos_animacao_list)
        """
        pedidos_cluster = cluster.get('pedidos', [])
        if len(pedidos_cluster) <= 1:
            return ({
                **cluster,
                'rota_ordenada': pedidos_cluster,
                'distancia_total': 0,
                'sequencia_otimizada': [p.id for p in pedidos_cluster]
            }, [])

        locs = self._extract_locs(localizacoes_container)
        grafo = self._extract_grafo(localizacoes_container)

        # localizar restaurante
        restaurante = None
        for loc in locs.values():
            if getattr(loc, 'tipo', None) == 'restaurante':
                restaurante = loc
                break
        if not restaurante and locs:
            # fallback para primeira
            restaurante = next(iter(locs.values()))
        if not restaurante:
            raise RuntimeError("Restaurante não encontrado e localizacoes vazio.")

        rota = []
        pedidos_restantes = pedidos_cluster.copy()
        atual = restaurante
        passos_anim_total = []

        # vizinho mais próximo por A*
        while pedidos_restantes:
            proximos = []
            for pedido in pedidos_restantes:
                target_id = getattr(pedido, 'localizacao_entrega_id', None)
                if target_id is None:
                    continue
                res = a_estrela(grafo, locs, atual.id, target_id)
                if res:
                    path_ids, custo = res
                    proximos.append((pedido, custo, path_ids))
            if not proximos:
                # se A* não encontrou nada (problema de grafo), pega primeiro e segue
                pedido_fallback = pedidos_restantes[0]
                rota.append(pedido_fallback)
                pedidos_restantes.remove(pedido_fallback)
                atual = locs.get(getattr(pedido_fallback, 'localizacao_entrega_id'))
                continue

            # escolher menor custo
            escolha = min(proximos, key=lambda x: x[1])
            pedido_atual, custo_escolha, caminho_ids = escolha
            rota.append(pedido_atual)

            # gerar passos de animação A* para esta sub-rota (start -> target)
            passos = simular_a_estrela(grafo, locs, atual.id, pedido_atual.localizacao_entrega_id)
            # simular_a_estrela já retorna lista de dicts; acrescentar
            if passos:
                # normalize passos: certifique-se que cada passo é dicionário simples
                passos_normalizados = []
                for p in passos:
                    # simplificar eventuais objetos para apenas ids / números
                    passo_clean = {
                        'tipo': p.get('tipo'),
                        'no_atual': p.get('no_atual'),
                        'open': [(int(x[0]), float(x[1]), float(x[2])) if len(x) >= 3 else x for x in p.get('open', [])],
                        'closed': [int(c) for c in p.get('closed', [])],
                        'caminho_parcial': [int(i) for i in p.get('caminho_parcial', [])]
                    }
                    if 'custo_total' in p:
                        passo_clean['custo_total'] = float(p.get('custo_total', 0))
                    passos_normalizados.append(passo_clean)
                passos_anim_total.extend(passos_normalizados)

            pedidos_restantes.remove(pedido_atual)
            atual = locs.get(pedido_atual.localizacao_entrega_id, atual)

        distancia_total = self._calcular_distancia_rota(rota, locs)

        resultado_cluster = {
            **cluster,
            'rota_ordenada': rota,
            'distancia_total': distancia_total,
            'sequencia_otimizada': [p.id for p in rota]
        }

        return resultado_cluster, passos_anim_total

    # ---------- funções auxiliares (mantive as suas, com pequenas melhorias) ----------
    def _distancia_entre_pedidos(self, origem, destino, localizacoes_dict: Dict) -> float:
        try:
            locs = self._extract_locs(localizacoes_dict)
            if isinstance(origem, Localizacao):
                loc_origem = origem
            else:
                loc_origem = locs.get(getattr(origem, 'localizacao_entrega_id', None)) or next(iter(locs.values()), None)

            if isinstance(destino, Localizacao):
                loc_destino = destino
            else:
                loc_destino = locs.get(getattr(destino, 'localizacao_entrega_id', None)) or next(iter(locs.values()), None)

            if not loc_origem or not loc_destino:
                return 1000.0

            return haversine_m(loc_origem.latitude, loc_origem.longitude,
                               loc_destino.latitude, loc_destino.longitude) / 1000.0
        except Exception as e:
            print(f"⚠️ [DEBUG] Erro ao calcular distância: {e}")
            return 1000.0

    def _calcular_distancia_rota(self, rota: List[Pedido], localizacoes_dict: Dict) -> float:
        if len(rota) <= 1:
            return 0.0
        locs = self._extract_locs(localizacoes_dict)
        restaurante = next((loc for loc in locs.values() if getattr(loc, 'tipo', None) == 'restaurante'), None)
        if not restaurante and locs:
            restaurante = next(iter(locs.values()))
        if not restaurante:
            return 0.0

        distancia_total = 0.0
        distancia_total += self._distancia_entre_pedidos(restaurante, rota[0], localizacoes_dict)
        for i in range(len(rota) - 1):
            distancia_total += self._distancia_entre_pedidos(rota[i], rota[i+1], localizacoes_dict)
        distancia_total += self._distancia_entre_pedidos(rota[-1], restaurante, localizacoes_dict)
        return distancia_total * 1000.0  # retornar em metros (compatível com outras partes)

    def _atribuir_entregadores_inteligente(self, clusters: List[Dict],
                                           entregadores: List[Entregador],
                                           max_entregas: int) -> List[Dict]:
        # simplificado: ciclar entregadores e criar atribuições
        atribuicoes = []
        if not entregadores:
            return atribuicoes

        entregadores_ord = sorted(entregadores, key=lambda e: getattr(e, 'id', 0))
        for i, cluster in enumerate(clusters):
            entregador = entregadores_ord[i % len(entregadores_ord)]
            pedidos_cluster = cluster.get('rota_ordenada', cluster.get('pedidos', []))
            atribuicoes.append({
                'entregador_id': entregador.id,
                'entregador_nome': entregador.nome,
                'entregador_veiculo': entregador.veiculo,
                'cluster_info': cluster,
                'pedidos_ids': [p.id for p in pedidos_cluster],
                'pedidos_sequencia': cluster.get('sequencia_otimizada', [p.id for p in pedidos_cluster]),
                'numero_entregas': len(pedidos_cluster),
                'distancia_total': float(cluster.get('distancia_total', 0)),
                'eficiencia': float(cluster.get('eficiencia', 0.8)) if cluster.get('eficiencia') is not None else 0.8,
                'tempo_estimado_minutos': float(cluster.get('tempo_estimado_minutos', 0))
            })
        return atribuicoes

    def _calcular_metricas_finais(self, atribuicoes: List[Dict]) -> Dict:
        if not atribuicoes:
            return {}
        total_entregas = sum(a.get('numero_entregas', 0) for a in atribuicoes)
        total_dist = sum(a.get('distancia_total', 0) for a in atribuicoes)
        eficiencia_media = sum(a.get('eficiencia', 0) for a in atribuicoes) / max(1, len(atribuicoes))
        tempo_total = sum(a.get('tempo_estimado_minutos', 0) for a in atribuicoes)
        return {
            'total_entregas': total_entregas,
            'total_distancia_km': total_dist / 1000.0,
            'eficiencia_media': eficiencia_media,
            'tempo_total_minutos': tempo_total,
            'entregas_por_hora': (total_entregas / (tempo_total / 60)) if tempo_total > 0 else 0
        }
