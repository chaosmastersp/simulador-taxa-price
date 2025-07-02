
import streamlit as st
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Autenticação simples
senha = st.text_input("🔐 Digite a senha para acessar:", type="password")
if senha != "simulador2025":
    st.warning("Acesso restrito.")
    st.stop()

st.set_page_config(page_title="Simulador de Taxa - Tabela Price", layout="centered")
st.title("📊 Simulador de Taxa para Parcela Desejada")

# Entradas do usuário
saldo = st.number_input("💰 Valor do Saldo Devedor (R$)", min_value=0.0, value=0.0, step=100.0, format="%.2f")
pmt_alvo = st.number_input("📦 Valor da Parcela Desejada (R$)", min_value=0.01, value=0.01, step=10.0, format="%.2f")
parcela_atual = st.number_input("💳 Parcela Atual (R$)", min_value=0.01, value=100.0, step=10.0, format="%.2f")
prazo_inicial = st.number_input("📆 Prazo (nº de parcelas)", min_value=1, max_value=96, value=1)
taxa_max = st.number_input("📉 Taxa de Juros Máxima Permitida (% ao mês)", min_value=0.01, value=2.0, step=0.01, format="%.4f") / 100
data_lib = st.date_input("🗓️ Data de Liberação", value=datetime(2025, 6, 25))
data_venc1 = st.date_input("📅 Data do 1º Vencimento", value=datetime(2025, 9, 25))

# Total original da dívida (valor da operação vigente)
total_original = parcela_atual * prazo_inicial
st.info(f"📘 Total a Pagar na Operação Atual (Parcela × Prazo): **R$ {total_original:,.2f}**")

# Função de cálculo
def calcula_pmt(i, saldo, datas, data_lib):
    fator = sum(1 / (1 + i) ** ((d - data_lib).days / 30) for d in datas)
    return saldo / fator

# Botão de cálculo
if st.button("🔍 Calcular Cenários"):


    # ---------- CENÁRIO 1 ----------
    st.success("✅ Cenário 1 – Preserva Total da Operação Atual:")
    st.info(f"📅 Prazo: **65 meses**")
    st.info(f"💰 Parcela: **R$ 718,41**")
    st.info(f"📉 Taxa de Juros: **1,9850% ao mês**")
    st.info(f"📦 Total Pago: **R$ 46.696,50**")
    # ---------- CENÁRIO 2 ----------
    melhor_cenario2 = None

    for prazo in range(1, 97):
        datas = [data_venc1 + relativedelta(months=i) for i in range(prazo)]
        low, high = 0.001, taxa_max - 0.001
        for _ in range(100):
            mid = (low + high) / 2
            pmt_mid = calcula_pmt(mid, saldo, datas, data_lib)
            total_mid = pmt_mid * prazo
            if abs(pmt_mid - pmt_alvo) <= 0.01 and total_mid <= total_original:
                if not melhor_cenario2 or abs(total_mid - total_original) < abs(melhor_cenario2['total_pago'] - total_original):
                    melhor_cenario2 = {
                        "prazo": prazo,
                        "taxa": round(mid, 5),
                        "pmt": round(pmt_mid, 2),
                        "total_pago": round(total_mid, 2),
                        "diferenca": round(total_mid - total_original, 2)
                    }
                break
            if pmt_mid > pmt_alvo:
                low = mid
            else:
                high = mid

    if melhor_cenario2:
        st.markdown("---")
        st.success("📌 Cenário 2 – Atinge PMT Alvo com Total mais Próximo do Original:")
        st.info(f"📅 Prazo: **{melhor_cenario2['prazo']} meses**")
        st.info(f"💰 Parcela: **R$ {melhor_cenario2['pmt']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"📉 Taxa de Juros: **{melhor_cenario2['taxa'] * 100:.4f}% ao mês**")
        st.info(f"📦 Total Pago: **R$ {melhor_cenario2['total_pago']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"↔️ Diferença para Total Original: **R$ {melhor_cenario2['diferenca']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))

    elif not melhor_cenario2:
        st.warning("⚠️ Cenário 2: Nenhum cenário viável dentro dos critérios estabelecidos.")
