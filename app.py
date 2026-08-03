import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text

# 1. Configuração de Layout e Tema Limpo
st.set_page_config(layout="wide", page_title="ERP DTF - Sistema de Gestão", page_icon="📦")

# CSS customizado para deixar a interface limpa e elegante (Estilo Bling)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetric"] {
        background-color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
    }
    div[data-testid="stForm"] {
        background-color: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #e9ecef;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📦 Bling DTF — Painel de Controle")
st.caption("Gerenciamento profissional de pedidos e fluxo de caixa em tempo real.")

# 2. Conexão com o Banco de Dados Real (PostgreSQL)
conn = st.connection("postgresql", type="sql")

def buscar_dados():
    return conn.query("SELECT id, data, cliente, metros, valor_total, pago, retirou FROM pedidos ORDER BY id DESC;", ttl=0)

try:
    df_pedidos = buscar_dados()
except Exception as e:
    st.error(f"Erro de conexão com o banco de dados: {e}")
    df_pedidos = pd.DataFrame(columns=["id", "data", "cliente", "metros", "valor_total", "pago", "retirou"])

# 3. Indicadores Financeiros de Destaque
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

col_financeiro1, col_financeiro2 = st.columns(2)
with col_financeiro1:
    st.metric(label="📊 FATURAMENTO DIÁRIO (HOJE)", value=f"R$ {vendas_hoje:,.2f}")
with col_financeiro2:
    st.metric(label="📈 TOTAL ACUMULADO DO MÊS", value=f"R$ {vendas_mes:,.2f}")

st.markdown("---")

# 4. Área de Trabalho Dividida (Lançamento à esquerda, Painel à direita)
col_cadastro, col_painel = st.columns([1, 2])

with col_cadastro:
    st.subheader("➕ Incluir Pedido")
    with st.form("novo_pedido_form", clear_on_submit=True):
        cliente = st.text_input("Nome do Cliente", placeholder="Ex: João Silva")
        metros = st.number_input("Metragem DTF (m)", min_value=0.1, step=0.1, value=1.0)
        preco_metro = st.number_input("Preço por Metro (R$)", min_value=1.0, value=30.0, step=1.0)
        
        btn_salvar = st.form_submit_button("✨ Salvar Pedido no Bling")
        
        if btn_salvar and cliente:
            valor_total = float(metros * preco_metro)
            try:
                with conn.session as session:
                    sql = text("""
                        INSERT INTO pedidos (data, cliente, metros, valor_total, pago, retirou) 
                        VALUES (:dt, :cli, :met, :val, false, false);
                    """)
                    session.execute(sql, {"dt": hoje, "cli": str(cliente), "met": float(metros), "val": float(valor_total)})
                    session.commit()
                st.success("Pedido registrado!")
                st.rerun()
            except Exception as err:
                st.error(f"Erro ao salvar: {err}")

with col_painel:
    st.subheader("📋 Lista de Pedidos Cadastrados")
    
    # Filtros Rápidos Estilo ERP
    filtro = st.radio("Filtro rápido por status de pagamento:", ["Todos", "Apenas Pagos", "Apenas Não Pagos"], horizontal=True)
    
    df_filtrado = df_pedidos.copy()
    if filtro == "Apenas Pagos":
        df_filtrado = df_filtrado[df_filtrado["pago"] == True]
    elif filtro == "Apenas Não Pagos":
        df_filtrado = df_filtrado[df_filtrado["pago"] == False]

    if not df_filtrado.empty:
        # Loop para criar uma lista limpa com ações diretas linha por linha
        for idx, row in df_filtrado.iterrows():
            id_pedido = int(row["id"])
            
            # Formatação de textos e cores para os badges
            status_pago = "🟢 PAGO" if row["pago"] else "🔴 NÃO PAGO"
            status_entrega = "📦 RETIROU" if row["retirou"] else "⏳ PENDENTE RETIRADA"
            
            # Caixa visual de cada pedido
            with st.container():
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                
                with c1:
                    st.markdown(f"**Cliente:** {row['cliente']} | **Data:** {row['data'].strftime('%d/%m/%Y')}")
                    st.markdown(f"<small style='color:gray;'>{row['metros']}m de DTF — Total: R$ {row['valor_total']:,.2f}</small>", unsafe_allow_html=True)
                
                with c2:
                    # Botão para alternar pagamento
                    label_pago = "Mudar p/ Não Pago" if row["pago"] else "Dar Baixa (Pago)"
                    if st.button(label_pago, key=f"pago_{id_pedido}"):
                        with conn.session as session:
                            session.execute(text("UPDATE pedidos SET pago = :pago WHERE id = :id;"), {"pago": not row["pago"], "id": id_pedido})
                            session.commit()
                        st.rerun()
                
                with c3:
                    # Botão para alternar retirada
                    label_retirou = "Mudar p/ Pendente" if row["retirou"] else "Confirmar Retirada"
                    if st.button(label_retirou, key=f"retirou_{id_pedido}"):
                        with conn.session as session:
                            session.execute(text("UPDATE pedidos SET retirou = :retirou WHERE id = :id;"), {"retirou": not row["retirou"], "id": id_pedido})
                            session.commit()
                        st.rerun()
                        
                with c4:
                    st.markdown(f"**{status_pago}**")
                    st.markdown(f"<small>{status_entrega}</small>", unsafe_allow_html=True)
                
                st.markdown("<hr style='margin: 8px 0; border-color: #eee;'>", unsafe_allow_html=True)
    else:
        st.info("Nenhum pedido encontrado para o filtro selecionado.")
