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
    return saldo / fator

# Lógica principal
if st.button("🔍 Calcular Melhor Taxa e Prazo"):
    melhor_resultado = None
    melhor_diferenca = float('inf') # Initialize with a very large number
    taxa_limite = taxa_max - 0.0001

    for prazo in range(1, 97):
        datas = [data_venc1 + relativedelta(months=i) for i in range(prazo)]
        taxa = 0.005
        for _ in range(100):
            pmt1 = calcula_pmt(taxa, saldo, datas, data_lib)
            pmt2 = calcula_pmt(taxa + 0.00001, saldo, datas, data_lib)
            f1 = pmt1 - pmt_alvo
            derivada = (pmt2 - pmt1) / 0.00001
            if abs(f1) < 0.00001 and taxa <= taxa_limite:
                break
            taxa = taxa - f1 / derivada
            if taxa < 0 or taxa > taxa_limite:
                taxa = None
                break

        if taxa is not None:
            taxa = round(taxa, 4)
            pmt = calcula_pmt(taxa, saldo, datas, data_lib)
            total_pago = pmt * prazo
            
            # Calculate the difference and compare
            diferenca = abs(saldo_devedor_total - total_pago)
            
            if pmt <= pmt_alvo and diferenca < melhor_diferenca: # Condition to find the best result (smallest difference)
                melhor_diferenca = diferenca
                melhor_resultado = {
                    "prazo": prazo,
                    "taxa": taxa,
                    "pmt": pmt,
                    "total_pago": total_pago,
                    "diferenca": diferenca
                }

    if melhor_resultado:
        st.success("✅ Melhor Resultado Encontrado (Menor Diferença):")
        st.info(f"📅 Prazo: **{melhor_resultado['prazo']} meses**")
        st.info(f"💰 Parcela: **R$ {melhor_resultado['pmt']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"📉 Taxa de Juros: **{melhor_resultado['taxa'] * 100:.4f}% ao mês**")
        st.info(f"📦 Total Pago: **R$ {melhor_resultado['total_pago']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"↔️ Diferença (Saldo Estimado - Total Pago): **R$ {melhor_resultado['diferenca']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
    else:
        st.warning("⚠️ Não foi possível encontrar a melhor taxa e prazo para os critérios informados.")


    # Cenário Alternativo (validando taxa e parcela com base no saldo devedor total estimado)
    encontrou_cenario2 = False

    def total_pago_por_taxa(taxa, saldo, datas, data_lib):
        # Prevent division by zero if factor becomes zero (though unlikely with valid dates)
        fator = sum(1 / (1 + taxa) ** ((d - data_lib).days / 30) for d in datas)
        if fator == 0: # Avoid division by zero in case 'fator' is 0
            return 0, 0
        pmt = saldo / fator
        return pmt, pmt * len(datas)

    for novo_prazo in range(1, 97):
        datas_alt = [data_venc1 + relativedelta(months=i) for i in range(novo_prazo)]
        low, high = 0.0001, taxa_max
        taxa_real_encontrada = None

        # Binary search for the optimal rate
        for _ in range(100):
            mid = (low + high) / 2
            if mid <= 0: # Ensure mid is positive to avoid issues with (1+mid)
                mid = 0.0001
            
            pmt_mid, total_mid = total_pago_por_taxa(mid, saldo, datas_alt, data_lib)
            
            # Check if this scenario meets the conditions (total paid close to estimated, pmt <= target)
            if abs(total_mid - saldo_devedor_total) <= 1.00 and pmt_mid <= pmt_alvo:
                taxa_real_encontrada = mid
                break # Found a good rate for this specific prazo
            elif total_mid > saldo_devedor_total or pmt_mid > pmt_alvo:
                high = mid
            else: # total_mid < saldo_devedor_total and pmt_mid < pmt_alvo (need higher total or pmt)
                low = mid

        if taxa_real_encontrada is not None:
            # Re-calculate with the found rounded rate to ensure accuracy for display
            taxa_real = round(taxa_real_encontrada, 4)
            pmt_final, total_final = total_pago_por_taxa(taxa_real, saldo, datas_alt, data_lib)
            
            # Final validation before displaying
            if pmt_final <= pmt_alvo and total_final <= saldo_devedor_total and total_final >= (saldo_devedor_total - 50.00):
                pmt_final = round(pmt_final, 2)
                total_final = round(total_final, 2)
                diferenca_cenario2 = abs(saldo_devedor_total - total_final)

                pmt_formatada = f"R$ {pmt_final:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                total_formatado = f"R$ {total_final:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                taxa_formatada = f"{taxa_real * 100:.2f}%"
                diferenca_formatada = f"R$ {diferenca_cenario2:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

                st.markdown("---")
                st.success("📌 Cenário Alternativo Encontrado:")
                st.info(f"📅 Prazo: **{novo_prazo} meses**")
                st.info(f"💰 Parcela: **{pmt_formatada}**")
                st.info(f"📉 Taxa de Juros: **{taxa_formatada} ao mês**")
                st.info(f"📦 Total Pago: **{total_formatado}**")
                st.info(f"↔️ Diferença (Saldo Estimado - Total Pago): **{diferenca_formatada}**")
                encontrou_cenario2 = True
                break # Break from the prazo loop as we found one alternative scenario

    if not encontrou_cenario2: # This 'if' now checks the flag
        st.warning("⚠️ Não foi possível calcular um cenário alternativo com total pago ≤ saldo estimado e parcela ≤ desejada.")

