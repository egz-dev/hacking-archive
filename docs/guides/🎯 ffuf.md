---
tags: [web]
---

> **ffuf** (Fuzz Faster U Fool) is a web fuzzer written in Go. It excels at subdomain and virtual host enumeration — often faster than Gobuster for DNS/vhost tasks. This guide covers what we've practiced.

---

## Quickstart — Subdomain Fuzzing

```bash
# Basic subdomain fuzz (will show EVERY result — mostly false positives)
$ ffuf -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt -u http://FUZZ.thetoppers.htb

# The magic flag: auto-calibrate (filters out default responses)
$ ffuf -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt -u http://FUZZ.thetoppers.htb -ac

# Manual filtering: exclude responses of a specific size
$ ffuf -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt -u http://FUZZ.thetoppers.htb -fs 11952
```

---

## The Problem — Why ffuf Shows Nothing (or Everything)

When a web server uses virtual host routing, every `Host` header returns the same default page. Without filtering, ffuf reports **20,000 "found" subdomains** — all false positives. With `-ac` (auto-calibrate), ffuf sends a few requests with random bogus subdomains, identifies the default response pattern, and only shows results that differ from that baseline.

### Diagnostic workflow

```bash
# 1. Manually check what the default response looks like
$ curl -s -o /dev/null -w "%{size_download}" -H "Host: abcdefg12345.thetoppers.htb" http://10.129.X.X

# 2. Note the response size (e.g., 11952 bytes) — that's your filter value
# 3. Run ffuf excluding that size
$ ffuf -w wordlist.txt -u http://FUZZ.thetoppers.htb -fs <that_number>
```

---

## Core Flags

| Flag | What it does |
| :--- | :----------- |
| `-u <url>` | Target URL with `FUZZ` placeholder |
| `-w <wordlist>` | Wordlist for the `FUZZ` keyword |
| `-ac` | **Auto-calibrate** — filters out default responses automatically |
| `-fs <size>` | Filter out responses of this size (bytes) |
| `-fw <words>` | Filter out responses with this word count |
| `-fc <code>` | Filter out this HTTP status code |
| `-mc <code>` | Only show this status code (e.g., `-mc 200,301,302`) |
| `-t <n>` | Threads (default 40) |
| `-o <file>` | Save output to file |

---

## Filters — Pick the Right One

| Flag | Best for | Example |
| :--- | :------- | :------ |
| `-ac` | **Start here** — auto-detects false positives | `ffuf ... -ac` |
| `-fs` | When you know the default page size | `-fs 11952` |
| `-fc` | When the default returns a specific code | `-fc 403,404` |

```bash
# Recommended pipeline for CTFs
# Step 1 — try auto-calibrate first
$ ffuf -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt -u http://FUZZ.domain.htb -ac

# Step 2 — if too aggressive, fall back to manual size filter
$ ffuf -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt -u http://FUZZ.domain.htb -fs <size> -mc 200
```

---

## DNS vs Host Header — No DNS Required

ffuf doesn't use DNS — it sends HTTP requests directly to the IP with different `Host` headers. As long as the target domain is in `/etc/hosts`, ffuf works:

```bash
# /etc/hosts entry is all ffuf needs
10.129.X.X    thetoppers.htb

# ffuf just swaps FUZZ in the Host header
$ ffuf -w wordlist.txt -u http://FUZZ.thetoppers.htb -ac
```

---

## Wordlists

| Wordlist | Size | Best for |
| :------- | :--- | :------- |
| `subdomains-top1million-5000.txt` | 5,000 | Quick first pass |
| `subdomains-top1million-20000.txt` | 20,000 | **The standard** for CTF boxes |

Both in `/usr/share/seclists/Discovery/DNS/`.

---

## ffuf vs Gobuster

| | ffuf | Gobuster |
| :--- | :--- | :------- |
| **Subdomain fuzzing** | ✅ Best — auto-calibrate, fast | ✅ Works, fewer filter options |
| **Directory busting** | ✅ Works | ✅ Best — purpose-built |
| **Auto-filtering** | ✅ `-ac` flag | ❌ Manual only |
| **Speed** | Very fast (Go) | Very fast (Go) |

> 💡 Use **ffuf** for subdomain/vhost discovery, **Gobuster** for directory busting. Both are Go-based and share wordlists.

---

## Troubleshooting

| Error / Symptom | Likely cause |
| :-------------- | :------------- |
| All 20,000 results shown | No filter — add `-ac` or `-fs <size>` |
| Zero results with `-ac` | Auto-calibrate too aggressive — use `-fs` manually |
| `command not found: ffuf` | Not installed — `sudo apt install ffuf` |
| `wfuzz` broken with Python error | wfuzz is Python 2, unmaintained — use ffuf instead |

---

## 🔗 Related

**Machines:** [[🥉 Three]]

**Guides:** [[💣 Gobuster]]

---

## References

- [ffuf GitHub](https://github.com/ffuf/ffuf)
- [SecLists — DNS Subdomains](https://github.com/danielmiessler/SecLists/tree/master/Discovery/DNS)
