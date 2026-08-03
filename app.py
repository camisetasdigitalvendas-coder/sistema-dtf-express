import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text

# 1. Configuração do Sistema e Layout Responsivo
st.set_page_config(layout="wide", page_title="DTF EXPRESS - Sistema de Gestão", page_icon="🖨️")

# CSS Avançado para a Interface Profissional do DTF EXPRESS
st.markdown("""
    <style>
    /* Estilo Geral do Fundo */
    .main, .stApp { background-color: #ffffff !important; }
    
    /* Inputs e Seletores Customizados */
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
    
    /* Badges de Status Modernos */
    .badge { padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; display: inline-block; margin-right: 5px; margin-bottom: 2px; }
    .badge-success { background-color: #dcfce7; color: #15803d; }
    .badge-danger { background-color: #fee2e2; color: #b91c1c; }
    .badge-warning { background-color: #fef9c3; color: #a16207; }
    .badge-info { background-color: #e0f2fe; color: #0369a1; }
    </style>
""", unsafe_allow_html=True)

# Cabeçalho Fixo do Sistema
st.markdown("<h2 style='color:#0f172a; margin-bottom:2px; font-weight:700;'>🖨️ DTF EXPRESS — Painel de Controle</h2>", unsafe_allow_html=True)
st.markdown("<p style='color:#64748b; font-size:13px; margin-bottom:25px;'>Módulo Profissional de Gestão Operacional e Financeira</p>", unsafe_allow_html=True)

# 2. Conexão com o Banco de Dados Real (PostgreSQL)
conn = st.connection("postgresql", type="sql")

def buscar_pedidos():
    return conn.query("SELECT id, data, cliente, metros, valor_total, dtf_pronto, pago, retirou, desconto, acrescimo FROM pedidos ORDER BY id DESC;", ttl=0)

def buscar_clientes():
    return conn.query("SELECT nome FROM clientes ORDER BY nome ASC;", ttl=0)

def buscar_servicos():
    return conn.query("SELECT nome, preco_base FROM servicos ORDER BY nome ASC;", ttl=0)

# Carregamento dos dados seguros
df_pedidos = buscar_pedidos()
df_clientes_db = buscar_clientes()
df_servicos_db = buscar_servicos()

lista_clientes = ["Selecionar Cliente..."] + list(df_clientes_db["nome"].unique()) if not df_clientes_db.empty else ["Nenhum cliente cadastrado"]
lista_servicos = ["Selecionar Serviço..."] + list(df_servicos_db["nome"].unique()) if not df_servicos_db.empty else ["Nenhum serviço cadastrado"]

# 3. Blocos Financeiros Superiores
hoje = datetime.now().date()
mes_atual = hoje.month
ano_atual = hoje.year

if not df_pedidos.empty:
    df_pedidos["data"] = pd.to_datetime(df_pedidos["data"]).dt.date
    vendas_hoje = df_pedidos[df_pedidos["data"] == hoje]["valor_total"].sum()
    vendas_mes = df_pedidos[
        (pd.to_datetime(df_pedidos["data"]).dt.month == mes_atual) & 
        (pd.to_datetime(df_pedidos["data"]).dt.year == ano_atual)
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

# 4. Navegação pelas Abas Organizadas
aba_vendas, aba_extratos, aba_clientes, aba_servicos, aba_historico = st.tabs([
    "🛒 Itens do Pedido de Venda", 
    "📊 Extratos Mensais",
    "👤 Cadastro de Clientes", 
    "🛍️ Cadastro de Serviços/Preços", 
    "📜 Histórico Geral"
])

# --- ABA 1: PEDIDOS E FLUXO DIÁRIO ---
with aba_vendas:
    st.markdown("<h4 style='color:#334155; font-size:15px; margin-bottom:15px; font-weight:600;'>📋 Novo Lançamento de Venda</h4>", unsafe_allow_html=True)
    
    with st.form("form_dtf_pedido", clear_on_submit=True):
        c_cli, c_vend, c_loja, c_uni = st.columns([2.5, 1.5, 1.5, 1.5])
        with c_cli:
            cliente_sel = st.selectbox("Cliente *", lista_clientes)
        with c_vend:
            st.selectbox("Vendedor", ["Nenhum Vendedor", "Balcão", "Produção"])
        with c_loja:
            st.selectbox("Loja", ["Nenhuma Loja", "Matriz"])
        with c_uni:
            st.selectbox("Unidade de negócio", ["Nenhuma unidade de negócio"])
            
        c_serv, c_qtd, c_desc, c_acre = st.columns([2.5, 1.5, 1.5, 1.5])
        with c_serv:
            servico_sel = st.selectbox("Descrição / Serviço *", lista_servicos)
        with c_qtd:
            metros = st.number_input("Quantidade (m ou un)", min_value=0.1, step=0.1, value=1.0)
        with c_desc:
            desconto = st.number_input("Desc (R$)", min_value=0.0, step=0.5, value=0.0)
        with c_acre:
            acrescimo = st.number_input("Acréscimo / Taxa (R$)", min_value=0.0, step=0.5, value=0.0)
            
        c_space, c_btn = st.columns([5.5, 1.5])
        with c_btn:
            btn_salvar = st.form_submit_button("＋ Adicionar Item", use_container_width=True)
            
        if btn_salvar:
            if cliente_sel == "Selecionar Cliente..." or servico_sel == "Selecionar Serviço...":
                st.error("Por favor, selecione um Cliente e um Serviço cadastrados antes.")
            else:
                preco_base = float(df_servicos_db[df_servicos_db["nome"] == servico_sel]["preco_base"].values)
                valor_total = float((metros * preco_base) + acrescimo - desconto)
                if valor_total < 0: valor_total = 0.0
                
                try:
                    with conn.session as session:
                        session.execute(text("""
                            INSERT INTO pedidos (data, cliente, metros, valor_total, dtf_pronto, pago, retirou, desconto, acrescimo) 
                            VALUES (:dt, :cli, :met, :val, false, false, false, :desc, :acre);
                        """), {"dt": hoje, "cli": str(cliente_sel), "met": float(metros), "val": float(valor_total), "desc": float(desconto), "acre": float(acrescimo)})
                        session.commit()
                    st.success("Pedido adicionado à fila!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

    st.markdown("---")
    st.markdown("<h4 style='color:#334155; font-size:15px; font-weight:600; margin-bottom:15px;'>📋 Fila de Pedidos Ativos</h4>", unsafe_allow_html=True)
    
    c_pesq, c_flt = st.columns(2)
    with c_pesq:
        pesquisa = st.text_input("🔍 Procurar por Cliente", placeholder="Digite o nome do cliente para buscar e somar...")
    with c_flt:
        filtro_status = st.selectbox("Status Financeiro", ["Todos os Pedidos", "Apenas Não Pagos", "Apenas Pagos"])

    # Filtra fila ativa (O que não foi pago e retirado ao mesmo tempo)
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
        
        # Grid Operacional com Status e Botões de Controle Lado a Lado
        for idx, row in df_ativos.iterrows():
            id_p = int(row["id"])
            lbl_prod = "✨ PRONTO" if row.get("dtf_pronto", False) else "⏳ IMPRIMINDO"
            cls_prod = "badge-success" if row.get("dtf_pronto", False) else "badge-warning"
            
            lbl_pago = "🟢 PAGO" if row["pago"] else "🔴 NÃO PAGO"
            cls_pago = "badge-success" if row["pago"] else "badge-danger"
            
            lbl_ret = "📦 RETIROU" if row["retirou"] else "⏳ PENDENTE"
            cls_ret = "badge-info" if row["retirou"] else "badge-warning"

            col_inf, col_bt1, col_bt2, col_bt3, col_st, col_dl = st.columns([2.5, 1.1, 1.1, 1.1, 1.2, 0.3])
            
            with col_inf:
                st.markdown(f"👤 **{row['cliente']}**")
                st.markdown(f"<small style='color:gray;'>{row['metros']} un/m | Desc: R$ {row['desconto']} | Taxa: R$ {row['acrescimo']}</small><br>Total: **R$ {row['valor_total']:,.2f}**", unsafe_allow_html=True)
            with col_bt1:
