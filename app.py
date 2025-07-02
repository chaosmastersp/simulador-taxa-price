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
# Ensure taxa_max input correctly captures 4 decimal places and is then divided by 100 for internal calculation
taxa_max = st.number_input("📉 Taxa de Juros Máxima Permitida (% ao mês)", min_value=0.01, value=2.0, step=0.0001, format="%.4f") / 100
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
    # Scenario 1: Best result primarily targeting PMT_ALVO, and finding the smallest absolute difference to Saldo Estimado
    melhor_resultado_pmt_alvo = None
    melhor_diferenca_pmt_alvo = float('inf') # Now minimizing absolute difference

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
            taxa_final = round(taxa_encontrada_pmt_alvo, 4) # Rate calculated and rounded to 4 decimals
            pmt_calc, total_pago_calc = get_pmt_and_total(taxa_final, saldo, datas, data_lib)

            diferenca = saldo_devedor_total - total_pago_calc # This is the actual difference
            current_abs_diferenca = abs(diferenca) # Absolute difference for comparison
            
            # Condition: pmt_calc close to pmt_alvo
            if pmt_calc <= pmt_alvo + 0.01:
                # Find the result with the smallest absolute difference
                if current_abs_diferenca < melhor_diferenca_pmt_alvo:
                    melhor_diferenca_pmt_alvo = current_abs_diferenca
                    melhor_resultado_pmt_alvo = {
                        "prazo": prazo,
                        "taxa": taxa_final,
                        "pmt": pmt_calc,
                        "total_pago": total_pago_calc,
                        "diferenca": diferenca # Store actual difference for display (can be positive or negative)
                    }
    
    if melhor_resultado_pmt_alvo:
        st.success("✅ Cenário 1: Melhor Resultado (Parcela próxima da desejada, com a menor diferença absoluta ao Saldo Estimado):")
        st.info(f"📅 Prazo: **{melhor_resultado_pmt_alvo['prazo']} meses**")
        st.info(f"💰 Parcela: **R$ {melhor_resultado_pmt_alvo['pmt']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"📉 Taxa de Juros: **{melhor_resultado_pmt_alvo['taxa'] * 100:.4f}% ao mês**") # Displayed with 4 decimals
        st.info(f"📦 Total Pago: **R$ {melhor_resultado_pmt_alvo['total_pago']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"↔️ Diferença (Saldo Estimado - Total Pago): **R$ {melhor_resultado_pmt_alvo['diferenca']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
    else:
        st.warning("⚠️ Cenário 1: Não foi possível encontrar um resultado com parcela desejada e a menor diferença absoluta ao saldo estimado.")

    st.markdown("---") # Separador para clareza

    # Scenario 2: Total paid as close as possible to estimated balance (not exceeding it)
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
            
            current_diferenca_alt_candidate = saldo_devedor_total - total_mid_alt

            if (total_mid_alt <= saldo_devedor_total + 0.01 and # Total Paid must be less than or equal to estimated balance (with tiny tolerance)
                current_diferenca_alt_candidate >= 0 and current_diferenca_alt_candidate <= 50.00 and # Difference must be between 0 and 50.00
                pmt_mid_alt <= pmt_alvo + 0.01): # PMT must be acceptable
                
                taxa_encontrada_total_pago = mid_taxa_alt
                break 
            
            elif total_mid_alt < saldo_devedor_total - 50.00: 
                low_taxa_alt = mid_taxa_alt
            elif total_mid_alt > saldo_devedor_total + 0.01: # If it exceeds saldo_devedor_total, decrease rate
                 high_taxa_alt = mid_taxa_alt
            else: # total_mid_alt is within range but pmt_mid_alt is too high or other issues.
                if pmt_mid_alt > pmt_alvo + 0.01:
                    high_taxa_alt = mid_taxa_alt
                else:
                    low_taxa_alt = mid_taxa_alt

        if taxa_encontrada_total_pago is not None:
            taxa_final_alt = round(taxa_encontrada_total_pago, 4) # Rate calculated and rounded to 4 decimals
            pmt_final_alt, total_final_alt = get_pmt_and_total(taxa_final_alt, saldo, datas_alt, data_lib)
            
            diferenca_alt = saldo_devedor_total - total_final_alt 
            
            if (pmt_final_alt <= pmt_alvo + 0.01 and 
                total_final_alt <= saldo_devedor_total + 0.01 and # Final check for total_pago not exceeding saldo
                diferenca_alt >= 0 and diferenca_alt <= 50.00):
                
                if diferenca_alt > melhor_diferenca_total_pago_proximo: 
                    melhor_diferenca_total_pago_proximo = diferenca_alt
                    melhor_resultado_total_pago_proximo = {
                        "prazo": novo_prazo,
                        "taxa": taxa_final_alt,
                        "pmt": pmt_final_alt,
                        "total_pago": total_final_alt,
                        "diferenca": diferenca_alt 
                    }
    
    if melhor_resultado_total_pago_proximo:
        st.success("📌 Cenário 2: Alternativo (Total Pago NÃO maior que Saldo Estimado, Diferença (Saldo - Total) entre R$ 0,00 e R$ 50,00):")
        st.info(f"📅 Prazo: **{melhor_resultado_total_pago_proximo['prazo']} meses**")
        st.info(f"💰 Parcela: **R$ {melhor_resultado_total_pago_proximo['pmt']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"📉 Taxa de Juros: **{melhor_resultado_total_pago_proximo['taxa'] * 100:.4f}% ao mês**") # Displayed with 4 decimals
        st.info(f"📦 Total Pago: **R$ {melhor_resultado_total_pago_proximo['total_pago']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"↔️ Diferença (Saldo Estimado - Total Pago): **R$ {melhor_resultado_total_pago_proximo['diferenca']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
    else:
        st.warning("⚠️ Cenário 2: Não foi possível encontrar um cenário alternativo com total pago não maior que o saldo estimado e diferença (Saldo - Total) entre R$ 0,00 e R$ 50,00.")

    st.markdown("---") # Separador para clareza

    # --- Scenario 3: Alternative allowing up to R$ 5.00 greater difference (Total Pago > Saldo Estimado) ---
    melhor_resultado_total_pago_maior = None
    melhor_diferenca_total_pago_maior = float('inf') # Minimize absolute difference (can be negative)

    for novo_prazo in range(1, 97):
        datas_alt = [data_venc1 + relativedelta(months=i) for i in range(novo_prazo)]
        low_taxa_alt, high_taxa_alt = 0.0001, taxa_max
        taxa_encontrada_total_pago_maior = None
        
        for _ in range(100):
            mid_taxa_alt = (low_taxa_alt + high_taxa_alt) / 2
            if mid_taxa_alt <= 0: mid_taxa_alt = 0.0001
            
            pmt_mid_alt, total_mid_alt = get_pmt_and_total(mid_taxa_alt, saldo, datas_alt, data_lib)
            
            if (pmt_mid_alt <= pmt_alvo + 0.01 and # PMT must be acceptable
                total_mid_alt >= saldo_devedor_total - 50.00 and # Total paid not too low
                total_mid_alt <= saldo_devedor_total + 5.00): # Total paid not more than 5.00 higher
                
                taxa_encontrada_total_pago_maior = mid_taxa_alt
                break
            
            elif total_mid_alt > saldo_devedor_total + 5.00: # If total is too high, decrease rate
                high_taxa_alt = mid_taxa_alt
            else: # If total is too low (or within range but PMT is too high), increase rate
                low_taxa_alt = mid_taxa_alt
                

        if taxa_encontrada_total_pago_maior is not None:
            taxa_final_alt_maior = round(taxa_encontrada_total_pago_maior, 4) # Rate calculated and rounded to 4 decimals
            pmt_final_alt_maior, total_final_alt_maior = get_pmt_and_total(taxa_final_alt_maior, saldo, datas_alt, data_lib)
            
            diferenca_alt_maior = saldo_devedor_total - total_final_alt_maior 
            
            if (pmt_final_alt_maior <= pmt_alvo + 0.01 and 
                total_final_alt_maior >= saldo_devedor_total - 50.00 and
                total_final_alt_maior <= saldo_devedor_total + 5.00):
                
                current_abs_diferenca_maior = abs(diferenca_alt_maior)

                if current_abs_diferenca_maior < melhor_diferenca_total_pago_maior:
                    melhor_diferenca_total_pago_maior = current_abs_diferenca_maior
                    melhor_resultado_total_pago_maior = {
                        "prazo": novo_prazo,
                        "taxa": taxa_final_alt_maior,
                        "pmt": pmt_final_alt_maior,
                        "total_pago": total_final_alt_maior,
                        "diferenca": diferenca_alt_maior # Store actual difference (can be negative)
                    }
    
    if melhor_resultado_total_pago_maior:
        st.success("🔵 Cenário 3: Alternativo (Total Pago pode ser até R$ 5,00 MAIOR que Saldo Estimado, Parcela Aceitável):")
        st.info(f"📅 Prazo: **{melhor_resultado_total_pago_maior['prazo']} meses**")
        st.info(f"💰 Parcela: **R$ {melhor_resultado_total_pago_maior['pmt']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"📉 Taxa de Juros: **{melhor_resultado_total_pago_maior['taxa'] * 100:.4f}% ao mês**") # Displayed with 4 decimals
        st.info(f"📦 Total Pago: **R$ {melhor_resultado_total_pago_maior['total_pago']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"↔️ Diferença (Saldo Estimado - Total Pago): **R$ {melhor_resultado_total_pago_maior['diferenca']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
    else:
        st.warning("⚠️ Cenário 3: Não foi possível encontrar um cenário alternativo onde o total pago é até R$ 5,00 maior que o saldo estimado, com parcela aceitável.")
