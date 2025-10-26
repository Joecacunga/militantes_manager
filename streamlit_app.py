# streamlit_app.py — MPLA v4.6 (principal)
import streamlit as st
import os, base64
from utils_v4 import carregar_base_dados, guardar_base_dados, carregar_localidades, adicionar_militante, gerar_recibo_pdf_bytes, exportar_para_excel, importar_dados_excel, importar_dados_texto, atualizar_militante_por_cap, remover_por_cap, gerar_registro_interno_por_cap

st.set_page_config(page_title="MPLA — SISTEMA DE GESTÃO DE MILITANTES", layout="wide")
st.title("MPLA — SISTEMA DE GESTÃO DE MILITANTES")
st.write("MPLA — Servir o Povo e Fazer Angola Crescer")

base = carregar_base_dados()
localidades = carregar_localidades()

if 'nav' not in st.session_state:
    st.session_state['nav'] = "Bem-vindo"

if st.button("📋 MENU"):
    st.session_state['nav']="Menu Principal"
if st.sidebar.button("Menu Principal"):
    st.session_state['nav']="Menu Principal"

if st.session_state['nav']=="Menu Principal":
    c1,c2,c3 = st.columns(3)
    with c1:
        if st.button("Cadastrar Militante"):
            st.session_state['nav']="Formulário"
    with c2:
        if st.button("Base de Dados"):
            st.session_state['nav']="Base de Dados"
    with c3:
        if st.button("Gerar Recibo"):
            st.session_state['nav']="Recibos"

if st.session_state['nav']=="Formulário":
    st.header("Formulário de Registo")
    with st.form("f", clear_on_submit=False):
        primeiro = st.text_input("Nome(s) Próprio(s)")
        ultimo = st.text_input("Último Nome")
        cap = st.text_input("Nº CAP (Ex: CAP041)")
        telefone = st.text_input("Telefone")
        municipio = st.selectbox("Município", list(localidades.keys()) if localidades else [""])
        foto = st.camera_input("Tirar foto (opcional)")
        submitted = st.form_submit_button("Guardar")
        if submitted:
            registro = {'primeiro_nome':primeiro,'ultimo_nome':ultimo,'cap':cap.strip().upper(),'telefone':telefone,'municipio':municipio}
            if foto:
                registro['foto_b64']=base64.b64encode(foto.getbuffer()).decode('utf-8')
            base, ok, msg = adicionar_militante(base, registro)
            if ok:
                st.success(msg); guardar_base_dados(base); st.experimental_rerun()
            else:
                st.error(msg)

elif st.session_state['nav']=="Base de Dados":
    st.header("Base de Dados")
    st.write(base)
    cap_edit = st.text_input("Nº CAP para editar")
    if cap_edit:
        militantes=[m for m in base if m.get('cap','').upper()==cap_edit.strip().upper()]
        if militantes:
            m=militantes[0]
            with st.form("edit"):
                p=st.text_input("Nome",m.get('primeiro_nome',''))
                if st.form_submit_button("Aplicar"):
                    atualizar_militante_por_cap(base, cap_edit, {'primeiro_nome':p}); guardar_base_dados(base); st.experimental_rerun()

elif st.session_state['nav']=="Recibos":
    st.header("Recibos")
    if base:
        escolhas=[f"{m.get('primeiro_nome','')} {m.get('ultimo_nome','')} — {m.get('cap','')}" for m in base]
        sel=st.selectbox("Selecionar", escolhas)
        if st.button("Gerar Recibo"):
            idx=escolhas.index(sel); militante=base[idx]
            if not militante.get('registro_interno'): militante['registro_interno']=gerar_registro_interno_por_cap(base, militante.get('cap','')); guardar_base_dados(base)
            pdf=gerar_recibo_pdf_bytes(militante)
            st.download_button("Baixar PDF", data=pdf, file_name=f"Recibo_{militante.get('cap')}.pdf", mime='application/pdf')
else:
    st.write('Use o MENU para navegar.')
