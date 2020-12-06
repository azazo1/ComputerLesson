import hashlib
while 1:
    print(hashlib.md5(input("输入密码：").encode()).hexdigest())
