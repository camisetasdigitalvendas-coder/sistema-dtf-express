import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text

# 1. Configuração de Layout e Visual ERP
st.set_page_config(layout="wide", page_title="Sistema DTF EXPRESS", page_icon="🖨️")

st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetric"] {
        background-color: white; padding: 15px 20px; border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #e9ecef;
    }
    div[data-testid="stForm"] {
        background-color: white; padding: 20px; border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05); border: 1px solid #e9ecef;
    }
    </style>
""", unsafe_allow_html=True)

# 2. Conexão com o Banco de Dados Real (PostgreSQL)
conn = st.connection("postgresql", type="sql")

# Criação automática de tabelas de Clientes e Serviços caso não existam
def inicializar_banco_de_dados():
    try:
        with conn.session as session:
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS clientes (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(255) UNIQUE NOT NULL
                );
            """))
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS servicos (
                    id SERIAL PRIMARY KEY,
                    nome VARCHAR(255) UNIQUE NOT NULL,
                    preco_base NUMERIC(10,2) NOT NULL
                );
            """))
            # Atualiza a tabela de pedidos para vincular com as novas opções
            session.execute(text("ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS dtf_pronto BOOLEAN DEFAULT FALSE;"))
            session.execute(text("ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS desconto NUMERIC(10,2) DEFAULT 0.0;"))
            session.execute(text("ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS acrescimo NUMERIC(10,2) DEFAULT 0.0;"))
            session.commit()
    except Exception:
        pass

inicializar_banco_de_dados()

# Funções de busca de dados em tempo real
def buscar_pedidos():
    return conn.query("SELECT id, data, cliente, metros, valor_total, dtf_pronto, pago, retirou, desconto, acrescimo FROM pedidos ORDER BY id DESC;", ttl=0)

def buscar_clientes():
    return conn.query("SELECT nome FROM clientes ORDER BY nome ASC;", ttl=0)

def buscar_servicos():
    return conn.query("SELECT nome, preco_base FROM servicos ORDER BY nome ASC;", ttl=0)

# Carrega os dados do banco
df_pedidos = buscar_pedidos()
df_clientes_db = buscar_clientes()
df_servicos_db = buscar_servicos()

# Cria listas para os menus de seleção (Dropdowns)
lista_clientes = ["Selecionar Cliente..."] + list(df_clientes_db["nome"].unique()) if not df_clientes_db.empty else ["Nenhum cliente cadastrado"]
lista_servicos = ["Selecionar Serviço..."] + list(df_servicos_db["nome"].unique()) if not df_servicos_db.empty else ["Nenhum serviço cadastrado"]

# 3. Criação de Abas do Aplicativo
aba_painel, aba_clientes, aba_servicos, aba_historico = st.tabs([
    "📊 Fila de Pedidos & Caixa", 
    "👤 Cadastro de Clientes", 
    "🛍️ Cadastro de Serviços/Preços", 
    "📜 Histórico Geral"
])

hoje = datetime.now().date()
mes_atual = hoje.month
ano_atual = today_year = hoje.year

# --- ABA 1: PAINEL DE CONTROLE DE PEDIDOS E CAIXA ---
with aba_painel:
    st.title("🖨️ Painel Operacional — DTF EXPRESS")
    
    # Indicadores Financeiros do Dia e do Mês (Pedidos ativos e histórico somados)
    if not df_pedidos.empty:
        df_pedidos["data"] = pd.to_datetime(df_pedidos["data"]).dt.date
        vendas_hoje = df_pedidos[df_pedidos["data"] == hoje]["valor_total"].sum()
        vendas_mes = df_pedidos[
            (pd.to_datetime(df_pedidos["data"]).dt.month == mes_atual) & 
            (pd.to_datetime(df_pedidos["data"]).dt.year == ano_atual)
        ]["valor_total"].sum()
    else:
        vendas_hoje, vendas_mes = 0.0, 0.0

    col_fin1, col_fin2 = st.columns(2)
    with col_fin1:
        st.metric(label="📊 VALOR TOTAL RECEBIDO/LANÇADO HOJE", value=f"R$ {vendas_hoje:,.2f}")
    with col_fin2:
        st.metric(label="📈 FATURAMENTO ACUMULADO DO MÊS", value=f"R$ {vendas_mes:,.2f}")

    st.markdown("---")
    
    col_cadastro, col_operacao = st.columns([1, 2])
    
    with col_cadastro:
        st.subheader("➕ Novo Pedido")
        with st.form("novo_pedido_form", clear_on_submit=True):
            # Puxa o cliente direto do cadastro salvo
            cliente_selecionado = st.selectbox("Cliente", lista_clientes)
            # Puxa o serviço direto do cadastro de preços salvo
            servico_selecionado = st.selectbox("Serviço / Produto", lista_servicos)
            
            metros = st.number_input("Quantidade (Metros ou Unidades)", min_value=0.1, step=0.1, value=1.0)
            
            st.markdown("**Ajustes Extras Financeiros:**")
            desconto = st.number_input("Desconto (R$)", min_value=0.0, step=0.5, value=0.0)
            acrescimo = st.number_input("Acréscimo / Taxa (R$)", min_value=0.0, step=0.5, value=0.0)
            
            btn_salvar = st.form_submit_button("🚀 Enviar para Produção")
            
            if btn_salvar:
                if cliente_selecionado == "Selecionar Cliente..." or servico_selecionado == "Selecionar Serviço...":
                    st.error("Por favor, selecione um Cliente e um Serviço cadastrados.")
                else:
                    # Busca o preço base do serviço selecionado para calcular o valor automático
                    preco_unidade = float(df_servicos_db[df_servicos_db["nome"] == servico_selecionado]["preco_base"].values[0])
                    valor_base = metros * preco_unidade
                    valor_total = float(valor_base + acrescimo - desconto)
                    if valor_total < 0: valor_total = 0.0
                    
                    try:
                        with conn.session as session:
                            sql = text("""
                                INSERT INTO pedidos (data, cliente, metros, valor_total, dtf_pronto, pago, retirou, desconto, acrescimo) 
                                VALUES (:dt, :cli, :met, :val, false, false, false, :desc, :acre);
                            """)
                            session.execute(sql, {
                                "dt": hoje, "cli": str(cliente_selecionado), "met": float(metros), 
                                "val": float(valor_total), "desc": float(desconto), "acre": float(acrescimo)
                            })
                            session.commit()
                        st.success(f"Pedido de {cliente_selecionado} lançado!")
                        st.rerun()
                    except Exception as err:
                        st.error(f"Erro ao salvar pedido: {err}")

    with col_operacao:
        st.subheader("📋 Fila de Impressão e Cobrança Activa")
        
        # Filtros de Busca e Status (Estilo Bling)
        c_busca, c_filtro_pago = st.columns([2, 1])
        with c_busca:
            busca_nome = st.text_input("🔍 Pesquisar por nome do Cliente", placeholder="Digite o nome para buscar e somar...")
        with c_filtro_pago:
            filtro_pago = st.selectbox("Filtrar por Caixa", ["Todos", "Apenas Pagos", "Apenas NÃO PAGOS"])
        
        # Separa apenas os pedidos da fila ativa (O que não foi retirado e pago ao mesmo tempo)
        df_ativa = df_pedidos[~((df_pedidos["pago"] == True) & (df_pedidos["retirou"] == True))] if not df_pedidos.empty else df_pedidos
        
        # Aplica a busca por texto se digitado
        if busca_nome:
            df_ativa = df_ativa[df_ativa["cliente"].str.contains(busca_nome, case=False, na=False)]
            
        # Aplica o filtro de caixa
        if filtro_pago == "Apenas Pagos":
            df_ativa = df_ativa[df_ativa["pago"] == True]
        elif filtro_pago == "Apenas NÃO PAGOS":
            df_ativa = df_ativa[df_ativa["pago"] == False]
            
        # CALCULA E SOMA DA BUSCA ATUAL
        if not df_ativa.empty:
            soma_busca = df_ativa["valor_total"].sum()
            st.markdown(f"**💰 Total Encontrado nesta busca/filtro: R$ {soma_busca:,.2f}**")
            st.markdown("---")
            
            for idx, row in df_ativa.iterrows():
                id_pedido = int(row["id"])
                status_producao = "✨ DTF PRONTO" if row.get("dtf_pronto", False) else "⏳ IMPRIMINDO"
                status_pago = "🟢 PAGO" if row["pago"] else "🔴 NÃO PAGO"
                status_entrega = "📦 RETIROU" if row["retirou"] else "⏳ PENDENTE"
                
                with st.container():
                    c_info, c_b1, c_b2, c_b3, c_st, c_del = st.columns([1.8, 1.1, 1.1, 1.1, 1.3, 0.3])
                    
                    with c_info:
                        st.markdown(f"👤 **{row['cliente']}**")
                        st.markdown(f"<small style='color:gray;'>{row['metros']} un/m | {row['data'].strftime('%d/%m/%Y')}</small>", unsafe_allow_html=True)
                        st.markdown(f"**Total: R$ {row['valor_total']:,.2f}**")
                    
                    with c_b1:
                        if st.button("Finalizar DTF" if not row.get("dtf_pronto", False) else "Voltar p/ Fila", key=f"f_p_{id_pedido}", use_container_width=True):
                            with conn.session as session:
                                session.execute(text("UPDATE pedidos SET dtf_pronto = :p WHERE id = :id;"), {"p": not row.get("dtf_pronto", False), "id": id_pedido})
                                session.commit()
                            st.rerun()
                    with c_b2:
                        if st.button("Dar Baixa (Pago)" if not row["pago"] else "Marcar Aberto", key=f"f_f_{id_pedido}", use_container_width=True):
                            with conn.session as session:
                                session.execute(text("UPDATE pedidos SET pago = :p WHERE id = :id;"), {"p": not row["pago"], "id": id_pedido})
