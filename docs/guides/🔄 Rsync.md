---
tags: [rsync]
---

> **Rsync** (Remote Sync) is a file synchronization tool running on **port 873**. Misconfigured **anonymous access** to shared directories (modules) is a common finding. This guide covers what we've practiced.

---

## Quickstart — Module enumeration and exfiltration

```bash
# List available modules — the first thing to test
$ rsync 10.129.1.10::

# Download everything from a module
$ rsync -av 10.129.1.10::module_name ./local-destination/

# List contents of a module without downloading
$ rsync --list-only 10.129.1.10::module_name

# Download a single file
$ rsync -av 10.129.1.10::public/flag.txt ./flag.txt
```

---

## Essential commands

| Command | What it does |
| :------ | :------ |
| `rsync <host>::` | List available modules (no auth) |
| `rsync <host>::<module>` | List files inside a module |
| `rsync -av <host>::<module> ./dest/` | Download module contents |
| `rsync --list-only <host>::<module>` | List without downloading |

---

## Useful Nmap Scripts

```bash
# List rsync modules (most useful script)
nmap --script rsync-list-modules -p873 10.129.1.10

# Full service + version detection
nmap -sV -p873 10.129.1.10
```

---

## CTF Workflow

1. **Scan port** — `nmap -sCV -p873 10.129.1.10`
2. **List modules** — `rsync 10.129.1.10::`
3. **Explore module** — `rsync --list-only 10.129.1.10::public`
4. **Download** — `rsync -av 10.129.1.10::public ./output/`

---

## Rsync Security Notes

- **Anonymous access** is the critical misconfiguration — without `auth users` in `rsyncd.conf`, anyone can read (and potentially write) files
- We saw it on: **Synced** (rsync protocol 31, anonymous `public` module, flag in `flag.txt`)

---

## 🔗 Related

**Machines:** [[🔄 Synced]]

**Guides:** [[🗃️ FTP]]

---

## References

- [Rsync Man Page](https://linux.die.net/man/1/rsync)
- [HackTricks — Pentesting Rsync](https://book.hacktricks.xyz/network-services-pentesting/873-pentesting-rsync)
- [Nmap NSE — rsync-list-modules](https://nmap.org/nsedoc/scripts/rsync-list-modules.html)
