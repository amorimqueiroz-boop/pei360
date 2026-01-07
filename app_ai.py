import streamlit as st
from datetime import date
from io import BytesIO
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from openai import OpenAI
from pypdf import PdfReader
from fpdf import FPDF
import re
import base64
import os

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="PEI 360º | Sistema Inclusivo",
    page_icon="🌀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILO VISUAL ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #2D3748; }
    
    :root { --main-blue: #004e92; --bg-light: #F7FAFC; }
    
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        border-radius: 8px !important; border: 1px solid #CBD5E0 !important;
    }
    
    div[data-testid="stFileUploader"] section { 
        background-color: #EBF8FF; border: 2px dashed #004e92; border-radius: 10px;
    }

    .info-card {
        background-color: white; padding: 20px; border-radius: 12px;
        border-left: 5px solid var(--main-blue);
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); height: 100%; margin-bottom: 15px;
    }
    .info-card h4 { color: var(--main-blue); margin-bottom: 8px; font-weight: 700; }
    
    .stButton>button {
        background-color: var(--main-blue); color: white; border-radius: 8px;
        font-weight: 600; height: 3em; width: 100%; border: none; transition: all 0.3s;
    }
    .stButton>button:hover { background-color: #003a6e; transform: scale(1.01); }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE ARQUIVO ---
def encontrar_arquivo_logo():
    """Procura especificamente por 360.png ou variações"""
    possiveis_nomes = ["360.png", "360.jpg", "logo.png", "logo.jpg"]
    for nome in possiveis_nomes:
        if os.path.exists(nome):
            return nome
    return None

def get_base64_image(image_path):
    if not image_path: return ""
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

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

# --- FUNÇÕES DE TEXTO ---
def limpar_markdown(texto):
    if not texto: return ""
    texto = texto.replace('**', '').replace('__', '')
    texto = texto.replace('### ', '').replace('## ', '').replace('# ', '')
    return texto

def limpar_para_pdf(texto):
    if not texto: return ""
    texto = texto.replace('**', '').replace('__', '')
    texto = texto.replace('### ', '').replace('## ', '').replace('# ', '')
    texto = texto.replace('* ', '• ')
    texto = re.sub(r'[^\x00-\x7F\xA0-\xFF]', '', texto) 
    return texto

# --- INTELIGÊNCIA (DEEPSEEK V3 + BNCC) ---
def consultar_ia(api_key, dados, contexto_pdf=""):
    if not api_key: return None, "⚠️ A chave de API não foi detectada."
    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        # Prompt atualizado com BNCC
        prompt_sistema = """
        Você é um Especialista em Inclusão Escolar e Currículo Brasileiro.
        BASES OBRIGATÓRIAS:
        1. LBI (Lei 13.146) - Foco em eliminar barreiras.
        2. Neurociência - Foco em Funções Executivas.
        3. BNCC (Base Nacional Comum Curricular) - Foco em Habilidades Essenciais da série.
        """
        
        contexto_extra = f"\n📄 RESUMO DO LAUDO/ANEXO:\n{contexto_pdf[:3000]}" if contexto_pdf else ""
        
        prompt_usuario = f"""
        Analise este ESTUDANTE:
        Nome: {dados['nome']} | Série: {dados['serie']} | Idade/Nasc: {dados['nasc']}
        Diagnóstico: {dados['diagnostico']}
        Rede de Apoio: {', '.join(dados['rede_apoio'])}
        Hiperfoco: {dados['hiperfoco']}
        
        {contexto_extra}
        
        Barreiras Mapeadas: {', '.join(dados['b_sensorial'] + dados['b_cognitiva'] + dados['b_social'])}
        
        GERE UM PARECER TÉCNICO ESTRUTURADO (Sem Markdown complexo):
        1. 🧠 Conexão Neural: Como usar o Hiperfoco para engajar.
        2. 📘 BNCC em Foco: Cite 1 ou 2 habilidades essenciais da BNCC para o {dados['serie']} que precisam ser flexibilizadas para este estudante.
        3. 🛠️ Estratégias Práticas: Sugestões de adaptação de ambiente e avaliação.
        """
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": prompt_usuario}],
            temperature=0.7, stream=False
        )
        return response.choices[0].message.content, None
    except Exception as e:
        return None, f"Erro DeepSeek: {str(e)}"

# --- GERADOR PDF ---
class PDF(FPDF):
    def header(self):
        arquivo_logo = encontrar_arquivo_logo()
        if arquivo_logo:
            self.image(arquivo_logo, x=10, y=8, w=25)
            x_title = 40
        else:
            x_title = 0
            
        self.set_font('Arial', 'B', 16)
        self.set_text_color(0, 78, 146) 
        self.cell(x_title) 
        self.cell(0, 10, 'PEI - PLANO DE ENSINO INDIVIDUALIZADO', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Página {self.page_no()} | Documento Confidencial', 0, 0, 'C')

def gerar_pdf_nativo(dados):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    def txt(t): return str(t).encode('latin-1', 'replace').decode('latin-1')

    # 1. Identificação
    pdf.set_font("Arial", 'B', 12); pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 10, txt("1. IDENTIFICAÇÃO DO ESTUDANTE"), 0, 1)
    pdf.set_font("Arial", size=11); pdf.set_text_color(0)
    
    # Formata data
    data_nasc = dados['nasc'].strftime('%d/%m/%Y') if dados['nasc'] else "Não informada"
    
    pdf.multi_cell(0, 7, txt(f"Nome: {dados['nome']} | Série: {dados['serie']}\nNascimento: {data_nasc}\nDiagnóstico: {dados['diagnostico']}"))
    
    if dados['rede_apoio']:
        pdf.ln(2)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(0, 8, txt("Rede de Apoio (Saúde/Terapêutica):"), 0, 1)
        pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 7, txt(", ".join(dados['rede_apoio'])))
    
    pdf.ln(3)

    # 2. Mapeamento
    pdf.set_font("Arial", 'B', 12); pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 10, txt("2. MAPEAMENTO PEDAGÓGICO"), 0, 1)
    pdf.set_font("Arial", size=11); pdf.set_text_color(0)
    pdf.multi_cell(0, 7, txt(f"Hiperfoco: {dados['hiperfoco']}"))
    pdf.ln(2)
    
    b_sens = limpar_para_pdf(', '.join(dados['b_sensorial']))
    b_cog = limpar_para_pdf(', '.join(dados['b_cognitiva']))
    b_soc = limpar_para_pdf(', '.join(dados['b_social']))
    
    if b_sens: pdf.multi_cell(0, 6, txt(f"- Sensorial: {b_sens}"))
    if b_cog: pdf.multi_cell(0, 6, txt(f"- Cognitivo: {b_cog}"))
    if b_soc: pdf.multi_cell(0, 6, txt(f"- Social: {b_soc}"))
    pdf.ln(3)

    # 3. Estratégias
    pdf.set_font("Arial", 'B', 12); pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 10, txt("3. ESTRATÉGIAS DEFINIDAS"), 0, 1)
    pdf.set_font("Arial", size=11); pdf.set_text_color(0)
    pdf.multi_cell(0, 7, txt("Acesso: " + limpar_para_pdf(', '.join(dados['estrategias_acesso']))))
    pdf.ln(2)
    pdf.multi_cell(0, 7, txt("Currículo: " + limpar_para_pdf(', '.join(dados['estrategias_curriculo']))))
    pdf.ln(3)

    # 4. Parecer IA
    if dados['ia_sugestao']:
        texto_limpo = limpar_para_pdf(dados['ia_sugestao'])
        pdf.set_font("Arial", 'B', 12); pdf.set_text_color(0, 78, 146)
        pdf.cell(0, 10, txt("4. PARECER DO ESPECIALISTA & BNCC"), 0, 1)
        pdf.set_font("Arial", size=11); pdf.set_text_color(50)
        pdf.multi_cell(0, 6, txt(texto_limpo))

    pdf.ln(15)
    pdf.set_draw_color(0); pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.cell(0, 10, txt("Coordenação Pedagógica / Direção Escolar"), 0, 1, 'C')
    return pdf.output(dest='S').encode('latin-1')

# --- GERADOR DOCX ---
def gerar_docx_final(dados):
    doc = Document()
    style = doc.styles['Normal']; style.font.name = 'Arial'; style.font.size = Pt(11)
    doc.add_heading('PEI - PLANO DE ENSINO INDIVIDUALIZADO', 0).alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Nome: {dados['nome']} | Série: {dados['serie']}")
    doc.add_paragraph(f"Nascimento: {dados['nasc']} | Diagnóstico: {dados['diagnostico']}")
    if dados['rede_apoio']: doc.add_paragraph(f"Rede de Apoio: {', '.join(dados['rede_apoio'])}")
    
    if dados['ia_sugestao']:
        doc.add_heading('PARECER TÉCNICO', level=1)
        doc.add_paragraph(limpar_markdown(dados['ia_sugestao']))
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# --- ESTADO INICIAL ---
if 'dados' not in st.session_state:
    st.session_state.dados = {
        'nome': '', 'nasc': None, 'serie': None, 'escola': '', 'tem_laudo': False, 'diagnostico': '', 
        'rede_apoio': [], # Novo campo
        'historico': '', 'familia': '', 'hiperfoco': '', 'potencias': [], 
        'b_sensorial': [], 'sup_sensorial': '🟡 Monitorado',
        'b_cognitiva': [], 'sup_cognitiva': '🟡 Monitorado',
        'b_social': [], 'sup_social': '🟡 Monitorado',
        'estrategias_acesso': [], 'estrategias_curriculo': [], 'ia_sugestao': ''
    }
if 'pdf_text' not in st.session_state: st.session_state.pdf_text = ""

# --- SIDEBAR ---
with st.sidebar:
    arquivo_logo = encontrar_arquivo_logo()
    if arquivo_logo: st.image(arquivo_logo, width=120)
    
    if 'DEEPSEEK_API_KEY' in st.secrets:
        api_key = st.secrets['DEEPSEEK_API_KEY']
        st.success("✅ Chave Segura Ativa")
    else:
        api_key = st.text_input("Chave API DeepSeek:", type="password")
    
    st.markdown("---")
    st.info("Versão 8.0 | BNCC Integrated")

# --- CABEÇALHO ---
arquivo_logo = encontrar_arquivo_logo()
logo_html = ""
if arquivo_logo:
    mime = "image/png" if arquivo_logo.lower().endswith("png") else "image/jpeg"
    b64 = get_base64_image(arquivo_logo)
    if b64: logo_html = f'<img src="data:{mime};base64,{b64}" style="height: 60px; margin-right: 15px; border-radius: 8px;">'

if not logo_html: logo_html = '<span style="font-size: 3rem; margin-right: 15px;">🌀</span>'

st.markdown(f"""
<div style="display: flex; align-items: center; padding: 20px; background: linear-gradient(90deg, #FFFFFF 0%, #E3F2FD 100%); border-radius: 15px; border-left: 6px solid #004E92; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 25px;">
    {logo_html}
    <div>
        <h1 style="color: #004E92; margin: 0; font-weight: 800; font-size: 2.2rem; letter-spacing: -1px; line-height: 1;">PEI 360º</h1>
        <p style="margin: 5px 0 0 0; color: #4A5568; font-weight: 500; font-size: 1rem;">
            Planejamento Educacional Individualizado
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

abas = ["🏠 Início", "👤 Estudante", "🔍 Mapeamento", "✅ Plano de Ação", "🤖 Assistente de IA", "🖨️ Documento"]
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(abas)

# 1. HOME
with tab1:
    st.markdown("### Bem-vindo ao PEI 360º")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="info-card"><h4>📘 O que é o PEI?</h4><p>Ferramenta oficial para eliminar barreiras e transformar a matrícula em inclusão real.</p></div>', unsafe_allow_html=True)
        st.markdown('<div class="info-card"><h4>🇧🇷 Conexão BNCC</h4><p>Nossa IA cruza o perfil do estudante com as Habilidades Essenciais da Base Nacional Comum Curricular.</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="info-card"><h4>🧠 Neurociência</h4><p>Foco nas Funções Executivas. Entendemos como o cérebro aprende para propor o método certo.</p></div>', unsafe_allow_html=True)

# 2. ESTUDANTE
with tab2:
    st.info("Dados do Estudante e Documentação.")
    c1, c2, c3 = st.columns([2, 1, 1])
    st.session_state.dados['nome'] = c1.text_input("Nome do Estudante", st.session_state.dados['nome'])
    st.session_state.dados['nasc'] = c2.date_input("Data de Nascimento", st.session_state.dados['nasc'])
    st.session_state.dados['serie'] = c3.selectbox("Série/Ano", ["Ed. Infantil", "1º Ano", "2º Ano", "3º Ano", "4º Ano", "5º Ano", "6º Ano", "7º Ano", "8º Ano", "9º Ano", "Ensino Médio"], index=None)
    
    st.markdown("---")
    c_diag, c_rede = st.columns(2)
    st.session_state.dados['diagnostico'] = c_diag.text_input("Diagnóstico Clínico", st.session_state.dados['diagnostico'])
    st.session_state.dados['rede_apoio'] = c_rede.multiselect("Rede de Apoio (Especialistas):", 
        ["Psicólogo", "Fonoaudiólogo", "Neuropediatra", "Terapeuta Ocupacional (TO)", "Psicopedagogo", "Psiquiatra", "Acompanhante Terapêutico (AT)"])
    
    st.write("")
    st.markdown("##### 📂 Anexar Laudo Anterior (PDF)")
    uploaded_file = st.file_uploader("Arraste o arquivo aqui para a IA ler", type="pdf", key="uploader_tab2")
    if uploaded_file is not None:
        texto = ler_pdf(uploaded_file)
        if texto: st.session_state.pdf_text = texto; st.success("✅ Documento Lido!")

    st.markdown("---")
    ch, cf = st.columns(2)
    st.session_state.dados['historico'] = ch.text_area("Histórico Escolar", st.session_state.dados['historico'])
    st.session_state.dados['familia'] = cf.text_area("Escuta da Família", st.session_state.dados['familia'])

# 3. MAPEAMENTO
with tab3:
    st.markdown("### 🚀 Potencialidades")
    c_pot1, c_pot2 = st.columns(2)
    st.session_state.dados['hiperfoco'] = c_pot1.text_input("Hiperfoco (Interesse)")
    st.session_state.dados['potencias'] = c_pot2.multiselect("Pontos Fortes", ["Memória Visual", "Tecnologia", "Artes", "Oralidade", "Lógica", "Empatia"])
    
    st.markdown("### 🚧 Barreiras")
    with st.expander("👁️ Sensorial e Físico", expanded=True):
        st.session_state.dados['b_sensorial'] = st.multiselect("Barreiras:", ["Hipersensibilidade", "Busca Sensorial", "Seletividade", "Motora"], key="b_sens")
        st.session_state.dados['sup_sensorial'] = st.select_slider("Suporte:", ["🟢 Autônomo", "🟡 Monitorado", "🟠 Substancial", "🔴 Muito Substancial"], value="🟡 Monitorado", key="s_sens")
    with st.expander("🧠 Cognitivo"):
        st.session_state.dados['b_cognitiva'] = st.multiselect("Barreiras:", ["Atenção", "Memória", "Rigidez", "Lentidão", "Abstração"], key="b_cog")
        st.session_state.dados['sup_cognitiva'] = st.select_slider("Suporte:", ["🟢 Autônomo", "🟡 Monitorado", "🟠 Substancial", "🔴 Muito Substancial"], value="🟡 Monitorado", key="s_cog")
    with st.expander("❤️ Social"):
        st.session_state.dados['b_social'] = st.multiselect("Barreiras:", ["Isolamento", "Frustração", "Literalidade", "Ansiedade"], key="b_soc")
        st.session_state.dados['sup_social'] = st.select_slider("Suporte:", ["🟢 Autônomo", "🟡 Monitorado", "🟠 Substancial", "🔴 Muito Substancial"], value="🟡 Monitorado", key="s_soc")

# 4. ESTRATÉGIAS
with tab4:
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Adaptações de Acesso**")
        st.session_state.dados['estrategias_acesso'] = st.multiselect("Recursos:", ["Tempo estendido", "Ledor/Escriba", "Material Ampliado", "Tablet", "Sala Silenciosa", "Pausas"])
    with c2:
        st.markdown("**Adaptações Curriculares**")
        st.session_state.dados['estrategias_curriculo'] = st.multiselect("Estratégias:", ["Menos Questões", "Prova Oral", "Mapa Mental", "Conteúdo Prioritário", "Prática"])

# 5. ASSISTENTE
with tab5:
    col_ia_left, col_ia_right = st.columns([1, 2])
    with col_ia_left:
        st.markdown("### 🤖 Consultor BNCC")
        st.info("Vou cruzar os dados do estudante com as Habilidades Essenciais da BNCC.")
        if st.button("✨ Gerar Parecer"):
            if not st.session_state.dados['nome']: st.warning("Preencha o nome.")
            else:
                with st.spinner("Analisando BNCC e Neurociência..."):
                    res, err = consultar_ia(api_key, st.session_state.dados, st.session_state.pdf_text)
                    if err: st.error(err)
                    else: st.session_state.dados['ia_sugestao'] = res; st.success("Pronto!")
    with col_ia_right:
        st.markdown("### 💡 Parecer")
        if st.session_state.dados['ia_sugestao']:
            st.text_area("Sugestões:", st.session_state.dados['ia_sugestao'], height=500)
        else:
            st.markdown("O parecer aparecerá aqui.")

# 6. DOCUMENTO
with tab6:
    st.markdown("<div style='text-align:center; padding: 30px;'>", unsafe_allow_html=True)
    if st.session_state.dados['nome']:
        c1, c2 = st.columns(2)
        with c1:
            docx = gerar_docx_final(st.session_state.dados)
            st.download_button("📥 Baixar Word (.docx)", docx, f"PEI_{st.session_state.dados['nome']}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        with c2:
            pdf = gerar_pdf_nativo(st.session_state.dados)
            st.download_button("📄 Baixar PDF Oficial", pdf, f"PEI_{st.session_state.dados['nome']}.pdf", "application/pdf")
    else:
        st.warning("Preencha o nome do estudante.")
    st.markdown("</div>", unsafe_allow_html=True)