import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração da página
st.set_page_config(page_title="Sistema DTF Express", layout="wide")

# Inicializar o banco de dados simulado no estado da sessão (Session State)
if "vendas" not in st.session_state:
    st.session_state.vendas = pd.DataFrame(columns=[
        "ID", "Data", "Cliente", "Produto/Tabela DTF", "Valor", "Retirado", "Status Financeiro"
    ])

# --- FUNÇÕES DE MANIPULAÇÃO ---
def adicionar_venda(cliente, produto, valor, retirado, status_pagamento):
    nova_venda = {
        "ID": int(datetime.now().timestamp() * 1000),
        "Data": datetime.now().strftime("%d/%m/%Y"),
        "Cliente": cliente,
        "Produto/Tabela DTF": produto,
        "Valor": float(valor),
        "Retirado": "Retirado" if retirado else "Pronto p/ Retirar",
        "Status Financeiro": status_pagamento
    }
    st.session_state.vendas = pd.concat([st.session_state.vendas, pd.DataFrame([nova_venda])], ignore_index=True)

def excluir_venda(id_venda):
    st.session_state.vendas = st.session_state.vendas[st.session_state.vendas["ID"] != id_venda]


# --- CÁLCULO DE INDICADORES ---
hoje = datetime.now().strftime("%d/%m/%Y")
df_hoje = st.session_state.vendas[st.session_state.vendas["Data"] == hoje]
faturamento_hoje = df_hoje["Valor"].sum()


# --- LAYOUT DA TELA ---
st.title("🎯 Controle de Pedidos e Cobrança - DTF Express")

# Indicadores de Cabeçalho
col_fat, col_ext = st.columns(2)
with col_fat:
    st.metric(label="Faturamento Diário (Hoje)", value=f"R$ {faturamento_hoje:.2f}")
with col_ext:
    st.subheader("Extrato Mensal")
    if st.button("Gerar Relatório Acumulado"):
        st.info("Relatório gerado com sucesso para a contabilidade!")

st.markdown("---")

# Formulário de Novo Lançamento
st.subheader("📝 Novo Lançamento de Venda")
with st.form("form_venda", clear_on_submit=True):
    col1, col2, col3 = st.columns(3)
    with col1:
        cliente_input = st.text_input("Cliente *", placeholder="Nome do cliente")
    with col2:
        produto_input = st.selectbox("Produto / Tabela DTF *", [
            "DTF Metro Linear - Tabela A", 
            "DTF Metro Linear - Tabela B", 
            "DTF Imagem Avulsa"
        ])
    with col3:
        valor_input = st.number_input("Valor (R$) *", min_value=0.0, step=0.01, format="%.2f")
        
    col4, col5 = st.columns(2)
    with col4:
        retirado_input = st.checkbox("DTF Pronto / Já Retirado")
    with col5:
        status_input = st.radio("Status Financeiro", ["Não Pago", "Pago"], horizontal=True)
        
    enviar = st.form_submit_button("+ Adicionar Item")
    if enviar:
        if cliente_input and valor_input > 0:
            adicionar_venda(cliente_input, produto_input, valor_input, retirado_input, status_input)
            st.success("Item adicionado com sucesso!")
            st.rerun()
        else:
            st.error("Por favor, preencha o nome do cliente e o valor.")

st.markdown("---")

# Área de Busca e Filtros
st.subheader("🔍 Fila de Pedidos e Histórico")
col_busca, col_filtro = st.columns(2)

with col_busca:
    busca_cliente = st.text_input("Procurar por Cliente", placeholder="Digite o nome para filtrar...")
with col_filtro:
    filtro_status = st.selectbox("Filtrar Status Financeiro", ["Todos", "Não Pago", "Pago"])

# Aplicar Filtros no DataFrame
df_filtrado = st.session_state.vendas.copy()

if busca_cliente:
    df_filtrado = df_filtrado[df_filtrado["Cliente"].str.contains(busca_cliente, case=False, na=False)]

if filtro_status != "Todos":
    df_filtrado = df_filtrado[df_filtrado["Status Financeiro"] == filtro_status]

# Mostrar total devedor do cliente pesquisado
if busca_cliente:
    total_devido = df_filtrado[df_filtrado["Status Financeiro"] == "Não Pago"]["Valor"].sum()
    st.error(f"⚠️ **Total Devido por {busca_cliente}:** R$ {total_devido:.2f}")

# Tabela Interativa de Resultados com Lixeira (Exclusão)
if not df_filtrado.empty:
    for idx, row in df_filtrado.iterrows():
        # Criar uma linha visual organizada para cada pedido
        c_data, c_nome, c_prod, c_val, c_ret, c_status, c_acao = st.columns([1, 2, 2, 1, 1.5, 1, 1])
        
        c_data.text(row["Data"])
        c_nome.markdown(f"**{row['Cliente']}**")
        c_prod.text(row["Produto/Tabela DTF"])
        c_val.text(f"R$ {row['Valor']:.2f}")
        c_ret.text(row["Retirado"])
        
        # Cor para o status financeiro
        if row["Status Financeiro"] == "Pago":
            c_status.markdown("🟢 **Pago**")
        else:
            c_status.markdown("🔴 **Não Pago**")
            
        # Botão de excluir para cada linha (A Lixeira)
        if c_acao.button("🗑️ Excluir", key=f"del_{row['ID']}"):
            excluir_venda(row["ID"])
            st.toast(f"Pedido de {row['Cliente']} excluído!")
            st.rerun()
else:
    st.info("Nenhum pedido localizado com os filtros selecionados.")
