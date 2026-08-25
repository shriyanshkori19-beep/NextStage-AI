# NetSage AI — AI-Assisted Hybrid Network Troubleshooter

NetSage AI is an intelligent network diagnostic platform that combines **deterministic rule-based checks** with **Gemini LLM-powered analysis** to troubleshoot Cisco Packet Tracer lab networks. A **Human-in-the-Loop (HITL)** Streamlit dashboard enables network engineers to review, edit, or reject AI-generated fixes before deployment.

---

## 📁 Project Structure

```
nextstageai/
├── data/
│   ├── cases.csv                  # 30 structured troubleshooting cases
│   ├── system_config.json         # Model configuration parameters
│   └── audit_history.json         # Persistent audit database (JSON)
├── prompts/
│   └── diagnose_prompt.md         # Structured prompt with few-shot examples
├── src/
│   ├── app.py                     # Streamlit Operations Dashboard
│   ├── checker.py                 # Deterministic rule engine (regex-based)
│   ├── engine.py                  # Hybrid diagnostic orchestrator (Gemini API)
│   ├── generate_cases.py          # Script to regenerate cases.csv
│   └── initialize_audit_log.py    # Script to regenerate audit log
├── docs/
│   └── model_audit_log.md         # Responsible AI audit log with metrics
├── tests/
│   └── verify_cases.py            # Automated verification test suite
└── README.md                      # This file
```

---

## 🚀 How to Run

### Prerequisites
- Python 3.10+
- pip

### 1. Clone the Repository
```bash
git clone [https://github.com/shriyanshkori19-beep/NextStage-AI.git](https://github.com/shriyanshkori19-beep/NextStage-AI.git)
cd NextStage-AI
```

### 2. Install Dependencies
```bash
pip install streamlit pandas python-dotenv matplotlib google-genai
```

### 3. Run Automated Tests
```bash
python tests/verify_cases.py
```

### 4. Launch the Streamlit Dashboard
```bash
python -m streamlit run src/app.py
```
Then open **http://localhost:8501** in your browser.

### 5. (Optional) Enable Live AI Diagnostics
Enter your **Gemini API Key** in the sidebar of the dashboard. Without a key, the system runs in **Simulation Mode** using pre-computed diagnostic outputs.

---

## 📊 Deliverables Summary

### 1. Dataset — `data/cases.csv`
30 structured cases covering 8 network fault categories:
- **VLAN**: Missing VLANs, trunk allowed VLAN mismatches, native VLAN mismatches
- **Gateway**: Interface down, IP mismatches, duplicate IPs
- **DHCP**: Pool exhaustion, missing helper-address, disabled service, wrong default-router
- **DNS**: Wrong DNS server IP, disabled DNS service, missing A records
- **Routing (OSPF)**: Missing network statements, area mismatches, MTU mismatches, missing default routes
- **ACL**: Unapplied ACLs, wrong direction, missing permit rules, overly permissive rules
- **NAT**: Missing inside/outside, missing overload, wrong ACL subnet, pool conflicts
- **Wireless**: SSID mismatches, PSK key case mismatches, DHCP exhaustion

### 2. Prompt Library — `prompts/diagnose_prompt.md`
Enforces structured JSON output containing:
- `root_cause`, `osi_layer`, `confidence`, `evidence`, `next_command`, `fix_steps`
- Includes 2 few-shot worked examples

### 3. Deterministic Checker — `src/checker.py`
Regex-based rule engine detecting 20+ configuration patterns including:
- Administratively down interfaces
- Duplicate IP addresses (config + ARP table)
- Subnet mask / MTU mismatches
- Missing VLANs, DHCP helpers, NAT designations, OSPF networks, default routes
- Wireless SSID and PSK mismatches

### 4. Streamlit Dashboard — `src/app.py`
Interactive operations dashboard with:
- **Case selector** with metadata badges (severity, OSI layer, concept tag)
- **Cisco CLI show output viewer**
- **Hybrid diagnostic engine** (static rules + AI analysis)
- **HITL decision gate**: Approve & Deploy, Edit & Override, or Reject
- **Real-time analytics**: Agreement rate, action distribution pie chart, fault type bar chart
- **Audit history table** synchronized with `data/audit_history.json`

### 5. Responsible AI Log — `docs/model_audit_log.md`
- **Human-AI Agreement Rate**: 76.7%
- **30 historical audit records**: 23 Accepted, 5 Edited, 2 Rejected
- **5 documented correction cases** where AI was overridden:
  1. NET-002: AI proposed destructive `no encapsulation` command
  2. NET-013: AI bypassed MTU fix with `ip ospf mtu-ignore`
  3. NET-017: AI recommended recreating entire ACL instead of changing direction
  4. NET-019: AI recommended rebooting router instead of adding `overload`
  5. NET-022: AI recommended disabling WPA2 security entirely

---

## 🏗️ Architecture

```
┌──────────────┐     ┌──────────────────┐     ┌───────────────────┐
│  cases.csv   │────▶│  checker.py      │────▶│  engine.py        │
│  (30 cases)  │     │  (Static Rules)  │     │  (Orchestrator)   │
└──────────────┘     └──────────────────┘     └────────┬──────────┘
                                                       │
                              ┌─────────────────┐      │
                              │ diagnose_prompt  │◀─────┤
                              │ (Few-shot LLM)   │      │
                              └─────────────────┘      │
                                                       ▼
                                              ┌────────────────┐
                                              │   Gemini API   │
                                              │ (or Simulation)│
                                              └────────┬───────┘
                                                       │
                                                       ▼
                                              ┌────────────────┐
                                              │   app.py       │
                                              │  (Streamlit    │
                                              │   Dashboard)   │
                                              └────────┬───────┘
                                                       │
                                          ┌────────────┼────────────┐
                                          ▼            ▼            ▼
                                     ✅ Approve   📝 Edit      ❌ Reject
                                          │            │            │
                                          └────────────┼────────────┘
                                                       ▼
                                              ┌────────────────┐
                                              │ audit_history  │
                                              │ .json + .md    │
                                              └────────────────┘
```

---

## 👤 Author
NetSage AI — Built for Next Stage AI Hackathon Submission
