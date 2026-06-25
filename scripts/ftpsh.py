#!/usr/bin/env python3
"""
ftpsh - a tiny interactive FTP "shell".

FTP is file-transfer only, so this is NOT a remote command shell: it's an
interactive browser over the FTP control connection (ftplib handles the
PASV/data-channel dance for you). Handy on a box where the `ftp` client
isn't installed but python3 is.

Usage:
    python3 ftpsh.py <host> [user] [--port 21]

You'll be prompted for the password (no echo). Type `help` at the prompt.
"""
import argparse
import getpass
import os
import shlex
import sys
from ftplib import FTP, error_perm


def connect(host, port, user, password):
    ftp = FTP()
    ftp.connect(host, port, timeout=15)
    ftp.login(user, password)
    try:
        ftp.set_pasv(True)
    except Exception:
        pass
    return ftp


def do_ls(ftp, args):
    path = args[0] if args else ""
    ftp.retrlines("LIST " + path if path else "LIST")


def do_cd(ftp, args):
    ftp.cwd(args[0] if args else "/")


def do_get(ftp, args):
    if not args:
        print("usage: get <remote> [local]")
        return
    remote = args[0]
    local = args[1] if len(args) > 1 else os.path.basename(remote)
    with open(local, "wb") as fh:
        ftp.retrbinary("RETR " + remote, fh.write)
    print(f"-> saved {local}")


def do_cat(ftp, args):
    if not args:
        print("usage: cat <remote>")
        return
    lines = []
    ftp.retrlines("RETR " + args[0], lines.append)
    print("\n".join(lines))


def do_put(ftp, args):
    if not args:
        print("usage: put <local> [remote]")
        return
    local = args[0]
    remote = args[1] if len(args) > 1 else os.path.basename(local)
    with open(local, "rb") as fh:
        ftp.storbinary("STOR " + remote, fh)
    print(f"-> uploaded {remote}")


HELP = """commands:
  ls [path]            list directory
  cd <path>            change directory
  pwd                  print working directory
  cat <file>           print a remote text file
  get <remote> [local] download a file
  put <local> [remote] upload a file
  raw <FTP CMD>        send a raw FTP command (e.g. raw SYST)
  help                 this text
  exit / quit          leave
"""


def repl(ftp):
    print(HELP)
    while True:
        try:
            cwd = ftp.pwd()
        except Exception:
            cwd = "?"
        try:
            line = input(f"ftp:{cwd}$ ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        try:
            parts = shlex.split(line)
        except ValueError:
            parts = line.split()
        cmd, args = parts[0], parts[1:]
        try:
            if cmd in ("exit", "quit"):
                break
            elif cmd == "help":
                print(HELP)
            elif cmd == "ls":
                do_ls(ftp, args)
            elif cmd == "cd":
                do_cd(ftp, args)
            elif cmd == "pwd":
                print(ftp.pwd())
            elif cmd == "cat":
                do_cat(ftp, args)
            elif cmd == "get":
                do_get(ftp, args)
            elif cmd == "put":
                do_put(ftp, args)
            elif cmd == "raw":
                print(ftp.sendcmd(" ".join(args)))
            else:
                print(f"unknown command: {cmd} (try 'help')")
        except error_perm as e:
            print(f"! {e}")
        except Exception as e:
            print(f"! error: {e}")


def main():
    ap = argparse.ArgumentParser(description="tiny interactive FTP shell")
    ap.add_argument("host")
    ap.add_argument("user", nargs="?", default="anonymous")
    ap.add_argument("--port", type=int, default=21)
    ap.add_argument("--password", help="password (will prompt if omitted)")
    args = ap.parse_args()

    password = args.password or getpass.getpass(f"{args.user}@{args.host} password: ")
    try:
        ftp = connect(args.host, args.port, args.user, password)
    except Exception as e:
        print(f"login failed: {e}", file=sys.stderr)
        sys.exit(1)
    print(f"connected to {args.host} as {args.user}")
    try:
        repl(ftp)
    finally:
        try:
            ftp.quit()
        except Exception:
            ftp.close()


if __name__ == "__main__":
    main()
