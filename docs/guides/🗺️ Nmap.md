---
tags: [scanning]
---

> **Nmap** (Network Mapper) is the standard port scanning and network discovery tool. It's the first thing you run on every HTB machine and CTF. This guide covers what we've practiced across the 11 writeups.

---

## Quickstart — The scans we actually run

> ⭐ **The 2-command pipeline I use in every writeup:**
>
> ```bash
> # 1️⃣ Full port scan — find all open ports
> nmap -p- --open -sS --min-rate 5000 -vvv -n -Pn $IP
>
> # 2️⃣ Service + version + default scripts on discovered ports
> nmap -sCV -p21,22,80,445,3389 $IP
> ```

---

## Essential Flags — The ones we actually use

| Flag | What it does |
| :--- | :------ |
| `-p <ports>` | Ports to scan (`-p22,80,443`, `-p-` all ports) |
| `-sS` | SYN scan (half-open, needs sudo, stealthy) |
| `-sT` | TCP connect scan (no sudo needed, slower) |
| `-sV` | Version detection |
| `-sC` | Run default NSE scripts |
| `-sCV` | `-sC` + `-sV` combined (my most-used flag) |
| `-Pn` | Skip host discovery (assume host is up) |
| `-n` | No DNS resolution (speeds up scan) |
| `--open` | Show only open ports |
| `--min-rate <n>` | Minimum packet send rate in packets/sec |
| `-vvv` | Maximum verbosity (see ports as they're found) |
| `-T4` | Aggressive timing template (CTF standard) |

---

## Standard Writeup Pipeline

```bash
# Stage 1 — Fast full port scan
nmap -p- --open -sS --min-rate 5000 -vvv -n -Pn $IP

# Stage 2 — Service scan on discovered ports
nmap -sCV -p21,80,445,3389,5985 $IP -oA scan-$IP

# Optional: save text-only (-oN) instead of all formats
nmap -sCV -p21,80 $IP -oN scan-$IP.txt
```

---

## NSE Scripts — The ones we've used

```bash
# FTP — anonymous access
nmap --script ftp-anon -p21 10.129.1.10

# SMB — signing and shares
nmap --script smb2-security-mode -p445 10.129.1.10
nmap --script smb-enum-shares -p445 10.129.1.10

# RDP — NTLM info
nmap --script rdp-ntlm-info -p3389 10.129.1.10

# Rsync — list modules
nmap --script rsync-list-modules -p873 10.129.1.10

# MongoDB — databases
nmap --script mongodb-databases -p27017 10.129.1.10

# MySQL — empty password
nmap --script mysql-empty-password -p3306 10.129.1.10

# Redis — info
nmap --script redis-info -p6379 10.129.1.10
```

---

## Ports and Services — What we've seen

| Port | Service | What to check | Seen in |
| :----- | :------ | :----------- | :------ |
| **21** | FTP | Anonymous access, `ftp-anon` | Fawn, Crocodile |
| **80** | HTTP | Web app, Gobuster, virtual hosts | Preignition, Appointment, Crocodile, Responder |
| **135** | MSRPC | Windows RPC (part of the Windows pattern) | Dancing, Explosion |
| **139** | NetBIOS | SMB over NetBIOS | Dancing, Explosion |
| **445** | SMB | Shares, null session, signing check | Dancing, Explosion |
| **873** | Rsync | Anonymous modules | Synced |
| **3306** | MySQL | Root with no password | Sequel |
| **3389** | RDP | Administrator with empty password | Explosion |
| **5985** | WinRM | PowerShell shell (needs creds) | Dancing, Explosion, Responder |
| **6379** | Redis | No authentication | Redeemer |
| **27017** | MongoDB | No authentication | Mongod |

---

## Port States — What they mean

| State | Meaning | What to do |
| :---- | :--------- | :-------- |
| **open** | Service accepting connections | Enumerate further |
| **filtered** | Firewall blocking probes | Might be open but protected |
| **closed** | Port reachable but no service listening | Move on |

---

## Timing Templates

| Template | Flag | When to use |
| :------- | :--- | :----------- |
| **Aggressive** | `-T4` | **CTF standard** — fast, reliable networks |
| **Normal** | `-T3` | Default — balanced speed/stealth |

---

## Output Formats

| Flag | Format | When to use |
| :--- | :----- | :----------- |
| `-oN <file>` | Normal | Human-readable text |
| `-oA <basename>` | All formats | Saves `.nmap`, `.xml`, `.gnmap` |

---

## References

- [Official Nmap Documentation](https://nmap.org/docs.html)
- [Nmap NSE Scripts Reference](https://nmap.org/nsedoc/)
- [HackTricks — Nmap Cheatsheet](https://book.hacktricks.xyz/network-services-pentesting/cheatsheet-nmap)
