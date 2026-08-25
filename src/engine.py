import os
import json
import re
from google import genai
from google.genai import types
from src.checker import check_case

def load_system_config():
    config_path = os.path.join("data", "system_config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "model_name": "gemini-2.5-flash",
        "confidence_threshold": 0.7,
        "max_tokens": 1024,
        "temperature": 0.1
    }

def get_simulated_ai_response(case):
    """
    Generate a realistic, structured JSON diagnostic output 
    based on the case data, used when no Gemini API key is available.
    """
    case_id = case["case_id"]
    expected_fault = case["expected_fault"]
    osi_layer = case["osi_layer"]
    concept = case["concept_tag"]
    
    # Define verification commands and fix steps for each case
    # to make the simulated AI output highly realistic and Cisco-compliant.
    fix_and_commands = {
        "NET-001": ("show ip interface brief", "configure terminal\ninterface GigabitEthernet0/0.30\nno shutdown"),
        "NET-002": ("show running-config interface GigabitEthernet0/0.10", "configure terminal\ninterface GigabitEthernet0/0.10\n ip address 192.168.10.1 255.255.255.0"),
        "NET-003": ("show vlan brief", "configure terminal\nvlan 20\n name Sales\nexit"),
        "NET-004": ("show interfaces trunk", "configure terminal\ninterface GigabitEthernet0/1\n switchport trunk allowed vlan add 10"),
        "NET-005": ("show interfaces trunk", "configure terminal\ninterface GigabitEthernet0/1\n switchport trunk native vlan 10"),
        "NET-006": ("show ip dhcp binding", "configure terminal\nip dhcp pool OFFICE_POOL\n network 192.168.1.0 255.255.255.0\n ! Expand range or clean up leases"),
        "NET-007": ("show running-config interface GigabitEthernet0/0.10", "configure terminal\ninterface GigabitEthernet0/0.10\n ip helper-address 10.1.1.5"),
        "NET-008": ("show running-config | include dhcp", "configure terminal\nip dhcp service"),
        "NET-009": ("show running-config | section ip dhcp pool", "configure terminal\nip dhcp pool CLIENT_POOL\n no dns-server 192.168.1.100\n dns-server 192.168.1.10"),
        "NET-010": ("show service-status", "# In Cisco Packet Tracer DNS Server GUI:\n# Enable the DNS service and verify record mappings."),
        "NET-011": ("show running-config | section router ospf", "configure terminal\nrouter ospf 1\n network 192.168.30.0 0.0.0.255 area 0"),
        "NET-012": ("show ip ospf interface", "configure terminal\nrouter ospf 1\n no network 192.168.12.0 0.0.0.3 area 1\n network 192.168.12.0 0.0.0.3 area 0"),
        "NET-013": ("show ip ospf interface GigabitEthernet0/1", "configure terminal\ninterface GigabitEthernet0/1\n ip ospf mtu-ignore\n# OR adjust MTU on Router2:\n# interface GigabitEthernet0/1\n# ip mtu 1500"),
        "NET-014": ("show ip route", "configure terminal\nip route 0.0.0.0 0.0.0.0 203.0.113.2"),
        "NET-015": ("show running-config interface GigabitEthernet0/0.40", "configure terminal\ninterface GigabitEthernet0/0.40\n ip access-group GUEST_ACL in"),
        "NET-016": ("show access-lists OUTSIDE_ACL", "configure terminal\nip access-list extended OUTSIDE_ACL\n 5 permit udp any any eq 53"),
        "NET-017": ("show running-config interface GigabitEthernet0/1", "configure terminal\ninterface GigabitEthernet0/1\n no ip access-group DMZ_ACL in\n ip access-group DMZ_ACL out"),
        "NET-018": ("show running-config interface GigabitEthernet0/0", "configure terminal\ninterface GigabitEthernet0/0\n ip nat inside"),
        "NET-019": ("show running-config | include ip nat", "configure terminal\nno ip nat inside source list 1 interface GigabitEthernet0/1\nip nat inside source list 1 interface GigabitEthernet0/1 overload"),
        "NET-020": ("show access-lists 10", "configure terminal\nno access-list 10\naccess-list 10 permit 192.168.10.0 0.0.0.255"),
        "NET-021": ("show wireless summary", "# In Linksys AP/Client settings:\n# Align SSID name to 'Office_Wifi' on the client device."),
        "NET-022": ("show wireless security", "# On Wireless Client Laptop:\n# Correct pre-shared key capitalization to match 'Cisco12345!'."),
        "NET-023": ("show dhcp-summary", "configure terminal\n# Expand DHCP scope address range on WLC console GUI."),
        "NET-024": ("show arp", "configure terminal\ninterface GigabitEthernet0/1\n ip address 192.168.10.1 255.255.255.0\n# Verify WebServer has host IP 192.168.10.10."),
        "NET-025": ("show running-config interface GigabitEthernet0/1", "configure terminal\ninterface GigabitEthernet0/1\n ip address 10.10.10.2 255.255.255.0"),
        "NET-026": ("show ip interface brief", "configure terminal\ninterface GigabitEthernet0/1\n no shutdown"),
        "NET-027": ("show access-lists GUEST_FILTER", "configure terminal\nip access-list extended GUEST_FILTER\n 5 deny ip 172.16.50.0 0.0.0.255 10.0.0.0 0.255.255.255\n 30 permit ip any any"),
        "NET-028": ("show running-config | section ip dhcp pool", "configure terminal\nip dhcp pool VLAN10_POOL\n no default-router 192.168.10.254\n default-router 192.168.10.1"),
        "NET-029": ("show dns-records", "# On DNS Server Service Console:\n# Add A record: 'database.internal.local' -> '10.1.1.50'"),
        "NET-030": ("show ip interface brief", "configure terminal\nno ip nat pool WAN_POOL 203.0.113.1 203.0.113.6 netmask 255.255.255.248\nip nat pool WAN_POOL 203.0.113.2 203.0.113.6 netmask 255.255.255.248")
    }
    
    next_cmd, fix = fix_and_commands.get(case_id, ("show ip route", "configure terminal"))
    
    # Extract a line of evidence from the show outputs
    evidence = ""
    lines = case["show_outputs"].split("\n")
    for line in lines:
        if any(kw in line.lower() for kw in ["down", "mismatch", "error", "no", "disabled", "status:", "address", "allowed", "native", "list", "permit", "deny", "utilization"]):
            evidence = line.strip()
            break
    if not evidence and lines:
        evidence = lines[0]
        
    return {
        "root_cause": f"Simulated Diagnosis: {expected_fault}",
        "osi_layer": osi_layer,
        "confidence": "High",
        "evidence": evidence,
        "next_command": next_cmd,
        "fix_steps": fix,
        "is_simulated": True
    }

def run_diagnosis(case, api_key=None):
    """
    Run diagnostic pipeline on a single case dictionary:
    1. Run deterministic checks.
    2. Query Gemini API (if key available) or fallback to simulation.
    3. Return combined diagnostic results.
    """
    symptom = case["symptom"]
    topology_note = case["topology_note"]
    show_outputs = case["show_outputs"]
    case_id = case["case_id"]
    
    # 1. Run deterministic rule check
    rule_errors = check_case(case_id, symptom, topology_note, show_outputs)
    checker_feedback = "\n".join(rule_errors) if rule_errors else "None"
    
    # 2. Get AI Diagnosis (live or simulated)
    api_key = api_key or os.environ.get("GEMINI_API_KEY")
    
    if api_key:
        try:
            # Read prompt template
            prompt_path = os.path.join("prompts", "diagnose_prompt.md")
            with open(prompt_path, "r") as f:
                prompt_template = f.read()
                
            prompt = prompt_template.format(
                symptom=symptom,
                topology_note=topology_note,
                show_outputs=show_outputs,
                checker_feedback=checker_feedback
            )
            
            # Load settings
            config = load_system_config()
            client = genai.Client(api_key=api_key)
            
            response = client.models.generate_content(
                model=config["model_name"],
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=config["temperature"],
                    max_output_tokens=config["max_tokens"]
                )
            )
            
            response_text = response.text.strip()
            
            # Clean response text from potential markdown JSON wrapper
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            diagnostic_data = json.loads(response_text)
            diagnostic_data["is_simulated"] = False
            
        except Exception as e:
            # Fallback to simulation if live call fails
            diagnostic_data = get_simulated_ai_response(case)
            diagnostic_data["root_cause"] = f"[API Error, Falling back to Simulation] {diagnostic_data['root_cause']}"
            diagnostic_data["error_details"] = str(e)
    else:
        # No key, use simulation
        diagnostic_data = get_simulated_ai_response(case)
        
    # 3. Combine results
    result = {
        "case_id": case_id,
        "symptom": symptom,
        "topology_note": topology_note,
        "expected_fault": case["expected_fault"],
        "concept_tag": case["concept_tag"],
        "severity": case["severity"],
        "rule_checker_warnings": rule_errors,
        "ai_root_cause": diagnostic_data.get("root_cause", ""),
        "ai_osi_layer": diagnostic_data.get("osi_layer", ""),
        "ai_confidence": diagnostic_data.get("confidence", "Medium"),
        "ai_evidence": diagnostic_data.get("evidence", ""),
        "ai_next_command": diagnostic_data.get("next_command", ""),
        "ai_fix_steps": diagnostic_data.get("fix_steps", ""),
        "is_simulated": diagnostic_data.get("is_simulated", False),
        "api_error": diagnostic_data.get("error_details", None)
    }
    
    return result
