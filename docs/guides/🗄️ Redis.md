---
tags: [database, redis]
---

> **Redis** (Remote Dictionary Server) es un almacén clave-valor en memoria que corre en **puerto 6379**. Por defecto no tiene autenticación, lo que lo convierte en un objetivo de alto valor para exfiltración de datos en CTFs. Esta guía cubre lo que hemos practicado.

---

## Quickstart — Acceso sin autenticación

```bash
# Probar si Redis acepta conexiones sin autenticación
$ redis-cli -h 10.129.1.10
10.129.1.10:6379> PING
PONG                    # ✅ no auth required
```

**Si obtienes `NOAUTH Authentication required`, el servidor tiene contraseña:**
```bash
redis-cli -h 10.129.1.10 -a password
```

---

## Enumeración básica

```bash
$ redis-cli -h 10.129.1.10

# Info del servidor — OS, versión, uptime
10.129.1.10:6379> INFO
10.129.1.10:6379> INFO keyspace          # bases de datos con claves
10.129.1.10:6379> INFO server           # versión de Redis, OS

# Navegación de base de datos
10.129.1.10:6379> SELECT 0              # cambiar de DB (0-15 por defecto)
10.129.1.10:6379> DBSIZE                # número de claves en la DB actual
10.129.1.10:6379> KEYS *                # todas las claves (⚠️ lento en DBs grandes)
10.129.1.10:6379> GET <key>             # leer un valor string
10.129.1.10:6379> MGET <k1> <k2>        # leer múltiples claves
```

---

## Redis Commands Cheat Sheet

| Comando | Qué hace |
| :------ | :------ |
| `PING` | Test de conectividad |
| `INFO` | Estadísticas del servidor + metadata |
| `INFO keyspace` | Bases de datos y conteo de claves |
| `SELECT <0-15>` | Cambiar de base de datos |
| `KEYS *` | Listar todas las claves |
| `DBSIZE` | Número de claves en la DB actual |
| `GET <key>` | Leer valor string |
| `TYPE <key>` | Obtener tipo de dato de la clave |
| `EXISTS <key>` | Verificar si una clave existe |

---

## Useful Nmap Scripts

```bash
# Detectar Redis + verificar si no requiere auth
nmap --script redis-info -p6379 10.129.1.10
```

---

## Redis Security Notes

- **Sin auth por defecto** — Redis escucha en `0.0.0.0:6379` sin contraseña a menos que se configure explícitamente
- Lo vimos en: **Redeemer** (Redis 5.0.7, sin auth, 4 claves en db0, flag en `GET flag`)

---

## 🔗 Related

**Machines:** [[💾 Redeemer]]

**Guides:** [[🍃 MongoDB]], [[🐬 MySQL]]

---

## References

- [Redis Official Documentation](https://redis.io/docs/latest/commands/)
- [HackTricks — Pentesting Redis](https://book.hacktricks.xyz/network-services-pentesting/6379-pentesting-redis)
