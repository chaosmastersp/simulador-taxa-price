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
        return saldo / len(datas) if len(datas) > 0 else float('inf')

    fator = sum(1 / (1 + i) ** ((d - data_lib).days / 30) for d in datas)
    if fator == 0:
        return float('inf')
    return saldo / fator

# Helper function to calculate total paid and PMT for a given rate and term
def get_pmt_and_total(taxa, saldo, datas, data_lib):
    pmt = calcula_pmt(taxa, saldo, datas, data_lib)
    total_pago = pmt * len(datas)
    return pmt, total_pago

# Lógica principal
if st.button("🔍 Calcular Melhor Taxa e Prazo"):
    # Scenario 1: Best result primarily targeting PMT_ALVO, and total_pago <= saldo_devedor_total,
    # with a difference (Saldo Estimado - Total Pago) between 0 and 50.00
    melhor_resultado_pmt_alvo = None
    melhor_diferenca_pmt_alvo = float('-inf') # Maximize difference (Saldo - Total) up to 50.00

    for prazo in range(1, 97):
        datas = [data_venc1 + relativedelta(months=i) for i in range(prazo)]
        
        low_taxa, high_taxa = 0.0001, taxa_max
        taxa_encontrada_pmt_alvo = None
        
        for _ in range(100):
            mid_taxa = (low_taxa + high_taxa) / 2
            if mid_taxa <= 0: mid_taxa = 0.0001
            
            current_pmt = calcula_pmt(mid_taxa, saldo, datas, data_lib)
            
            if abs(current_pmt - pmt_alvo) < 0.01:
                taxa_encontrada_pmt_alvo = mid_taxa
                break
            elif current_pmt > pmt_alvo:
                high_taxa = mid_taxa
            else:
                low_taxa = mid_taxa
                
        if taxa_encontrada_pmt_alvo is not None:
            taxa_final = round(taxa_encontrada_pmt_alvo, 4)
            pmt_calc, total_pago_calc = get_pmt_and_total(taxa_final, saldo, datas, data_lib)

            diferenca = saldo_devedor_total - total_pago_calc # This should be positive
            
            # Conditions: pmt_calc close to pmt_alvo AND total_pago_calc <= saldo_devedor_total AND 0 <= diferenca <= 50.00
            if (pmt_calc <= pmt_alvo + 0.01 and 
                total_pago_calc <= saldo_devedor_total and # Total Paid must be less than or equal to estimated balance
                diferenca >= 0 and diferenca <= 50.00): # Difference must be between 0 and 50.00

                # We want the highest difference (closer to 50.00), meaning lower total paid while staying within bounds
                if diferenca > melhor_diferenca_pmt_alvo:
                    melhor_diferenca_pmt_alvo = diferenca
                    melhor_resultado_pmt_alvo = {
                        "prazo": prazo,
                        "taxa": taxa_final,
                        "pmt": pmt_calc,
                        "total_pago": total_pago_calc,
                        "diferenca": diferenca 
                    }
    
    if melhor_resultado_pmt_alvo:
        st.success("✅ Cenário 1: Melhor Resultado (Parcela próxima da desejada, Total Pago NÃO maior que Saldo Estimado, Diferença (Saldo - Total) <= R$ 50,00):")
        st.info(f"📅 Prazo: **{melhor_resultado_pmt_alvo['prazo']} meses**")
        st.info(f"💰 Parcela: **R$ {melhor_resultado_pmt_alvo['pmt']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"📉 Taxa de Juros: **{melhor_resultado_pmt_alvo['taxa'] * 100:.4f}% ao mês**")
        st.info(f"📦 Total Pago: **R$ {melhor_resultado_pmt_alvo['total_pago']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"↔️ Diferença (Saldo Estimado - Total Pago): **R$ {melhor_resultado_pmt_alvo['diferenca']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
    else:
        st.warning("⚠️ Cenário 1: Não foi possível encontrar um resultado com parcela desejada, total pago não maior que o saldo estimado, e diferença (Saldo - Total) entre R$ 0,00 e R$ 50,00.")

    st.markdown("---") # Separador para clareza

    # Scenario 2: Alternative scenario - Total paid as close as possible to estimated balance (not exceeding it)
    # with a difference (Saldo Estimado - Total Pago) between 0 and 50.00, respecting pmt_alvo
    melhor_resultado_total_pago_proximo = None
    melhor_diferenca_total_pago_proximo = float('-inf') # Maximize difference (Saldo - Total) up to 50.00

    for novo_prazo in range(1, 97):
        datas_alt = [data_venc1 + relativedelta(months=i) for i in range(novo_prazo)]
        low_taxa_alt, high_taxa_alt = 0.0001, taxa_max
        taxa_encontrada_total_pago = None
        
        for _ in range(100):
            mid_taxa_alt = (low_taxa_alt + high_taxa_alt) / 2
            if mid_taxa_alt <= 0: mid_taxa_alt = 0.0001
            
            pmt_mid_alt, total_mid_alt = get_pmt_and_total(mid_taxa_alt, saldo, datas_alt, data_lib)
            
            # Prioritize total_mid_alt <= saldo_devedor_total, AND pmt_mid_alt <= pmt_alvo + tolerance
            # Also, the difference (saldo - total) must be within 0 and 50.00
            
            current_diferenca_alt_candidate = saldo_devedor_total - total_mid_alt

            if (total_mid_alt <= saldo_devedor_total and # Total Paid must be less than or equal to estimated balance
                current_diferenca_alt_candidate >= 0 and current_diferenca_alt_candidate <= 50.00 and # Difference must be between 0 and 50.00
                pmt_mid_alt <= pmt_alvo + 0.01): # PMT must be acceptable
                
                taxa_encontrada_total_pago = mid_taxa_alt
                break # Found a candidate within the range

            # Adjust search range based on total_mid_alt relative to the target total_pago range
            # If total_mid_alt is too low (difference too high), increase rate
            elif total_mid_alt < saldo_devedor_total - 50.00: 
                low_taxa_alt = mid_taxa_alt
            # If total_mid_alt is too high (difference negative), decrease rate
            elif total_mid_alt > saldo_devedor_total: # If it exceeds saldo_devedor_total, decrease rate
                 high_taxa_alt = mid_taxa_alt
            else: # total_mid_alt is between saldo_devedor_total - 50 and saldo_devedor_total
                  # but PMT might be too high. Or still trying to converge.
                if pmt_mid_alt > pmt_alvo + 0.01:
                    high_taxa_alt = mid_taxa_alt
                else:
                    low_taxa_alt = mid_taxa_alt # try to increase total_pago slightly (reduce diff) if pmt allows

        if taxa_encontrada_total_pago is not None:
            taxa_final_alt = round(taxa_encontrada_total_pago, 4)
            pmt_final_alt, total_final_alt = get_pmt_and_total(taxa_final_alt, saldo, datas_alt, data_lib)
            
            diferenca_alt = saldo_devedor_total - total_final_alt # This should be positive
            
            # Final check with rounded values: must meet criteria and be the best found so far
            if (pmt_final_alt <= pmt_alvo + 0.01 and 
                total_final_alt <= saldo_devedor_total and # Total Paid must be less than or equal to estimated balance
                diferenca_alt >= 0 and diferenca_alt <= 50.00):
                
                if diferenca_alt > melhor_diferenca_total_pago_proximo: # Maximize difference (lesser total paid)
                    melhor_diferenca_total_pago_proximo = diferenca_alt
                    melhor_resultado_total_pago_proximo = {
                        "prazo": novo_prazo,
                        "taxa": taxa_final_alt,
                        "pmt": pmt_final_alt,
                        "total_pago": total_final_alt,
                        "diferenca": diferenca_alt 
                    }
    
    if melhor_resultado_total_pago_proximo:
        st.success("📌 Cenário 2: Alternativo (Total Pago NÃO maior que Saldo Estimado, Diferença (Saldo - Total) <= R$ 50,00):")
        st.info(f"📅 Prazo: **{melhor_resultado_total_pago_proximo['prazo']} meses**")
        st.info(f"💰 Parcela: **R$ {melhor_resultado_total_pago_proximo['pmt']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"📉 Taxa de Juros: **{melhor_resultado_total_pago_proximo['taxa'] * 100:.4f}% ao mês**")
        st.info(f"📦 Total Pago: **R$ {melhor_resultado_total_pago_proximo['total_pago']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"↔️ Diferença (Saldo Estimado - Total Pago): **R$ {melhor_resultado_total_pago_proximo['diferenca']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
    else:
        st.warning("⚠️ Cenário 2: Não foi possível encontrar um cenário alternativo com total pago não maior que o saldo estimado e diferença (Saldo - Total) entre R$ 0,00 e R$ 50,00.")
