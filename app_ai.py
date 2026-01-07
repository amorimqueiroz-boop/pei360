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

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="PEI 360º | Sistema Inclusivo",
    page_icon="💙",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILO VISUAL (CLEAN & PROFISSIONAL) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #2D3748; }
    
    :root { --main-blue: #004e92; --bg-light: #F7FAFC; }
    
    /* Inputs refinados */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        border-radius: 8px !important; border: 1px solid #CBD5E0 !important;
    }
    
    /* Área de Upload Destacada */
    div[data-testid="stFileUploader"] section { 
        background-color: #EBF8FF; 
        border: 2px dashed #004e92;
        border-radius: 10px;
    }

    /* Cards Informativos */
    .info-card {
        background-color: white; padding: 20px; border-radius: 12px;
        border-left: 5px solid var(--main-blue);
        box-shadow: 0 2px 5px rgba(0,0,0,0.05); height: 100%; margin-bottom: 15px;
    }
    .info-card h4 { color: var(--main-blue); margin-bottom: 8px; font-weight: 700; }
    
    /* Botões */
    .stButton>button {
        background-color: var(--main-blue); color: white; border-radius: 8px;
        font-weight: 600; height: 3em; width: 100%; border: none; transition: all 0.3s;
    }
    .stButton>button:hover { background-color: #003a6e; transform: scale(1.01); }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES UTILITÁRIAS ---
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

def limpar_markdown(texto):
    """Limpa formatação para o WORD (Mantém emojis, tira negrito markdown)"""
    if not texto: return ""
    texto = texto.replace('**', '').replace('__', '')
    texto = texto.replace('### ', '').replace('## ', '').replace('# ', '')
    return texto

def limpar_para_pdf(texto):
    """Limpa formatação para o PDF (REMOVE EMOJIS e Markdown)"""
    if not texto: return ""
    # 1. Remove Markdown
    texto = texto.replace('**', '').replace('__', '')
    texto = texto.replace('### ', '').replace('## ', '').replace('# ', '')
    texto = texto.replace('* ', '• ')
    
    # 2. Remove Emojis (Regex para tirar caracteres fora do padrão Latin-1)
    # Isso evita os "???" no PDF
    texto = re.sub(r'[^\x00-\x7F\xA0-\xFF]', '', texto) 
    
    return texto

# --- INTELIGÊNCIA (DEEPSEEK V3) ---
def consultar_ia(api_key, dados, contexto_pdf=""):
    if not api_key: return None, "⚠️ A chave de API não foi detectada."
    try:
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        prompt_sistema = """
        Você é um Especialista em Inclusão Escolar.
        Base: LBI 13.146 + Neurociência.
        Se houver laudo anexo, use-o.
        """
        
        contexto_extra = f"\n📄 RESUMO DO LAUDO ANEXADO:\n{contexto_pdf[:3000]}" if contexto_pdf else ""
        
        prompt_usuario = f"""
        Aluno: {dados['nome']} ({dados['serie']})
        Diag: {dados['diagnostico']}
        Hiperfoco: {dados['hiperfoco']}
        
        {contexto_extra}
        
        Barreiras: {', '.join(dados['b_sensorial'] + dados['b_cognitiva'] + dados['b_social'])}
        Estratégias: {', '.join(dados['estrategias_acesso'] + dados['estrategias_curriculo'])}
        
        GERE UM PARECER TÉCNICO ESTRUTURADO (Sem usar Markdown):
        1. Conexão Neural (Uso do Hiperfoco).
        2. Análise do Contexto/Laudo.
        3. Sugestões Práticas de Adaptação.
        """
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": prompt_sistema}, {"role": "user", "content": prompt_usuario}],
            temperature=0.7, stream=False
        )
        return response.choices[0].message.content, None
    except Exception as e:
        return None, f"Erro DeepSeek: {str(e)}"

# --- GERADOR PDF (GENÉRICO E LIMPO) ---
class PDF(FPDF):
    def header(self):
        # Tenta carregar logo (Genérica ou Arco se desejar, aqui deixei sem para ser genérico)
        # Se quiser logo, descomente a linha abaixo:
        # self.image('https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Arco_Educa%C3%A7%C3%A3o_logo.png/640px-Arco_Educa%C3%A7%C3%A3o_logo.png', x=10, y=8, w=30)
        
        self.set_font('Arial', 'B', 16)
        self.set_text_color(0, 78, 146) 
        self.cell(0, 10, 'PEI - PLANO DE ENSINO INDIVIDUALIZADO', 0, 1, 'C') # Centralizado
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
    pdf.multi_cell(0, 7, txt(f"Nome: {dados['nome']} | Série: {dados['serie']}\nDiagnóstico: {dados['diagnostico']}"))
    pdf.ln(3)

    # 2. Mapeamento
    pdf.set_font("Arial", 'B', 12); pdf.set_text_color(0, 78, 146)
    pdf.cell(0, 10, txt("2. MAPEAMENTO PEDAGÓGICO"), 0, 1)
    pdf.set_font("Arial", size=11); pdf.set_text_color(0)
    pdf.multi_cell(0, 7, txt(f"Hiperfoco: {dados['hiperfoco']}"))
    
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, txt("Barreiras Identificadas:"), 0, 1)
    pdf.set_font("Arial", size=10)
    
    # Limpa emojis das barreiras também (se houver)
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
        # AQUI ESTÁ A MÁGICA: Limpa emojis e markdown antes de ir para o PDF
        texto_limpo = limpar_para_pdf(dados['ia_sugestao'])
        
        pdf.set_font("Arial", 'B', 12); pdf.set_text_color(0, 78, 146)
        pdf.cell(0, 10, txt("4. PARECER DO ESPECIALISTA"), 0, 1)
        pdf.set_font("Arial", size=11); pdf.set_text_color(50)
        pdf.multi_cell(0, 6, txt(texto_limpo))

    pdf.ln(15)
    pdf.set_draw_color(0); pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    # Assinatura Genérica
    pdf.cell(0, 10, txt("Coordenação Pedagógica / Direção Escolar"), 0, 1, 'C')

    return pdf.output(dest='S').encode('latin-1')

# --- GERADOR DOCX ---
def gerar_docx_final(dados):
    doc = Document()
    style = doc.styles['Normal']; style.font.name = 'Arial'; style.font.size = Pt(11)
    
    titulo = doc.add_heading('PEI - PLANO DE ENSINO INDIVIDUALIZADO', 0)
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.add_paragraph('_' * 70)
    
    doc.add_heading('1. IDENTIFICAÇÃO', level=1)
    doc.add_paragraph(f"Nome: {dados['nome']} | Série: {dados['serie']}")
    doc.add_paragraph(f"Diagnóstico: {dados['diagnostico']}")
    if dados['historico']: doc.add_paragraph(f"Histórico: {dados['historico']}")
    if dados['familia']: doc.add_paragraph(f"Família: {dados['familia']}")

    doc.add_heading('2. ESTRATÉGIAS', level=1)
    doc.add_paragraph("Acesso: " + ', '.join(dados['estrategias_acesso']))
    doc.add_paragraph("Currículo: " + ', '.join(dados['estrategias_curriculo']))

    if dados['ia_sugestao']:
        doc.add_heading('3. CONSULTORIA ESPECIALISTA', level=1)
        # Word aceita emojis, então limpamos só o markdown
        texto_limpo = limpar_markdown(dados['ia_sugestao'])
        doc.add_paragraph(texto_limpo)
    
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

# --- SIDEBAR (CHAVE DE API) ---
with st.sidebar:
    # Logo pode ser mantida no app (visual), mas no PDF tiramos
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/c/ca/Arco_Educa%C3%A7%C3%A3o_logo.png/640px-Arco_Educa%C3%A7%C3%A3o_logo.png", width=140)
    
    if 'DEEPSEEK_API_KEY' in st.secrets:
        api_key = st.secrets['DEEPSEEK_API_KEY']
        st.success("✅ Chave Segura Ativada")
    else:
        api_key = st.text_input("Chave API DeepSeek:", type="password")
    
    st.markdown("---")
    st.info("Versão 7.3 | Multi-Escola")

# --- CABEÇALHO VISUAL ---
st.markdown("""
<div style="display: flex; align-items: center; padding: 15px 20px; background: linear-gradient(90deg, #F8FAFC 0%, #E3F2FD 100%); border-radius: 15px; border-left: 6px solid #004E92; box-shadow: 0 4px 6px rgba(0,0,0,0.05); margin-bottom: 25px;">
    <span style="font-size: 3rem; margin-right: 15px;">🧠</span>
    <div>
        <h1 style="color: #004E92; margin: 0; font-weight: 800; font-size: 2.2rem; letter-spacing: -1px; line-height: 1;">PEI 360º</h1>
        <p style="margin: 5px 0 0 0; color: #4A5568; font-weight: 500; font-size: 1rem;">
            Sistema de Inclusão Inteligente 
        </p>
    </div>
</div>
""", unsafe_allow_html=True)

abas = ["🏠 Início", "👤 Aluno (Upload)", "🔍 Mapeamento", "✅ Plano de Ação", "🤖 Assistente de IA", "🖨️ Documento"]
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

# 2. ALUNO (AGORA COM UPLOAD VISÍVEL)
with tab2:
    st.info("Preencha os dados básicos e anexe documentos anteriores.")
    c1, c2 = st.columns(2)
    st.session_state.dados['nome'] = c1.text_input("Nome do Estudante", st.session_state.dados['nome'], placeholder="Digite o nome completo")
    st.session_state.dados['serie'] = c2.selectbox("Série/Ano", ["Ed. Infantil", "1º Ano", "2º Ano", "3º Ano", "4º Ano", "5º Ano", "6º Ano", "7º Ano", "8º Ano", "9º Ano", "Ensino Médio"], index=None)
    
    st.markdown("---")
    c3, c4 = st.columns([1, 2])
    st.session_state.dados['tem_laudo'] = c3.checkbox("Possui Laudo Médico?")
    st.session_state.dados['diagnostico'] = c4.text_input("Diagnóstico ou Hipótese", st.session_state.dados['diagnostico'], placeholder="Ex: TEA, TDAH...")
    
    # --- ÁREA DE UPLOAD MOVIDA PARA CÁ ---
    st.write("")
    st.markdown("##### 📂 Anexar Laudo ou Relatório Anterior (PDF)")
    uploaded_file = st.file_uploader("Arraste o arquivo aqui para a IA ler", type="pdf", key="uploader_tab2")
    if uploaded_file is not None:
        texto_extraido = ler_pdf(uploaded_file)
        if texto_extraido:
            st.session_state.pdf_text = texto_extraido
            st.success("✅ Documento Lido com Sucesso! A IA usará estas informações.")
    # -------------------------------------
    
    st.markdown("---")
    st.markdown("#### 📝 Contexto")
    ch, cf = st.columns(2)
    st.session_state.dados['historico'] = ch.text_area("Histórico Escolar", st.session_state.dados['historico'])
    st.session_state.dados['familia'] = cf.text_area("Escuta da Família", st.session_state.dados['familia'])

# 3. MAPEAMENTO
with tab3:
    st.info("💡 Identifique as potências para superar as barreiras.")
    st.markdown("### 🚀 Potencialidades")
    c_pot1, c_pot2 = st.columns(2)
    st.session_state.dados['hiperfoco'] = c_pot1.text_input("Hiperfoco (Interesse)", placeholder="O que o aluno AMA?")
    st.session_state.dados['potencias'] = c_pot2.multiselect("Pontos Fortes", ["Memória Visual", "Tecnologia", "Artes/Desenho", "Oralidade", "Lógica", "Empatia"])
    
    st.markdown("---")
    st.markdown("### 🚧 Barreiras e Nível de Suporte")
    
    with st.expander("👁️ Sensorial e Físico", expanded=True):
        st.session_state.dados['b_sensorial'] = st.multiselect("Quais são as barreiras?", ["Hipersensibilidade", "Busca Sensorial", "Seletividade Alimentar", "Dificuldade Motora"], key="b_sens")
        st.session_state.dados['sup_sensorial'] = st.select_slider("Suporte Sensorial:", ["🟢 Autônomo", "🟡 Monitorado", "🟠 Substancial", "🔴 Muito Substancial"], value="🟡 Monitorado", key="s_sens")

    with st.expander("🧠 Cognitivo e Aprendizagem"):
        st.session_state.dados['b_cognitiva'] = st.multiselect("Quais são as barreiras?", ["Atenção Dispersa", "Memória Curta", "Rigidez", "Lentidão", "Abstração"], key="b_cog")
        st.session_state.dados['sup_cognitiva'] = st.select_slider("Suporte Cognitivo:", ["🟢 Autônomo", "🟡 Monitorado", "🟠 Substancial", "🔴 Muito Substancial"], value="🟡 Monitorado", key="s_cog")

    with st.expander("❤️ Social e Emocional"):
        st.session_state.dados['b_social'] = st.multiselect("Quais são as barreiras?", ["Isolamento", "Baixa Frustração", "Interpretação Literal", "Ansiedade"], key="b_soc")
        st.session_state.dados['sup_social'] = st.select_slider("Suporte Social:", ["🟢 Autônomo", "🟡 Monitorado", "🟠 Substancial", "🔴 Muito Substancial"], value="🟡 Monitorado", key="s_soc")

# 4. PLANO DE AÇÃO
with tab4:
    st.markdown("### ✅ Definição de Estratégias")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Adaptações de Acesso (Meio)**")
        st.session_state.dados['estrategias_acesso'] = st.multiselect("Recursos:", ["Tempo estendido", "Ledor/Escriba", "Material Ampliado", "Uso de Tablet", "Local Silencioso", "Pausas Ativas"])
    with c2:
        st.markdown("**Adaptações Curriculares (Fim)**")
        st.session_state.dados['estrategias_curriculo'] = st.multiselect("Estratégias:", ["Redução de Questões", "Prova Oral", "Mapa Mental", "Conteúdo Prioritário", "Atividade Prática"])

# 5. ASSISTENTE IA
with tab5:
    col_ia_left, col_ia_right = st.columns([1, 2])
    with col_ia_left:
        st.markdown("### 🤖 Olá, Parceiro Pedagógico!")
        st.markdown("""
        <div class="info-card" style="border-left: 5px solid #48BB78;">
        <p>Estou pronto para atuar como seu Consultor Sênior. Vou analisar o mapeamento, o histórico e o <b>laudo anexado (se houver)</b>.</p>
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

        st.write("")
        with st.expander("⚙️ Detalhes técnicos"):
            st.markdown(f"**Status Anexo:** {status_pdf}")

    with col_ia_right:
        st.markdown("### 💡 Parecer Técnico")
        if st.session_state.dados['ia_sugestao']:
            st.text_area("Sugestões do Assistente:", st.session_state.dados['ia_sugestao'], height=500)
        else:
            st.info("O resultado da análise aparecerá aqui.")

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