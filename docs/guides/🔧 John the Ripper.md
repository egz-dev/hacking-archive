> **John the Ripper (JtR)** is one of the most versatile password cracking tools used in CTFs and penetration testing. It supports hundreds of hash formats — from NTLM and Kerberos to SSH keys, ZIP/RAR archives, PDFs, and database hashes. This guide covers everything from quick one-liners to advanced cracking techniques for real-world CTF scenarios.

---

## Quickstart — The 5-Minute Crack

```bash
# The most common CTF cracking workflow:
# 1. Capture or extract the hash
responder -I tun0                  # captures NTLMv2 hashes

# 2. Identify the hash type (JtR usually auto-detects)
john --list=formats                # see all supported formats
john hash.txt                      # auto-detect + crack

# 3. Crack with a wordlist
john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt

# 4. View results
john --show hash.txt
```

> 💡 **Key difference from Hashcat:** John auto-detects hash formats and handles file conversions (via `*2john` tools). Hashcat requires you to specify the mode (`-m`) and is generally faster for GPU cracking. For CTFs, John is often faster to set up.

---

## Hash Format Detection & Listing

```bash
# List all supported hash formats
john --list=formats

# List formats filtered by keyword
john --list=formats | grep -i ntlm
john --list=formats | grep -i krb
john --list=formats | grep -i ssh

# Auto-detect hash type (JtR guesses from format)
john hash.txt

# Force a specific format
john --format=nt hash.txt
john --format=netntlmv2 hash.txt

# Test if a format works
john --test --format=nt
```

### Common Hash Formats for CTFs

| Format | `--format=` flag | Source |
| :----- | :--------------- | :----- |
| NTLM (Windows SAM) | `nt` | `secretsdump.py`, SAM dump |
| Net-NTLMv2 (Responder) | `netntlmv2` | Responder capture |
| Net-NTLMv1 (Responder) | `netntlm` | Responder capture |
| Kerberos TGS (Kerberoast) | `krb5tgs` | `GetUserSPNs.py` / `krb5tgs2john.py` |
| Kerberos AS-REP (AS-REP Roast) | `krb5asrep` | `GetNPUsers.py` / `krb52john.py` |
| MD5 / raw-MD5 | `raw-md5` | Generic MD5 |
| SHA-256 / raw-SHA256 | `raw-sha256` | Generic SHA-256 |
| SHA-512 / raw-SHA512 | `raw-sha512` | Generic SHA-512 |
| bcrypt | `bcrypt` | PHP, Django, modern apps |
| Linux /etc/shadow | `sha512crypt` / `sha256crypt` | `unshadow` output |
| SSH private key | `ssh` | `ssh2john` output |
| RAR archive | `rar` | `rar2john` output |
| ZIP archive | `zip` | `zip2john` output |
| 7z archive | `7z` | `7z2john` output |
| PDF | `pdf` | `pdf2john` output |
| KeePass | `keepass` | `keepass2john` output |
| MySQL | `mysql-sha1` | `mysql2john` output |
| MSSQL | `mssql` | `mssql2john.py` output |
| PostgreSQL | `postgres` | Manual extraction |
| Cached Windows credentials | `mscash` | `cachedump.py` output |
| WPA/WPA2 | `wpapsk` | `hcxpcapngtool` output |
| Django PBKDF2 | `django` | Manual extraction |
| Django bcrypt | `bcrypt` | Manual extraction |

---

## Attack Modes

### 1. Wordlist Attack

```bash
# Basic wordlist attack
john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt

# With rules for password mutation
john --wordlist=/usr/share/wordlists/rockyou.txt --rules hash.txt

# Force format
john --wordlist=/usr/share/wordlists/rockyou.txt --rules --format=netntlmv2 hash.txt
```

### 2. Rules — Password Mutation

Rules apply patterns to wordlist entries (e.g., `password` → `P@ssw0rd123`).

```bash
# Built-in rules (in john.conf)
john --wordlist=rockyou.txt --rules=best64 hash.txt       # fast, common mutations
john --wordlist=rockyou.txt --rules=d3ad0ne hash.txt      # broad, aggressive
john --wordlist=rockyou.txt --rules=rockyou-30000 hash.txt # top 30k mutations
john --wordlist=rockyou.txt --rules=jumbo hash.txt        # all built-in rules

# Custom rules (edit ~/.john/john.conf)
[List.Rules:MyCustom]
# Append year
Az"[0-9][0-9][0-9][0-9]"
# Prepend capital + append number + special
c Az"[0-9]" $[!@#$]
# Leetspeak substitution
sa@ se3 si1 so0 ss$
```

### 3. Mask Attack (Brute Force / Pattern)

Use masks when you know the password structure.

```bash
# Mask placeholders
# ?l = lowercase (a-z)
# ?u = uppercase (A-Z)
# ?d = digit (0-9)
# ?s = special (!@#$%^&*)
# ?a = all characters
# ?b = all bytes (0x00-0xff)

# 8-char lowercase password
john --mask='?l?l?l?l?l?l?l?l' hash.txt

# Password starting with capital, ending with 4 digits
john --mask='?u?l?l?l?l?l?d?d?d?d' hash.txt

# Custom charset (e.g., only HEX chars)
john --mask='?1?1?1?1?1?1?1?1' --charsets='?1=abcdef0123456789' hash.txt

# 6-digit PIN
john --mask='?d?d?d?d?d?d' hash.txt

# Password + year
john --mask='?l?l?l?l?l?l20?d?d' hash.txt
```

### 4. Incremental Mode (Full Brute Force)

```bash
# Incremental lowercase (a-z, all lengths)
john --incremental=lower hash.txt

# Incremental all (a-z, A-Z, 0-9, special)
john --incremental=all hash.txt

# Incremental digits only (0-9)
john --incremental=digits hash.txt
```

> ⚠️ **Incremental mode is VERY slow.** Use wordlists + rules first. Only use incremental for short passwords or small hash lists.

---

## Cracking NTLM / Net-NTLMv2 (Responder Captures)

### From Responder Output

```bash
# Responder saves captures to /usr/share/responder/logs/
# NTLMv2 hashes are in: SMB-NTLMv2-*.txt

# Crack directly with John
john --format=netntlmv2 --wordlist=/usr/share/wordlists/rockyou.txt /usr/share/responder/logs/SMB-NTLMv2-*.txt

# Or copy the hash to a file first
cp /usr/share/responder/logs/SMB-NTLMv2-*.txt hash.txt
john --format=netntlmv2 --wordlist=rockyou.txt hash.txt
```

### Hash Format (NTLMv2)

```
username::domain:ServerChallenge:NTProofStr:NTResponse
```

Example:
```
admin::WORKGROUP:1122334455667788:a3b4c5d6e7f8091a2b3c4d5e6f708192:0101000000000000...
```

### From secretsdump (SAM Dump)

```bash
# Extract SAM hashes with Impacket
impacket-secretsdump 'DOMAIN/user:password@10.10.10.10' > secrets.txt

# Or dump SAM locally (if you have admin)
impacket-secretsdump SAM:SAMSYSTEM:SECURITY

# Format the output for John (NTLM hashes)
# secretsdump output is already in hashcat format, convert for JtR:
grep -E "^Administrator:" secrets.txt | cut -d: -f1,3 > hash.txt
# Then use format=nt

# Or crack directly (secretsdump output is often already JtR-compatible)
john --format=nt --wordlist=rockyou.txt hash.txt
```

---

## Cracking Kerberos Hashes

### Kerberoasting (TGS-REP)

```bash
# Step 1: Request TGS tickets for SPN accounts
impacket-GetUserSPNs 'DOMAIN/user:password' -dc-ip 10.10.10.10 -request > kerberoast.txt

# Step 2: Extract the hash (format varies by tool)
# From GetUserSPNs output, copy the hash to a file:
# $krb5tgs$23$*user$DOMAIN$SPN*$<hash>

# Step 3: Crack with John
john --format=krb5tgs --wordlist=rockyou.txt kerberoast.txt

# Or with rules
john --format=krb5tgs --wordlist=rockyou.txt --rules=best64 kerberoast.txt
```

### AS-REP Roasting

```bash
# Step 1: Find accounts with "Do not require Kerberos preauthentication"
impacket-GetNPUsers 'DOMAIN/user:password' -dc-ip 10.10.10.10 -no-pass -usersfile users.txt -outputfile asrep.txt

# Step 2: Crack the AS-REP hash
john --format=krb5asrep --wordlist=rockyou.txt asrep.txt
```

---

## Cracking Linux Passwords (/etc/shadow)

```bash
# Step 1: Combine /etc/passwd and /etc/shadow
unshadow /etc/passwd /etc/shadow > unshadow.txt

# Step 2: Crack
john --wordlist=rockyou.txt unshadow.txt

# Step 3: View results
john --show unshadow.txt
```

> 💡 Modern Linux uses SHA-512 (`$6$`) or SHA-256 (`$5$`) hashes. John auto-detects the format.

---

## Cracking SSH Private Key Passwords

```bash
# Step 1: Convert SSH key to John format
ssh2john id_rsa > id_rsa.hash

# Step 2: Crack
john --wordlist=rockyou.txt id_rsa.hash

# Step 3: Use the cracked key
chmod 600 id_rsa
ssh -i id_rsa user@target
```

---

## Cracking Archive Passwords (ZIP / RAR / 7z)

### ZIP

```bash
# Convert ZIP to John format
zip2john protected.zip > zip.hash

# Crack
john --wordlist=rockyou.txt zip.hash
```

### RAR

```bash
# Convert RAR to John format
rar2john protected.rar > rar.hash

# Crack
john --wordlist=rockyou.txt rar.hash
```

### 7z

```bash
# Convert 7z to John format
7z2john protected.7z > 7z.hash

# Crack
john --wordlist=rockyou.txt 7z.hash
```

---

## Cracking PDF Passwords

```bash
# Convert PDF to John format
pdf2john protected.pdf > pdf.hash

# Crack
john --wordlist=rockyou.txt pdf.hash
```

---

## Cracking KeePass Databases

```bash
# Convert KeePass to John format
keepass2john database.kdbx > keepass.hash

# Crack
john --wordlist=rockyou.txt keepass.hash
```

---

## Cracking Database Passwords

### MySQL

```bash
# From MySQL dump (hash in format: *<40-char-hex>)
# Save the hash to a file, then:
john --format=mysql-sha1 --wordlist=rockyou.txt mysql.hash
```

### MSSQL

```bash
# Use mssql2john.py (from Impacket or JtR contrib)
python3 /usr/share/john/mssql2john.py mssql.hash > mssql_john.txt

john --format=mssql --wordlist=rockyou.txt mssql_john.txt
```

### PostgreSQL

```bash
# Extract hash from pg_shadow table
# MD5 format: md5<32chars>
# Save to file, then:
john --format=postgres --wordlist=rockyou.txt pg.hash
```

---

## Cracking WPA/WPA2 Handshakes

```bash
# Convert pcap/pcapng to JtR format
hcxpcapngtool -o handshake.hc22000 capture.pcapng

# Crack WPA2
john --format=wpapsk --wordlist=rockyou.txt handshake.hc22000

# Or with rules for better coverage
john --format=wpapsk --wordlist=rockyou.txt --rules=best64 handshake.hc22000
```

---

## *2john Conversion Tools — Cheat Sheet

| Tool | Converts | Source |
| :--- | :------- | :----- |
| `ssh2john` | SSH private key → hash | `ssh2john id_rsa > hash.txt` |
| `zip2john` | ZIP archive → hash | `zip2john file.zip > hash.txt` |
| `rar2john` | RAR archive → hash | `rar2john file.rar > hash.txt` |
| `7z2john` | 7z archive → hash | `7z2john file.7z > hash.txt` |
| `pdf2john` | PDF → hash | `pdf2john file.pdf > hash.txt` |
| `keepass2john` | KeePass DB → hash | `keepass2john database.kdbx > hash.txt` |
| `unshadow` | Linux shadow+passwd → hash | `unshadow /etc/passwd /etc/shadow > hash.txt` |
| `krb5tgs2john.py` | Kerberos TGS → hash | `krb5tgs2john.py ticket.kirbi > hash.txt` |
| `krb52john.py` | Kerberos AS-REP → hash | `krb52john.py asrep.txt > hash.txt` |
| `netntlm2john.py` | Net-NTLMv2 → hash | `netntlm2john.py responder.txt > hash.txt` |
| `mysql2john.py` | MySQL hash → hash | `mysql2john.py hash.txt > john_hash.txt` |
| `mssql2john.py` | MSSQL hash → hash | `mssql2john.py hash.txt > john_hash.txt` |
| `dpapi2john.py` | DPAPI → hash | `dpapi2john.py master.key > hash.txt` |

---

## Session Management

```bash
# Start a named session (auto-saves progress)
john --session=crack1 --wordlist=rockyou.txt hash.txt

# Restore an interrupted session
john --restore=crack1

# Show cracked passwords from a session
john --show --session=crack1 hash.txt

# List all sessions
ls ~/.john/

# Delete a session (force re-crack)
rm ~/.john/john_restore
```

> 💡 **Always use sessions for long-running cracks.** John saves progress automatically — you can Ctrl+C and resume later with `--restore`.

---

## GPU Acceleration (OpenCL)

```bash
# Check available OpenCL devices
john --list=formats --format=opencl-nt 2>&1 | head -5

# Crack with GPU (format names include "opencl-")
john --format=opencl-raw-md5 --wordlist=rockyou.txt hash.txt
john --format=opencl-nt --wordlist=rockyou.txt hash.txt

# Fork across multiple CPU cores (no GPU needed)
john --format=nt --fork=4 --wordlist=rockyou.txt hash.txt
```

> 💡 **Hashcat vs John for GPU:** Hashcat is generally 2-10x faster for GPU cracking. Use Hashcat for large-scale brute force, John for quick one-liners and format auto-detection.

---

## Advanced Techniques

### Custom Rules (john.conf)

```bash
# Edit ~/.john/john.conf and add a custom rule section:

[List.Rules:CTF]
# Append 4 digits
Az"[0-9][0-9][0-9][0-9]"
# Capitalize first letter + append year
c Az"20[0-9][0-9]"
# Leetspeak + append special char
sa@ se3 si1 so0 ss$ $!
# Mixed case + numbers
c $[0-9] $[0-9]
```

### External Mode (Custom Logic)

```bash
# Use external wordlist generator (edit john.conf [List.External:MyMode])
john --external=MyMode hash.txt
```

### Cracking Multiple Hash Files

```bash
# John can handle multiple files at once
john hash1.txt hash2.txt hash3.txt

# Or all files in a directory
for f in hashes/*.txt; do john --wordlist=rockyou.txt "$f"; done
```

### Viewing Uncracked Hashes

```bash
# Show only uncracked hashes
john --show --format=netntlmv2 hash.txt | grep -v ":"

# Or use --list=left to see remaining hashes
john --list=left hash.txt
```

---

## JtR vs Hashcat — When to Use Which

| Feature | John the Ripper | Hashcat |
| :------ | :-------------- | :------ |
| **Best for** | Quick one-liners, format auto-detection, file conversions | Large-scale GPU cracking, complex rules |
| **Hash formats** | 300+ (auto-detect) | 300+ (must specify `-m`) |
| **GPU support** | OpenCL (slower) | CUDA/OpenCL (much faster) |
| **Setup** | `john hash.txt` (minimal config) | Requires mode + device selection |
| **Session mgmt** | Built-in restore | Built-in restore |
| **Rules** | Built-in + custom in john.conf | Separate .rule files |
| **Wordlists** | Any text file | Any text file |
| **CTF recommendation** | Start here for speed | Use for GPU brute force |

> 💡 **CTF workflow:** Start with John for quick auto-detection. If you need GPU speed or specific hash modes, switch to Hashcat.

---

## Essential Wordlists

```bash
# RockYou (the standard CTF wordlist)
/usr/share/wordlists/rockyou.txt.gz    # Debian/Kali (gunzip first)

# SecLists (comprehensive collection)
git clone https://github.com/danielmiessler/SecLists
# Popular paths:
# SecLists/Passwords/Common-Credentials/rockyou-25.txt
# SecLists/Passwords/Leaked-Databases/rockyou.txt
# SecLists/Passwords/Default-Credentials/default-passwords.txt

# CrackStation (large compiled list)
wget https://crackstation.net/files/crackstation.txt.gz
```

---

## CTF / HTB John the Ripper Workflow Checklist

1. **Identify the hash type** — `john hash.txt` (auto-detect) or `john --list=formats | grep -i keyword`
2. **Convert if needed** — use `*2john` tools (`ssh2john`, `zip2john`, `rar2john`, etc.)
3. **Crack with wordlist first** — `john --wordlist=rockyou.txt hash.txt`
4. **Add rules if wordlist fails** — `john --wordlist=rockyou.txt --rules=best64 hash.txt`
5. **Try mask attack** — `john --mask='?u?l?l?l?l?l?d?d' hash.txt`
6. **Check session progress** — `john --show hash.txt` or `john --list=left hash.txt`
7. **Use GPU if available** — switch to Hashcat for speed, or `john --format=opencl-*`
8. **For Kerberoast** — use `--format=krb5tgs`; for AS-REP — `--format=krb5asrep`
9. **For Responder captures** — `--format=netntlmv2` on the `.txt` file from `/usr/share/responder/logs/`
10. **Restore interrupted sessions** — `john --restore`

---

## Troubleshooting

| Issue | Cause | Fix |
| :---- | :---- | :-- |
| "No password hashes loaded" | Wrong hash format or empty file | Check hash format with `john --list=formats`, verify file is not empty |
| "Unknown ciphertext format" | Hash not recognized | Try `*2john` conversion tool, or force `--format=` |
| "Invalid hash" | Malformed hash or wrong line endings | Run `dos2unix hash.txt` to fix line endings |
| Cracking is extremely slow | Incremental mode on large charset | Use wordlist + rules first, reserve incremental for last resort |
| Session won't restore | Session file corrupted | Delete `~/.john/john_restore` and re-crack |
| "No devices found" (OpenCL) | GPU not configured | Install OpenCL drivers, or use CPU mode |
| Wrong passwords shown | Hash format mismatch | Specify correct `--format=` flag |
| `ssh2john` not found | Missing JtR contrib scripts | `locate ssh2john` or `find / -name "*2john*" 2>/dev/null` |
| Rules produce no results | Rule syntax error | Check `john.conf` for rule syntax, try built-in rules first |
| Hashcat shows "Token length exception" | Hash format wrong | Use `--show` in John to verify format, or try Hashcat's `--example-hashes` |

---

## Installing Tools

```bash
# John the Ripper (Jumbo version — has all formats)
# Debian/Kali
sudo apt install john

# Arch
sudo pacman -S john

# Build from source (latest version with all features)
git clone https://github.com/openwall/john src/john
cd src/john/src
./configure && make -s
# Binary at ../run/john

# Impacket (secretsdump, GetNPUsers, GetUserSPNs, etc.)
pip install impacket

# Hashcat (alternative GPU cracker)
sudo apt install hashcat

# Responder (NTLM hash capture)
sudo apt install responder

# hcxpcapngtool (WPA handshake conversion)
sudo apt install hcxtools
```

---

## References

- [John the Ripper Documentation](https://www.openwall.com/john/doc/)
- [John the Ripper Jumbo GitHub](https://github.com/openwall/john)
- [Hashcat Wiki](https://hashcat.net/wiki/doku.php?id=example_hashes)
- [PayloadsAllTheThings — Cracking](https://github.com/swisskyrepo/PayloadsAllTheThings/blob/master/Methodology%20and%20Resources/Hash%20Cracking.md)
- [HackTricks — Hash Cracking](https://book.hacktricks.xyz/generic-methodologies-and-resources/tips-and-tricks-getting-credentials)
- [SecLists — Passwords](https://github.com/danielmiessler/SecLists/tree/master/Passwords)
- [CrackStation — Online Hash Cracker](https://crackstation.net/)
