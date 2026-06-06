> **Nmap** (Network Mapper) is the industry-standard port scanning and network discovery tool. It's the first tool you'll run on every HTB box and CTF — from simple port checks to full NSE-powered service enumeration. This guide focuses on what you actually need for CTFs.

---

## Quickstart — The Scans You'll Actually Run

> ⭐ **My go-to commands — the ones I use in every writeup**
>
> This two-command workflow is my standard routine. First the full port scan, then the service scan on the discovered ports:
>
> ```bash
> # 1️⃣ Full port scan — find all open ports
> nmap -p- --open -sS --min-rate 5000 -vvv -n -Pn $IP
>
> # 2️⃣ Service + version + default scripts on the discovered ports
> nmap -sCV -p21,22,80,... $IP
> ```

```bash
# The one you'll use 80% of the time: service/version + default scripts
$ nmap -sCV -p- 10.129.1.10

# Fast top-1000 scan (good first pass, barely slower than -sV alone)
$ nmap -sCV 10.129.1.10

# Full port scan (all 65535) — do this while you explore manually
$ nmap -p- 10.129.1.10 -oN full-port-scan.txt

# Then service scan on the open ports found
$ nmap -sCV -p21,22,80,445 10.129.1.10

# Quick service/OS detection
$ nmap -sV -O 10.129.1.10

# Aggressive mode — all-in-one (don't use as first scan, too noisy)
$ nmap -A 10.129.1.10
```

### ✅ Before starting — essential checks

```bash
# Step 1 — Discover live hosts (ping sweep)
$ nmap -sn 10.129.1.0/24

# Step 2 — Quick port scan (top 1000 fast, then full port in background)
$ nmap -sCV 10.129.1.10

# Step 3 — Full port scan while you investigate the quick hits
$ nmap -p- 10.129.1.10 -oN full-ports.txt

# Step 4 — Deep service scan on all open ports
$ nmap -sCV -p $(awk -F'/' '/open/{print $1}' full-ports.txt | paste -sd,) 10.129.1.10
```

---

## Scan Types — When to Use Each

| Type | Flag | What it does | Speed | Privilege | Detection |
| :--- | :--- | :----------- | :---- | :-------- | :-------- |
| **SYN scan** | `-sS` | Half-open TCP scan (default with sudo) | ⚡ Fastest | Root | Low |
| **TCP connect** | `-sT` | Full TCP handshake (default without sudo) | 🐢 Slower | Any | Medium |
| **UDP scan** | `-sU` | Scan UDP ports (slow but necessary) | 🐌 Very slow | Root | Low |
| **Ping sweep** | `-sn` | Discover live hosts (no port scan) | ⚡ Instant | Any | Low |
| **Version detection** | `-sV` | Probe services for version info | 🐢 Slow | Root | Medium |
| **OS detection** | `-O` | Fingerprint OS via TCP/IP stack | ⚡ Fast | Root | Medium |
| **Aggressive** | `-A` | `-sV -O -sC --traceroute` combined | 🐢 Slow | Any | High |
| **No ping** | `-Pn` | Skip host discovery (target blocks ICMP) | ⚡ Fast | Any | None |

```bash
# SYN scan (needs sudo) — stealthy, fast
$ sudo nmap -sS -p- 10.129.1.10

# TCP connect scan (no sudo) — works but slower
$ nmap -sT -p- 10.129.1.10

# UDP scan — only scan interesting ports, don't do all 65535
$ sudo nmap -sU -p53,161,500,514,1434,1900 10.129.1.10

# Skip ping if host doesn't respond to ICMP (common on Windows firewalls)
$ nmap -Pn -sCV 10.129.1.10

# Force IPv4
$ nmap -4 -sCV 10.129.1.10
```

---

## Core Flags — The Ones You'll Actually Use

| Flag | What it does |
| :--- | :----------- |
| `-p <ports>` | Ports to scan (e.g., `-p22,80,443`, `-p-` all 65535, `-p1-10000`) |
| `--top-ports <n>` | Scan the top N most common ports (`--top-ports 1000` default) |
| `-sV` | Version detection — identify service versions |
| `-sC` | Run default NSE scripts (same as `--script=default`) |
| `-sV --version-intensity <0-9>` | Version probing intensity (0=light, 9=aggressive, default 7) |
| `-O` | OS detection (requires root) |
| `-A` | Aggressive mode: `-sV -O -sC --traceroute` |
| `-T<0-5>` | Timing template: `-T0` (paranoid) to `-T5` (insane). Default `-T3`, CTF standard `-T4` |
| `-Pn` | Skip host discovery (assume host is up) |
| `-n` | No DNS resolution (speed up scans) |
| `-sn` | Ping sweep only (no port scan) |
| `--open` | Show only open (or listening) ports |
| `--reason` | Show why Nmap determined port state |
| `--dns-server <ip>` | Use a custom DNS server for resolution |
| `--disable-arp-ping` | Disable ARP ping (useful in some local network scenarios) |
| `--exclude-ports <ports>` | Exclude specific ports from scan |
| `--exclude <host>` | Exclude hosts from scan |
| `-f` | Fragment packets (evade simple firewalls) |
| `--mtu <size>` | Set MTU for packet fragmentation |
| `--data-length <n>` | Append random data to packets (evade some IDS) |
| `--spoof-mac <mac>` | Spoof MAC address |
| `-D <decoy1,decoy2,ME>` | Decoy scan — blend with dummy IPs |
| `-S <src-ip>` | Spoof source IP address |
| `-e <interface>` | Use specific network interface |
| `--source-port <port>` | Set source port (bypass some firewall rules) |
| `--max-retries <n>` | Maximum probe retransmissions |
| `--min-rate <n>` | Minimum send rate in packets/sec |
| `--max-rate <n>` | Maximum send rate in packets/sec |
| `--host-timeout <time>` | Give up on host after N seconds (e.g., `30s`) |
| `--scan-delay <time>` | Delay between probes (e.g., `1s` for stealth) |
| `-v` / `-vv` | Increase verbosity (see open ports as they're found) |
| `-d` / `-dd` | Enable debugging output |

---

## NSE Scripts — Network Mapper Scripting Engine

### Default Scripts (`-sC` / `--script=default`)

The `-sC` flag runs a curated set of **safe-ish** scripts that are most likely to find useful information. This is always worth doing.

```bash
# Run default scripts (equivalent to -sC)
$ nmap --script=default -p22,80,443 10.129.1.10
```

### Protocol-specific scripts

```bash
# SMB enumeration
$ nmap --script smb-enum-shares,smb-enum-users,smb-os-discovery -p445 10.129.1.10
$ nmap --script smb-vuln-ms17-010 -p445 10.129.1.10          # EternalBlue

# HTTP enumeration
$ nmap --script http-enum,http-title,http-headers -p80,443 10.129.1.10
$ nmap --script http-methods,http-shellshock -p80 10.129.1.10

# FTP enumeration
$ nmap --script ftp-anon,ftp-syst -p21 10.129.1.10
$ nmap --script ftp-vsftpd-backdoor -p21 10.129.1.10

# MySQL enumeration
$ nmap --script mysql-empty-password,mysql-users,mysql-databases -p3306 10.129.1.10

# RDP enumeration
$ nmap --script rdp-ntlm-info,rdp-enum-encryption -p3389 10.129.1.10

# DNS enumeration
$ nmap --script dns-zone-transfer,dns-brute -p53 10.129.1.10

# LDAP enumeration
$ nmap --script ldap-rootdse -p389 10.129.1.10
```

### Vulnerability scanning scripts

```bash
# Check ALL known vuln scripts
$ nmap --script vuln -p21,22,80,445 10.129.1.10

# Check specific CVEs
$ nmap --script smb-vuln-* -p445 10.129.1.10
$ nmap --script rdp-vuln-* -p3389 10.129.1.10
$ nmap --script http-vuln-* -p80,443 10.129.1.10

# Brute-force scripts
$ nmap --script http-brute -p80 10.129.1.10
$ nmap --script ftp-brute -p21 10.129.1.10
$ nmap --script smb-brute -p445 10.129.1.10
```

### Discovery & safety scripts

```bash
# Service + version detection with safe scripts only
$ nmap -sV --script safe -p- 10.129.1.10

# Broadcast discovery (local network)
$ nmap --script broadcast-dhcp-discover
$ nmap --script broadcast-ping
```

### Script categories reference

| Category | Description | Safe? |
| :------- | :---------- | :---- |
| `default` (or `-sC`) | Usual safe scripts | ✅ |
| `safe` | Non-intrusive scripts | ✅ |
| `discovery` | Service/network discovery | ✅ |
| `version` | Version detection helpers | ✅ |
| `auth` | Authentication bypass | ⚠️ |
| `brute` | Brute-force attacks | ❌ |
| `dos` | Denial of service (⚠️ dangerous) | ❌ |
| `exploit` | Active exploitation attempts | ❌ |
| `external` | Sends data to third-party services | ⚠️ |
| `fuzzer` | Fuzzing scripts (slow, noisy) | ❌ |
| `intrusive` | May crash services, trigger alarms | ❌ |
| `malware` | Malware detection | ⚠️ |
| `vuln` | Vulnerability checks | ⚠️ |

```bash
# Combine safe scripts only
$ nmap --script "safe or default" -p- 10.129.1.10

# Exclude intrusive scripts
$ nmap --script "default and not intrusive" -p- 10.129.1.10

# Run all discovery + vuln
$ nmap --script "discovery or vuln" -p- 10.129.1.10
```

---

## Output Formats — Save Your Results

| Flag | Format | Use case |
| :--- | :----- | :------- |
| `-oN <file>` | Normal | Readable text — good for quick reference |
| `-oX <file>` | XML | Machine-parsable — for tools or scripts |
| `-oG <file>` | Greppable | `grep`-friendly — best for one-liner parsing |
| `-oA <basename>` | All formats | Saves `basename.nmap`, `basename.xml`, `basename.gnmap` |
| `-oS <file>` | Script kiddie | l33tspeak output (fun but useless) |

```bash
# Save everything for later analysis
$ nmap -sCV -p- 10.129.1.10 -oA scan-10.129.1.10

# Greppable output — easy to parse with grep/awk
$ nmap -sCV -p- 10.129.1.10 -oG scan.gnmap
$ grep -E '/open/' scan.gnmap | awk -F' ' '{print $NF}'  # extract port info

# Append to a file (resume flag)
$ nmap --resume scan-full-ports.nmap
```

---

## Port States — What They Mean

| State | Meaning | What to do |
| :---- | :------ | :--------- |
| **open** | Service is actively accepting connections | Immediate target — enumerate further |
| **filtered** | Firewall is blocking probes | Could be open but protected — try different scan type |
| **closed** | Port is reachable but no service listening | Move on, but note this means host is up |
| **unfiltered** | Port is reachable but state unknown | Try `-sS` or `-sT` to determine open/closed |
| **open\|filtered** | Can't distinguish between open and filtered | Try version detection or UDP scan |
| **closed\|filtered** | Can't distinguish between closed and filtered | Rare — IP protocol scan only |

---

## Timing Templates — Speed vs Stealth

| Template | Flag | Use case |
| :------- | :--- | :------- |
| **Paranoid** | `-T0` | IDS evasion — serial scan, minutes between probes |
| **Sneaky** | `-T1` | Stealthy — 15s between probes |
| **Polite** | `-T2` | Less bandwidth (0.4s delay) |
| **Normal** | `-T3` | Default — balanced speed/stealth |
| **Aggressive** | `-T4` | **CTF standard** — fast, reliable networks |
| **Insane** | `-T5` | Very fast LAN — may miss ports on slow networks |

```bash
# CTF standard — -T4 is almost always fine
$ nmap -T4 -sCV 10.129.1.10

# Faster full port scan on local network
$ nmap -T5 -p- --min-rate 10000 10.129.1.10

# Slow stealth scan for IDS-heavy environments
$ nmap -T1 -sS -p- 10.129.1.10
```

---

## CTF / HTB Techniques

### 1. The Pipeline — Full Enumeration Workflow

```bash
#!/bin/bash
TARGET="10.129.1.10"

# Stage 1 — Quick scan to find what's open
nmap -T4 -sCV $TARGET -oN quick-scan.txt

# Stage 2 — Full port scan (all 65535) in background
nmap -T4 -p- $TARGET -oN full-ports.txt

# Wait... while you investigate the quick scan results
# When full-ports.txt finishes:

# Stage 3 — Deep scan on all discovered ports
PORTS=$(awk -F'/' '/open/{print $1}' full-ports.txt | paste -sd,)
nmap -T4 -sCV -p $PORTS $TARGET -oN deep-scan.txt

# Stage 4 — Vulnerability scan
nmap --script vuln -p $PORTS $TARGET -oN vuln-scan.txt

# Stage 5 — UDP scan on key ports
nmap -sU --top-ports 20 $TARGET -oN udp-scan.txt
```

### 2. Top Services and Ports — What Each Means

| Port | Service | What to check |
| :--- | :------ | :------------ |
| **21** | FTP | Anonymous access, vsftpd backdoor |
| **22** | SSH | Version, brute force |
| **25** | SMTP | Open relay, user enumeration |
| **53** | DNS | Zone transfer, subdomain brute force |
| **80** | HTTP | Web app enumeration |
| **88** | Kerberos | User enumeration (krb5-enum-users) |
| **110** | POP3 | Mail access |
| **111** | RPC | NFS enumeration |
| **135** | MSRPC | Windows RPC services |
| **139** | NetBIOS | SMB over NetBIOS |
| **143** | IMAP | Mail access |
| **161** | SNMP | Community strings, info disclosure |
| **389** | LDAP | Directory enumeration |
| **443** | HTTPS | Web app (TLS) |
| **445** | SMB | Shares, EternalBlue, SMBGhost |
| **500** | ISAKMP | VPN key exchange (UDP) |
| **514** | Syslog | Log monitoring |
| **587** | SMTP | Mail submission |
| **636** | LDAPS | Secure LDAP |
| **993** | IMAPS | Secure IMAP |
| **995** | POP3S | Secure POP3 |
| **1433** | MSSQL | Database access |
| **1521** | Oracle | Database access |
| **2049** | NFS | Share enumeration |
| **2100** | Oracle XML DB | Oracle Services |
| **2375** | Docker | Docker API (unauthenticated) |
| **2376** | Docker TLS | Docker API (TLS) |
| **3306** | MySQL | Database enumeration |
| **3389** | RDP | Remote Desktop, Pass-the-Hash |
| **4444** | Metasploit | Default reverse shell listener |
| **4848** | GlassFish | Admin console |
| **5000** | Flask/Node | Custom web apps |
| **5432** | PostgreSQL | Database enumeration |
| **5900** | VNC | Remote desktop (check for no-auth) |
| **5901** | VNC | Usually VNC display :1 |
| **5985** | WinRM HTTP | Windows Remote Management |
| **5986** | WinRM HTTPS | Secure WinRM |
| **6379** | Redis | Unauthenticated access, RCE |
| **8080** | HTTP-Proxy | Web app / proxy |
| **8443** | HTTPS-Alt | Alternative HTTPS |
| **27017** | MongoDB | Unauthenticated database access |
| **27018** | MongoDB | Shard server |

### 3. OS Detection

```bash
# Basic OS detection
$ sudo nmap -O 10.129.1.10

# OS detection with version scanning
$ sudo nmap -sV -O 10.129.1.10

# OS detection + default scripts + version
$ sudo nmap -sCV -O 10.129.1.10

# OS detection guess (less accurate, but works when fingerprint fails)
$ sudo nmap -O --osscan-guess 10.129.1.10

# Limit OS detection attempts to 1 (faster)
$ sudo nmap -O --max-os-tries 1 10.129.1.10
```

```bash
# Example output
$ sudo nmap -O 10.129.1.10
...
Device type: general purpose
Running: Linux 3.X|4.X
OS CPE: cpe:/o:linux:linux_kernel:3 cpe:/o:linux:linux_kernel:4
OS details: Linux 3.2 - 4.9
...
```

### 4. Quick Service/Version Probe — Custom Intensity

```bash
# Light version probing (faster, less accurate)
$ nmap -sV --version-intensity 2 -p- 10.129.1.10

# Full version probe (slowest, most accurate)
$ nmap -sV --version-intensity 9 -p- 10.129.1.10

# Light + full combo
$ nmap -sV --version-intensity 2 -p- 10.129.1.10 -oN light.txt
$ nmap -sV --version-intensity 9 -p $(awk -F'/' '/open/{print $1}' light.txt | paste -sd,) 10.129.1.10
```

### 5. Evasion — Get Past Firewalls

```bash
# Fragment packets
$ sudo nmap -f -sS -p- 10.129.1.10

# Use decoys (blend with fake IPs)
$ sudo nmap -D 10.0.0.1,10.0.0.2,ME -sS 10.129.1.10

# Random data length (evades signature-based detection)
$ sudo nmap --data-length 25 -sS -p- 10.129.1.10

# Source port manipulation (some firewalls allow port 53 or 20)
$ sudo nmap --source-port 53 -sS 10.129.1.10

# Spoof MAC address
$ sudo nmap --spoof-mac Cisco -sS 10.129.1.10

# Custom MTU
$ sudo nmap --mtu 24 -sS -p- 10.129.1.10

# Idle scan (zombie host required)
$ sudo nmap -sI <zombie-ip> 10.129.1.10
```

### 6. Nmap with Proxychains

```bash
# Scan through a SOCKS proxy
$ proxychains4 nmap -sT -Pn -sV -p22,80,443 10.129.1.10
```

> ℹ️ Proxychains only works with TCP connect scan (`-sT`). SYN scan (`-sS`) doesn't work because it requires raw socket access.

### 7. NSE Script with Arguments

```bash
# HTTP brute force with custom user/pass lists
$ nmap --script http-brute -p80 --script-args userdb=users.txt,passdb=pass.txt 10.129.1.10

# FTP brute force with custom args
$ nmap --script ftp-brute -p21 --script-args brute.threads=8,brute.userastext=on 10.129.1.10

# SMB vulnerability check with arguments
$ nmap --script smb-vuln-ms17-010 -p445 --script-args smb-vuln-ms17-010.check-version=true 10.129.1.10

# DNS brute force with custom wordlist
$ nmap --script dns-brute -p53 --script-args dns-brute.domain=example.htb,dns-brute.wordlist=subdomains.txt 10.129.1.10
```

---

## Automation & One-liners

### One-liner — extract open ports from grepable output

```bash
grep -E '^[0-9]' scan.gnmap | awk -F'/' '{print $1}' | paste -sd,
```

### One-liner — scan and save only open ports

```bash
nmap -p- --open -oG - 10.129.1.10 | grep -oP '\d+/open/tcp//' | cut -d'/' -f1 | paste -sd,
```

### One-liner — service scan on previously discovered ports

```bash
nmap -sCV -p $(grep -oP '\d+/open/tcp//' scan.gnmap | cut -d'/' -f1 | paste -sd,) 10.129.1.10
```

### One-liner — ping sweep entire subnet

```bash
nmap -sn 10.129.1.0/24 -oG - | grep -E '/Up/' | awk '{print $2}'
```

### One-liner — masscan equivalent (fast port scan with nmap)

```bash
nmap -T5 --min-rate 10000 -p- --open 10.129.1.10 -oN fast-all-ports.txt
```

### One-liner — scan multiple targets from a file

```bash
while read ip; do
  nmap -T4 -sCV -oN "scan-$ip.txt" $ip
done < targets.txt
```

### One-liner — scan + parse + launch browser

```bash
nmap -sCV -p- 10.129.1.10 -oA scan && \
  grep -E '80/open|443/open|8080/open' scan.gnmap | \
  awk '{print "http://" $2}' | xargs -I{} xdg-open {}
```

### One-liner — auto-version probe on all open ports

```bash
nmap -p- --open -oG - 10.129.1.10 | \
  grep -oP '\d+/open/tcp//' | cut -d'/' -f1 | \
  paste -sd, | xargs -I{} nmap -sCV -p{} 10.129.1.10 -oA deep-scan
```

### Full pipeline — Discover, scan, enumerate

```bash
#!/bin/bash
SUBNET="10.129.1.0/24"

echo "[*] Ping sweep..."
nmap -sn $SUBNET -oG ping.txt

for ip in $(grep -E '/Up/' ping.txt | awk '{print $2}'); do
  echo "[*] Scanning $ip..."
  nmap -T4 -p- --open $ip -oN "$ip-ports.txt"
  PORTS=$(grep -oP '\d+/open/tcp//' "$ip-ports.txt" | cut -d'/' -f1 | paste -sd,)
  
  if [ -n "$PORTS" ]; then
    nmap -T4 -sCV -p $PORTS $ip -oA "$ip-service"
    nmap --script vuln -p $PORTS $ip -oN "$ip-vuln.txt"
  fi
  
  echo "[+] Done: $ip"
done
```

---

## Masscan — Faster Than Nmap for Full Port Scans

```bash
# Install
$ sudo apt install masscan

# Full port scan — much faster than nmap
$ sudo masscan -p1-65535 --rate=1000 10.129.1.10

# Output in nmap-compatible greppable format
$ sudo masscan -p1-65535 --rate=1000 10.129.1.10 -oG masscan.gnmap

# Specific ports + rate + output
$ sudo masscan -p80,443,22,445,3306,3389 --rate=500 10.129.1.10 -oG masscan.gnmap

# Then pipe to nmap for service enumeration
$ nmap -sCV -p $(grep -oP '\d+/open/tcp//' masscan.gnmap | cut -d'/' -f1 | paste -sd,) 10.129.1.10
```

> ℹ️ Masscan is 10-100x faster than nmap for full port scans. Use it for the initial `-p-` pass, then feed the results to nmap for version/service detection.

---

## Troubleshooting — What You'll Actually See

| Error / Symptom | Likely Cause |
| :-------------- | :----------- |
| `Failed to resolve "10.129.1.10"` | Forgot `-n` or DNS is slow — add `-n` to skip DNS |
| `Host seems down. If it is really up...` | Host blocks ICMP — use `-Pn` |
| `Note: Host seems down` | Same as above — use `-Pn` |
| All ports `filtered` | Firewall is dropping packets — try `-sS` (root) or `-Pn` |
| `You requested a scan type which requires root privileges` | SYN scan (`-sS`) needs sudo — use `sudo nmap` or `-sT` |
| `SERVICE: p912-serv` or weird service names | Version detection misidentified — increase `--version-intensity` |
| Scan is extremely slow | Too few ports or timing too low — add `-T4` or limit ports |
| `Nmap done: 1 IP address (0 hosts up)` | Firewall is blocking everything — add `-Pn` |
| Scan reports ports but `nc` can't connect | Firewall allows SYN but blocks handshake — try `-sT` |
| No results in `-sU` scan | UDP scan is slow by nature — limit to ~10 ports and be patient |
| `Failed to open normal output file` | Directory doesn't exist or no write permissions |
| `masscan: command not found` | Install masscan: `sudo apt install masscan` |

---

## References

- [Official Nmap Documentation](https://nmap.org/docs.html)
- [Nmap NSE Scripts Reference](https://nmap.org/nsedoc/)
- [Nmap Book (Gordon Lyon)](https://nmap.org/book/)
- [Masscan — GitHub](https://github.com/robertdavidgraham/masscan)
- [HackTricks — Nmap Cheatsheet](https://book.hacktricks.xyz/network-services-pentesting/cheatsheet-nmap)
- [SecLists — Wordlists for NSE scripts](https://github.com/danielmiessler/SecLists)
- [Nmap Ports Top 1000](https://nmap.org/book/nmap-services.html)
