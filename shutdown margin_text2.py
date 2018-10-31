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
from parameter import para


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

        self.data=[]

        self.fig = plt.figure()
        self.ax1 = self.fig.add_subplot(1, 1, 1)

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


        self.ShutdownMarginCalculation()
        self.number += 1

        # 3. 이전의 그렸던 그래프를 지우는거야.
        self.ax1.clear()

        # 4. 그래프 업데이트.
        self.ax1.plot(self.list_mem_number, self.result, label='Result', linewidth=1)
        self.ax1.legend(loc='upper right', ncol=5, fontsize=10)
        self.ax1.set_ylim(0, 1.1)
        self.ax1.set_xlabel('Time')
        self.ax1.set_ylabel('Monitoring Result')
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

    def ShutdownMarginCalculation(self):

        ##################################################
        # BOL일때, 현출력 -> 0% 하기위한 출력 결손량을 계산하자.

        ReactorPower = self.mem['QPROLD']['Val']
        PowerDefect_BOL = para.TotalPowerDefect_BOL * ReactorPower / para.HFP
        print(PowerDefect_BOL)
        self.data.append(PowerDefect_BOL)

        ###################################################
        # EOL일때, 현출력 -> 0% 하기위한 출력 결손량을 계산하자.

        ReactorPower = self.mem['QPROLD']['Val']
        PowerDefect_EOL = para.TotalPowerDefect_EOL * ReactorPower / para.HFP
        print(PowerDefect_EOL)
        self.data.append(PowerDefect_EOL)

        ####################################################
        # 현재 연소도일때, 현출력 -> 0% 하기위한 출력 결손량을 계산하자.
        A = para.Burnup_EOL - para.Burnup_BOL
        B = PowerDefect_EOL - PowerDefect_BOL
        C = para.Burnup - para.Burnup_BOL

        PowerDefect_Burnup = B * C / A + 1602
        print(PowerDefect_Burnup)
        self.data.append(PowerDefect_Burnup)

        ######################################################
        # 반응도 결손량을 계산하자

        PowerDefect_Final = PowerDefect_Burnup + para.VoidCondtent
        print(PowerDefect_Final)
        self.data.append(PowerDefect_Final)

        #####################################################
        # 운전불가능 제어봉 제어능을 계산하자

        InoperableRodWorth = para.InoperableRodNumber * para.WorstStuckRodWorth
        print(InoperableRodWorth)
        self.data.append(InoperableRodWorth)

        ######################################################
        # 비정상 제어봉 제어능을 계산하자

        if para.InoperableRodName == 'C':
            # print(para.BankWorth_C)
            AbnormalRodWorth = para.BankWorth_C / 8
            return print(AbnormalRodWorth), self.data.append(AbnormalRodWorth)
        elif para.InoperableRodName == 'A':
            AbnormalRodWorth = para.BankWorth_A / 8
            return print(AbnormalRodWorth), self.data.append(AbnormalRodWorth)
        elif para.InoperableRodName == 'B':
            AbnormalRodWorth = para.BankWorth_B / 8
            return print(AbnormalRodWorth), self.data.append(AbnormalRodWorth)
        elif para.InoperableRodName == 'D':
            AbnormalRodWorth = para.BankWorth_D / 8
            return print(AbnormalRodWorth), self.data.append(AbnormalRodWorth)

        #####################################################
        # 운전 불능, 비정상 제어봉 제어능의 합을 계산하자

        InoperableAbnormal_RodWorth = InoperableRodWorth + AbnormalRodWorth
        print(InoperableAbnormal_RodWorth)
        self.data.append(InoperableAbnormal_RodWorth)


        #####################################################
        # 현 출력에서의 정지여유도를 계산하자

        ShutdownMargin = para.TotalRodWorth - InoperableAbnormal_RodWorth - PowerDefect_Final
        print(ShutdownMargin)
        #self.data.append(ShutdownMargin)

        ######################################################
        # 정지여유도 제한치를 만족하는지 비교하자

        if ShutdownMargin >= para.ShutdownMarginValue:
            self.result.append(1) #만족
            return ShutdownMargin, print('만족')#, self.data.append('만족')
        else:
            self.result.append(0) #불만족
            return ShutdownMargin, print('불만족')#, self.data.append('불만족')




    def test(self):
        a = self.mem['ZINST65']['Val'] + self.mem['UAVLEG1']['Val']
        self.tt.append(a)
        print(self.tt)

    def write(self):
        print(self.data)

if __name__ == '__main__':

    # unit test
    test = DataShare('192.168.0.192', 8001)  # current computer ip / port
    test.reset()

    test.make_gp()
    test.write()


