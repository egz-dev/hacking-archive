---
tags: [database, mysql]
---

> **MySQL / MariaDB** is a relational database running on **port 3306**. In CTFs, the most common misconfiguration is root access with no password — allowing full database enumeration. This guide covers what we've practiced.

---

## Quickstart — Unauthenticated access

```bash
# Test if MySQL accepts root with no password
$ mysql -h 10.129.1.10 -u root

# With password
$ mysql -h 10.129.1.10 -u root -p
$ mysql -h 10.129.1.10 -u root -proot

# Disable SSL (necessary on some CTF servers)
$ mysql -h 10.129.1.10 -u root --ssl=0
```

**If `mysql` is not installed:**
```bash
sudo apt install mysql-client
```

---

## Basic enumeration

Once connected, these are the essential commands to map the database:

```sql
-- Server info
SELECT VERSION();
SHOW VARIABLES LIKE '%version%';

-- List all databases
SHOW DATABASES;

-- Switch to a database
USE <database>;

-- List tables in the current database
SHOW TABLES;

-- View table structure
DESCRIBE <table>;

-- Dump entire table
SELECT * FROM <table>;

-- Count rows
SELECT COUNT(*) FROM <table>;

-- Current user and privileges
SELECT USER();
SHOW GRANTS;
```

---

## MySQL Commands Cheat Sheet

### Database Operations

| Command | What it does |
| :------ | :------ |
| `SHOW DATABASES;` | List all databases |
| `USE <db>;` | Switch to a database |
| `SELECT DATABASE();` | Show current database |

### Table Operations

| Command | What it does |
| :------ | :------ |
| `SHOW TABLES;` | List tables in current DB |
| `DESCRIBE <table>;` | Show columns, types, keys |
| `SELECT * FROM <table>;` | Dump all rows |
| `SELECT column1,column2 FROM <table>;` | Dump specific columns |

---

## Useful Nmap Scripts

```bash
# Info + version detection
nmap -sV -p3306 --script mysql-info 10.129.1.10

# Check root with empty password
nmap -sV -p3306 --script mysql-empty-password 10.129.1.10
```

---

## MySQL Security Notes

- **Root with no password** is the #1 CTF misconfiguration — always test `mysql -h <IP> -u root` first
- **MariaDB on Debian** uses `unix_socket` auth for local root — but if `bind-address = 0.0.0.0`, remote root may still have no password
- We saw it on: **Sequel** (MariaDB 10.3.27, root with no password, flag in table `config`)

---

## 🔗 Related

**Machines:** [[🐬 Sequel]]

**Guides:** [[💉 SQL Injection]]

---

## References

- [MySQL Official Documentation](https://dev.mysql.com/doc/refman/8.0/en/)
- [HackTricks — Pentesting MySQL (3306)](https://book.hacktricks.xyz/network-services-pentesting/pentesting-mysql)
