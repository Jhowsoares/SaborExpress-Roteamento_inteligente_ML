// static/js/grafo.js — v2.1 (adaptado para inicialização via chamada externa)
console.log("🕸️ [GRAFO] Script carregado - v2.1");

let svg, simulation;
let nodes = [], links = [];
let nodeElements, linkElements, labelElements;
let width, height;
let filtersState = { restaurante: true, entrega: true, cluster_centro: true, rota_otimizada: true };
let showLabels = true;
let showClusters = true;
let astarStepsCache = {}; // cache de passos por cluster (opcional)

/* --------------------------------------------------
   UTIL / PROCESSAMENTO DE DADOS
   -------------------------------------------------- */
function debugGrafo(dados) {
    console.group("🔍 DEBUG GRAFO");
    console.log(dados);
    console.groupEnd();
}

function processarDadosGrafo(dados) {
    // aceita formatos nos/arestas ou nodes/links
    const rawNodes = dados.nos || dados.nodes || [];
    const rawLinks = dados.arestas || dados.links || [];

    nodes = rawNodes.map(n => (Object.assign({}, n, {
        x: (typeof n.x === "number") ? n.x : (Math.random() * 500 + 50),
        y: (typeof n.y === "number") ? n.y : (Math.random() * 400 + 50),
        fx: n.tipo === "restaurante" ? (n.x || 400) : null,
        fy: n.tipo === "restaurante" ? (n.y || 300) : null
    })));

    links = rawLinks.map(a => (Object.assign({}, a, {
        source: a.source,
        target: a.target,
        peso: a.peso || a.distancia_metros || 0
    })));
}

/* --------------------------------------------------
   INICIALIZAÇÃO (função pública)
   -------------------------------------------------- */
function inicializarGrafo(dados) {
    debugGrafo(dados);

    const container = document.getElementById("grafo-container");
    if (!container) {
        console.warn("Container do grafo não encontrado (#grafo-container)");
        return;
    }

    width = container.clientWidth;
    height = container.clientHeight;

    // remove conteúdo anterior
    d3.select("#grafo-container").selectAll("*").remove();

    svg = d3.select("#grafo-container")
        .append("svg")
        .attr("width", width)
        .attr("height", height)
        .call(
            d3.zoom().scaleExtent([0.2, 4]).on("zoom", event => {
                svg.select("g.main-g").attr("transform", event.transform);
            })
        );

    svg.append("g").attr("class", "main-g");

    processarDadosGrafo(dados);
    criarSimulacao();
    desenharGrafo();

    simulation.alpha(1).restart();

    if (nodes.length > 8) layoutCluster();
    else layoutGrid();

    atualizarEstatisticas();
    configurarUI();

    if (!nodes || nodes.length === 0) {
        const ph = document.createElement("div");
        ph.className = "grafo-empty";
        ph.textContent = "Sem dados para exibir no grafo — execute uma otimização para gerar rotas.";
        container.appendChild(ph);
    }

    // cache de animações (se vierem)
    if (dados.animacoes) {
        window.grafoAnimacoes = dados.animacoes;
    }
}

/* --------------------------------------------------
   SIMULAÇÃO (D3 Force)
   -------------------------------------------------- */
function criarSimulacao() {
    if (simulation) simulation.stop();

    simulation = d3.forceSimulation(nodes)
        .force("charge", d3.forceManyBody().strength(-60))
        .force("link", d3.forceLink(links).id(d => d.id).distance(d => (d.peso ? Math.max(20, 120 - d.peso/10) : 80)))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collide", d3.forceCollide().radius(d => (d.tipo === "restaurante" ? 18 : 10)).iterations(2))
        .alphaTarget(0.01)
        .on("tick", atualizarPosicoes);
}

/* --------------------------------------------------
   DESENHO DO GRAFO
   -------------------------------------------------- */
function desenharGrafo() {
    const g = svg.select("g.main-g");

    // arestas
    linkElements = g.selectAll(".link").data(links, d => `${d.source}-${d.target}`);
    linkElements.exit().remove();
    linkElements = linkElements.enter().append("line")
        .attr("class", d => "link link-" + (d.tipo || 'link'))
        .attr("stroke-width", d => d.tipo === "rota_otimizada" ? 2.6 : 1.2)
        .attr("opacity", 0.8)
        .merge(linkElements);

    // nós
    nodeElements = g.selectAll(".node").data(nodes, d => d.id);
    nodeElements.exit().remove();
    const nodeEnter = nodeElements.enter().append("circle")
        .attr("class", d => "node node-" + (d.tipo || 'local'))
        .attr("r", d => d.tipo === "restaurante" ? 14 : d.tipo === "cluster_centro" ? 11 : 7)
        .attr("fill", d => d.tipo === "restaurante" ? "#DC143C" : d.tipo === "cluster_centro" ? "#FFD700" : "#1E90FF")
        .attr("stroke", "#fff")
        .attr("stroke-width", 1.8)
        .on("mouseover", nodeHover)
        .on("mouseout", nodeOut)
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended)
        );

    nodeElements = nodeEnter.merge(nodeElements);

    // labels
    labelElements = g.selectAll(".label").data(nodes, d => d.id);
    labelElements.exit().remove();
    const labelEnter = labelElements.enter().append("text")
        .attr("class", "label")
        .attr("font-size", "10px")
        .attr("text-anchor", "middle")
        .attr("fill", "#222")
        .text(d => d.tipo === "restaurante" ? "🏠" : d.tipo === "cluster_centro" ? "C" + d.cluster : "#" + (d.dados?.id || "?"));

    labelElements = labelEnter.merge(labelElements);
}

/* --------------------------------------------------
   POSICIONAMENTO
   -------------------------------------------------- */
function atualizarPosicoes() {
    if (!nodeElements || !linkElements) return;

    nodeElements.attr("cx", d => d.x).attr("cy", d => d.y);
    labelElements.attr("x", d => d.x).attr("y", d => d.y - 12).style("display", showLabels ? "block" : "none");

    linkElements
        .attr("x1", d => getNode(d.source).x)
        .attr("y1", d => getNode(d.source).y)
        .attr("x2", d => getNode(d.target).x)
        .attr("y2", d => getNode(d.target).y);
}

/* --------------------------------------------------
   DRAG HANDLERS
   -------------------------------------------------- */
function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}
function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
}
function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0.01);
    if (d.tipo !== "restaurante") {
        d.fx = null;
        d.fy = null;
    }
}

/* --------------------------------------------------
   HELPERS
   -------------------------------------------------- */
function getNode(ref) {
    return (typeof ref === "object") ? ref : nodes.find(n => n.id === ref) || {x:0,y:0};
}

/* --------------------------------------------------
   TOOLTIP
   -------------------------------------------------- */
function nodeHover(event, d) {
    const container = document.getElementById("grafo-container");
    const tooltip = container.querySelector('.node-tooltip');
    if (!tooltip) return;

    tooltip.style.display = "block";
    const rect = container.getBoundingClientRect();
    const left = (event.sourceEvent ? event.sourceEvent.pageX : event.pageX) - rect.left + 12;
    const top = (event.sourceEvent ? event.sourceEvent.pageY : event.pageY) - rect.top - 12;

    tooltip.style.left = left + "px";
    tooltip.style.top = top + "px";

    tooltip.innerHTML = `
        <strong>${d.nome || "Nó"}</strong><br>
        Tipo: ${d.tipo}<br>
        Cluster: ${d.cluster || "-"}<br>
        ${d?.dados?.endereco ? "Endereço: "+d.dados.endereco : ""}
    `;
}

function nodeOut() { const container = document.getElementById("grafo-container"); const tooltip = container.querySelector('.node-tooltip'); if (tooltip) tooltip.style.display = "none"; }

/* --------------------------------------------------
   SIMULAÇÃO A* (animação visual simples)
   -------------------------------------------------- */
function simularAStar() {
    linkElements
        .transition()
        .duration(600)
        .attr("stroke", d => d.tipo === "rota_otimizada" ? "#32CD32" : "#CCC")
        .attr("opacity", d => d.tipo === "rota_otimizada" ? 1 : 0.15)
        .transition()
        .delay(1600)
        .duration(600)
        .attr("stroke", d => d.tipo === "rota_otimizada" ? "#2E8B57" : "#A9A9A9")
        .attr("opacity", 0.8);
}

/* --------------------------------------------------
   FILTROS / UI
   -------------------------------------------------- */
function aplicarFiltro(tipo, mostrar) {
    filtersState[tipo] = mostrar;
    atualizarFiltro();
}

function atualizarFiltro() {
    nodeElements.transition().duration(300).attr("opacity", d => filtersState[d.tipo] ? 1 : 0.12);
    linkElements.transition().duration(300).attr("opacity", d => filtersState[d.tipo] ? 1 : 0.08);
}

function toggleLabels(show) { showLabels = show; labelElements.style("display", show ? "block" : "none"); }

function toggleClusters(show) { showClusters = show; nodeElements.filter(d => d.tipo === "cluster_centro").style("display", show ? "block" : "none"); }

/* --------------------------------------------------
   ESTATÍSTICAS
   -------------------------------------------------- */
function atualizarEstatisticas() {
    document.getElementById("node-count").textContent = nodes.length;
    document.getElementById("edge-count").textContent = links.length;
}

/* --------------------------------------------------
   LAYOUTS
   -------------------------------------------------- */
function layoutGrid() {
    let cols = Math.ceil(Math.sqrt(nodes.length || 1));
    let cw = width / Math.max(cols,1), ch = height / Math.max(cols,1);

    nodes.forEach((n,i) => {
        n.fx = (i % cols) * cw + cw/2;
        n.fy = Math.floor(i / cols) * ch + ch/2;
    });
    simulation.alpha(0.8).restart();
}

function layoutCluster() {
    const clusterGroups = {};
    nodes.forEach(n => {
        const key = (n.cluster === undefined || n.cluster === null) ? "0" : String(n.cluster);
        if (!clusterGroups[key]) clusterGroups[key] = [];
        clusterGroups[key].push(n);
    });

    let i = 0;
    const keys = Object.keys(clusterGroups);
    for (const key of keys) {
        const ang = i++ * (2 * Math.PI / Math.max(1, keys.length));
        const cx = width/2 + 220 * Math.cos(ang);
        const cy = height/2 + 160 * Math.sin(ang);

        clusterGroups[key].forEach((n,j) => {
            n.fx = cx + 40 * Math.cos(j);
            n.fy = cy + 40 * Math.sin(j);
        });
    }
    simulation.alpha(0.7).restart();
}

/* --------------------------------------------------
   UI CONFIG
   -------------------------------------------------- */
function configurarUI() {
    document.getElementById("btn-reset-grafo")?.addEventListener("click", () => {
        nodes.forEach(n => { if (n.tipo !== "restaurante") { n.fx = null; n.fy = null; } });
        simulation.alpha(0.8).restart();
        linkElements.attr("opacity", 0.8);
    });

    document.getElementById("btn-animar-astar")?.addEventListener("click", simularAStar);
    document.getElementById("btn-ligar-forcas")?.addEventListener("click", () => simulation.alpha(0.8).restart());

    document.getElementById("btn-layout-grid")?.addEventListener("click", layoutGrid);
    document.getElementById("btn-layout-cluster")?.addEventListener("click", layoutCluster);

    document.getElementById("btn-simulacao-passo")?.addEventListener("click", () => {
        if (window.grafoAnimacoes) {
            const firstKey = Object.keys(window.grafoAnimacoes || {})[0];
            const passos = window.grafoAnimacoes[firstKey] || [];
            playAStarSteps(passos);
        } else {
            alert("Nenhuma simulação passo-a-passo disponível (verifique se a otimização salvou animacoes).");
        }
    });

    document.getElementById("btn-heat")?.addEventListener("click", () => {
        nodeElements.transition().duration(600).attr("opacity", d => Math.min(1, 0.4 + (d.cluster || 0) * 0.05));
    });

    document.querySelectorAll(".legend-item").forEach(item => {
        item.addEventListener("click", () => {
            let tipo = item.dataset.filter;
            let ativo = !item.classList.contains("active");
            item.classList.toggle("active", ativo);
            aplicarFiltro(tipo, ativo);
        });
    });

    document.getElementById("toggle-labels")?.addEventListener("change", e => toggleLabels(e.target.checked));
    document.getElementById("toggle-clusters")?.addEventListener("change", e => toggleClusters(e.target.checked));
}

/* --------------------------------------------------
   EXPORT / ANIMAÇÃO PASSO-A-PASSO
   -------------------------------------------------- */
function exportarGrafo() {
    try {
        const dataStr = JSON.stringify(window.grafoData || {nos: nodes, arestas: links}, null, 2);
        const blob = new Blob([dataStr], {type: "application/json"});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'grafo_export.json';
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    } catch (e) {
        console.warn("Export failed:", e);
        alert("Erro ao exportar grafo (veja console).");
    }
}

async function playAStarSteps(passos) {
    const stepEl = document.getElementById("astar-step");
    if (!passos || passos.length === 0) {
        stepEl.textContent = "Sem passos de A* disponíveis";
        return;
    }
    for (const passo of passos) {
        stepEl.textContent = `Tipo: ${passo.tipo} | Atual: ${passo.no_atual} | Open: ${passo.open?.length || 0} | Closed: ${passo.closed?.length || 0}`;
        linkElements.attr("stroke-opacity", d => (passo.open?.some(o => o[0] === d.source || o[0] === d.target) ? 1 : 0.15));
        await new Promise(r => setTimeout(r, 550));
    }
    stepEl.textContent = "Simulação A* concluída.";
}

/* --------------------------------------------------
   exportar função para usar no template (opcional)
   -------------------------------------------------- */
window.inicializarGrafo = inicializarGrafo;
window.exportarGrafo = exportarGrafo;

function startIfReady() {
  if (typeof window.grafoData !== "undefined") {
    inicializarGrafo(window.grafoData);
  }
}

// Se já houver grafoData quando o script carregar
startIfReady();

// Caso contrário, aguarda evento (o template dispara quando o fetch termina)
document.addEventListener('grafoDataReady', startIfReady);