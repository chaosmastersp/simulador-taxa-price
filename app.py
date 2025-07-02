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
    fator = sum(1 / (1 + i) ** ((d - data_lib).days / 30) for d in datas)
    # Avoid division by zero if factor is extremely small or zero
    if fator == 0:
        return float('inf') # Return a very large number if factor is zero
    return saldo / fator

# Lógica principal
if st.button("🔍 Calcular Melhor Taxa e Prazo"):
    melhor_resultado_pmt = None
    melhor_diferenca_pmt = float('inf') # For results primarily targeting pmt_alvo

    melhor_resultado_total = None
    melhor_diferenca_total = float('inf') # For results primarily targeting saldo_devedor_total

    taxa_limite = taxa_max - 0.0001

    for prazo in range(1, 97):
        datas = [data_venc1 + relativedelta(months=i) for i in range(prazo)]
        
        # --- Scenario 1: Optimize for pmt_alvo ---
        taxa_pmt = 0.005 # Starting guess for Newton-Raphson
        encontrou_pmt = False
        for _ in range(100):
            pmt1 = calcula_pmt(taxa_pmt, saldo, datas, data_lib)
            pmt2 = calcula_pmt(taxa_pmt + 0.00001, saldo, datas, data_lib)
            
            f1 = pmt1 - pmt_alvo
            derivada = (pmt2 - pmt1) / 0.00001 if (pmt2 - pmt1) != 0 else 0.00001 # Avoid division by zero
            
            if abs(f1) < 0.00001 and taxa_pmt <= taxa_limite:
                encontrou_pmt = True
                break
            
            # Newton-Raphson step
            if derivada != 0:
                taxa_pmt = taxa_pmt - f1 / derivada
            else: # If derivative is zero, try a small adjustment or break
                taxa_pmt += 0.00001 
                
            if taxa_pmt < 0 or taxa_pmt > taxa_limite:
                taxa_pmt = None
                break

        if taxa_pmt is not None and encontrou_pmt:
            taxa_pmt_redonda = round(taxa_pmt, 4)
            pmt_calculado_pmt = calcula_pmt(taxa_pmt_redonda, saldo, datas, data_lib)
            total_pago_pmt = pmt_calculado_pmt * prazo
            
            diferenca_atual_pmt = abs(saldo_devedor_total - total_pago_pmt)
            
            # We still want the best match for pmt_alvo here, but also store the difference
            # Let's prioritize smallest difference to saldo_devedor_total within pmt_alvo constraint
            if pmt_calculado_pmt <= pmt_alvo + 0.01 and diferenca_atual_pmt < melhor_diferenca_pmt: # Add a small tolerance for pmt_alvo
                melhor_diferenca_pmt = diferenca_atual_pmt
                melhor_resultado_pmt = {
                    "prazo": prazo,
                    "taxa": taxa_pmt_redonda,
                    "pmt": pmt_calculado_pmt,
                    "total_pago": total_pago_pmt,
                    "diferenca": diferenca_atual_pmt
                }

        # --- Scenario 2: Optimize for saldo_devedor_total, respecting pmt_alvo ---
        low, high = 0.0001, taxa_max
        taxa_total_encontrada = None
        
        for _ in range(100): # Binary search for optimal rate
            mid = (low + high) / 2
            if mid <= 0: mid = 0.0001 # Ensure positive rate
            
            pmt_mid, total_mid = calcula_pmt(mid, saldo, datas, data_lib), calcula_pmt(mid, saldo, datas, data_lib) * len(datas) # Recalculate total for clarity
            
            # Prioritize total_mid close to saldo_devedor_total AND pmt_mid <= pmt_alvo
            if abs(total_mid - saldo_devedor_total) <= 1.00 and pmt_mid <= pmt_alvo + 0.01: # Small tolerance for PMT
                taxa_total_encontrada = mid
                break
            
            if total_mid > saldo_devedor_total or pmt_mid > pmt_alvo: # If total is too high or pmt is too high, decrease rate
                high = mid
            else: # If total is too low and pmt is fine, increase rate
                low = mid

        if taxa_total_encontrada is not None:
            taxa_total_redonda = round(taxa_total_encontrada, 4)
            pmt_calculado_total = calcula_pmt(taxa_total_redonda, saldo, datas, data_lib)
            total_pago_total = pmt_calculado_total * prazo
            
            diferenca_atual_total = abs(saldo_devedor_total - total_pago_total)

            # Only consider if it's truly better in terms of difference to saldo_devedor_total
            if pmt_calculado_total <= pmt_alvo + 0.01 and diferenca_atual_total < melhor_diferenca_total:
                melhor_diferenca_total = diferenca_atual_total
                melhor_resultado_total = {
                    "prazo": prazo,
                    "taxa": taxa_total_redonda,
                    "pmt": pmt_calculado_total,
                    "total_pago": total_pago_total,
                    "diferenca": diferenca_atual_total
                }

    # Decide which is the "Melhor Resultado Encontrado"
    final_best_result = None
    if melhor_resultado_pmt and melhor_resultado_total:
        if melhor_resultado_pmt['diferenca'] <= melhor_resultado_total['diferenca']:
            final_best_result = melhor_resultado_pmt
        else:
            final_best_result = melhor_resultado_total
    elif melhor_resultado_pmt:
        final_best_result = melhor_resultado_pmt
    elif melhor_resultado_total:
        final_best_result = melhor_resultado_total

    if final_best_result:
        st.success("✅ Melhor Resultado Encontrado (Menor Diferença entre Saldo Estimado e Total Pago):")
        st.info(f"📅 Prazo: **{final_best_result['prazo']} meses**")
        st.info(f"💰 Parcela: **R$ {final_best_result['pmt']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"📉 Taxa de Juros: **{final_best_result['taxa'] * 100:.4f}% ao mês**")
        st.info(f"📦 Total Pago: **R$ {final_best_result['total_pago']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"↔️ Diferença (Saldo Estimado - Total Pago): **R$ {final_best_result['diferenca']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
    else:
        st.warning("⚠️ Não foi possível encontrar um cenário que atenda aos critérios.")

    st.markdown("---") # Separator for clarity

    # Display an alternative scenario if a different one was found and it's not the 'final_best_result'
    # This part needs careful consideration to avoid duplicating the 'best' result if they happen to be the same.
    # For simplicity, let's re-run the "Cenário Alternativo" logic if a distinct one is required,
    # or just omit it if the final_best_result already fulfills that purpose.
    # Given your request, I will simplify and just present the *single best result* according to your criteria.
    # If you still want two distinct scenarios (e.g., one optimized for PMT and one for Total), let me know.
    # For now, I'll focus on the single "Melhor Resultado" based on the difference.

