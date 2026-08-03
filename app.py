import streamlit as st
import pandas as pd
from datetime import datetime
from sqlalchemy import text

# 1. Configuração de Layout e Visual ERP Limpo
st.set_page_config(layout="wide", page_title="Controle DTF EXPRESS", page_icon="🖨️")

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

st.title("🖨️ DTF EXPRESS — Painel de Produção e Vendas")
st.caption("Controle em tempo real de impressão, pagamentos e retiradas.")

# 2. Conexão com o Banco de Dados Real (PostgreSQL)
conn = st.connection("postgresql", type="sql")

# Garante que a nova coluna de produção exista no banco de dados
def atualizar_banco_producao():
    try:
        with conn.session as session:
            session.execute(text("ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS dtf_pronto BOOLEAN DEFAULT FALSE;"))
            session.execute(text("ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS desconto NUMERIC(10,2) DEFAULT 0.0;"))
            session.execute(text("ALTER TABLE pedidos ADD COLUMN IF NOT EXISTS acrescimo NUMERIC(10,2) DEFAULT 0.0;"))
            session.commit()
    except Exception:
        pass

atualizar_banco_producao()

def buscar_dados():
    return conn.query("SELECT id, data, cliente, metros, valor_total, dtf_pronto, pago, retirou, desconto, acrescimo FROM pedidos ORDER BY id DESC;", ttl=0)

try:
    df_pedidos = buscar_dados()
except Exception as e:
    st.error(f"Erro de conexão com o banco de dados: {e}")
    df_pedidos = pd.DataFrame(columns=["id", "data", "cliente", "metros", "valor_total", "dtf_pronto", "pago", "retirou", "desconto", "acrescimo"])

# 3. Indicadores Financeiros do Dia e do Mês
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

col_fin1, col_fin2 = st.columns(2)
with col_fin1:
    st.metric(label="📊 FATURAMENTO DIÁRIO (HOJE)", value=f"R$ {vendas_hoje:,.2f}")
with col_fin2:
    st.metric(label="📈 TOTAL ACUMULADO DO MÊS", value=f"R$ {vendas_mes:,.2f}")

st.markdown("---")

# 4. Divisão da Tela: Lançamento à Esquerda e Lista à Direita
col_cadastro, col_painel = st.columns([1, 2])

with col_cadastro:
    st.subheader("➕ Novo Lançamento")
    with st.form("novo_pedido_form", clear_on_submit=True):
        cliente = st.text_input("Nome do Cliente", placeholder="Ex: Estamparia Silva")
        metros = st.number_input("Metragem DTF (m)", min_value=0.1, step=0.1, value=1.0)
        preco_metro = st.number_input("Preço por Metro (R$)", min_value=1.0, value=30.0, step=1.0)
        
        st.markdown("**Ajustes de Valores:**")
        desconto = st.number_input("Desconto (R$)", min_value=0.0, step=0.5, value=0.0)
        acrescimo = st.number_input("Acréscimo / Taxa (R$)", min_value=0.0, step=0.5, value=0.0)
        
        btn_salvar = st.form_submit_button("🚀 Cadastrar Pedido na Produção")
        
        if btn_salvar and cliente:
            valor_base = metros * preco_metro
            valor_total = float(valor_base + acrescimo - desconto)
            if valor_total < 0: valor_total = 0.0
            
            try:
                with conn.session as session:
                    sql = text("""
                        INSERT INTO pedidos (data, cliente, metros, valor_total, dtf_pronto, pago, retirou, desconto, acrescimo) 
                        VALUES (:dt, :cli, :met, :val, false, false, false, :desc, :acre);
                    """)
                    session.execute(sql, {
                        "dt": hoje, "cli": str(cliente), "met": float(metros), 
                        "val": float(valor_total), "desc": float(desconto), "acre": float(acrescimo)
                    })
                    session.commit()
                st.success("Pedido enviado para a fila de impressão!")
                st.rerun()
            except Exception as err:
                st.error(f"Erro ao salvar: {err}")

with col_painel:
    st.subheader("📋 Fila de Pedidos Ativos")
    
    # Filtro rápido focado na produção
    filtro = st.radio("Filtrar por Status de Impressão:", ["Todos", "Em Impressão (Pendentes)", "Prontos"], horizontal=True)
    
    df_filtrado = df_pedidos.copy()
    if filtro == "Em Impressão (Pendentes)":
        df_filtrado = df_filtrado[df_filtrado["dtf_pronto"] == False]
    elif filtro == "Prontos":
        df_filtrado = df_filtrado[df_filtrado["dtf_pronto"] == True]

    if not df_filtrado.empty:
        for idx, row in df_filtrado.iterrows():
            id_pedido = int(row["id"])
            
            # Definição visual dos status com emojis informativos
            status_producao = "✨ DTF PRONTO" if row.get("dtf_pronto", False) else "⏳ IMPRIMINDO"
            status_pago = "🟢 PAGO" if row["pago"] else "🔴 NÃO PAGO"
            status_entrega = "📦 RETIROU" if row["retirou"] else "⏳ PENDENTE"
            
            with st.container():
                # Divisão em colunas para os botões ficarem lado a lado de forma enxuta
                c_info, c_btn1, c_btn2, c_btn3, c_status, c_del = st.columns([2.2, 1.2, 1.2, 1.2, 1.5, 0.4])
                
                with c_info:
                    st.markdown(f"👤 **{row['cliente']}**")
                    txt_valores = f"{row['metros']}m de DTF"
                    if row.get('desconto', 0) > 0: txt_valores += f" | Desc: -R$ {row['desconto']}"
                    if row.get('acrescimo', 0) > 0: txt_valores += f" | Taxa: +R$ {row['acrescimo']}"
                    st.markdown(f"<small style='color:gray;'>{txt_valores}</small>", unsafe_allow_html=True)
                    st.markdown(f"**Total: R$ {row['valor_total']:,.2f}**")
                
                with c_btn1:
                    # 1º Botão: Controle de Impressão do DTF
                    label_prod = "Voltar p/ Fila" if row.get("dtf_pronto", False) else "Finalizar DTF"
                    if st.button(label_prod, key=f"prod_{id_pedido}", use_container_width=True):
                        with conn.session as session:
                            session.execute(text("UPDATE pedidos SET dtf_pronto = :pronto WHERE id = :id;"), {"pronto": not row.get("dtf_pronto", False), "id": id_pedido})
                            session.commit()
                        st.rerun()
                
                with c_btn2:
                    # 2º Botão: Controle Financeiro
                    label_pago = "Marcar Não Pago" if row["pago"] else "Dar Baixa (Pago)"
                    if st.button(label_pago, key=f"pago_{id_pedido}", use_container_width=True):
                        with conn.session as session:
                            session.execute(text("UPDATE pedidos SET pago = :pago WHERE id = :id;"), {"pago": not row["pago"], "id": id_pedido})
                            session.commit()
                        st.rerun()
                
                with c_btn3:
                    # 3º Botão: Controle de Saída/Retirada do Cliente
                    label_retirou = "Marcar Pendente" if row["retirou"] else "Confirmar Saída"
                    if st.button(label_retirou, key=f"retirou_{id_pedido}", use_container_width=True):
                        with conn.session as session:
                            session.execute(text("UPDATE pedidos SET retirou = :retirou WHERE id = :id;"), {"retirou": not row["retirou"], "id": id_pedido})
                            session.commit()
                        st.rerun()
                        
                with c_status:
                    # Coluna que agrupa as etiquetas de status lado a Lado
                    st.markdown(f"🎬 `{status_producao}`")
                    st.markdown(f"💰 **{status_pago}**")
                    st.markdown(f"🚚 <small>{status_entrega}</small>", unsafe_allow_html=True)
                
                with c_del:
                    # Botão de apagar permanente
                    if st.button("🗑️", key=f"deletar_{id_pedido}", help="Deletar este pedido"):
                        with conn.session as session:
                            session.execute(text("DELETE FROM pedidos WHERE id = :id;"), {"id": id_pedido})
                            session.commit()
                        st.success("Removido!")
                        st.rerun()
                
                st.markdown("<hr style='margin: 8px 0; border-color: #eee;'>", unsafe_allow_html=True)
    else:
        st.info("Nenhum pedido na fila para este filtro.")
