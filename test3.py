import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
import numpy as np


'''
Class name  : Data share
Ver         : Ver 0
Release     : 2018 - 07 -06
Developer   : Deail Lee

'''

import socket
import pickle
from struct import pack, unpack
from numpy import shape
from time import sleep


class DataShare:
    def __init__(self, ip, port):
        # socket part
        self.ip, self.port = ip, port  # remote computer

        # cns-data memory
        self.mem = {}  # {'PID val': {'Sig': sig, 'Val': val, 'Num': idx }}
        self.list_mem = {}          ##
        self.list_mem_number = []   ##
        self.number = 0             ##

        self.result=[]
        self.trigger = True
        self.Detection_signal = 0
        self.ActionPlanning_signal = 0
        self.timer1 = 0
        self.timer1_signal = False

        self.fig = plt.figure()
        self.ax1 = self.fig.add_subplot(3, 1, 1)
        self.ax2 = self.fig.add_subplot(3, 1, 2)
        self.ax3 = self.fig.add_subplot(3, 1, 3)

    # 1. memory reset and refresh UDP
    def reset(self):
        self.mem, self.list_mem = {}, {}
        self.initial_DB()
        for i in range(5):
            self.read_socketdata()
        print('Memory and UDP network reset ready...')

    # 2. update mem from read CNS
    def update_mem(self):
        data = self.read_socketdata()
        for i in range(0, 4000, 20):
            sig = unpack('h', data[24 + i: 26 + i])[0]
            para = '12sihh' if sig == 0 else '12sfhh'
            pid, val, sig, idx = unpack(para, data[8 + i:28 + i])
            pid = pid.decode().rstrip('\x00')  # remove '\x00'
            if pid != '':
                self.mem[pid]['Val'] = val
                self.list_mem[pid]['Val'].append(val)

    # 3. change value and send
    def sc_value(self, para, val, cns_ip, cns_port):
        self.change_value(para, val)
        self.send_data(para, cns_ip, cns_port)

    # 4. dump list_mem as pickle (binary file)
    def save_list_mem(self, file_name):
        with open(file_name, 'wb') as f:
            print('{}_list_mem save done'.format(file_name))
            pickle.dump(self.list_mem, f)

    # (sub) 1.
    def animate(self,i):
        # 1. 값을 로드.
        # 2. 로드한 값을 리스로 저장.
        self.update_mem()
        self.list_mem_number.append(self.number)

        #self.test()
        self.Detection()
        self.ActionPlanning()
        # self.timer1 += 1

        self.number += 1

        # 3. 이전의 그렸던 그래프를 지우는거야.
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        # 4. 그래프 업데이트.
        self.ax1.plot(self.list_mem_number, self.list_mem['ZINST65']['Val'],label='RCS Pressure',linewidth=1)
        self.ax2.plot(self.list_mem_number, self.list_mem['UCOLEG1']['Val'], label='Loop1 Tcold', linewidth=1)
        self.ax2.plot(self.list_mem_number, self.list_mem['UCOLEG2']['Val'], label='Loop2 Tcold', linewidth=1)
        self.ax2.plot(self.list_mem_number, self.list_mem['UCOLEG3']['Val'], label='Loop3 Tcold', linewidth=1)
        self.ax3.plot(self.list_mem_number, self.result, label='Result', linewidth=1)
        # 범례 설정
        self.ax1.legend(loc='upper right', ncol=5, fontsize=8)
        self.ax2.legend(loc='upper right',  fontsize=8)
        self.ax3.legend(loc='upper right', ncol=5, fontsize=8)

        #self.fig.suptitle('ddd', fontsize = 15)
        self.ax1.set_title('RCS Pressure Monitoring', fontsize=15)
        self.ax1.axhline(y=161.6, ls='--', color='r', linewidth=1.5)
        self.ax1.axhline(y=154.7, ls='--', color='r', linewidth=1.5)
        self.ax1.set_ylim(153, 164)
        self.ax1.set_yticks([154.7, 161.6])
        self.ax1.set_yticklabels(['154.7[kg/cm^2]', '161.6[kg/cm^2]'], fontsize = 8)
        self.ax2.set_title('RCS Tcold Monitoring', fontsize=15)
        self.ax2.axhline(y=305, ls='--', color='r', linewidth=1.5)
        self.ax2.axhline(y=286.7, ls='--', color='r', linewidth=1.5)
        self.ax2.set_ylim(282, 310)
        self.ax2.set_yticks([286.7, 305])
        self.ax2.set_yticklabels(['286.7[℃]', '305[℃]'], fontsize=8)
        self.ax3.set_title('LCO 3.4.1 Monitoring', fontsize = 15)
        self.ax3.set_ylim(-0.1, 1.1)
        # self.ax1.set_ylabel('value')
        self.ax3.set_xlabel('Time (s)')
        self.fig.tight_layout()


    # (sub) 1.1make grape
    def make_gp(self):
        style.use('fivethirtyeight')  # 뭔지 몰라 # 스타일..
        ani = animation.FuncAnimation(self.fig, self.animate, interval=1000)
        plt.show()

    # (sub) socket part function
    def read_socketdata(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # socket definition
        sock.bind((self.ip, self.port))
        data, addr = sock.recvfrom(4008)
        sock.close()
        return data

    # (sub) initial memory
    def initial_DB(self):
        idx = 0
        with open('./db.txt', 'r') as f:   # use unit-test
        #with open('./fold/db.txt', 'r') as f: # This line is to use the "import" other function
            while True:
                temp_ = f.readline().split('\t')
                if temp_[0] == '':  # if empty space -> break
                    break
                sig = 0 if temp_[1] == 'INTEGER' else 1
                self.mem[temp_[0]] = {'Sig': sig, 'Val': 0, 'Num': idx}
                self.list_mem[temp_[0]] = {'Sig': sig, 'Val': [], 'Num': idx}
                idx += 1

    def Detection(self):

        if self.trigger == True :

            if 154.7 < self.mem['ZINST65']['Val'] <  161.6 and 286.7 < self.mem['UCOLEG1']['Val'] < 293.3 :
                self.result.append(1)
            else:
                self.result.append(0)
                self.Detection_signal = 1
                print(self.ActionPlanning_signal)
                # self.trigger.append(0)
        elif self.ActionPlanning_signal == 1 :
            if self.timer1_signal == True :
                self.timer1 += 1


            if 154.7 < self.mem['ZINST65']['Val'] <  161.6 and 286.7 < self.mem['UCOLEG1']['Val'] < 293.3 :
                if self.timer1 < 180 : #180 -> 7200으로 바꿀 것
                    print('복구 성공')
                    print(self.timer1)
                    self.result.append(1)
                    self.trigger = True
                    print('Detection1번 신호 발생')
                else :
                    print('소용없어.')
                    print(self.timer1)
                    self.result.append(0)
                    self.Detection_signal = 2
            else:
                if self.timer1 < 180 :
                    print('초는 멀쩡해유')
                    self.result.append(0)
                    self.Detection_signal = 0
                    print(self.timer1)
                else:
                    print('시간도 초과했따')
                    self.result.append(0)
                    self.Detection_signal = 2


    def ActionPlanning(self):

        if self.Detection_signal == 1 :
            print('신호 잘옴.')
            self.trigger = False
            self.ActionPlanning_signal = 1
            self.timer1_signal = True

        elif self.Detection_signal == 2:
            print('운전모드 신호 줘라')
            self.trigger = False

        else :
            print('pass')
            pass



if __name__ == '__main__':

    # unit test
    test = DataShare('192.168.0.192', 8001)  # current computer ip / port
    test.reset()

    test.make_gp()