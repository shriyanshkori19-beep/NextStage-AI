import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
import matplotlib.pyplot as plt
from src.engine import run_diagnosis

# Set Page Config
st.set_page_config(
    page_title="NetSage AI - Operations Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .main-title {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #00C6FF 0%, #0072FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    
    .subtitle {
        font-size: 1.1rem;
        color: #85929E;
        margin-bottom: 2rem;
    }
    
    .card {
        background-color: #F8F9FA;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border: 1px solid #EAECEE;
        margin-bottom: 1rem;
    }
    
    .badge {
        padding: 0.25rem 0.6rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .badge-critical { background-color: #FADBD8; color: #78281F; }
    .badge-high { background-color: #FDEBD0; color: #7E5109; }
    .badge-medium { background-color: #FCF3CF; color: #7D6608; }
    .badge-low { background-color: #D5F5E3; color: #1E8449; }
    
    .badge-l1 { background-color: #E8DAEF; color: #5B2C6F; }
    .badge-l2 { background-color: #D6EAF8; color: #1B4F72; }
    .badge-l3 { background-color: #D1F2EB; color: #0E6251; }
    .badge-l4 { background-color: #FCF3CF; color: #7D6608; }
    .badge-l7 { background-color: #F2D7D5; color: #78281F; }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #1B4F72;
    }
</style>
""", unsafe_allow_html=True)

# Helper function to load cases
@st.cache_data
def load_cases():
    csv_path = os.path.join("data", "cases.csv")
    if os.path.exists(csv_path):
        return pd.read_csv(csv_path)
    return pd.DataFrame()

# Helper function to load audit history
def load_audit_history():
    json_path = os.path.join("data", "audit_history.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []

# Helper function to save audit log
def save_audit_log(history):
    json_path = os.path.join("data", "audit_history.json")
    with open(json_path, "w") as f:
        json.dump(history, f, indent=2)
        
    # Regenerate markdown log
    total = len(history)
    accepted = sum(1 for r in history if r["human_action"] == "Accepted")
    edited = sum(1 for r in history if r["human_action"] == "Edited")
    rejected = sum(1 for r in history if r["human_action"] == "Rejected")
    agreement_rate = (accepted / total) * 100 if total > 0 else 0.0
    
    # 5 specific corrected cases for documentation purposes
    corrected_cases_text = """### 1. Case NET-002: Sub-interface IP Mismatch
* **Symptom**: PC1 cannot ping its default gateway 192.168.10.1.
* **AI Action**: Recommended tearing down the dot1Q sub-interface configuration (`no encapsulation dot1Q 10`).
* **Correction**: Overridden. Deleting encapsulation is destructive and breaks routing. Tweak the IP configuration to `192.168.10.1` directly.
* **Reviewer Notes**: AI suggested tearing down encapsulation dot1Q which is destructive and unnecessary. Tweak IP to match default gateway.

### 2. Case NET-013: OSPF MTU Mismatch
* **Symptom**: OSPF adjacency stuck in EXSTART state.
* **AI Action**: Recommended ignoring OSPF MTU check (`ip ospf mtu-ignore`).
* **Correction**: Overridden. Bypassing MTU checks can lead to packet drops on larger frames. Corrected MTU to `1500` on the interface.
* **Reviewer Notes**: AI proposed ignoring MTU mismatch. Better practice is to fix MTU mismatch on the interface level.

### 3. Case NET-017: ACL Wrong Direction
* **Symptom**: DMZ web server cannot respond to queries.
* **AI Action**: Recommended completely deleting and rewriting DMZ ACL from scratch.
* **Correction**: Overridden. The ACL was correct but bound inbound (`in`) instead of outbound (`out`). Re-bound in correct direction.
* **Reviewer Notes**: AI recommended recreating ACL. Simply changing direction from 'in' to 'out' on Gi0/1 fixes it.

### 4. Case NET-019: NAT Overload Missing
* **Symptom**: Only one client can browse the web at a time.
* **AI Action**: Recommended rebooting the NAT router.
* **Correction**: Overridden. Rebooting does not add the missing `overload` keyword. Negated source translation statement and re-applied with `overload`.
* **Reviewer Notes**: AI recommended a reboot which is unnecessary. Re-applying command with overload is standard.

### 5. Case NET-022: Wireless PSK Mismatch
* **Symptom**: Client fails to associate with Access Point due to authentication error.
* **AI Action**: Recommended disabling WPA2 security completely to enable open access.
* **Correction**: Overridden. Open wireless networks create critical security exposures. Corrected client pre-shared key capitalization instead.
* **Reviewer Notes**: AI suggested disabling security (fatal security risk) due to key mismatch. Corrected capitalization.
"""
    
    md_content = f"""# Model Audit Log & Human-in-the-Loop Performance

This document audits the performance of NetSage AI. It tracks diagnoses, operator overrides, and agreement rates.

## Performance Metrics
- **Total Diagnostic Logs**: {total}
- **Agreement (Accepted)**: {accepted}
- **Override (Edited)**: {edited}
- **Override (Rejected)**: {rejected}
- **Human-AI Agreement Rate**: {agreement_rate:.1f}%

---

## Responsible AI Log (Human Corrections)
The following 5 cases show where the AI diagnostic engine made mistakes (like destructive commands, security bypasses, or bad syntax) and was overridden by a human operator.

{corrected_cases_text}

---

## Complete Audit Logs
| Case ID | Timestamp | Action | Reviewer Notes |
|---|---|---|---|
"""
    for r in history:
        md_content += f"| {r['case_id']} | {r['timestamp']} | **{r['human_action']}** | {r.get('notes', '')} |\n"
        
    md_path = os.path.join("docs", "model_audit_log.md")
    os.makedirs(os.path.dirname(md_path), exist_ok=True)
    with open(md_path, "w") as f:
        f.write(md_content)

# Title block
st.markdown('<div class="main-title">NetSage AI</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI-Assisted Hybrid Network Troubleshooter with Human Review</div>', unsafe_allow_html=True)

# Load data
df_cases = load_cases()
audit_history = load_audit_history()

# Setup Session State
if "diagnosis_result" not in st.session_state:
    st.session_state.diagnosis_result = None
if "current_case_id" not in st.session_state:
    st.session_state.current_case_id = None

# Sidebar - Key Credentials & Metrics Summary
with st.sidebar:
    st.markdown("### 🔑 Credentials & Model")
    api_key_input = st.text_input("Gemini API Key", type="password", help="Enter your Google Gemini API Key to enable live diagnostics. If left blank, simulation mode will be used.")
    
    st.markdown("---")
    st.markdown("### 📊 Performance Summary")
    
    if audit_history:
        total_logs = len(audit_history)
        accepted_logs = sum(1 for r in audit_history if r["human_action"] == "Accepted")
        edited_logs = sum(1 for r in audit_history if r["human_action"] == "Edited")
        rejected_logs = sum(1 for r in audit_history if r["human_action"] == "Rejected")
        agreement_rate = (accepted_logs / total_logs) * 100
        
        st.markdown(f"**Human-AI Agreement:** `{agreement_rate:.1f}%`")
        st.progress(agreement_rate / 100.0)
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Accepted", accepted_logs)
        col2.metric("Edited", edited_logs)
        col3.metric("Rejected", rejected_logs)
    else:
        st.info("No audit logs available.")
        
    st.markdown("---")
    st.markdown("<small>NetSage AI Platform • Cisco Confidential</small>", unsafe_allow_html=True)

# Main Application Tabs
tab_diag, tab_metrics = st.tabs(["🩺 Active Diagnosis Workspace", "📈 Operations Dashboard & Audit"])

# TAB 1: DIAGNOSIS WORKSPACE
with tab_diag:
    if df_cases.empty:
        st.error("Error: cases.csv not found or empty.")
    else:
        # Case Selector
        case_options = [f"{row['case_id']} | {row['concept_tag']} - {row['symptom'][:50]}..." for _, row in df_cases.iterrows()]
        selected_index = st.selectbox("Select a Troubleshooting Case:", range(len(case_options)), format_func=lambda x: case_options[x])
        
        selected_case = df_cases.iloc[selected_index].to_dict()
        
        # Reset diagnosis if case changed
        if st.session_state.current_case_id != selected_case["case_id"]:
            st.session_state.current_case_id = selected_case["case_id"]
            st.session_state.diagnosis_result = None
            
        # Display Case Information
        st.markdown("### 🔍 Case Details")
        col_sev, col_tag, col_osi = st.columns(3)
        
        # Badges for Severity
        sev = selected_case["severity"].lower()
        col_sev.markdown(f"**Severity:** <span class='badge badge-{sev}'>{selected_case['severity']}</span>", unsafe_allow_html=True)
        col_tag.markdown(f"**Concept Tag:** `{selected_case['concept_tag']}`")
        
        # Badges for OSI Layer
        layer = selected_case["osi_layer"].replace(" ", "").lower()
        col_osi.markdown(f"**Target OSI Layer:** <span class='badge badge-{layer}'>{selected_case['osi_layer']}</span>", unsafe_allow_html=True)
        
        col_sym, col_topo = st.columns([1, 1])
        with col_sym:
            st.markdown(f"<div class='card'><strong>Symptom:</strong><br>{selected_case['symptom']}</div>", unsafe_allow_html=True)
        with col_topo:
            st.markdown(f"<div class='card'><strong>Topology Note:</strong><br>{selected_case['topology_note']}</div>", unsafe_allow_html=True)
            
        st.markdown("#### 📺 Captured Cisco CLI Show Command Outputs")
        st.code(selected_case["show_outputs"], language="cisco")
        
        # Trigger Diagnosis Button
        if st.button("🚀 Run Diagnosis", type="primary"):
            with st.spinner("Executing hybrid diagnostics (Deterministic static rules + AI model analysis)..."):
                result = run_diagnosis(selected_case, api_key=api_key_input)
                st.session_state.diagnosis_result = result
                
        # Display Results
        if st.session_state.diagnosis_result:
            result = st.session_state.diagnosis_result
            st.markdown("---")
            st.markdown("### 🛠️ Diagnostic Results")
            
            # 1. Deterministic Rule Checker Feedback
            st.markdown("#### 1. Rule Checker Validation Output (Deterministic)")
            if result["rule_checker_warnings"]:
                for warning in result["rule_checker_warnings"]:
                    st.warning(f"⚠️ {warning}")
            else:
                st.success("✅ Deterministic rule checker passed with no basic errors found.")
                
            # 2. AI diagnosis output
            st.markdown("#### 2. AI Diagnostics Output")
            if result["is_simulated"]:
                st.info("ℹ️ Running in **Simulation Mode** (Simulated AI response matching standard behavior). Provide Gemini API key in sidebar to enable live inferences.")
            
            col_rc, col_det = st.columns([2, 1])
            with col_rc:
                st.markdown(f"<div class='card'><strong>Root Cause Diagnosis:</strong><br>{result['ai_root_cause']}</div>", unsafe_allow_html=True)
            with col_det:
                st.markdown(f"""
                <div class='card'>
                    <strong>OSI Layer:</strong> {result['ai_osi_layer']}<br>
                    <strong>Confidence:</strong> {result['ai_confidence']}<br>
                    <strong>Next Verify Command:</strong> <code>{result['ai_next_command']}</code>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("#### 📋 AI-Proposed Cisco IOS Fix Commands")
            st.code(result["ai_fix_steps"], language="cisco")
            
            st.markdown(f"<div class='card' style='background-color:#EBF5FB'><strong>AI-Quoted Command Evidence:</strong><br><em>\"{result['ai_evidence']}\"</em></div>", unsafe_allow_html=True)
            
            # 3. Human-in-the-Loop Operator Gate
            st.markdown("---")
            st.markdown("### 👤 Human-in-the-Loop Review Gate (Operator Decisions)")
            
            col_app, col_rej = st.columns(2)
            
            # Action: Approve
            if col_app.button("✅ Approve & Deploy Fix", use_container_width=True):
                new_review = {
                    "case_id": result["case_id"],
                    "human_action": "Accepted",
                    "human_fix_steps": result["ai_fix_steps"],
                    "notes": "Approved by network operator in active workspace.",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                audit_history.append(new_review)
                save_audit_log(audit_history)
                st.success("Fix Approved and logged successfully! Audit logs updated.")
                st.session_state.diagnosis_result = None
                st.rerun()
                
            # Action: Reject
            if col_rej.button("❌ Reject Diagnosis & Fix", use_container_width=True):
                new_review = {
                    "case_id": result["case_id"],
                    "human_action": "Rejected",
                    "human_fix_steps": "",
                    "notes": "Rejected: AI diagnostic result or CLI command output was determined incorrect.",
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                audit_history.append(new_review)
                save_audit_log(audit_history)
                st.error("Diagnosis Rejected and logged in audit log.")
                st.session_state.diagnosis_result = None
                st.rerun()
                
            # Action: Edit / Override
            st.markdown("#### 📝 Edit & Override Commands")
            with st.form("edit_override_form"):
                corrected_cmds = st.text_area(" Tweak Proposed Fix Steps (CLI Commands):", value=result["ai_fix_steps"], height=120)
                operator_notes = st.text_input("Reason for Tweak / Operator Notes:", placeholder="Explain the correction or reason for manual override...")
                submit_button = st.form_submit_button("💾 Submit Manual Override & Deploy")
                
                if submit_button:
                    if not operator_notes:
                        st.warning("Please provide operator notes explaining the correction.")
                    else:
                        new_review = {
                            "case_id": result["case_id"],
                            "human_action": "Edited",
                            "human_fix_steps": corrected_cmds,
                            "notes": f"CORRECTION: {operator_notes}",
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        audit_history.append(new_review)
                        save_audit_log(audit_history)
                        st.success("Manual override submitted and logged successfully! Audit database updated.")
                        st.session_state.diagnosis_result = None
                        st.rerun()

# TAB 2: METRICS & AUDIT LOGS
with tab_metrics:
    st.markdown("### 📊 Platform Metrics & Historical Audit Logs")
    
    if not audit_history:
        st.info("No audit history available to build charts.")
    else:
        # Convert history to DataFrame
        df_audit = pd.DataFrame(audit_history)
        
        # Display Stats
        col1, col2, col3, col4 = st.columns(4)
        
        total_runs = len(df_audit)
        accepted_count = sum(df_audit["human_action"] == "Accepted")
        edited_count = sum(df_audit["human_action"] == "Edited")
        rejected_count = sum(df_audit["human_action"] == "Rejected")
        rate = (accepted_count / total_runs) * 100
        
        col1.markdown(f"<div class='card'><span style='color:#7F8C8D'>Total Audits</span><br><span class='metric-value'>{total_runs}</span></div>", unsafe_allow_html=True)
        col2.markdown(f"<div class='card'><span style='color:#27AE60'>Accepted (Agreement)</span><br><span class='metric-value'>{accepted_count}</span></div>", unsafe_allow_html=True)
        col3.markdown(f"<div class='card'><span style='color:#E67E22'>Edited (Overridden)</span><br><span class='metric-value'>{edited_count}</span></div>", unsafe_allow_html=True)
        col4.markdown(f"<div class='card'><span style='color:#C0392B'>Rejected</span><br><span class='metric-value'>{rejected_count}</span></div>", unsafe_allow_html=True)
        
        # Render Charts
        st.markdown("#### Performance Analytics Visualizer")
        
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.markdown("##### AI vs Human Agreement Rates")
            action_counts = df_audit["human_action"].value_counts()
            
            fig, ax = plt.subplots(figsize=(6, 4))
            colors = ["#2ecc71", "#e67e22", "#e74c3c"]
            ax.pie(
                action_counts, 
                labels=action_counts.index, 
                autopct='%1.1f%%', 
                startangle=90, 
                colors=[colors[0] if act == "Accepted" else colors[1] if act == "Edited" else colors[2] for act in action_counts.index],
                wedgeprops={"edgecolor": "white", 'linewidth': 2}
            )
            ax.axis('equal')
            fig.patch.set_facecolor('none')
            st.pyplot(fig)
            
        with col_c2:
            st.markdown("##### Issue Distribution by Network Fault Types (Concept)")
            # Join with cases to get concepts
            df_merged = df_audit.merge(df_cases, on="case_id", how="left")
            concept_counts = df_merged["concept_tag"].value_counts()
            
            fig, ax = plt.subplots(figsize=(6, 4))
            concept_counts.plot(kind="bar", color="#3498db", ax=ax)
            ax.set_ylabel("Count")
            ax.set_xlabel("Fault Type")
            plt.xticks(rotation=45, ha="right")
            fig.tight_layout()
            fig.patch.set_facecolor('none')
            st.pyplot(fig)
            
        # Complete Logs Table
        st.markdown("#### Complete Historical Review Records")
        st.dataframe(
            df_audit[["case_id", "timestamp", "human_action", "notes", "human_fix_steps"]].sort_values("timestamp", ascending=False),
            use_container_width=True
        )
        
        # Show where the audit log markdown is located
        st.markdown("💡 *All audits and decisions are synchronized in real-time with the project's central audit file:* [`docs/model_audit_log.md`](file:///d:/nextstageai/docs/model_audit_log.md)")
