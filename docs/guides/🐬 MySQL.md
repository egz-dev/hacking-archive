---
tags: [database, mysql]
---

> **MySQL / MariaDB** es una base de datos relacional que corre en **puerto 3306**. En CTFs, la mala configuración más común es acceso root sin contraseña — permitiendo enumeración completa de la base de datos. Esta guía cubre lo que hemos practicado.

---

## Quickstart — Acceso sin autenticación

```bash
# Probar si MySQL acepta root sin contraseña
$ mysql -h 10.129.1.10 -u root

# Con contraseña
$ mysql -h 10.129.1.10 -u root -p
$ mysql -h 10.129.1.10 -u root -proot

# Deshabilitar SSL (necesario en algunos servidores CTF)
$ mysql -h 10.129.1.10 -u root --ssl=0
```

**Si `mysql` no está instalado:**
```bash
sudo apt install mysql-client
```

---

## Enumeración básica

Una vez conectado, estos son los comandos esenciales para mapear la base de datos:

```sql
-- Info del servidor
SELECT VERSION();
SHOW VARIABLES LIKE '%version%';

-- Listar todas las bases de datos
SHOW DATABASES;

-- Cambiar a una base de datos
USE <database>;

-- Listar tablas en la base de datos actual
SHOW TABLES;

-- Ver estructura de una tabla
DESCRIBE <table>;

-- Dumpear toda la tabla
SELECT * FROM <table>;

-- Contar filas
SELECT COUNT(*) FROM <table>;

-- Usuario actual y privilegios
SELECT USER();
SHOW GRANTS;
```

---

## MySQL Commands Cheat Sheet

### Database Operations

| Comando | Qué hace |
| :------ | :------ |
| `SHOW DATABASES;` | Listar todas las bases de datos |
| `USE <db>;` | Cambiar a una base de datos |
| `SELECT DATABASE();` | Mostrar base de datos actual |

### Table Operations

| Comando | Qué hace |
| :------ | :------ |
| `SHOW TABLES;` | Listar tablas en la BD actual |
| `DESCRIBE <table>;` | Mostrar columnas, tipos, claves |
| `SELECT * FROM <table>;` | Dumpear todas las filas |
| `SELECT column1,column2 FROM <table>;` | Dumpear columnas específicas |

---

## Useful Nmap Scripts

```bash
# Info + detección de versión
nmap -sV -p3306 --script mysql-info 10.129.1.10

# Verificar root sin contraseña
nmap -sV -p3306 --script mysql-empty-password 10.129.1.10
```

---

## MySQL Security Notes

- **Root sin contraseña** es la mala configuración #1 en CTF — siempre prueba `mysql -h <IP> -u root` primero
- **MariaDB en Debian** usa `unix_socket` auth para root localmente — pero si `bind-address = 0.0.0.0`, root remoto puede seguir sin contraseña
- Lo vimos en: **Sequel** (MariaDB 10.3.27, root sin password, flag en tabla `config`)

---

## 🔗 Related

**Machines:** [[🐬 Sequel]]

**Guides:** [[💉 SQL Injection]]

---

## References

- [MySQL Official Documentation](https://dev.mysql.com/doc/refman/8.0/en/)
- [HackTricks — Pentesting MySQL (3306)](https://book.hacktricks.xyz/network-services-pentesting/pentesting-mysql)
