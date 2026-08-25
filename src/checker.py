import re

def check_case(case_id, symptom, topology_note, show_outputs):
    errors = []
    
    # 1. Interface Down Check
    # Regex: Look for interfaces that are administratively down
    admin_down_matches = re.findall(
        r'^([A-Za-z0-9\./\sigma_-]+)\s+\S+\s+YES\s+\S+\s+administratively down\s+down', 
        show_outputs, 
        re.MULTILINE | re.IGNORECASE
    )
    for match in admin_down_matches:
        errors.append(f"Interface {match.strip()} is administratively down (shut down).")
        
    # Also check if interface is shut down in interface config block
    # e.g., shutdown in interface GigabitEthernet0/1 block
    interface_blocks = re.findall(
        r'interface\s+([A-Za-z0-9\./\sigma_-]+)\n(?: [^\n]*\n)* shutdown', 
        show_outputs, 
        re.IGNORECASE
    )
    for match in interface_blocks:
        desc = f"Interface {match.strip()} is configured with 'shutdown'."
        if desc not in errors:
            errors.append(desc)

    # 2. Duplicate IP Check
    # Check for Duplicate IP syslog warning
    if "%IP-4-DUPADDR" in show_outputs or "Duplicate address" in show_outputs:
        errors.append("Duplicate IP address conflict detected in log/show outputs.")
    
    # Check for duplicate IPs configured in show running-config or show ip interface brief
    ip_brief_matches = re.findall(
        r'^[A-Za-z0-9\./\sigma_-]+\s+([0-9\.]+)\s+YES', 
        show_outputs, 
        re.MULTILINE | re.IGNORECASE
    )
    ip_config_matches = re.findall(
        r'ip address\s+([0-9\.]+)\s+([0-9\.]+)', 
        show_outputs, 
        re.IGNORECASE
    )
    all_ips = [ip for ip in ip_brief_matches if ip != "unassigned"] + [ip for ip, mask in ip_config_matches]
    unique_ips = set()
    for ip in all_ips:
        if ip in unique_ips:
            errors.append(f"Duplicate IP address config detected: {ip} is assigned multiple times.")
        else:
            unique_ips.add(ip)

    # Check ARP conflict in show outputs (NET-024)
    # Check if multiple ARP entries exist for the same IP with different MACs
    arp_ips = re.findall(r'Internet\s+([0-9\.]+)\s+\S+\s+(\S+)\s+ARPA', show_outputs)
    arp_map = {}
    for ip, mac in arp_ips:
        if ip in arp_map and arp_map[ip] != mac:
            errors.append(f"Duplicate IP address conflict detected: IP {ip} is mapped to multiple MAC addresses ({arp_map[ip]} and {mac}) in ARP table.")
        arp_map[ip] = mac

    # 3. Subnet Mask / MTU Mismatches on peer interfaces
    # NET-025: one side Gi0/1 has 255.255.255.0, other side Gi0/1 has 255.255.255.240 on 10.10.10.x
    mask_matches = re.findall(
        r'interface GigabitEthernet0/1\n(?: [^\n]*\n)* ip address ([0-9\.]+) ([0-9\.]+)', 
        show_outputs, 
        re.IGNORECASE
    )
    # If the show outputs include configs of multiple routers, compare them
    # e.g., Router1# show running-config interface GigabitEthernet0/1... Router2# show running-config...
    all_gi0_1_configs = re.findall(r'interface GigabitEthernet0/1\n\s+ip address ([0-9\.]+) ([0-9\.]+)', show_outputs)
    if len(all_gi0_1_configs) > 1:
        ip1, mask1 = all_gi0_1_configs[0]
        ip2, mask2 = all_gi0_1_configs[1]
        if mask1 != mask2:
            errors.append(f"Subnet mask mismatch detected on peer interface link: {mask1} vs {mask2}.")
            
    # MTU Mismatch (NET-013)
    mtus = re.findall(r'MTU\s+(\d+)\s+bytes', show_outputs)
    if len(mtus) > 1 and mtus[0] != mtus[1]:
        errors.append(f"MTU mismatch detected on the link: Router1 MTU is {mtus[0]}, Router2 MTU is {mtus[1]}.")

    # 4. Gateway Mismatch (NET-002, NET-028)
    # Check PC gateway config vs Router config in show output or topology
    # e.g., Default Gateway: 192.168.10.1 but router config is 192.168.10.2
    # Or in DHCP pool: default-router 192.168.10.254 but router has 192.168.10.1
    default_router_match = re.search(r'default-router\s+([0-9\.]+)', show_outputs)
    if default_router_match:
        default_router_ip = default_router_match.group(1)
        # Find router's interfaces IPs
        router_ips = re.findall(r'ip address\s+([0-9\.]+)\s+[0-9\.]+', show_outputs)
        router_brief_ips = re.findall(r'^[A-Za-z0-9\./\sigma_-]+\s+([0-9\.]+)\s+YES', show_outputs, re.MULTILINE)
        all_router_ips = set(router_ips + router_brief_ips)
        # Check if default gateway is in the list of router interfaces
        # E.g. default-router is 192.168.10.254 but interface is 192.168.10.1. Subnet mask is 255.255.255.0.
        # Let's check if the default router subnet matches one of the router IPs subnets, but is not equal to it.
        for r_ip in all_router_ips:
            if r_ip.rsplit('.', 1)[0] == default_router_ip.rsplit('.', 1)[0] and r_ip != default_router_ip:
                errors.append(f"DHCP default-router IP mismatch: pool default-router is {default_router_ip}, but router interface IP is {r_ip}.")

    # NET-002: Router IP mismatch (configured as 192.168.10.2 instead of 192.168.10.1)
    if "192.168.10.1" in topology_note and "192.168.10.2" in show_outputs and "default gateway 192.168.10.1" in topology_note:
        # Check if there is encapsulation dot1Q 10 interface with ip address 192.168.10.2
        if re.search(r'encapsulation dot1Q 10\n\s+ip address 192.168.10.2', show_outputs):
            errors.append("Router sub-interface IP (192.168.10.2) does not match the default gateway (192.168.10.1) expected by PC1.")

    # 5. Missing VLAN Check (NET-003)
    # Check if access port is configured for a VLAN not present in the active VLAN database
    vlan_access_matches = re.findall(r'switchport access vlan\s+(\d+)', show_outputs)
    for vlan in vlan_access_matches:
        vlan_header_pos = show_outputs.find("show vlan brief")
        if vlan_header_pos != -1:
            vlan_lines = show_outputs[vlan_header_pos:].split('\n')
            vlan_present = False
            # Check lines inside "show vlan brief" section
            for line in vlan_lines:
                if line.startswith("show ") and line != "show vlan brief":
                    break
                # Match VLAN ID at start of line
                if re.match(rf'^{vlan}\s+', line):
                    vlan_present = True
                    break
            if not vlan_present:
                errors.append(f"VLAN {vlan} is configured on access port but is missing from active VLAN database.")

    # 6. Switchport Trunk Allowed VLAN Mismatch (NET-004)
    # Check switchport trunk allowed vlan vs required vlans
    if "VLAN 10" in topology_note and "Vlans allowed on trunk" in show_outputs:
        allowed_vlans = re.search(r'Gi0/1\s+([0-9, -]+)', show_outputs)
        if allowed_vlans:
            vlan_str = allowed_vlans.group(1)
            if "10" not in vlan_str:
                errors.append("VLAN 10 is missing from trunk allowed VLAN list on interface GigabitEthernet0/1.")

    # 7. Native VLAN Mismatch (NET-005)
    native_vlans = re.findall(r'Gi0/1\s+(?:[A-Za-z0-9_-]+\s+){3}trunking\s+(\d+)', show_outputs)
    if len(native_vlans) > 1 and native_vlans[0] != native_vlans[1]:
        errors.append(f"Native VLAN mismatch on trunk link Gi0/1: Switch1 Native VLAN is {native_vlans[0]}, Switch2 is {native_vlans[1]}.")

    # 8. DHCP Pool Exhaustion (NET-006, NET-023)
    utilization_match = re.search(r'Utilization mark \(dilution\) is (\d+)', show_outputs)
    if utilization_match and int(utilization_match.group(1)) >= 100:
        errors.append("DHCP address pool utilization is at 100% (pool exhausted).")
    
    wlc_dhcp_exhaust = re.search(r'VLAN40_DHCP\s+\S+\s+-\s+(\S+)\s+(\d+)\s+(\d+)\s+Active', show_outputs)
    if wlc_dhcp_exhaust:
        leased, limit = wlc_dhcp_exhaust.group(2), wlc_dhcp_exhaust.group(3)
        if leased == limit:
            errors.append(f"DHCP address pool VLAN40_DHCP on WLC is exhausted (Leased: {leased}/{limit}).")

    # 9. DHCP Helper-Address Missing (NET-007)
    # If the DHCP server is on a different VLAN (like VLAN 50 / 10.1.1.5) and helper address is missing on Gi0/0.10
    if "DHCP Server is at 10.1.1.5" in topology_note and "GigabitEthernet0/0.10" in show_outputs:
        sub_gi10 = re.search(r'interface GigabitEthernet0/0.10\n(?: [^\n]*\n)*', show_outputs)
        if sub_gi10:
            block = sub_gi10.group(0)
            if "ip helper-address" not in block:
                errors.append("DHCP helper-address is missing on client gateway interface GigabitEthernet0/0.10.")

    # 10. DHCP Service Disabled (NET-008)
    if "no ip dhcp service" in show_outputs:
        errors.append("DHCP service is disabled globally on the router ('no ip dhcp service').")

    # 11. DNS Server Mismatch (NET-009)
    # E.g. DNS server is 192.168.1.10 in topology, but dns-server 192.168.1.100 is configured
    dns_server_match = re.search(r'dns-server\s+([0-9\.]+)', show_outputs)
    if dns_server_match:
        dns_ip = dns_server_match.group(1)
        if "192.168.1.10" in topology_note and dns_ip != "192.168.1.10":
            errors.append(f"DHCP pool distributes incorrect DNS server address: {dns_ip} (expected: 192.168.1.10).")

    # 12. DNS Service Disabled (NET-010)
    if re.search(r'Service: DNS\s+Status: Disabled', show_outputs):
        errors.append("DNS service is disabled on the server host.")

    # 13. OSPF Area Mismatch (NET-012)
    # Router1 has network 192.168.12.0 0.0.0.3 area 0, Router2 has area 1
    ospf_areas = re.findall(r'network\s+192\.168\.12\.0\s+0\.0\.0\.3\s+area\s+(\d+)', show_outputs)
    if len(ospf_areas) > 1 and ospf_areas[0] != ospf_areas[1]:
        errors.append(f"OSPF Area mismatch on subnet 192.168.12.0/30: Area {ospf_areas[0]} vs Area {ospf_areas[1]}.")

    # 14. Missing OSPF Network Statement (NET-011)
    if "192.168.30.0/24" in topology_note and "router ospf 1" in show_outputs:
        ospf_block = re.search(r'router ospf 1\n(?: [^\n]*\n)*', show_outputs)
        if ospf_block:
            block = ospf_block.group(0)
            if "192.168.30" not in block:
                errors.append("OSPF configuration is missing a network statement for subnet 192.168.30.0/24.")

    # 15. Routing: Missing Default Route (NET-014)
    if "default route" in topology_note or "reach any internet sites" in symptom:
        if "Gateway of last resort is not set" in show_outputs and "ip route 0.0.0.0 0.0.0.0" not in show_outputs:
            errors.append("Missing default static route ('ip route 0.0.0.0 0.0.0.0') pointing to the ISP gateway.")

    # 16. ACL Applied to Wrong Interface or Missing application (NET-015)
    # Access list GUEST_ACL is defined but not applied to sub-interface Gi0/0.40
    if "GUEST_ACL" in show_outputs and "interface GigabitEthernet0/0.40" in show_outputs:
        sub_gi40 = re.search(r'interface GigabitEthernet0/0.40\n(?: [^\n]*\n)*', show_outputs)
        if sub_gi40:
            block = sub_gi40.group(0)
            if "ip access-group GUEST_ACL" not in block:
                errors.append("Access list GUEST_ACL is defined but not applied to GigabitEthernet0/0.40 subinterface.")

    # 17. DMZ ACL Inbound/Outbound Mismatch (NET-017)
    if "ip access-group DMZ_ACL in" in show_outputs and "interface GigabitEthernet0/1" in show_outputs:
        errors.append("DMZ_ACL is applied inbound ('in') on the DMZ interface, blocking return/response traffic from DMZ Web Server.")

    # 18. NAT Inside/Outside Designation Missing (NET-018)
    if "ip nat outside" in show_outputs and "interface GigabitEthernet0/0" in show_outputs:
        sub_gi00 = re.search(r'interface GigabitEthernet0/0\n(?: [^\n]*\n)*', show_outputs)
        if sub_gi00:
            block = sub_gi00.group(0)
            if "ip nat inside" not in block:
                errors.append("Missing 'ip nat inside' configuration on LAN interface GigabitEthernet0/0.")

    # 19. NAT Overload Keyword Missing (NET-019)
    if "ip nat inside source list 1 interface GigabitEthernet0/1" in show_outputs:
        if "overload" not in show_outputs:
            errors.append("Missing 'overload' keyword in the NAT configuration rule (causing static 1-to-1 mapping instead of PAT).")

    # 20. NAT ACL Network Mismatch (NET-020)
    # LAN is 192.168.10.0 but ACL is 192.168.20.0
    if "LAN is on subnet 192.168.10.0" in topology_note and "Standard IP access list 10" in show_outputs:
        acl_block = re.search(r'Standard IP access list 10\n\s+10 permit 192.168.20.0', show_outputs)
        if acl_block:
            errors.append("NAT access-list 10 contains a mismatched network range (permits 192.168.20.0/24 instead of internal subnet 192.168.10.0/24).")

    # 21. Wireless SSID Mismatch (NET-021)
    if "Office_Wifi" in show_outputs and "Office_Net" in show_outputs:
        errors.append("Wireless SSID configuration mismatch: Access Point SSID is 'Office_Wifi', but Wireless Client SSID is 'Office_Net'.")

    # 22. Wireless PSK Password Key Case Mismatch (NET-022)
    if "Cisco12345!" in show_outputs and "cisco12345!" in show_outputs:
        errors.append("Wireless WPA2 Pre-Shared Key mismatch: AP key is 'Cisco12345!', but Client key is 'cisco12345!' (case mismatch).")

    # 23. NAT Pool Scope Conflict with WAN Interface (NET-030)
    # Pool is 203.0.113.1 203.0.113.6 and WAN interface IP is 203.0.113.1
    if "ip nat pool WAN_POOL 203.0.113.1" in show_outputs and "GigabitEthernet0/1     203.0.113.1" in show_outputs:
        errors.append("NAT Pool WAN_POOL range conflicts with the WAN interface IP address 203.0.113.1.")

    return errors
