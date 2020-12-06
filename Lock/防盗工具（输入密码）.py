# coding=utf-8
import json
import sys
import traceback
from PIL import Image, ImageTk
from win32gui import GetForegroundWindow as getWindow
from sys import argv
import os
import tkinter as tk
import hashlib
import time
from threading import Thread
import threading

waittime = 0.05  # 公用等待时间


class Configure:
    def __init__(self):
        self.configureFile = 'PasswordConfiguration.azo'
        self._con: dict
        self._defaultCon = {
            "KillTaskManager": False,
        }

    def getAttr(self, item):
        try:
            return self._con[item]
        except KeyError:
            sys.stderr.write('NoThisName:' + item + '\n')
            sys.stderr.flush()
            return None

    def initCon(self):
        try:
            with open(self.configureFile, 'r') as r:
                getCon = r.read()
                # noinspection PyAttributeOutsideInit
                self._con = json.loads(getCon)
        except (FileNotFoundError, json.JSONDecodeError):
            with open(self.configureFile, 'w') as w:
                json.dump(self._defaultCon, w)
            self.initCon()  # 重新读取


class PasswordManager:
    def __init__(self):
        self.con = Configure()
        self.con.initCon()
        self.__password = '0b5e948e92f21dcbd1025a4e5ba7eca4'  # md5加密后的密码
        self._filepath = 'E:\\Azazo1Keys\\OpeningPassword.key'  # 密码文件位置
        self._pngpath = r"azazo1_logo.png", r'C:\Users\13436\OneDrive\图片\azazo1_logo.png'  # 末尾显示图片文件位置

    def getCon(self, item):
        return self.con.getAttr(item)

    def check(self, password: str):
        return self.encrypt(password) == self.__password

    def checkFile(self):
        try:
            with open(self._filepath, 'r') as r:
                get = r.read()
            if self.encrypt(get) == self.__password:
                return True
        except Exception as e:
            print(type(e), e)

    @staticmethod
    def encrypt(str1: str) -> str:
        md5 = hashlib.md5(str1.encode())
        return md5.hexdigest()


class GUIBuilder(PasswordManager):
    def __init__(self):
        super().__init__()
        self.event = threading.Event()  # 用于同步线程
        self.root = None
        self.entry = None
        self.label = None
        self.text = None
        self.wrongtimes = 0
        self.alive = True
        self.originWindow = getWindow()

    def closecomputer(self):
        os.system('shutdown -s -t 10')
        self.close()

    def rightpass(self):
        self.label['text'] = f'Welcome!'
        self.root.update()

    def close(self):
        self.alive = False
        self.root.destroy()

    def check(self, password: str, gopass=False):
        if not super().check(password) and not self.checkFile() and not gopass:
            self.entry.delete(0, tk.END)
            self.wrongtimes += 1
            self.label['text'] = f"Wrong Password! This is the {self.wrongtimes} times."
            if self.wrongtimes >= 3:
                self.closecomputer()
        else:
            self.rightpass()
            os.system('shutdown -a')
            time.sleep(0.5)
            # 取下所有元素
            for item in list(self.root.children.values())[::-1]:  # 倒序迭代窗口中元素
                item.forget()
                time.sleep(waittime)
                self.root.update()
            # 放置图片

            for p in self._pngpath:
                try:
                    im = Image.open(p)
                    im.resize((self.root.winfo_screenwidth(), self.root.winfo_screenheight()), Image.ANTIALIAS)
                    tkim = ImageTk.PhotoImage(im)
                    label = tk.Label(self.root, image=tkim, background='#000000')
                    label.pack(fill=tk.BOTH, expand=True)
                    self.root.update()
                    break  # 无报错
                except Exception:
                    traceback.print_exc()

            time.sleep(waittime * 50)

            self.close()

    def getWindow(self):
        self.originWindow = getWindow()
        self.text['text'] += f'[INFO] {time.asctime()} Get Window Successfully\n'
        self.root.bind('<Enter>', lambda *args: None)  # 防止第二次更新

    def go(self):
        self.root = root = tk.Tk()

        self.label = tk.Label(root, text='Hello, please input my password. '
                                         'If you want to quit, '
                                         'just close the computer in a correct way.\n'
                                         f'If you have a Key File in Correct Path: {self._filepath}, just click Verify.')
        self.label.pack(fill=tk.BOTH, expand=True)  # 提示信息
        self.entry = entry = tk.Entry(root, show='*')
        entry.pack(fill=tk.X, expand=True)

        buttonframe = tk.Frame(root)
        buttonframe.pack(fill=tk.BOTH, expand=True)

        self.text = text = tk.Label(
            root,
            height=10,  # 消息框占用行数
            text='',
        )
        text.pack(expand=True, fill=tk.BOTH)

        tk.Button(  # 确认按钮
            buttonframe,
            text='Verify',
            background='#ffff00',
            command=lambda: self.check(entry.get())
        ).pack(side=tk.LEFT, expand=True)

        tk.Button(  # 关机按钮
            buttonframe,
            text='Close Computer',
            background='#ff0000',
            command=self.closecomputer
        ).pack(side=tk.LEFT, expand=True)

        entry.focus()
        entry.bind('<Return>', lambda *arg: self.check(entry.get()))
        entry.bind('<Escape>', lambda *arg: self.closecomputer())

        root.title(argv[0].split('\\')[-1])
        root.bind('<Enter>', lambda *a: self.getWindow())  # 通过鼠标悬浮获取当前窗口句柄
        root.protocol("WM_DELETE_WINDOW", lambda: None)
        root.attributes("-fullscreen", True)
        root.attributes("-topmost", True)
        self.event.set()  # 同步多线程防止太早形成 调用NoneType的局面
        root.mainloop()


def checkloop(gui: GUIBuilder):
    this = argv[0].replace("/", os.sep)
    gui.event.wait()  # 同步多线程防止太早形成 调用NoneType的局面
    while not gui.checkFile() and gui.alive:
        try:
            os.system('wmic process where Name="Taskmgr.exe" delete') if gui.getCon('KillTaskManager') else None
            if getWindow() != gui.originWindow:  # 检测到窗口离开，重新启动程序
                gui.text['text'] += f'[INFO] {time.asctime()} {getWindow(), gui.originWindow}\n'
                os.system('"{}"'.format(this))  # 新建进程
                gui.close()  # 守护线程关闭窗口后自动关闭
            gui.text['text'] += f'[INFO] {time.asctime()} Load File Failed.\n'
            if len(gui.text['text'].split('\n')) > 7:  # 消息显示最大行数
                gui.text['text'] = '\n'.join(gui.text['text'].split('\n')[1:])
            time.sleep(1)
        except Exception:
            traceback.print_exc()
            return
    gui.text['text'] = ''
    gui.text['text'] += f'[INFO] {time.asctime()} Load File Successfully!\n'
    time.sleep(waittime)
    gui.text['text'] += f'[INFO] {time.asctime()} File Reading...'
    time.sleep(waittime)
    gui.text['text'] += f'Read It!\n'
    time.sleep(waittime)
    gui.text['text'] += f'[INFO] {time.asctime()} Password Parsing...'
    time.sleep(waittime)
    gui.text['text'] += f'Parsed It!\n'
    time.sleep(waittime)
    gui.text['text'] += f'[INFO] {time.asctime()} Password is Corrected.\n'
    time.sleep(waittime)
    gui.text['text'] += f'[INFO] {time.asctime()} Welcome to use Azazo1\'s Computer.\n'
    time.sleep(waittime)
    gui.check('', True)


if __name__ == '__main__':
    g = GUIBuilder()
    rp = Thread(target=checkloop, args=(g,))  # 不断循环检查的线程
    rp.setDaemon(True)
    rp.start()
    g.go()
