---
OS: 
Level: 
Skills:
---
# Machine Name

*Name* is a **Difficulty** *OS* machine that demonstrates how *vulnerability/misconfiguration* allows *outcome/impact*.

---

## Recon

A full port scan reveals *N* open ports:

```
$ nmap -p- --open -sS --min-rate 5000 -vvv -n -Pn <IP>
```

A service scan identifies *service/version*:

```
$ nmap -sCV -p<port> <IP>
```

**Key findings:**
- **Port/Service** — brief description
- **Version** — relevance to exploitation
- **Vulnerability** — why this finding is exploitable

---

## Foothold

### Step 1 — Action description

```
$ command
```

Explanation of what the command does and why it works.

### Step 2 — Action description

```
$ command
```

Result obtained and what it means.

> 💡 **Why this works:** Technical explanation of the attack vector or misconfiguration exploited.

---

## Key Takeaways

- **Lesson 1** — description of the technique or concept learned
- **Lesson 2** — relevant command or tool to remember
- **Lesson 3** — mindset or approach applicable to other scenarios
- **Lesson 4** — note on what was NOT needed (rabbit holes avoided)
