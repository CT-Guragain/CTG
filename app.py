"""
app.py -- Local Network Troubleshooting Chatbot
Free / offline version: no API keys, runs entirely on your own machine
via Ollama. Built as a companion portfolio project to the paid
API-based Net_troubleshooting-chatbot.

Run with:  streamlit run app.py
Requires Ollama running locally (see README.md for setup).
"""

import json
import os
import requests
import streamlit as st
from retriever import KnowledgeBaseRetriever

# When running via plain `streamlit run app.py` on your own machine, Ollama
# is on localhost. When running inside docker-compose, the app container
# reaches Ollama through the service name "ollama" on the shared network --
# that's what OLLAMA_HOST is for (already set in docker-compose.yml).
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_URL = f"{OLLAMA_HOST}/api/chat"
DEFAULT_MODEL = "llama3.2"  # small enough to run on a normal laptop, no GPU required

SYSTEM_PROMPT = """You are a senior network engineer assistant helping troubleshoot
network issues (routing, switching, VPN, wireless, DNS, DHCP, and related protocols).
Use the CONTEXT below, which comes from a curated internal knowledge base, as your
primary source of truth. If the context doesn't cover the question, say so plainly
and then use general networking knowledge, clearly marking it as a general suggestion
rather than a verified internal procedure. Keep answers structured as numbered,
actionable steps, the way a real troubleshooting runbook would."""

st.set_page_config(page_title="Network Troubleshooter (Local)", page_icon=":globe_with_meridians:", layout="wide")

# ---------- Dark network-ops themed CSS ----------
st.markdown("""
<style>
.stApp { background-color: #0b0f14; color: #d6e4e5; }
[data-testid="stSidebar"] { background-color: #0f1720; }
.stChatMessage { background-color: #101820; border: 1px solid #1c2b30; border-radius: 8px; }
h1, h2, h3 { color: #2dd4bf; font-family: 'Courier New', monospace; }
.stButton>button { background-color: #0f766e; color: white; border-radius: 6px; border: none; }
.match-box { background:#0f1720; border-left:3px solid #2dd4bf; padding:8px 12px; margin-bottom:6px; font-size:13px; }
</style>
""", unsafe_allow_html=True)

st.title("Network Troubleshooter -- Local Edition")
st.caption("Runs fully offline with Ollama. No API key. No usage cost. Companion project to the paid API-powered version.")

# ---------- Sidebar ----------
with st.sidebar:
    st.header("Settings")
    model_name = st.text_input("Ollama model", value=DEFAULT_MODEL,
                                help="Must already be pulled: `ollama pull llama3.2`")
    top_k = st.slider("Knowledge base matches to use", 1, 5, 3)
    st.markdown("---")
    st.subheader("Add to knowledge base")
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
if "last_exchange" not in st.session_state:
    st.session_state.last_exchange = None


def call_ollama(model: str, messages: list) -> str:
    """Send the conversation to a locally running Ollama server and return
    the full text response. Ollama exposes an OpenAI-style REST API on
    localhost -- nothing leaves your machine."""
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

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.session_state.last_exchange = {"question": user_input, "answer": answer}

# ---------- Promote last exchange into the knowledge base ----------
if st.session_state.last_exchange:
    if st.button("Save this last exchange as a new knowledge base entry"):
        ex = st.session_state.last_exchange
        entry = st.session_state.retriever.add_entry(
            category="From chat",
            issue=ex["question"][:80],
            symptoms=ex["question"],
            solution=ex["answer"],
        )
        st.success(f"Saved as {entry['id']}. Future questions like this will retrieve it directly.")