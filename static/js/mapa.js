// --- Estado do mapa ---
let mapa;
let marcadores = [];
let polylines = [];
let circulosCluster = [];
let centroMarkers = [];

// Haversine defensivo
function calcDistance(lat1, lon1, lat2, lon2) {
    const R = 6371;
    const dLat = (lat2-lat1)*Math.PI/180;
    const dLon = (lon2-lon1)*Math.PI/180;

    const a = Math.sin(dLat/2)**2 +
        Math.cos(lat1*Math.PI/180) *
        Math.cos(lat2*Math.PI/180) *
        Math.sin(dLon/2)**2;

    return R * (2*Math.atan2(Math.sqrt(a), Math.sqrt(1-a)));
}

function inicializarMapa() {
    const view = [-23.5505,-46.6333];

    mapa = L.map('map').setView(view,12);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{
        maxZoom:18,
        attribution:"© OpenStreetMap"
    }).addTo(mapa);

    adicionarRestaurante();
    adicionarClusters();
    adicionarRotas();
    adicionarConexoesEspaciais();
}

function adicionarRestaurante() {
    const r = mapaData.restaurante;
    if(!r || !r.latitude) return;

    const m = L.marker([r.latitude,r.longitude],{
        icon:L.divIcon({html:"🏠",className:"restaurante-marker"})
    }).addTo(mapa);

    m.bindPopup(`<b>${r.nome}</b><br>${r.latitude.toFixed(4)},${r.longitude.toFixed(4)}`);
    marcadores.push(m);
}

function adicionarClusters() {
    const cores = ["#FF6B6B","#4ECDC4","#45B7D1","#96CEB4","#FFEAA7","#DDA0DD"];

    mapaData.clusters.forEach((c,i)=>{
        const cor = cores[i % cores.length];

        const circulo = L.circle([c.centro_lat,c.centro_lng],{
            color:cor,fillColor:cor,fillOpacity:.08,radius:c.raio*1000
        }).addTo(mapa);
        circulosCluster.push(circulo);

        const centro = L.marker([c.centro_lat,c.centro_lng],{
            icon:L.divIcon({html:"⭐",className:"cluster-centro-icon"})
        }).addTo(mapa);

        centroMarkers.push(centro);

        (c.entregas||[]).forEach(e=>{
            const m = L.marker([e.latitude,e.longitude],{
                icon:L.divIcon({html:"📦",className:"entrega-marker"})
            }).addTo(mapa);

            m.bindPopup(`
                <b>Entrega #${e.pedido_id}</b><br>
                R$ ${e.valor.toFixed(2)}<br>
                ${e.endereco}
            `);

            marcadores.push(m);
        });
    });
}

function adicionarRotas() {
    const cores = ["#FF4444","#44FF44","#4444FF","#FF44FF","#44FFFF"];

    mapaData.rotas.forEach((rota,i)=>{
        const cor = cores[i%cores.length];
        const coords = rota.coordenadas.map(c=>[c.lat,c.lng]);

        const p = L.polyline(coords,{color:cor,weight:4,opacity:.75})
            .addTo(mapa)
            .bindPopup(`
                <b>${rota.entregador_nome}</b><br>
                ${rota.num_entregas} entregas<br>
                ${rota.distancia_km.toFixed(2)}km - ${rota.tempo_minutos}min
            `);

        polylines.push(p);
    });
}

// liga entregas próximas (~1km)
function adicionarConexoesEspaciais(){
    const entregas = mapaData.clusters.flatMap(c=>c.entregas||[]);

    entregas.forEach((e1,i)=>{
        entregas.slice(i+1).forEach(e2=>{
            const dist = calcDistance(e1.latitude,e1.longitude,e2.latitude,e2.longitude);
            if(dist<=1.1){
                L.polyline([[e1.latitude,e1.longitude],[e2.latitude,e2.longitude]],{
                    color:"#777",weight:1.3,dashArray:"4,6",opacity:.5
                }).addTo(mapa);
            }
        });
    });
}

// --- Controles ---
document.addEventListener("DOMContentLoaded",()=>{
    inicializarMapa();

    document.getElementById("btn-show-clusters").onclick=()=>{
        circulosCluster.forEach(c=>{
            if(mapa.hasLayer(c)) mapa.removeLayer(c)
            else mapa.addLayer(c);
        });
        centroMarkers.forEach(m=>{
            if(mapa.hasLayer(m)) mapa.removeLayer(m)
            else mapa.addLayer(m);
        });
    };

    document.getElementById("btn-show-routes").onclick=()=>{
        polylines.forEach(p=>{
            if(mapa.hasLayer(p)) mapa.removeLayer(p)
            else mapa.addLayer(p);
        });
    };

    document.getElementById("btn-reset-view").onclick=()=>{
        mapa.setView([-23.5505,-46.6333],12);
    };
});
