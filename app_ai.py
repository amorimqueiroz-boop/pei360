import streamlit as st
from datetime import date
from io import BytesIO
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
import google.generativeai as genai

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="PEI 360º | AI", page_icon="✨", layout="wide", initial_sidebar_state="expanded")

# --- CSS VISUAL ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #2D3748; }
    :root { --arco-blue: #004e92; --arco-orange: #ff7f00; --input-border: #CBD5E0; --input-bg: #FFFFFF; }
    .stTextInput input, .stTextArea textarea, .stDateInput input, .stSelectbox div[data-baseweb="select"] {
        border: 1px solid var(--input-border) !important; background-color: var(--input-bg) !important; border-radius: 6px !important; color: #2D3748 !important; }
    .kpi-card { background: white; padding: 15px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); border-left: 5px solid var(--arco-orange); text-align: center; }
    .kpi-value { font-size: 24px; color: var(--arco-blue); font-weight: 800; }
    .kpi-title { font-size: 12px; color: #718096; font-weight: 600; text-transform: uppercase; }
    .stButton>button { background-color: var(--arco-blue); color: white; font-weight: 600; border-radius: 6px; border: none; height: 3em; width: 100%; }
    .stButton>button:hover { background-color: #003a6e; }
    .home-card { background: #F7FAFC; padding: 25px; border-radius: 12px; border: 1px solid #E2E8F0; height: 100%; }
    .status-info { color: #004e92; font-weight: bold; font-size: 0.9em; margin-top:-10px; margin-bottom:10px;}
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO GEMINI AI ---
def consultar_ia(api_key, dados):
    if not api_key: return None, "⚠️ Insira a API Key na barra lateral."
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        Aja como um Especialista em Inclusão Escolar.
        Aluno: {dados['nome']}, Série: {dados['serie']}.
        Hiperfoco: {dados['hiperfoco']}.
        Barreiras: {', '.join(dados['b_sensorial'] + dados['b_cognitiva'] + dados['b_social'])}.
        
        Gere 2 listas curtas e práticas:
        1. Adaptações de Acesso (Ambiente/Material).
        2. Adaptações Curriculares (Conteúdo/Avaliação).
        """
        response = model.generate_content(prompt)
        return response.text, None
    except Exception as e: return None, f"Erro IA: {str(e)}"

# --- GERADOR WORD ---
def gerar_docx_final(dados):
    doc = Document()
    titulo = doc.add_heading('PEI 360º - PLANO COM IA', 0)
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f'Escola: {dados["escola"]} | Ano: {date.today().year}').alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph('_' * 70)
    
    doc.add_heading('1. IDENTIFICAÇÃO', level=1)
    doc.add_paragraph(f"Nome: {dados['nome']} | Série: {dados['serie']}")
    doc.add_paragraph(f"Diagnóstico: {dados['cid']}")
    if dados['historico']: doc.add_paragraph(f"Histórico: {dados['historico']}")

    doc.add_heading('2. MAPEAMENTO', level=1)
    doc.add_paragraph(f"Suporte: {dados['nivel_suporte']} | Engajamento: {dados['nivel_engajamento']}")
    if dados['hiperfoco']: doc.add_paragraph(f"Hiperfoco: {dados['hiperfoco']}", style='List Bullet')
    for p in dados['potencias']: doc.add_paragraph(p, style='List Bullet')
    
    doc.add_heading('Barreiras:', level=2)
    # Correção do erro de Style (usando bold manual)
    if dados['b_sensorial']:
        p = doc.add_paragraph(); p.add_run("Sensoriais: ").bold = True
        for b in dados['b_sensorial']: doc.add_paragraph(b, style='List Bullet')
    if dados['b_cognitiva']:
        p = doc.add_paragraph(); p.add_run("Cognitivas: ").bold = True
        for b in dados['b_cognitiva']: doc.add_paragraph(b, style='List Bullet')
    if dados['b_social']:
        p = doc.add_paragraph(); p.add_run("Sociais: ").bold = True
        for b in dados['b_social']: doc.add_paragraph(b, style='List Bullet')

    doc.add_heading('3. ESTRATÉGIAS (IA + MANUAL)', level=1)
    if dados['ia_sugestao']:
        doc.add_heading('Sugestões da Inteligência Artificial:', level=2)
        doc.add_paragraph(dados['ia_sugestao'])
    
    doc.add_heading('Estratégias Selecionadas:', level=2)
    for e in dados['estrategias_acesso'] + dados['estrategias_curriculo']: doc.add_paragraph(e, style='List Bullet')

    doc.add_paragraph('\n___________________________\nCoordenação Pedagógica')
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- ESTADO ---
if 'dados' not in st.session_state:
    st.session_state.dados = {
        'nome': '', 'nasc': None, 'serie': '', 'turma': '', 'escola': '', 'cid': '', 'equipe_externa': [], 
        'historico': '', 'familia': '', 'hiperfoco': '', 'nivel_suporte': 'Leve', 'nivel_engajamento': 'Médio', 'nivel_autonomia': 'Parcial',
        'potencias': [], 'b_sensorial': [], 'b_cognitiva': [], 'b_social': [], 'estrategias_acesso': [], 'estrategias_curriculo': [], 'ia_sugestao': ''
    }

# --- INTERFACE ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Arco_Educa%C3%A7%C3%A3o_logo.png/640px-Arco_Educa%C3%A7%C3%A3o_logo.png", width=140)
    st.markdown("### 🤖 Gemini AI")
    api_key = st.text_input("Cole a API Key aqui:", type="password")
    st.info("Versão PRO com IA")

st.markdown("## PEI 360º <span style='font-size:0.6em; background:#E3F2FD; color:#004E92; padding:5px 10px; border-radius:15px;'>AI EDITION</span>", unsafe_allow_html=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 Visão", "👤 Aluno", "🔍 Mapa", "🤖 IA & Ação", "🖨️ Doc"])

with tab1:
    c1, c2 = st.columns(2)
    c1.markdown("<div class='home-card'><h3>📘 Diferencial IA</h3><p>O Gemini analisa o perfil do aluno e cria estratégias personalizadas.</p></div>", unsafe_allow_html=True)
    c2.markdown("<div class='home-card'><h3>⚖️ Legislação</h3><p>Decreto 12.773/25: Tecnologia assistiva como aliada.</p></div>", unsafe_allow_html=True)

with tab2:
    c1, c2 = st.columns(2)
    st.session_state.dados['nome'] = c1.text_input("Nome", st.session_state.dados['nome'])
    st.session_state.dados['nasc'] = c2.date_input("Nascimento")
    st.session_state.dados['escola'] = c1.text_input("Escola", st.session_state.dados['escola'])
    st.session_state.dados['serie'] = c2.selectbox("Série", ["Ed. Infantil", "Fund I", "Fund II", "Médio"])
    st.session_state.dados['cid'] = st.text_input("CID")
    c_h, c_f = st.columns(2)
    st.session_state.dados['historico'] = c_h.text_area("Histórico", height=100)
    st.session_state.dados['familia'] = c_f.text_area("Família", height=100)

with tab3:
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.dados['hiperfoco'] = st.text_input("Hiperfoco")
        st.session_state.dados['potencias'] = st.multiselect("Habilidades", ["Memória Visual", "Tecnologia", "Desenho", "Oralidade", "Lógica", "Música"])
        eng = st.select_slider("Engajamento", ["Baixo", "Médio", "Alto"], value="Médio"); st.session_state.dados['nivel_engajamento'] = eng
    with c2:
        with st.expander("Barreiras (Sensorial/Cognitivo/Social)", expanded=True):
            st.session_state.dados['b_sensorial'] = st.multiselect("Sensorial", ["Hipersensibilidade", "Agitação", "Baixa Visão"])
            st.session_state.dados['b_cognitiva'] = st.multiselect("Cognitivo", ["Atenção Curta", "Não copia", "Dificuldade Leitura"])
            st.session_state.dados['b_social'] = st.multiselect("Social", ["Isolamento", "Opositor", "Ecolalia"])
        sup = st.select_slider("Suporte", ["Leve", "Moderado", "Elevado"], value="Leve"); st.session_state.dados['nivel_suporte'] = sup

with tab4:
    st.markdown("### 🧠 Consultar Especialista Virtual")
    if st.button("✨ Gerar Estratégias com IA"):
        with st.spinner("Analisando caso..."):
            res, err = consultar_ia(api_key, st.session_state.dados)
            if err: st.error(err)
            else: st.session_state.dados['ia_sugestao'] = res; st.success("Análise concluída!")
    
    st.session_state.dados['ia_sugestao'] = st.text_area("Sugestões da IA (Editável):", st.session_state.dados['ia_sugestao'], height=250)
    
    st.markdown("---")
    c1, c2 = st.columns(2)
    st.session_state.dados['estrategias_acesso'] = c1.multiselect("Manual - Acesso", ["Tempo estendido", "Ledor", "Material ampliado", "Tablet"])
    st.session_state.dados['estrategias_curriculo'] = c2.multiselect("Manual - Currículo", ["Redução questões", "Prova Oral", "Atividade Prática"])

with tab5:
    if st.session_state.dados['nome']:
        doc = gerar_docx_final(st.session_state.dados)
        st.download_button("📥 BAIXAR PEI COM IA (.DOCX)", doc, "PEI_AI.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else: st.warning("Preencha o nome do aluno.")
