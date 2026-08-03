import streamlit as st
import pandas as pd
from datetime import datetime

# Configuração da página para aproveitar bem o espaço horizontal
st.set_page_config(page_title="Sistema DTF Express", layout="wide")

# 1. Inicializar os bancos de dados simulados no estado da sessão
if "pedidos_salvos" not in st.session_state:
    st.session_state.pedidos_salvos = pd.DataFrame(columns=[
        "ID", "Data", "Cliente", "Descrição/DTF", "Quantidade", "Preço Un.", "Preço Total", "Retirada", "Status Financeiro"
    ])

if "itens_rascunho" not in st.session_state:
    # Começa com uma linha vazia para o formulário estilo tabela
    st.session_state.itens_rascunho = [{"id": 0, "descricao": "", "quantidade": 1, "preco_un": 0.0}]

# --- CÁLCULO DE INDICADORES (Topo do App) ---
hoje = datetime.now().strftime("%d/%m/%Y")
df_hoje = st.session_state.pedidos_salvos[st.session_state.pedidos_salvos["Data"] == hoje]
faturamento_hoje = df_hoje["Preço Total"].sum()

st.title("🎯 Sistema de Vendas e Cobrança - DTF Express")

col_fat, col_ext = st.columns(2)
with col_fat:
    st.metric(label="Faturamento Diário (Hoje)", value=f"R$ {faturamento_hoje:.2f}")
with col_ext:
    st.subheader("Extrato Mensal")
    if st.button("📊 Gerar Relatório Acumulado"):
        st.info("Relatório mensal gerado com sucesso!")

st.markdown("---")

# --- CRIAÇÃO DAS ABAS (SEPARAÇÃO DE LOCAIS) ---
aba_cadastro, aba_gerenciamento = st.tabs(["📝 Criar Novo Pedido", "🔍 Gerenciar Status e Cobrança"])

# =========================================================================
# ABA 1: CRIAR NOVO PEDIDO (LAYOUT IGUAL AO SEU PRINT)
# =========================================================================
with aba_cadastro:
    st.subheader("Novo Lançamento de Pedido")
    
    # Campo do Cliente fora da tabela
    cliente_pedido = st.text_input("Nome do Cliente *", placeholder="Digite o nome do cliente...", key="nome_cliente_novo")
    
    st.markdown("### Itens do Pedido")
    
    # Cabeçalho da Tabela Horizontal
    c_desc_h, c_un_h, c_qtd_h, c_prec_h, c_tot_h, c_del_h = st.columns([4, 1, 1.5, 1.5, 1.5, 1])
    c_desc_h.markdown("**Descrição do Produto / Tabela DTF**")
    c_un_h.markdown("**Un.**")
    c_qtd_h.markdown("**Quantidade**")
    c_prec_h.markdown("**Preço Un. (R$)**")
    c_tot_h.markdown("**Preço Total (R$)**")
    c_del_h.markdown("**Ação**")

    lista_para_deletar = []
    
    # Renderiza as linhas dinâmicas de itens
    for idx, item in enumerate(st.session_state.itens_rascunho):
        c_desc, c_un, c_qtd, c_prec, c_tot, c_del = st.columns([4, 1, 1.5, 1.5, 1.5, 1])
        
        # Campo Descrição (Pode ser selectbox ou texto livre)
        desc_val = c_desc.selectbox(
            "Desc", ["Selecione o DTF...", "DTF Metro Linear - Tabela A", "DTF Metro Linear - Tabela B", "DTF Imagem Avulsa"],
            index=0 if item["descricao"] == "" else ["Selecione o DTF...", "DTF Metro Linear - Tabela A", "DTF Metro Linear - Tabela B", "DTF Imagem Avulsa"].index(item["descricao"]),
            key=f"desc_{idx}", label_visibility="collapsed"
        )
        st.session_state.itens_rascunho[idx]["descricao"] = desc_val
        
        # Unidade fixa
        c_un.markdown("<div style='padding-top: 10px;'>UN</div>", unsafe_allow_html=True)
        
        # Quantidade
        qtd_val = c_qtd.number_input("Qtd", min_value=1, value=int(item["quantidade"]), key=f"qtd_{idx}", label_visibility="collapsed")
        st.session_state.itens_rascunho[idx]["quantidade"] = qtd_val
        
        # Preço Unitário
        prec_val = c_prec.number_input("Preço", min_value=0.0, step=0.01, value=float(item["preco_un"]), key=f"prec_{idx}", label_visibility="collapsed")
        st.session_state.itens_rascunho[idx]["preco_un"] = prec_val
        
        # Preço Total Calculado Automaticamente
        total_item = qtd_val * prec_val
        c_tot.markdown(f"<div style='padding-top: 10px; font-weight: bold;'>R$ {total_item:.2f}</div>", unsafe_allow_html=True)
        
        # Botão de Remover a linha específica (Lixeira vermelha)
        if c_del.button("🗑️", key=f"del_item_{idx}"):
            lista_para_deletar.append(idx)

    # Executa a remoção de linhas se clicado
    if lista_para_deletar:
        for index in sorted(lista_para_deletar, reverse=True):
            if len(st.session_state.itens_rascunho) > 1:
                st.session_state.itens_rascunho.pop(index)
        st.rerun()

    # Botão de adicionar outra linha (Igual ao "+ Adicionar outro item" do seu print)
    if st.button("➕ Adicionar outro item"):
        st.session_state.itens_rascunho.append({"id": len(st.session_state.itens_rascunho), "descricao": "", "quantidade": 1, "preco_un": 0.0})
        st.rerun()

    st.markdown("---")
    
    # Botão Final para Enviar o Pedido para o outro local
    if st.button("🚀 ENVIAR PEDIDO", type="primary", use_container_width=True):
        if not cliente_pedido:
            st.error("Por favor, preencha o nome do cliente antes de enviar!")
        elif any(item["descricao"] == "Selecione o DTF..." or item["preco_un"] <= 0 for item in st.session_state.itens_rascunho):
            st.error("Preencha corretamente a descrição e o valor de todos os itens!")
        else:
            # Salva todos os itens na tabela definitiva de gerenciamento
            novos_pedidos = []
            timestamp_id = int(datetime.now().timestamp() * 1000)
            
            for item in st.session_state.itens_rascunho:
                novo_item = {
                    "ID": timestamp_id,
                    "Data": datetime.now().strftime("%d/%m/%Y"),
                    "Cliente": cliente_pedido,
                    "Descrição/DTF": item["descricao"],
                    "Quantidade": item["quantidade"],
                    "Preço Un.": item["preco_un"],
                    "Preço Total": item["quantidade"] * item["preco_un"],
                    "Retirada": "Pronto p/ Retirar", # Padrão inicial
                    "Status Financeiro": "Não Pago"   # Padrão inicial
                }
                novos_pedidos.append(novo_item)
            
            st.session_state.pedidos_salvos = pd.concat([st.session_state.pedidos_salvos, pd.DataFrame(novos_pedidos)], ignore_index=True)
            
            # Limpa o rascunho para o próximo pedido
            st.session_state.itens_rascunho = [{"id": 0, "descricao": "", "quantidade": 1, "preco_un": 0.0}]
            st.success("✅ Pedido enviado com sucesso para a tela de gerenciamento!")
            st.rerun()

# =========================================================================
# ABA 2: O OUTRO LOCAL (GERENCIAMENTO, PAGAMENTO E ENTREGA)
# =========================================================================
with aba_gerenciamento:
    st.subheader("📋 Controle de Status e Histórico de Clientes")
    
    col_b, col_f = st.columns(2)
    with col_b:
        busca_cliente = st.text_input("🔍 Procurar por Cliente", placeholder="Digite o nome do cliente para ver tudo...")
    with col_f:
        filtro_status = st.selectbox("📌 Filtrar Status Financeiro", ["Todos", "Não Pago", "Pago"])

    # Filtros aplicados na tabela definitiva
    df_filtrado = st.session_state.pedidos_salvos.copy()
    if busca_cliente:
        df_filtrado = df_filtrado[df_filtrado["Cliente"].str.contains(busca_cliente, case=False, na=False)]
    if filtro_status != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Status Financeiro"] == filtro_status]

    # Exibe Alerta Vermelho de Débito Acumulado caso pesquise um cliente específico
    if busca_cliente:
        total_devido = df_filtrado[df_filtrado["Status Financeiro"] == "Não Pago"]["Preço Total"].sum()
        st.error(f"⚠️ **Total que o(a) {busca_cliente} está devendo no momento:** R$ {total_devido:.2f}")

    st.markdown("---")

    # Listagem dos pedidos enviados com controles de alterar status
    if not df_filtrado.empty:
        # Cabeçalho da tabela de gerenciamento
        c_dt, c_cl, c_ds, c_tot_p, c_ret_p, c_fin_p, c_ac_p = st.columns([1, 1.5, 2.5, 1, 1.5, 1.5, 1])
        c_dt.markdown("**Data**")
        c_cl.markdown("**Cliente**")
        c_ds.markdown("**Item**")
        c_tot_p.markdown("**Total**")
        c_ret_p.markdown("**Status Entrega**")
        c_fin_p.markdown("**Financeiro**")
        c_ac_p.markdown("**Excluir**")
        
        st.markdown("<hr style='margin: 5px 0;'>", unsafe_allow_html=True)

        for idx, row in df_filtrado.iterrows():
            c_dt, c_cl, c_ds, c_tot_p, c_ret_p, c_fin_p, c_ac_p = st.columns([1, 1.5, 2.5, 1, 1.5, 1.5, 1])
            
            c_dt.text(row["Data"])
            c_cl.markdown(f"**{row['Cliente']}**")
            c_ds.text(f"{row['Quantidade']}x {row['Descrição/DTF']}")
            c_tot_p.text(f"R$ {row['Preço Total']:.2f}")
            
            # --- CONTROLE 1: STATUS DE ENTREGA ---
            # Troca o texto baseado no clique
            atual_retirada = row["Retirada"]
            if c_ret_p.button(f"📦 {atual_retirada}", key=f"btn_ret_{idx}", help="Clique para mudar o status de entrega"):
                novo_status_ret = "Retirado" if atual_retirada == "Pronto p/ Retirar" else "Pronto p/ Retirar"
                st.session_state.pedidos_salvos.at[idx, "Retirada"] = novo_status_ret
                st.rerun()
                
            # --- CONTROLE 2: STATUS FINANCEIRO ---
            # Fica verde se pago, vermelho se não pago. Muda com 1 clique
            atual_pagamento = row["Status Financeiro"]
            cor_botao = "🟢 Pago" if atual_pagamento == "Pago" else "🔴 Não Pago"
            if c_fin_p.button(cor_botao, key=f"btn_pag_{idx}", help="Clique para mudar entre Pago e Não Pago"):
                novo_status_pag = "Pago" if atual_pagamento == "Não Pago" else "Não Pago"
                st.session_state.pedidos_salvos.at[idx, "Status Financeiro"] = novo_status_pag
                st.rerun()

            # --- CONTROLE 3: LIXEIRA PARA EXCLUIR ---
