
# script to take a file and remove the two words from each line

with open("history.txt", "r") as f:
    with open("processed_history.txt", "w") as o:
        for line in f.readlines():
            ws = line.split()
            if len(ws) < 3:
                continue
            s = " ".join(ws[2:]) + "\n"
            if s.startswith("!") or s.startswith("^"):
                continue
            o.write(s)
