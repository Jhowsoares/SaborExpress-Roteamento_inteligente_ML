// static/js/dashboard.js

let mapaDashboard, grafoDashboard;
let comparacaoChart, eficienciaChart;

function inicializarMapaDashboard(dados) {
    if (mapaDashboard) {
        mapaDashboard.remove();
    }
    
    mapaDashboard = L.map('map-dashboard').setView([-23.5505, -46.6333], 12);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '© OpenStreetMap contributors'
    }).addTo(mapaDashboard);
    
    // Adicionar elementos do mapa (similar ao mapa.js)
    adicionarElementosMapa(mapaDashboard, dados);
    
    // Configurar controles do dashboard
    configurarControlesMapaDashboard();
}

function inicializarGrafoDashboard(dados) {
    // Similar à inicialização do grafo.js, mas adaptada para o dashboard
    const container = document.getElementById('grafo-dashboard');
    const width = container.clientWidth;
    const height = container.clientHeight;

    d3.select('#grafo-dashboard').selectAll('*').remove();
    
    const svg = d3.select('#grafo-dashboard')
        .append('svg')
        .attr('width', width)
        .attr('height', height);
    
    // Implementação simplificada para dashboard
    desenharGrafoDashboard(svg, dados);
    
    configurarControlesGrafoDashboard();
}

function inicializarGraficosComparacao(dados) {
    const ctxComparacao = document.getElementById('chart-comparacao').getContext('2d');
    const ctxEficiencia = document.getElementById('chart-eficiencia').getContext('2d');
    
    // Gráfico de comparação
    comparacaoChart = new Chart(ctxComparacao, {
        type: 'bar',
        data: {
            labels: ['Distância (km)', 'Tempo (min)', 'Eficiência (%)', 'Entregas/hora'],
            datasets: [{
                label: 'Otimizado',
                data: dados.otimizado,
                backgroundColor: 'rgba(40, 167, 69, 0.8)'
            }, {
                label: 'Manual',
                data: dados.manual,
                backgroundColor: 'rgba(220, 53, 69, 0.8)'
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Comparação: Otimizado vs Manual'
                }
            }
        }
    });
    
    // Gráfico de eficiência
    eficienciaChart = new Chart(ctxEficiencia, {
        type: 'doughnut',
        data: {
            labels: ['Rotas Eficientes', 'Rotas Medianas', 'Rotas Ineficientes'],
            datasets: [{
                data: dados.eficiencia,
                backgroundColor: [
                    'rgba(40, 167, 69, 0.8)',
                    'rgba(255, 193, 7, 0.8)',
                    'rgba(220, 53, 69, 0.8)'
                ]
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: true,
                    text: 'Distribuição de Eficiência'
                }
            }
        }
    });
}

function configurarControlesMapaDashboard() {
    document.getElementById('btn-mapa-clusters')?.addEventListener('click', function() {
        // Alternar visibilidade de clusters
        console.log('Controle de clusters clicado');
    });
    
    document.getElementById('btn-mapa-rotas')?.addEventListener('click', function() {
        // Alternar visibilidade de rotas
        console.log('Controle de rotas clicado');
    });
    
    document.getElementById('btn-mapa-reset')?.addEventListener('click', function() {
        mapaDashboard.setView([-23.5505, -46.6333], 12);
    });
}

function configurarControlesGrafoDashboard() {
    document.getElementById('btn-grafo-forcas')?.addEventListener('click', function() {
        console.log('Forças do grafo ativadas');
    });
    
    document.getElementById('btn-grafo-astar')?.addEventListener('click', function() {
        console.log('Simulação A* iniciada');
    });
    
    document.getElementById('btn-grafo-reset')?.addEventListener('click', function() {
        console.log('Grafo resetado');
    });
}

// Funções auxiliares para o dashboard
function adicionarElementosMapa(mapa, dados) {
    // Implementação similar à do mapa.js
    if (dados.restaurante) {
        L.marker([dados.restaurante.latitude, dados.restaurante.longitude])
            .addTo(mapa)
            .bindPopup(`<strong>🏠 ${dados.restaurante.nome}</strong>`);
    }
    
    // Adicionar clusters e rotas...
}

function desenharGrafoDashboard(svg, dados) {
    // Implementação simplificada do grafo para dashboard
    const nodes = dados.nos || [];
    const links = dados.arestas || [];
    
    // Desenhar elementos básicos do grafo
    links.forEach(link => {
        svg.append('line')
            .attr('x1', link.source.x || 100)
            .attr('y1', link.source.y || 100)
            .attr('x2', link.target.x || 200)
            .attr('y2', link.target.y || 200)
            .attr('stroke', '#999')
            .attr('stroke-width', 1);
    });
    
    nodes.forEach(node => {
        svg.append('circle')
            .attr('cx', node.x || 150)
            .attr('cy', node.y || 150)
            .attr('r', 5)
            .attr('fill', '#007bff');
    });
}