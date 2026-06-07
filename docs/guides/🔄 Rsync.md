---
tags: [rsync]
---

> **Rsync** (Remote Sync) es una herramienta de sincronización de archivos que corre en **puerto 873**. Es común encontrar mala configuración de **acceso anónimo** a directorios compartidos (módulos). Esta guía cubre lo que hemos practicado.

---

## Quickstart — Enumeración de módulos y exfiltración

```bash
# Listar módulos disponibles — lo primero que se prueba
$ rsync 10.129.1.10::

# Descargar todo de un módulo
$ rsync -av 10.129.1.10::module_name ./local-destination/

# Listar contenido de un módulo sin descargar
$ rsync --list-only 10.129.1.10::module_name

# Descargar un solo archivo
$ rsync -av 10.129.1.10::public/flag.txt ./flag.txt
```

---

## Comandos esenciales

| Comando | Qué hace |
| :------ | :------ |
| `rsync <host>::` | Listar módulos disponibles (sin auth) |
| `rsync <host>::<module>` | Listar archivos dentro de un módulo |
| `rsync -av <host>::<module> ./dest/` | Descargar contenido del módulo |
| `rsync --list-only <host>::<module>` | Listar sin descargar |

---

## Useful Nmap Scripts

```bash
# Listar módulos rsync (el script más útil)
nmap --script rsync-list-modules -p873 10.129.1.10

# Full service + version detection
nmap -sV -p873 10.129.1.10
```

---

## CTF Workflow

1. **Escanear puerto** — `nmap -sCV -p873 10.129.1.10`
2. **Listar módulos** — `rsync 10.129.1.10::`
3. **Explorar módulo** — `rsync --list-only 10.129.1.10::public`
4. **Descargar** — `rsync -av 10.129.1.10::public ./output/`

---

## Rsync Security Notes

- **Acceso anónimo** es la mala configuración crítica — sin `auth users` en `rsyncd.conf`, cualquiera puede leer (y potencialmente escribir) archivos
- Lo vimos en: **Synced** (rsync protocol 31, módulo `public` anónimo, flag en `flag.txt`)

---

## 🔗 Related

**Machines:** [[🔄 Synced]]

**Guides:** [[🗃️ FTP]]

---

## References

- [Rsync Man Page](https://linux.die.net/man/1/rsync)
- [HackTricks — Pentesting Rsync](https://book.hacktricks.xyz/network-services-pentesting/873-pentesting-rsync)
- [Nmap NSE — rsync-list-modules](https://nmap.org/nsedoc/scripts/rsync-list-modules.html)
