import streamlit as st
from datetime import date
from io import BytesIO
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from openai import OpenAI
from pypdf import PdfReader
from fpdf import FPDF

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="PEI 360º | Arco Hub",
    page_icon="💙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILO VISUAL (DESIGN SYSTEM ARCO) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #2D3748; }
    
    :root { --arco-blue: #004e92; --arco-light: #E3F2FD; }
    
    /* Inputs refinados */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        border-radius: 8px !important; border: 1px solid #CBD5E0 !important;
    }
    
    /* Upload Area */
    div[data-testid="stFileUploader"] section { background-color: #F7FAFC; border: 1px dashed #A0AEC0; }

    /* Cards Informativos */
    .info-card {
        background-color: white; padding: 20px; border-radius: 12px;
        border-left: 5px solid var(--arco-blue);
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); height: 100%; margin-bottom: 15px;
    }
    .info-card h4 { color: var(--arco-blue); margin-bottom: 8px; font-weight: 700; }
    .info-card p { font-size: 0.9rem; color: #4A5568; line-height: 1.4; }
    
    /* Botões */
    .stButton>button {
        background-color: var(--arco-blue); color: white; border-radius: 8px;
        font-weight: 600; height: 3em; width: 100%; border: none; transition: all 0.3s;
    }
    .stButton>button:hover { background-color: #003a6e; transform: scale(1.01); }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÃO DE LEITURA DE PDF ---
def ler_pdf(arquivo):
    if arquivo is None: return ""
    try:
        reader = PdfReader(arquivo)
        texto = ""
        for page in reader.pages:
            texto += page.extract_text() + "\n"
        return texto
    except Exception as e:
        return f"Erro ao ler PDF: {e}"

# --- FUNÇÃO INTEELIGÊNCIA (DEEPSEEK V3) ---
def consultar_ia(api_key, dados, contexto_pdf=""):
    if not api_key: return None, "⚠️ A chave de API não foi detectada."
    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        prompt_sistema = """
        Você é um Assistente Pedagógico Especialista em Inclusão Escolar (PEI) da rede COC/Arco.
        
        CALIBRAGEM:
        - Temperatura: 0.7.
        - Base: LBI 13.146 + Neurociência (Funções Executivas).
        - Contexto Extra: Se houver texto de laudo anexado, use-o para refinar as sugestões.
        """
        
        contexto_extra = f"\n📄 CONTEÚDO DO LAUDO/RELATÓRIO ANEXADO:\n{contexto_pdf}" if contexto_pdf else ""
        
        prompt_usuario = f"""
        Analise este aluno e o documento anexo (se houver) para gerar estratégias:
        
        👤 ALUNO: {dados['nome']} ({dados['serie']})
        🏥 DIAGNÓSTICO: {dados['diagnostico']}
        🚀 HIPERFOCO: {dados['hiperfoco']}
        
        {contexto_extra}
        
        📊 BARREIRAS & SUPORTE:
        - Sensorial: {', '.join(dados['b_sensorial'])} ({dados['sup_sensorial']})
        - Cognitivo: {', '.join(dados['b_cognitiva'])} ({dados['sup_cognitiva']})
        - Social: {', '.join(dados['b_social'])} ({dados['sup_social']})
        
        📝 ESTRATÉGIAS DA ESCOLA:
        - Acesso: {', '.join(dados['estrategias_acesso'])}
        - Currículo: {', '.join(dados['estrategias_curriculo'])}
        
        GERAR PARECER TÉCNICO:
        1. 🧠 Conexão Neural (Uso do Hiperfoco).
        2. 🛠️ Análise do Laudo/Contexto (Se houver laudo, cite pontos de atenção).
        3. 🎓 Sugestões Práticas de Adaptação (Ambiente e Provas).
        """
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": prompt_usuario}],
            temperature=0.7, stream=False
        )
        return response.choices[0].message.content, None
    except Exception as e:
        return None, f"Erro DeepSeek: {str(e)}"

# --- GERADOR PDF (NATIVO) ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.set_text_color(0, 78, 146) # Arco Blue
        self.cell(0, 10, 'PEI 360 - PLANO DE ENSINO INDIVIDUALIZADO', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

def gerar_pdf_nativo(dados):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    
    def txt(t): return str(t).encode('latin-1', 'replace').decode('latin-1')

    # 1. Identificação
    pdf.set_font("Arial", 'B', 12); pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 10, txt("1. IDENTIFICAÇÃO DO ESTUDANTE"), 0, 1)
    pdf.set_font("Arial", size=11); pdf.set_text_color(0)
    pdf.multi_cell(0, 7, txt(f"Nome: {dados['nome']} | Série: {dados['serie']}\nDiagnóstico: {dados['diagnostico']}"))
    pdf.ln(3)

    # 2. Histórico e Família
    if dados['historico'] or dados['familia']:
        pdf.set_font("Arial", 'B', 12); pdf.set_text_color(0, 78, 146)
        pdf.cell(0, 10, txt("2. CONTEXTO E HISTÓRICO"), 0, 1)
        pdf.set_font("Arial", size=11); pdf.set_text_color(0)
        if dados['historico']: pdf.multi_cell(0, 7, txt(f"Histórico Escolar: {dados['historico']}"))
        if dados['familia']: pdf.multi_cell(0, 7, txt(f"Relato da Família: {dados['familia']}"))
        pdf.ln(3)

    # 3. Mapeamento
    pdf.set_font("Arial", 'B', 12); pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 10, txt("3. MAPEAMENTO PEDAGÓGICO"), 0, 1)
    pdf.set_font("Arial", size=11); pdf.set_text_color(0)
    pdf.multi_cell(0, 7, txt(f"Hiperfoco: {dados['hiperfoco']}"))
    
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, txt("Barreiras Identificadas:"), 0, 1)
    pdf.set_font("Arial", size=10)
    if dados['b_sensorial']: pdf.multi_cell(0, 6, txt(f"- Sensorial ({dados['sup_sensorial']}): {', '.join(dados['b_sensorial'])}"))
    if dados['b_cognitiva']: pdf.multi_cell(0, 6, txt(f"- Cognitivo ({dados['sup_cognitiva']}): {', '.join(dados['b_cognitiva'])}"))
    if dados['b_social']: pdf.multi_cell(0, 6, txt(f"- Social ({dados['sup_social']}): {', '.join(dados['b_social'])}"))
    pdf.ln(3)

    # 4. Estratégias
    pdf.set_font("Arial", 'B', 12); pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 10, txt("4. PLANO DE AÇÃO"), 0, 1)
    pdf.set_font("Arial", size=11); pdf.set_text_color(0)
    pdf.multi_cell(0, 7, txt("Adaptações de Acesso: " + ', '.join(dados['estrategias_acesso'])))
    pdf.ln(2)
    pdf.multi_cell(0, 7, txt("Adaptações Curriculares: " + ', '.join(dados['estrategias_curriculo'])))
    pdf.ln(3)

    # 5. Parecer IA
    if dados['ia_sugestao']:
        pdf.set_font("Arial", 'B', 12); pdf.set_text_color(0, 78, 146)
        pdf.cell(0, 10, txt("5. PARECER DO ESPECIALISTA"), 0, 1)
        pdf.set_font("Arial", size=10); pdf.set_text_color(50)
        pdf.multi_cell(0, 6, txt(dados['ia_sugestao']))

    pdf.ln(15)
    pdf.set_draw_color(0); pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.cell(0, 10, txt("Coordenação Pedagógica / Atendimento Educacional Especializado"), 0, 1, 'C')

    return pdf.output(dest='S').encode('latin-1')

# --- GERADOR DOCX ---
def gerar_docx_final(dados):
    doc = Document()
    style = doc.styles['Normal']; style.font.name = 'Arial'; style.font.size = Pt(11)
    titulo = doc.add_heading('PEI - PLANO DE ENSINO INDIVIDUALIZADO', 0)
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f'Ano: {date.today().year}').alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph('_' * 70)
    
    doc.add_heading('1. IDENTIFICAÇÃO', level=1)
    doc.add_paragraph(f"Nome: {dados['nome']} | Série: {dados['serie']}")
    doc.add_paragraph(f"Diagnóstico: {dados['diagnostico']}")
    if dados['historico']: doc.add_paragraph(f"Histórico: {dados['historico']}")
    if dados['familia']: doc.add_paragraph(f"Família: {dados['familia']}")
    
    doc.add_heading('2. MAPEAMENTO', level=1)
    doc.add_paragraph(f"Hiperfoco: {dados['hiperfoco']}")
    doc.add_heading('Barreiras:', level=2)
    if dados['b_sensorial']: doc.add_paragraph(f"Sensorial: {', '.join(dados['b_sensorial'])}")
    if dados['b_cognitiva']: doc.add_paragraph(f"Cognitivo: {', '.join(dados['b_cognitiva'])}")
    if dados['b_social']: doc.add_paragraph(f"Social: {', '.join(dados['b_social'])}")

    doc.add_heading('3. ESTRATÉGIAS', level=1)
    doc.add_paragraph("Acesso: " + ', '.join(dados['estrategias_acesso']))
    doc.add_paragraph("Currículo: " + ', '.join(dados['estrategias_curriculo']))

    if dados['ia_sugestao']:
        doc.add_heading('4. CONSULTORIA (IA)', level=1)
        doc.add_paragraph(dados['ia_sugestao'])
    
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- ESTADO INICIAL ---
if 'dados' not in st.session_state:
    st.session_state.dados = {
        'nome': '', 'serie': None, 'escola': '', 'tem_laudo': False, 'diagnostico': '', 
        'historico': '', 'familia': '', 'hiperfoco': '', 'potencias': [], 
        'b_sensorial': [], 'sup_sensorial': '🟡 Monitorado',
        'b_cognitiva': [], 'sup_cognitiva': '🟡 Monitorado',
        'b_social': [], 'sup_social': '🟡 Monitorado',
        'estrategias_acesso': [], 'estrategias_curriculo': [], 'ia_sugestao': ''
    }
if 'pdf_text' not in st.session_state: st.session_state.pdf_text = ""

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Arco_Educa%C3%A7%C3%A3o_logo.png/640px-Arco_Educa%C3%A7%C3%A3o_logo.png", width=140)
    if 'DEEPSEEK_API_KEY' in st.secrets:
        api_key = st.secrets['DEEPSEEK_API_KEY']
        st.success("✅ Chave Segura Ativada")
    else:
        api_key = st.text_input("Chave API DeepSeek:", type="password")
    
    st.markdown("---")
    st.markdown("### 📂 Leitor de Laudos")
    uploaded_file = st.file_uploader("Arraste um PDF aqui (Laudo/Relatório)", type="pdf")
    if uploaded_file is not None:
        texto_extraido = ler_pdf(uploaded_file)
        if texto_extraido:
            st.session_state.pdf_text = texto_extraido
            st.success("✅ PDF Lido! Contexto ativado.")
        else:
            st.warning("Não foi possível ler o PDF.")

    st.markdown("---")
    st.info("Versão 7.1 | Titanium Polished")

# --- APP ---
st.markdown("## PEI 360º <span style='font-size:0.6em; background:#E3F2FD; color:#004E92; padding:5px 12px; border-radius:15px; font-weight:600;'>TITANIUM</span>", unsafe_allow_html=True)

abas = ["🏠 Início", "👤 Aluno", "🔍 Mapeamento", "✅ Plano de Ação", "🤖 Assistente de IA", "🖨️ Documento"]
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(abas)

# 1. HOME
with tab1:
    st.markdown("### Bem-vindo ao Sistema de Inclusão Inteligente")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="info-card"><h4>📘 O que é o PEI?</h4><p>O Plano de Ensino Individualizado é a ferramenta oficial para eliminar barreiras. Ele transforma a matrícula em inclusão real.</p></div>', unsafe_allow_html=True)
        st.markdown('<div class="info-card"><h4>⚖️ Legislação (LBI)</h4><p>Baseado na Lei 13.146 e Decreto 10.502. O sistema garante que as adaptações razoáveis sejam registradas.</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="info-card"><h4>🧠 Neurociência</h4><p>Foco nas Funções Executivas. Entendemos como o cérebro do aluno aprende para propor o método certo.</p></div>', unsafe_allow_html=True)
        st.markdown('<div class="info-card"><h4>🤝 Escola & Família</h4><p>A colaboração é vital. Utilize os dados da escuta familiar para alinhar expectativas e criar vínculo.</p></div>', unsafe_allow_html=True)

# 2. ALUNO
with tab2:
    st.info("Preencha os dados básicos para iniciar o dossiê do estudante.")
    c1, c2 = st.columns(2)
    st.session_state.dados['nome'] = c1.text_input("Nome do Estudante", st.session_state.dados['nome'], placeholder="Digite o nome completo")
    st.session_state.dados['serie'] = c2.selectbox("Série/Ano", ["Ed. Infantil", "1º Ano", "2º Ano", "3º Ano", "4º Ano", "5º Ano", "6º Ano", "7º Ano", "8º Ano", "9º Ano", "Ensino Médio"], index=None, placeholder="Selecione a série...")
    
    st.markdown("---")
    c3, c4 = st.columns([1, 2])
    st.session_state.dados['tem_laudo'] = c3.checkbox("Possui Laudo Médico?")
    st.session_state.dados['diagnostico'] = c4.text_input("Diagnóstico ou Hipótese", st.session_state.dados['diagnostico'], placeholder="Ex: TEA, TDAH, Dislexia (Se houver)")
    
    st.markdown("---")
    st.markdown("#### 📝 Contexto Completo")
    ch, cf = st.columns(2)
    st.session_state.dados['historico'] = ch.text_area("Histórico Escolar", st.session_state.dados['historico'], placeholder="Escolas anteriores, repetências...", help="Descreva a trajetória escolar.")
    st.session_state.dados['familia'] = cf.text_area("Escuta da Família", st.session_state.dados['familia'], placeholder="Relato dos pais, rotina...", help="Expectativas da família.")

# 3. MAPEAMENTO
with tab3:
    st.info("💡 Identifique as potências para superar as barreiras.")
    st.markdown("### 🚀 Potencialidades")
    c_pot1, c_pot2 = st.columns(2)
    st.session_state.dados['hiperfoco'] = c_pot1.text_input("Hiperfoco (Interesse)", placeholder="O que o aluno AMA?", help="Alavanca de engajamento.")
    st.session_state.dados['potencias'] = c_pot2.multiselect("Pontos Fortes", ["Memória Visual", "Tecnologia", "Artes/Desenho", "Oralidade", "Lógica", "Empatia"], placeholder="Selecione as habilidades...")
    
    st.markdown("---")
    st.markdown("### 🚧 Barreiras e Nível de Suporte")
    
    with st.expander("👁️ Sensorial e Físico", expanded=True):
        st.session_state.dados['b_sensorial'] = st.multiselect("Quais são as barreiras?", ["Hipersensibilidade", "Busca Sensorial", "Seletividade Alimentar", "Dificuldade Motora"], placeholder="Selecione...")
        st.session_state.dados['sup_sensorial'] = st.select_slider("Suporte Sensorial:", ["🟢 Autônomo", "🟡 Monitorado", "🟠 Substancial", "🔴 Muito Substancial"], value="🟡 Monitorado")

    with st.expander("🧠 Cognitivo e Aprendizagem"):
        st.session_state.dados['b_cognitiva'] = st.multiselect("Quais são as barreiras?", ["Atenção Dispersa", "Memória Curta", "Rigidez", "Lentidão", "Abstração"], placeholder="Selecione...")
        st.session_state.dados['sup_cognitiva'] = st.select_slider("Suporte Cognitivo:", ["🟢 Autônomo", "🟡 Monitorado", "🟠 Substancial", "🔴 Muito Substancial"], value="🟡 Monitorado")

    with st.expander("❤️ Social e Emocional"):
        st.session_state.dados['b_social'] = st.multiselect("Quais são as barreiras?", ["Isolamento", "Baixa Frustração", "Interpretação Literal", "Ansiedade"], placeholder="Selecione...")
        st.session_state.dados['sup_social'] = st.select_slider("Suporte Social:", ["🟢 Autônomo", "🟡 Monitorado", "🟠 Substancial", "🔴 Muito Substancial"], value="🟡 Monitorado")

# 4. PLANO DE AÇÃO
with tab4:
    st.markdown("### ✅ Definição de Estratégias")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Adaptações de Acesso (Meio)**")
        st.session_state.dados['estrategias_acesso'] = st.multiselect("Recursos:", ["Tempo estendido", "Ledor/Escriba", "Material Ampliado", "Uso de Tablet", "Local Silencioso", "Pausas Ativas"], placeholder="Selecione...")
    with c2:
        st.markdown("**Adaptações Curriculares (Fim)**")
        st.session_state.dados['estrategias_curriculo'] = st.multiselect("Estratégias:", ["Redução de Questões", "Prova Oral", "Mapa Mental", "Conteúdo Prioritário", "Atividade Prática"], placeholder="Selecione...")

# 5. ASSISTENTE IA (VISUAL POLIDO)
with tab5:
    col_ia_left, col_ia_right = st.columns([1, 2])
    with col_ia_left:
        # Card Amigável (Destaque)
        st.markdown("### 🤖 Olá, Parceiro Pedagógico!")
        st.markdown("""
        <div class="info-card" style="border-left: 5px solid #48BB78;">
        <p>Estou pronto para atuar como seu Consultor Sênior. Vou analisar o mapeamento do aluno, o histórico e o <b>laudo anexado (se houver)</b> para sugerir estratégias baseadas na Neurociência.</p>
        </div>
        """, unsafe_allow_html=True)
        
        status_pdf = "✅ Documento Anexado" if st.session_state.pdf_text else "⚪ Nenhum anexo"
        
        if st.button("✨ Gerar Parecer do Especialista"):
            if not st.session_state.dados['nome']: st.warning("Preencha o nome do aluno.")
            else:
                with st.spinner("Analisando perfil neurofuncional..."):
                    res, err = consultar_ia(api_key, st.session_state.dados, st.session_state.pdf_text)
                    if err: st.error(err)
                    else: st.session_state.dados['ia_sugestao'] = res; st.success("Consultoria realizada!")

        # Área Técnica Discreta (Expander)
        st.write("")
        with st.expander("⚙️ Ver detalhes técnicos da IA"):
            st.markdown(f"""
            <div style="font-size:0.8rem; color:#718096;">
            <b>Modelo:</b> DeepSeek V3 (Reasoning)<br>
            <b>Status do Anexo:</b> {status_pdf}<br>
            <b>Temperatura:</b> 0.7<br>
            <b>Base de Conhecimento:</b> LBI 13.146 + DUA
            </div>
            """, unsafe_allow_html=True)

    with col_ia_right:
        st.markdown("### 💡 Parecer Técnico")
        if st.session_state.dados['ia_sugestao']:
            st.text_area("Sugestões do Assistente:", st.session_state.dados['ia_sugestao'], height=500)
        else:
            st.info("O resultado da análise aparecerá aqui após o processamento.")

# 6. DOCUMENTO
with tab6:
    st.markdown("<div style='text-align:center; padding: 30px;'>", unsafe_allow_html=True)
    if st.session_state.dados['nome']:
        c_doc1, c_doc2 = st.columns(2)
        with c_doc1:
            docx_file = gerar_docx_final(st.session_state.dados)
            st.download_button("📥 Baixar PEI Editável (.docx)", docx_file, f"PEI_{st.session_state.dados['nome']}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        with c_doc2:
            pdf_bytes = gerar_pdf_nativo(st.session_state.dados)
            st.download_button("📄 Baixar PEI Oficial (.pdf)", pdf_bytes, f"PEI_{st.session_state.dados['nome']}.pdf", "application/pdf")
    else:
        st.warning("Preencha os dados do aluno para liberar os downloads.")
    st.markdown("</div>", unsafe_allow_html=True)