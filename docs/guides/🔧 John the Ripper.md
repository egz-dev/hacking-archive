---
tags: [cracking]
---

> **John the Ripper (JtR)** is a password cracking tool that supports hundreds of hash formats. This guide covers what we've practiced: cracking NTLMv2 hashes captured with Responder.

---

## Quickstart — Crack NTLMv2

```bash
# 1. Capture the hash with Responder
sudo responder -I tun0
# The hash appears in: /usr/share/responder/logs/SMB-NTLMv2-*.txt

# 2. Crack with John (auto-detects the format)
john hash.txt

# 3. Or force the format and use a wordlist
john --format=netntlmv2 --wordlist=/usr/share/wordlists/rockyou.txt hash.txt

# 4. Show results
john --show hash.txt
```

---

## NTLMv2 hash format

```
username::domain:ServerChallenge:NTProofStr:NTResponse
```

Example:
```
admin::WORKGROUP:1122334455667788:a3b4c5d6e7f8091a2b3c4d5e6f708192:0101000000000000...
```

---

## Attack modes

### 1. Wordlist Attack

```bash
# Basic wordlist attack
john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt

# With rules for password mutation
john --wordlist=/usr/share/wordlists/rockyou.txt --rules hash.txt

# Force format
john --wordlist=/usr/share/wordlists/rockyou.txt --rules --format=netntlmv2 hash.txt
```

### 2. Auto-detection

```bash
# John auto-detects the hash format
john hash.txt

# List all supported formats
john --list=formats

# Filter formats by keyword
john --list=formats | grep -i ntlm
```

---

## Session management

```bash
# Start a named session (auto-saves progress)
john --session=crack1 --wordlist=rockyou.txt hash.txt

# Restore an interrupted session
john --restore=crack1

# Show cracked passwords
john --show hash.txt
```

> 💡 **Always use sessions for long cracks.** John saves progress automatically — you can Ctrl+C and resume with `--restore`.

---

## Essential wordlists

```bash
# RockYou (the standard CTF wordlist)
/usr/share/wordlists/rockyou.txt.gz    # Debian/Kali (gunzip first)

# SecLists (full collection)
git clone https://github.com/danielmiessler/SecLists
```

---

## CTF Workflow

1. **Capture the hash** — with Responder or another tool
2. **Identify the format** — `john hash.txt` (auto-detects) or `john --list=formats | grep keyword`
3. **Crack with wordlist first** — `john --wordlist=rockyou.txt hash.txt`
4. **Add rules if wordlist fails** — `john --wordlist=rockyou.txt --rules=best64 hash.txt`
5. **Check progress** — `john --show hash.txt`
6. **Restore interrupted sessions** — `john --restore`

---

## 🔗 Related

**Machines:** [[🧑‍🚒 Responder]]

**Guides:** [[🔐 NTLM]], [[🖥️ WinRM]]

---

## References

- [John the Ripper Documentation](https://www.openwall.com/john/doc/)
- [PayloadsAllTheThings — Cracking](https://github.com/swisskyrepo/PayloadsAllTheThings/blob/master/Methodology%20and%20Resources/Hash%20Cracking.md)
- [HackTricks — Hash Cracking](https://book.hacktricks.xyz/generic-methodologies-and-resources/tips-and-tricks-getting-credentials)
