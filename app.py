# -*- coding: utf-8 -*-
import streamlit as st
from datetime import date

# Configuração da Página
st.set_page_config(page_title="Inclusão.AI - Gerador de PEI", layout="wide")

# Título e Cabeçalho Institucional
st.title("🧩 Inclusão.AI | Sistema de Gestão de PEI")
st.markdown(f"**Conformidade:** Decreto nº 12.773 (Dez/2025) | **Data:** {date.today().strftime('%d/%m/%Y')}")
st.markdown("---")

# Sidebar para Navegação
st.sidebar.header("Fluxo de Trabalho")
etapa = st.sidebar.radio("Selecione a Etapa:", ["1. Dados do Aluno", "2. Anamnese Pedagógica", "3. Gerar PEI e Relatório"])

# Variáveis de Sessão
if 'nome_aluno' not in st.session_state: st.session_state.nome_aluno = ""
if 'potencias' not in st.session_state: st.session_state.potencias = []
if 'barreiras' not in st.session_state: st.session_state.barreiras = []

# --- ETAPA 1: DADOS DO ALUNO ---
if etapa == "1. Dados do Aluno":
    st.subheader("📄 Identificação Escolar")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.nome_aluno = st.text_input("Nome Completo do Aluno", st.session_state.nome_aluno)
        st.session_state.ano_escolar = st.selectbox("Ano/Série", ["Ed. Infantil", "1º ao 5º Ano", "6º ao 9º Ano", "Ensino Médio"])
    with col2:
        st.session_state.data_nasc = st.date_input("Data de Nascimento")
        st.text_area("Histórico Escolar Breve (Escolas anteriores, repetências)", height=100)

    st.info("💡 Pela nova resolução, a ausência de laudo médico NÃO impede a elaboração deste plano.")

# --- ETAPA 2: ANAMNESE / ESTUDO DE CASO ---
elif etapa == "2. Anamnese Pedagógica":
    st.subheader("🔍 Estudo de Caso: Mapeamento de Potências e Barreiras")
    st.write("Esqueça o 'Diagnóstico Clínico'. Foque no funcionamento do aluno na escola.")
    
    st.markdown("### 1. Potencialidades e Hiperfocos")
    st.session_state.potencias = st.multiselect(
        "O que o aluno JÁ faz bem ou gosta muito? (Base para engajamento)",
        ["Memória visual excelente", "Gosta de desenhar/artes", "Hiperfoco em tecnologia/games", 
         "Boa oralidade", "Gosta de ajudar colegas", "Habilidade lógico-matemática", "Interesse por música"]
    )
    
    st.markdown("---")
    
    st.markdown("### 2. Barreiras Identificadas")
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        st.markdown("**Barreiras Comunicacionais e de Interação**")
        barreiras_com = st.multiselect(
            "Selecione as dificuldades observadas:",
            ["Não mantém contato visual", "Dificuldade em expressar dor/sentimento", 
             "Fala pouco compreensível", "Dificuldade de compreender ironias/regras sociais",
             "Isolamento no recreio"]
        )
    with col_b2:
        st.markdown("**Barreiras Sensoriais e de Aprendizagem**")
        barreiras_sen = st.multiselect(
            "Selecione os desafios cognitivos/sensoriais:",
            ["Hipersensibilidade a barulho (tapa ouvidos)", "Agitação motora excessiva", 
             "Dificuldade de foco sustentado", "Não copia do quadro", 
             "Dificuldade na escrita (coordenação fina)"]
        )
    st.session_state.barreiras = barreiras_com + barreiras_sen
    
    st.markdown("### 3. O que a família relata?")
    st.text_area("Anote aqui rotinas de casa que funcionam (ex: dorme bem, come sozinho):")

# --- ETAPA 3: GERADOR DE PEI ---
elif etapa == "3. Gerar PEI e Relatório":
    st.subheader("🚀 Plano de Ensino Individualizado (PEI)")
    
    if not st.session_state.nome_aluno:
        st.warning("⚠️ Por favor, preencha o nome do aluno na Etapa 1 primeiro.")
    else:
        st.success(f"Gerando proposta de PEI para: **{st.session_state.nome_aluno}**")
        
        estrategias_sugeridas = []
        if "Hipersensibilidade a barulho (tapa ouvidos)" in st.session_state.barreiras:
            estrategias_sugeridas.append("- Permitir uso de fones abafadores em momentos de pico de ruído.")
            estrategias_sugeridas.append("- Antecipar sinais sonoros (sinal do recreio).")
        if "Dificuldade de foco sustentado" in st.session_state.barreiras:
            estrategias_sugeridas.append("- Fragmentar tarefas longas em etapas curtas (Checklist visual).")
            estrategias_sugeridas.append("- Assento preferencial longe de janelas/porta.")
        if "Não copia do quadro" in st.session_state.barreiras:
            estrategias_sugeridas.append("- Fornecer material impresso ou permitir foto do quadro.")
            estrategias_sugeridas.append("- Escriba ou uso de tablet para registros longos.")
        if "Hiperfoco em tecnologia/games" in st.session_state.potencias:
            estrategias_sugeridas.append("- Gamificação: usar elementos de jogos para explicar conteúdos.")
            estrategias_sugeridas.append("- Permitir entrega de trabalhos em formato digital/vídeo.")
        if not estrategias_sugeridas:
            estrategias_sugeridas.append("- Observação contínua necessária para definir estratégias específicas.")

        pei_texto = f"""
        RELATÓRIO DE PLANO DE ENSINO INDIVIDUALIZADO (PEI)
        --------------------------------------------------
        Aluno: {st.session_state.nome_aluno}
        Data de Elaboração: {date.today().strftime('%d/%m/%Y')}
        Base Legal: Decreto nº 12.773/2025
        
        1. PERFIL DO ESTUDANTE
        Pontos Fortes a explorar: {', '.join(st.session_state.potencias)}
        
        2. BARREIRAS IDENTIFICADAS (Estudo de Caso)
        {', '.join(st.session_state.barreiras)}
        
        3. PLANO DE AÇÃO PEDAGÓGICA (Adaptações Curriculares)
        {chr(10).join(estrategias_sugeridas)}
        
        4. CRITÉRIOS DE AVALIAÇÃO
        Avaliação processual e qualitativa (Art. 24 da LDB).
        _____________________________
        Assinatura da Coordenação
        """
        st.text_area("Visualização do Documento Final:", pei_texto, height=400)
        st.download_button(label="📥 Baixar PEI em Texto (.txt)", data=pei_texto, file_name=f"PEI_{st.session_state.nome_aluno}.txt", mime="text/plain")
