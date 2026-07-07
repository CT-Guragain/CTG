"""
app.py -- Local Network Troubleshooting Chatbot
Free / offline version: no API keys, runs entirely on your own machine
via Ollama. Companion project to the paid API-based version.

Run with:  streamlit run app.py
Requires Ollama running locally (see README.md for setup).
"""

import json
import os
import requests
import streamlit as st
import streamlit.components.v1 as components
from retriever import KnowledgeBaseRetriever

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_URL = f"{OLLAMA_HOST}/api/chat"
DEFAULT_MODEL = "llama3.2"

SYSTEM_PROMPT = """You are a senior network engineer assistant helping troubleshoot
network issues (routing, switching, VPN, wireless, DNS, DHCP, and related protocols).
Use the CONTEXT below, which comes from a curated internal knowledge base, as your
primary source of truth. If the context doesn't cover the question, say so plainly
and then use general networking knowledge, clearly marking it as a general suggestion
rather than a verified internal procedure. Keep answers structured as numbered,
actionable steps, the way a real troubleshooting runbook would."""

st.set_page_config(page_title="Network Troubleshooter (Local)", page_icon=":globe_with_meridians:", layout="wide")

# ---------- White / blue themed CSS ----------
st.markdown("""
<style>
.stApp { background-color: #f4f8fc; color: #10253e; }
[data-testid="stSidebar"] { background-color: #eaf2fb; border-right: 1px solid #cfe0f2; }
.stChatMessage { background-color: #ffffff; border: 1px solid #d6e6f7; border-radius: 10px; }
h1, h2, h3 { color: #1d4ed8; font-family: 'Segoe UI', sans-serif; }
.stButton>button { background-color: #2563eb; color: white; border-radius: 6px; border: none; }
.stButton>button:hover { background-color: #1d4ed8; }
input, textarea { background-color: #ffffff !important; color: #10253e !important; border: 1px solid #93c5fd !important; }
[data-testid="stChatInput"] textarea { background-color: #ffffff !important; color: #10253e !important; }
[data-testid="stChatInput"] { background-color: #ffffff !important; }
[data-baseweb="input"] input { color: #10253e !important; }
.match-box { background:#eaf2fb; border-left:3px solid #2563eb; padding:8px 12px; margin-bottom:6px; font-size:13px; color:#10253e; }
</style>
""", unsafe_allow_html=True)

# ---------- Header with live ticking clock ----------
header_col1, header_col2 = st.columns([4, 1])
with header_col1:
    st.title("Network Troubleshooter — Local Edition")
    st.caption("Runs fully offline with Ollama. No API key. No usage cost. Every exchange trains the knowledge base.")
with header_col2:
    components.html("""
    <div style="text-align:right; font-family:'Segoe UI',sans-serif; color:#2563eb; font-size:20px; padding-top:10px;" id="clock"></div>
    <script>
    function tick() {
        const now = new Date();
        document.getElementById("clock").innerText = now.toLocaleTimeString();
    }
    tick();
    setInterval(tick, 1000);
    </script>
    """, height=50)

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Settings")
    model_name = st.text_input("Ollama model", value=DEFAULT_MODEL,
                                help="Must already be pulled: `ollama pull llama3.2`")
    top_k = st.slider("Knowledge base matches to use", 1, 5, 3)
    auto_learn = st.checkbox("Auto-learn from every conversation", value=True,
                              help="If on, every question and answer is automatically added to the knowledge base.")
    st.markdown("---")
    st.subheader("Add a curated entry")
    with st.form("add_kb_form", clear_on_submit=True):
        new_category = st.text_input("Category (e.g. DNS, BGP, IPsec)")
        new_issue = st.text_input("Issue title")
        new_symptoms = st.text_area("Symptoms", height=70)
        new_solution = st.text_area("Solution steps", height=100)
        submitted = st.form_submit_button("Save to knowledge base")
        if submitted and new_issue and new_solution:
            entry = st.session_state.retriever.add_entry(
                new_category or "General", new_issue, new_symptoms, new_solution
            )
            st.success(f"Saved as {entry['id']}. It's searchable immediately.")

# ---------- State ----------
if "retriever" not in st.session_state:
    st.session_state.retriever = KnowledgeBaseRetriever("knowledge_base.json")
if "messages" not in st.session_state:
    st.session_state.messages = []


def call_ollama(model: str, messages: list) -> str:
    payload = {"model": model, "messages": messages, "stream": False}
    resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()["message"]["content"]


# ---------- Render history ----------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------- Chat input ----------
user_input = st.chat_input("Describe the network issue you're seeing...")

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    matches = st.session_state.retriever.search(user_input, top_k=top_k)

    context_text = "\n\n".join(
        f"[{m['id']}] {m['category']} -- {m['issue']}\n"
        f"Symptoms: {m['symptoms']}\nSolution: {m['solution']}"
        for m in matches
    ) or "No matching internal knowledge base entries found for this query."

    with st.expander(f"Knowledge base matches used ({len(matches)})", expanded=False):
        if matches:
            for m in matches:
                st.markdown(
                    f"<div class='match-box'><b>{m['category']}</b> — {m['issue']} "
                    f"(score {m['score']})</div>", unsafe_allow_html=True
                )
        else:
            st.write("None -- answering from general knowledge only.")

    chat_payload = [
        {"role": "system", "content": f"{SYSTEM_PROMPT}\n\nCONTEXT:\n{context_text}"},
        *[{"role": m["role"], "content": m["content"]} for m in st.session_state.messages],
    ]

    with st.chat_message("assistant"):
        with st.spinner("Thinking locally..."):
            try:
                answer = call_ollama(model_name, chat_payload)
            except requests.exceptions.ConnectionError:
                answer = (
                    "Could not reach Ollama at localhost:11434. "
                    "Make sure Ollama is installed and running (`ollama serve`), "
                    f"and the model is pulled (`ollama pull {model_name}`)."
                )
        st.markdown(answer)
        if auto_learn:
            st.caption("📘 learned from this exchange")

    st.session_state.messages.append({"role": "assistant", "content": answer})

    if auto_learn:
        st.session_state.retriever.add_entry(
            category="From chat",
            issue=user_input[:80],
            symptoms=user_input,
            solution=answer,
        )