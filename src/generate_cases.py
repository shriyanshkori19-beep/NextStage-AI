import os
import pandas as pd

cases = [
    {
        "case_id": "NET-001",
        "symptom": "PC1 in VLAN 30 cannot reach Server1 in VLAN 30; gateway ping fails.",
        "topology_note": "PC1 (192.168.30.50) is in VLAN 30. Default gateway is Router sub-interface GigabitEthernet0/0.30 (192.168.30.1).",
        "concept_tag": "Gateway",
        "severity": "High",
        "osi_layer": "Layer 1",
        "show_outputs": (
            "Router# show ip interface brief\n"
            "Interface              IP-Address      OK? Method Status                Protocol\n"
            "GigabitEthernet0/0     unassigned      YES unset  up                    up\n"
            "GigabitEthernet0/0.10  192.168.10.1    YES manual up                    up\n"
            "GigabitEthernet0/0.20  192.168.20.1    YES manual up                    up\n"
            "GigabitEthernet0/0.30  192.168.30.1    YES manual administratively down down\n"
            "GigabitEthernet0/1     10.1.1.1        YES manual up                    up\n"
        ),
        "expected_fault": "Sub-interface GigabitEthernet0/0.30 is administratively down."
    },
    {
        "case_id": "NET-002",
        "symptom": "PC1 in VLAN 10 cannot ping its default gateway 192.168.10.1.",
        "topology_note": "PC1 IP: 192.168.10.50, Mask: 255.255.255.0, Default Gateway: 192.168.10.1. Switch1 trunk is configured and active.",
        "concept_tag": "Gateway",
        "severity": "Medium",
        "osi_layer": "Layer 3",
        "show_outputs": (
            "Router# show running-config interface GigabitEthernet0/0.10\n"
            "interface GigabitEthernet0/0.10\n"
            " encapsulation dot1Q 10\n"
            " ip address 192.168.10.2 255.255.255.0\n"
        ),
        "expected_fault": "Router interface IP configuration mismatch (configured as 192.168.10.2 instead of default gateway 192.168.10.1)."
    },
    {
        "case_id": "NET-003",
        "symptom": "PC2 in VLAN 20 is plugged into Switch port FastEthernet0/5 but has no network connectivity.",
        "topology_note": "PC2 should be in VLAN 20. Switch1 port Fa0/5 is assigned to VLAN 20.",
        "concept_tag": "VLAN",
        "severity": "High",
        "osi_layer": "Layer 2",
        "show_outputs": (
            "Switch1# show vlan brief\n"
            "VLAN Name                             Status    Ports\n"
            "---- -------------------------------- --------- -------------------------------\n"
            "1    default                          active    Fa0/1, Fa0/2, Fa0/3, Fa0/4\n"
            "10   Sales                            active    Fa0/6, Fa0/7\n"
            "30   Engineering                      active    Fa0/8, Fa0/9\n"
            "\n"
            "Switch1# show running-config interface FastEthernet0/5\n"
            "interface FastEthernet0/5\n"
            " switchport access vlan 20\n"
            " switchport mode access\n"
        ),
        "expected_fault": "VLAN 20 is missing from the Switch's active VLAN database."
    },
    {
        "case_id": "NET-004",
        "symptom": "VLAN 10 hosts cannot communicate across Switch1 and Switch2.",
        "topology_note": "Switch1 and Switch2 are connected via GigabitEthernet0/1. Both switches host VLAN 10 and VLAN 20.",
        "concept_tag": "VLAN",
        "severity": "High",
        "osi_layer": "Layer 2",
        "show_outputs": (
            "Switch1# show interfaces trunk\n"
            "Port        Mode         Encapsulation  Status        Native vlan\n"
            "Gi0/1       on           802.1q         trunking      1\n"
            "\n"
            "Port        Vlans allowed on trunk\n"
            "Gi0/1       20,30\n"
        ),
        "expected_fault": "VLAN 10 is missing from the allowed VLAN list on the trunk port GigabitEthernet0/1."
    },
    {
        "case_id": "NET-005",
        "symptom": "Switch console is flooded with native VLAN mismatch messages, and traffic on native VLAN is leaking.",
        "topology_note": "Switch1 Gi0/1 connects to Switch2 Gi0/1.",
        "concept_tag": "VLAN",
        "severity": "Medium",
        "osi_layer": "Layer 2",
        "show_outputs": (
            "Switch1# show interfaces trunk\n"
            "Port        Mode         Encapsulation  Status        Native vlan\n"
            "Gi0/1       on           802.1q         trunking      10\n"
            "\n"
            "Switch2# show interfaces trunk\n"
            "Port        Mode         Encapsulation  Status        Native vlan\n"
            "Gi0/1       on           802.1q         trunking      99\n"
        ),
        "expected_fault": "Native VLAN mismatch on trunk link: Switch1 Native VLAN is 10, Switch2 is 99."
    },
    {
        "case_id": "NET-006",
        "symptom": "Newly connected PCs are unable to get an IP address, getting APIPA 169.254.x.x addresses.",
        "topology_note": "Router provides DHCP service via pool OFFICE_POOL.",
        "concept_tag": "DHCP",
        "severity": "High",
        "osi_layer": "Layer 7",
        "show_outputs": (
            "Router# show ip dhcp pool OFFICE_POOL\n"
            "Pool OFFICE_POOL :\n"
            " Utilization mark (dilution) is 100\n"
            " Current index        IP address range             Leased/Excluded/Total\n"
            " 192.168.1.254        192.168.1.10-192.168.1.254   245/0/245\n"
        ),
        "expected_fault": "DHCP address pool OFFICE_POOL is exhausted (utilization is 100%)."
    },
    {
        "case_id": "NET-007",
        "symptom": "PCs in VLAN 10 fail to receive IP addresses via DHCP, but PCs in VLAN 50 (where DHCP Server is located) work fine.",
        "topology_note": "DHCP Server is at 10.1.1.5 (VLAN 50). Router sub-interface Gi0/0.10 serves VLAN 10.",
        "concept_tag": "DHCP",
        "severity": "High",
        "osi_layer": "Layer 3",
        "show_outputs": (
            "Router# show running-config interface GigabitEthernet0/0.10\n"
            "interface GigabitEthernet0/0.10\n"
            " encapsulation dot1Q 10\n"
            " ip address 192.168.10.1 255.255.255.0\n"
            " ! Missing helper-address pointing to 10.1.1.5\n"
        ),
        "expected_fault": "Missing DHCP helper-address configuration on Router sub-interface GigabitEthernet0/0.10."
    },
    {
        "case_id": "NET-008",
        "symptom": "All clients on the local network fail to get IP addresses from the Router DHCP server.",
        "topology_note": "Router has a valid DHCP pool configured, but clients cannot lease IPs.",
        "concept_tag": "DHCP",
        "severity": "High",
        "osi_layer": "Layer 7",
        "show_outputs": (
            "Router# show running-config\n"
            "ip dhcp pool MYPOOL\n"
            " network 192.168.1.0 255.255.255.0\n"
            " default-router 192.168.1.1\n"
            "no ip dhcp service\n"
        ),
        "expected_fault": "DHCP service is disabled globally on the router ('no ip dhcp service')."
    },
    {
        "case_id": "NET-009",
        "symptom": "Client PCs can ping internal server IPs but cannot browse websites using domain names.",
        "topology_note": "DNS Server is at 192.168.1.10. Client PCs receive DHCP configuration from the Router.",
        "concept_tag": "DNS",
        "severity": "Medium",
        "osi_layer": "Layer 7",
        "show_outputs": (
            "Router# show running-config | section ip dhcp pool\n"
            "ip dhcp pool CLIENT_POOL\n"
            " network 192.168.1.0 255.255.255.0\n"
            " default-router 192.168.1.1\n"
            " dns-server 192.168.1.100\n"
        ),
        "expected_fault": "DHCP pool distributes incorrect DNS Server IP address (192.168.1.100 instead of 192.168.1.10)."
    },
    {
        "case_id": "NET-010",
        "symptom": "DNS queries fail for all clients, and server is not responding to port 53 UDP requests.",
        "topology_note": "DNS Server is located at 10.1.1.10.",
        "concept_tag": "DNS",
        "severity": "High",
        "osi_layer": "Layer 7",
        "show_outputs": (
            "DNSServer# show service-status\n"
            "Service: DNS        Status: Disabled\n"
            "Service: HTTP       Status: Enabled\n"
            "Service: HTTPS      Status: Enabled\n"
        ),
        "expected_fault": "DNS Server service is disabled on the DNS Server host."
    },
    {
        "case_id": "NET-011",
        "symptom": "Router1 cannot reach networks connected to Router2 via OSPF.",
        "topology_note": "Router1 (192.168.12.1) and Router2 (192.168.12.2) are neighbors. Router1 has interface GigabitEthernet0/0 on subnet 192.168.30.0/24.",
        "concept_tag": "Routing",
        "severity": "High",
        "osi_layer": "Layer 3",
        "show_outputs": (
            "Router1# show running-config | section router ospf\n"
            "router ospf 1\n"
            " network 192.168.12.0 0.0.0.3 area 0\n"
            " ! Missing network statement for 192.168.30.0/24\n"
        ),
        "expected_fault": "OSPF network statement is missing for subnet 192.168.30.0/24 on Router1."
    },
    {
        "case_id": "NET-012",
        "symptom": "OSPF neighbor adjacency is not forming between Router1 and Router2.",
        "topology_note": "Router1 Gi0/0 connects to Router2 Gi0/0 on network 192.168.12.0/30.",
        "concept_tag": "Routing",
        "severity": "High",
        "osi_layer": "Layer 3",
        "show_outputs": (
            "Router1# show running-config | section router ospf\n"
            "router ospf 1\n"
            " network 192.168.12.0 0.0.0.3 area 0\n"
            "\n"
            "Router2# show running-config | section router ospf\n"
            "router ospf 1\n"
            " network 192.168.12.0 0.0.0.3 area 1\n"
        ),
        "expected_fault": "OSPF area mismatch: Router1 is in Area 0, Router2 is in Area 1."
    },
    {
        "case_id": "NET-013",
        "symptom": "OSPF adjacency fails, stuck in EXSTART state.",
        "topology_note": "OSPF forming neighbor over GigabitEthernet0/1 link.",
        "concept_tag": "Routing",
        "severity": "Medium",
        "osi_layer": "Layer 3",
        "show_outputs": (
            "Router1# show interfaces GigabitEthernet0/1\n"
            "GigabitEthernet0/1 is up, line protocol is up\n"
            "  MTU 1500 bytes, BW 1000000 Kbit/sec\n"
            "\n"
            "Router2# show interfaces GigabitEthernet0/1\n"
            "GigabitEthernet0/1 is up, line protocol is up\n"
            "  MTU 1450 bytes, BW 1000000 Kbit/sec\n"
        ),
        "expected_fault": "MTU mismatch on OSPF link (Router1 has MTU 1500, Router2 has MTU 1450)."
    },
    {
        "case_id": "NET-014",
        "symptom": "Internal clients cannot reach any internet sites (e.g. 8.8.8.8) even though local routing works.",
        "topology_note": "Gateway Router should have a default route pointing to the ISP gateway at 203.0.113.2.",
        "concept_tag": "Routing",
        "severity": "Critical",
        "osi_layer": "Layer 3",
        "show_outputs": (
            "Router# show ip route\n"
            "Gateway of last resort is not set\n"
            "\n"
            "      10.0.0.0/24 is subnetted, 2 subnets\n"
            "C        10.1.1.0 is directly connected, GigabitEthernet0/0\n"
            "C        10.1.2.0 is directly connected, GigabitEthernet0/1\n"
        ),
        "expected_fault": "Missing default static route ('ip route 0.0.0.0 0.0.0.0') pointing to ISP."
    },
    {
        "case_id": "NET-015",
        "symptom": "Security policy to block SSH access from guest VLAN to router is not working.",
        "topology_note": "ACL GUEST_ACL blocks TCP port 22. Switch subinterface Gi0/0.40 handles guest VLAN 40.",
        "concept_tag": "ACL",
        "severity": "High",
        "osi_layer": "Layer 4",
        "show_outputs": (
            "Router# show access-lists GUEST_ACL\n"
            "Extended IP access list GUEST_ACL\n"
            "    10 deny tcp 172.16.40.0 0.0.0.255 any eq 22\n"
            "    20 permit ip any any\n"
            "\n"
            "Router# show running-config interface GigabitEthernet0/0.40\n"
            "interface GigabitEthernet0/0.40\n"
            " encapsulation dot1Q 40\n"
            " ip address 172.16.40.1 255.255.255.0\n"
            " ! No ip access-group configured\n"
        ),
        "expected_fault": "Access list GUEST_ACL is defined but not applied to sub-interface GigabitEthernet0/0.40."
    },
    {
        "case_id": "NET-016",
        "symptom": "Web surfing works by typing IPs, but typing domain names fails for all hosts.",
        "topology_note": "DNS traffic (UDP port 53) must be allowed through the router security ACL.",
        "concept_tag": "ACL",
        "severity": "High",
        "osi_layer": "Layer 4",
        "show_outputs": (
            "Router# show access-lists OUTSIDE_ACL\n"
            "Extended IP access list OUTSIDE_ACL\n"
            "    10 permit tcp any any eq 80\n"
            "    20 permit tcp any any eq 443\n"
            "    30 permit icmp any any\n"
            "    # Implicit deny blocking UDP port 53\n"
        ),
        "expected_fault": "Access list lacks permit statement for UDP port 53 (DNS) traffic, causing queries to be blocked by the implicit deny."
    },
    {
        "case_id": "NET-017",
        "symptom": "Internal clients cannot reach the web server on the DMZ subnet.",
        "topology_note": "DMZ Web Server is at 192.168.100.10. ACL is applied inbound on Router interface GigabitEthernet0/1 (DMZ interface).",
        "concept_tag": "ACL",
        "severity": "High",
        "osi_layer": "Layer 4",
        "show_outputs": (
            "Router# show running-config interface GigabitEthernet0/1\n"
            "interface GigabitEthernet0/1\n"
            " ip address 192.168.100.1 255.255.255.0\n"
            " ip access-group DMZ_ACL in\n"
            "\n"
            "Router# show access-lists DMZ_ACL\n"
            "Extended IP access list DMZ_ACL\n"
            "    10 permit tcp any host 192.168.100.10 eq 80\n"
            "    20 permit tcp any host 192.168.100.10 eq 443\n"
            "    ! This ACL prevents return traffic from the web server because it is applied 'in' on the DMZ interface\n"
        ),
        "expected_fault": "DMZ_ACL is applied in the wrong direction ('in' instead of 'out' on Gi0/1) or missing permit rules for server response traffic."
    },
    {
        "case_id": "NET-018",
        "symptom": "Hosts on private subnet 192.168.1.0/24 cannot access the internet; NAT translation table is empty.",
        "topology_note": "Gateway Router is configured for dynamic PAT. Gi0/0 is connected to LAN, Gi0/1 to WAN.",
        "concept_tag": "NAT",
        "severity": "Critical",
        "osi_layer": "Layer 3",
        "show_outputs": (
            "Router# show running-config interface GigabitEthernet0/0\n"
            "interface GigabitEthernet0/0\n"
            " ip address 192.168.1.1 255.255.255.0\n"
            " ! Missing 'ip nat inside'\n"
            "\n"
            "Router# show running-config interface GigabitEthernet0/1\n"
            "interface GigabitEthernet0/1\n"
            " ip address 203.0.113.1 255.255.255.252\n"
            " ip nat outside\n"
        ),
        "expected_fault": "Missing 'ip nat inside' configuration on interface GigabitEthernet0/0."
    },
    {
        "case_id": "NET-019",
        "symptom": "Only one local PC can browse the web at a time. Other PCs get connection timeouts.",
        "topology_note": "Router uses external interface IP for translation (PAT). Subnet is 192.168.1.0/24.",
        "concept_tag": "NAT",
        "severity": "High",
        "osi_layer": "Layer 3",
        "show_outputs": (
            "Router# show running-config | include ip nat\n"
            "ip nat inside source list 1 interface GigabitEthernet0/1\n"
            "\n"
            "Router# show access-lists 1\n"
            "Standard IP access list 1\n"
            "    10 permit 192.168.1.0 0.0.0.255\n"
        ),
        "expected_fault": "Missing 'overload' keyword in the NAT translation rule, causing static 1-to-1 NAT instead of Port Address Translation (PAT)."
    },
    {
        "case_id": "NET-020",
        "symptom": "NAT translations are not occurring, and users cannot reach the external ISP network.",
        "topology_note": "LAN is on subnet 192.168.10.0/24. Router NAT configuration references ACL 10.",
        "concept_tag": "NAT",
        "severity": "High",
        "osi_layer": "Layer 3",
        "show_outputs": (
            "Router# show running-config | include ip nat\n"
            "ip nat inside source list 10 interface GigabitEthernet0/1 overload\n"
            "\n"
            "Router# show access-lists 10\n"
            "Standard IP access list 10\n"
            "    10 permit 192.168.20.0 0.0.0.255\n"
        ),
        "expected_fault": "NAT access-list 10 contains the wrong subnet (permits 192.168.20.0/24 instead of internal subnet 192.168.10.0/24)."
    },
    {
        "case_id": "NET-021",
        "symptom": "Wireless client laptop fails to associate with the Access Point.",
        "topology_note": "Wireless LAN SSID is 'Office_Net'. Client Laptop is configured for wireless.",
        "concept_tag": "Wireless",
        "severity": "Medium",
        "osi_layer": "Layer 2",
        "show_outputs": (
            "AccessPoint# show wireless ssid\n"
            "SSID: Office_Wifi\n"
            "Security: WPA2-PSK\n"
            "\n"
            "ClientLaptop# show wireless connection-status\n"
            "SSID configured: Office_Net\n"
            "Status: Searching for AP...\n"
        ),
        "expected_fault": "SSID mismatch between the Access Point ('Office_Wifi') and the Wireless Client ('Office_Net')."
    },
    {
        "case_id": "NET-022",
        "symptom": "Wireless client is stuck on authentication failure when trying to connect to the AP.",
        "topology_note": "SSID is 'Staff_Secure' using WPA2 Pre-Shared Key.",
        "concept_tag": "Wireless",
        "severity": "High",
        "osi_layer": "Layer 2",
        "show_outputs": (
            "AccessPoint# show security wpa-psk\n"
            "SSID: Staff_Secure\n"
            "Key: Cisco12345!\n"
            "\n"
            "ClientLaptop# show wireless auth-settings\n"
            "SSID: Staff_Secure\n"
            "Key configured: cisco12345!\n"
        ),
        "expected_fault": "Pre-Shared Key mismatch (Cisco12345! on AP vs lowercase cisco12345! on Client)."
    },
    {
        "case_id": "NET-023",
        "symptom": "Wireless clients connect to the AP but fail to get an IP address, getting APIPA addresses.",
        "topology_note": "Wireless clients are on VLAN 40. The WLC handles the DHCP configuration for wireless.",
        "concept_tag": "Wireless",
        "severity": "High",
        "osi_layer": "Layer 7",
        "show_outputs": (
            "WirelessLANController# show dhcp-summary\n"
            "Scope Name         Address Range                  Leased   Limit    Status\n"
            "VLAN40_DHCP        172.16.40.10 - 172.16.40.20    11       11       Active\n"
        ),
        "expected_fault": "DHCP address pool on WLC for VLAN40 is exhausted."
    },
    {
        "case_id": "NET-024",
        "symptom": "Duplicate IP warnings are displayed on the router console, and connectivity to WebServer is erratic.",
        "topology_note": "DMZ WebServer is configured on 192.168.10.10. Router interface Gi0/1 is the gateway for DMZ.",
        "concept_tag": "Gateway",
        "severity": "High",
        "osi_layer": "Layer 3",
        "show_outputs": (
            "Router# show running-config interface GigabitEthernet0/1\n"
            "interface GigabitEthernet0/1\n"
            " ip address 192.168.10.10 255.255.255.0\n"
            "\n"
            "Router# show arp\n"
            "Protocol  Address          Age (min)  Hardware Addr   Type   Interface\n"
            "Internet  192.168.10.10           -   0001.97A2.A8B0  ARPA   GigabitEthernet0/1\n"
            "Internet  192.168.10.10           2   000A.F3C1.B821  ARPA   GigabitEthernet0/1\n"
        ),
        "expected_fault": "Duplicate IP address conflict: Both the Router interface Gi0/1 and DMZ WebServer host are configured with the IP 192.168.10.10."
    },
    {
        "case_id": "NET-025",
        "symptom": "OSPF Neighbor relationship fails to form between Router1 and Router2 on a point-to-point link.",
        "topology_note": "Router1 is on subnet 10.10.10.0. Router2 is on subnet 10.10.10.0.",
        "concept_tag": "Routing",
        "severity": "Medium",
        "osi_layer": "Layer 3",
        "show_outputs": (
            "Router1# show running-config interface GigabitEthernet0/1\n"
            "interface GigabitEthernet0/1\n"
            " ip address 10.10.10.1 255.255.255.0\n"
            "\n"
            "Router2# show running-config interface GigabitEthernet0/1\n"
            "interface GigabitEthernet0/1\n"
            " ip address 10.10.10.2 255.255.255.240\n"
        ),
        "expected_fault": "Subnet mask mismatch on the interconnecting link (Router1 uses /24, Router2 uses /28)."
    },
    {
        "case_id": "NET-026",
        "symptom": "VLAN 30 users cannot communicate across the network switch.",
        "topology_note": "Switch trunk port GigabitEthernet0/1 is used to carry VLAN 30 to the core switch.",
        "concept_tag": "VLAN",
        "severity": "High",
        "osi_layer": "Layer 2",
        "show_outputs": (
            "Switch# show interfaces GigabitEthernet0/1 switchport\n"
            "Name: Gi0/1\n"
            "Administrative Mode: trunk\n"
            "Operational Mode: trunk\n"
            "\n"
            "Switch# show ip interface brief\n"
            "Interface              IP-Address      OK? Method Status                Protocol\n"
            "GigabitEthernet0/1     unassigned      YES unset  administratively down down\n"
        ),
        "expected_fault": "The trunk interface GigabitEthernet0/1 is shut down ('administratively down')."
    },
    {
        "case_id": "NET-027",
        "symptom": "Guest VLAN users can ping internal production database servers.",
        "topology_note": "Guest network is 172.16.50.0/24. Production Database is at 10.1.1.200. ACL is supposed to isolate guest traffic.",
        "concept_tag": "ACL",
        "severity": "High",
        "osi_layer": "Layer 4",
        "show_outputs": (
            "Router# show access-lists GUEST_FILTER\n"
            "Extended IP access list GUEST_FILTER\n"
            "    10 permit tcp any any eq 80\n"
            "    20 permit tcp any any eq 443\n"
            "    30 permit ip any any\n"
            "    ! permit ip any any allows all traffic including to the production servers\n"
        ),
        "expected_fault": "Access list GUEST_FILTER is missing a deny rule to block traffic from the Guest subnet to the internal 10.0.0.0/8 network before permitting everything else."
    },
    {
        "case_id": "NET-028",
        "symptom": "DHCP clients get correct IP addresses but cannot access other subnets or the internet.",
        "topology_note": "Router sub-interface Gi0/0.10 is 192.168.10.1. Client subnet is 192.168.10.0/24.",
        "concept_tag": "DHCP",
        "severity": "High",
        "osi_layer": "Layer 7",
        "show_outputs": (
            "Router# show running-config | section ip dhcp pool\n"
            "ip dhcp pool VLAN10_POOL\n"
            " network 192.168.10.0 255.255.255.0\n"
            " default-router 192.168.10.254\n"
            " dns-server 8.8.8.8\n"
        ),
        "expected_fault": "DHCP pool default-router IP is misconfigured as 192.168.10.254 (should be Router interface IP 192.168.10.1)."
    },
    {
        "case_id": "NET-029",
        "symptom": "Pinging database.internal.local fails, but pinging the server IP 10.1.1.50 directly works.",
        "topology_note": "Internal DNS server should resolve database.internal.local to 10.1.1.50.",
        "concept_tag": "DNS",
        "severity": "Medium",
        "osi_layer": "Layer 7",
        "show_outputs": (
            "DNSServer# show dns-records\n"
            "Domain: www.internal.local    Type: A      IP: 10.1.1.10\n"
            "Domain: mail.internal.local   Type: A      IP: 10.1.1.20\n"
            "! Missing A record for database.internal.local\n"
        ),
        "expected_fault": "DNS A record for database.internal.local is missing on the DNS Server."
    },
    {
        "case_id": "NET-030",
        "symptom": "Internet connectivity fails; external router reports conflict on its public interface.",
        "topology_note": "Router uses NAT pool WAN_POOL to map internal IP addresses to the WAN range 203.0.113.0/29.",
        "concept_tag": "NAT",
        "severity": "Critical",
        "osi_layer": "Layer 3",
        "show_outputs": (
            "Router# show running-config | include ip nat pool\n"
            "ip nat pool WAN_POOL 203.0.113.1 203.0.113.6 netmask 255.255.255.248\n"
            "\n"
            "Router# show ip interface brief\n"
            "Interface              IP-Address      OK? Method Status                Protocol\n"
            "GigabitEthernet0/1     203.0.113.1     YES manual up                    up\n"
        ),
        "expected_fault": "NAT pool IP range WAN_POOL conflicts with Router WAN interface Gi0/1 IP address (203.0.113.1)."
    }
]

df = pd.DataFrame(cases)
os.makedirs("data", exist_ok=True)
df.to_csv("data/cases.csv", index=False)
print("Successfully generated data/cases.csv with 30 cases.")
