# algoritmos/visualizador_grafo_real.py
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import io
import base64
import json
from typing import Dict, List

class VisualizadorGrafoReal:
    def __init__(self):
        self.G = nx.Graph()
        
    def criar_grafo_com_coordenadas_reais(self, localizacoes_dict: Dict[int, object]):
        """Cria grafo usando coordenadas reais de São Paulo"""
        self.G.clear()
        
        print(f"📍 Criando grafo com {len(localizacoes_dict)} localizações reais")
        
        # Encontrar restaurante
        restaurante = None
        for loc_id, loc in localizacoes_dict.items():
            if hasattr(loc, 'nome') and 'restaurante' in loc.nome.lower():
                restaurante = loc
                break
        
        # Adicionar restaurante
        if restaurante:
            self.G.add_node(
                "Restaurante",
                pos=(restaurante.longitude, restaurante.latitude),
                tipo="restaurante",
                nome=restaurante.nome,
                lat_original=restaurante.latitude,
                lon_original=restaurante.longitude
            )
            print(f"🏠 Restaurante: {restaurante.nome} ({restaurante.latitude}, {restaurante.longitude})")
        
        # Adicionar localizações reais
        for loc_id, loc in localizacoes_dict.items():
            if hasattr(loc, 'latitude') and hasattr(loc, 'longitude'):
                # Pular restaurante se já adicionamos
                if loc == restaurante:
                    continue
                    
                node_id = f"Local_{loc_id}"
                self.G.add_node(
                    node_id,
                    pos=(loc.longitude, loc.latitude),
                    tipo="entrega", 
                    nome=getattr(loc, 'nome', f'Local_{loc_id}'),
                    lat_original=loc.latitude,
                    lon_original=loc.longitude
                )
                print(f"📌 {loc.nome}: ({loc.latitude}, {loc.longitude})")
        
        print(f"✅ Grafo criado: {len(self.G.nodes())} nós")
        return self.G

    def visualizar_plotly_interativo(self):
        """Gera visualização interativa com Plotly usando coordenadas reais"""
        
        if not self.G.nodes():
            return None
            
        # Extrair dados do grafo
        node_lons = []
        node_lats = []
        node_text = []
        node_color = []
        node_size = []
        
        for node, data in self.G.nodes(data=True):
            lon, lat = data['pos']
            node_lons.append(lon)
            node_lats.append(lat)
            node_text.append(data.get('nome', node))
            
            if data.get('tipo') == 'restaurante':
                node_color.append('red')
                node_size.append(20)
            else:
                node_color.append('blue')
                node_size.append(10)
        
        # Criar figura Plotly
        fig = go.Figure()
        
        # Adicionar nós como scatter no mapa
        fig.add_trace(go.Scattermapbox(
            lat=node_lats,
            lon=node_lons,
            mode='markers',
            marker=dict(
                size=node_size,
                color=node_color,
                opacity=0.8
            ),
            text=node_text,
            hoverinfo='text',
            name='Pontos de Entrega'
        ))
        
        # Configurar layout do mapa
        fig.update_layout(
            mapbox=dict(
                style="open-street-map",
                center=dict(lat=-23.5505, lon=-46.6333),  # Centro de São Paulo
                zoom=10
            ),
            title="Mapa de Entregas - Sabor Express (Coordenadas Reais)",
            height=600,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        
        return fig

    def gerar_dados_json(self):
        """Gera dados serializáveis para API"""
        if not self.G.nodes():
            return {"error": "Grafo vazio"}
            
        nodes_data = []
        for node, data in self.G.nodes(data=True):
            nodes_data.append({
                "id": node,
                "nome": data.get('nome', node),
                "tipo": data.get('tipo', 'desconhecido'),
                "latitude": data.get('lat_original', 0),
                "longitude": data.get('lon_original', 0)
            })
            
        return {
            "nodes": nodes_data,
            "total_nodes": len(nodes_data),
            "status": "success"
        }