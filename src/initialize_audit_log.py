import os
import json
from datetime import datetime

# 30 historical cases to populate the audit log
historical_reviews = [
    # 23 Accepted Cases
    {"case_id": "NET-001", "human_action": "Accepted", "human_fix_steps": "configure terminal\ninterface GigabitEthernet0/0.30\nno shutdown", "notes": "AI diagnosis was 100% correct.", "timestamp": "2026-08-25 10:15:00"},
    {"case_id": "NET-003", "human_action": "Accepted", "human_fix_steps": "configure terminal\nvlan 20\n name Sales\nexit", "notes": "VLAN was indeed missing from database.", "timestamp": "2026-08-25 10:18:00"},
    {"case_id": "NET-004", "human_action": "Accepted", "human_fix_steps": "configure terminal\ninterface GigabitEthernet0/1\n switchport trunk allowed vlan add 10", "notes": "Trunk configuration checked and fixed.", "timestamp": "2026-08-25 10:20:00"},
    {"case_id": "NET-005", "human_action": "Accepted", "human_fix_steps": "configure terminal\ninterface GigabitEthernet0/1\n switchport trunk native vlan 10", "notes": "Fixed native VLAN mismatch.", "timestamp": "2026-08-25 10:22:00"},
    {"case_id": "NET-006", "human_action": "Accepted", "human_fix_steps": "configure terminal\nip dhcp pool OFFICE_POOL\n network 192.168.1.0 255.255.255.0", "notes": "Confirmed pool was exhausted.", "timestamp": "2026-08-25 10:25:00"},
    {"case_id": "NET-007", "human_action": "Accepted", "human_fix_steps": "configure terminal\ninterface GigabitEthernet0/0.10\n ip helper-address 10.1.1.5", "notes": "DHCP relay configured.", "timestamp": "2026-08-25 10:28:00"},
    {"case_id": "NET-008", "human_action": "Accepted", "human_fix_steps": "configure terminal\nip dhcp service", "notes": "Enabled disabled service.", "timestamp": "2026-08-25 10:30:00"},
    {"case_id": "NET-009", "human_action": "Accepted", "human_fix_steps": "configure terminal\nip dhcp pool CLIENT_POOL\n no dns-server 192.168.1.100\n dns-server 192.168.1.10", "notes": "DNS server IP corrected.", "timestamp": "2026-08-25 10:35:00"},
    {"case_id": "NET-010", "human_action": "Accepted", "human_fix_steps": "# Enable DNS in server settings GUI", "notes": "DNS service turned on.", "timestamp": "2026-08-25 10:38:00"},
    {"case_id": "NET-011", "human_action": "Accepted", "human_fix_steps": "configure terminal\nrouter ospf 1\n network 192.168.30.0 0.0.0.255 area 0", "notes": "OSPF network added.", "timestamp": "2026-08-25 10:40:00"},
    {"case_id": "NET-012", "human_action": "Accepted", "human_fix_steps": "configure terminal\nrouter ospf 1\n no network 192.168.12.0 0.0.0.3 area 1\n network 192.168.12.0 0.0.0.3 area 0", "notes": "OSPF area mismatch fixed.", "timestamp": "2026-08-25 10:45:00"},
    {"case_id": "NET-014", "human_action": "Accepted", "human_fix_steps": "configure terminal\nip route 0.0.0.0 0.0.0.0 203.0.113.2", "notes": "Default route added.", "timestamp": "2026-08-25 10:48:00"},
    {"case_id": "NET-015", "human_action": "Accepted", "human_fix_steps": "configure terminal\ninterface GigabitEthernet0/0.40\n ip access-group GUEST_ACL in", "notes": "ACL applied successfully.", "timestamp": "2026-08-25 10:50:00"},
    {"case_id": "NET-016", "human_action": "Accepted", "human_fix_steps": "configure terminal\nip access-list extended OUTSIDE_ACL\n 5 permit udp any any eq 53", "notes": "DNS UDP 53 permitted.", "timestamp": "2026-08-25 10:55:00"},
    {"case_id": "NET-018", "human_action": "Accepted", "human_fix_steps": "configure terminal\ninterface GigabitEthernet0/0\n ip nat inside", "notes": "NAT inside config added.", "timestamp": "2026-08-25 11:00:00"},
    {"case_id": "NET-020", "human_action": "Accepted", "human_fix_steps": "configure terminal\nno access-list 10\naccess-list 10 permit 192.168.10.0 0.0.0.255", "notes": "NAT ACL subnet range corrected.", "timestamp": "2026-08-25 11:05:00"},
    {"case_id": "NET-021", "human_action": "Accepted", "human_fix_steps": "# Correct client SSID settings to Office_Wifi", "notes": "SSID mismatch fixed.", "timestamp": "2026-08-25 11:10:00"},
    {"case_id": "NET-023", "human_action": "Accepted", "human_fix_steps": "# Expand DHCP scope range on WLC", "notes": "IP scope expanded.", "timestamp": "2026-08-25 11:15:00"},
    {"case_id": "NET-024", "human_action": "Accepted", "human_fix_steps": "configure terminal\ninterface GigabitEthernet0/1\n ip address 192.168.10.1 255.255.255.0", "notes": "Duplicate IP address conflict resolved.", "timestamp": "2026-08-25 11:20:00"},
    {"case_id": "NET-025", "human_action": "Accepted", "human_fix_steps": "configure terminal\ninterface GigabitEthernet0/1\n ip address 10.10.10.2 255.255.255.0", "notes": "Mismatched mask resolved.", "timestamp": "2026-08-25 11:25:00"},
    {"case_id": "NET-026", "human_action": "Accepted", "human_fix_steps": "configure terminal\ninterface GigabitEthernet0/1\n no shutdown", "notes": "Brought up trunk port interface.", "timestamp": "2026-08-25 11:30:00"},
    {"case_id": "NET-028", "human_action": "Accepted", "human_fix_steps": "configure terminal\nip dhcp pool VLAN10_POOL\n no default-router 192.168.10.254\n default-router 192.168.10.1", "notes": "Default router IP in pool fixed.", "timestamp": "2026-08-25 11:35:00"},
    {"case_id": "NET-029", "human_action": "Accepted", "human_fix_steps": "# Add A record: database.internal.local -> 10.1.1.50", "notes": "A record added.", "timestamp": "2026-08-25 11:40:00"},

    # 5 Edited Cases (Corrections / Human Override)
    {
        "case_id": "NET-002",
        "human_action": "Edited",
        "human_fix_steps": "configure terminal\ninterface GigabitEthernet0/0.10\n ip address 192.168.10.1 255.255.255.0",
        "notes": "CORRECTION: AI suggested 'no encapsulation dot1Q 10' which is destructive and unnecessary. Tweak IP to match default gateway directly.",
        "timestamp": "2026-08-25 12:00:00"
    },
    {
        "case_id": "NET-013",
        "human_action": "Edited",
        "human_fix_steps": "configure terminal\ninterface GigabitEthernet0/1\n ip mtu 1500\n# OR on Router2:\n# interface GigabitEthernet0/1\n# ip mtu 1500",
        "notes": "CORRECTION: AI proposed 'ip ospf mtu-ignore' which bypasses troubleshooting best practices. Corrected MTU directly on interface.",
        "timestamp": "2026-08-25 12:05:00"
    },
    {
        "case_id": "NET-017",
        "human_action": "Edited",
        "human_fix_steps": "configure terminal\ninterface GigabitEthernet0/1\n no ip access-group DMZ_ACL in\n ip access-group DMZ_ACL out",
        "notes": "CORRECTION: AI suggested deleting and recreating the DMZ_ACL. Simply changing the application direction from 'in' to 'out' on Gi0/1 fixes it.",
        "timestamp": "2026-08-25 12:10:00"
    },
    {
        "case_id": "NET-019",
        "human_action": "Edited",
        "human_fix_steps": "configure terminal\nno ip nat inside source list 1 interface GigabitEthernet0/1\nip nat inside source list 1 interface GigabitEthernet0/1 overload",
        "notes": "CORRECTION: AI recommended rebooting the NAT router to clear translations. Re-applying the command with the overload keyword is clean and standard.",
        "timestamp": "2026-08-25 12:15:00"
    },
    {
        "case_id": "NET-022",
        "human_action": "Edited",
        "human_fix_steps": "# Configure client key with correct uppercase letter:\n# staff pre-shared key = Cisco12345!",
        "notes": "CORRECTION: AI suggested disabling WPA2 security completely due to key mismatch. Corrected key capitalization on client side to preserve security.",
        "timestamp": "2026-08-25 12:20:00"
    },

    # 2 Rejected Cases
    {
        "case_id": "NET-027",
        "human_action": "Rejected",
        "human_fix_steps": "",
        "notes": "REJECTED: AI failed to notice that permit ip any any statement bypassed the block rules. AI recommended a static route instead of correcting ACL.",
        "timestamp": "2026-08-25 12:30:00"
    },
    {
        "case_id": "NET-030",
        "human_action": "Rejected",
        "human_fix_steps": "",
        "notes": "REJECTED: AI recommended deleting the WAN subinterface completely. This would break outer connectivity. Conflicting IP range inside pool must be adjusted.",
        "timestamp": "2026-08-25 12:35:00"
    }
]

def generate_markdown_log(reviews):
    total = len(reviews)
    accepted = sum(1 for r in reviews if r["human_action"] == "Accepted")
    edited = sum(1 for r in reviews if r["human_action"] == "Edited")
    rejected = sum(1 for r in reviews if r["human_action"] == "Rejected")
    
    agreement_rate = (accepted / total) * 100 if total > 0 else 0.0
    
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

### 1. Case NET-002: Sub-interface IP Mismatch
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

---

## Complete Audit Logs
| Case ID | Timestamp | Action | Reviewer Notes |
|---|---|---|---|
"""
    for r in reviews:
        md_content += f"| {r['case_id']} | {r['timestamp']} | **{r['human_action']}** | {r['notes']} |\n"
        
    return md_content

def main():
    os.makedirs("data", exist_ok=True)
    os.makedirs("docs", exist_ok=True)
    
    # Save backing JSON database
    json_path = os.path.join("data", "audit_history.json")
    with open(json_path, "w") as f:
        json.dump(historical_reviews, f, indent=2)
        
    # Generate markdown log
    md_content = generate_markdown_log(historical_reviews)
    md_path = os.path.join("docs", "model_audit_log.md")
    with open(md_path, "w") as f:
        f.write(md_content)
        
    print("Successfully initialized audit_history.json and model_audit_log.md")

if __name__ == "__main__":
    main()
