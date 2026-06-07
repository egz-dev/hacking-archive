---
tags: [windows, rdp, windows-tools]
---

> **xfreerdp** is the open-source RDP client from the FreeRDP project. It connects to Windows hosts on **port 3389**. This guide covers what we've practiced.

---

## Quickstart — Basic connection

```bash
# Interactive (prompts for password — safest)
$ xfreerdp /v:10.129.1.10 /u:Administrator

# With inline password (⚠️ appears in shell history)
$ xfreerdp /v:10.129.1.10 /u:Administrator /p:Password123

# Ignore self-signed certificate (essential in CTF)
$ xfreerdp /v:10.129.1.10 /u:Administrator /p:Password123 /cert-ignore

# Full screen
$ xfreerdp /v:10.129.1.10 /u:Administrator /p:Password123 /cert-ignore /f
```

**To exit full screen:** `Ctrl+Alt+Enter`

### ✅ Before you start
```bash
$ nmap -sCV -p3389 10.129.1.10
# Look for "Remote Desktop Protocol" in the output
```

---

## Essential options

| Flag | What it does |
| :--- | :------ |
| `/v:<host>` | Target IP/hostname (defaults to port 3389) |
| `/u:<user>` | Username |
| `/p:<pass>` | Password |
| `/cert-ignore` | Ignore certificate warnings (self-signed certs) |
| `/f` | Full screen mode |

---

## CTF / HTB Techniques

### Administrator with empty password

Trying RDP as `Administrator` with an **empty password** is surprisingly common in CTF environments:

```bash
$ xfreerdp3 /v:10.129.1.10 /u:Administrator /cert-ignore
Password:                    <-- just press Enter
```

> 💡 **Why it works:** Windows allows accounts with blank passwords in certain configurations (freshly provisioned VMs, misconfigured Group Policy).

---

## Useful Nmap Scripts

```bash
# Detect RDP + NTLM info
nmap -sV -p3389 10.129.1.10
nmap --script rdp-ntlm-info -p3389 10.129.1.10
```

---

## Troubleshooting

| Error / Symptom | Likely cause |
| :-------------- | :------------- |
| `ERRCONNECT_CONNECT_FAILED` | Port 3389 not open / host unreachable |
| `ERRCONNECT_LOGON_FAILURE` | Incorrect username/password |
| `SSL certificate problem` | Self-signed cert — use `/cert-ignore` |

---

## 🔗 Related

**Machines:** [[💥 Explosion]]

**Guides:** [[🖥️ WinRM]]

---

## References

- [FreeRDP Official GitHub](https://github.com/FreeRDP/FreeRDP)
- [HackTricks — 3389 RDP Pentesting](https://book.hacktricks.xyz/network-services-pentesting/pentesting-rdp)
