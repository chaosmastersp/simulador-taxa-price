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

# Saldo devedor total estimado com base na parcela atual
saldo_devedor_total = parcela_atual * prazo_inicial
st.info(f"📘 Saldo Devedor Total Estimado (com base na parcela atual): **R$ {saldo_devedor_total:,.2f}**")

# Função de cálculo
def calcula_pmt(i, saldo, datas, data_lib):
    if i <= 0: # Handle zero or negative interest rate
        # If rate is zero, PMT is simply saldo / num_payments
        return saldo / len(datas) if len(datas) > 0 else float('inf')

    # Original Price Table factor calculation adjusted for days / 30
    fator = sum(1 / (1 + i) ** ((d - data_lib).days / 30) for d in datas)
    if fator == 0: # Avoid division by zero
        return float('inf')
    return saldo / fator

# Helper function to calculate total paid and PMT for a given rate and term
def get_pmt_and_total(taxa, saldo, datas, data_lib):
    pmt = calcula_pmt(taxa, saldo, datas, data_lib)
    total_pago = pmt * len(datas)
    return pmt, total_pago

# Lógica principal
if st.button("🔍 Calcular Melhor Taxa e Prazo"):
    # Scenario 1: Best result primarily targeting PMT_ALVO, but also aiming for total_pago <= saldo_devedor_total
    melhor_resultado_pmt_alvo = None
    # We want the lowest possible total_pago below saldo_devedor_total, or closest if none are below
    melhor_diferenca_pmt_alvo = float('inf') 
    
    taxa_limite = taxa_max # Use taxa_max directly as the upper bound for search

    for prazo in range(1, 97):
        datas = [data_venc1 + relativedelta(months=i) for i in range(prazo)]
        
        # Binary search to find a rate that yields a PMT close to pmt_alvo
        low_taxa, high_taxa = 0.0001, taxa_max
        taxa_encontrada_pmt_alvo = None
        
        for _ in range(100): # 100 iterations for binary search convergence
            mid_taxa = (low_taxa + high_taxa) / 2
            if mid_taxa <= 0: mid_taxa = 0.0001 # Ensure positive rate
            
            current_pmt = calcula_pmt(mid_taxa, saldo, datas, data_lib)
            
            if abs(current_pmt - pmt_alvo) < 0.01: # Found a PMT very close to target
                taxa_encontrada_pmt_alvo = mid_taxa
                break
            elif current_pmt > pmt_alvo: # PMT is too high, decrease rate
                high_taxa = mid_taxa
            else: # PMT is too low, increase rate
                low_taxa = mid_taxa
                
        if taxa_encontrada_pmt_alvo is not None:
            taxa_final = round(taxa_encontrada_pmt_alvo, 4)
            pmt_calc, total_pago_calc = get_pmt_and_total(taxa_final, saldo, datas, data_lib)

            # Only consider if PMT is at or below target AND total paid is less than or equal to estimated saldo
            # If total_pago exceeds saldo_devedor_total, it's not the "best" in terms of lowest difference *while not exceeding*.
            if pmt_calc <= pmt_alvo + 0.01 and total_pago_calc <= saldo_devedor_total + 1.00: # Small tolerance for total_pago
                diferenca = abs(saldo_devedor_total - total_pago_calc)
                
                if diferenca < melhor_diferenca_pmt_alvo:
                    melhor_diferenca_pmt_alvo = diferenca
                    melhor_resultado_pmt_alvo = {
                        "prazo": prazo,
                        "taxa": taxa_final,
                        "pmt": pmt_calc,
                        "total_pago": total_pago_calc,
                        "diferenca": diferenca
                    }
    
    if melhor_resultado_pmt_alvo:
        st.success("✅ Cenário 1: Melhor Resultado (Parcela próxima da desejada, Total Pago <= Saldo Estimado):")
        st.info(f"📅 Prazo: **{melhor_resultado_pmt_alvo['prazo']} meses**")
        st.info(f"💰 Parcela: **R$ {melhor_resultado_pmt_alvo['pmt']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"📉 Taxa de Juros: **{melhor_resultado_pmt_alvo['taxa'] * 100:.4f}% ao mês**")
        st.info(f"📦 Total Pago: **R$ {melhor_resultado_pmt_alvo['total_pago']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"↔️ Diferença (Saldo Estimado - Total Pago): **R$ {melhor_resultado_pmt_alvo['diferenca']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
    else:
        st.warning("⚠️ Cenário 1: Não foi possível encontrar um resultado com parcela desejada e total pago menor ou igual ao saldo estimado.")

    st.markdown("---") # Separador para clareza

    # Scenario 2: Alternative scenario - Total paid as close as possible to estimated balance, respecting pmt_alvo
    melhor_resultado_total_pago_proximo = None
    melhor_diferenca_total_pago_proximo = float('inf')

    for novo_prazo in range(1, 97):
        datas_alt = [data_venc1 + relativedelta(months=i) for i in range(novo_prazo)]
        low_taxa_alt, high_taxa_alt = 0.0001, taxa_max
        taxa_encontrada_total_pago = None
        
        for _ in range(100):
            mid_taxa_alt = (low_taxa_alt + high_taxa_alt) / 2
            if mid_taxa_alt <= 0: mid_taxa_alt = 0.0001
            
            pmt_mid_alt, total_mid_alt = get_pmt_and_total(mid_taxa_alt, saldo, datas_alt, data_lib)
            
            # This scenario prioritizes total_mid_alt being close to saldo_devedor_total
            # and pmt_mid_alt <= pmt_alvo + tolerance.
            
            # Check if this rate makes total_paid close to estimated saldo
            if abs(total_mid_alt - saldo_devedor_total) <= 1.00: # Within 1 R$ tolerance
                if pmt_mid_alt <= pmt_alvo + 0.01: # Check if PMT is also acceptable
                    taxa_encontrada_total_pago = mid_taxa_alt
                    break
                elif pmt_mid_alt > pmt_alvo + 0.01: # If PMT is too high, try lower rate (even if total is close)
                    high_taxa_alt = mid_taxa_alt
                else: # PMT is too low, total is close. This case is less likely but could be fine.
                    low_taxa_alt = mid_taxa_alt # try to get closer
            
            # If not close enough to saldo_devedor_total, adjust search range
            elif total_mid_alt > saldo_devedor_total:
                high_taxa_alt = mid_taxa_alt
            else: # total_mid_alt < saldo_devedor_total
                low_taxa_alt = mid_taxa_alt

        if taxa_encontrada_total_pago is not None:
            taxa_final_alt = round(taxa_encontrada_total_pago, 4)
            pmt_final_alt, total_final_alt = get_pmt_and_total(taxa_final_alt, saldo, datas_alt, data_lib)
            
            diferenca_alt = abs(saldo_devedor_total - total_final_alt)

            # Ensure it truly respects the target PMT and is the best of its kind
            if pmt_final_alt <= pmt_alvo + 0.01 and diferenca_alt < melhor_diferenca_total_pago_proximo:
                melhor_diferenca_total_pago_proximo = diferenca_alt
                melhor_resultado_total_pago_proximo = {
                    "prazo": novo_prazo,
                    "taxa": taxa_final_alt,
                    "pmt": pmt_final_alt,
                    "total_pago": total_final_alt,
                    "diferenca": diferenca_alt
                }
    
    if melhor_resultado_total_pago_proximo:
        st.success("📌 Cenário 2: Alternativo (Total Pago mais próximo do Saldo Estimado, Parcela Aceitável):")
        st.info(f"📅 Prazo: **{melhor_resultado_total_pago_proximo['prazo']} meses**")
        st.info(f"💰 Parcela: **R$ {melhor_resultado_total_pago_proximo['pmt']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"📉 Taxa de Juros: **{melhor_resultado_total_pago_proximo['taxa'] * 100:.4f}% ao mês**")
        st.info(f"📦 Total Pago: **R$ {melhor_resultado_total_pago_proximo['total_pago']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"↔️ Diferença (Saldo Estimado - Total Pago): **R$ {melhor_resultado_total_pago_proximo['diferenca']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
    else:
        st.warning("⚠️ Cenário 2: Não foi possível encontrar um cenário alternativo próximo ao saldo estimado com parcela aceitável.")

