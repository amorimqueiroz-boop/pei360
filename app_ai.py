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
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILO VISUAL & ÍCONES (REMIX ICON) ---
st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/remixicon@2.5.0/fonts/remixicon.css" rel="stylesheet">
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #2D3748; }
    :root { --main-blue: #004e92; --bg-light: #F7FAFC; }
    
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        border-radius: 8px !important; border: 1px solid #CBD5E0 !important;
    }
    div[data-testid="stFileUploader"] { padding-top: 0px; }
    div[data-testid="stFileUploader"] section { background-color: #F7FAFC; border: 1px dashed #CBD5E0; border-radius: 8px; }

    .info-card {
        background-color: white; padding: 25px; border-radius: 12px;
        border-left: 5px solid var(--main-blue);
        box-shadow: 0 4px 10px rgba(0,0,0,0.03); height: 100%; margin-bottom: 20px;
    }
    .info-card h4 { color: var(--main-blue); margin-bottom: 12px; font-weight: 700; display: flex; align-items: center; gap: 10px; }
    .info-card i { font-size: 1.2rem; }
    h3 i { color: var(--main-blue); margin-right: 8px; font-weight: normal; }
    
    .stButton>button {
        background-color: var(--main-blue); color: white; border-radius: 8px;
        font-weight: 600; height: 3em; width: 100%; border: none; transition: all 0.3s;
    }
    .stButton>button:hover { background-color: #003a6e; transform: scale(1.01); }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES ---
def encontrar_arquivo_logo():
    possiveis_nomes = ["360.png", "360.jpg", "logo.png", "logo.jpg"]
    for nome in possiveis_nomes:
        if os.path.exists(nome): return nome
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
        for page in reader.pages: texto += page.extract_text() + "\n"
        return texto
    except Exception as e: return f"Erro: {e}"

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

# --- INTELIGÊNCIA (LÓGICA BNCC DINÂMICA) ---
def consultar_ia(api_key, dados, contexto_pdf=""):
    if not api_key: return None, "⚠️ A chave de API não foi detectada."
    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        # LÓGICA DE SÉRIE (INFANTIL vs FUNDAMENTAL)
        serie = dados['serie'] if dados['serie'] else ""
        if "Infantil" in serie:
            termo_bncc = "CAMPOS DE EXPERIÊNCIA e OBJETIVOS DE APRENDIZAGEM (EI)"
            exemplo_bncc = "Ex: EI03EO02 (Agir de maneira independente...)"
        else:
            termo_bncc = "HABILIDADES ESSENCIAIS (EF/EM)"
            exemplo_bncc = f"Ex: Identificar habilidade central do {serie} que precisa de flexibilização."

        prompt_sistema = f"""
        Você é um Especialista em Inclusão Escolar.
        TRIPÉ DE ANÁLISE:
        1. LBI 13.146 (Eliminação de Barreiras).
        2. Neurociência (Funções Executivas).
        3. BNCC: Foco específico em {termo_bncc}.
        """
        
        contexto_extra = f"\n📄 LAUDO ANEXO:\n{contexto_pdf[:3000]}" if contexto_pdf else ""
        nasc_str = str(dados.get('nasc', ''))
        
        prompt_usuario = f"""
        Estudante: {dados['nome']} | Série: {serie} | Nasc: {nasc_str}
        Diag: {dados['diagnostico']} | Hiperfoco: {dados['hiperfoco']}
        {contexto_extra}
        Barreiras: {', '.join(dados['b_sensorial'] + dados['b_cognitiva'] + dados['b_social'])}
        
        GERE UM PARECER TÉCNICO NESTE FORMATO EXATO (Sem Markdown pesado):
        
        1. CONEXÃO NEURAL E HIPERFOCO
        (Explique como usar o interesse do aluno para ativar a atenção).
        
        2. ALVO PEDAGÓGICO - {termo_bncc}
        (Cite 1 ou 2 códigos da BNCC ({exemplo_bncc}) e como flexibilizá-los).
        
        3. ESTRATÉGIAS PRÁTICAS
        (Sugestões de ambiente e avaliação).
        """
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": prompt_usuario}],
            temperature=0.7, stream=False
        )
        return response.choices[0].message.content, None
    except Exception as e: return None, f"Erro DeepSeek: {str(e)}"

# --- GERADOR PDF ---
class PDF(FPDF):
    def header(self):
        arquivo_logo = encontrar_arquivo_logo()
        if arquivo_logo:
            self.image(arquivo_logo, x=10, y=8, w=25)
            x_title = 40
        else: x_title = 0
        self.set_font('Arial', 'B', 16); self.set_text_color(0, 78, 146)
        self.cell(x_title); self.cell(0, 10, 'PEI - PLANO DE ENSINO INDIVIDUALIZADO', 0, 1, 'C'); self.ln(5)
    def footer(self):
        self.set_y(-15); self.set_font('Arial', 'I', 8); self.set_text_color(128)
        self.cell(0, 10, f'Página {self.page_no()} | Confidencial', 0, 0, 'C')

def gerar_pdf_nativo(dados):
    pdf = PDF(); pdf.add_page(); pdf.set_font("Arial", size=11)
    def txt(t): return str(t).encode('latin-1', 'replace').decode('latin-1')

    pdf.set_font("Arial", 'B', 12); pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 10, txt("1. IDENTIFICAÇÃO"), 0, 1)
    pdf.set_font("Arial", size=11); pdf.set_text_color(0)
    
    nasc = dados.get('nasc')
    data_nasc = nasc.strftime('%d/%m/%Y') if nasc else "-"
    rede = dados.get('rede_apoio', [])
    
    pdf.multi_cell(0, 7, txt(f"Nome: {dados['nome']} | Série: {dados['serie']}\nNascimento: {data_nasc}"))
    pdf.ln(2)
    pdf.multi_cell(0, 7, txt(f"Histórico: {dados['historico']}"))
    pdf.ln(3)

    pdf.set_font("Arial", 'B', 12); pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 10, txt("2. CLÍNICO E TERAPÊUTICO"), 0, 1)
    pdf.set_font("Arial", size=11); pdf.set_text_color(0)
    pdf.multi_cell(0, 7, txt(f"Diagnóstico: {dados['diagnostico']}"))
    if rede: pdf.multi_cell(0, 7, txt(f"Rede de Apoio: {', '.join(rede)}"))
    pdf.ln(3)

    pdf.set_font("Arial", 'B', 12); pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 10, txt("3. MAPEAMENTO E ESTRATÉGIAS"), 0, 1)
    pdf.set_font("Arial", size=11); pdf.set_text_color(0)
    pdf.multi_cell(0, 7, txt(f"Hiperfoco: {dados['hiperfoco']}"))
    
    b_total = dados['b_sensorial'] + dados['b_cognitiva'] + dados['b_social']
    if b_total: pdf.multi_cell(0, 7, txt(f"Barreiras: {limpar_para_pdf(', '.join(b_total))}"))
    
    pdf.ln(2)
    pdf.multi_cell(0, 7, txt("Adaptações: " + limpar_para_pdf(', '.join(dados['estrategias_acesso'] + dados['estrategias_curriculo']))))
    pdf.ln(3)

    if dados['ia_sugestao']:
        texto_limpo = limpar_para_pdf(dados['ia_sugestao'])
        pdf.set_font("Arial", 'B', 12); pdf.set_text_color(0, 78, 146)
        
        # Título Dinâmico no PDF também
        titulo_parecer = "4. PARECER (CAMPOS DE EXPERIÊNCIA)" if "Infantil" in str(dados['serie']) else "4. PARECER TÉCNICO (HABILIDADES BNCC)"
        
        pdf.cell(0, 10, txt(titulo_parecer), 0, 1)
        pdf.set_font("Arial", size=11); pdf.set_text_color(50)
        pdf.multi_cell(0, 6, txt(texto_limpo))

    pdf.ln(15); pdf.set_draw_color(0); pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.cell(0, 10, txt("Coordenação Pedagógica"), 0, 1, 'C')
    return pdf.output(dest='S').encode('latin-1')

# --- GERADOR DOCX ---
def gerar_docx_final(dados):
    doc = Document(); style = doc.styles['Normal']; style.font.name = 'Arial'; style.font.size = Pt(11)
    doc.add_heading('PEI - PLANO DE ENSINO INDIVIDUALIZADO', 0).alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph(f"Nome: {dados['nome']} | Série: {dados['serie']}")
    if dados['ia_sugestao']:
        doc.add_heading('PARECER TÉCNICO', level=1)
        doc.add_paragraph(limpar_markdown(dados['ia_sugestao']))
    buffer = BytesIO(); doc.save(buffer); buffer.seek(0)
    return buffer

# --- ESTADO INICIAL ---
if 'dados' not in st.session_state:
    st.session_state.dados = {
        'nome': '', 'nasc': None, 'serie': None, 'escola': '', 'tem_laudo': False, 'diagnostico': '', 
        'rede_apoio': [], 'historico': '', 'familia': '', 'hiperfoco': '', 'potencias': [], 
        'b_sensorial': [], 'sup_sensorial': '🟡 Monitorado',
        'b_cognitiva': [], 'sup_cognitiva': '🟡 Monitorado',
        'b_social': [], 'sup_social': '🟡 Monitorado',
        'estrategias_acesso': [], 'estrategias_curriculo': [], 'ia_sugestao': ''
    }
if 'nasc' not in st.session_state.dados: st.session_state.dados['nasc'] = None
if 'rede_apoio' not in st.session_state.dados: st.session_state.dados['rede_apoio'] = []
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
    st.info("Versão 11.0 | Diamond Edition")

# --- CABEÇALHO ---
arquivo_logo = encontrar_arquivo_logo()
header_html = ""
if arquivo_logo:
    mime = "image/png" if arquivo_logo.lower().endswith("png") else "image/jpeg"
    b64 = get_base64_image(arquivo_logo)
    img_tag = f'<img src="data:{mime};base64,{b64}" style="max-height: 85px; width: auto; margin-right: 20px;">'
    text_div = '<div style="border-left: 2px solid #CBD5E0; padding-left: 20px; height: 60px; display: flex; align-items: center;"><p style="margin: 0; color: #4A5568; font-weight: 500; font-size: 1.1rem;">Planejamento Educacional Individualizado</p></div>'
    header_inner = f'<div style="display: flex; align-items: center; height: 100%;">{img_tag}{text_div}</div>'
else:
    header_inner = '<div style="display: flex; align-items: center;"><i class="ri-global-line" style="font-size: 3.5rem; margin-right: 20px; color: #004E92;"></i><div><h1 style="color: #004E92; margin: 0; font-weight: 800; font-size: 2.5rem; line-height: 1;">PEI 360º</h1><p style="margin: 5px 0 0 0; color: #4A5568;">Sistema de Inclusão</p></div></div>'

st.markdown(f"""
<div style="padding: 15px 25px; background: linear-gradient(90deg, #FFFFFF 0%, #E3F2FD 100%); border-radius: 15px; border-left: 8px solid #004E92; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 30px; min-height: 100px; display: flex; align-items: center;">
    {header_inner}
</div>
""", unsafe_allow_html=True)

abas = ["Início", "Estudante", "Mapeamento", "Plano de Ação", "Assistente de IA", "Documento"]
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(abas)

# 1. HOME
with tab1:
    st.markdown("### <i class='ri-dashboard-line'></i> Ecossistema de Inclusão", unsafe_allow_html=True)
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="info-card"><h4><i class="ri-book-open-line"></i> O que é o PEI?</h4><p>Não é apenas um formulário. É um <b>mapa vivo</b> que transforma a matrícula em inclusão real.</p></div>', unsafe_allow_html=True)
        st.markdown('<div class="info-card"><h4><i class="ri-scales-3-line"></i> Legislação (LBI)</h4><p>A Lei Brasileira de Inclusão garante o acesso. O PEI é a prova material das adaptações oferecidas.</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="info-card"><h4><i class="ri-brain-line"></i> Neurociência</h4><p>Foco nas <b>Funções Executivas</b>. Entendemos como o cérebro processa a informação.</p></div>', unsafe_allow_html=True)
        st.markdown('<div class="info-card"><h4><i class="ri-compass-3-line"></i> Conexão BNCC</h4><p>Para Ed. Infantil: <b>Campos de Experiência</b>. Para EF/EM: <b>Habilidades Essenciais</b>.</p></div>', unsafe_allow_html=True)

# 2. ESTUDANTE (FLUXO REORGANIZADO)
with tab2:
    st.info("Dossiê do Estudante.")
    # 1. Identificação Básica
    c1, c2, c3 = st.columns([2, 1, 1])
    st.session_state.dados['nome'] = c1.text_input("Nome do Estudante", st.session_state.dados['nome'])
    val_nasc = st.session_state.dados.get('nasc')
    st.session_state.dados['nasc'] = c2.date_input("Data de Nascimento", val_nasc, format="DD/MM/YYYY")
    st.session_state.dados['serie'] = c3.selectbox("Série/Ano", ["Ed. Infantil", "1º Ano", "2º Ano", "3º Ano", "4º Ano", "5º Ano", "6º Ano", "7º Ano", "8º Ano", "9º Ano", "Ensino Médio"], index=None, placeholder="Selecione...")
    
    st.markdown("---")
    # 2. Histórico e Família (MOVIDO PARA CIMA)
    st.markdown("##### <i class='ri-history-line'></i> Contexto Escolar e Familiar", unsafe_allow_html=True)
    ch, cf = st.columns(2)
    st.session_state.dados['historico'] = ch.text_area("Histórico Escolar", st.session_state.dados['historico'], placeholder="Escolas anteriores, retenção, adaptação...")
    st.session_state.dados['familia'] = cf.text_area("Escuta da Família", st.session_state.dados['familia'], placeholder="Expectativas, rotina, autonomia...")

    st.markdown("---")
    # 3. Clínico e Apoio (MOVIDO PARA BAIXO)
    st.markdown("##### <i class='ri-stethoscope-line'></i> Clínico e Apoio", unsafe_allow_html=True)
    c_diag, c_rede = st.columns(2)
    st.session_state.dados['diagnostico'] = c_diag.text_input("Diagnóstico Clínico", st.session_state.dados['diagnostico'])
    val_rede = st.session_state.dados.get('rede_apoio', [])
    st.session_state.dados['rede_apoio'] = c_rede.multiselect("Rede de Apoio:", ["Psicólogo", "Fonoaudiólogo", "Neuropediatra", "Terapeuta Ocupacional", "Psicopedagogo", "AT"], default=val_rede, placeholder="Selecione...")
    
    # 4. Upload (NO FINAL)
    st.write("")
    with st.expander("📂 Anexar Laudo Médico (PDF)"):
        uploaded_file = st.file_uploader("Arraste o arquivo aqui", type="pdf", key="uploader_tab2")
        if uploaded_file is not None:
            texto = ler_pdf(uploaded_file)
            if texto: st.session_state.pdf_text = texto; st.success("✅ Documento Lido!")

# 3. MAPEAMENTO
with tab3:
    st.markdown("### <i class='ri-rocket-line'></i> Potencialidades", unsafe_allow_html=True)
    c_pot1, c_pot2 = st.columns(2)
    st.session_state.dados['hiperfoco'] = c_pot1.text_input("Hiperfoco (Interesse)")
    st.session_state.dados['potencias'] = c_pot2.multiselect("Pontos Fortes", ["Memória Visual", "Tecnologia", "Artes", "Oralidade", "Lógica"], placeholder="Selecione...")
    
    st.markdown("### <i class='ri-barricade-line'></i> Barreiras", unsafe_allow_html=True)
    with st.expander("👁️ Sensorial e Físico", expanded=True):
        st.session_state.dados['b_sensorial'] = st.multiselect("Barreiras:", ["Hipersensibilidade", "Busca Sensorial", "Seletividade", "Motora"], key="b_sens", placeholder="Selecione...")
        st.session_state.dados['sup_sensorial'] = st.select_slider("Suporte:", ["🟢 Autônomo", "🟡 Monitorado", "🟠 Substancial", "🔴 Muito Substancial"], value="🟡 Monitorado", key="s_sens")
    with st.expander("🧠 Cognitivo"):
        st.session_state.dados['b_cognitiva'] = st.multiselect("Barreiras:", ["Atenção", "Memória", "Rigidez", "Lentidão", "Abstração"], key="b_cog", placeholder="Selecione...")
        st.session_state.dados['sup_cognitiva'] = st.select_slider("Suporte:", ["🟢 Autônomo", "🟡 Monitorado", "🟠 Substancial", "🔴 Muito Substancial"], value="🟡 Monitorado", key="s_cog")
    with st.expander("❤️ Social"):
        st.session_state.dados['b_social'] = st.multiselect("Barreiras:", ["Isolamento", "Frustração", "Literalidade", "Ansiedade"], key="b_soc", placeholder="Selecione...")
        st.session_state.dados['sup_social'] = st.select_slider("Suporte:", ["🟢 Autônomo", "🟡 Monitorado", "🟠 Substancial", "🔴 Muito Substancial"], value="🟡 Monitorado", key="s_soc")

# 4. ESTRATÉGIAS
with tab4:
    st.markdown("### <i class='ri-checkbox-circle-line'></i> Estratégias", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Adaptações de Acesso**")
        st.session_state.dados['estrategias_acesso'] = st.multiselect("Recursos:", ["Tempo estendido", "Ledor/Escriba", "Material Ampliado", "Tablet", "Sala Silenciosa", "Pausas"], placeholder="Selecione...")
    with c2:
        st.markdown("**Adaptações Curriculares**")
        st.session_state.dados['estrategias_curriculo'] = st.multiselect("Estratégias:", ["Menos Questões", "Prova Oral", "Mapa Mental", "Conteúdo Prioritário", "Prática"], placeholder="Selecione...")

# 5. ASSISTENTE (MELHORADO)
with tab5:
    col_ia_left, col_ia_right = st.columns([1, 2])
    with col_ia_left:
        st.markdown("### <i class='ri-robot-line'></i> Consultor Especialista", unsafe_allow_html=True)
        st.markdown("""
        <div class="info-card">
            <h4><i class="ri-lightbulb-flash-line"></i> Inteligência Pedagógica</h4>
            <p style="font-size:0.9rem; margin-bottom:10px;">Minha análise cruza três bases fundamentais:</p>
            <ul style="margin: 0; padding-left: 20px; font-size: 0.85rem; color: #4A5568;">
                <li><b>LBI:</b> Garantia de direitos e acesso.</li>
                <li><b>Neurociência:</b> Respeito ao funcionamento cerebral.</li>
                <li><b>BNCC:</b> Habilidades e Objetivos da série.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        status_anexo = "✅ PDF Anexado" if st.session_state.pdf_text else "⚪ Sem anexo"
        st.caption(f"Contexto: {status_anexo}")
        
        if st.button("✨ Gerar Parecer Completo"):
            if not st.session_state.dados['nome']: st.warning("Preencha o nome.")
            else:
                with st.spinner("Consultando bases pedagógicas..."):
                    res, err = consultar_ia(api_key, st.session_state.dados, st.session_state.pdf_text)
                    if err: st.error(err)
                    else: st.session_state.dados['ia_sugestao'] = res; st.success("Análise Gerada!")
    with col_ia_right:
        st.markdown("### <i class='ri-file-text-line'></i> Parecer Técnico", unsafe_allow_html=True)
        if st.session_state.dados['ia_sugestao']:
            # Visualização melhorada para leitura (Card)
            st.markdown(f"""
            <div style="background-color:#F8FAFC; padding:20px; border-radius:10px; border:1px solid #E2E8F0; max-height:500px; overflow-y:auto; font-size:0.95rem; line-height:1.6;">
                {st.session_state.dados['ia_sugestao'].replace(chr(10), '<br>')}
            </div>
            """, unsafe_allow_html=True)
            # Campo para edição (Expander)
            with st.expander("✏️ Editar Texto"):
                st.session_state.dados['ia_sugestao'] = st.text_area("Edição:", st.session_state.dados['ia_sugestao'], height=300)
        else:
            st.info("O parecer aparecerá aqui após o processamento.")

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