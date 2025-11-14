# algoritmos/visualizador_grafo.py
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import math
import io
import base64
from typing import Dict, List

class VisualizadorGrafo:
    def __init__(self, grid_size=10, fator_escala_km=0.5):
        self.grid_size = grid_size
        self.fator_escala_km = fator_escala_km
        self.G = None
        self.pos = None
        
    def criar_grafo_cidade(self):
        """Cria grafo representando a cidade em grade (como no exemplo)"""
        self.G = nx.Graph()
        self.pos = {}
        
        # Adicionando nós
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                node_id = i * self.grid_size + j
                self.G.add_node(node_id)
                self.pos[node_id] = (i, j)
        
        # Adicionando arestas com pesos aleatórios
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                node_id = i * self.grid_size + j

                # Conexão horizontal
                if i < self.grid_size - 1:
                    right_node_id = (i + 1) * self.grid_size + j
                    base_dist = 1.0
                    fator_realismo = np.random.uniform(0.9, 1.5)
                    distancia_km = base_dist * fator_realismo * self.fator_escala_km
                    self.G.add_edge(node_id, right_node_id, weight=distancia_km)

                # Conexão vertical
                if j < self.grid_size - 1:
                    bottom_node_id = i * self.grid_size + (j + 1)
                    base_dist = 1.0
                    fator_realismo = np.random.uniform(0.9, 1.5)
                    distancia_km = base_dist * fator_realismo * self.fator_escala_km
                    self.G.add_edge(node_id, bottom_node_id, weight=distancia_km)

                # Conexão diagonal
                if i < self.grid_size - 1 and j < self.grid_size - 1:
                    diag_node_id = (i + 1) * self.grid_size + (j + 1)
                    base_dist = math.sqrt(2)
                    fator_realismo = np.random.uniform(0.9, 1.5)
                    distancia_km = base_dist * fator_realismo * self.fator_escala_km
                    self.G.add_edge(node_id, diag_node_id, weight=distancia_km)

        return self.G, self.pos
    
    def mapear_localizacoes_para_grafo(self, localizacoes_dict: Dict[int, object]):
        """Mapeia localizações reais para nós do grafo (CORRIGIDO)"""
        if not self.pos:
            self.criar_grafo_cidade()
            
        print(f"📍 Mapeando {len(localizacoes_dict)} localizações para o grafo...")
        
        # Encontrar nós mais próximos para cada localização
        mapeamento = {}
        for loc_id, localizacao in localizacoes_dict.items():
            # Converter coordenadas reais para posição no grid
            # Normalizar para faixa 0-1 baseada em São Paulo
            lat_min, lat_max = -23.62, -23.51
            lng_min, lng_max = -46.70, -46.54
            
            lat_norm = (localizacao.latitude - lat_min) / (lat_max - lat_min)
            lng_norm = (localizacao.longitude - lng_min) / (lng_max - lng_min)
            
            # Garantir dentro dos limites
            lat_norm = max(0, min(1, lat_norm))
            lng_norm = max(0, min(1, lng_norm))
            
            grid_i = int(lat_norm * (self.grid_size - 1))
            grid_j = int(lng_norm * (self.grid_size - 1))
            
            node_id = grid_i * self.grid_size + grid_j
            mapeamento[loc_id] = node_id
            
            print(f"  📌 {localizacao.nome} → Nó {node_id} (grid[{grid_i},{grid_j}])")
            
        return mapeamento
    
    def visualizar_rotas_otimizadas(self, clusters_otimizados, localizacoes_dict, entregadores):
        """Gera visualização ESTÁTICA das rotas otimizadas (como no exemplo)"""
        if not self.G:
            self.criar_grafo_cidade()
            
        # Primeiro mapear todas as localizações para nós
        mapeamento = self.mapear_localizacoes_para_grafo(localizacoes_dict)
        
        fig, ax = plt.subplots(figsize=(16, 12))
        
        # Desenhar grafo base
        nx.draw_networkx_nodes(self.G, self.pos, node_size=30, 
                              node_color='lightgray', ax=ax)
        nx.draw_networkx_edges(self.G, self.pos, width=0.4, 
                              edge_color='lightgray', ax=ax)
        
        # Encontrar nó do restaurante
        restaurante_node = None
        for loc_id, loc in localizacoes_dict.items():
            if getattr(loc, 'tipo', None) == 'restaurante' or 'restaurante' in loc.nome.lower():
                restaurante_node = mapeamento[loc_id]
                print(f"🏠 Restaurante mapeado para nó {restaurante_node}")
                break
        
        if restaurante_node is None:
            restaurante_node = self.grid_size * self.grid_size // 2
            print(f"⚠️ Restaurante não encontrado, usando nó central {restaurante_node}")
        
        colors = ['#d62728', '#1f77b4', '#ff7f0e', '#2ca02c', '#9467bd']
        legend_elements = []
        edge_label_sides = {}
        
        # Desenhar rotas para cada cluster
        for i, cluster in enumerate(clusters_otimizados):
            if i >= len(colors):
                color = np.random.rand(3,)
            else:
                color = colors[i]
                
            # Mapear pedidos para nós do grafo
            pedidos_nodes = []
            for pedido in cluster.get('pedidos', []):
                loc_id = getattr(pedido, 'localizacao_entrega_id', None)
                if loc_id and loc_id in mapeamento:
                    node_id = mapeamento[loc_id]
                    pedidos_nodes.append(node_id)
                    print(f"  📦 Pedido {pedido.id} → Nó {node_id}")
            
            if pedidos_nodes:
                # Desenhar pontos de entrega
                nx.draw_networkx_nodes(self.G, self.pos, nodelist=pedidos_nodes,
                                      node_color=color, node_size=150, ax=ax)
                
                # Simular rota otimizada (restaurante -> pedidos -> restaurante)
                if len(pedidos_nodes) > 0:
                    # Ordenar por proximidade do restaurante (simulação do A*)
                    pedidos_nodes_sorted = sorted(pedidos_nodes, 
                        key=lambda node: math.sqrt(
                            (self.pos[node][0] - self.pos[restaurante_node][0])**2 +
                            (self.pos[node][1] - self.pos[restaurante_node][1])**2
                        ))
                    
                    # Criar rota: restaurante -> pedidos -> restaurante
                    rota = [restaurante_node] + pedidos_nodes_sorted + [restaurante_node]
                    
                    # Desenhar rota com setas (como no exemplo)
                    path_edges = list(zip(rota, rota[1:]))
                    for u, v in path_edges:
                        ax.annotate("", 
                                  xy=self.pos[v], xycoords='data',
                                  xytext=self.pos[u], textcoords='data',
                                  arrowprops=dict(arrowstyle="->", color=color,
                                                shrinkA=8, shrinkB=8,
                                                connectionstyle="arc3,rad=0.1",
                                                lw=3, alpha=0.9))
                        
                        # Adicionar labels de distância (como no exemplo)
                        pos_u = np.array(self.pos[u])
                        pos_v = np.array(self.pos[v])
                        mid_point = (pos_u + pos_v) / 2
                        
                        direction = pos_v - pos_u
                        if np.linalg.norm(direction) > 0:
                            perp_direction = np.array([-direction[1], direction[0]])
                            norm_perp = perp_direction / np.linalg.norm(perp_direction)
                            
                            edge_key = tuple(sorted((u, v)))
                            if edge_key in edge_label_sides:
                                side = -edge_label_sides[edge_key]
                                edge_label_sides[edge_key] = side
                            else:
                                side = 1
                                edge_label_sides[edge_key] = side
                                
                            label_pos = mid_point + norm_perp * 0.1 * side
                            
                            # Calcular distância aproximada
                            weight = self.G.edges[u, v]['weight'] if self.G.has_edge(u, v) else 1.0
                            label_text = f"{weight:.1f}km"
                            
                            ax.text(label_pos[0], label_pos[1], label_text,
                                   size=7.5, color=color, ha='center', va='center',
                                   bbox=dict(facecolor='white', edgecolor='none', alpha=0.7, pad=0.1))
                
                # Adicionar à legenda
                legend_elements.append(
                    plt.Line2D([0], [0], color=color, marker='o', 
                              linestyle='-', markersize=8, 
                              label=f'Rota {i+1} ({len(pedidos_nodes)} pedidos)')
                )
        
        # Desenhar restaurante
        nx.draw_networkx_nodes(self.G, self.pos, nodelist=[restaurante_node],
                              node_color='green', node_size=300, 
                              node_shape='s', ax=ax)
        
        legend_elements.append(
            plt.Line2D([0], [0], color='green', marker='s', 
                      linestyle='None', markersize=10, 
                      label='Sabor Express')
        )
        
        plt.title("Rotas de Entrega Otimizadas - Sabor Express\n(K-Means + A*)", 
                 fontsize=16, pad=20)
        plt.legend(handles=legend_elements, loc='upper left', 
                  bbox_to_anchor=(1, 1))
        plt.axis('equal')
        plt.tight_layout()
        
        # Converter para base64 para exibir no HTML
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        print(f"✅ Visualização gerada: {len(clusters_otimizados)} clusters, {sum(len(c.get('pedidos', [])) for c in clusters_otimizados)} pedidos")

        # Adicione isso no visualizador para debug
        print("🔍 DEBUG - Mapeamento completo:")
        for loc_id, node_id in mapeamento.items():
            loc = localizacoes_dict[loc_id]
            print(f"  {loc.nome} → Nó {node_id} (pos: {self.pos[node_id]})")

        return f"data:image/png;base64,{image_base64}"