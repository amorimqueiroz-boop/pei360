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

# --- FUNÇÕES DE SUPORTE ---
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
        for page in reader.pages: texto += page.extract_text() + "\n"
        return texto
    except Exception as e: return f"Erro: {e}"

def limpar_para_pdf(texto):
    if not texto: return ""
    texto = texto.replace('**', '').replace('__', '')
    texto = texto.replace('### ', '').replace('## ', '').replace('# ', '')
    texto = texto.replace('* ', '• ')
    # Remove caracteres não suportados pelo Latin-1 (comum na FPDF padrão)
    return re.sub(r'[^\x00-\xff]', '', texto)

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="PEI 360º | Gestão Inclusiva v2.19",
    page_icon="📘",
    layout="wide"
)

# --- ESTILO CSS (SINCRONIZADO) ---
st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/remixicon@4.1.0/fonts/remixicon.css" rel="stylesheet">
    <style>
    html, body, [class*="css"] { font-family: 'Nunito', sans-serif; }
    :root { --brand-blue: #004E92; --brand-coral: #FF6B6B; }
    
    /* Header Unificado com o Padrão de Cards */
    .header-container {
        padding: 30px; 
        background: white; 
        border-radius: 20px; 
        border: 1px solid #EDF2F7; 
        border-top: 6px solid var(--brand-blue); 
        box-shadow: 0 10px 15px -3px rgba(0,0,0,0.05);
        margin-bottom: 30px;
        display: flex; align-items: center; gap: 25px;
    }

    /* Cards e Abas */
    .stTabs [aria-selected="true"] { 
        background-color: var(--brand-coral) !important; 
        color: white !important; 
        border-radius: 12px;
    }
    .feature-card {
        background: white; padding: 20px; border-radius: 20px;
        border: 1px solid #EDF2F7; box-shadow: 0 4px 6px rgba(0,0,0,0.02);
        height: 100%; transition: 0.3s;
    }
    .feature-card:hover { border-color: var(--brand-blue); transform: translateY(-2px); }
    
    /* Estilização de Botões */
    div[data-testid="column"] .stButton button {
        border-radius: 12px !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    </style>
""", unsafe_allow_html=True)

# --- LÓGICA DE INTELIGÊNCIA ARTIFICIAL (CONSOLIDADA) ---
def consultar_ia_unificada(api_key, dados, contexto_pdf=""):
    if not api_key: return None, "Chave API não encontrada."
    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        prompt_sistema = """Você é um Especialista Sênior em Educação Especial, Neurociência e Legislação Brasileira (LBI e BNCC).
        Sua tarefa é redigir o corpo principal de um Plano de Ensino Individualizado (PEI).
        O texto deve ser técnico, coeso e pronto para o documento oficial. 
        Importante: Se o aluno tiver Altas Habilidades, foque em ENRIQUECIMENTO e ACELERAÇÃO.
        Se houver dados de Rede de Apoio, integre as recomendações clínicas às práticas pedagógicas."""

        prompt_usuario = f"""
        Estudante: {dados['nome']} | Série: {dados['serie']} | Diagnóstico: {dados['diagnostico']}
        Hiperfoco/Interesses: {dados['hiperfoco']}
        
        HISTÓRICO E FAMÍLIA: {dados['historico']} | {dados['familia']}
        REDE DE APOIO: {', '.join(dados['rede_apoio'])}
        ORIENTAÇÕES DOS ESPECIALISTAS: {dados['orientacoes_especialistas']}
        
        BARREIRAS: Sensorial({', '.join(dados['b_sensorial'])}), Cognitiva({', '.join(dados['b_cognitiva'])}), Social({', '.join(dados['b_social'])})
        ESTRATÉGIAS SELECIONADAS: {', '.join(dados['estrategias_acesso'] + dados['estrategias_ensino'])}

        ESTRUTURA DO TEXTO:
        1. ANÁLISE BIOPSICOSSOCIAL: (Integre diagnóstico, histórico e orientações da rede de apoio).
        2. PLANEJAMENTO PEDAGÓGICO (BNCC): (Como as habilidades da série serão trabalhadas sob a ótica da diferenciação ou enriquecimento).
        3. PLANO DE SUPORTE: (Valide as barreiras e justifique as estratégias de acesso e avaliação).
        """

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": prompt_usuario}],
            temperature=0.6
        )
        return response.choices[0].message.content, None
    except Exception as e: return None, str(e)

# --- PDF PROFISSIONAL COM BORDAS E DIAGRAMAÇÃO ---
class ProfessionalPDF(FPDF):
    def header(self):
        # Desenha borda decorativa
        self.set_line_width(0.5)
        self.rect(5, 5, 200, 287)
        
        logo = finding_logo()
        if logo: self.image(logo, 10, 10, 22)
        
        self.set_font('Arial', 'B', 14)
        self.set_text_color(0, 78, 146)
        self.cell(30)
        self.cell(0, 10, 'PLANO DE ENSINO INDIVIDUALIZADO (PEI)', 0, 1, 'L')
        self.set_font('Arial', 'I', 9)
        self.cell(30)
        self.cell(0, 5, 'Documento Elaborado via Ecossistema PEI 360', 0, 1, 'L')
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(150)
        self.cell(0, 10, f'PEI 360 - Página {self.page_no()} | Gerado em {date.today().strftime("%d/%m/%Y")}', 0, 0, 'C')

    def section_title(self, label):
        self.set_fill_color(240, 245, 255)
        self.set_text_color(0, 78, 146)
        self.set_font('Arial', 'B', 11)
        self.cell(0, 10, f"  {label}", 0, 1, 'L', fill=True)
        self.ln(3)

def gerar_pdf_v219(dados):
    pdf = ProfessionalPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # 1. Identificação
    pdf.section_title("1. IDENTIFICAÇÃO DO ESTUDANTE")
    pdf.set_font("Arial", size=10); pdf.set_text_color(0)
    pdf.cell(0, 7, f"Nome: {dados['nome']}", 0, 1)
    pdf.cell(0, 7, f"Data de Nascimento: {dados['nasc'].strftime('%d/%m/%Y') if dados['nasc'] else 'N/A'}", 0, 1)
    pdf.cell(0, 7, f"Série/Ano: {dados['serie']} | Diagnóstico: {dados['diagnostico']}", 0, 1)
    pdf.ln(5)

    # 2. Parecer Unificado (IA)
    if dados['ia_sugestao']:
        pdf.section_title("2. ANÁLISE TÉCNICA E PEDAGÓGICA UNIFICADA")
        pdf.set_font("Arial", size=10)
        texto_limpo = limpar_para_pdf(dados['ia_sugestao'])
        pdf.multi_cell(0, 6, texto_limpo)
    
    # Assinaturas
    pdf.ln(20)
    pdf.line(20, pdf.get_y(), 90, pdf.get_y())
    pdf.line(120, pdf.get_y(), 190, pdf.get_y())
    pdf.set_font("Arial", 'I', 8)
    pdf.cell(90, 5, "Coordenação Pedagógica", 0, 0, 'C')
    pdf.cell(90, 5, "Responsável Legal / Família", 0, 1, 'C')
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- INTERFACE (STREAMLIT) ---
if 'dados' not in st.session_state:
    st.session_state.dados = {
        'nome': '', 'nasc': None, 'serie': None, 'diagnostico': '', 
        'historico': '', 'familia': '', 'hiperfoco': '',
        'rede_apoio': [], 'orientacoes_especialistas': '',
        'b_sensorial': [], 'b_cognitiva': [], 'b_social': [],
        'estrategias_acesso': [], 'estrategias_ensino': [], 'estrategias_avaliacao': [],
        'ia_sugestao': ''
    }

# Cabeçalho Profissional
logo_path = finding_logo()
if logo_path:
    b64_logo = get_base64_image(logo_path)
    st.markdown(f"""
        <div class="header-container">
            <img src="data:image/png;base64,{b64_logo}" height="80">
            <div style="border-left: 2px solid #EEE; padding-left: 20px;">
                <h2 style="margin:0; color:var(--brand-blue);">PEI 360º | Inclusão & Alta Performance</h2>
                <p style="margin:0; color:#666;">Sistema Inteligente de Planejamento Educacional</p>
            </div>
        </div>
    """, unsafe_allow_html=True)

# Abas
tab1, tab2, tab3, tab4, tab5 = st.tabs(["Estudante", "Rede de Apoio", "Mapeamento", "Plano IA", "Documento"])

with tab1:
    c1, c2, c3 = st.columns([2, 1, 1])
    st.session_state.dados['nome'] = c1.text_input("Nome do Aluno", st.session_state.dados['nome'])
    st.session_state.dados['nasc'] = c2.date_input("Nascimento", st.session_state.dados['nasc'])
    st.session_state.dados['serie'] = c3.selectbox("Série", ["Infantil", "1-5 Ano", "6-9 Ano", "Ensino Médio"])
    st.session_state.dados['diagnostico'] = st.text_input("Diagnóstico principal (Ex: TEA, TDAH, AH/SD - Altas Habilidades)")
    
    st.markdown("---")
    colh, colf = st.columns(2)
    st.session_state.dados['historico'] = colh.text_area("Breve Histórico Escolar")
    st.session_state.dados['familia'] = colf.text_area("Principais Queixas/Expectativas da Família")

with tab2:
    st.subheader("🌐 Conexão com Especialistas")
    st.info("Abaixo, registre quem acompanha o aluno fora da escola e o que eles recomendam.")
    st.session_state.dados['rede_apoio'] = st.multiselect("Profissionais Ativos:", 
        ["Psicólogo", "Fonoaudiólogo", "Terapeuta Ocupacional", "Neuropediatra", "Psicopedagogo", "Professor de AEE"])
    st.session_state.dados['orientacoes_especialistas'] = st.text_area("Resumo das orientações clínicas (Ex: 'A fono recomenda uso de comunicação alternativa')", height=150)

with tab3:
    st.subheader("🚀 Potencialidades & Barreiras")
    cpot, chp = st.columns(2)
    st.session_state.dados['hiperfoco'] = cpot.text_input("Áreas de interesse/Hiperfoco")
    
    with st.expander("Barreiras Identificadas", expanded=True):
        b1, b2, b3 = st.columns(3)
        st.session_state.dados['b_sensorial'] = b1.multiselect("Sensoriais", ["Luz", "Som", "Texturas", "Movimento"])
        st.session_state.dados['b_cognitiva'] = b2.multiselect("Cognitivas", ["Atenção", "Memória", "Abstração", "Organização"])
        st.session_state.dados['b_social'] = b3.multiselect("Sociais", ["Interação", "Frustração", "Rigidez"])

with tab4:
    st.subheader("🤖 Redator Inteligente PEI")
    if 'DEEPSEEK_API_KEY' in st.secrets:
        key = st.secrets['DEEPSEEK_API_KEY']
    else:
        key = st.sidebar.text_input("DeepSeek Key", type="password")
        
    if st.button("GERAR PEI UNIFICADO", type="primary"):
        with st.spinner("IA processando histórico, laudo e rede de apoio..."):
            res, err = consultar_ia_unificada(key, st.session_state.dados)
            if err: st.error(err)
            else: st.session_state.dados['ia_sugestao'] = res
            
    if st.session_state.dados['ia_sugestao']:
        st.markdown(st.session_state.dados['ia_sugestao'])

with tab5:
    st.subheader("📄 Exportação Oficial")
    if st.session_state.dados['nome'] and st.session_state.dados['ia_sugestao']:
        pdf_bytes = gerar_pdf_v219(st.session_state.dados)
        st.download_button("Baixar PDF Institucional", pdf_bytes, f"PEI_360_{st.session_state.dados['nome']}.pdf", "application/pdf")
    else:
        st.warning("Gere o parecer na aba 'Plano IA' antes de exportar.")

st.markdown("---")
st.caption("PEI 360º v2.19 | Desenvolvido por Rodrigo Queiroz")