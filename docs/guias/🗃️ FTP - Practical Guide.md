> **FTP** transfers files over TCP on two channels: **control** (port 21) and **data** (port 20 or negotiated). This guide focuses on what you actually need for HTB boxes and CTFs.

---

## Quickstart — Anonymous Login

```bash
$ ftp 10.129.1.10
Name: anonymous
Password: <any or press Enter>
ftp> ls
ftp> get flag.txt
ftp> quit
```

**Try toggling passive mode if the server rejects your data connection:**
```bash
ftp> passive
```
*(Most firewalls require passive mode — if you get a `425 Can't open data connection`, toggle with `passive`.)*

---

## Client Commands (what you type)

| Command | What it does |
| :------ | :----------- |
| `open <host>` | Connect to an FTP server |
| `ls` / `dir` | List files (`ls -la` works too) |
| `cd <path>` | Change directory |
| `cdup` | Go to parent directory |
| `pwd` | Show current directory |
| `get <file>` | Download a file |
| `get <remote> <local>` | Download and rename locally |
| `put <file>` | Upload a file |
| `mget *.txt` | Download multiple files |
| `mput *.txt` | Upload multiple files |
| `reget <file>` | Resume interrupted download |
| `rename <old> <new>` | Rename a file |
| `delete <file>` | Delete a file |
| `mkdir <dir>` / `rmdir <dir>` | Create / remove directory |
| `ascii` / `binary` | Switch transfer mode (text / binary) |
| `passive` | Toggle passive mode on/off |
| `status` | Show connection state |
| `verbose` | Toggle verbose output |
| `hash` | Show progress `#` during transfers |
| `debug` | Toggle debug mode |
| `prompt` | Toggle interactive prompts (for mget/mput) |
| `help` | List available commands |
| `quit` / `bye` | Disconnect |

### ✅ Before starting — essential checks
```bash
$ nmap -sCV -p21 10.129.1.10
# Look for "Anonymous FTP login allowed" in the output
```

---

## Protocol Commands (what goes over the wire)

Client commands are just aliases. Under the hood, the client sends these:

| Command | Purpose |
| :------ | :------ |
| `USER anonymous` | Login without credentials |
| `PASS <pass>` | Send password |
| `LIST` / `NLST` | List files (detailed / names only) |
| `RETR <file>` | Download (`get` → `RETR`) |
| `STOR <file>` | Upload (`put` → `STOR`) |
| `PASV` | Request passive mode |
| `PORT a,b,c,d,p1,p2` | Request active mode |
| `SIZE <file>` | Get file size |
| `MDTM <file>` | Get file modification time |
| `REST <offset>` | Resume transfer at byte offset |
| `SYST` | Show server OS |
| `FEAT` | List server features/extensions |
| `SITE CHMOD 755 file` | Set permissions (vsftpd) |
| `QUIT` | Close connection |

---

## Useful Nmap Scripts

```bash
# Check anonymous access + list files
nmap --script ftp-anon -p21 10.129.1.10

# Brute force credentials
nmap --script ftp-brute -p21 10.129.1.10

# Check vsftpd backdoor (exploit)
nmap --script ftp-vsftpd-backdoor -p21 10.129.1.10

# Enumerate server capabilities
nmap --script ftp-syst -p21 10.129.1.10
```

---

## Response Codes — The Ones You'll Actually See

| Code | Meaning |
| :--- | :------ |
| **220** | Service ready |
| **227** | Entering Passive Mode (got IP:port) |
| **230** | Login successful ✅ |
| **331** | Username OK, need password |
| **425** | Can't open data connection (try `passive`) |
| **426** | Connection closed / transfer aborted |
| **500** | Command not recognized |
| **530** | Not logged in |
| **550** | File unavailable (doesn't exist / no permission) |

---

## vsftpd Notes

- **vsftpd** — "Very Secure FTP Daemon", very common on Linux
- Default config allows anonymous access if `anonymous_enable=YES` in `/etc/vsftpd.conf`
- vsftpd 2.3.4 had a **backdoor** (port 6200) — triggered by username ending in `:)`
- Check version with: `nmap -sV -p21 10.129.1.10`

---

## Automation with cURL

```bash
# Download (supports FTP://)
curl ftp://10.129.1.10/flag.txt --user anonymous: -o flag.txt

# Upload
curl ftp://10.129.1.10/ --user user:pass -T local.txt

# List directory
curl ftp://10.129.1.10/ --user anonymous:
```

## Automation with wget

```bash
wget -m ftp://anonymous:@10.129.1.10/   # Mirror entire FTP site
```

---

## One-liner — Anonymous FTP Recon

```bash
curl -s ftp://10.129.1.10/ --user anonymous: | awk '{print $NF}'
```

---

## References

- [RFC 959](https://tools.ietf.org/html/rfc959) — FTP Standard
- [IANA FTP Commands](https://www.iana.org/assignments/ftp-commands-extensions/ftp-commands-extensions.xhtml)
- [vsftpd](https://security.appspot.com/vsftpd.html)
