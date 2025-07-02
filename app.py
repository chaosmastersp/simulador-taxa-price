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
    # Scenario 1: Best result primarily targeting PMT_ALVO, and total_pago should be within the acceptable difference
    melhor_resultado_pmt_alvo = None
    melhor_diferenca_pmt_alvo = float('inf') 
    
    taxa_limite = taxa_max

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

            diferenca = saldo_devedor_total - total_pago_calc # Calculate difference as Saldo - Total Pago
            
            # Applying the new limit: diferenca (Saldo Estimado - Total Pago) must be >= -50.00 (i.e., total_pago <= saldo_devedor_total + 50.00)
            # And also, total_pago should preferably be <= saldo_devedor_total, or only slightly above.
            # Let's define the acceptable range for total_pago: [saldo_devedor_total - 50.00, saldo_devedor_total + 50.00]
            
            # The core goal for "melhor_resultado_pmt_alvo" is to find the best PMT match while keeping total_pago within a reasonable range
            # and minimizing the absolute difference to saldo_devedor_total.
            
            if (pmt_calc <= pmt_alvo + 0.01 and 
                total_pago_calc >= saldo_devedor_total - 50.00 and 
                total_pago_calc <= saldo_devedor_total + 50.00):
                
                # We want the result with the smallest absolute difference within this range
                current_abs_diferenca = abs(saldo_devedor_total - total_pago_calc)
                
                if current_abs_diferenca < melhor_diferenca_pmt_alvo:
                    melhor_diferenca_pmt_alvo = current_abs_diferenca
                    melhor_resultado_pmt_alvo = {
                        "prazo": prazo,
                        "taxa": taxa_final,
                        "pmt": pmt_calc,
                        "total_pago": total_pago_calc,
                        "diferenca": current_abs_diferenca # Store absolute difference for display
                    }
    
    if melhor_resultado_pmt_alvo:
        st.success("✅ Cenário 1: Melhor Resultado (Parcela próxima da desejada, Diferença absoluta <= R$ 50,00):")
        st.info(f"📅 Prazo: **{melhor_resultado_pmt_alvo['prazo']} meses**")
        st.info(f"💰 Parcela: **R$ {melhor_resultado_pmt_alvo['pmt']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"📉 Taxa de Juros: **{melhor_resultado_pmt_alvo['taxa'] * 100:.4f}% ao mês**")
        st.info(f"📦 Total Pago: **R$ {melhor_resultado_pmt_alvo['total_pago']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"↔️ Diferença Absoluta (Saldo Estimado - Total Pago): **R$ {melhor_resultado_pmt_alvo['diferenca']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
    else:
        st.warning("⚠️ Cenário 1: Não foi possível encontrar um resultado com parcela desejada e diferença absoluta menor ou igual a R$ 50,00.")

    st.markdown("---") # Separador para clareza

    # Scenario 2: Alternative scenario - Total paid as close as possible to estimated balance, respecting pmt_alvo
    melhor_resultado_total_pago_proximo = None
    melhor_diferenca_total_pago_proximo = float('inf') # This will store the absolute difference for comparison

    for novo_prazo in range(1, 97):
        datas_alt = [data_venc1 + relativedelta(months=i) for i in range(novo_prazo)]
        low_taxa_alt, high_taxa_alt = 0.0001, taxa_max
        taxa_encontrada_total_pago = None
        
        for _ in range(100):
            mid_taxa_alt = (low_taxa_alt + high_taxa_alt) / 2
            if mid_taxa_alt <= 0: mid_taxa_alt = 0.0001
            
            pmt_mid_alt, total_mid_alt = get_pmt_and_total(mid_taxa_alt, saldo, datas_alt, data_lib)
            
            # The goal here is to get total_mid_alt within the +/- 50.00 range of saldo_devedor_total
            # while also considering pmt_alvo.
            
            # Check if current total_mid_alt is within the acceptable range AND pmt is acceptable
            if (total_mid_alt >= saldo_devedor_total - 50.00 and 
                total_mid_alt <= saldo_devedor_total + 50.00 and
                pmt_mid_alt <= pmt_alvo + 0.01): # PMT must be acceptable
                
                taxa_encontrada_total_pago = mid_taxa_alt
                break # Found a candidate within the range
            
            # Adjust search range based on total_mid_alt relative to the target range
            elif total_mid_alt > saldo_devedor_total + 50.00: # Too high
                high_taxa_alt = mid_taxa_alt
            elif total_mid_alt < saldo_devedor_total - 50.00: # Too low
                low_taxa_alt = mid_taxa_alt
            else: # total_mid_alt is within range but pmt_mid_alt is too high or other issues. Try to refine.
                if pmt_mid_alt > pmt_alvo + 0.01:
                    high_taxa_alt = mid_taxa_alt
                else: # pmt_mid_alt is fine but total_mid_alt is not exactly at the target, refine binary search
                    # this branch is a bit trickier, could oscillate. Let's keep it simple for now, the break should catch it.
                    if abs(total_mid_alt - saldo_devedor_total) < abs(low_taxa_alt - high_taxa_alt) * 1000: # Heuristic for convergence
                        taxa_encontrada_total_pago = mid_taxa_alt
                        break

        if taxa_encontrada_total_pago is not None:
            taxa_final_alt = round(taxa_encontrada_total_pago, 4)
            pmt_final_alt, total_final_alt = get_pmt_and_total(taxa_final_alt, saldo, datas_alt, data_lib)
            
            current_abs_diferenca_alt = abs(saldo_devedor_total - total_final_alt)

            # Final check with rounded values: must meet criteria and be the best found so far
            if (pmt_final_alt <= pmt_alvo + 0.01 and 
                total_final_alt >= saldo_devedor_total - 50.00 and 
                total_final_alt <= saldo_devedor_total + 50.00):
                
                if current_abs_diferenca_alt < melhor_diferenca_total_pago_proximo:
                    melhor_diferenca_total_pago_proximo = current_abs_diferenca_alt
                    melhor_resultado_total_pago_proximo = {
                        "prazo": novo_prazo,
                        "taxa": taxa_final_alt,
                        "pmt": pmt_final_alt,
                        "total_pago": total_final_alt,
                        "diferenca": current_abs_diferenca_alt # Store absolute difference for display
                    }
    
    if melhor_resultado_total_pago_proximo:
        st.success("📌 Cenário 2: Alternativo (Total Pago mais próximo do Saldo Estimado, Diferença absoluta <= R$ 50,00):")
        st.info(f"📅 Prazo: **{melhor_resultado_total_pago_proximo['prazo']} meses**")
        st.info(f"💰 Parcela: **R$ {melhor_resultado_total_pago_proximo['pmt']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"📉 Taxa de Juros: **{melhor_resultado_total_pago_proximo['taxa'] * 100:.4f}% ao mês**")
        st.info(f"📦 Total Pago: **R$ {melhor_resultado_total_pago_proximo['total_pago']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"↔️ Diferença Absoluta (Saldo Estimado - Total Pago): **R$ {melhor_resultado_total_pago_proximo['diferenca']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
    else:
        st.warning("⚠️ Cenário 2: Não foi possível encontrar um cenário alternativo com total pago próximo ao saldo estimado e diferença absoluta menor ou igual a R$ 50,00.")
