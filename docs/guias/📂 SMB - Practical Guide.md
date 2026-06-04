> **SMB** (Server Message Block) is a network file-sharing protocol used primarily by Windows. It runs on **port 445** (modern SMB over TCP) and **port 139** (legacy NetBIOS). This guide focuses on what you actually need for HTB boxes and CTFs.

---

## Quickstart — Anonymous Share Enumeration

```bash
# List shares anonymously
$ smbclient -L 10.129.1.10
Enter WORKGROUP\user's password:        <-- just press Enter

# Connect to an accessible share
$ smbclient \\\\10.129.1.10\\ShareName
Enter WORKGROUP\user's password:        <-- just press Enter
smb: \> ls
smb: \> get flag.txt
smb: \> quit
```

**If you get `NT_STATUS_ACCESS_DENIED` listing shares, try with a guest account:**
```bash
smbclient -L 10.129.1.10 -U guest
smbclient -L 10.129.1.10 -U guest%          # empty password
```
*(Some servers allow guest access but reject true anonymous/null sessions.)*

---

## smbclient Commands (inside the shell)

| Command | What it does |
| :------ | :----------- |
| `ls` / `dir` | List files and directories |
| `cd <dir>` | Change directory |
| `cd ..` | Go to parent directory |
| `pwd` | Show current directory |
| `get <file>` | Download a file |
| `get <remote> <local>` | Download and rename locally |
| `put <file>` | Upload a file |
| `mget *.txt` | Download multiple files |
| `mput *.txt` | Upload multiple files |
| `reget <file>` | Resume interrupted download |
| `rename <old> <new>` | Rename a file |
| `del <file>` / `rm <file>` | Delete a file |
| `mkdir <dir>` / `rmdir <dir>` | Create / remove directory |
| `recurse` | Toggle recursive mode (for mget/mput) |
| `prompt` | Toggle interactive prompts (for mget/mput) |
| `mask <pattern>` | Set file-matching pattern for mget/mput |
| `allinfo <file>` | Show all file metadata (timestamps, size, ACL) |
| `more <file>` | Display file contents in the shell |
| `help` | List available commands |
| `quit` / `exit` | Disconnect |

### ✅ Before starting — essential checks
```bash
$ nmap -sCV -p139,445 10.129.1.10
# Look for SMB service and OS fingerprinting in the output
```

---

## Enumeration Tools (beyond smbclient)

### smbmap — modern share enumeration & access

```bash
# List shares with anonymous access
smbmap -H 10.129.1.10

# List shares with guest account
smbmap -H 10.129.1.10 -u guest

# Recursively list a share
smbmap -H 10.129.1.10 -R ShareName

# Download a file
smbmap -H 10.129.1.10 --download ShareName/path/to/file

# Execute a command (if writable share + psexec access)
smbmap -H 10.129.1.10 -u user -p pass -x 'whoami'
```

### enum4linux — classic SMB/NetBIOS enumerator

```bash
# Full enumeration (shares, users, OS info, password policy)
enum4linux -a 10.129.1.10

# List shares only
enum4linux -S 10.129.1.10

# List users (via RID cycling)
enum4linux -U 10.129.1.10

# Check password policy
enum4linux -P 10.129.1.10
```

### crackmapexec — the Swiss Army knife

```bash
# Check anonymous/guest access
crackmapexec smb 10.129.1.10 -u '' -p '' --shares
crackmapexec smb 10.129.1.10 -u guest -p '' --shares

# List shares with credentials
crackmapexec smb 10.129.1.10 -u user -p pass --shares

# Spider a share for sensitive files
crackmapexec smb 10.129.1.10 -u user -p pass --spider ShareName --regex 'pass|cred|flag'

# Password spraying
crackmapexec smb 10.129.1.10 -u users.txt -p 'Spring2021!' --continue-on-success
```

### impacket — Python SMB toolkit

```bash
# Enumeration
lookupsid.py anonymous:@10.129.1.10
smbclient.py anonymous:@10.129.1.10

# Post-exploitation (requires admin credentials)
secretsdump.py DOMAIN/user:pass@10.129.1.10
psexec.py DOMAIN/user:pass@10.129.1.10
```

---

## Useful Nmap Scripts

```bash
# Enumerate shares + check anonymous access
nmap --script smb-enum-shares -p445 10.129.1.10

# Enumerate users (RID cycling)
nmap --script smb-enum-users -p445 10.129.1.10

# Check for known SMB vulnerabilities
nmap --script smb-vuln-* -p445 10.129.1.10

# OS discovery via SMB
nmap --script smb-os-discovery -p445 10.129.1.10

# Check supported SMB protocol versions
nmap --script smb-protocols -p445 10.129.1.10

# Check SMB signing (relay attack prerequisite)
nmap --script smb2-security-mode -p445 10.129.1.10

# Full SMB enumeration combo
nmap --script smb-enum-* -p139,445 10.129.1.10
```

---

## NT_STATUS Codes — The Ones You'll Actually See

| Code | Meaning |
| :--- | :------ |
| **NT_STATUS_OK** | Operation succeeded ✅ |
| **NT_STATUS_ACCESS_DENIED** | No permission (try guest, or different share) |
| **NT_STATUS_LOGON_FAILURE** | Wrong credentials |
| **NT_STATUS_ACCOUNT_DISABLED** | Account disabled |
| **NT_STATUS_PASSWORD_EXPIRED** | Password expired (change before using) |
| **NT_STATUS_ACCOUNT_LOCKED_OUT** | Account locked (password spray carefully!) |
| **NT_STATUS_BAD_NETWORK_NAME** | Share doesn't exist |
| **NT_STATUS_CONNECTION_REFUSED** | SMB port not accessible or service down |
| **NT_STATUS_IO_TIMEOUT** | No response from host |
| **NT_STATUS_INVALID_PARAMETER** | Malformed request (usually a tool bug) |

---

## Default Windows Shares

Shares present on almost every Windows machine. Anonymous access is **almost always denied** — focus on custom shares.

| Share | Purpose | Anonymous? |
| :---- | :------ | :--------- |
| `ADMIN$` | Remote admin (access to `C:\Windows`) | ❌ No |
| `C$` / `D$` | Default drive shares | ❌ No |
| `IPC$` | Inter-Process Communication (named pipes) | Limited |
| `NETLOGON$` | Domain controller logon scripts | ❌ No |
| `SYSVOL` | Domain Group Policy files | ❌ No |
| `print$` | Printer drivers | Sometimes read |

---

## Common SMB Vulnerabilities

| Vulnerability | CVE | Impact |
| :------------ | :-- | :----- |
| **EternalBlue** | CVE-2017-0144 | RCE (MS17-010) — Windows 7/2008 R2 and earlier |
| **SMBGhost** | CVE-2020-0796 | RCE — Windows 10 v1903–1909 |
| **SMBleed** | CVE-2020-1206 | Information disclosure |
| **PrintNightmare** | CVE-2021-34527 | RCE via print spooler |
| **ZeroLogon** | CVE-2020-1472 | Domain controller privilege escalation |

```bash
# Quick EternalBlue check
nmap --script smb-vuln-ms17-010 -p445 10.129.1.10
```

---

## Automation & Scripting

### One-liner — list shares anonymously

```bash
smbclient -L 10.129.1.10 -N 2>/dev/null | grep Disk | awk '{print $1}'
```

### One-liner — download all readable files from a share

```bash
smbclient \\\\10.129.1.10\\ShareName -N -c 'recurse; prompt; mget *'
```

### One-liner — recursive share enumeration with smbmap

```bash
smbmap -H 10.129.1.10 -R 2>/dev/null | grep -v 'No Access\|Permission Denied'
```

### Mount an SMB share (Linux)

```bash
# Install cifs-utils first
sudo mount -t cifs //10.129.1.10/ShareName /mnt/smb -o username=guest,password=
# Or with credentials
sudo mount -t cifs //10.129.1.10/ShareName /mnt/smb -o username=user,password=pass
```

### Bash loop — try common share names

```bash
for share in Users Shared Files Backup Data Public; do
  echo "=== $share ==="
  smbclient "\\\\10.129.1.10\\$share" -N -c ls 2>/dev/null
done
```

---

## References

- [SMB Protocol (Microsoft Docs)](https://learn.microsoft.com/en-us/windows/win32/fileio/microsoft-smb-protocol-and-cifs-protocol-overview)
- [Impacket Tools](https://github.com/fortra/impacket)
- [CrackMapExec Wiki](https://wiki.porchetta.industries/)
- [smbmap](https://github.com/ShawnDEvans/smbmap)
- [HackTricks — 139/445 SMB Pentesting](https://book.hacktricks.xyz/network-services-pentesting/pentesting-smb)
