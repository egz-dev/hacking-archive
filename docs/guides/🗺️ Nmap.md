---
tags: [scanning]
---

> **Nmap** (Network Mapper) es la herramienta estándar de escaneo de puertos y descubrimiento de red. Es lo primero que ejecutas en cada máquina HTB y CTF. Esta guía cubre lo que hemos practicado en los 11 writeups.

---

## Quickstart — Los scans que realmente ejecutamos

> ⭐ **El pipeline de 2 comandos que uso en cada writeup:**
>
> ```bash
> # 1️⃣ Full port scan — encontrar todos los puertos abiertos
> nmap -p- --open -sS --min-rate 5000 -vvv -n -Pn $IP
>
> # 2️⃣ Service + version + default scripts en los puertos descubiertos
> nmap -sCV -p21,22,80,445,3389 $IP
> ```

---

## Flags esenciales — Las que realmente usamos

| Flag | Qué hace |
| :--- | :------ |
| `-p <ports>` | Puertos a escanear (`-p22,80,443`, `-p-` todos) |
| `-sS` | SYN scan (half-open, necesita sudo, sigiloso) |
| `-sT` | TCP connect scan (sin sudo, más lento) |
| `-sV` | Version detection |
| `-sC` | Ejecutar NSE scripts por defecto |
| `-sCV` | `-sC` + `-sV` combinados (lo que más uso) |
| `-Pn` | Saltar host discovery (asumir que el host está up) |
| `-n` | No DNS resolution (acelera el scan) |
| `--open` | Mostrar solo puertos abiertos |
| `--min-rate <n>` | Velocidad mínima de envío en packets/sec |
| `-vvv` | Máxima verbosidad (ver puertos según se encuentran) |
| `-T4` | Timing template agresivo (estándar CTF) |

---

## Pipeline estándar de los writeups

```bash
# Stage 1 — Full port scan rápido
nmap -p- --open -sS --min-rate 5000 -vvv -n -Pn $IP

# Stage 2 — Service scan en los puertos descubiertos
nmap -sCV -p21,80,445,3389,5985 $IP -oA scan-$IP

# Opcional: guardar solo texto (-oN) en lugar de todos los formatos
nmap -sCV -p21,80 $IP -oN scan-$IP.txt
```

---

## NSE Scripts — Los que hemos usado

```bash
# FTP — anonymous access
nmap --script ftp-anon -p21 10.129.1.10

# SMB — signing y shares
nmap --script smb2-security-mode -p445 10.129.1.10
nmap --script smb-enum-shares -p445 10.129.1.10

# RDP — NTLM info
nmap --script rdp-ntlm-info -p3389 10.129.1.10

# Rsync — list modules
nmap --script rsync-list-modules -p873 10.129.1.10

# MongoDB — databases
nmap --script mongodb-databases -p27017 10.129.1.10

# MySQL — empty password
nmap --script mysql-empty-password -p3306 10.129.1.10

# Redis — info
nmap --script redis-info -p6379 10.129.1.10
```

---

## Puertos y servicios — Los que hemos visto

| Puerto | Servicio | Qué verificar | Visto en |
| :----- | :------ | :----------- | :------ |
| **21** | FTP | Anonymous access, `ftp-anon` | Fawn, Crocodile |
| **80** | HTTP | Web app, Gobuster, virtual hosts | Preignition, Appointment, Crocodile, Responder |
| **135** | MSRPC | Windows RPC (parte del patrón Windows) | Dancing, Explosion |
| **139** | NetBIOS | SMB sobre NetBIOS | Dancing, Explosion |
| **445** | SMB | Shares, null session, signing check | Dancing, Explosion |
| **873** | Rsync | Anonymous modules | Synced |
| **3306** | MySQL | Root sin password | Sequel |
| **3389** | RDP | Administrator contraseña vacía | Explosion |
| **5985** | WinRM | Shell PowerShell (necesita creds) | Dancing, Explosion, Responder |
| **6379** | Redis | Sin autenticación | Redeemer |
| **27017** | MongoDB | Sin autenticación | Mongod |

---

## Port States — Qué significan

| State | Significado | Qué hacer |
| :---- | :--------- | :-------- |
| **open** | Servicio acepta conexiones | Enumerar más |
| **filtered** | Firewall bloquea probes | Podría estar abierto pero protegido |
| **closed** | Puerto alcanzable pero sin servicio | Seguir adelante |

---

## Timing Templates

| Template | Flag | Cuándo usarlo |
| :------- | :--- | :----------- |
| **Aggressive** | `-T4` | **Estándar CTF** — rápido, redes fiables |
| **Normal** | `-T3` | Default — balance velocidad/sigilo |

---

## Output Formats

| Flag | Formato | Cuándo usarlo |
| :--- | :----- | :----------- |
| `-oN <file>` | Normal | Texto legible |
| `-oA <basename>` | Todos los formatos | Guarda `.nmap`, `.xml`, `.gnmap` |

---

## 🔗 Related

**Machines:** [[🦌 Fawn]], [[🩰 Dancing]], [[💾 Redeemer]], [[💥 Explosion]], [[🧨 Preignition]], [[👹 Mongod]], [[🔄 Synced]], [[📅 Appointment]], [[🐬 Sequel]], [[🐊 Crocodile]], [[🧑‍🚒 Responder]]

**Guides:**

---

## References

- [Official Nmap Documentation](https://nmap.org/docs.html)
- [Nmap NSE Scripts Reference](https://nmap.org/nsedoc/)
- [HackTricks — Nmap Cheatsheet](https://book.hacktricks.xyz/network-services-pentesting/cheatsheet-nmap)
