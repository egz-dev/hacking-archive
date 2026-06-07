---
tags: [database, redis]
---

> **Redis** (Remote Dictionary Server) is an in-memory key-value store running on **port 6379**. By default it has no authentication, making it a high-value target for data exfiltration in CTFs. This guide covers what we've practiced.

---

## Quickstart — Unauthenticated access

```bash
# Test if Redis accepts unauthenticated connections
$ redis-cli -h 10.129.1.10
10.129.1.10:6379> PING
PONG                    # ✅ no auth required
```

**If you get `NOAUTH Authentication required`, the server has a password:**
```bash
redis-cli -h 10.129.1.10 -a password
```

---

## Basic enumeration

```bash
$ redis-cli -h 10.129.1.10

# Server info — OS, version, uptime
10.129.1.10:6379> INFO
10.129.1.10:6379> INFO keyspace          # databases with keys
10.129.1.10:6379> INFO server           # Redis version, OS

# Database navigation
10.129.1.10:6379> SELECT 0              # switch DB (0-15 by default)
10.129.1.10:6379> DBSIZE                # number of keys in current DB
10.129.1.10:6379> KEYS *                # all keys (⚠️ slow on large DBs)
10.129.1.10:6379> GET <key>             # read a string value
10.129.1.10:6379> MGET <k1> <k2>        # read multiple keys
```

---

## Redis Commands Cheat Sheet

| Command | What it does |
| :------ | :------ |
| `PING` | Connectivity test |
| `INFO` | Server statistics + metadata |
| `INFO keyspace` | Databases and key count |
| `SELECT <0-15>` | Switch database |
| `KEYS *` | List all keys |
| `DBSIZE` | Number of keys in current DB |
| `GET <key>` | Read string value |
| `TYPE <key>` | Get key data type |
| `EXISTS <key>` | Check if a key exists |

---

## Useful Nmap Scripts

```bash
# Detect Redis + check if no auth required
nmap --script redis-info -p6379 10.129.1.10
```

---

## Redis Security Notes

- **No auth by default** — Redis listens on `0.0.0.0:6379` with no password unless explicitly configured
- We saw it on: **Redeemer** (Redis 5.0.7, no auth, 4 keys in db0, flag at `GET flag`)

---

## 🔗 Related

**Machines:** [[💾 Redeemer]]

**Guides:** [[🍃 MongoDB]], [[🐬 MySQL]]

---

## References

- [Redis Official Documentation](https://redis.io/docs/latest/commands/)
- [HackTricks — Pentesting Redis](https://book.hacktricks.xyz/network-services-pentesting/6379-pentesting-redis)
