---
tags: [windows, rdp, windows-tools]
---

> **xfreerdp** es el cliente RDP open-source del proyecto FreeRDP. Se conecta a hosts Windows en **puerto 3389**. Esta guía cubre lo que hemos practicado.

---

## Quickstart — Conexión básica

```bash
# Interactivo (pide contraseña — lo más seguro)
$ xfreerdp /v:10.129.1.10 /u:Administrator

# Con contraseña inline (⚠️ aparece en el historial de shell)
$ xfreerdp /v:10.129.1.10 /u:Administrator /p:Password123

# Ignorar certificado autofirmado (esencial en CTF)
$ xfreerdp /v:10.129.1.10 /u:Administrator /p:Password123 /cert-ignore

# Pantalla completa
$ xfreerdp /v:10.129.1.10 /u:Administrator /p:Password123 /cert-ignore /f
```

**Para salir de pantalla completa:** `Ctrl+Alt+Enter`

### ✅ Antes de empezar
```bash
$ nmap -sCV -p3389 10.129.1.10
# Buscar "Remote Desktop Protocol" en el output
```

---

## Opciones esenciales

| Flag | Qué hace |
| :--- | :------ |
| `/v:<host>` | IP/hostname del target (puerto 3389 por defecto) |
| `/u:<user>` | Username |
| `/p:<pass>` | Password |
| `/cert-ignore` | Ignorar warnings de certificado (certs autofirmados) |
| `/f` | Modo pantalla completa |

---

## CTF / HTB Techniques

### Contraseña vacía de Administrator

Intentar RDP como `Administrator` con **contraseña vacía** es sorprendentemente común en entornos CTF:

```bash
$ xfreerdp3 /v:10.129.1.10 /u:Administrator /cert-ignore
Password:                    <-- solo presiona Enter
```

> 💡 **Por qué funciona:** Windows permite cuentas con contraseña en blanco en ciertas configuraciones (VMs recién provisionadas, Group Policy mal configurada).

---

## Useful Nmap Scripts

```bash
# Detectar RDP + info NTLM
nmap -sV -p3389 10.129.1.10
nmap --script rdp-ntlm-info -p3389 10.129.1.10
```

---

## Troubleshooting

| Error / Síntoma | Causa probable |
| :-------------- | :------------- |
| `ERRCONNECT_CONNECT_FAILED` | Puerto 3389 no abierto / host inalcanzable |
| `ERRCONNECT_LOGON_FAILURE` | Username/password incorrectos |
| `SSL certificate problem` | Cert autofirmado — usa `/cert-ignore` |

---

## 🔗 Related

**Machines:** [[💥 Explosion]]

**Guides:** [[🖥️ WinRM]]

---

## References

- [FreeRDP Official GitHub](https://github.com/FreeRDP/FreeRDP)
- [HackTricks — 3389 RDP Pentesting](https://book.hacktricks.xyz/network-services-pentesting/pentesting-rdp)
