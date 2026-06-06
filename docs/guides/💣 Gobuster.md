> **Gobuster** is a high-speed directory, file, DNS, and virtual host brute-forcing tool written in Go. It's the most widely used tool in CTFs for discovering hidden endpoints on web servers. This guide focuses on what you actually need for HTB boxes and CTFs.

---

## Quickstart — Directory Busting

```bash
# Basic dir scan — the command you'll run 90% of the time
$ gobuster dir -u http://10.129.1.10 -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt

# With extensions, threads, and status code filtering
$ gobuster dir -u http://10.129.1.10 -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt -x php,txt,html,bak,zip -t 50 -s 200,204,301,302,307,401,403

# Ignore self-signed cert warnings (HTTPS)
$ gobuster dir -u https://10.129.1.10 -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt -k
```

**If you need a smaller & faster wordlist for a quick first pass:**
```bash
gobuster dir -u http://10.129.1.10 -w /usr/share/seclists/Discovery/Web-Content/common.txt -x php,txt,html
```

---

## Modes — The 4 You Actually Need

Gobuster uses a mode-based command structure: `gobuster <mode> [flags]`

| Mode | Purpose | Example |
| :--- | :------ | :------ |
| `dir` | Brute-force directories & files (the bread-and-butter mode) | `gobuster dir -u http://IP -w wordlist.txt` |
| `dns` | Brute-force subdomains via DNS resolution | `gobuster dns -d example.com -w subdomains.txt` |
| `vhost` | Discover virtual hosts (same IP, different Host header) | `gobuster vhost -u http://IP -w vhosts.txt` |
| `fuzz` | General fuzzing using `FUZZ` keyword in URL | `gobuster fuzz -u http://IP/api/FUZZ -w params.txt` |

---

## Core Flags — Directory Mode (`dir`)

| Flag | What it does |
| :--- | :----------- |
| `-u <url>` | Target URL (⚠️ include `http://` or `https://`) |
| `-w <wordlist>` | Path to wordlist file |
| `-x <ext>` | File extensions to append (e.g., `php,txt,html,bak,zip,tar,gz`) |
| `-t <n>` | Number of concurrent threads (default 10, bump to 50–100 for speed) |
| `-o <file>` | Save output to file |
| `-s <codes>` | Show only these status codes (e.g., `200,204,301,302,307,401,403`) |
| `-b <codes>` | Blacklist status codes (ignore these; e.g., `404,500`) |
| `-k` | Skip TLS/SSL certificate verification (CTF essential) |
| `--no-tls-validation` | Same as `-k` |
| `-l` | Show response body length in output |
| `-a <ua>` | Custom User-Agent string |
| `-c <cookies>` | Cookies for authenticated scanning (e.g., `PHPSESSID=abc123`) |
| `-H <header>` | Custom HTTP header (e.g., `Authorization: Bearer <token>`) |
| `-q` | Quiet mode — suppress banner and warnings |
| `--no-error` | Suppress error messages during scanning |
| `--expanded` | Show full URLs in output (includes word + extension) |
| `--add-slash` | Append `/` to each directory request |
| `--exclude-length <n>` | Exclude responses by body length (e.g., `0`, `100-200`) |
| `--delay <time>` | Delay between requests (e.g., `500ms`, `1s`) |
| `--retry <n>` | Number of retries on network failures |
| `--timeout <time>` | HTTP request timeout (default 10s) |
| `--random-agent` | Use a random User-Agent for each request (evades basic WAF fingerprinting) |
| `--no-color` | Disable colored terminal output |
| `-r` | Follow redirects |
| `-p <proxy>` | Route traffic through a proxy (e.g., `http://127.0.0.1:8080`) |

### ✅ Before starting — essential checks
```bash
# Verify the web server is alive
$ curl -I http://10.129.1.10

# Check what technologies are in use (helps pick extensions)
$ whatweb http://10.129.1.10

# Quick manual browse — check robots.txt + source code
$ curl http://10.129.1.10/robots.txt
$ curl -s http://10.129.1.10 | grep -E 'href|src|action'
```

---

## DNS Mode Flags

```bash
$ gobuster dns -d example.htb -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -t 50
```

| Flag | What it does |
| :--- | :----------- |
| `-d <domain>` | Target domain to enumerate subdomains for |
| `-r <ip>` | Custom DNS resolver (e.g., `-r 10.129.1.10` for target's DNS) |
| `-c` / `--check-cname` | Display CNAME records for discovered subdomains |
| `--show-ips` | Display resolved IP addresses |
| `--wildcard` | Force wildcard DNS detection (false positives filter) |

---

## VHost Mode Flags

```bash
# Basic vhost scanning
$ gobuster vhost -u http://10.129.1.10 -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt

# Append domain automatically
$ gobuster vhost -u http://10.129.1.10 -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt --append-domain

# With status code filtering (ignore default page responses)
$ gobuster vhost -u http://10.129.1.10 -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt --exclude-length 12345
```

| Flag | What it does |
| :--- | :----------- |
| `--append-domain` | Append base domain to each word (e.g., `admin` → `admin.example.htb`) |
| `--exclude-length <n>` | Filter out responses matching this body length (key for vhost) |
| `--domain <domain>` | Override the Host header domain (different from `-d` in DNS mode) |

> ℹ️ **Dir mode vs VHost mode:** `dir` mode enumerates paths on a single host (`/admin`, `/backup`). `vhost` mode tests different `Host:` headers against the same IP to discover hidden virtual hosts (`admin.example.htb`, `dev.example.htb`).

---

## Fuzz Mode — Custom Fuzzing

```bash
# Fuzz URL parameters
$ gobuster fuzz -u http://10.129.1.10/api/user/FUZZ -w /usr/share/seclists/Discovery/Web-Content/common.txt

# Fuzz API endpoints
$ gobuster fuzz -u http://10.129.1.10/api/v1/FUZZ -w /usr/share/seclists/Discovery/Web-Content/common.txt -x json

# Fuzz with custom headers and cookies
$ gobuster fuzz -u http://10.129.1.10/FUZZ -w wordlist.txt -H 'X-API-Key: secret' -c 'token=abc123'

# Fuzz POST body data
$ gobuster fuzz -u http://10.129.1.10/search -X POST -w wordlist.txt -B "q=FUZZ"
```

> ℹ️ `FUZZ` is a keyword — gobuster replaces it with each entry from your wordlist.

---

## Wordlists — The Right One for the Job

Wordlists live in `/usr/share/seclists/` (Arch) or `/usr/share/wordlists/` (Kali). Pick the right one for the situation:

| Wordlist | Size | Best for |
| :------- | :--- | :------- |
| `/usr/share/seclists/Discovery/Web-Content/common.txt` | ~4,700 | Small, fast first pass |
| `/usr/share/seclists/Discovery/Web-Content/big.txt` | ~20,000 | Deeper directory scan |
| `/usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt` | ~220,000 | **The go-to** — comprehensive but manageable |
| `/usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-small.txt` | ~87,000 | Balanced speed vs. depth |
| `/usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-lowercase-2.3-medium.txt` | ~207,000 | All lowercase (case-insensitive servers) |
| `/usr/share/seclists/Discovery/Web-Content/raft-medium-directories.txt` | ~30,000 | RAFT-based, high hit rate |
| `/usr/share/seclists/Discovery/Web-Content/raft-medium-files.txt` | ~17,000 | Files specifically (not directories) |
| `/usr/share/seclists/Discovery/Web-Content/Apache.fuzz.txt` | ~1,000 | Apache-specific paths |
| `/usr/share/seclists/Discovery/Web-Content/IIS.fuzz.txt` | ~360 | IIS-specific paths |
| `/usr/share/seclists/Discovery/Web-Content/CGI-XPlatform.fuzz.txt` | ~700 | CGI scripts |
| `/usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt` | ~5,000 | DNS/VHost subdomain brute force |

---

## Status Codes — Filter Like a Pro

| Code | Meaning | Action |
| :--- | :------ | :----- |
| **200** | Found ✅ | Interesting — investigate |
| **204** | No Content | Often API responses — investigate |
| **301** / **302** | Redirect | Could lead somewhere — follow with `-r` |
| **307** | Temporary Redirect | Same as 301/302 |
| **401** | Unauthorized | Protected resource — try auth bypass |
| **403** | Forbidden | Hidden but exists — may indicate something juicy |
| **405** | Method Not Allowed | Try different HTTP methods (`PUT`, `POST`, etc.) |
| **404** | Not Found | Ignore (unless using small wordlists — then it's noise) |
| **500** | Internal Server Error | May indicate a vulnerable endpoint |
| **502** / **503** | Bad Gateway / Unavailable | Server overloaded — lower threads (`-t`) |

```bash
# Recommended status code filter for CTFs
$ gobuster dir -u http://10.129.1.10 -w wordlist.txt -s 200,204,301,302,307,401,403

# Exclude common noise
$ gobuster dir -u http://10.129.1.10 -w wordlist.txt -b 404,503
```

---

## CTF / HTB Techniques

### 1. Quick First Pass → Deep Scan Pipeline

```bash
# Step 1 — quick scan with small wordlist
$ gobuster dir -u http://10.129.1.10 -w /usr/share/seclists/Discovery/Web-Content/common.txt -x php,txt,html -t 100 -s 200,301

# Step 2 — if you find nothing, go deep
$ gobuster dir -u http://10.129.1.10 -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt -x php,html,txt,bak,zip,tar,gz,sql,backup~,old -t 50 -s 200,204,301,302,307,401,403
```

### 2. Extension Drills — When You Know the Tech Stack

| Tech | Extensions |
| :--- | :--------- |
| **PHP** | `.php`, `.php.bak`, `.php~`, `.php.old`, `.php.save`, `.phps`, `.pht`, `.phtml` |
| **ASP.NET** | `.aspx`, `.asp`, `.cshtml`, `.config`, `.master` |
| **Java** | `.jsp`, `.do`, `.action`, `.war`, `.jar` |
| **Python** | `.py`, `.wsgi`, `.cfg` |
| **Node.js** | `.js`, `.json`, `.map` |
| **Ruby** | `.rb`, `.erb` |
| **Generic** | `.txt`, `.bak`, `.zip`, `.tar`, `.tar.gz`, `.sql`, `.git`, `.env`, `.swp`, `.DS_Store` |

### 3. VHost Discovery — Find Hidden Subdomains

```bash
# Step 1 — Use --exclude-length to filter out the default page
$ curl -s http://10.129.1.10 -o /dev/null -w "%{size_download}"
12345    # <-- this is your exclude-length

# Step 2 — Scan with exclusion
$ gobuster vhost -u http://10.129.1.10 -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt --exclude-length 12345 -k

# Step 3 — If you have a domain name, append it
$ gobuster vhost -u http://example.htb -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt --append-domain -k
```

### 4. Authenticated Scanning — Behind a Login

```bash
# Cookie-based auth (CTF tip: steal session cookies with XSS first)
$ gobuster dir -u http://10.129.1.10/admin -w wordlist.txt -c 'PHPSESSID=abc123;token=xyz'

# Bearer token auth (API scanning)
$ gobuster dir -u http://10.129.1.10/api -w wordlist.txt -H 'Authorization: Bearer eyJhbGciOi...'

# Basic auth
$ gobuster dir -u http://user:pass@10.129.1.10 -w wordlist.txt
```

### 5. Exclude Length — Filter Out False Positives

```bash
# Many sites return the same HTML for 404s disguised as 200s.
# Use -l to see lengths, then exclude that length.

# First scan with lengths
$ gobuster dir -u http://10.129.1.10 -w wordlist.txt -l

# If you see many hits with length 9876 and the same page content, exclude it
$ gobuster dir -u http://10.129.1.10 -w wordlist.txt --exclude-length 9876
```

### 6. Subdomain Discovery with Custom Resolver

```bash
# If the target runs its own DNS server, use it directly
$ gobuster dns -d example.htb -w subdomains.txt -r 10.129.1.10

# Or use a public resolver for external domains
$ gobuster dns -d example.com -w subdomains.txt -r 8.8.8.8
```

---

## Automation & One-liners

### One-liner — Full dir scan with output

```bash
gobuster dir -u http://10.129.1.10 -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt -x php,txt,html,bak,zip -t 50 -s 200,204,301,302,307,401,403 -o gobuster-results.txt
```

### One-liner — Scan multiple hosts from a file

```bash
while read ip; do
  echo "=== Scanning $ip ==="
  gobuster dir -u "http://$ip" -w /usr/share/seclists/Discovery/Web-Content/common.txt -x php,txt,html -t 100 -q -o "gobuster-$ip.txt"
done < targets.txt
```

### One-liner — Run with proxy (for Burp Suite integration)

```bash
gobuster dir -u http://10.129.1.10 -w wordlist.txt -p http://127.0.0.1:8080 -k
```

### One-liner — Parse gobuster output for interesting extensions

```bash
gobuster dir -u http://10.129.1.10 -w wordlist.txt -x php,txt,html,bak,zip -s 200 -q | awk '{print $1}' | sort -u
```

### One-liner — Combine gobuster + whatweb for quick recon

```bash
whatweb http://10.129.1.10 && gobuster dir -u http://10.129.1.10 -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt -x php,txt,html -t 50 -s 200,301 -q
```

### Full pipeline — All modes on one target

```bash
#!/bin/bash
TARGET="10.129.1.10"
DOMAIN="example.htb"

# Step 1 — Directory busting
gobuster dir -u "http://$TARGET" -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt -x php,txt,html,bak,zip -t 50 -s 200,204,301,302,307,401,403 -o "dir-$TARGET.txt" &

# Step 2 — VHost discovery
gobuster vhost -u "http://$TARGET" -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt --append-domain -k -o "vhost-$TARGET.txt" &

# Step 3 — DNS subdomain discovery
gobuster dns -d "$DOMAIN" -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -t 50 -o "dns-$DOMAIN.txt" &

wait
echo "[+] All scans complete"
```

---

## Troubleshooting — What You'll Actually See

| Error / Symptom | Likely Cause |
| :-------------- | :----------- |
| `Error: error on parsing url` | Forgot `http://` or `https://` in `-u` |
| `[✗] Timeout` or many 502/503 | Too many threads — lower `-t` to 10–25 |
| `[✗] x509: certificate signed by unknown authority` | Self-signed cert — add `-k` |
| All results are 404s | Web server is case-sensitive or uses weird routing — try lowercase wordlist |
| All results are 403s | Rate limiting / WAF detected you — add `--delay 1s` |
| `Error: the server returns an error` | Target down or unreachable — check with `curl -I` |
| No results at all | Wrong wordlist or no extensions — add `-x php,html,txt` |

---

## References

- [Official Gobuster GitHub](https://github.com/OJ/gobuster)
- [SecLists Wordlists](https://github.com/danielmiessler/SecLists)
- [HackTricks — 80/443 HTTP Pentesting](https://book.hacktricks.xyz/network-services-pentesting/pentesting-web)
- [OWASP DirBuster Project](https://wiki.owasp.org/index.php/Category:OWASP_DirBuster_Project)
- [ffuf — Fuzz Faster U Fool](https://github.com/ffuf/ffuf)
