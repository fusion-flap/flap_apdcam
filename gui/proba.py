import glob

files = glob.glob("/home/barna/tmp/a-[0-9].txt")
for f in files:
    print(f)
