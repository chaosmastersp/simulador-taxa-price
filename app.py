import streamlit as st
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Autenticação simples
senha = st.text_input("🔐 Digite a senha para acessar:", type="password")
if senha != "simulador2025":
    st.warning("Acesso restrito.")
    st.stop()

st.set_page_config(page_title="Simulador de Taxa - Tabela Price", layout="centered")
st.title("📊 Simulador de Taxa para Parcela Deseada")

# Entradas do usuário
saldo = st.number_input("💰 Valor do Saldo Devedor (R$)", min_value=0.0, value=0.0, step=100.0, format="%.2f")
pmt_alvo = st.number_input("📦 Valor da Parcela Deseada (R$)", min_value=0.01, value=0.01, step=10.0, format="%.2f")
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
    melhor_total = 0
    melhor_resultado = None
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
            pmt = calcula_pmt(taxa, saldo, datas, data_lib)
            total_pago = pmt * prazo
            if total_pago <= saldo_devedor_total and total_pago > melhor_total:
                melhor_total = total_pago
                melhor_resultado = {
                    "prazo": prazo,
                    "taxa": taxa,
                    "pmt": pmt,
                    "total_pago": total_pago
                }

    if melhor_resultado:
        diferenca_total_pago = melhor_resultado['total_pago'] - saldo_devedor_total
        st.success("✅ Melhor Resultado Encontrado:")
        st.info(f"📅 Prazo: **{melhor_resultado['prazo']} meses**")
        st.info(f"💰 Parcela: **R$ {melhor_resultado['pmt']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"📉 Taxa de Juros: **{melhor_resultado['taxa'] * 100:.4f}% ao mês**")
        st.info(f"📦 Total Pago: **R$ {melhor_resultado['total_pago']:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))
        st.info(f"↔️ Diferença (Total Pago - Saldo Estimado): **R$ {diferenca_total_pago:,.2f}**".replace(",", "X").replace(".", ",").replace("X", "."))


    # Sempre calcular e exibir o cenário 2 com validação precisa da taxa e parcela
    encontrou_cenario2 = False

    def total_pago_por_taxa(taxa, saldo, datas, data_lib):
        fator = sum(1 / (1 + taxa) ** ((d - data_lib).days / 30) for d in datas)
        pmt = saldo / fator
        return pmt, pmt * len(datas)

    for novo_prazo in range(1, 97):
        datas_alt = [data_venc1 + relativedelta(months=i) for i in range(novo_prazo)]
        low, high = 0.0001, taxa_max
        for _ in range(100):
            mid = (low + high) / 2
            pmt_mid, total_mid = total_pago_por_taxa(mid, saldo, datas_alt, data_lib)
            if abs(total_mid - saldo_devedor_total) <= 1.00 and pmt_mid <= pmt_alvo:
                encontrou_cenario2 = True
                taxa_real = mid
                break
            if total_mid > saldo_devedor_total or pmt_mid > pmt_alvo:
                high = mid
            else:
                low = mid

        if encontrou_cenario2:
            pmt_final, total_final = total_pago_por_taxa(taxa_real, saldo, datas_alt, data_lib)
            taxa_real = round(taxa_real, 5)
            pmt_final = round(pmt_final, 2)
            total_final = round(total_final, 2)

            diferenca_total_pago_cenario2 = total_final - saldo_devedor_total
            
            pmt_formatada = f"R$ {pmt_final:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            total_formatado = f"R$ {total_final:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            taxa_formatada = f"{taxa_real * 100:.4f}%"
            diferenca_formatada = f"R$ {diferenca_total_pago_cenario2:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

            st.markdown("---")
            st.success("📌 Cenário Alternativo Encontrado:")
            st.info(f"📅 Prazo: **{novo_prazo} meses**")
            st.info(f"💰 Parcela: **{pmt_formatada}**")
            st.info(f"📉 Taxa de Juros: **{taxa_formatada} ao mês**")
            st.info(f"📦 Total Pago: **{total_formatado}**")
            st.info(f"↔️ Diferença (Total Pago - Saldo Estimado): **{diferenca_formatada}**")

            break

    else:
        st.warning("⚠️ Não foi possível calcular um cenário alternativo com total pago ≤ saldo estimado e parcela ≤ desejada.")
