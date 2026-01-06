import streamlit as st
from datetime import date
from io import BytesIO
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from openai import OpenAI # Usamos a biblioteca OpenAI para conectar no DeepSeek

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="PEI 360º | DeepSeek Edition", page_icon="🦈", layout="wide", initial_sidebar_state="expanded")

# --- ESTILO VISUAL (MANTIDO) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #2D3748; }
    :root { --arco-blue: #004e92; --arco-orange: #ff7f00; --input-border: #CBD5E0; --input-bg: #FFFFFF; }
    .stTextInput input, .stTextArea textarea, .stDateInput input, .stSelectbox div[data-baseweb="select"] {
        border: 1px solid var(--input-border) !important; background-color: var(--input-bg) !important; border-radius: 8px !important; color: #2D3748 !important; }
    .stButton>button { background-color: var(--arco-blue); color: white; font-weight: 600; border-radius: 8px; border: none; height: 3em; width: 100%; transition: all 0.3s ease;}
    .stButton>button:hover { background-color: #003a6e; transform: scale(1.02); }
    .home-card { background: #F8FAFC; padding: 25px; border-radius: 12px; border: 1px solid #E2E8F0; height: 100%; box-shadow: 0 2px 4px rgba(0,0,0,0.02);}
    .home-card h3 { color: var(--arco-blue); margin-top: 0; margin-bottom: 10px;}
    .help-text { font-size: 0.9em; color: #4A5568; background-color: #EBF8FF; padding: 12px; border-radius: 8px; border-left: 4px solid #3182CE; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO DEEPSEEK ---
def consultar_ia(api_key, dados):
    if not api_key: return None, "⚠️ Insira a API Key da DeepSeek na barra lateral."
    try:
        # CONEXÃO COM DEEPSEEK
        # A mágica acontece aqui: usamos a biblioteca da OpenAI, mas mudamos a 'base_url'
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com"
        )
        
        prompt_sistema = "Você é um Especialista em Inclusão Escolar (PEI). Seja direto, técnico e muito empático."
        
        prompt_usuario = f"""
        Analise este aluno e crie estratégias pedagógicas:
        
        ALUNO: {dados['nome']} | SÉRIE: {dados['serie']}
        HIPERFOCO (Interesse): {dados['hiperfoco']}
        BARREIRAS: {', '.join(dados['b_sensorial'] + dados['b_cognitiva'] + dados['b_social'])}.
        
        Gere uma resposta estruturada:
        1. ESTRATÉGIA DE ENGAJAMENTO: Como usar o hiperfoco "{dados['hiperfoco']}" nas aulas?
        2. ADAPTAÇÕES DE ACESSO: O que mudar no ambiente ou material?
        3. ADAPTAÇÕES CURRICULARES: Como adaptar o conteúdo e a prova?
        """
        
        response = client.chat.completions.create(
            model="deepseek-chat", # Modelo V3 oficial
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario}
            ],
            temperature=0.7,
            stream=False
        )
        
        return response.choices[0].message.content, None
        
    except Exception as e:
        return None, f"Erro DeepSeek: {str(e)}"

# --- GERADOR DOCX ---
def gerar_docx_final(dados):
    doc = Document()
    titulo = doc.add_heading('PEI 360º - PLANO DE EDUCAÇÃO INCLUSIVA', 0)
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f'Escola: {dados["escola"]} | Ano: {date.today().year}').alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph('_' * 70)
    
    doc.add_heading('1. IDENTIFICAÇÃO E CONTEXTO', level=1)
    doc.add_paragraph(f"Nome: {dados['nome']} | Série: {dados['serie']}")
    tipo_diag = "Diagnóstico Clínico (Laudo)" if dados['tem_laudo'] else "Hipótese Diagnóstica (Em investigação)"
    doc.add_paragraph(f"{tipo_diag}: {dados['diagnostico']}")
    
    if dados['historico']: doc.add_heading('Histórico:', level=2); doc.add_paragraph(dados['historico'])
    if dados['familia']: doc.add_heading('Família:', level=2); doc.add_paragraph(dados['familia'])

    doc.add_heading('2. MAPEAMENTO PEDAGÓGICO', level=1)
    doc.add_paragraph(f"Suporte: {dados['nivel_suporte']} | Engajamento: {dados['nivel_engajamento']}")
    if dados['hiperfoco']: doc.add_paragraph(f"Hiperfoco: {dados['hiperfoco']}", style='List Bullet')
    for p in dados['potencias']: doc.add_paragraph(p, style='List Bullet')
    
    doc.add_heading('Barreiras:', level=2)
    if dados['b_sensorial']: 
        doc.add_paragraph("Sensorial/Físico:").bold = True
        for b in dados['b_sensorial']: doc.add_paragraph(b, style='List Bullet')
    if dados['b_cognitiva']: 
        doc.add_paragraph("Cognitivo:").bold = True
        for b in dados['b_cognitiva']: doc.add_paragraph(b, style='List Bullet')
    if dados['b_social']: 
        doc.add_paragraph("Social/Emocional:").bold = True
        for b in dados['b_social']: doc.add_paragraph(b, style='List Bullet')

    doc.add_heading('3. ESTRATÉGIAS', level=1)
    if dados['ia_sugestao']:
        doc.add_heading('Consultoria DeepSeek AI:', level=2)
        doc.add_paragraph(dados['ia_sugestao'])
    
    doc.add_heading('Definições da Escola:', level=2)
    doc.add_paragraph("Adaptações de Acesso:", style='Heading 3')
    for e in dados['estrategias_acesso']: doc.add_paragraph(e, style='List Bullet')
    doc.add_paragraph("Adaptações Curriculares:", style='Heading 3')
    for e in dados['estrategias_curriculo']: doc.add_paragraph(e, style='List Bullet')

    doc.add_paragraph('\n___________________________\nCoordenação Pedagógica')
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- ESTADO ---
if 'dados' not in st.session_state:
    st.session_state.dados = {
        'nome': '', 'nasc': None, 'serie': '', 'escola': '', 
        'tem_laudo': False, 'diagnostico': '', 'historico': '', 'familia': '', 'hiperfoco': '', 
        'nivel_suporte': 'Leve', 'nivel_engajamento': 'Médio', 
        'potencias': [], 'b_sensorial': [], 'b_cognitiva': [], 'b_social': [], 
        'estrategias_acesso': [], 'estrategias_curriculo': [], 'ia_sugestao': ''
    }

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Arco_Educa%C3%A7%C3%A3o_logo.png/640px-Arco_Educa%C3%A7%C3%A3o_logo.png", width=140)
    st.markdown("### 🦈 Configuração DeepSeek")
    api_key = st.text_input("Chave API DeepSeek:", type="password", placeholder="Cole a chave sk-...")
    if not api_key: st.warning("Cole sua chave aqui")
    st.markdown("---")
    st.info("Sistema v4.3 | Powered by DeepSeek V3")

# --- APP ---
st.markdown("## PEI 360º <span style='font-size:0.6em; background:#E3F2FD; color:#004E92; padding:5px 12px; border-radius:15px; font-weight:600;'>DEEPSEEK EDITION</span>", unsafe_allow_html=True)

abas = ["🏠 Início", "👤 Aluno", "🔍 Mapeamento", "🤖 Assistente IA", "✅ Plano de Ação", "🖨️ Documento"]
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(abas)

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="home-card"><h3>📘 O PEI Inclusivo</h3><p>Ferramenta para estruturar o planejamento pedagógico com foco nas potencialidades do aluno.</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="home-card"><h3>🦈 Inteligência DeepSeek</h3><p>Utilizamos o modelo DeepSeek-V3, reconhecido mundialmente por sua capacidade de raciocínio avançado.</p></div>', unsafe_allow_html=True)

with tab2:
    c1, c2 = st.columns(2)
    st.session_state.dados['nome'] = c1.text_input("Nome", st.session_state.dados['nome'])
    st.session_state.dados['escola'] = c1.text_input("Escola", st.session_state.dados['escola'])
    st.session_state.dados['nasc'] = c2.date_input("Nascimento")
    st.session_state.dados['serie'] = c2.selectbox("Série", ["Ed. Infantil", "Fund I", "Fund II", "Ensino Médio"])
    st.markdown("---")
    cl, cd = st.columns([1,2])
    st.session_state.dados['tem_laudo'] = cl.checkbox("Possui Laudo?")
    st.session_state.dados['diagnostico'] = cd.text_input("Diagnóstico", st.session_state.dados['diagnostico'])
    c_h, c_f = st.columns(2)
    st.session_state.dados['historico'] = c_h.text_area("Histórico Escolar")
    st.session_state.dados['familia'] = c_f.text_area("Relato da Família")

with tab3:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### 🚀 Potências")
        st.session_state.dados['hiperfoco'] = st.text_input("Hiperfoco")
        st.session_state.dados['potencias'] = st.multiselect("Habilidades", ["Visual", "Tecnologia", "Artes", "Oralidade", "Lógica"])
        st.session_state.dados['nivel_engajamento'] = st.select_slider("Engajamento", ["Baixo", "Médio", "Alto"], value="Médio")
    with c2:
        st.markdown("### 🚧 Barreiras")
        st.session_state.dados['b_sensorial'] = st.multiselect("Sensorial", ["Hipersensibilidade", "Busca Sensorial", "Agitação"])
        st.session_state.dados['b_cognitiva'] = st.multiselect("Cognitivo", ["Atenção", "Leitura", "Rigidez"])
        st.session_state.dados['b_social'] = st.multiselect("Social", ["Isolamento", "Frustração", "Comunicação"])
        st.session_state.dados['nivel_suporte'] = st.select_slider("Suporte", ["Leve", "Moderado", "Intenso"], value="Leve")

with tab4:
    st.markdown("### 🤖 Consultoria DeepSeek")
    if st.button("✨ Gerar Sugestões"):
        if not st.session_state.dados['nome']: st.warning("Preencha o nome do aluno.")
        else:
            with st.spinner("DeepSeek pensando..."):
                res, err = consultar_ia(api_key, st.session_state.dados)
                if err: st.error(err)
                else: st.session_state.dados['ia_sugestao'] = res; st.success("Sucesso!")
    st.session_state.dados['ia_sugestao'] = st.text_area("Sugestões:", st.session_state.dados['ia_sugestao'], height=400)

with tab5:
    c1, c2 = st.columns(2)
    st.session_state.dados['estrategias_acesso'] = c1.multiselect("Adaptações de Acesso", ["Tempo estendido", "Ledor", "Material ampliado", "Tablet"])
    st.session_state.dados['estrategias_curriculo'] = c2.multiselect("Adaptações Curriculares", ["Redução de questões", "Prova Oral", "Atividade Prática"])

with tab6:
    if st.session_state.dados['nome']:
        doc_file = gerar_docx_final(st.session_state.dados)
        st.download_button("📥 Baixar DOCX", doc_file, f"PEI_{st.session_state.dados['nome']}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")