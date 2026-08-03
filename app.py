import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text

# 1. Configuração do Sistema e Layout Responsivo
st.set_page_config(layout="wide", page_title="Bling ERP - DTF EXPRESS", page_icon="📦")

# CSS Avançado para Emular Perfeitamente a Interface do Bling ERP
st.markdown("""
    <style>
    /* Estilo Geral do Fundo */
    .main, .stApp { background-color: #ffffff !important; }
    
    /* Inputs e Seletores Estilo Bling */
    div[data-testid="stForm"] {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 6px !important;
        padding: 24px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
    }
    input, select, .stSelectbox div[data-baseweb="select"] {
        border-radius: 4px !important;
        border: 1px solid #cbd5e1 !important;
        height: 38px !important;
    }
    
    /* Indicadores Financeiros Limpos no Topo */
    .metric-container {
        display: flex; gap: 20px; margin-bottom: 25px;
    }
    .metric-box {
        background: #f8fafc; border: 1px solid #e2e8f0;
        padding: 15px 25px; border-radius: 6px; flex: 1;
    }
    .metric-title { font-size: 11px; color: #64748b; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; }
    .metric-value { font-size: 24px; color: #0f172a; font-weight: 700; margin-top: 5px; }
    
    /* Abas Customizadas (Tabs) */
    button[data-baseweb="tab"] {
        font-size: 14px !important; font-weight: 600 !important;
        color: #64748b !important; border-bottom: 2px solid transparent !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #0284c7 !important; border-bottom: 2px solid #0284c7 !important;
    }
    
    /* Tabela de Itens Padrão ERP Bling */
    .erp-table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 13px; }
    .erp-table th { background-color: #f8fafc; color: #475569; text-align: left; padding: 10px 14px; font-weight: 600; border-bottom: 2px solid #e2e8f0; }
    .erp-table td { padding: 14px; border-bottom: 1px solid #f1f5f9; color: #334155; vertical-align: middle; }
    .erp-table tr:hover { background-color: #f8fafc; }
    
    /* Badges de Status Modernos */
    .badge { padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; display: inline-block; }
    .badge-success { background-color: #dcfce7; color: #15803d; }
    .badge-danger { background-color: #fee2e2; color: #b91c1c; }
    .badge-warning { background-color: #fef9c3; color: #a16207; }
    .badge-info { background-color: #e0f2fe; color: #0369a1; }
    </style>
""", unsafe_allow_html=True)

# Cabeçalho Fixo do Sistema
st.markdown("<h2 style='color:#0f172a; margin-bottom:2px; font-weight:700;'>📦 Bling ERP — Vendas e Impressão</h2>", unsafe_allow_html=True)
st.markdown("<p style='color:#64748b; font-size:13px; margin-bottom:25px;'>Módulo Avançado de Gestão Operacional DTF EXPRESS</p>", unsafe_allow_html=True)

# 2. Conexão com o Banco de Dados Real (PostgreSQL)
conn = st.connection("postgresql", type="sql")

def buscar_pedidos():
    return conn.query("SELECT id, data, cliente, metros, valor_total, dtf_pronto, pago, retirou, desconto, acrescimo FROM pedidos ORDER BY id DESC;", ttl=0)

def buscar_clientes():
    return conn.query("SELECT nome FROM clientes ORDER BY nome ASC;", ttl=0)

def buscar_servicos():
    return conn.query("SELECT nome, preco_base FROM servicos ORDER BY nome ASC;", ttl=0)

# Carregamento dos dados
df_pedidos = buscar_pedidos()
df_clientes_db = buscar_clientes()
df_servicos_db = buscar_servicos()

lista_clientes = ["Selecionar Cliente..."] + list(df_clientes_db["nome"].unique()) if not df_clientes_db.empty else ["Nenhum cliente cadastrado"]
lista_servicos = ["Selecionar Serviço..."] + list(df_servicos_db["nome"].unique()) if not df_servicos_db.empty else ["Nenhum serviço cadastrado"]

# 3. Blocos Financeiros Superiores (Estilo Bling Dashboard)
if not df_pedidos.empty:
    df_pedidos["data"] = pd.to_datetime(df_pedidos["data"]).dt.date
    vendas_hoje = df_pedidos[df_pedidos["data"] == datetime.now().date()]["valor_total"].sum()
    vendas_mes = df_pedidos[
        (pd.to_datetime(df_pedidos["data"]).dt.month == datetime.now().month) & 
        (pd.to_datetime(df_pedidos["data"]).dt.year == datetime.now().year)
    ]["valor_total"].sum()
else:
    vendas_hoje, vendas_mes = 0.0, 0.0

st.markdown(f"""
    <div class='metric-container'>
        <div class='metric-box'>
            <div class='metric-title'>📊 Faturamento Diário (Hoje)</div>
            <div class='metric-value'>R$ {vendas_hoje:,.2f}</div>
        </div>
        <div class='metric-box'>
            <div class='metric-title'>📈 Total Acumulado do Mês</div>
            <div class='metric-value'>R$ {vendas_mes:,.2f}</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# 4. Navegação por Abas Limpas
aba_vendas, aba_clientes, aba_servicos, aba_historico = st.tabs([
    "🛒 Itens do Pedido de Venda", 
    "👤 Cadastro de Clientes", 
    "🛍️ Cadastro de Serviços/Preços", 
    "📜 Histórico Geral"
])

# --- ABA 1: PEDIDOS E ENTRADAS ---
with aba_vendas:
    # Cabeçalho do Pedido (Igual ao seu Print)
    st.markdown("<h4 style='color:#334155; font-size:15px; margin-bottom:15px; font-weight:600;'>📋 Novo Lançamento de Venda</h4>", unsafe_allow_html=True)
    
    with st.form("form_bling_pedido", clear_on_submit=True):
        # Linha 1 do Print: Cliente, Vendedor, Loja, Unidade
        c_cli, c_vend, c_loja, c_uni = st.columns([2.5, 1.5, 1.5, 1.5])
        with c_cli:
            cliente_sel = st.selectbox("Cliente *", lista_clientes)
        with c_vend:
            st.selectbox("Vendedor", ["Nenhum Vendedor", "Balcão", "Produção"])
        with c_loja:
            st.selectbox("Loja", ["Nenhuma Loja", "Matriz"])
        with c_uni:
            st.selectbox("Unidade de negócio", ["Nenhuma unidade de negócio"])
            
        # Linha 2 do Print: Serviço, Quantidade, Ajustes
        c_serv, c_qtd, c_desc, c_acre = st.columns([2.5, 1.5, 1.5, 1.5])
        with c_serv:
            servico_sel = st.selectbox("Descrição / Serviço *", lista_servicos)
        with c_qtd:
            metros = st.number_input("Quantidade (m ou un)", min_value=0.1, step=0.1, value=1.0)
        with c_desc:
            desconto = st.number_input("Desc (R$)", min_value=0.0, step=0.5, value=0.0)
        with c_acre:
            acrescimo = st.number_input("Acréscimo / Taxa (R$)", min_value=0.0, step=0.5, value=0.0)
            
        # Botão Alinhado à Direita para Salvar
        c_space, c_btn = st.columns([5, 1])
        with c_btn:
            btn_salvar = st.form_submit_button("＋ Adicionar Item", use_container_width=True)
            
        if btn_salvar:
            if cliente_sel == "Selecionar Cliente..." or servico_sel == "Selecionar Serviço...":
                st.error("Selecione um Cliente e um Serviço válidos.")
            else:
                preco_base = float(df_servicos_db[df_servicos_db["nome"] == servico_sel]["preco_base"].values)
                valor_total = float((metros * preco_base) + acrescimo - desconto)
                if valor_total < 0: valor_total = 0.0
                
                try:
                    with conn.session as session:
                        session.execute(text("""
                            INSERT INTO pedidos (data, cliente, metros, valor_total, dtf_pronto, pago, retirou, desconto, acrescimo) 
                            VALUES (:dt, :cli, :met, :val, false, false, false, :desc, :acre);
                        """), {"dt": datetime.now().date(), "cli": str(cliente_sel), "met": float(metros), "val": float(valor_total), "desc": float(desconto), "acre": float(acrescimo)})
                        session.commit()
                    st.success("Item inserido com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

    st.markdown("---")
    
    # Filtros e Tabela de Pedidos Ativos
    st.markdown("<h4 style='color:#334155; font-size:15px; margin-weight:600; margin-bottom:15px;'>📋 Fila de Pedidos Ativos</h4>", unsafe_allow_html=True)
    
    c_pesq, c_flt = st.columns([4, 2])
    with c_pesq:
        pesquisa = st.text_input("🔍 Procurar por Cliente", placeholder="Digite o nome do cliente para buscar e somar...")
    with c_flt:
        filtro_status = st.selectbox("Status Financeiro", ["Todos os Pedidos", "Apenas Não Pagos", "Apenas Pagos"])

    # Filtra pedidos ativos (O que não foi pago e retirado ao mesmo tempo)
    df_ativos = df_pedidos[~((df_pedidos["pago"] == True) & (df_pedidos["retirou"] == True))] if not df_pedidos.empty else df_pedidos

    if pesquisa and not df_ativos.empty:
        df_ativos = df_ativos[df_ativos["cliente"].str.contains(pesquisa, case=False, na=False)]
    if filtro_status == "Apenas Não Pagos" and not df_ativos.empty:
        df_ativos = df_ativos[df_ativos["pago"] == False]
    elif filtro_status == "Apenas Pagos" and not df_ativos.empty:
        df_ativos = df_ativos[df_ativos["pago"] == True]

    if not df_ativos.empty:
        soma_total_filtro = df_ativos["valor_total"].sum()
        st.markdown(f"<p style='font-size:15px; color:#0284c7; font-weight:700;'>💰 Total Pendente/Localizado nesta Busca: R$ {soma_total_filtro:,.2f}</p>", unsafe_allow_html=True)
        
        # Estrutura de Tabela Horizontal Estilo Bling
        html_tabela = """
        <table class='erp-table'>
            <thead>
                <tr>
                    <th>Cliente</th>
                    <th>Data</th>
                    <th>Detalhes</th>
                    <th>Total</th>
                    <th>Status Impressão</th>
                    <th>Status Caixa</th>
                    <th>Status Saída</th>
                </tr>
            </thead>
            <tbody>
        """
