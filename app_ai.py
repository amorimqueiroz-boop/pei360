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
    page_title="PEI 360º | Sistema Inclusivo",
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
        for page in reader.pages: texto += page.extract_text() + "\n"
        return texto
    except Exception as e: return f"Erro na leitura do PDF: {e}"

def limpar_texto_pdf(texto):
    if not texto: return ""
    # Remove formatação Markdown para impressão limpa
    texto = texto.replace('**', '').replace('__', '')
    texto = texto.replace('### ', '').replace('## ', '').replace('# ', '')
    texto = texto.replace('* ', '• ')
    # Tratamento de caracteres para FPDF (Latin-1)
    texto = re.sub(r'[^\x00-\xff]', '', texto) 
    return texto

# --- 2. CSS PROFISSIONAL & HARMONIZAÇÃO VISUAL ---
st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/remixicon@4.1.0/fonts/remixicon.css" rel="stylesheet">
    <link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap" rel="stylesheet">
    
    <style>
    /* Global */
    html, body, [class*="css"] { font-family: 'Nunito', sans-serif; color: #2D3748; }
    
    :root { 
        --brand-blue: #004E92; 
        --brand-coral: #FF6B6B; 
        --bg-light: #F7FAFC;
        --card-shadow: 0 4px 6px rgba(0,0,0,0.04);
    }

    /* Cabeçalho (Harmonizado) */
    .header-container {
        padding: 25px;
        background: white;
        border-radius: 20px;
        border: 1px solid #EDF2F7;
        /* Detalhe sutil na esquerda ao invés de topo, para alinhar com v2.18 mas modernizado */
        border-left: 6px solid var(--brand-blue); 
        box-shadow: var(--card-shadow);
        margin-bottom: 30px;
        display: flex; align-items: center; gap: 25px;
    }

    /* Cards Informativos (Aba Início) */
    .feature-card {
        background: white; 
        padding: 25px; 
        border-radius: 20px;
        border: 1px solid #EDF2F7; 
        box-shadow: var(--card-shadow);
        height: 100%; 
        transition: all 0.3s ease;
        display: flex; flex-direction: column; align-items: flex-start;
    }
    .feature-card:hover { 
        transform: translateY(-3px); 
        box-shadow: 0 10px 20px rgba(0,0,0,0.06); 
        border-color: var(--brand-blue); 
    }
    
    .icon-box {
        width: 45px; height: 45px; 
        background: #E3F2FD; 
        border-radius: 12px;
        display: flex; align-items: center; justify-content: center; 
        margin-bottom: 15px; flex-shrink: 0;
    }
    .icon-box i { font-size: 22px; color: var(--brand-blue); }
    .feature-card h4 { color: var(--brand-blue); font-weight: 800; font-size: 1.1rem; margin-bottom: 8px; line-height: 1.3; }
    .feature-card p { font-size: 0.95rem; color: #718096; line-height: 1.5; margin: 0; }

    /* Abas */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        height: 42px;
        border-radius: 20px;
        padding: 0 20px;
        background-color: white;
        border: 1px solid #CBD5E0;
        font-weight: 700;
        color: #4A5568;
    }
    .stTabs [aria-selected="true"] {
        background-color: var(--brand-coral) !important;
        color: white !important;
        border-color: var(--brand-coral) !important;
        box-shadow: 0 4px 10px rgba(255, 107, 107, 0.3);
    }
    
    /* Inputs e Sliders */
    div[data-baseweb="select"] { border-radius: 12px !important; }
    .stTextInput input, .stTextArea textarea { border-radius: 12px !important; }
    
    /* Botões */
    div[data-testid="column"] .stButton button {
        border-radius: 12px !important;
        font-weight: 700 !important;
        height: 3.5em !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. LÓGICA DE IA (INTEGRADA COM SLIDERS E REDE DE APOIO) ---
def consultar_ia_unificada(api_key, dados, contexto_pdf=""):
    if not api_key: return None, "⚠️ A chave de API não foi detectada."
    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        # Detecção de AH/SD
        termo_ahsd = "Altas Habilidades/Superdotação" if "altas habilidades" in dados['diagnostico'].lower() or "superdotação" in dados['diagnostico'].lower() else dados['diagnostico']
        foco_estrategia = "Enriquecimento Curricular e Aprofundamento" if "altas habilidades" in dados['diagnostico'].lower() else "Flexibilização e Suporte"

        prompt_sistema = f"""
        Você é um Consultor Sênior em Educação Inclusiva e Neurociência.
        Gere um parecer técnico para o PEI (Plano de Ensino Individualizado).
        Seja técnico, mas claro. O texto será usado em documento oficial.
        FOCO: {foco_estrategia}.
        """

        prompt_usuario = f"""
        ALUNO: {dados['nome']} | SÉRIE: {dados['serie']} | DIAGNÓSTICO: {termo_ahsd}
        HIPERFOCO: {dados['hiperfoco']}
        
        HISTÓRICO: {dados['historico']} | FAMÍLIA: {dados['familia']}
        
        REDE DE APOIO (INTEGRAR):
        Profissionais: {', '.join(dados['rede_apoio'])}
        Orientações Clínicas: {dados['orientacoes_especialistas']}
        
        MAPEAMENTO DE SUPORTE (IMPORTANTE):
        - Sensorial: {', '.join(dados['b_sensorial'])} (Nível: {dados['sup_sensorial']})
        - Cognitivo: {', '.join(dados['b_cognitiva'])} (Nível: {dados['sup_cognitiva']})
        - Social: {', '.join(dados['b_social'])} (Nível: {dados['sup_social']})
        
        ESTRATÉGIAS DEFINIDAS:
        Acesso: {', '.join(dados['estrategias_acesso'])}
        Ensino: {', '.join(dados['estrategias_ensino'])}
        
        LAUDO MÉDICO (CONTEXTO): {contexto_pdf[:1500]}
        
        GERE O TEXTO EM 3 TÓPICOS FLUIDOS (Sem listas excessivas):
        1. ANÁLISE BIOPSICOSSOCIAL (Cruze diagnóstico, níveis de suporte e histórico).
        2. PLANEJAMENTO PEDAGÓGICO E {foco_estrategia.upper()} (Conecte as estratégias escolhidas com a BNCC).
        3. ORIENTAÇÕES PARA AVALIAÇÃO E ROTINA.
        """
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": prompt_usuario}],
            temperature=0.7, stream=False
        )
        return response.choices[0].message.content, None
    except Exception as e: return None, f"Erro DeepSeek: {str(e)}"

# --- 4. PDF PROFISSIONAL ---
class ProfessionalPDF(FPDF):
    def header(self):
        # Borda elegante (Moldura)
        self.set_line_width(0.5)
        self.set_draw_color(0, 78, 146) # Azul Institucional
        self.rect(5, 5, 200, 287)
        
        logo = finding_logo()
        if logo: 
            self.image(logo, 10, 10, 22)
            x_offset = 38
        else: x_offset = 10
        
        self.set_xy(x_offset, 12)
        self.set_font('Arial', 'B', 15)
        self.set_text_color(0, 78, 146)
        self.cell(0, 8, 'PLANO DE ENSINO INDIVIDUALIZADO (PEI)', 0, 1, 'L')
        
        self.set_xy(x_offset, 19)
        self.set_font('Arial', 'I', 9)
        self.set_text_color(100)
        self.cell(0, 5, 'Documento Oficial de Planejamento e Acompanhamento', 0, 1, 'L')
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Sistema PEI 360 | Página {self.page_no()} | Confidencial', 0, 0, 'C')

    def section_title(self, label):
        self.set_fill_color(240, 248, 255) # Azul Alice
        self.set_text_color(0, 78, 146)
        self.set_font('Arial', 'B', 11)
        self.ln(5)
        self.cell(0, 8, f"  {label}", 0, 1, 'L', fill=True)
        self.ln(3)

def gerar_pdf_final(dados):
    pdf = ProfessionalPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=20)
    
    # 1. Identificação
    pdf.section_title("1. IDENTIFICAÇÃO DO ESTUDANTE")
    pdf.set_font("Arial", size=10); pdf.set_text_color(0)
    
    nasc_fmt = dados['nasc'].strftime('%d/%m/%Y') if dados['nasc'] else "-"
    texto_ident = (
        f"Nome: {dados['nome']}\n"
        f"Data de Nascimento: {nasc_fmt}\n"
        f"Série/Ano: {dados['serie']}\n"
        f"Diagnóstico/Hipótese: {dados['diagnostico']}"
    )
    pdf.multi_cell(0, 6, limpar_texto_pdf(texto_ident))
    
    # 2. Rede de Apoio (Novo)
    if dados['rede_apoio']:
        pdf.ln(2)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(0, 6, "Rede de Apoio Multidisciplinar:", 0, 1)
        pdf.set_font("Arial", size=10)
        pdf.multi_cell(0, 6, limpar_texto_pdf(', '.join(dados['rede_apoio'])))

    # 3. Parecer Técnico (IA)
    if dados['ia_sugestao']:
        pdf.ln(4)
        # O título da seção geralmente vem no texto da IA, mas garantimos visualmente
        # pdf.section_title("2. PARECER TÉCNICO E PEDAGÓGICO") 
        texto_ia = limpar_texto_pdf(dados['ia_sugestao'])
        pdf.multi_cell(0, 6, texto_ia)
        
    # 4. Assinaturas
    pdf.ln(25)
    y = pdf.get_y()
    if y > 250: pdf.add_page(); y = 40
    
    pdf.line(20, y, 90, y)
    pdf.line(120, y, 190, y)
    pdf.set_font("Arial", 'I', 8)
    pdf.text(35, y+5, "Coordenação Pedagógica")
    pdf.text(135, y+5, "Responsável Legal")
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

def gerar_docx_final(dados):
    doc = Document()
    style = doc.styles['Normal']; style.font.name = 'Arial'; style.font.size = Pt(11)
    
    doc.add_heading('PLANO DE ENSINO INDIVIDUALIZADO', 0)
    doc.add_paragraph(f"Estudante: {dados['nome']}")
    doc.add_paragraph(f"Série: {dados['serie']}")
    
    if dados['ia_sugestao']:
        doc.add_heading('Parecer Técnico', level=1)
        doc.add_paragraph(dados['ia_sugestao'])
        
    buffer = BytesIO(); doc.save(buffer); buffer.seek(0)
    return buffer

# --- 5. INTERFACE (STREAMLIT) ---

# Inicialização de Estado (Preservando Sliders)
if 'dados' not in st.session_state:
    st.session_state.dados = {
        'nome': '', 'nasc': None, 'serie': None, 'diagnostico': '', 
        'historico': '', 'familia': '', 'hiperfoco': '', 'potencias': [],
        'rede_apoio': [], 'orientacoes_especialistas': '',
        'b_sensorial': [], 'sup_sensorial': '🟡 Monitorado',
        'b_cognitiva': [], 'sup_cognitiva': '🟡 Monitorado',
        'b_social': [], 'sup_social': '🟡 Monitorado',
        'estrategias_acesso': [], 'estrategias_ensino': [], 'estrategias_avaliacao': [],
        'ia_sugestao': ''
    }
if 'pdf_text' not in st.session_state: st.session_state.pdf_text = ""

# Sidebar
with st.sidebar:
    logo = finding_logo()
    if logo: st.image(logo, width=120)
    
    if 'DEEPSEEK_API_KEY' in st.secrets:
        api_key = st.secrets['DEEPSEEK_API_KEY']
        st.success("✅ Chave Segura")
    else:
        api_key = st.text_input("Chave API:", type="password")
        
    st.markdown("---")
    st.caption("Versão 2.20 | Final Stable")

# Cabeçalho Visual (Harmonizado)
logo_path = finding_logo()
b64_logo = get_base64_image(logo_path)
mime = "image/png" if logo_path and logo_path.endswith("png") else "image/jpeg"
img_html = f'<img src="data:{mime};base64,{b64_logo}" style="max-height: 85px; width: auto;">' if logo_path else ""

st.markdown(f"""
    <div class="header-container">
        {img_html}
        <div class="header-text" style="border-left: 2px solid #E2E8F0; padding-left: 25px;">
            <p style="margin: 0; color: #004E92; font-weight: 800; font-size: 1.4rem;">PEI 360º</p>
            <p style="margin: 0; color: #718096; font-size: 0.95rem;">Ecossistema de Gestão da Educação Inclusiva</p>
        </div>
    </div>
""", unsafe_allow_html=True)

# Abas
abas = ["Início", "Estudante", "Rede de Apoio", "Mapeamento", "Plano de Ação", "Assistente IA", "Documento"]
tab0, tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(abas)

# TAB 0: Início (RESTORED)
with tab0:
    st.markdown("### <i class='ri-dashboard-line'></i> Visão Geral", unsafe_allow_html=True)
    st.write("")
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("""
        <div class="feature-card">
            <div class="icon-box"><i class="ri-book-open-line"></i></div>
            <h4>O que é o PEI?</h4>
            <p>Instrumento oficial de acessibilidade curricular. Garante que o estudante acesse o conhecimento respeitando suas especificidades, conforme a Lei Brasileira de Inclusão.</p>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="feature-card">
            <div class="icon-box"><i class="ri-scales-3-line"></i></div>
            <h4>Legislação Vigente</h4>
            <p>O PEI 360 está atualizado com o Decreto 12.686/2025 e a Política Nacional de Educação Especial Inclusiva. O foco é eliminar barreiras.</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.write("")
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("""
        <div class="feature-card">
            <div class="icon-box"><i class="ri-brain-line"></i></div>
            <h4>Neurociência Aplicada</h4>
            <p>Mapeamos funções executivas e perfil sensorial para sugerir estratégias que façam sentido para o funcionamento cerebral do aluno.</p>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown("""
        <div class="feature-card">
            <div class="icon-box"><i class="ri-compass-3-line"></i></div>
            <h4>Alinhamento BNCC</h4>
            <p>Não criamos um currículo paralelo. Flexibilizamos as Habilidades Essenciais da BNCC para garantir equidade na aprendizagem.</p>
        </div>
        """, unsafe_allow_html=True)

# TAB 1: Estudante
with tab1:
    st.markdown("### 👤 Dados Cadastrais")
    c1, c2, c3 = st.columns([2, 1, 1])
    st.session_state.dados['nome'] = c1.text_input("Nome do Estudante", st.session_state.dados['nome'])
    st.session_state.dados['nasc'] = c2.date_input("Nascimento", st.session_state.dados['nasc'])
    st.session_state.dados['serie'] = c3.selectbox("Série/Ano", ["Ed. Infantil", "1º Ano", "2º Ano", "3º Ano", "4º Ano", "5º Ano", "6º ao 9º Ano", "Ensino Médio"], placeholder="Selecione...")
    
    st.write("")
    # Diagnóstico sem alerta excessivo, mas com help text
    st.session_state.dados['diagnostico'] = st.text_input(
        "Diagnóstico ou Hipótese Diagnóstica", 
        st.session_state.dados['diagnostico'],
        help="Insira o diagnóstico clínico (ex: TEA, TDAH). Para Altas Habilidades, digite 'Altas Habilidades' para ativar estratégias de enriquecimento."
    )

    st.markdown("---")
    ch, cf = st.columns(2)
    st.session_state.dados['historico'] = ch.text_area("Histórico Escolar (Breve resumo)", height=100)
    st.session_state.dados['familia'] = cf.text_area("Contexto Familiar e Expectativas", height=100)
    
    with st.expander("📎 Anexar Laudo Médico (PDF)"):
        up = st.file_uploader("Carregar arquivo", type="pdf")
        if up:
            st.session_state.pdf_text = ler_pdf(up)
            st.success("Laudo processado com sucesso!")

# TAB 2: Rede de Apoio
with tab2:
    st.markdown("### 🤝 Conexão Terapêutica")
    st.info("Registre aqui os profissionais externos para que a escola trabalhe em parceria.")
    
    c_rede1, c_rede2 = st.columns(2)
    st.session_state.dados['rede_apoio'] = c_rede1.multiselect(
        "Profissionais que acompanham:", 
        ["Psicólogo", "Fonoaudiólogo", "Terapeuta Ocupacional", "Neuropediatra", "Psicopedagogo", "Professor Particular"],
        placeholder="Selecione..."
    )
    
    st.session_state.dados['orientacoes_especialistas'] = st.text_area(
        "Orientações Técnicas (Resumo)",
        placeholder="Ex: A TO recomendou uso de engrossador para escrita e pausas sensoriais...",
        height=150
    )

# TAB 3: Mapeamento (RESTORED SLIDERS)
with tab3:
    st.markdown("### 🧠 Mapeamento de Barreiras")
    st.session_state.dados['hiperfoco'] = st.text_input("Hiperfoco / Áreas de Interesse (Alavanca de aprendizagem)")
    
    # Sensorial
    with st.expander("Perfil Sensorial e Físico", expanded=True):
        st.session_state.dados['b_sensorial'] = st.multiselect("Barreiras Identificadas:", ["Hipersensibilidade (Luz/Som)", "Busca Sensorial", "Baixo Tônus", "Coordenação Motora"], placeholder="Selecione...")
        st.write("Nível de Suporte Necessário:")
        st.session_state.dados['sup_sensorial'] = st.select_slider("Nível Sensorial", ["🟢 Autônomo", "🟡 Monitorado", "🟠 Substancial", "🔴 Muito Substancial"], value="🟡 Monitorado", key="slider_sens")

    # Cognitivo
    with st.expander("Perfil Cognitivo"):
        st.session_state.dados['b_cognitiva'] = st.multiselect("Barreiras Identificadas:", ["Atenção Sustentada", "Memória de Trabalho", "Rigidez Mental", "Velocidade de Processamento"], placeholder="Selecione...")
        st.write("Nível de Suporte Necessário:")
        st.session_state.dados['sup_cognitiva'] = st.select_slider("Nível Cognitivo", ["🟢 Autônomo", "🟡 Monitorado", "🟠 Substancial", "🔴 Muito Substancial"], value="🟡 Monitorado", key="slider_cog")

    # Social
    with st.expander("Perfil Social e Emocional"):
        st.session_state.dados['b_social'] = st.multiselect("Barreiras Identificadas:", ["Interação Social", "Tolerância à Frustração", "Compreensão de Regras", "Isolamento"], placeholder="Selecione...")
        st.write("Nível de Suporte Necessário:")
        st.session_state.dados['sup_social'] = st.select_slider("Nível Social", ["🟢 Autônomo", "🟡 Monitorado", "🟠 Substancial", "🔴 Muito Substancial"], value="🟡 Monitorado", key="slider_soc")

# TAB 4: Plano de Ação (CORRECTED TERMS)
with tab4:
    st.markdown("### 🛠️ Estratégias Pedagógicas")
    
    c_acesso, c_ensino = st.columns(2)
    with c_acesso:
        st.markdown("#### Acesso ao Currículo")
        st.session_state.dados['estrategias_acesso'] = st.multiselect(
            "Recursos de Acessibilidade:", 
            ["Tempo Estendido (+25%)", "Apoio à Leitura e Escrita", "Material Ampliado", "Sala com Redução de Estímulos", "Uso de Tablet/Tecnologia", "Pausas Programadas"],
            placeholder="Selecione..."
        )
        
    with c_ensino:
        st.markdown("#### Metodologia e Ensino")
        st.session_state.dados['estrategias_ensino'] = st.multiselect(
            "Estratégias de Sala de Aula:", 
            ["Fragmentação de Tarefas", "Pistas Visuais", "Mapas Mentais", "Enriquecimento Curricular (AH/SD)", "Antecipação de Rotina", "Aprendizagem Baseada em Projetos"],
            placeholder="Selecione..."
        )

# TAB 5: Assistente IA
with tab5:
    st.markdown("### 🤖 Inteligência Pedagógica")
    st.info("A IA cruzará o Histórico, Rede de Apoio e Níveis de Suporte (Sliders) para criar o plano.")
    
    col_btn, col_res = st.columns([1, 3])
    with col_btn:
        st.write("")
        st.write("")
        if st.button("GERAR PEI UNIFICADO", type="primary"):
            if not st.session_state.dados['nome']:
                st.error("Preencha o nome na aba 'Estudante'.")
            else:
                with st.spinner("Analisando BNCC e Neurociência..."):
                    res, err = consultar_ia_unificada(api_key, st.session_state.dados, st.session_state.pdf_text)
                    if err: st.error(err)
                    else: st.session_state.dados['ia_sugestao'] = res; st.success("Sucesso!")
    
    with col_res:
        if st.session_state.dados['ia_sugestao']:
            st.text_area("Parecer Técnico (Editável):", st.session_state.dados['ia_sugestao'], height=450)
        else:
            st.markdown("<div style='padding:40px; text-align:center; color:#A0AEC0; border:2px dashed #CBD5E0; border-radius:12px;'>O parecer técnico aparecerá aqui.</div>", unsafe_allow_html=True)

# TAB 6: Documento
with tab6:
    st.markdown("### 📄 Documento Oficial")
    if st.session_state.dados['ia_sugestao']:
        c_pdf, c_word = st.columns(2)
        with c_pdf:
            st.markdown("#### Versão PDF (Final)")
            pdf_bytes = gerar_pdf_final(st.session_state.dados)
            st.download_button("📥 Baixar PDF Institucional", pdf_bytes, f"PEI_{st.session_state.dados['nome']}.pdf", "application/pdf", type="primary")
            st.caption("Com bordas, logo e formatação oficial.")
            
        with c_word:
            st.markdown("#### Versão Editável")
            docx_bytes = gerar_docx_final(st.session_state.dados)
            st.download_button("📥 Baixar Word (.docx)", docx_bytes, f"PEI_{st.session_state.dados['nome']}.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    else:
        st.warning("Gere o parecer na aba 'Assistente IA' antes de baixar o documento.")

# Rodapé
st.markdown("---")
st.markdown("<div style='text-align: center; color: #718096; font-size: 0.8rem;'>PEI 360º v2.20 | Desenvolvido por Rodrigo Queiroz</div>", unsafe_allow_html=True)