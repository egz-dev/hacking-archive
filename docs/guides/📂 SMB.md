---
tags: [smb, windows]
---

> **SMB** (Server Message Block) is a network file sharing protocol used primarily by Windows. It runs on **port 445** (modern SMB over TCP) and **port 139** (NetBIOS legacy). This guide covers what we've practiced.

---

## Quickstart — Anonymous share enumeration

```bash
# List shares anonymously
$ smbclient -L 10.129.1.10
Enter WORKGROUP\\user's password:        <-- just press Enter

# Connect to an accessible share
$ smbclient \\\\\\\\10.129.1.10\\\\ShareName
Enter WORKGROUP\\user's password:        <-- just press Enter
smb: \\> ls
smb: \\> get flag.txt
smb: \\> quit
```

**If you get `NT_STATUS_ACCESS_DENIED` listing shares, try guest:**
```bash
smbclient -L 10.129.1.10 -U guest
smbclient -L 10.129.1.10 -U guest%          # empty password
```

---

## What to check when SMB is open

SMB rarely appears alone on Windows machines. Treat it as part of a reconnaissance pattern:

### Classic Windows port pattern

```
PORT      STATE SERVICE          Notes
135/tcp   open  msrpc             RPC — internal Windows services
139/tcp   open  netbios-ssn       NetBIOS legacy
445/tcp   open  microsoft-ds      SMB — file shares, null sessions
3389/tcp  open  ms-wbt-server     RDP — GUI access (try empty password)
5985/tcp  open  wsman             WinRM — PowerShell shell (needs creds)
```

> 💡 **Pattern recognition:** When you see SMB (445) + RPC (135) + WinRM (5985), you're on a Windows machine where your goal is to **find credentials**. Anonymous SMB shares, Responder NTLM capture, or web exploitation are the typical initial vectors.

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

> 💡 **From HTB Dancing:** SMB signing was *"enabled but not required"* — if we had captured credentials, relay would have been possible. We noted it as a recon observation.

---

## smbclient Commands

| Command | What it does |
| :------ | :------ |
| `ls` / `dir` | List files and directories |
| `cd <dir>` | Change directory |
| `cd ..` | Go to parent directory |
| `pwd` | Show current directory |
| `get <file>` | Download a file |
| `get <remote> <local>` | Download and rename locally |
| `mget *.txt` | Download multiple files |
| `quit` / `exit` | Disconnect |

---

## Default Windows Shares

Shares present on nearly every Windows machine. Anonymous access is **almost always denied** — focus on custom shares.

| Share | Purpose | Anonymous? |
| :---- | :-------- | :-------- |
| `ADMIN$` | Remote admin (access to `C:\\Windows`) | ❌ No |
| `C$` / `D$` | Default drive shares | ❌ No |
| `IPC$` | Inter-Process Communication (named pipes) | Limited |

> 💡 **From HTB Dancing:** `WorkShares` was the only non-default share — and it had anonymous read access.

---

## Useful Nmap Scripts

```bash
# Enumerate shares + check anonymous access
nmap --script smb-enum-shares -p445 10.129.1.10

# Check SMB signing (prerequisite for relay)
nmap --script smb2-security-mode -p445 10.129.1.10

# Full SMB enumeration
nmap --script smb-enum-* -p139,445 10.129.1.10
```

---

## 🔗 Related

**Machines:** [[🩰 Dancing]]

**Guides:** [[🖥️ WinRM]], [[🔐 NTLM]], [[🖥️ xfreerdp]]

---

## References

- [SMB Protocol (Microsoft Docs)](https://learn.microsoft.com/en-us/windows/win32/fileio/microsoft-smb-protocol-and-cifs-protocol-overview)
- [HackTricks — 139/445 SMB Pentesting](https://book.hacktricks.xyz/network-services-pentesting/pentesting-smb)
