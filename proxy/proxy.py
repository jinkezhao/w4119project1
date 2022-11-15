#!/usr/bin/env python
from socket import socket, AF_INET, SOCK_STREAM
import select
import time
import re
import sys
import thread
import math
from multiprocessing import Process


averagethroughput=0
bitrate = [45514,176827,506300,1006743] 


class Proxy:
    def __init__(self,soc,alpha,fake_ip,server_ip):
        print('init: accepting client')
        self.client,_ = soc.accept()
        self.target = None
        self.web_server_ip = server_ip
        self.fake_ip = (fake_ip,0)
        self.br = 46
        self.bitrate = 45514
        self.a = alpha

    def getClientRequest(self):
        #print('receving from client')
        global bitrate
        bitrate1=re.compile(b"bunny_[0-9]*bps")
        chunk_name = re.compile(b"BigBuckBunny_6s[0-9]*.m4s")
        request = ""
        self.client.setblocking(0)
        while True:
            try:
                request1 = self.client.recv(4096)
            
                request+=request1
            except :
                break
        self.client.setblocking(1)
        #print(request)
        bit_res = re.findall(bitrate1,request)
        if bit_res:
            for i in bit_res:
                rate = int(i[6:-3])
                if rate not in bitrate:
                    bitrate.append(rate)
                    #print(bitrate)
        chk_name_res=re.search(chunk_name,request,flags=0)
        #print("aaaaaaaaa")
        get_chunk_name=None
        if chk_name_res:
            get_chunk_name=chk_name_res.group(0)
            
        return (get_chunk_name,request)

    def connectServer(self,request):
        self.target = socket(AF_INET, SOCK_STREAM)
        #print('connecting to server')
        self.target.bind(self.fake_ip) #bind socket to fake ip
        self.target.connect((self.web_server_ip,8080))
        #print('sending message to server')
        self.target.send(request)
    
    def chooseBitrate(self,throughput):
        global bitrate
        length = len(bitrate)
        for i in range(length):
            if throughput/1.5 < bitrate[i]:
                if i == 0:
                    return bitrate[0]
                else:
                    return bitrate[i-1]
        res=bitrate[length-1]
        return res
    
    def receive_calculate(self,chunk_name=None):
        packet_length = re.compile(b'ontent-Length: .\w+') 
        global  averagethroughput
        ts = time.time()
        inputstream=[self.client,self.target]
        old_name=""
        while True:
            readable,wirteable,err=select.select(inputstream,[],inputstream,10)
            if err:
                break
            for i in readable:
                if i is self.client:
                    tmp = self.getClientRequest()
                    request=tmp[1]
                    chunk_name=tmp[0]
                    if chunk_name:
                        print (chunk_name)
                    if request:
                        self.target.send(request)




                if i is self.target:
                    buffer1=""
                    self.target.setblocking(0)
                    while True:
                        try:
                            data = self.target.recv(4096)
                            buffer1+=data
                        except:
                            break
                    self.target.setblocking(1)
                    self.client.send(buffer1)
                    res = re.search(packet_length,buffer1,flags = 0)

                    if res:
                        pac_length = int(res.group(0)[15:])


                    if chunk_name: 
                        tf = time.time()
                        dur = tf - ts
                        newthroughput = 8*pac_length/(dur)/1024
                        averagethroughput = self.a * newthroughput + (1 - self.a) * averagethroughput
                        ts = time.time()
                        self.bitrate = self.chooseBitrate(averagethroughput)
                        self.br = math.ceil(self.bitrate/1000.)
                        log.write('%f %f %f %f %d %s b\'/bunny_%dbps/%s\'\n'%(tf,dur,newthroughput,
                            averagethroughput,self.br,self.web_server_ip,self.bitrate,chunk_name))
                        chunk_name=None
                
                        print("==========================")
                        print(averagethroughput)
                        print(self.bitrate)
        self.client.close()
        self.target.close()
        self.log.close()
        
        return           
    

    def run(self):
    
        tmp = self.getClientRequest()
        request=tmp[1]
        if request:
            self.connectServer(request)
            self.receive_calculate(tmp[0])


if __name__ == '__main__':
    print(sys.argv)
    log_path = sys.argv[1]
    a = sys.argv[2]
    listen_port = sys.argv[3]
    fake_ip = sys.argv[4]
    web_server_ip = sys.argv[5]
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.bind(('', int(listen_port)))
    clientSocket.listen(1)
    print('The proxy is ready to receive')
    log = open(log_path,'w')
    while True:
        try:
            #client_ocket,info = proxySocket.accept()
            # a new thread for each connection
            thread.start_new_thread(Proxy(clientSocket,float(a),fake_ip, web_server_ip).run, ())
            #print ("asd")
        except Exception as e:
            print(e)
