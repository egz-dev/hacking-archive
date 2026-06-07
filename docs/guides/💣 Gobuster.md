---
tags: [web]
---

> **Gobuster** is a directory, file, and virtual host brute-forcing tool written in Go. It's the most-used tool in CTFs for discovering hidden endpoints on web servers. This guide covers what we've practiced.

---

## Quickstart — Directory Busting

```bash
# The command you'll run 90% of the time
$ gobuster dir -u http://10.129.1.10 -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt

# With extensions, threads, and status code filtering
$ gobuster dir -u http://10.129.1.10 -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt -x php,txt,html -t 50

# First quick pass with a small wordlist
gobuster dir -u http://10.129.1.10 -w /usr/share/seclists/Discovery/Web-Content/common.txt -x php,html,txt -t 100
```

---

## Core Flags — Directory Mode (`dir`)

| Flag | What it does |
| :--- | :------ |
| `-u <url>` | Target URL (⚠️ include `http://` or `https://`) |
| `-w <wordlist>` | Path to wordlist file |
| `-x <ext>` | Extensions to test (e.g., `php,txt,html`) |
| `-t <n>` | Concurrent threads (default 10, bump to 50-100 for speed) |
| `-o <file>` | Save output to file |
| `-s <codes>` | Show only these status codes (e.g., `200,301,403`) |
| `-k` | Skip TLS certificate verification |
| `-q` | Quiet mode — suppress banner and warnings |

---

## Wordlists — The right one for each job

| Wordlist | Size | Best for |
| :------- | :----- | :--------- |
| `common.txt` | ~4,700 | First quick pass |
| `DirBuster-2007_directory-list-2.3-small.txt` | ~87,000 | Balanced speed vs depth |
| `DirBuster-2007_directory-list-2.3-medium.txt` | ~220,000 | **The standard** — comprehensive but manageable |

---

## Virtual Host Mode (`vhost`)

When a web server uses virtual host routing, the IP returns different content based on the `Host` header. Gobuster can brute-force subdomains by swapping the `Host` header on every request:

```bash
# Basic vhost fuzzing
$ gobuster vhost -u http://thetoppers.htb -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt

# With --append-domain (appends .domain.htb to each wordlist entry)
$ gobuster vhost -u http://thetoppers.htb -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt --append-domain -t 50

# Filter by status code to reduce noise
$ gobuster vhost -u http://thetoppers.htb -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt --append-domain -s 200,302,404
```

### vhost vs dir — When to use each

| Mode | What it fuzzes | When |
| :--- | :------------- | :---- |
| `dir` | URL paths (`/admin`, `/login.php`) | **Default** — always run first |
| `vhost` | `Host` headers (`s3.domain.htb`) | When `dir` finds nothing or the page renders differently by domain |

> 💡 **Key insight:** Gobuster `vhost` found `s3.thetoppers.htb` (Status: 404, Size: 21) while `dir` found only `index.php`. The distinct response size (21 vs. 11,952) confirmed it was a real subdomain, not a catch-all.

### vhost flags

| Flag | What it does |
| :--- | :----------- |
| `--append-domain` | Appends the base domain to each wordlist entry (e.g., `s3` → `s3.thetoppers.htb`) |
| `-s <codes>` | Show only these status codes |
| `--exclude-length <size>` | Exclude responses of this size (filter out the default page) |

---

## Status Codes — Filter like a pro

| Code | Meaning | Action |
| :--- | :---------- | :----- |
| **200** | Found ✅ | Interesting — investigate |
| **301** / **302** | Redirect | Might lead somewhere — follow |
| **401** | Unauthorized | Protected resource — try auth bypass |
| **403** | Forbidden | Hidden but exists — may indicate something juicy |

```bash
# Recommended filter for CTFs
$ gobuster dir -u http://10.129.1.10 -w wordlist.txt -s 200,301,302,401,403
```

---

## CTF / HTB Techniques

### Pipeline: first quick pass → deep scan

```bash
# Step 1 — quick scan with small wordlist
$ gobuster dir -u http://10.129.1.10 -w /usr/share/seclists/Discovery/Web-Content/common.txt -x php,txt,html -t 100

# Step 2 — if you find nothing, dig deeper
$ gobuster dir -u http://10.129.1.10 -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt -x php,html,txt -t 50
```

### Extensions by tech stack

| Tech | Extensions |
| :--- | :---------- |
| **PHP** | `.php`, `.php.bak`, `.php~` |
| **ASP.NET** | `.aspx`, `.asp` |
| **Generic** | `.txt`, `.bak`, `.zip`, `.tar.gz`, `.sql` |

### From the writeups

Gobuster found:
- `/admin.php` — **Preignition** (hidden behind a default nginx page)
- `/login.php` and `/dashboard` — **Crocodile** (no visible links from the homepage)
- `s3.thetoppers.htb` — **Three** (`vhost` mode discovered the S3-compatible storage subdomain while `dir` found only `index.php`)

> 💡 A homepage with no visible links does NOT mean there isn't a hidden login panel. And when `gobuster dir` finds nothing, switch to `gobuster vhost` — the target domain may route to different apps by `Host` header.

---

## Troubleshooting

| Error / Symptom | Likely cause |
| :-------------- | :------------- |
| `Error: error on parsing url` | You forgot `http://` or `https://` in `-u` |
| All results are 404 | Web server is case-sensitive or uses unusual paths — try lowercase wordlist |
| No results | Try adding extensions with `-x php,html,txt` |

---

## 🔗 Related

**Machines:** [[🧨 Preignition]], [[📅 Appointment]], [[🐊 Crocodile]], [[🥉 Three]]

**Guides:** [[🗃️ FTP]], [[💉 SQL Injection]], [[🎯 ffuf]]

---

## References

- [Official Gobuster GitHub](https://github.com/OJ/gobuster)
- [SecLists Wordlists](https://github.com/danielmiessler/SecLists)
- [HackTricks — 80/443 HTTP Pentesting](https://book.hacktricks.xyz/network-services-pentesting/pentesting-web)
