# Model Audit Log & Human-in-the-Loop Performance

This document audits the performance of NetSage AI. It tracks diagnoses, operator overrides, and agreement rates.

## Performance Metrics
- **Total Diagnostic Logs**: 31
- **Agreement (Accepted)**: 24
- **Override (Edited)**: 5
- **Override (Rejected)**: 2
- **Human-AI Agreement Rate**: 77.4%

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
| NET-001 | 2026-08-25 10:15:00 | **Accepted** | AI diagnosis was 100% correct. |
| NET-003 | 2026-08-25 10:18:00 | **Accepted** | VLAN was indeed missing from database. |
| NET-004 | 2026-08-25 10:20:00 | **Accepted** | Trunk configuration checked and fixed. |
| NET-005 | 2026-08-25 10:22:00 | **Accepted** | Fixed native VLAN mismatch. |
| NET-006 | 2026-08-25 10:25:00 | **Accepted** | Confirmed pool was exhausted. |
| NET-007 | 2026-08-25 10:28:00 | **Accepted** | DHCP relay configured. |
| NET-008 | 2026-08-25 10:30:00 | **Accepted** | Enabled disabled service. |
| NET-009 | 2026-08-25 10:35:00 | **Accepted** | DNS server IP corrected. |
| NET-010 | 2026-08-25 10:38:00 | **Accepted** | DNS service turned on. |
| NET-011 | 2026-08-25 10:40:00 | **Accepted** | OSPF network added. |
| NET-012 | 2026-08-25 10:45:00 | **Accepted** | OSPF area mismatch fixed. |
| NET-014 | 2026-08-25 10:48:00 | **Accepted** | Default route added. |
| NET-015 | 2026-08-25 10:50:00 | **Accepted** | ACL applied successfully. |
| NET-016 | 2026-08-25 10:55:00 | **Accepted** | DNS UDP 53 permitted. |
| NET-018 | 2026-08-25 11:00:00 | **Accepted** | NAT inside config added. |
| NET-020 | 2026-08-25 11:05:00 | **Accepted** | NAT ACL subnet range corrected. |
| NET-021 | 2026-08-25 11:10:00 | **Accepted** | SSID mismatch fixed. |
| NET-023 | 2026-08-25 11:15:00 | **Accepted** | IP scope expanded. |
| NET-024 | 2026-08-25 11:20:00 | **Accepted** | Duplicate IP address conflict resolved. |
| NET-025 | 2026-08-25 11:25:00 | **Accepted** | Mismatched mask resolved. |
| NET-026 | 2026-08-25 11:30:00 | **Accepted** | Brought up trunk port interface. |
| NET-028 | 2026-08-25 11:35:00 | **Accepted** | Default router IP in pool fixed. |
| NET-029 | 2026-08-25 11:40:00 | **Accepted** | A record added. |
| NET-002 | 2026-08-25 12:00:00 | **Edited** | CORRECTION: AI suggested 'no encapsulation dot1Q 10' which is destructive and unnecessary. Tweak IP to match default gateway directly. |
| NET-013 | 2026-08-25 12:05:00 | **Edited** | CORRECTION: AI proposed 'ip ospf mtu-ignore' which bypasses troubleshooting best practices. Corrected MTU directly on interface. |
| NET-017 | 2026-08-25 12:10:00 | **Edited** | CORRECTION: AI suggested deleting and recreating the DMZ_ACL. Simply changing the application direction from 'in' to 'out' on Gi0/1 fixes it. |
| NET-019 | 2026-08-25 12:15:00 | **Edited** | CORRECTION: AI recommended rebooting the NAT router to clear translations. Re-applying the command with the overload keyword is clean and standard. |
| NET-022 | 2026-08-25 12:20:00 | **Edited** | CORRECTION: AI suggested disabling WPA2 security completely due to key mismatch. Corrected key capitalization on client side to preserve security. |
| NET-027 | 2026-08-25 12:30:00 | **Rejected** | REJECTED: AI failed to notice that permit ip any any statement bypassed the block rules. AI recommended a static route instead of correcting ACL. |
| NET-030 | 2026-08-25 12:35:00 | **Rejected** | REJECTED: AI recommended deleting the WAN subinterface completely. This would break outer connectivity. Conflicting IP range inside pool must be adjusted. |
| NET-001 | 2026-08-25 15:34:40 | **Accepted** | Approved by network operator in active workspace. |
