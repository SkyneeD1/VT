import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Lançamentos", page_icon="🧠", layout="centered")

st.title("🧠 Lançamentos")
st.subheader("📋 Cole sua tabela:")

texto = st.text_area("Cole aqui:", height=300)

if st.button("🚀 Processar"):
    if texto.strip() == "":
        st.warning("⚠️ Cole os dados no campo acima.")
    else:
        linhas = texto.strip().splitlines()

        # 🔥 Junta linhas quebradas
        linhas_corrigidas = []
        linha_acumulada = ""

        for linha in linhas:
            linha_check = linha.strip()
            if any(x in linha_check.upper() for x in ["CÁLCULO LIQUIDADO", "VERSÃO", "PÁG"]):
                continue  # Ignorar rodapé

            numeros = re.findall(r'[\d\.,\(\)]+', linha_check)
            if len(numeros) >= 3:
                if linha_acumulada:
                    linha_completa = linha_acumulada + " " + linha_check
                    linhas_corrigidas.append(linha_completa.strip())
                    linha_acumulada = ""
                else:
                    linhas_corrigidas.append(linha_check.strip())
            else:
                linha_acumulada += " " + linha_check

        if linha_acumulada:
            linhas_corrigidas.append(linha_acumulada.strip())

        # 🏗️ Processamento
        dados = []
        for linha in linhas_corrigidas:
            numeros = re.findall(r'[\d\.,\(\)]+', linha)
            if len(numeros) >= 1:
                total = numeros[-1]  # pega o último número da linha (TOTAL)
                try:
                    # 🔎 Se tiver parênteses → valor negativo
                    if "(" in total and ")" in total:
                        total = -float(total.replace("(", "").replace(")", "").replace('.', '').replace(',', '.'))
                    else:
                        total = float(total.replace('.', '').replace(',', '.'))
                except:
                    total = 0.0

                descricao = linha
                for num in numeros[-3:]:
                    descricao = descricao.rsplit(num, 1)[0]
                descricao = descricao.strip().upper()

                dados.append([descricao, total])

        df = pd.DataFrame(dados, columns=['Descricao', 'Total'])

        # 🔥 Categorização
        def classificar_verba(descricao):
            desc = descricao.upper()

            # 🔹 INDENIZAÇÕES (abrangente)
            indenizacoes = [
                "ACIDENTE", "ACIDENTE DE TRABALHO",
                "VEICULO LOCADO", "VEÍCULOS LOCADOS", "LOCAÇÃO", "LOCAÇÃO DE VEICULOS", "LOCAÇÃO DE VEÍCULOS",
                "DOENÇA", "DOENÇAS DO TRABALHO",
                "DANO MORAL", "DANOS MORAIS", "DANO MATERIAL", "DANOS MATERIAIS",
                "INDENIZAÇÃO", "INDENIZACAO",
                "VALE TRANSPORTE", "VALE-TRANSPORTE",
                "VALE ALIMENTAÇÃO", "VALE-ALIMENTAÇÃO", "VALE REFEIÇÃO", "VALE-REFEIÇÃO",
                "RESCISÃO INDIRETA", "RESCISAO INDIRETA",
                "MULTA ART. 477", "MULTA ART. 467"
            ]
            if any(palavra in desc for palavra in indenizacoes):
                return "INDENIZAÇÕES"

            # 🔹 HORAS EXTRAS
            if (
                "HORA EXTRA" in desc
                or "HORAS EXTRAS" in desc
                or "INTERVALO INTRAJORNADA" in desc
                or "INTERVALO INTERJORNADA" in desc
            ):
                return "HORAS EXTRAS"

            # 🔹 ADICIONAIS DIVERSOS
            adicionais = ["ADICIONAL", "INSALUBRIDADE", "PERICULOSIDADE", "NOTURNO", "DSR"]
            if any(palavra in desc for palavra in adicionais):
                return "ADICIONAIS DIVERSOS"

            # 🔹 DIFERENÇAS SALARIAIS
            if "DIFERENÇA" in desc or "SALARIAL" in desc or "REAJUSTE" in desc:
                return "DIFERENÇAS SALARIAIS"

            # 🔹 HONORÁRIOS
            if "HONORÁRIO" in desc or "ADVOCATÍCIO" in desc or "PERICIA" in desc:
                return "HONORÁRIOS"

            # 🔹 Demais ações (default)
            return "DEMAIS AÇÕES"

        df['Categoria'] = df['Descricao'].apply(classificar_verba)

        # 📊 Agrupamento
        resultado = df.groupby('Categoria').sum(numeric_only=True).reset_index()

        # 🔎 Honorários líquidos
        honorarios_liquidos = df[df['Categoria'] == "HONORÁRIOS"]['Total'].sum()

        # 🔄 Transformar em horizontal com colunas fixas
        categorias_fixas = [
            "INDENIZAÇÕES",
            "HORAS EXTRAS",
            "ADICIONAIS DIVERSOS",
            "DIFERENÇAS SALARIAIS",
            "HONORÁRIOS",
            "DEMAIS AÇÕES"
        ]

        linha_final = {cat: 0.0 for cat in categorias_fixas}
        for _, row in resultado.iterrows():
            cat = row['Categoria']
            if cat in linha_final:
                linha_final[cat] = row['Total']

        # Garantir que Honorários use sempre o valor líquido encontrado
        linha_final["HONORÁRIOS"] = honorarios_liquidos

        # Criar DataFrame final
        df_final = pd.DataFrame([linha_final], columns=categorias_fixas)

        # ➕ Total geral no final
        df_final["TOTAL GERAL"] = df_final.sum(axis=1)

        # 🔧 Formatar em padrão brasileiro
        for col in df_final.columns:
            df_final[col] = df_final[col].apply(
                lambda x: f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            )

        st.success("✅ Processamento concluído!")
        st.subheader("📊 Resultado Consolidado (Horizontal):")
        st.dataframe(df_final, use_container_width=True)
