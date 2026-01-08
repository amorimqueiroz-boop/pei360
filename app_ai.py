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

# --- 1. CONFIGURAÇÃO INICIAL ---
def get_favicon():
    return "📘"

st.set_page_config(
    page_title="PEI 360º | OpenAI Edition",
    page_icon=get_favicon(),
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. UTILITÁRIOS ---
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
        # O GPT-4 suporta janelas de contexto maiores, podemos ler mais páginas
        for i, page in enumerate(reader.pages):
            if i >= 6: break 
            texto += page.extract_text() + "\n"
        return texto
    except Exception as e: return f"Erro ao ler PDF: {e}"

def limpar_texto_pdf(texto):
    if not texto: return ""
    texto = texto.replace('**', '').replace('__', '')
    texto = texto.replace('### ', '').replace('## ', '').replace('# ', '')
    texto = texto.replace('* ', '• ')
    texto = re.sub(r'[^\x00-\xff]', '', texto) 
    return texto

# --- 3. CSS UNIFICADO (DESIGN SYSTEM ARCO) ---
st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/remixicon@4.1.0/fonts/remixicon.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap" rel="stylesheet">
    
    <style>
    html, body, [class*="css"] { font-family: 'Nunito', sans-serif; color: #2D3748; }
    
    :root { 
        --brand-blue: #004E92; 
        --brand-coral: #FF6B6B; 
        --bg-gray: #F7FAFC;
        --card-radius: 16px;
    }

    div[data-baseweb="tab-highlight"] { background-color: transparent !important; }

    .unified-card {
        background-color: white;
        padding: 25px;
        border-radius: var(--card-radius);
        border: 1px solid #EDF2F7;
        box-shadow: 0 4px 6px rgba(0,0,0,0.03);
        margin-bottom: 20px;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .interactive-card:hover {
        transform: translateY(-3px);
        border-color: var(--brand-blue);
        box-shadow: 0 8px 15px rgba(0,78,146,0.08);
    }

    .header-content {
        display: flex;
        align-items: center;
        gap: 25px;
        border-left: 6px solid var(--brand-blue);
    }

    .stTabs [data-baseweb="tab-list"] { gap: 10px; padding-bottom: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        border-radius: 25px;
        padding: 0 25px;
        background-color: white;
        border: 1px solid #E2E8F0;
        font-weight: 700;
        color: #718096;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--brand-coral) !important;
        color: white !important;
        border-color: var(--brand-coral) !important;
        box-shadow: 0 4px 10px rgba(255, 107, 107, 0.2);
    }

    .icon-box {
        width: 45px; height: 45px;
        background: #EBF8FF;
        border-radius: 12px;
        display: flex; align-items: center; justify-content: center;
        margin-bottom: 15px;
        color: var(--brand-blue);
        font-size: 22px;
    }

    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        border-radius: 12px !important;
        border-color: #E2E8F0 !important;
    }
    div[data-testid="column"] .stButton button {
        border-radius: 12px !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        height: 50px !important;
        letter-spacing: 0.5px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 4. INTELIGÊNCIA ARTIFICIAL (OPENAI - GPT-4o-mini) ---
def consultar_gpt(api_key, dados, contexto_pdf=""):
    if not api_key: return None, "⚠️ Configure a Chave API OpenAI na barra lateral."
    
    try:
        # Cliente OpenAI Padrão
        client = OpenAI(api_key=api_key)
        
        # Limpeza e preparação de contexto
        contexto_seguro = contexto_pdf[:4000] if contexto_pdf else "Sem laudo anexado."
        
        # Definição de Perfil (AH/SD vs Dificuldades)
        is_ahsd = "altas habilidades" in dados['diagnostico'].lower() or "superdotação" in dados['diagnostico'].lower()
        foco_estrategico = "ENRIQUECIMENTO E APROFUNDAMENTO (Bloom Nível Superior)" if is_ahsd else "FLEXIBILIZAÇÃO E SUPORTE (DUA - Desenho Universal)"

        # Prompt de Sistema (Role) - Neuropsicopedagogo
        prompt_sistema = """
        Você é um Neuropsicopedagogo Sênior especialista em LBI (Lei Brasileira de Inclusão) e BNCC.
        Sua tarefa: Redigir o PEI (Plano de Ensino Individualizado) oficial.
        
        Regras de Ouro:
        1. CRUZE DADOS: Se o aluno tem "Memória Curta" (Mapeamento), justifique o uso de "Pistas Visuais" (Estratégia).
        2. BASE LEGAL: Garanta que o texto esteja em conformidade com o Decreto 12.686/2025 (Brasil).
        3. TOM DE VOZ: Profissional, acolhedor e técnico.
        4. BNCC: Cite explicitamente códigos da BNCC adequados à série do aluno.
        """

        # Prompt do Usuário (Dados)
        prompt_usuario = f"""
        PERFIL DO ESTUDANTE:
        Nome: {dados['nome']} | Série: {dados['serie']} | Turma: {dados['turma']}
        Diagnóstico: {dados['diagnostico']} ({foco_estrategico})
        Hiperfoco/Interesses: {dados['hiperfoco']}
        
        CONTEXTO BIOPSICOSSOCIAL:
        - Histórico Escolar: {dados['historico']}
        - Família: {dados['familia']}
        - Rede de Apoio (Incluir recomendações): {', '.join(dados['rede_apoio'])} | {dados['orientacoes_especialistas']}
        
        MAPEAMENTO DE BARREIRAS (Neurociência):
        - Sensorial: {', '.join(dados['b_sensorial'])}
        - Cognitivo (Funções Executivas): {', '.join(dados['b_cognitiva'])}
        - Social: {', '.join(dados['b_social'])}
        
        ESTRATÉGIAS PEDAGÓGICAS DEFINIDAS:
        - Acesso: {', '.join(dados['estrategias_acesso'])}
        - Ensino: {', '.join(dados['estrategias_ensino'])}
        - Avaliação: {', '.join(dados['estrategias_avaliacao'])}
        
        RESUMO DO LAUDO MÉDICO: {contexto_seguro}
        
        GERE O RELATÓRIO ESTRUTURADO:
        1. CARACTERIZAÇÃO DO ESTUDANTE: Sintetize o perfil cruzando histórico, diagnóstico e o impacto das barreiras nas funções executivas.
        2. PLANEJAMENTO CURRICULAR (BNCC): Selecione 1 Habilidade Essencial da {dados['serie']} e descreva como adaptá-la usando o Hiperfoco do aluno.
        3. ESTRATÉGIAS DE INTERVENÇÃO: Explique COMO aplicar as estratégias selecionadas (ex: como usar o ledor, como fracionar tarefas) baseando-se na neurociência.
        4. PARECER FINAL: Conclusão sobre a viabilidade do plano e recomendações à família.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Modelo rápido, barato e inteligente (ou gpt-4o se preferir)
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": prompt_usuario}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content, None
    except Exception as e: 
        return None, f"Erro OpenAI: {str(e)}. Verifique sua chave API ou saldo."

# --- 5. PDF EXECUTIVO ---
class PDF_V3(FPDF):
    def header(self):
        self.set_draw_color(0, 78, 146)
        self.set_line_width(0.4)
        self.rect(5, 5, 200, 287)
        
        logo = finding_logo()
        if logo: 
            self.image(logo, 12, 12, 22)
            x_offset = 40
        else: x_offset = 12
        
        self.set_xy(x_offset, 15)
        self.set_font('Arial', 'B', 14)
        self.set_text_color(0, 78, 146)
        self.cell(0, 8, 'PEI - PLANO DE ENSINO INDIVIDUALIZADO', 0, 1, 'L')
        
        self.set_xy(x_offset, 22)
        self.set_font('Arial', 'I', 9)
        self.set_text_color(100)
        self.cell(0, 5, 'Documento Oficial de Planejamento Pedagógico | LBI & BNCC', 0, 1, 'L')
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Gerado via PEI 360º (GPT-Powered) | Página {self.page_no()}', 0, 0, 'C')

    def section_title(self, label):
        self.ln(5)
        self.set_fill_color(240, 248, 255)
        self.set_text_color(0, 78, 146)
        self.set_font('Arial', 'B', 11)
        self.cell(0, 8, f"  {label}", 0, 1, 'L', fill=True)
        self.ln(3)

def gerar_pdf(dados):
    pdf = PDF_V3()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)
    
    # 1. Identificação
    pdf.section_title("1. IDENTIFICAÇÃO E CONTEXTO")
    pdf.set_font("Arial", size=10); pdf.set_text_color(0)
    
    nasc = dados['nasc'].strftime('%d/%m/%Y') if dados['nasc'] else "-"
    txt_ident = (
        f"Nome: {dados['nome']}\n"
        f"Nascimento: {nasc}\n"
        f"Série: {dados['serie']} | Turma: {dados['turma']}\n"
        f"Diagnóstico: {dados['diagnostico']}"
    )
    pdf.multi_cell(0, 6, limpar_texto_pdf(txt_ident))
    
    # 2. Rede de Apoio
    if dados['rede_apoio']:
        pdf.ln(3)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 6, "Rede de Apoio Multidisciplinar:", 0, 1)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 6, limpar_texto_pdf(', '.join(dados['rede_apoio'])))

    # 3. Relatório IA
    if dados['ia_sugestao']:
        pdf.ln(5)
        txt_ia = limpar_texto_pdf(dados['ia_sugestao'])
        pdf.multi_cell(0, 6, txt_ia)
        
    # 4. Assinaturas
    pdf.ln(20)
    y = pdf.get_y()
    if y > 250: pdf.add_page(); y = 40
    pdf.line(20, y, 90, y); pdf.line(120, y, 190, y)
    pdf.set_font("Arial", 'I', 8)
    pdf.text(35, y+5, "Coordenação / Direção"); pdf.text(135, y+5, "Família / Responsável")
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

def gerar_docx(dados):
    doc = Document()
    style = doc.styles['Normal']; style.font.name = 'Arial'; style.font.size = Pt(11)
    
    doc.add_heading('PLANO DE ENSINO INDIVIDUALIZADO', 0)
    doc.add_paragraph(f"Estudante: {dados['nome']}")
    doc.add_paragraph(f"Série: {dados['serie']} | Turma: {dados['turma']}")
    doc.add_paragraph(f"Diagnóstico: {dados['diagnostico']}")
    
    if dados['ia_sugestao']:
        doc.add_heading('Parecer Pedagógico', level=1)
        doc.add_paragraph(dados['ia_sugestao'])
        
    buffer = BytesIO(); doc.save(buffer); buffer.seek(0)
    return buffer

# --- 6. ESTADO DA SESSÃO ---
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

# --- 7. SIDEBAR ---
with st.sidebar:
    logo = finding_logo()
    if logo: st.image(logo, width=120)
    
    # MUDANÇA: Chave agora é OPENAI
    if 'OPENAI_API_KEY' in st.secrets:
        api_key = st.secrets['OPENAI_API_KEY']
        st.success("✅ OpenAI Ativa")
    else:
        api_key = st.text_input("Chave OpenAI (sk-...):", type="password")
        
    st.markdown("---")
    st.markdown("<div style='font-size:0.8rem; color:#A0AEC0;'>PEI 360º v3.2<br>Powered by GPT-4o</div>", unsafe_allow_html=True)

# --- 8. LAYOUT PRINCIPAL ---

# CABEÇALHO
logo_path = finding_logo()
b64_logo = get_base64_image(logo_path)
mime = "image/png" if logo_path and logo_path.endswith("png") else "image/jpeg"
img_html = f'<img src="data:{mime};base64,{b64_logo}" style="height: 70px;">' if logo_path else ""

st.markdown(f"""
    <div class="unified-card header-content">
        {img_html}
        <div>
            <h1 style="margin: 0; color: #004E92; font-size: 1.8rem; font-weight: 800;">PEI 360º</h1>
            <p style="margin: 0; color: #718096; font-size: 1rem;">Ecossistema de Inteligência Pedagógica e Inclusiva</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# ABAS
abas = ["Início", "Estudante", "Rede de Apoio", "Mapeamento", "Plano de Ação", "Consultoria IA", "Documento"]
tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(abas)

# TAB 0: INÍCIO
with tab0:
    st.markdown("### <i class='ri-dashboard-line'></i> Visão Geral", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="unified-card interactive-card">
            <div class="icon-box"><i class="ri-book-read-line"></i></div>
            <h4>O que é o PEI?</h4>
            <p>O PEI materializa o direito à educação. Adaptamos o método, o tempo e a avaliação para garantir o acesso ao currículo, conforme LBI e BNCC.</p>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="unified-card interactive-card">
            <div class="icon-box"><i class="ri-scales-3-line"></i></div>
            <h4>Legalidade e Direito</h4>
            <p>Em conformidade com o Decreto 12.686/2025. O PEI deve ser elaborado com base nas barreiras, independente de laudo médico fechado.</p>
        </div>""", unsafe_allow_html=True)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown("""
        <div class="unified-card interactive-card">
            <div class="icon-box"><i class="ri-brain-line"></i></div>
            <h4>Neurociência Aplicada</h4>
            <p>O sistema cruza as Funções Executivas (Memória, Atenção) com as estratégias pedagógicas para maximizar a aprendizagem.</p>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown("""
        <div class="unified-card interactive-card">
            <div class="icon-box"><i class="ri-compass-3-line"></i></div>
            <h4>Base Nacional (BNCC)</h4>
            <p>Garantimos as Aprendizagens Essenciais. O sistema sugere adaptações específicas para as habilidades de cada ano/série.</p>
        </div>""", unsafe_allow_html=True)

# TAB 1: ESTUDANTE
with tab1:
    st.markdown("### <i class='ri-user-smile-line'></i> Dossiê do Estudante", unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
    st.session_state.dados['nome'] = c1.text_input("Nome Completo", st.session_state.dados['nome'])
    st.session_state.dados['nasc'] = c2.date_input("Nascimento", st.session_state.dados['nasc'])
    st.session_state.dados['serie'] = c3.selectbox("Série/Ano", ["Infantil", "1º Ano", "2º Ano", "3º Ano", "4º Ano", "5º Ano", "Fund. II", "Ensino Médio"])
    st.session_state.dados['turma'] = c4.text_input("Turma", st.session_state.dados['turma'])

    st.markdown("---")
    st.markdown("##### 1. Contexto Biopsicossocial")
    
    ch, cf = st.columns(2)
    with ch:
        st.info("Trajetória escolar (escolas anteriores, retenções, avanços, relação com a escola).")
        st.session_state.dados['historico'] = st.text_area("Histórico Escolar", st.session_state.dados['historico'], height=120, label_visibility="collapsed")
    with cf:
        st.info("Rotina, cuidadores, expectativas e estrutura familiar.")
        st.session_state.dados['familia'] = st.text_area("Contexto Familiar", st.session_state.dados['familia'], height=120, label_visibility="collapsed")

    st.markdown("##### 2. Hipótese ou Diagnóstico")
    st.caption("Preencha após analisar o contexto. O PEI independe de laudo fechado, mas o diagnóstico guia estratégias específicas.")
    st.session_state.dados['diagnostico'] = st.text_input(
        "Diagnóstico Clínico", 
        st.session_state.dados['diagnostico'],
        placeholder="Ex: TEA Nível 1, TDAH, Dislexia. Para Altas Habilidades, digite 'Altas Habilidades'."
    )
    
    with st.expander("📎 Upload de Laudo (PDF)"):
        up = st.file_uploader("Anexar arquivo", type="pdf")
        if up:
            st.session_state.pdf_text = ler_pdf(up)
            st.success("PDF processado!")

# TAB 2: REDE DE APOIO
with tab2:
    st.markdown("### <i class='ri-team-line'></i> Rede de Apoio Multidisciplinar", unsafe_allow_html=True)
    st.info("A inclusão acontece em rede. Registre os parceiros clínicos do estudante.")
    
    c_rede1, c_rede2 = st.columns(2)
    st.session_state.dados['rede_apoio'] = c_rede1.multiselect(
        "Profissionais que atendem o aluno:", 
        ["Psicólogo", "Fonoaudiólogo", "Terapeuta Ocupacional", "Neuropediatra", "Psicopedagogo", "Professor Particular"]
    )
    
    st.session_state.dados['orientacoes_especialistas'] = st.text_area(
        "Orientações Técnicas (Resumo)",
        placeholder="Ex: A Fonoaudióloga solicitou que o aluno tenha mais tempo para respostas orais...",
        height=150
    )

# TAB 3: MAPEAMENTO
with tab3:
    st.markdown("### <i class='ri-map-pin-user-line'></i> Mapeamento de Barreiras e Potencialidades", unsafe_allow_html=True)
    
    st.session_state.dados['hiperfoco'] = st.text_input("Hiperfoco / Interesses (A chave para o engajamento)", placeholder="Ex: Dinossauros, Minecraft, Futebol, Desenho...")
    
    c_bar1, c_bar2, c_bar3 = st.columns(3)
    
    with c_bar1:
        with st.container(border=True):
            st.markdown("#### <i class='ri-eye-line'></i> Sensorial", unsafe_allow_html=True)
            st.session_state.dados['b_sensorial'] = st.multiselect("Barreiras:", ["Hipersensibilidade Auditiva", "Hipersensibilidade Visual", "Busca Sensorial", "Baixo Tônus", "Agitação Motora"], key="b1")
            st.session_state.dados['sup_sensorial'] = st.select_slider("Nível de Suporte", ["Autônomo", "Monitorado", "Substancial", "Muito Substancial"], value="Monitorado", key="s1")

    with c_bar2:
        with st.container(border=True):
            st.markdown("#### <i class='ri-brain-line'></i> Cognitivo", unsafe_allow_html=True)
            st.session_state.dados['b_cognitiva'] = st.multiselect("Barreiras:", ["Atenção Sustentada", "Memória de Trabalho", "Rigidez Mental", "Processamento Lento", "Abstração"], key="b2")
            st.session_state.dados['sup_cognitiva'] = st.select_slider("Nível de Suporte", ["Autônomo", "Monitorado", "Substancial", "Muito Substancial"], value="Monitorado", key="s2")

    with c_bar3:
        with st.container(border=True):
            st.markdown("#### <i class='ri-emotion-line'></i> Social", unsafe_allow_html=True)
            st.session_state.dados['b_social'] = st.multiselect("Barreiras:", ["Interação com Pares", "Tolerância à Frustração", "Entendimento de Regras", "Isolamento"], key="b3")
            st.session_state.dados['sup_social'] = st.select_slider("Nível de Suporte", ["Autônomo", "Monitorado", "Substancial", "Muito Substancial"], value="Monitorado", key="s3")

# TAB 4: PLANO DE AÇÃO
with tab4:
    st.markdown("### <i class='ri-tools-line'></i> Estratégias Pedagógicas (DUA)", unsafe_allow_html=True)
    st.caption("Selecione os recursos de Desenho Universal para Aprendizagem.")
    
    c_acesso, c_ensino = st.columns(2)
    with c_acesso:
        st.markdown("#### 1. Acesso ao Currículo")
        st.session_state.dados['estrategias_acesso'] = st.multiselect(
            "Recursos de Acessibilidade:", 
            ["Tempo Estendido (+25%)", "Apoio à Leitura e Escrita (Ledor/Escriba)", "Material Ampliado", "Sala com Redução de Estímulos", "Uso de Tecnologia/Tablet", "Pausas Sensoriais"],
            placeholder="Selecione..."
        )
        
    with c_ensino:
        st.markdown("#### 2. Metodologia de Ensino")
        st.session_state.dados['estrategias_ensino'] = st.multiselect(
            "Estratégias Didáticas:", 
            ["Fragmentação de Tarefas", "Pistas Visuais e Mapas", "Enriquecimento Curricular (AH/SD)", "Antecipação de Rotina", "Aprendizagem Baseada em Projetos"],
            placeholder="Selecione..."
        )
    
    st.write("")
    st.markdown("#### 3. Avaliação Diferenciada")
    st.session_state.dados['estrategias_avaliacao'] = st.multiselect(
        "Formato de Avaliação:", 
        ["Prova Adaptada (Conteúdo)", "Consulta Permitida", "Avaliação Oral", "Trabalho ou Projeto Prático", "Enunciados Curtos e Diretos"],
        placeholder="Selecione..."
    )

# TAB 5: CONSULTORIA IA
with tab5:
    st.markdown("### <i class='ri-robot-2-line'></i> Consultoria Pedagógica (GPT-4o)", unsafe_allow_html=True)
    
    col_btn, col_txt = st.columns([1, 2])
    with col_btn:
        st.markdown("""
        <div style="background:#EBF8FF; padding:15px; border-radius:12px; font-size:0.9rem; color:#004E92;">
            <b>Inteligência Neuropsicopedagógica:</b><br>
            Eu cruzo o perfil do aluno com a BNCC e a Neurociência para sugerir um plano fundamentado e legalmente seguro.
        </div>
        """, unsafe_allow_html=True)
        st.write("")
        if st.button("GERAR PLANO AGORA", type="primary"):
            if not st.session_state.dados['nome']:
                st.error("⚠️ Preencha o nome do aluno na aba 'Estudante'.")
            else:
                with st.spinner("Consultando OpenAI (Neurociência + BNCC)..."):
                    res, err = consultar_gpt(api_key, st.session_state.dados, st.session_state.pdf_text)
                    if err: 
                        st.error(err)
                    else: 
                        st.session_state.dados['ia_sugestao'] = res
                        st.success("Plano gerado com sucesso!")
    
    with col_txt:
        if st.session_state.dados['ia_sugestao']:
            st.text_area("Parecer Técnico (Editável):", st.session_state.dados['ia_sugestao'], height=500)
        else:
            st.markdown("""
            <div style='padding:50px; text-align:center; color:#A0AEC0; border:2px dashed #CBD5E0; border-radius:12px;'>
                <i class="ri-magic-line" style="font-size: 30px;"></i><br>
                O parecer técnico aparecerá aqui.
            </div>
            """, unsafe_allow_html=True)

# TAB 6: DOCUMENTO
with tab6:
    st.markdown("### <i class='ri-file-pdf-line'></i> Exportação Oficial", unsafe_allow_html=True)
    
    if st.session_state.dados['ia_sugestao']:
        c_pdf, c_word = st.columns(2)
        with c_pdf:
            st.markdown("#### Versão PDF (Final)")
            st.caption("Documento oficial com bordas e formatação institucional.")
            pdf_bytes = gerar_pdf(st.session_state.dados)
            st.download_button("📥 Baixar PDF", pdf_bytes, f"PEI_{st.session_state.dados['nome']}.pdf", "application/pdf", type="primary")
            
        with c_word:
            st.markdown("#### Versão Word (Editável)")
            st.caption("Para ajustes finos de formatação.")
            docx_bytes = gerar_docx(st.session_state.dados)
            st.download_button("📥 Baixar Word", docx_bytes, f"PEI_{st.session_state.dados['nome']}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        st.warning("⚠️ Gere o conteúdo na aba 'Consultoria IA' antes de exportar.")

# Rodapé
st.markdown("---")
st.markdown("<div style='text-align: center; color: #718096; font-size: 0.8rem;'>PEI 360º v3.2 | Powered by OpenAI</div>", unsafe_allow_html=True)