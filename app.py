import streamlit as st
from datetime import date

# --- CONFIGURAÇÃO DA PÁGINA (VISUAL) ---
st.set_page_config(
    page_title="Inclusão.AI | Gestão de PEI",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS Personalizado para deixar mais bonito
st.markdown("""
    <style>
    .main {background-color: #f8f9fa;}
    .stButton>button {width: 100%; background-color: #004e92; color: white;}
    .stTextArea>div>div>textarea {background-color: #ffffff;}
    h1 {color: #004e92;}
    h2 {color: #333;}
    .success-box {padding: 1rem; background-color: #d4edda; border-radius: 5px; color: #155724; border: 1px solid #c3e6cb;}
    </style>
    """, unsafe_allow_html=True)

# --- CABEÇALHO ---
col_logo, col_titulo = st.columns([1, 5])
with col_logo:
    st.markdown("# 🧩")
with col_titulo:
    st.title("Sistema de Gestão de PEI - Inclusão.AI")
    st.markdown("**Conformidade:** Decreto nº 12.773 (Dez/2025) | **Foco:** Estudo de Caso e Plano de Ação")

st.markdown("---")

# --- SIDEBAR (MENU LATERAL) ---
with st.sidebar:
    st.header("📌 Painel de Controle")
    st.info("Este sistema dispensa a obrigatoriedade de laudo médico para início das intervenções pedagógicas (Art. 3º).")
    
    st.markdown("---")
    st.markdown("### Status do Documento")
    progresso = st.progress(0)
    
    st.markdown("---")
    st.caption("Desenvolvido para Cases Pedagógicos")
    st.caption("Versão 2.0 - Atualizada")

# --- GERENCIAMENTO DE ESTADO (MEMÓRIA DO APP) ---
if 'nome' not in st.session_state: st.session_state.nome = ""
if 'barreiras_sel' not in st.session_state: st.session_state.barreiras_sel = []
if 'potencias_sel' not in st.session_state: st.session_state.potencias_sel = []

# --- NAVEGAÇÃO POR ABAS (MAIS MODERNO) ---
tab1, tab2, tab3, tab4 = st.tabs(["1. Identificação", "2. Mapeamento (Anamnese)", "3. Apoio Externo", "4. Gerar PEI"])

# --- ABA 1: IDENTIFICAÇÃO ---
with tab1:
    st.subheader("📝 Dados do Aluno")
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.nome = st.text_input("Nome Completo do Aluno", st.session_state.nome)
        serie = st.selectbox("Ano/Série Atual", ["Educação Infantil", "1º ao 5º Ano (Fund I)", "6º ao 9º Ano (Fund II)", "Ensino Médio"])
    with c2:
        dtnasc = st.date_input("Data de Nascimento")
        turma = st.text_input("Turma/Turno")
    
    st.markdown("#### Histórico Escolar Breve")
    st.text_area("Descreva brevemente a trajetória escolar (repetências, escolas anteriores):", height=100)
    
    st.markdown("#### Hipótese Diagnóstica (Opcional)")
    laudo = st.radio("A família apresentou laudo médico?", ["Não", "Sim", "Em investigação"])
    if laudo == "Sim":
        st.text_input("Qual o CID/Diagnóstico informado?")

# --- ABA 2: MAPEAMENTO PEDAGÓGICO (O CORAÇÃO DO APP) ---
with tab2:
    st.subheader("🔍 Estudo de Caso: Barreiras e Potências")
    st.markdown("Selecione as opções que melhor descrevem o aluno no ambiente escolar.")

    col_pot, col_bar = st.columns(2)

    with col_pot:
        st.markdown("### 🌟 Potencialidades (Pontos Fortes)")
        st.caption("Use isso para engajar o aluno.")
        potencias = [
            "Memória visual excelente", "Hiperfoco em temas específicos", "Vocabulário avançado",
            "Habilidade com tecnologia", "Desenho/Artes", "Gosta de ajudar colegas",
            "Pensamento lógico-matemático", "Criatividade acima da média", "Boa coordenação motora"
        ]
        st.session_state.potencias_sel = st.multiselect("Selecione as habilidades:", potencias)

    with col_bar:
        st.markdown("### 🚧 Barreiras de Aprendizagem")
        st.caption("O que impede o acesso ao currículo?")
        
        with st.expander("Barreiras Sensoriais e Físicas"):
            b_sensorial = st.multiselect("Selecione:", [
                "Hipersensibilidade auditiva (barulho)", "Hipersensibilidade tátil/texturas",
                "Agitação motora constante", "Baixa visão/Audição", "Dificuldade motora fina"
            ])
            
        with st.expander("Barreiras de Comunicação e Social"):
            b_social = st.multiselect("Selecione:", [
                "Não mantém contato visual", "Fala pouco compreensível", "Ecolalia (repetição)",
                "Isolamento social/Recreio", "Dificuldade em entender regras sociais/ironia",
                "Comportamento opositor/agressivo"
            ])
            
        with st.expander("Barreiras Cognitivas/Acadêmicas"):
            b_cognitiva = st.multiselect("Selecione:", [
                "Dificuldade de foco/atenção sustentada", "Não copia do quadro",
                "Dificuldade na alfabetização/leitura", "Desorganização espacial no caderno",
                "Dificuldade em sequenciar tarefas"
            ])
            
        st.session_state.barreiras_sel = b_sensorial + b_social + b_cognitiva

# --- ABA 3: APOIO EXTERNO E SAÚDE ---
with tab3:
    st.subheader("🤝 Rede de Apoio")
    st.write("Quais profissionais atendem o aluno fora da escola?")
    
    c_saude1, c_saude2 = st.columns(2)
    with c_saude1:
        st.checkbox("Psicólogo")
        st.checkbox("Fonoaudiólogo")
        st.checkbox("Terapeuta Ocupacional")
    with c_saude2:
        st.checkbox("Neuropediatra")
        st.checkbox("Psicopedagogo")
        st.checkbox("Acompanhante Terapêutico (AT)")

    st.text_area("Observações sobre medicação ou rotina de sono (relato da família):", height=100)

# --- ABA 4: GERADOR DE PEI ---
with tab4:
    st.subheader("🚀 Plano de Ensino Individualizado (PEI)")
    
    if st.session_state.nome == "":
        st.warning("⚠️ Volte na aba 'Identificação' e preencha o nome do aluno.")
    else:
        # Lógica de Sugestão de Metas (IA Simulada)
        estrategias = []
        
        # Lógica baseada nas seleções
        if "Hipersensibilidade auditiva (barulho)" in st.session_state.barreiras_sel:
            estrategias.append("🔴 AMBIENTE: Permitir uso de fones/abafadores em momentos de crise ou muito ruído.")
            estrategias.append("🔴 ROTINA: Antecipar sinais sonoros (sinal do recreio/entrada).")
            
        if "Não copia do quadro" in st.session_state.barreiras_sel:
            estrategias.append("🟡 MATERIAL: Fornecer pauta impressa ou permitir foto da lousa.")
            estrategias.append("🟡 AVALIAÇÃO: Reduzir a quantidade de exercícios (foco na qualidade, não volume).")
            
        if "Dificuldade de foco/atenção sustentada" in st.session_state.barreiras_sel:
            estrategias.append("🟢 MEDIAÇÃO: Fragmentar tarefas complexas em etapas curtas (Checklist).")
            estrategias.append("🟢 SALA: Assento preferencial longe de janelas e porta (foco do professor).")
            
        if "Comportamento opositor/agressivo" in st.session_state.barreiras_sel:
            estrategias.append("🟣 COMPORTAMENTO: Criar cartões de regulação emocional (ex: cartão vermelho para 'preciso sair').")
            estrategias.append("🟣 VÍNCULO: Validar sentimentos antes de corrigir o comportamento.")

        # Texto Padrão se nada for selecionado
        if not estrategias:
            estrategias.append("Nenhuma barreira específica selecionada. O plano focará no Desenho Universal para Aprendizagem (DUA).")

        # Visualização do Documento
        st.markdown('<div class="success-box">✅ Documento gerado com base nas evidências coletadas.</div>', unsafe_allow_html=True)
        
        texto_final = f"""
DOC. REF: PEI-{date.today().year}/COC
INSTITUIÇÃO: [Nome da Escola]
============================================================
PLANO DE ENSINO INDIVIDUALIZADO (PEI)
Decreto nº 12.773/2025
============================================================

1. DADOS DO ESTUDANTE
---------------------
Nome: {st.session_state.nome}
Série: {serie}
Data de Elaboração: {date.today().strftime('%d/%m/%Y')}

2. ESTUDO DE CASO (SÍNTESE)
---------------------------
Com base na observação pedagógica e relato familiar, identificamos:

POTENCIALIDADES (Pontos de partida para aprendizagem):
{', '.join(st.session_state.potencias_sel) if st.session_state.potencias_sel else "Não declaradas."}

BARREIRAS (O que precisa ser removido/adaptado):
{', '.join(st.session_state.barreiras_sel) if st.session_state.barreiras_sel else "Nenhuma barreira significativa reportada nesta triagem."}

3. PLANO DE AÇÃO E ADAPTAÇÕES CURRICULARES
------------------------------------------
Visando a garantia de aprendizado e permanência, a equipe escolar aplicará:

{chr(10).join(estrategias)}

4. CRITÉRIOS DE AVALIAÇÃO
-------------------------
A avaliação será formativa, considerando o percurso individual do aluno 
em relação às suas próprias conquistas anteriores.

__________________________________
Assinatura da Coordenação Pedagógica
        """
        
        col_txt, col_btn = st.columns([2, 1])
        with col_txt:
            st.text_area("Prévia do Documento:", texto_final, height=400)
        with col_btn:
            st.download_button(
                label="📥 Baixar Documento (.txt)",
                data=texto_final,
                file_name=f"PEI_{st.session_state.nome.replace(' ', '_')}.txt",
                mime="text/plain"
            )
            st.markdown("*Dica: Copie o texto e cole no Word timbrado da escola para a versão final.*")
