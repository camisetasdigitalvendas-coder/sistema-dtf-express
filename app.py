import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text

# 1. Configuração de Layout e Estilo Limpo ERP
st.set_page_config(layout="wide", page_title="ERP DTF - Sistema de Gestão", page_icon="📦")

# CSS para estilização profissional
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

st.title("📦 Bling DTF — Painel de Controle Avançado")
st.caption("Gerenciamento completo de pedidos, fluxo de caixa e formas de pagamento.")

# 2. Conexão com o Banco de Dados Real (PostgreSQL)
conn = st.connection("postgresql", type="sql")

# Função para garantir que as novas colunas existam no banco sem dar erro
def atualizar_banco_se_necessario():
    try:
        with conn.session as session:
            # Tenta adicionar as colunas novas caso elas não existam de antes
            session.execute(text("ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS forma_pagto VARCHAR(50) DEFAULT 'Pix';"))
            session.execute(text("ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS desconto NUMERIC(10,2) DEFAULT 0.0;"))
            session.execute(text("ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS acrescimo NUMERIC(10,2) DEFAULT 0.0;"))
            session.commit()
    except Exception:
        pass

atualizar_banco_se_necessario()

def buscar_dados():
    # Busca com os novos campos inclusos
    return conn.query("SELECT id, data, cliente, metros, valor_total, pago, retirou, forma_pagto, desconto, acrescimo FROM pedidos ORDER BY id DESC;", ttl=0)

try:
    df_pedidos = buscar_dados()
except Exception as e:
    st.error(f"Erro de conexão com o banco de dados: {e}")
    df_pedidos = pd.DataFrame(columns=["id", "data", "cliente", "metros", "valor_total", "pago", "retirou", "forma_pagto", "desconto", "acrescimo"])

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

# 4. Interface Dividida: Lançamento vs Painel de Pedidos
col_cadastro, col_painel = st.columns([1, 2]) # Painel de pedidos ganha mais espaço horizontal

with col_cadastro:
    st.subheader("➕ Incluir Pedido")
    with st.form("novo_pedido_form", clear_on_submit=True):
        cliente = st.text_input("Nome do Cliente", placeholder="Ex: João Silva")
        metros = st.number_input("Metragem DTF (m)", min_value=0.1, step=0.1, value=1.0)
        preco_metro = st.number_input("Preço por Metro (R$)", min_value=1.0, value=30.0, step=1.0)
        
        st.markdown("**Opções Adicionais de Valores:**")
        forma_pagto = st.selectbox("Forma de Pagamento", ["Pix", "Dinheiro", "Cartão de Crédito", "Cartão de Débito"])
        desconto = st.number_input("Desconto (R$)", min_value=0.0, step=0.5, value=0.0)
        acrescimo = st.number_input("Acréscimo / Taxa (R$)", min_value=0.0, step=0.5, value=0.0)
        
        btn_salvar = st.form_submit_button("✨ Salvar Pedido no Bling")
        
        if btn_salvar and cliente:
            # Cálculo completo do valor total com acréscimos e descontos
            valor_base = metros * preco_metro
            valor_total = float(valor_base + acrescimo - desconto)
            if valor_total < 0: valor_total = 0.0
            
            try:
                with conn.session as session:
                    sql = text("""
                        INSERT INTO pedidos (data, cliente, metros, valor_total, pago, retirou, forma_pagto, desconto, acrescimo) 
                        VALUES (:dt, :cli, :met, :val, false, false, :forma, :desc, :acre);
                    """)
                    session.execute(sql, {
                        "dt": hoje, "cli": str(cliente), "met": float(metros), 
                        "val": float(valor_total), "forma": str(forma_pagto),
                        "desc": float(desconto), "acre": float(acrescimo)
                    })
                    session.commit()
                st.success("Pedido registrado com sucesso!")
                st.rerun()
            except Exception as err:
                st.error(f"Erro ao salvar: {err}")

with col_painel:
    st.subheader("📋 Lista de Pedidos Cadastrados")
    
    # Filtros Rápidos
    filtro = st.radio("Filtrar por Status de Pagamento:", ["Todos", "Apenas Pagos", "Apenas Não Pagos"], horizontal=True)
    
    df_filtrado = df_pedidos.copy()
    if filtro == "Apenas Pagos":
        df_filtrado = df_filtrado[df_filtrado["pago"] == True]
    elif filtro == "Apenas Não Pagos":
        df_filtrado = df_filtrado[df_filtrado["pago"] == False]

    if not df_filtrado.empty:
        for idx, row in df_filtrado.iterrows():
            id_pedido = int(row["id"])
            status_pago = "🟢 PAGO" if row["pago"] else "🔴 NÃO PAGO"
            status_entrega = "📦 RETIROU" if row["retirou"] else "⏳ PENDENTE"
            
            # Caixa visual individual para cada pedido cadastrado
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([2.5, 1.5, 1.5, 1.2, 0.5])
                
                with c1:
                    st.markdown(f"👤 **{row['cliente']}** | 🗓️ {row['data'].strftime('%d/%m/%Y')}")
                    # Mostra os detalhes avançados de valores de forma organizada
                    txt_detalhes = f"{row['metros']}m de DTF | Método: {row.get('forma_pagto', 'Pix')}"
                    if row.get('desconto', 0) > 0: txt_detalhes += f" | Desc: -R$ {row['desconto']}"
                    if row.get('acrescimo', 0) > 0: txt_detalhes += f" | Taxa: +R$ {row['acrescimo']}"
                    st.markdown(f"<small style='color:gray;'>{txt_detalhes}</small>", unsafe_allow_html=True)
                    st.markdown(f"**Total final: R$ {row['valor_total']:,.2f}**")
                
                with c2:
                    label_pago = "Marcar Pendente" if row["pago"] else "Dar Baixa (Pago)"
                    if st.button(label_pago, key=f"pago_{id_pedido}", use_container_width=True):
                        with conn.session as session:
                            session.execute(text("UPDATE pedidos SET pago = :pago WHERE id = :id;"), {"pago": not row["pago"], "id": id_pedido})
                            session.commit()
                        st.rerun()
                
                with c3:
                    label_retirou = "Marcar Pendente" if row["retirou"] else "Confirmar Retirada"
                    if st.button(label_retirou, key=f"retirou_{id_pedido}", use_container_width=True):
                        with conn.session as session:
                            session.execute(text("UPDATE pedidos SET retirou = :retirou WHERE id = :id;"), {"retirou": not row["retirou"], "id": id_pedido})
                            session.commit()
                        st.rerun()
                        
                with c4:
                    st.markdown(f"**{status_pago}**")
                    st.markdown(f"<small>{status_entrega}</small>", unsafe_allow_html=True)
                
                with c5:
                    # Botão de apagar/deletar pedido com ícone de lixeira
                    if st.button("🗑️", key=f"deletar_{id_pedido}", help="Excluir este pedido permanentemente"):
                        with conn.session as session:
                            session.execute(text("DELETE FROM pedidos WHERE id = :id;"), {"id": id_pedido})
                            session.commit()
                        st.success("Pedido removido!")
                        st.rerun()
                
                st.markdown("<hr style='margin: 10px 0; border-color: #ddd;'>", unsafe_allow_html=True)
    else:
        st.info("Nenhum pedido encontrado para o filtro selecionado.")
