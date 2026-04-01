with open("ruff_e501.txt", "rb") as f:
    for i in range(40):
        b = f.readline()
        if not b:
            break
        print(i + 1, b[:200])
