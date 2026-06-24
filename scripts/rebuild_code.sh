#!/bin/bash

FT_FUN="/home/pulgamecanica/42Org/boot2root/fun/ft_fun"
OUTPUT="/tmp/reassembled.c"

echo "[*] Counting fragments..."
TOTAL=$(ls "$FT_FUN" | wc -l)
echo "[*] Found $TOTAL fragments"

echo "[*] Reassembling in order..."
> "$OUTPUT"
for i in $(seq 1 "$TOTAL"); do
    f=$(grep -rl "//file${i}$" "$FT_FUN" 2>/dev/null)
    if [ -n "$f" ]; then
        grep -v "//file" "$f" >> "$OUTPUT"
    fi
done

echo "[*] Reassembled code written to $OUTPUT"
echo "[*] Compiling..."
gcc "$OUTPUT" -o /tmp/fun_bin 2>&1

if [ $? -eq 0 ]; then
    echo "[*] Running..."
    /tmp/fun_bin
else
    echo "[!] Compilation failed"
fi
