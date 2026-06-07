---
tags: [cracking]
---

> **John the Ripper (JtR)** es una herramienta de cracking de contraseñas que soporta cientos de formatos de hash. Esta guía cubre lo que hemos practicado: crackear hashes NTLMv2 capturados con Responder.

---

## Quickstart — Crackear NTLMv2

```bash
# 1. Capturar el hash con Responder
sudo responder -I tun0
# El hash aparece en: /usr/share/responder/logs/SMB-NTLMv2-*.txt

# 2. Crackear con John (auto-detecta el formato)
john hash.txt

# 3. O forzar el formato y usar wordlist
john --format=netntlmv2 --wordlist=/usr/share/wordlists/rockyou.txt hash.txt

# 4. Ver resultados
john --show hash.txt
```

---

## Formato del hash NTLMv2

```
username::domain:ServerChallenge:NTProofStr:NTResponse
```

Ejemplo:
```
admin::WORKGROUP:1122334455667788:a3b4c5d6e7f8091a2b3c4d5e6f708192:0101000000000000...
```

---

## Modos de ataque

### 1. Wordlist Attack

```bash
# Ataque básico con wordlist
john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt

# Con reglas para mutación de contraseñas
john --wordlist=/usr/share/wordlists/rockyou.txt --rules hash.txt

# Forzar formato
john --wordlist=/usr/share/wordlists/rockyou.txt --rules --format=netntlmv2 hash.txt
```

### 2. Auto-detección

```bash
# John auto-detecta el formato del hash
john hash.txt

# Listar todos los formatos soportados
john --list=formats

# Filtrar formatos por keyword
john --list=formats | grep -i ntlm
```

---

## Gestión de sesiones

```bash
# Iniciar una sesión con nombre (auto-guarda progreso)
john --session=crack1 --wordlist=rockyou.txt hash.txt

# Restaurar una sesión interrumpida
john --restore=crack1

# Mostrar contraseñas crackeadas
john --show hash.txt
```

> 💡 **Siempre usa sesiones para cracks largos.** John guarda el progreso automáticamente — puedes Ctrl+C y retomar con `--restore`.

---

## Wordlists esenciales

```bash
# RockYou (el wordlist estándar de CTF)
/usr/share/wordlists/rockyou.txt.gz    # Debian/Kali (gunzip primero)

# SecLists (colección completa)
git clone https://github.com/danielmiessler/SecLists
```

---

## CTF Workflow

1. **Capturar el hash** — con Responder u otra herramienta
2. **Identificar el formato** — `john hash.txt` (auto-detecta) o `john --list=formats | grep keyword`
3. **Crackear con wordlist primero** — `john --wordlist=rockyou.txt hash.txt`
4. **Añadir reglas si la wordlist falla** — `john --wordlist=rockyou.txt --rules=best64 hash.txt`
5. **Ver progreso** — `john --show hash.txt`
6. **Restaurar sesiones interrumpidas** — `john --restore`

---

## 🔗 Related

**Machines:** [[🧑‍🚒 Responder]]

**Guides:** [[🔐 NTLM]], [[🖥️ WinRM]]

---

## References

- [John the Ripper Documentation](https://www.openwall.com/john/doc/)
- [PayloadsAllTheThings — Cracking](https://github.com/swisskyrepo/PayloadsAllTheThings/blob/master/Methodology%20and%20Resources/Hash%20Cracking.md)
- [HackTricks — Hash Cracking](https://book.hacktricks.xyz/generic-methodologies-and-resources/tips-and-tricks-getting-credentials)
