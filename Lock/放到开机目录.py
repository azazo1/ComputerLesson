import getpass
import os
import shutil

username = getpass.getuser()
targetpath = rf'C:\Users\{username}\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup'

os.system(f'copy {input("输入要移动的文件位置：")} {targetpath}')
input('成功移动')
