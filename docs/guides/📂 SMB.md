---
tags: [smb, windows]
---

> **SMB** (Server Message Block) es un protocolo de compartición de archivos en red usado principalmente por Windows. Corre en **puerto 445** (SMB moderno sobre TCP) y **puerto 139** (NetBIOS legacy). Esta guía cubre lo que hemos practicado.

---

## Quickstart — Enumeración anónima de shares

```bash
# Listar shares anónimamente
$ smbclient -L 10.129.1.10
Enter WORKGROUP\user's password:        <-- solo presiona Enter

# Conectarse a un share accesible
$ smbclient \\\\10.129.1.10\\ShareName
Enter WORKGROUP\user's password:        <-- solo presiona Enter
smb: \> ls
smb: \> get flag.txt
smb: \> quit
```

**Si obtienes `NT_STATUS_ACCESS_DENIED` listando shares, prueba con guest:**
```bash
smbclient -L 10.129.1.10 -U guest
smbclient -L 10.129.1.10 -U guest%          # contraseña vacía
```

---

## Qué verificar cuando SMB está abierto

SMB rara vez aparece solo en máquinas Windows. Trátalo como parte de un patrón de reconocimiento:

### Patrón clásico de puertos Windows

```
PORT      STATE SERVICE          Notes
135/tcp   open  msrpc             RPC — servicios internos Windows
139/tcp   open  netbios-ssn       NetBIOS legacy
445/tcp   open  microsoft-ds      SMB — file shares, null sessions
3389/tcp  open  ms-wbt-server     RDP — acceso GUI (probar contraseña vacía)
5985/tcp  open  wsman             WinRM — shell PowerShell (necesita creds)
```

> 💡 **Reconocimiento de patrones:** Cuando ves SMB (445) + RPC (135) + WinRM (5985), estás en una máquina Windows donde tu objetivo es **encontrar credenciales**. Anonymous SMB shares, Responder NTLM capture, o web exploitation son los vectores iniciales típicos.

---

## SMB Signing — Por qué importa

SMB signing previene ataques de relay NTLM. Verifícalo temprano.

```bash
# Verificar SMB signing con nmap
nmap --script smb2-security-mode -p445 10.129.1.10
# Output:
# | smb2-security-mode:
# |   3.1.1:
# |_    Message signing enabled but not required    → ✅ relayable
```

| Estado de Signing | Qué significa |
| :---------------- | :------------ |
| **Enabled but not required** | Se puede relayar hashes NTLM a este target |
| **Required** | No se puede relayar — crackear el hash |
| **Disabled** | Se puede relayar — común en workstations y Linux/Samba |

> 💡 **De HTB Dancing:** SMB signing estaba *"enabled but not required"* — si hubiéramos capturado credenciales, el relay habría sido posible. Lo dejamos anotado como observación de recon.

---

## Comandos smbclient

| Comando | Qué hace |
| :------ | :------ |
| `ls` / `dir` | Listar archivos y directorios |
| `cd <dir>` | Cambiar de directorio |
| `cd ..` | Ir al directorio padre |
| `pwd` | Mostrar directorio actual |
| `get <file>` | Descargar un archivo |
| `get <remote> <local>` | Descargar y renombrar localmente |
| `mget *.txt` | Descargar múltiples archivos |
| `quit` / `exit` | Desconectar |

---

## Default Windows Shares

Shares presentes en casi toda máquina Windows. El acceso anónimo **casi siempre está denegado** — enfócate en shares personalizados.

| Share | Propósito | ¿Anónimo? |
| :---- | :-------- | :-------- |
| `ADMIN$` | Admin remoto (acceso a `C:\Windows`) | ❌ No |
| `C$` / `D$` | Shares de unidad por defecto | ❌ No |
| `IPC$` | Inter-Process Communication (named pipes) | Limitado |

> 💡 **De HTB Dancing:** `WorkShares` era el único share no-default — y tenía acceso anónimo de lectura.

---

## Useful Nmap Scripts

```bash
# Enumerar shares + verificar acceso anónimo
nmap --script smb-enum-shares -p445 10.129.1.10

# Verificar SMB signing (prerrequisito para relay)
nmap --script smb2-security-mode -p445 10.129.1.10

# Full SMB enumeration
nmap --script smb-enum-* -p139,445 10.129.1.10
```

---

## 🔗 Related

**Machines:** [[🩰 Dancing]]

**Guides:** [[🖥️ WinRM]], [[🔐 NTLM]], [[🖥️ xfreerdp]]

---

## References

- [SMB Protocol (Microsoft Docs)](https://learn.microsoft.com/en-us/windows/win32/fileio/microsoft-smb-protocol-and-cifs-protocol-overview)
- [HackTricks — 139/445 SMB Pentesting](https://book.hacktricks.xyz/network-services-pentesting/pentesting-smb)
