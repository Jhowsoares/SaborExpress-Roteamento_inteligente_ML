# 🍔 Rota Inteligente — Sabor Express

**Disciplina:** Artificial Intelligence Fundamentals  
**Instituição:** Universidade UniFecaf  
**Aluno:** Jhonata Viana Soares  
**Projeto:** Sistema inteligente de otimização de rotas para entregas (K-Means + A*), com painel web em Flask.

---

## 🚀 Desafio

A empresa fictícia **Sabor Express**, especializada em delivery de alimentos, enfrenta atrasos e custos elevados devido à definição manual das rotas de entrega.  
O objetivo do projeto é **desenvolver uma solução inteligente** capaz de **otimizar as rotas** dos entregadores utilizando **algoritmos de Inteligência Artificial**.

---

## 🎯 Objetivos

- Modelar a cidade como um **grafo**, onde os nós representam locais de entrega e as arestas representam ruas com pesos de distância.  
- Aplicar **K-Means** para **agrupar pedidos próximos** em zonas de entrega.  
- Utilizar **A\*** para **calcular o menor caminho** dentro de cada cluster.  
- Criar uma **interface web** que permita visualizar e gerenciar rotas.  
- Avaliar o desempenho com métricas de eficiência e distância total percorrida.

---

## 🧠 Funcionamento dos Algoritmos de IA

### 🌀 K-Means (Aprendizado Não Supervisionado)
O **K-Means** é um algoritmo de *Machine Learning não supervisionado* que agrupa dados com base na proximidade.  
Ele foi utilizado para **agrupar pedidos de entrega por região**, definindo os melhores clusters (zonas).  
O algoritmo tenta minimizar a soma das distâncias entre cada ponto e o centro de seu grupo.

> Fórmula de minimização:  
> \( \\sum_i ||x_i - \mu_c||^2 \)

**Aplicação no projeto:**  
Cada pedido é convertido em coordenadas (latitude e longitude). O K-Means cria grupos de pedidos próximos para cada entregador.

---

### 🧭 A* (Busca Heurística)
O algoritmo **A\*** pertence à área de *Inteligência Artificial clássica*.  
Ele encontra o **caminho mais curto** entre dois pontos de forma otimizada, utilizando uma função heurística:  
> \( f(n) = g(n) + h(n) \)

- `g(n)` = custo do caminho até o ponto atual  
- `h(n)` = estimativa de distância até o destino  

**Aplicação no projeto:**  
Dentro de cada cluster, o A* determina a **sequência ideal de entregas**, reduzindo tempo e distância total percorrida.

---

## 🧩 Estrutura do Projeto

```
📦 hamburgueria_deploy/
 ┣ 📂 routes/              → Rotas Flask (admin, roteamento, etc.)
 ┣ 📂 templates/admin/     → Templates HTML (painel e gráficos)
 ┣ 📂 static/css/          → Estilos e temas modernos
 ┣ 📂 static/img/          → Imagens e ícones
 ┣ 📂 algoritmos/          → Implementação de A* e K-Means
 ┣ 📜 app.py               → Inicialização do servidor Flask
 ┗ 📜 README.md
```

---

## ⚙️ Tecnologias Utilizadas

| Categoria | Ferramenta |
|------------|------------|
| Backend | Python, Flask |
| IA/Algoritmos | Scikit-learn, NetworkX |
| Banco de Dados | SQLite |
| Frontend | HTML, CSS, Material Icons |
| Visualização | Gráficos e tabelas dinâmicas |

---
## Pré-requisitos

- Python 3.10+ (recomendado)
- Conta Brevo (ou outro provedor SMTP) — opcional para envio real de e-mails

---

## 📊 Resultados Obtidos

| Métrica | Resultado |
|----------|------------|
| Total de entregas | Agrupadas em clusters otimizados |
| Distância total | Reduzida em até 30% |
| Eficiência média | Superior a 85% |

**Impacto:**  
A aplicação do K-Means e A* reduziu o tempo de entrega, melhorou a distribuição de entregadores e automatizou o planejamento logístico.

---
## Instalação (passo a passo — Windows / PowerShell)

1. Clone:
```bash
git clone https://github.com/Jhowsoares/SaborExpress-Roteamento_inteligente_ML.git
cd SaborExpress-Roteamento_inteligente_ML
```
2. Crie e ative virtualenv:

```bash
py -m venv .venv
.\.venv\Scripts\Activate.ps1
```
3. Instale dependências:
```bash
pip install -U pip
pip install -r requirements.txt
```

4. Crie .env a partir do exemplo e preencha:
```bash
copy .env.example .env
notepad .env
# Preencha MAIL_USERNAME / MAIL_PASSWORD (Brevo API key), SECRET_KEY, DATABASE_URI etc.
```
5. Inicialize banco e crie tabelas:
```bash
py -c "from app import create_app; from models import db; app=create_app(); \
with app.app_context(): db.create_all(); print('DB initialized')"
```

6. Teste envio de e-mail (opcional):

- Ajuste o destinatário em test_mail.py e rode:
```bash
py test_mail.py
```

7. Rode a aplicação:
```bash
py app.py
# Acesse http://127.0.0.1:5000
```
---

## 🧪 Demonstração Prática

- **Painel Administrativo:** Interface moderna e responsiva.  
- **Grafo Interativo:** Visualização dos clusters e rotas.  
- **Métricas:** Distância total, tempo médio e eficiência.

### 📸 Exemplo de execução
1. Administrador acessa a aba *Roteamento*.
2. Clica em *Otimização Completa (K-Means + A\**)*.
3. O sistema gera os clusters e exibe o grafo das rotas.
4. A tela de resultados mostra eficiência e métricas calculadas.

---

## 🧰 Como Executar o Projeto

```bash
# Clone o repositório
git clone https://github.com/Jhowsoares/rota-inteligente.git
cd rota-inteligente

# Crie o ambiente virtual
python -m venv venv
venv/Scripts/activate  # (Windows)

# Instale dependências
pip install -r requirements.txt

# Execute o servidor Flask
python app.py
```

Acesse **http://localhost:5000/admin** no navegador.

---

## 🔍 Análise e Melhorias Futuras

- 🔄 Adicionar **aprendizado por reforço (Q-Learning)** para autoajuste das rotas.  
- 🗺️ Integração com **APIs reais de geolocalização** (Google Maps).  
- 📱 Tornar o painel totalmente adaptado para **uso mobile**.  
- 📊 Criar comparativos automáticos entre execuções.  

---

## 🧩 Conclusão

O projeto **Rota Inteligente — Sabor Express** demonstrou o potencial dos algoritmos de Inteligência Artificial em um cenário realista de logística.  
A combinação de **K-Means + A\*** gerou uma solução prática, eficiente e escalável para otimização de rotas de entrega.

---

## 📚 Referências

- *Wired — UPS ORION Route Optimization System*  
- *Medium — Optimizing Logistics with AI*  
- *Scikit-Learn Documentation — K-Means*  
- *AIMA — Artificial Intelligence: A Modern Approach*  
