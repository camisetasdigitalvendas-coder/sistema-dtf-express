import streamlit as st
import pandas as pd
from datetime import datetime

# 1. Configuração da página para PC e Celular
st.set_page_config(layout="wide", page_title="Gestão DTF")
st.title("🖨️ Gestão de Pedidos em Tempo Real - DTF")

# 2. Conexão com o Banco de Dados Real (PostgreSQL)
conn = st.connection("postgresql", type="sql")

# 3. Função para buscar os dados atualizados do banco
def buscar_dados():
    return conn.query("SELECT id, data, cliente, metros, valor_total, pago, retirou FROM pedidos ORDER BY id DESC;", ttl=0)

try:
    df_pedidos = buscar_dados()
except Exception as e:
    st.error("Erro ao conectar ao banco de dados. Verifique as configurações.")
    df_pedidos = pd.DataFrame(columns=["id", "data", "cliente", "metros", "valor_total", "pago", "retirou"])

# 4. Cálculos de Faturamento em Tempo Real (Dia e Mês)
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
    vendas_hoje = 0.0
    vendas_mes = 0.0

# 5. Exibição dos Indicadores Financeiros
st.subheader("💰 Resumo Financeiro (Atualizado)")
col_dia, col_mes = st.columns(2)
with col_dia:
    st.metric(label="Vendas de Hoje", value=f"R$ {vendas_hoje:,.2f}")
with col_mes:
    st.metric(label="Vendas do Mês Atual", value=f"R$ {vendas_mes:,.2f}")

st.markdown("---")

# 6. Formulário para Entrada de Novos Pedidos
st.subheader("➕ Novo Pedido")
with st.form("formulario_pedido", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        cliente = st.text_input("Nome do Cliente")
    with col2:
        metros = st.number_input("Metros de DTF", min_value=0.1, step=0.1, value=1.0)
    with col3:
        preco_metro = st.number_input("Preço por Metro (R$)", min_value=1.0, value=30.0, step=1.0)
    
    cadastrar = st.form_submit_button("Inserir Pedido no Sistema")
    
    if cadastrar and cliente:
        valor_total = metros * preco_metro
        data_atual = hoje.strftime("%Y-%m-%d")
        
        with conn.session as session:
            session.execute(
                "INSERT INTO pedidos (data, cliente, metros, valor_total, pago, retirou) VALUES (:data, :cliente, :metros, :valor_total, false, false);",
                {"data": data_atual, "cliente": cliente, "metros": metros, "valor_total": valor_total}
            )
            session.commit()
        st.success(f"Pedido de {cliente} salvo na nuvem!")
        st.rerun()

st.markdown("---")

# 7. Painel de Controle Lado a Lado
st.subheader("📊 Painel de Pedidos Ativos")
st.caption("Altere o status de 'Pago' ou 'Retirou' e clique em 'Salvar Alterações' abaixo da tabela.")

if not df_pedidos.empty:
    pedidos_editados = st.data_editor(
        df_pedidos, 
        disabled=["id", "data", "cliente", "metros", "valor_total"],
        use_container_width=True,
        key="editor_pedidos"
    )

    if st.button("💾 Salvar Alterações de Status"):
        with conn.session as session:
            for index, row in pedidos_editados.iterrows():
                session.execute(
                    "UPDATE pedidos SET pago = :pago, retirou = :retirou WHERE id = :id;",
                    {"pago": bool(row["pago"]), "retirou": bool(row["retirou"]), "id": int(row["id"])}
                )
            session.commit()
        st.success("Banco de dados atualizado para todos os usuários!")
        st.rerun()
else:
    st.info("Nenhum pedido cadastrado ainda.")
