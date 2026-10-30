#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick peek into the 26.3 jar: find class entries / dump a datapack json."""
import sys
import zipfile

MC = r"C:\Users\95959\AppData\Roaming\.minecraft\versions\26.3\26.3.jar"


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    mc = zipfile.ZipFile(MC)
    mode = sys.argv[1] if len(sys.argv) > 1 else "find"
    if mode == "find":
        for pat in sys.argv[2:]:
            hits = [n for n in mc.namelist() if pat in n]
            print("%-30s %d %s" % (pat, len(hits), hits[:6]))
    elif mode == "dump":
        print(mc.read(sys.argv[2]).decode("utf-8", "replace"))
    elif mode == "ls":
        pre = sys.argv[2]
        for n in mc.namelist():
            if n.startswith(pre):
                print(n)


if __name__ == "__main__":
    main()
