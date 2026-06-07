---
tags: [web]
---

> **Gobuster** es una herramienta de fuerza bruta de directorios, archivos y virtual hosts escrita en Go. Es la herramienta más usada en CTFs para descubrir endpoints ocultos en servidores web. Esta guía cubre lo que hemos practicado.

---

## Quickstart — Directory Busting

```bash
# El comando que usarás el 90% del tiempo
$ gobuster dir -u http://10.129.1.10 -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt

# Con extensiones, threads, y filtrado de status codes
$ gobuster dir -u http://10.129.1.10 -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt -x php,txt,html -t 50

# Primera pasada rápida con wordlist pequeño
gobuster dir -u http://10.129.1.10 -w /usr/share/seclists/Discovery/Web-Content/common.txt -x php,html,txt -t 100
```

---

## Core Flags — Directory Mode (`dir`)

| Flag | Qué hace |
| :--- | :------ |
| `-u <url>` | URL del target (⚠️ incluir `http://` o `https://`) |
| `-w <wordlist>` | Ruta al archivo de wordlist |
| `-x <ext>` | Extensiones a probar (ej., `php,txt,html`) |
| `-t <n>` | Threads concurrentes (default 10, subir a 50-100 para velocidad) |
| `-o <file>` | Guardar output a archivo |
| `-s <codes>` | Mostrar solo estos status codes (ej., `200,301,403`) |
| `-k` | Saltar verificación de certificado TLS |
| `-q` | Modo quiet — suprimir banner y warnings |

---

## Wordlists — La correcta para cada trabajo

| Wordlist | Tamaño | Mejor para |
| :------- | :----- | :--------- |
| `common.txt` | ~4,700 | Primera pasada rápida |
| `DirBuster-2007_directory-list-2.3-small.txt` | ~87,000 | Balance velocidad vs profundidad |
| `DirBuster-2007_directory-list-2.3-medium.txt` | ~220,000 | **La estándar** — comprehensiva pero manejable |

---

## Status Codes — Filtra como un pro

| Code | Significado | Acción |
| :--- | :---------- | :----- |
| **200** | Encontrado ✅ | Interesante — investigar |
| **301** / **302** | Redirect | Puede llevar a algo — seguir |
| **401** | Unauthorized | Recurso protegido — probar auth bypass |
| **403** | Forbidden | Oculto pero existe — puede indicar algo jugoso |

```bash
# Filtro recomendado para CTFs
$ gobuster dir -u http://10.129.1.10 -w wordlist.txt -s 200,301,302,401,403
```

---

## CTF / HTB Techniques

### Pipeline: primera pasada rápida → scan profundo

```bash
# Paso 1 — scan rápido con wordlist pequeño
$ gobuster dir -u http://10.129.1.10 -w /usr/share/seclists/Discovery/Web-Content/common.txt -x php,txt,html -t 100

# Paso 2 — si no encuentras nada, profundiza
$ gobuster dir -u http://10.129.1.10 -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt -x php,html,txt -t 50
```

### Extensiones por stack tecnológico

| Tech | Extensiones |
| :--- | :---------- |
| **PHP** | `.php`, `.php.bak`, `.php~` |
| **ASP.NET** | `.aspx`, `.asp` |
| **Genérico** | `.txt`, `.bak`, `.zip`, `.tar.gz`, `.sql` |

### De los writeups

Gobuster encontró:
- `/admin.php` — **Preignition** (detrás de una página nginx por defecto)
- `/login.php` y `/dashboard` — **Crocodile** (sin enlaces visibles desde la homepage)

> 💡 Una página de inicio sin enlaces visibles NO significa que no haya un panel de login oculto.

---

## Troubleshooting

| Error / Síntoma | Causa probable |
| :-------------- | :------------- |
| `Error: error on parsing url` | Olvidaste `http://` o `https://` en `-u` |
| Todos los resultados son 404 | Web server es case-sensitive o usa rutas raras — prueba wordlist lowercase |
| Sin resultados | Prueba añadir extensiones con `-x php,html,txt` |

---

## 🔗 Related

**Machines:** [[🧨 Preignition]], [[📅 Appointment]], [[🐊 Crocodile]]

**Guides:** [[🗃️ FTP]], [[💉 SQL Injection]]

---

## References

- [Official Gobuster GitHub](https://github.com/OJ/gobuster)
- [SecLists Wordlists](https://github.com/danielmiessler/SecLists)
- [HackTricks — 80/443 HTTP Pentesting](https://book.hacktricks.xyz/network-services-pentesting/pentesting-web)
