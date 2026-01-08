import streamlit as st
from datetime import date
from io import BytesIO
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt
from openai import OpenAI
from pypdf import PdfReader
from fpdf import FPDF
import base64
import os
import re

# --- 1. CONFIGURAÇÃO E UTILITÁRIOS ---

def get_favicon():
    return "📘"

st.set_page_config(
    page_title="PEI 360º | Inteligência Inclusiva",
    page_icon=get_favicon(),
    layout="wide",
    initial_sidebar_state="expanded"
)

def finding_logo():
    possiveis = ["360.png", "360.jpg", "logo.png", "logo.jpg", "iconeaba.png"]
    for nome in possiveis:
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
        # Limita a leitura às 5 primeiras páginas para evitar crash da API
        for i, page in enumerate(reader.pages):
            if i > 5: break 
            texto += page.extract_text() + "\n"
        return texto
    except Exception as e: return f"Erro na leitura do PDF: {e}"

def limpar_texto_pdf(texto):
    if not texto: return ""
    texto = texto.replace('**', '').replace('__', '')
    texto = texto.replace('### ', '').replace('## ', '').replace('# ', '')
    texto = texto.replace('* ', '• ')
    texto = re.sub(r'[^\x00-\xff]', '', texto) 
    return texto

# --- 2. CSS AVANÇADO (DESIGN SYSTEM ARCO) ---
st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/remixicon@4.1.0/fonts/remixicon.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap" rel="stylesheet">
    
    <style>
    /* RESET GLOBAL */
    html, body, [class*="css"] { font-family: 'Nunito', sans-serif; color: #2D3748; }
    
    :root { 
        --brand-blue: #004E92; 
        --brand-coral: #FF6B6B; 
        --bg-light: #F7FAFC;
        --card-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        --border-radius: 16px;
    }

    /* CABEÇALHO FLUTUANTE (FORA DA CURVA) */
    .header-container {
        background: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
        padding: 30px;
        border-radius: var(--border-radius);
        border: 1px solid #EDF2F7;
        box-shadow: var(--card-shadow);
        margin-bottom: 35px;
        display: flex; 
        align-items: center; 
        gap: 30px;
        border-left: 8px solid var(--brand-blue);
        position: relative;
        overflow: hidden;
    }
    
    /* Decoração de fundo do Header */
    .header-bg-icon {
        position: absolute;
        right: -20px;
        bottom: -20px;
        font-size: 150px;
        color: rgba(0, 78, 146, 0.03);
        transform: rotate(-15deg);
        z-index: 0;
    }

    /* REMOVER LINHA VERMELHA DAS ABAS */
    div[data-baseweb="tab-highlight"] { background-color: transparent !important; }

    /* ESTILO DAS ABAS (PÍLULAS) */
    .stTabs [data-baseweb="tab-list"] { gap: 12px; padding-bottom: 15px; }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        border-radius: 24px;
        padding: 0 28px;
        background-color: white;
        border: 1px solid #E2E8F0;
        font-weight: 700;
        color: #718096;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--brand-coral) !important;
        color: white !important;
        border-color: var(--brand-coral) !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
    }

    /* CARDS INFORMATIVOS */
    .feature-card {
        background: white; 
        padding: 25px; 
        border-radius: var(--border-radius);
        border: 1px solid #EDF2F7; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        height: 100%; 
        transition: all 0.3s ease;
    }
    .feature-card:hover { 
        transform: translateY(-4px); 
        border-color: var(--brand-blue); 
        box-shadow: var(--card-shadow);
    }
    
    /* ÍCONES FLAT */
    .icon-box {
        width: 50px; height: 50px; 
        background: #EBF8FF; 
        border-radius: 12px;
        display: flex; align-items: center; justify-content: center; 
        margin-bottom: 15px;
    }
    .icon-box i { font-size: 26px; color: var(--brand-blue); }

    /* INPUTS & BOTÕES */
    .stTextInput input, .stTextArea textarea, div[data-baseweb="select"] {
        border-radius: 12px !important;
        border-color: #CBD5E0 !important;
    }
    div[data-testid="column"] .stButton button {
        border-radius: 12px !important;
        font-weight: 800 !important;
        height: 3.8em !important;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. LÓGICA DE IA OTIMIZADA (PARA NÃO TRAVAR) ---
def consultar_ia_otimizada(api_key, dados, contexto_pdf=""):
    if not api_key: return None, "⚠️ Configure a Chave API na barra lateral."
    
    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        # OTIMIZAÇÃO: Limita o contexto do PDF para não estourar tokens
        pdf_resumido = contexto_pdf[:3000] if contexto_pdf else "Sem laudo anexo."

        termo_ahsd = "Altas Habilidades/Superdotação" if "altas habilidades" in dados['diagnostico'].lower() or "superdotação" in dados['diagnostico'].lower() else dados['diagnostico']
        
        # PROMPT ENGENHARIA REVERSA (BNCC + NEUROCIÊNCIA)
        prompt_sistema = """
        Você é um Especialista Sênior em Educação Inclusiva e Neurociência.
        Sua tarefa é criar o texto técnico de um PEI (Plano de Ensino Individualizado).
        Seja direto, técnico e evite repetições.
        """

        prompt_usuario = f"""
        ALUNO: {dados['nome']} | SÉRIE: {dados['serie']} | TURMA: {dados['turma']}
        DIAGNÓSTICO: {termo_ahsd} | HIPERFOCO: {dados['hiperfoco']}
        
        DADOS DE SUPORTE:
        - Histórico: {dados['historico']}
        - Família: {dados['familia']}
        - Rede de Apoio (Incluir no texto): {', '.join(dados['rede_apoio'])}
        - Orientações Clínicas: {dados['orientacoes_especialistas']}
        
        BARREIRAS & ESTRATÉGIAS:
        - Sensorial/Cognitivo/Social (Resumo): {', '.join(dados['b_sensorial'] + dados['b_cognitiva'])}
        - Estratégias Definidas: {', '.join(dados['estrategias_acesso'] + dados['estrategias_ensino'])}
        
        CONTEXTO LAUDO: {pdf_resumido}
        
        GERE O RELATÓRIO SEGUINDO ESTA ESTRUTURA (IMPORTANTE):
        1. ANÁLISE NEUROFUNCIONAL: Explique como o diagnóstico impacta a aprendizagem e como o hiperfoco será usado como ponte.
        2. HABILIDADE ESSENCIAL (BNCC): Cite UMA habilidade específica da BNCC (código alfanumérico) compatível com a série {dados['serie']} e explique como adaptá-la para este aluno.
        3. PLANO DE AÇÃO INTEGRADO: Conecte as orientações da rede de apoio com as estratégias de sala de aula selecionadas.
        4. AVALIAÇÃO: Defina como a nota será atribuída considerando as adaptações.
        """
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": prompt_usuario}],
            temperature=0.6, # Temperatura menor para ser mais objetivo e rápido
            max_tokens=1500,
            stream=False
        )
        return response.choices[0].message.content, None
    except Exception as e: return None, f"Erro de Conexão com IA: {str(e)}. Tente novamente."

# --- 4. PDF PROFISSIONAL ---
class ProfessionalPDF(FPDF):
    def header(self):
        # Moldura Institucional
        self.set_draw_color(0, 78, 146)
        self.set_line_width(0.5)
        self.rect(5, 5, 200, 287)
        
        logo = finding_logo()
        if logo: 
            self.image(logo, 12, 12, 22)
            x_offset = 40
        else: x_offset = 12
        
        self.set_xy(x_offset, 15)
        self.set_font('Arial', 'B', 14)
        self.set_text_color(0, 78, 146)
        self.cell(0, 8, 'PLANO DE ENSINO INDIVIDUALIZADO (PEI)', 0, 1, 'L')
        
        self.set_xy(x_offset, 22)
        self.set_font('Arial', 'I', 9)
        self.set_text_color(100)
        self.cell(0, 5, 'Documento Oficial | Sistema PEI 360º', 0, 1, 'L')
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Página {self.page_no()} | Documento Confidencial', 0, 0, 'C')

    def section_title(self, label):
        self.ln(5)
        self.set_fill_color(240, 248, 255)
        self.set_text_color(0, 78, 146)
        self.set_font('Arial', 'B', 11)
        self.cell(0, 8, f"  {label}", 0, 1, 'L', fill=True)
        self.ln(3)

def gerar_pdf_final(dados):
    pdf = ProfessionalPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)
    
    # 1. Identificação
    pdf.section_title("1. IDENTIFICAÇÃO E CONTEXTO")
    pdf.set_font("Arial", size=10); pdf.set_text_color(0)
    
    nasc_fmt = dados['nasc'].strftime('%d/%m/%Y') if dados['nasc'] else "-"
    texto_ident = (
        f"Nome: {dados['nome']}\n"
        f"Data de Nascimento: {nasc_fmt}\n"
        f"Série: {dados['serie']} | Turma: {dados['turma']}\n"
        f"Diagnóstico Clínico: {dados['diagnostico']}"
    )
    pdf.multi_cell(0, 6, limpar_texto_pdf(texto_ident))
    
    # 2. Rede de Apoio
    if dados['rede_apoio']:
        pdf.ln(2)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 6, "Acompanhamento Multidisciplinar:", 0, 1)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 6, limpar_texto_pdf(', '.join(dados['rede_apoio'])))

    # 3. Corpo do Relatório (IA)
    if dados['ia_sugestao']:
        pdf.ln(4)
        texto_ia = limpar_texto_pdf(dados['ia_sugestao'])
        pdf.multi_cell(0, 6, texto_ia)
        
    # 4. Assinaturas
    pdf.ln(20)
    y = pdf.get_y()
    if y > 250: pdf.add_page(); y = 40
    
    pdf.line(20, y, 90, y)
    pdf.line(120, y, 190, y)
    pdf.set_font("Arial", 'I', 8)
    pdf.text(30, y+5, "Coordenação Pedagógica")
    pdf.text(130, y+5, "Responsável Legal / Família")
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

def gerar_docx_final(dados):
    doc = Document()
    style = doc.styles['Normal']; style.font.name = 'Arial'; style.font.size = Pt(11)
    
    doc.add_heading('PLANO DE ENSINO INDIVIDUALIZADO', 0)
    doc.add_paragraph(f"Aluno(a): {dados['nome']}")
    doc.add_paragraph(f"Série: {dados['serie']} | Turma: {dados['turma']}")
    doc.add_paragraph(f"Diagnóstico: {dados['diagnostico']}")
    
    if dados['ia_sugestao']:
        doc.add_heading('Planejamento Pedagógico', level=1)
        doc.add_paragraph(dados['ia_sugestao'])
        
    buffer = BytesIO(); doc.save(buffer); buffer.seek(0)
    return buffer

# --- 5. INTERFACE (ESTADO E SIDEBAR) ---

if 'dados' not in st.session_state:
    st.session_state.dados = {
        'nome': '', 'nasc': None, 'serie': None, 'turma': '', 'diagnostico': '', 
        'historico': '', 'familia': '', 'hiperfoco': '', 'potencias': [],
        'rede_apoio': [], 'orientacoes_especialistas': '',
        'b_sensorial': [], 'sup_sensorial': '🟡 Monitorado',
        'b_cognitiva': [], 'sup_cognitiva': '🟡 Monitorado',
        'b_social': [], 'sup_social': '🟡 Monitorado',
        'estrategias_acesso': [], 'estrategias_ensino': [], 'estrategias_avaliacao': [],
        'ia_sugestao': ''
    }
if 'pdf_text' not in st.session_state: st.session_state.pdf_text = ""

with st.sidebar:
    logo = finding_logo()
    if logo: st.image(logo, width=120)
    
    if 'DEEPSEEK_API_KEY' in st.secrets:
        api_key = st.secrets['DEEPSEEK_API_KEY']
        st.success("✅ Sistema Ativo")
    else:
        api_key = st.text_input("Chave API:", type="password")
        
    st.markdown("---")
    st.markdown("<div style='font-size:0.8rem; color:#718096;'>PEI 360º v2.22<br>Performance Edition</div>", unsafe_allow_html=True)

# --- 6. CABEÇALHO FLUTUANTE (DESIGN NOVO) ---

logo_path = finding_logo()
b64_logo = get_base64_image(logo_path)
mime = "image/png" if logo_path and logo_path.endswith("png") else "image/jpeg"
img_html = f'<img src="data:{mime};base64,{b64_logo}" style="max-height: 80px; width: auto; position: relative; z-index: 1;">' if logo_path else ""

st.markdown(f"""
    <div class="header-container">
        <i class="ri-instance-line header-bg-icon"></i>
        {img_html}
        <div style="z-index: 1;">
            <h1 style="margin: 0; color: #004E92; font-weight: 800; font-size: 2rem; letter-spacing: -1px;">PEI 360º</h1>
            <p style="margin: 0; color: #718096; font-size: 1.1rem; font-weight: 600;">Ecossistema de Inteligência Pedagógica e Inclusiva</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- 7. ABAS E CONTEÚDO ---

abas = ["Início", "Estudante", "Rede de Apoio", "Mapeamento", "Plano de Ação", "Assistente IA", "Documento"]
tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(abas)

# TAB 0: Início
with tab0:
    st.markdown("### <i class='ri-dashboard-3-line'></i> Visão Geral", unsafe_allow_html=True)
    st.write("")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="feature-card">
            <div class="icon-box"><i class="ri-book-open-line"></i></div>
            <h4>O que é o PEI?</h4>
            <p>O documento oficial de acessibilidade curricular. Ele adapta o <b>acesso</b> ao conhecimento, não reduzindo o conteúdo, mas mudando a estratégia.</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="feature-card">
            <div class="icon-box"><i class="ri-government-line"></i></div>
            <h4>Base Legal</h4>
            <p>Em conformidade com a LBI e o novo Decreto 12.686/2025. O suporte é direito do aluno, independente de laudo médico fechado.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.write("")
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("""
        <div class="feature-card">
            <div class="icon-box"><i class="ri-brain-line"></i></div>
            <h4>Neurociência & BNCC</h4>
            <p>Nossa IA cruza o perfil neurofuncional (memória, atenção) com as Habilidades Essenciais da BNCC da série específica.</p>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown("""
        <div class="feature-card">
            <div class="icon-box"><i class="ri-team-line"></i></div>
            <h4>Rede de Apoio Integrada</h4>
            <p>O PEI 360 conecta as orientações dos terapeutas (fono, psico) com a prática de sala de aula do professor.</p>
        </div>
        """, unsafe_allow_html=True)

# TAB 1: Estudante
with tab1:
    st.markdown("### <i class='ri-user-smile-line'></i> Dossiê do Estudante", unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
    st.session_state.dados['nome'] = c1.text_input("Nome Completo", st.session_state.dados['nome'])
    st.session_state.dados['nasc'] = c2.date_input("Nascimento", st.session_state.dados['nasc'])
    st.session_state.dados['serie'] = c3.selectbox("Série/Ano", ["Ed. Infantil", "1º Ano", "2º Ano", "3º Ano", "4º Ano", "5º Ano", "6º ao 9º Ano", "Ensino Médio"], placeholder="Selecione...")
    st.session_state.dados['turma'] = c4.text_input("Turma", st.session_state.dados['turma'], placeholder="A, B...")
    
    st.write("")
    st.session_state.dados['diagnostico'] = st.text_input(
        "Diagnóstico Clínico (ou Hipótese)", 
        st.session_state.dados['diagnostico'],
        help="Ex: TEA, TDAH. Para Altas Habilidades, digite 'Altas Habilidades'."
    )

    st.markdown("---")
    ch, cf = st.columns(2)
    st.session_state.dados['historico'] = ch.text_area("Histórico Escolar (Trajetória)", height=100)
    st.session_state.dados['familia'] = cf.text_area("Contexto Familiar e Expectativas", height=100)
    
    with st.expander("📎 Upload de Laudo Médico (PDF)"):
        up = st.file_uploader("Selecione o arquivo", type="pdf")
        if up:
            st.session_state.pdf_text = ler_pdf(up)
            st.success("Documento lido com sucesso! (Otimizado para IA)")

# TAB 2: Rede de Apoio
with tab2:
    st.markdown("### <i class='ri-stethoscope-line'></i> Rede de Apoio Externa", unsafe_allow_html=True)
    st.info("Registre as orientações dos terapeutas para alinhar a conduta escolar.")
    
    c_rede1, c_rede2 = st.columns(2)
    st.session_state.dados['rede_apoio'] = c_rede1.multiselect(
        "Profissionais que atendem o aluno:", 
        ["Psicólogo", "Fonoaudiólogo", "Terapeuta Ocupacional", "Neuropediatra", "Psicopedagogo", "Professor Particular"],
        placeholder="Selecione..."
    )
    
    st.session_state.dados['orientacoes_especialistas'] = st.text_area(
        "Orientações Técnicas (O que a escola deve fazer?)",
        placeholder="Ex: A Fonoaudióloga solicitou uso de pistas visuais na lousa...",
        height=150
    )

# TAB 3: Mapeamento
with tab3:
    st.markdown("### <i class='ri-map-pin-user-line'></i> Mapeamento de Perfil", unsafe_allow_html=True)
    
    st.session_state.dados['hiperfoco'] = st.text_input("Hiperfoco / Áreas de Interesse (Alavanca de engajamento)")
    
    with st.expander("Perfil Sensorial e Físico", expanded=True):
        st.session_state.dados['b_sensorial'] = st.multiselect("Barreiras:", ["Hipersensibilidade Auditiva", "Hipersensibilidade Visual", "Busca Sensorial", "Baixo Tônus", "Agitação Motora"], placeholder="Selecione...")
        st.session_state.dados['sup_sensorial'] = st.select_slider("Suporte Sensorial", ["Autônomo", "Monitorado", "Substancial", "Muito Substancial"], value="Monitorado", key="sl_sens")

    with st.expander("Perfil Cognitivo"):
        st.session_state.dados['b_cognitiva'] = st.multiselect("Barreiras:", ["Atenção Sustentada", "Memória de Trabalho", "Rigidez Cognitiva", "Velocidade de Processamento", "Abstração"], placeholder="Selecione...")
        st.session_state.dados['sup_cognitiva'] = st.select_slider("Suporte Cognitivo", ["Autônomo", "Monitorado", "Substancial", "Muito Substancial"], value="Monitorado", key="sl_cog")

    with st.expander("Perfil Social e Emocional"):
        st.session_state.dados['b_social'] = st.multiselect("Barreiras:", ["Interação com Pares", "Tolerância à Frustração", "Compreensão de Regras", "Isolamento"], placeholder="Selecione...")
        st.session_state.dados['sup_social'] = st.select_slider("Suporte Social", ["Autônomo", "Monitorado", "Substancial", "Muito Substancial"], value="Monitorado", key="sl_soc")

# TAB 4: Plano de Ação
with tab4:
    st.markdown("### <i class='ri-tools-line'></i> Estratégias Pedagógicas", unsafe_allow_html=True)
    
    c_acesso, c_ensino = st.columns(2)
    with c_acesso:
        st.markdown("#### Acesso ao Currículo")
        st.session_state.dados['estrategias_acesso'] = st.multiselect(
            "Recursos de Acessibilidade:", 
            ["Tempo Estendido (+25%)", "Apoio à Leitura e Escrita (Ledor/Escriba)", "Material Ampliado", "Sala com Redução de Estímulos", "Uso de Tecnologia Assistiva", "Pausas Programadas"],
            placeholder="Selecione..."
        )
        
    with c_ensino:
        st.markdown("#### Metodologia de Ensino")
        st.session_state.dados['estrategias_ensino'] = st.multiselect(
            "Estratégias Didáticas:", 
            ["Fragmentação de Tarefas", "Pistas Visuais e Mapas Mentais", "Enriquecimento Curricular (AH/SD)", "Antecipação de Rotina", "Aprendizagem Baseada em Projetos"],
            placeholder="Selecione..."
        )
    
    st.write("")
    st.markdown("#### Avaliação Diferenciada")
    st.session_state.dados['estrategias_avaliacao'] = st.multiselect(
        "Como avaliar?", 
        ["Prova Adaptada (Conteúdo)", "Prova com Consulta", "Avaliação Oral", "Trabalhos e Projetos", "Sem Distratores Visuais"],
        placeholder="Selecione..."
    )

# TAB 5: Assistente IA
with tab5:
    st.markdown("### <i class='ri-robot-2-line'></i> Consultor Inteligente", unsafe_allow_html=True)
    st.info("A IA analisará todos os dados, inclusive BNCC e Neurociência, para gerar o texto final.")
    
    col_btn, col_res = st.columns([1, 3])
    with col_btn:
        st.write("")
        st.write("")
        if st.button("GERAR PEI AGORA", type="primary"):
            if not st.session_state.dados['nome']:
                st.error("Preencha o nome do estudante.")
            else:
                with st.spinner("Conectando com DeepSeek (Neurociência + BNCC)..."):
                    # Chamada otimizada
                    res, err = consultar_ia_otimizada(api_key, st.session_state.dados, st.session_state.pdf_text)
                    if err: st.error(err)
                    else: st.session_state.dados['ia_sugestao'] = res; st.success("PEI Gerado com Sucesso!")
    
    with col_res:
        if st.session_state.dados['ia_sugestao']:
            st.text_area("Texto do Relatório (Editável):", st.session_state.dados['ia_sugestao'], height=600)
        else:
            st.markdown("""
            <div style='padding:50px; text-align:center; color:#A0AEC0; border:2px dashed #CBD5E0; border-radius:12px; background-color: #F7FAFC;'>
                <i class="ri-file-text-line" style="font-size: 40px;"></i><br><br>
                O parecer técnico detalhado aparecerá aqui.<br>
                (Incluirá Habilidades BNCC e Análise Neurofuncional)
            </div>
            """, unsafe_allow_html=True)

# TAB 6: Documento
with tab6:
    st.markdown("### <i class='ri-file-pdf-line'></i> Exportação Oficial", unsafe_allow_html=True)
    
    if st.session_state.dados['ia_sugestao']:
        c_pdf, c_word = st.columns(2)
        with c_pdf:
            st.markdown("#### Arquivo PDF (Oficial)")
            pdf_bytes = gerar_pdf_final(st.session_state.dados)
            st.download_button("📥 Baixar PDF", pdf_bytes, f"PEI_{st.session_state.dados['nome']}.pdf", "application/pdf", type="primary")
            
        with c_word:
            st.markdown("#### Arquivo Word (Editável)")
            docx_bytes = gerar_docx_final(st.session_state.dados)
            st.download_button("📥 Baixar Word", docx_bytes, f"PEI_{st.session_state.dados['nome']}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        st.warning("⚠️ Gere o conteúdo na aba 'Assistente IA' antes de exportar.")

# Rodapé
st.markdown("---")
st.markdown("<div style='text-align: center; color: #718096; font-size: 0.8rem;'>PEI 360º v2.22 | Performance Edition</div>", unsafe_allow_html=True)