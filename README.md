# Network Troubleshooter -- Local Edition

A free, fully offline companion to the paid API-based network troubleshooting
chatbot. No API key, no per-message cost -- runs entirely on your own machine
using a local LLM through **Ollama**.

## Why this isn't "training a model" -- and why that's the right call

Training an LLM from scratch, or even fine-tuning one, needs large GPU
clusters and huge datasets -- not realistic for a solo portfolio project.
What real companies do instead for a support/troubleshooting bot is
**RAG (Retrieval-Augmented Generation)**:

1. You keep a knowledge base of real troubleshooting cases (`knowledge_base.json`).
2. When someone asks a question, the app searches that file for the closest
   matching cases (`retriever.py`, using TF-IDF -- fast, no downloads needed).
3. The matched cases are handed to a small local LLM (via Ollama) along with
   the question, so it answers grounded in *your* knowledge, not just
   whatever it learned generically.
4. You (or the app's "save exchange" button) can append new cases back into
   the JSON file, so the bot's knowledge grows from real conversations.

This is genuinely what "training the AI with your knowledge" means in
production systems like this -- it's also far more maintainable than
fine-tuning, because updating knowledge is just editing a JSON file, no
retraining required.

**If you later want true fine-tuning** (e.g. to also change the model's
tone or reasoning style, not just its knowledge), the next step up is
LoRA fine-tuning on top of an open model like Llama 3.2 using a tool
like Unsloth or Axolotl -- worth exploring once this RAG version is solid
and you have a large dataset of real Q&A pairs collected from actual use.

## What to actually "train" (i.e. what to put in the knowledge base)

Structure entries by protocol/technology, the same way you already think
about FortiGate/AD/Sangfor work. Good categories to build out, based on
what you already work with:

- DNS, DHCP, ARP (layer 2/3 basics)
- VLAN trunking, STP loops
- OSPF, BGP (routing protocols)
- IPsec VPN (Phase 1 / Phase 2 failures -- you already have real FortiGate experience here)
- SD-WAN / dual-ISP failover issues
- NAT / port forwarding
- MTU / fragmentation ("works with ping but not big transfers")
- Asymmetric routing
- Wireless throughput issues
- Active Directory / GPO issues (from your KUKL AD project -- huge asset, real cases)
- Sangfor HCI specific issues (from your SCP lab work)

The starter `knowledge_base.json` has 15 sample entries across most of
these. Replace and expand them with your **actual real incidents** --
that's what will make this stand out in a portfolio: it's not generic
internet advice, it's cases you've personally solved (KUKL AD, FortiGate
HA, Sangfor labs, etc.), scrubbed of anything confidential.

## Requirements

| Tool | Needed? | Why |
|---|---|---|
| Git | Yes | Version control + pushing to GitHub |
| Python 3.10+ | Yes | Runs the Streamlit app |
| Ollama | Yes | Runs the LLM locally, free, no API key |
| Docker | Optional | Makes it portable/deployable anywhere consistently -- you already used this pattern in your paid chatbot project |

You do **not** need a GPU. Small models like `llama3.2:3b` or `phi3.5`
run fine on a normal laptop CPU (slower, but workable for a demo/portfolio).

## Setup (without Docker -- fastest way to try it)

```bash
# 1. Install Ollama (one-time, does the actual LLM hosting)
# Linux:
curl -fsSL https://ollama.com/install.sh | sh
# Windows/Mac: download from https://ollama.com/download

# 2. Pull a small local model
ollama pull llama3.2

# 3. Start Ollama's server (often starts automatically after install)
ollama serve

# 4. In a new terminal, set up the Python side
cd network-troubleshooter-local
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 5. Run the app
streamlit run app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

## Setup (with Docker -- closer to a real deployment)

```bash
docker compose up --build
```

This starts two containers: `ollama` (the model server) and `app` (the
Streamlit UI), networked together. First run, pull a model into the
running Ollama container once:

```bash
docker exec -it ollama ollama pull llama3.2
```

## Pushing this to GitHub (git is genuinely enough)

```bash
cd network-troubleshooter-local
git init
git add .
git commit -m "Initial commit: local RAG-based network troubleshooting chatbot"
git branch -M main
git remote add origin https://github.com/CT-Guragain/network-troubleshooter-local.git
git push -u origin main
```

Add a short description on the GitHub repo page mentioning it's the free/
local companion to your API-based project -- that pairing (paid, cloud
version + free, local version) is a genuinely good portfolio story: it
shows you understand both sides of the cost/architecture trade-off, not
just "I called an API."

## Roadmap once your virtual card is active

Swap `call_ollama()` in `app.py` for a call to the Anthropic API (or
whichever provider), keeping the exact same retriever + knowledge base.
Because the RAG layer is provider-agnostic, this becomes a small,
contained change rather than a rewrite -- and at that point this repo
can either merge into your main `Net_troubleshooting-chatbot` project as
an "offline mode" toggle, or stay standalone as the free public version.

## Project structure

```
network-troubleshooter-local/
├── app.py                 # Streamlit UI + chat loop + save-to-KB flow
├── retriever.py            # TF-IDF search over the knowledge base
├── knowledge_base.json     # Your troubleshooting cases (edit/expand this)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml       # app + ollama, networked together
└── README.md
```
