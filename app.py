import streamlit as st
from datetime import date
from io import BytesIO
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

# --- CONFIGURAÇÃO VISUAL (Identidade Arco Educação) ---
st.set_page_config(
    page_title="PEI 360 | Arco Educação",
    page_icon="🧩",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Profissional e Limpo
st.markdown("""
    <style>
    /* Variáveis de Cor */
    :root {
        --arco-blue: #004e92;
        --arco-light-blue: #e3f2fd;
        --arco-orange: #ff7f00;
        --text-gray: #4a4a4a;
    }
    
    .main {background-color: #f8f9fa;}
    
    /* Títulos */
    h1, h2, h3 {color: var(--arco-blue); font-family: 'Helvetica Neue', sans-serif;}
    
    /* Botões */
    .stButton>button {
        background-color: var(--arco-blue); 
        color: white; 
        border-radius: 8px; 
        font-weight: 600;
        border: none;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover {background-color: #003366;}
    
    /* Caixas de Destaque (Cards) */
    .info-card {
        padding: 1.5rem;
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        border-left: 5px solid var(--arco-orange);
        margin-bottom: 1rem;
    }
    
    .lei-card {
        padding: 1rem;
        background-color: var(--arco-light-blue);
        border-radius: 8px;
        color: var(--arco-blue);
        border: 1px solid #b3e5fc;
    }
    
    /* Sliders personalizados */
    .stSlider > div > div > div > div {
        background-color: var(--arco-blue);
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO GERADORA DE WORD (.DOCX) ---
def gerar_docx_completo(dados):
    doc = Document()
    
    # Cabeçalho do Documento
    titulo = doc.add_heading('PLANO DE ENSINO INDIVIDUALIZADO (PEI)', 0)
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f'Instituição: {dados["escola"]} | Ano Letivo: {date.today().year}').alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph('_' * 70)

    # 1. Identificação
    doc.add_heading('1. DADOS DE IDENTIFICAÇÃO', level=1)
    
    tbl = doc.add_table(rows=1, cols=2)
    tbl.autofit = False 
    celulas = tbl.rows[0].cells
    celulas[0].text = f"Nome: {dados['nome']}\nNascimento: {str(dados['nasc']) if dados['nasc'] else '--'}"
    celulas[1].text = f"Série: {dados['serie']}\nSuporte Geral: {dados['nivel_suporte']}"
    
    doc.add_paragraph(f"\nDiagnóstico/Hipótese: {dados['cid']}")
    doc.add_paragraph(f"Equipe Externa: {', '.join(dados['equipe_externa']) if dados['equipe_externa'] else 'Não possui.'}")

    # 2. Perfil (Com os novos indicadores)
    doc.add_heading('2. PERFIL DO ESTUDANTE (ESTUDO DE CASO)', level=1)
    
    doc.add_paragraph(f"Nível de Engajamento Escolar: {dados['nivel_engajamento']}")
    doc.add_paragraph(f"Nível de Autonomia (AVDs): {dados['nivel_autonomia']}")

    doc.add_heading('Potencialidades (Alavancas):', level=2)
    if dados['potencias']:
        for p in dados['potencias']: doc.add_paragraph(p, style='List Bullet')
    else: doc.add_paragraph("Não informadas.")

    doc.add_heading('Barreiras Identificadas:', level=2)
    
    # Fix do Negrito
    if dados['b_sensorial']: 
        p = doc.add_paragraph(); p.add_run("Sensoriais/Físicas:").bold = True
        for b in dados['b_sensorial']: doc.add_paragraph(b, style='List Bullet')
    
    if dados['b_cognitiva']: 
        p = doc.add_paragraph(); p.add_run("Cognitivas/Aprendizagem:").bold = True
        for b in dados['b_cognitiva']: doc.add_paragraph(b, style='List Bullet')
        
    if dados['b_social']: 
        p = doc.add_paragraph(); p.add_run("Sociais/Comportamentais:").bold = True
        for b in dados['b_social']: doc.add_paragraph(b, style='List Bullet')

    # 3. Plano
    doc.add_heading('3. PLANO DE AÇÃO PEDAGÓGICA', level=1)
    
    doc.add_heading('Adaptações de Acesso:', level=2)
    if dados['estrategias_acesso']:
        for e in dados['estrategias_acesso']: doc.add_paragraph(e, style='List Bullet')
        
    doc.add_heading('Adaptações Curriculares:', level=2)
    if dados['estrategias_curriculo']:
        for e in dados['estrategias_curriculo']: doc.add_paragraph(e, style='List Bullet')

    # 4. Assinaturas
    doc.add_paragraph('\n\n___________________________________\nAssinatura da Coordenação')
    doc.add_paragraph('\n___________________________________\nAssinatura da Família/Responsável')
    
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Arco_Educa%C3%A7%C3%A3o_logo.png/640px-Arco_Educa%C3%A7%C3%A3o_logo.png", width=180)
    st.markdown("### PEI 360°")
    st.caption("v.Platinum 3.0")
    st.success("✅ Sistema Online")
    st.markdown("---")
    st.info("**Dica:** Use as barras deslizantes para refinar o perfil do aluno com precisão.")

# --- CABEÇALHO PRINCIPAL ---
st.title("Gestão de PEI e Inclusão Escolar")
st.markdown("**Compliance:** Decreto nº 12.773/2025 | **Foco:** Pedagógico & Legal")

# --- MENU DE NAVEGAÇÃO (TABS) ---
tab_educ, tab_aluno, tab_mapa, tab_plano, tab_doc = st.tabs([
    "📘 O que é & Lei", 
    "📝 Aluno & Contexto", 
    "🔍 Mapeamento", 
    "🛠️ Estratégias", 
    "🖨️ Documento"
])

# --- DICIONÁRIO DE DADOS ---
if 'dados' not in st.session_state:
    st.session_state.dados = {
        'nome': '', 'nasc': None, 'serie': '', 'escola': '', 'cid': '',
        'equipe_externa': [], 
        'nivel_suporte': 'Nível 1: Leve',
        'nivel_engajamento': 'Médio', # Novo
        'nivel_autonomia': 'Com Supervisão', # Novo
        'potencias': [], 'b_sensorial': [], 'b_cognitiva': [], 'b_social': [],
        'estrategias_acesso': [], 'estrategias_curriculo': []
    }

# === ABA 1: EDUCATIVA (O QUE É & LEI) ===
with tab_educ:
    col_e1, col_e2 = st.columns(2)
    
    with col_e1:
        st.markdown("""
        <div class="info-card">
        <h3>📘 O que é o PEI?</h3>
        <p>O <b>Plano de Ensino Individualizado</b> é o documento que traduz a inclusão em prática. 
        Ele não é um laudo médico; é um plano de ação da escola.</p>
        <p><b>Para que serve?</b></p>
        <ul>
            <li>Eliminar barreiras de acesso.</li>
            <li>Registrar adaptações curriculares.</li>
            <li>Proteger a escola juridicamente.</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        
    with col_e2:
        st.markdown("""
        <div class="info-card">
        <h3>⚖️ Legislação 2025</h3>
        <p><b>Decreto nº 12.773 (Dez/2025):</b></p>
        <div class="lei-card">
        "Art. 12. As instituições devem elaborar plano individualizado..."<br>
        "§ 2º As medidas de apoio independem de laudo médico."
        </div>
        <p><br>Isso significa que o <b>Estudo de Caso</b> pedagógico (que você fará aqui) tem valor legal imediato.</p>
        </div>
        """, unsafe_allow_html=True)

# === ABA 2: IDENTIFICAÇÃO ===
with tab_aluno:
    st.subheader("Dados Cadastrais")
    c1, c2 = st.columns(2)
    with c1:
        st.session_state.dados['nome'] = st.text_input("Nome do Estudante", value=st.session_state.dados['nome'])
        st.session_state.dados['nasc'] = st.date_input("Data de Nascimento")
        st.session_state.dados['escola'] = st.text_input("Unidade Escolar", value=st.session_state.dados['escola'])
    with c2:
        st.session_state.dados['serie'] = st.selectbox("Série", ["Ed. Infantil", "Fund I (1º-5º)", "Fund II (6º-9º)", "Ensino Médio"])
        st.session_state.dados['cid'] = st.text_input("Diagnóstico/Hipótese")
        st.session_state.dados['equipe_externa'] = st.multiselect("Apoio Externo:", ["Psicólogo", "Fonoaudiólogo", "TO", "Neuro", "Psiquiatra"])

    st.markdown("---")
    st.subheader("🌡️ Termômetro de Suporte (Geral)")
    # A BARRA QUE VOCÊ GOSTOU
    st.session_state.dados['nivel_suporte'] = st.select_slider(
        "Qual o nível de suporte geral que o aluno demanda hoje?",
        options=["Nível 1: Leve (Apenas adaptações)", "Nível 2: Moderado (Monitoria)", "Nível 3: Elevado (Suporte Contínuo/AT)"],
        value="Nível 1: Leve (Apenas adaptações)"
    )

# === ABA 3: MAPEAMENTO ===
with tab_mapa:
    st.markdown('<div class="lei-card">💡 Dica: Mapeie primeiro as potências para usar como "gancho" nas intervenções.</div>', unsafe_allow_html=True)
    
    col_pot, col_bar = st.columns([1, 1])

    with col_pot:
        st.markdown("### 🌟 Potencialidades")
        st.session_state.dados['potencias'] = st.multiselect("Pontos Fortes:", 
            ["Memória Visual", "Tecnologia", "Artes/Desenho", "Oralidade", "Lógica", "Música", "Esportes", "Vínculo Afetivo"])
        
        # NOVA BARRA 1: Engajamento
        st.write("")
        st.session_state.dados['nivel_engajamento'] = st.select_slider(
            "Nível de Engajamento Escolar:",
            options=["Baixo (Passivo)", "Médio (Requer estímulo)", "Alto (Participativo)", "Hiperfocado"],
            value="Médio (Requer estímulo)"
        )

    with col_bar:
        st.markdown("### 🚧 Barreiras")
        with st.expander("Sensorial e Físico", expanded=True):
            st.session_state.dados['b_sensorial'] = st.multiselect("Selecione:", ["Hipersensibilidade Auditiva", "Agitação Motora", "Baixa Visão/Audição", "Coordenação Motora"])
        with st.expander("Cognitivo e Acadêmico"):
            st.session_state.dados['b_cognitiva'] = st.multiselect("Selecione:", ["Atenção Curta", "Não copia do quadro", "Dificuldade Leitura", "Rigidez Cognitiva"])
        with st.expander("Social e Comportamental"):
            st.session_state.dados['b_social'] = st.multiselect("Selecione:", ["Isolamento", "Comportamento Opositor", "Pouca comunicação verbal", "Ecolalia"])
            
        # NOVA BARRA 2: Autonomia
        st.write("")
        st.session_state.dados['nivel_autonomia'] = st.select_slider(
            "Nível de Autonomia (Rotina/AVDs):",
            options=["Dependente (Total)", "Com Supervisão Constante", "Com Supervisão Parcial", "Autônomo"],
            value="Com Supervisão Parcial"
        )

# === ABA 4: ESTRATÉGIAS ===
with tab_plano:
    st.subheader("Plano de Ação")
    
    # Lógica Automática (Simplificada para brevidade)
    sugestoes_acesso = []
    if "Hipersensibilidade Auditiva" in st.session_state.dados['b_sensorial']: sugestoes_acesso.append("Uso de abafadores de ruído")
    if "Não copia do quadro" in st.session_state.dados['b_cognitiva']: sugestoes_acesso.append("Fornecer pauta impressa/Foto da lousa")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Adaptações de Acesso** (Ambiente/Recurso)")
        st.session_state.dados['estrategias_acesso'] = st.multiselect("Definir:", 
            options=sugestoes_acesso + ["Tempo Estendido", "Ledor/Escriba", "Material Ampliado", "Sentar na frente"],
            default=sugestoes_acesso)
    with c2:
        st.markdown("**Adaptações Curriculares** (Conteúdo/Avaliação)")
        st.session_state.dados['estrategias_curriculo'] = st.multiselect("Definir:", 
            ["Redução de questões", "Avaliação Oral", "Foco no conteúdo essencial", "Atividade prática em vez de escrita"])

# === ABA 5: DOCUMENTO ===
with tab_doc:
    st.markdown("### 📄 Exportação Oficial")
    
    if not st.session_state.dados['nome']:
        st.warning("⚠️ Preencha o Nome do Aluno na aba 'Aluno & Contexto'.")
    else:
        st.success("Documento pronto para emissão.")
        doc_buffer = gerar_docx_completo(st.session_state.dados)
        
        col_d1, col_d2 = st.columns([3, 1])
        with col_d1:
            st.info(f"O arquivo gerado é um **Documento Word Editável (.docx)**, pronto para receber o timbre da escola e assinaturas.")
        with col_d2:
            st.download_button(
                label="📥 Baixar PEI (.docx)",
                data=doc_buffer,
                file_name=f"PEI_{st.session_state.dados['nome'].strip()}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

