import os
import uuid
import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

st.set_page_config(page_title="Ticketing System", layout="wide")

# --- CONEXIÓN A LAKEBASE (PostgreSQL) ---
@st.cache_resource
def get_engine():
    # Obtiene las variables de entorno de Lakebase/Databricks Apps
    db_user = os.environ.get("LAKEBASE_USER", "postgres")
    db_password = os.environ.get("LAKEBASE_PASSWORD", "postgres")
    db_host = os.environ.get("LAKEBASE_HOST", "localhost")
    db_port = os.environ.get("LAKEBASE_PORT", "5432")
    db_name = os.environ.get("LAKEBASE_DATABASE", "postgres")
    
    connection_string = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    return create_engine(connection_string)

engine = get_engine()

st.title("🎟️ Sistema de Soporte - Lakebase App")

# --- BARRA LATERAL: Crear Ticket ---
st.sidebar.header("Crear Nuevo Ticket")
with st.sidebar.form("create_ticket_form", clear_on_submit=True):
    title = st.text_input("Título del Ticket")
    created_by = st.text_input("Tu Email / Usuario")
    initial_message = st.text_area("Descripción inicial")
    submit_ticket = st.form_submit_button("Crear Ticket")
    
    if submit_ticket and title and created_by and initial_message:
        ticket_id = f"t-{uuid.uuid4().hex[:6]}"
        message_id = f"m-{uuid.uuid4().hex[:6]}"
        
        with engine.begin() as conn:
            # Insertar Ticket
            conn.execute(
                text("INSERT INTO tickets (ticket_id, title, status, created_by) VALUES (:tid, :title, 'open', :cby)"),
                {"tid": ticket_id, "title": title, "cby": created_by}
            )
            # Insertar mensaje inicial
            conn.execute(
                text("INSERT INTO ticket_messages (message_id, ticket_id, message_text, author) VALUES (:mid, :tid, :msg, :author)"),
                {"mid": message_id, "tid": ticket_id, "msg": initial_message, "author": created_by}
            )
        st.sidebar.success(f"Ticket {ticket_id} creado con éxito.")
        st.rerun()

# --- VISTA PRINCIPAL: Consultar y Gestionar Tickets ---
with engine.connect() as conn:
    tickets_df = pd.read_sql_query("SELECT * FROM tickets ORDER BY created_at DESC", conn)

st.subheader("Tickets Registrados")

if tickets_df.empty:
    st.info("No hay tickets registrados en Lakebase.")
else:
    for _, row in tickets_df.iterrows():
        t_id = row['ticket_id']
        t_status = row['status']
        
        with st.expander(f"[{t_status.upper()}] {row['title']} (ID: {t_id}) - Creado por {row['created_by']}"):
            
            # Formulario para actualizar estado
            col1, col2 = st.columns([3, 1])
            with col1:
                new_status = st.selectbox(
                    "Estado actual:",
                    ["open", "in_progress", "resolved"],
                    index=["open", "in_progress", "resolved"].index(t_status) if t_status in ["open", "in_progress", "resolved"] else 0,
                    key=f"status_select_{t_id}"
                )
            with col2:
                if st.button("Actualizar Estado", key=f"btn_status_{t_id}"):
                    with engine.begin() as conn:
                        conn.execute(
                            text("UPDATE tickets SET status = :status WHERE ticket_id = :tid"),
                            {"status": new_status, "tid": t_id}
                        )
                    st.success("Estado actualizado")
                    st.rerun()
            
            st.divider()
            st.write("**Historial de Mensajes:**")
            
            # Cargar mensajes del ticket desde Lakebase
            with engine.connect() as conn:
                msgs_df = pd.read_sql_query(
                    text("SELECT author, message_text, created_at FROM ticket_messages WHERE ticket_id = :tid ORDER BY created_at ASC"),
                    conn,
                    params={"tid": t_id}
                )
            
            for _, mrow in msgs_df.iterrows():
                st.chat_message("user" if mrow['author'] == row['created_by'] else "assistant").write(
                    f"**{mrow['author']}** ({mrow['created_at']}):\n{mrow['message_text']}"
                )
            
            # Responder al ticket
            with st.form(f"reply_form_{t_id}", clear_on_submit=True):
                reply_author = st.text_input("Tu Email / Nombre", key=f"author_{t_id}")
                reply_text = st.text_area("Mensaje de respuesta", key=f"msg_{t_id}")
                submit_reply = st.form_submit_button("Enviar Respuesta")
                
                if submit_reply and reply_author and reply_text:
                    m_id = f"m-{uuid.uuid4().hex[:6]}"
                    with engine.begin() as conn:
                        conn.execute(
                            text("INSERT INTO ticket_messages (message_id, ticket_id, message_text, author) VALUES (:mid, :tid, :msg, :author)"),
                            {"mid": m_id, "tid": t_id, "msg": reply_text, "author": reply_author}
                        )
                    st.success("Mensaje agregado")
                    st.rerun()