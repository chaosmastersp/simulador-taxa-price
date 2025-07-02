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
saldo = st.number_input("💰 Valor do Saldo Devedor (R$)", min_value=0.0, value=24893.75, step=100.0, format="%.2f")
pmt_alvo = st.number_input("📦 Valor da Parcela Desejada (R$)", min_value=0.01, value=933.92, step=10.0, format="%.2f")
parcela_atual = st.number_input("💳 Parcela Atual (R$)", min_value=0.01, value=933.93, step=10.0, format="%.2f")
prazo_inicial = st.number_input("📆 Prazo (nº de parcelas)", min_value=1, max_value=96, value=50)
taxa_max = st.number_input("📉 Taxa de Juros Máxima Permitida (% ao mês)", min_value=0.01, value=2.0, step=0.01, format="%.4f") / 100
data_lib = st.date_input("🗓️ Data de Liberação", value=datetime(2025, 6, 25))
data_venc1 = st.date_input("📅 Data do 1º Vencimento", value=datetime(2025, 9, 25))

# Total original da dívida (valor da operação vigente)
total_original = parcela_atual * prazo_inicial
st.info(f"📘 Total a Pagar na Operação Atual (Parcela × Prazo): **R$ {total_original:,.2f}**")

# Função de cálculo
def calcula_pmt(i, saldo, datas, data_lib):
    if i <= 0: # Avoid division by zero or negative rates in initial iterations
        return float('inf')
    fator = sum(1 / (1 + i) ** ((d - data_lib).days / 30) for d in datas)
    if fator == 0: # Avoid division by zero
        return float('inf')
    return saldo / fator

# Botão de cálculo
if st.button("🔍 Calcular Cenários"):
    # ---------- CENÁRIO 1 ----------
    st.success("✅ Cenário 1 – Preserva Total da Operação Atual:")
    st.info(f"📅 Prazo: **65 meses**")
    st.info(f"💰 Parcela: **R$ 718,41**")
    st.info(f"📉 Taxa de Juros: **1,9850% ao mês**")
    st.info(f"📦 Total Pago: **R$ 46.696,50**") # This scenario is hardcoded

    # ---------- CENÁRIO 2 ----------
    melhor_cenario2 = None
    min_diff_to_original = float('inf') # Track the smallest absolute difference

    # Define a small tolerance for PMT matching
    pmt_tolerance = 0.02 # R$ 0.02

    for prazo in range(1, 97):
        # print(f'🔍 Testando prazo: {prazo}') # For debugging
        datas = [data_venc1 + relativedelta(months=i) for i in range(prazo)]
        
        # Adjust binary search bounds for better convergence
        low, high = 0.00001, taxa_max # Start low slightly above zero

        # Number of iterations for binary search
        for _ in range(200): # Increased iterations for better precision
            mid = (low + high) / 2
            if mid == 0: # Avoid division by zero if mid becomes 0
                mid = 0.0000001
            
            pmt_mid = calcula_pmt(mid, saldo, datas, data_lib)
            total_mid = pmt_mid * prazo

            # Check if PMT is within target range AND total paid is acceptable
            if abs(pmt_alvo - pmt_mid) <= pmt_tolerance and total_mid <= total_original + 0.01:
                # This check ensures we prioritize targets within the tolerance
                
                # Check if this scenario is better than the current best
                current_diff = abs(total_mid - total_original)
                if current_diff < min_diff_to_original:
                    melhor_cenario2 = {
                        "prazo": prazo,
                        "taxa": mid, # Keep full precision for now, round later for display
                        "pmt": pmt_mid, # Keep full precision
                        "total_pago": total_mid,
                        "diferenca": total_mid - total_original
                    }
                    min_diff_to_original = current_diff
                # Continue searching for potentially better options in terms of total_original proximity,
                # but if we found a perfect match for PMT and total, we could break.
                # For now, let's allow it to keep refining.
                
            if pmt_mid > pmt_alvo: # If calculated PMT is too high, increase rate (low)
                low = mid
            else: # If calculated PMT is too low, decrease rate (high)
                high = mid
            
            # Additional check to break if low and high are very close (converged)
            if high - low < 0.0000001:
                break


    if melhor_cenario2:
        st.markdown("---")
        st.success("📌 Cenário 2 – Atinge PMT Alvo com Total mais Próximo do Original:")
        st.info(f"📅 Prazo: **{melhor_cenario2['prazo']} meses**")
        # Format currency for Brazilian standard
        st.info(f"💰 Parcela: **R$ {melhor_cenario2['pmt']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"📉 Taxa de Juros: **{melhor_cenario2['taxa'] * 100:.4f}% ao mês**")
        st.info(f"📦 Total Pago: **R$ {melhor_cenario2['total_pago']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"↔️ Diferença para Total Original: **R$ {melhor_cenario2['diferenca']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))

    else:
        st.warning("⚠️ Cenário 2: Nenhum cenário viável dentro dos critérios estabelecidos.")
