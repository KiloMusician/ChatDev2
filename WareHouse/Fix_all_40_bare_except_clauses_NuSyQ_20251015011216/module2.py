try:
    with open('file.txt','r', encoding='utf-8') as f:
        data = f.read()
except:
    print("An error occurred")