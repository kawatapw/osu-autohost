#!/usr/bin/python3.6

import sys,socket,string,os,time,random,json,_thread,math
from threading import Timer
try:
    import requests
except ImportError:
    print('need requests dependency\ninstalling...')
    os.system('pip install requests')
    import requests
try:
    import numpy
except ImportError:
    print('need requests dependency\ninstalling...')
    os.system('pip install numpy')
    import numpy

KEY = "ad8c161908bcf5bf8f595300537edbbecb7fc17b"

class osuIRC:
    '''osu IRC class, dipakai untuk connect ke server irc, terima dan kirim data.'''
    host = "irc.kawata.pw"
    port = 6667
    UID = "AutoHost".lower()
    KEY = "b4e20c67424bd991d0c9b2d143a5c4df".lower()

    def connect():
        '''sambung ke server IRC osu!'''
        try:
            osuIRC.IRC = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            osuIRC.IRC.connect((osuIRC.host, osuIRC.port))
            osuIRC.send("PASS %s" %osuIRC.KEY)
            osuIRC.send("NICK %s" %osuIRC.UID)
            osuIRC.send("USER %s %s bla :%s" % (osuIRC.UID,osuIRC.host,osuIRC.UID))
            return True
        except:
            print('cannot connect to IRC server')
            return False
    def send(x):
        '''mengirim ke IRC'''
        osuIRC.IRC.send((x+"\r\n").encode())
    def sendto(channel,message):
        osuIRC.send("PRIVMSG %s %s" %(channel,message))
    def recv(size=4096):
        '''menerima dari IRC, convert ke lower caps, decode utf-8 menjadi string'''
        return osuIRC.IRC.recv(size).decode().lower()
    def show(file):
        '''cetak jika bukan baris kosong, notifikasi join atau notifikasi quit'''
        osuIRC.kata = file.split(" ")
        if len(osuIRC.kata)>2 :
            if osuIRC.kata[1] != ("quit" or "join"):
                #print(file)
                time.sleep(0.001)
    def DC():
        '''case disconnected'''
        osuIRC.IRC.shutdown(socket.SHUT_RDWR)
        osuIRC.IRC.close()
        osuIRC.connect()
        for room in osuCMD.roomList:
            osuIRC.send("JOIN %s" %room.id)
    def begin():
        connect = osuIRC.connect()
        print('[ connect ok ]')
        if connect == False:
            print('[ connect failed, closing ]')
            quit()
        osuIRC.watchdog = Watchdog(20, osuIRC.call)
        osuIRC.call()
    def call():
        print('WATCHDOG BITE!')
        while 1:
            osuIRC.loop()
    def loop():
        raw = osuIRC.recv()
        if raw.find('ping cho.ppy.sh') != -1:
            osuIRC.send('PONG')
            print('[ PONG ]')
        data = raw.split("\n")
        if len(data)-1 == 0:
            osuIRC.DC()
        for osuIRC.baris in data:
            osuIRC.kata = osuIRC.baris.split(" ")
            osuIRC.show(osuIRC.baris)
            osuCMD.getBasic()
            if osuCMD.chat != None:
                osuCMD.get()
                osuCMD.cmd()
                osuCMD.issuer = None
                osuCMD.type = None
                osuCMD.channel = None
                osuCMD.chat = None
        osuIRC.watchdog.reset()


class osuRoom():
    '''
    room has : id, number, name, mode, playmode, difficultyrating
               playerList[n], vote_ready[n], vote_skip[n], creator, moderator[n],
               map_list[n], auto_map[n], nowPlaying, nowPlayingMap, last_auto
    '''
    def __init__(self,creator,name=None,mode='std',id=None):
        self.creator = creator
        self.moderator = []
        self.roomNumber = 0
        self.mode = mode
        self.difficultyrating = ['3','4']
        self.playerList = []
        self.vote_ready = []
        self.vote_skip = []
        self.map_list = []
        self.nowPlaying = 0
        self.nowPlayingMap = 0
        self.auto_map = []
        self.last_auto = None
        if (name==None) and (id!=None):
            self.id = id
            self.getPlayerList = True
            self.name = "INVITED ROOM %s" %(id)
            _thread.start_new_thread(self.getPlayer,())
        elif (name!=None) and (id==None):
            self.name = name
            self.getID = True
            self.getNumber = True
            osuIRC.sendto('banchobot','!mp make %s | !info' %self.name)
            print('making room : %s' %self.name)
            _thread.start_new_thread(self.getRoomNumID,())
        _thread.start_new_thread(self.watchdog,())
    def watchdog(self):
        time.sleep(20)
        if self.playerList == []:
            self.close()
            print(self.id,'watchdog bite')
        else:
            self.watchdog()
    def getRoomNumID(self):
        print('getting room number...')
        watchdog = Watchdog(20)
        try:
            while (self.getID or self.getNumber):
                if len(osuIRC.kata) > 2:
                    if osuIRC.kata[1] == "332":
                        self.id = osuIRC.kata[3]
                        self.number = osuIRC.kata[6].replace("#","")
                        print("room id found : %s" %self.id)
                        print("room number found : %s" %self.number)
                        self.getID = False
                        self.getNumber = False
                if (self.getNumber==False) and (self.getID==False):
                    osuIRC.sendto(self.id,"!mp password")
                    osuIRC.sendto(self.id,"!mp set 0 0 16")
                    osuIRC.sendto(self.id,"!mp mods freemod")
                    print(self.id,"remove all shitty things success ...")
                    osuIRC.sendto(self.creator,"room created :  [osump://%s/ %s | !info] [%s mode]" %(self.number,self.name,self.mode))
                    print(self.id,"sending invitation to room creator success ...")
        except:
             print("room created, but cannot obtain info! delete it manually.")
        watchdog.stop()
    def getPlayer(self):
        print('getting player')
        watchdog = Watchdog(20)
        try:
            while(self.getPlayerList):
                if len(osuIRC.kata) > 2:
                    playerList = osuIRC.kata[6:]
                    for player in playerList:
                        if player == ("+%s" %osuIRC.UID):
                            try:
                                playerList.remove(player)
                            except:
                                print('cannot remove %s from player list' %player)
                    try:
                        player.remove("\r")
                    except:
                        print('cannot remove /r from player list')
                    self.playerList.extend(playerList)
                    self.getPlayerList = False
                    osuIRC.sendto(self.maker,"Joined the room!")
                    print(self.playerList)
        except RuntimeError:
            print("room created, but cannot obtain info! delete it manually.")
        watchdog.stop()
    def close(self):
        osuIRC.sendto(self.id,"!mp close")
        print(self.id,'closed')
    def begin(self):
        osuIRC.sendto(self.id,'!mp start 5')
        self.vote_ready = []
        self.vote_skip = []
        print(self.id,'game begin')
    def next(self):
        print(self.id,'getting next song')
        if len(self.map_list) != 0:
            print(self.id,'get song from user queue')
            self.nowPlaying = self.map_list.pop(0)
            self.nowPlayingMap = self.nowPlaying.hasDiff(self.difficultyrating)
            if self.nowPlayingMap in self.nowPlaying.map_list.keys():
                if self.mode==self.nowPlaying.map_list[self.nowPlayingMap]['mode']:
                    osuIRC.sendto(self.id,"!mp map %s" %self.nowPlayingMap)
                    if self.nowPlaying.DTHT != None:
                        osuIRC.sendto(self.id,"!mp mods %s freemod"%self.nowPlaying.DTHT)
                    else:
                        osuIRC.sendto(self.id,"!mp mods freemod")
                    #self.nowPlaying.sendPP(map,self.id)
                    _thread.start_new_thread(self.nowPlaying.getPP,(self.nowPlayingMap,self.id))
                else:
                    osuIRC.sendto(self.id,"%s not have %s mode. skipping ..." %(self.nowPlaying.mergeName,self.mode))
                    self.next()
            else:
                osuIRC.sendto(self.id,"%s not have  %s - %s ★  difficulty. skipping ..." %(self.nowPlaying.mergeName,self.difficultyrating[0],self.difficultyrating[1]))
                self.next()
        else:
            print(self.id,'get random song')
            if self.auto_map == []:
                print(self.id,'empty random')
                self.last_auto,self.auto_map = osuAPI.setRand(last=self.last_auto,playMode=self.mode)
            self.nowPlaying = osuBeatSet(set=self.auto_map.pop(0))
            self.nowPlayingMap = self.nowPlaying.hasDiff(self.difficultyrating)
            if self.nowPlayingMap != None:
                if self.nowPlaying.map_list[self.nowPlayingMap]['mode']==self.mode:
                    osuIRC.sendto(self.id,'!mp map %s' %self.nowPlayingMap)
                    osuIRC.sendto(self.id,"!mp mods freemod")
                    _thread.start_new_thread(self.nowPlaying.getPP,(self.nowPlayingMap,self.id))
                else:
                    self.next()
            else:
                self.next()
        del self.vote_ready[:]
        del self.vote_skip[:]
    def isJoin(self,name):
        if name not in self.playerList:
            if name != '':
                self.playerList.append(name)
                print(self.id,self.playerList)
    def isQuit(self,name):
        try:
            self.playerList.remove(name)
            if name in self.vote_ready:
                self.vote_ready.remove(name)
            if name in self.vote_skip:
                self.vote_skip.remove(name)
            print(self.id,self.playerList)
        except ValueError:
            pass

class osuBeatSet():
    '''
        set has : title, artist, creator, set_id, map_list['map_id'],DTHT,preferredDiff
        map has : id, diff, approve_stats ,diff_name ,mode, full_name
    '''
    def __init__(self,set=None,map=None,DTHT=None):
        self.DTHT = DTHT
        if set!=None :
            self.preferredDiff = None
            self.preferredMap = None
            #_thread.start_new_thread(self.getInfo,(set,))
            self.getInfo(set=set)
        elif map!=None :
            mapID = osuAPI.songAPI(map=map)
            if mapID != []:
                self.preferredDiff = mapID[0]['difficultyrating']
                self.preferredMap = map
                #_thread.start_new_thread(self.getInfo,(mapID[0]['beatmapset_id'],))
                self.getInfo(set=mapID[0]['beatmapset_id'])
            else:
                raise ValueError('Empty JSON','getMAP',str(map))
        else:
            raise ValueError('BeatSet not Assign Properly','osuBeatSet')
    def getInfo(self,set):
        json = osuAPI.songAPI(set=set)
        if json != []:
            self.title = json[0]['title']
            self.artist = json[0]['artist']
            self.creator = json[0]['creator']
            self.set_id = json[0]['beatmapset_id']
            self.mergeName = "[https://osu.ppy.sh/s/%s %s - %s (%s)]" %(self.set_id,self.artist,self.title,self.creator)
            self.map_list = {}
            for song in json:
                self.map_list[song['beatmap_id']] = {'id':song['beatmap_id'],'difficulty':song['difficultyrating'],'mode':osuAPI.MODEinv[int(song['mode'])],'diff_name':song['version'],'max_combo':song['max_combo'],'full_name':'[https://osu.ppy.sh/b/%s %s  [%s]]' %(song['beatmap_id'],self.title,song['version'])}
        else:
            raise ValueError('Empty JSON','getSET',str(set))
    def getPP(self,map,channel):
        watchdog = Watchdog(20)
        found = False
        data = []
        try:
            osuIRC.sendto('tillerino','\001ACTION is listening to [https://osu.ppy.sh/b/%s %s - %s]\001'%(map,self.artist,self.title))
            if self.DTHT != None:
                time.sleep(1)
                osuIRC.sendto('tillerino','!with %s'%self.DTHT)
                print('tillerino','!with %s'%self.DTHT)
            check = self.artist.lower().split(' ')[0]
            while not found:
                if osuIRC.kata[0]==":tillerino!cho@ppy.sh" and osuIRC.kata[2]==osuIRC.UID:
                    if osuIRC.kata[3] == ":I'm":
                        osuIRC.sendto(channel,'ppNotFound : Cannot obtain pp. the song is either very new, very hard, or not STD mode.')
                        found = True
                    else:
                        del data [:]
                        for item in osuIRC.kata:
                            data.append(item)
                        #print(data)
                        #time.sleep(0.3)
                        index = [data.index('95%:')+1,data.index('98%:')+1,data.index('99%:')+1,data.index('100%:')+1]
                        pp = []
                        for i in index:
                            pp.append(data[i])
                        if self.DTHT != None:
                            if 'dt' in data:
                                osuIRC.sendto(channel,'%s +DT ||  95%%: %s  ||  98%%: %s  ||  99%%: %s  ||  PF: %s  || [https://github.com/Tillerino/ppaddict [data from Tillerino]]' %(self.map_list[map]['full_name'],pp[0],pp[1],pp[2],pp[3]))
                                print('[GET] Tillerino PP')
                                found = True
                            elif 'ht' in data:
                                osuIRC.sendto(channel,'%s +HT ||  95%%: %s  ||  98%%: %s  ||  99%%: %s  ||  PF: %s  || [https://github.com/Tillerino/ppaddict [data from Tillerino]]' %(self.map_list[map]['full_name'],pp[0],pp[1],pp[2],pp[3]))
                                print('[GET] Tillerino PP')
                                found = True
                        else:
                            osuIRC.sendto(channel,'%s ||  95%%: %s  ||  98%%: %s  ||  99%%: %s  ||  PF: %s  || [https://github.com/Tillerino/ppaddict [data from Tillerino]]' %(self.map_list[map]['full_name'],pp[0],pp[1],pp[2],pp[3]))
                            print('[GET] Tillerino PP')
                            found = True
        except RuntimeError:
           print(channel,'Watchdog bite getPP')
           osuIRC.sendto(channel,'RequestTimeout : cannot obtain PP')
        watchdog.stop()
    def _getPP(self,map,mod):
        json = osuAPI.scoreAPI(map=map,mods=mod,DTHT=self.DTHT)
        if json != []:
            combo = []
            accuracy = []
            ppy = []
            mean = 0
            for score in json:
                acc = ((int(score['count300']))+(int(score['count100'])*60/100)+(int(score['count50'])*30/100)+(int(score['countmiss'])*0/100))/(int(score['count300'])+int(score['count100'])+int(score['count50'])+int(score['countmiss']))
                streak = int(score['maxcombo'])*acc
                accuracy.append(acc)
                combo.append(streak)
                if score['pp'] != None:
                    ppy.append(float(score['pp']))
                    mean += float(score['pp'])
                else:
                    ppy.append(0)
                    mean = 0
            #print(combo)
            #print(accuracy)
            #print(ppy)
            mean = mean/len(ppy)
            if((mean-ppy[0] > 1) or (mean-ppy[0] < -1)):
                ACCU = numpy.array(accuracy)
                COMBO = numpy.array(combo) #array of data 1a
                PPY = numpy.array(ppy) #array of data 2
                weightCombo = numpy.polyfit(COMBO,PPY,5)
                weightAccu = numpy.polyfit(ACCU,PPY,5) #array of polinomials (high to low)
                weightCombo = weightCombo[::-1]
                weightAccu = weightAccu[::-1]
                X = int(self.map_list[str(map)]['max_combo'])
                resultCombo = float(weightCombo[0]) + float(weightCombo[1])*X + float(weightCombo[2])*X**2 + float(weightCombo[3])*X**3 + float(weightCombo[4])*X**4 + float(weightCombo[5])*X**5 #+ float(PPar[6])*X**6 + float(PPar[7])*X**7
                resultAccu = float(weightAccu[0]) + float(weightAccu[1])*1 + float(weightAccu[2])*1**2 + float(weightAccu[3])*1**3 + float(weightAccu[4])*1**4 + float(weightAccu[5])*1**5 #+ float(PPar[6])*X**6 + float(PPar[7])*X**7
                result = float(weightCombo[0])*float(weightAccu[0]) + float(weightCombo[1])*float(weightAccu[1])*X + float(weightCombo[2])*float(weightAccu[2])*X**2 + float(weightCombo[3])*float(weightAccu[3])*X**3 + float(weightCombo[4])*float(weightAccu[4])*X**4 + float(weightCombo[5])*float(weightAccu[5])*X**5
                #print('comboPP:%s' %resultCombo)
                #print('accuPP:%s' %resultAccu)
                if (resultCombo-resultAccu > 100) or (resultCombo-resultAccu < -100):
                    return round(max(PPY[0],min(resultCombo,resultAccu)),2)
                else:
                    return round(max(PPY[0],(resultCombo+resultAccu)/2),2)
            else:
                return round(mean,2)
        elif json == []:
            return 'noData'
        else:
            raise ValueError('Error JSON','getPP',str(map))#deprecated
    def _getPPAll(self,map,channel):
        pp = {}
        for mods in osuAPI.MODS:
            #try:
            pp[mods] = self.getPP(map=map,mod=mods)
            #except:
            #    pp[mods] = '-eRR exception'
        osuIRC.sendto(channel,'%s  ||  FC: %s pp  |  HD: %s pp  |  HR: %s pp  |  HDHR: %s pp  ||'%(self.map_list[map]['full_name'],pp['NoMod'],pp['HD'],pp['HR'],pp['HDHR']))#deprecated#deprecated
    def hasDiff(self,diff):
        for ID in self.map_list:
            if self.preferredDiff != None:
                if (float(self.preferredDiff)>float(diff[0])) and (float(self.preferredDiff)<float(diff[1])):
                    return self.preferredMap
            if (float(self.map_list[ID]['difficulty'])>float(diff[0])) and (float(self.map_list[ID]['difficulty'])<float(diff[1])):
                return ID


class osuCMD:
    roomList = []
    def get():
        osuCMD.getBasic()
        osuCMD.getMake()
        osuCMD.getJoin()
        osuCMD.getQuit()
        osuCMD.getGameStart()
        osuCMD.getGameFinish()
        osuCMD.getAllReady()
    def getBasic():
        if(len(osuIRC.kata))>1:
            osuCMD.issuer = osuIRC.kata[0].replace(":","").replace("!cho@ppy.sh","")
            osuCMD.type = osuIRC.kata[1]
            if(osuCMD.type=="privmsg"):
                osuCMD.channel = osuIRC.kata[2]
                osuCMD.chat = osuIRC.kata[3:]
            else:
                osuCMD.channel = None
                osuCMD.chat = None
    def getMake():
        if(osuCMD.channel == osuIRC.UID and osuCMD.chat[0] == ":!make"):
            modeIndex = None
            try:
                modeIndex = osuCMD.chat.index('+mode')
            except ValueError:
                pass

            if (modeIndex==None):
                roomname = ' '.join(osuCMD.chat[1:])
                if len(roomname)>42:
                    osuIRC.sendto(osuCMD.issuer,'cannot create room : maximum room name is 42 character including space!')
                else:
                    osuCMD.roomList.append(osuRoom(name=roomname,creator=osuCMD.issuer))
            else:
                roomname = ' '.join(osuCMD.chat[1:modeIndex])
                if len(roomname)>42:
                    osuIRC.sendto(osuCMD.issuer,'cannot create room : maximum room name is 42 character including space!')
                else:
                    try:
                        modeObtain = osuCMD.chat[modeIndex+1]
                        if modeObtain in osuAPI.MODE.keys():
                            mode = modeObtain
                            osuCMD.roomList.append(osuRoom(name=roomname,creator=osuCMD.issuer,mode=mode))
                        else:
                            osuIRC.sendto(osuCMD.issuer,'you input wrong mode ,  mode available:  std , taiko , ctb , mania')
                    except IndexError:
                        osuIRC.sendto(osuCMD.issuer,'you input wrong mode ,  mode available:  std , taiko , ctb , mania')
    def getJoin():
        if osuIRC.baris.find("joined in slot") != -1:
            if osuCMD.issuer == 'banchobot':
                lenlist = len(osuIRC.kata)-4
                name = '_'.join(osuIRC.kata[3:lenlist]).replace(':','')
                for item in osuCMD.roomList:
                    if item.id == osuCMD.channel:
                        item.isJoin(name)
    def getQuit():
        if osuIRC.baris.find("left the game") != -1:
            if osuCMD.issuer == 'banchobot':
                lenlist = len(osuIRC.kata)-3
                name = '_'.join(osuIRC.kata[3:lenlist]).replace(':','')
                for item in osuCMD.roomList:
                    if item.id == osuCMD.channel:
                        item.isQuit(name)
    def getGameStart():
        if osuIRC.baris.find(":the match has started!") != -1:
            if osuCMD.issuer == 'banchobot':
                for item in osuCMD.roomList:
                    if item.id == osuCMD.channel:
                        item.vote_ready = []
                        item.vote_skip = []
    def getGameFinish():
        if osuIRC.baris.find(":the match has finished!") != -1 or osuIRC.baris.find(":aborted the match") != -1:
            if osuCMD.issuer == 'banchobot':
                for item in osuCMD.roomList:
                    if item.id == osuCMD.channel:
                        item.vote_ready = []
                        item.vote_skip = []
                        print(item.id,'game finish')
                        item.next()
    def getAllReady():
        if osuIRC.baris.find(":all players are ready") != -1:
            if osuCMD.issuer == 'banchobot':
                for item in osuCMD.roomList:
                    if item.id == osuCMD.channel:
                        item.begin()
                        print(item.id,'all player ready')

    def cmd():
        osuCMD.cmdClose()
        osuCMD.cmdAbort()
        osuCMD.cmdInfo()
        osuCMD.cmdRoomInfo()
        osuCMD.cmdAddModerator()
        osuCMD.cmdRef()
        osuCMD.cmdDiff()
        osuCMD.cmdQueue()
        osuCMD.cmdDelQueue()
        osuCMD.cmdReady()
        osuCMD.cmdSkip()
        osuCMD.cmdAdd()
        osuCMD.cmdTimeMods()
        osuCMD.cmdForce()
    def cmdClose():
        if (osuCMD.chat[0] == ":!cya"):
            for item in osuCMD.roomList:
                if item.id == osuCMD.channel:
                    if (item.creator==osuCMD.issuer) or (osuCMD.issuer in item.moderator):
                        item.close()
                        osuCMD.roomList.remove(item)
    def cmdAbort():
        if(osuCMD.chat[0]==':!a') or (osuCMD.chat[0]==':!abort'):
            for item in osuCMD.roomList:
                if item.id == osuCMD.channel:
                    if (osuCMD.issuer==item.creator) or (osuCMD.issuer in item.moderator):
                        osuIRC.sendto(osuCMD.channel,"!mp abort")
    def cmdInfo():
        if (osuCMD.chat[0]==':!i') or (osuCMD.chat[0]==':!info'):
            if osuCMD.channel!=osuIRC.UID:
                osuIRC.sendto(osuCMD.channel,"Autohost under developement. Made by [http://github.com/kron3 kron3], See all available command [https://github.com/kron3/osu-autohost/wiki/OSU-Autohost-Wiki here].")
            else:
                osuIRC.sendto(osuCMD.issuer,"Autohost under developement. Made by [http://github.com/kron3 kron3], See all available command [https://github.com/kron3/osu-autohost/wiki/OSU-Autohost-Wiki here].")
    def cmdRoomInfo():
        if (osuCMD.chat[0]==':!rm') or (osuCMD.chat[0]==':!room'):
            for item in osuCMD.roomList:
                if item.id == osuCMD.channel:
                    osuIRC.sendto(osuCMD.channel,"Mode: %s  |  Star Filter: %s-%s★  |  Room Creator: %s  |  Room Moderator: %s" %(item.mode.upper(),item.difficultyrating[0],item.difficultyrating[1],item.creator,'-' if(item.moderator==[]) else ", ".join(item.moderator)))
    def cmdAddModerator():
        if (osuCMD.chat[0]==':!m') or (osuCMD.chat[0]==':!momod'):
            for item in osuCMD.roomList:
                if item.id == osuCMD.channel:
                    if osuCMD.issuer == item.creator:
                        try:
                            momod = '_'.join(osuCMD.chat[1:])
                            if momod in item.playerList:
                                if momod in item.moderator:
                                    osuIRC.sendto(osuCMD.channel,"%s is a moderator!" %momod)
                                else:
                                    item.moderator.append(momod)
                                    osuIRC.sendto(osuCMD.channel,"%s added as room moderator" %momod)
                            else:
                                osuIRC.sendto(osuCMD.channel,"%s not exist in this room !  please recheck the name." %momod)
                        except:
                            osuIRC.sendto(osuCMD.channel,"CatchExeption : failed to add moderator, command example !momod name")
                    else:
                        osuIRC.sendto(osuCMD.channel,"this command only available to room creator")
    def cmdRef():
        if(osuCMD.chat[0]==':!ref' or osuCMD.chat[0]==':!f'):
            for item in osuCMD.roomList:
                if item.id == osuCMD.channel:
                    if (item.creator==osuCMD.issuer) or (osuCMD.issuer in item.moderator):
                        try:
                            addRef = '_'.join(osuCMD.chat[1:])
                            if addRef in item.playerList:
                                osuIRC.sendto(osuCMD.channel,"!mp addref %s" %addRef)
                            else:
                                osuIRC.sendto(osuCMD.channel,"%s not exist in this room !  please recheck the name." %addRef)
                        except:
                            osuIRC.sendto(osuCMD.channel,"CatchExeption : failed to add refree, command example: !ref name")
                    else:
                        osuIRC.sendto(osuCMD.channel,"this command only available to room creator and moderator")
    def cmdDiff():
        if(osuCMD.chat[0]==':!diff') or (osuCMD.chat[0]==':!d'):
            for item in osuCMD.roomList:
                if item.id == osuCMD.channel:
                    if (item.creator==osuCMD.issuer) or (osuCMD.issuer in item.moderator):
                        try:
                            diff = '-'.join(osuCMD.chat[1:]).replace(',','.')
                            d = diff.split('-')
                            if len(d)!=2:
                                raise ValueError()
                            if float(d[0])>float(d[1]):
                                d = d[::-1]
                            d[0] = str(round(float(d[0]),2))
                            d[1] = str(round(float(d[1]),2))
                            if((float(d[0])>10) or (float(d[0])<0)) and ((float(d[1])>10) or (float(d[1])<0)):
                                raise ValueError()
                            else:
                                osuIRC.sendto(osuCMD.channel,"set difficulty :  %s - %s ★"%(d[0],d[1]))
                                item.difficultyrating[0] = d[0]
                                item.difficultyrating[1] = d[1]
                                map = item.nowPlaying.hasDiff(d)
                                if map != None:
                                    osuIRC.sendto(osuCMD.channel,"!mp map %s" %map)
                                    #item.nowPlaying.sendPP(map,item.id)
                                    _thread.start_new_thread(item.nowPlaying.getPP,(map,item.id))
                                else:
                                    osuIRC.sendto(osuCMD.channel,'%s not have  %s - %s ★  difficulty.'%(item.nowPlaying.mergeName,item.difficultyrating[0],item.difficultyrating[1]))
                        except ValueError:
                            osuIRC.sendto(osuCMD.channel,"ValueError : it must be number greater than 0 and less than 10, command example: !diff 4.32-5")
                    else:
                        osuIRC.sendto(osuCMD.channel,"this command only available to room creator and moderator")
    def cmdQueue():
        showlist = []
        if(osuCMD.chat[0]==':!q') or (osuCMD.chat[0]==':!queue'):
            for item in osuCMD.roomList:
                if item.id == osuCMD.channel:
                    if item.map_list != []:
                        for map in item.map_list:
                            if (map.set_id!='') and (map.mergeName!=''):
                                showlist.append(map.mergeName)
                        osuIRC.sendto(osuCMD.channel,"Queue: "+str(len(showlist))+"  ||  "+"  ||  ".join(showlist))
                    else:
                        osuIRC.sendto(osuCMD.channel,"Empty Queue (ó﹏ò｡)  ... Add mode queue with '!add [beatmap_link]'")
    def cmdDelQueue():
        if(osuCMD.chat[0]==':!dq') or (osuCMD.chat[0]==':!delqueue'):
            for item in osuCMD.roomList:
                if item.id == osuCMD.channel:
                    if(item.creator==osuCMD.issuer) or (osuCMD.issuer in item.moderator):
                        del item.map_list[:]
                        osuIRC.sendto(osuCMD.channel,"Queue cleaned!")
    def cmdReady():
        if(osuCMD.chat[0]==':!r') or (osuCMD.chat[0]==':!ready'):
            for item in osuCMD.roomList:
                if item.id == osuCMD.channel:
                    if osuCMD.issuer not in item.vote_ready:
                        item.vote_ready.append(osuCMD.issuer)
                        # count minimal start
                        min = int(len(item.playerList)*0.7)
                        min = 1 if min<1 else min
                        # #
                        osuIRC.sendto(osuCMD.channel,"%s vote for start (%s/%s)"%(osuCMD.issuer,len(item.vote_ready),min))
                        if len(item.vote_ready) >= min:
                            item.begin()
                    else:
                        try:
                            item.vote_ready.remove(osuCMD.issuer)
                        except:
                            pass
                        # count minimal start
                        min = int(len(item.playerList)*0.7)
                        min = 1 if min<1 else min
                        # #
                        osuIRC.sendto(osuCMD.channel,"%s un-vote start (%s/%s)"%(osuCMD.issuer,len(item.vote_ready),min))
                        if len(item.vote_ready) >= min:
                            item.begin()
    def cmdSkip():
        if(osuCMD.chat[0]==':!s') or (osuCMD.chat[0]==':!skip'):
            for item in osuCMD.roomList:
                if item.id == osuCMD.channel:
                    if osuCMD.issuer not in item.vote_skip:
                        item.vote_skip.append(osuCMD.issuer)
                        # count minimal start
                        min = int(len(item.playerList)*0.6)
                        min = 1 if min<1 else min
                        # #
                        osuIRC.sendto(osuCMD.channel,"%s vote for skip (%s/%s)"%(osuCMD.issuer,len(item.vote_skip),min))
                        if len(item.vote_skip) >= min:
                            item.next()
                    else:
                        try:
                            item.vote_skip.remove(osuCMD.issuer)
                        except:
                            pass
                        # count minimal start
                        min = int(len(item.playerList)*0.7)
                        min = 1 if min<1 else min
                        # #
                        osuIRC.sendto(osuCMD.channel,"%s un-vote start (%s/%s)"%(osuCMD.issuer,len(item.vote_skip),min))
                        if len(item.vote_skip) >= min:
                            item.next()
    def cmdAdd():
        if(osuCMD.chat[0]==':+') or (osuCMD.chat[0]==':!add'):
            for item in osuCMD.roomList:
                if item.id == osuCMD.channel:
                    if(len(osuCMD.chat)>=2):
                        getmap = None
                        getset = None
                        DTHT = None
                        if len(osuCMD.chat)==3:
                            DTHT = 'dt' if osuCMD.chat[2]=='dt' else 'ht' if osuCMD.chat[2]=='ht' else None
                        if('osu.ppy.sh/b/' in osuCMD.chat[1]):
                            getmap = osuCMD.chat[1].replace("https://","").replace("http://","").replace("osu.ppy.sh/b/","")
                            getmap = getmap.split("&")
                            getmap = getmap[0]
                            getmap = getmap.split("?")
                            getmap = getmap[0]
                        elif('osu.ppy.sh/s/' in osuCMD.chat[1]):
                            getset = osuCMD.chat[1].replace("https://","").replace("http://","").replace("osu.ppy.sh/s/","")
                        elif('/beatmapsets/' in osuCMD.chat[1]):
                            getmap = osuCMD.chat[1].replace("https://","").replace("http://","")
                            getmap = getmap.split("/")
                            getmap = getmap[len(getmap)-1]
                            if "#" in getmap:
                                getset = getmap.split("#")
                                getset = getmap[0]
                                getmap = None

                        print(item.id,str(getset),str(getmap))

                        exist = False
                        if getset != None:
                            item.map_list.append(osuBeatSet(set=getset,DTHT=DTHT))
                            for check in item.map_list[:-1]:
                                if item.map_list[-1].set_id==check.set_id :
                                    a = item.map_list.pop()
                                    osuIRC.sendto(item.id,"%s already exist in queue" %a.mergeName)
                                    exist = True
                            if not exist:
                                osuIRC.sendto(item.id,"%s added to queue (%s)" %(item.map_list[-1].mergeName,len(item.map_list)))
                        elif getmap != None:
                            item.map_list.append(osuBeatSet(map=getmap,DTHT=DTHT))
                            for check in item.map_list[:-1]:
                                if getmap in check.map_list.keys():
                                    a = item.map_list.pop()
                                    osuIRC.sendto(item.id,"%s already exist in queue" %a.mergeName)
                                    exist = True
                            if not exist:
                                osuIRC.sendto(item.id,"%s added to queue (%s)" %(item.map_list[-1].mergeName,len(item.map_list)))
                        else:
                            osuIRC.sendto(item.id,'ERROR : wrong !add command.  example:  !add https://osu.ppy.sh/s/320118')
                    else:
                        osuIRC.sendto(item.id,'ERROR : wrong !add command.  example:  !add https://osu.ppy.sh/s/320118')
    def cmdTimeMods():
        if (osuCMD.chat[0]==':!tm') or (osuCMD.chat[0]==':!timemods'):
            if len(osuCMD.chat) == 2:
                for item in osuCMD.roomList:
                    if item.id == osuCMD.channel:
                        if (item.creator==osuCMD.issuer) or (osuCMD.issuer in item.moderator):
                            if osuCMD.chat[1] in ['none','dt','ht']:
                                if osuCMD.chat[1] == 'none':
                                    osuIRC.sendto(item.id,'!mp mods freemod')
                                    item.nowPlaying.DTHT=None
                                    _thread.start_new_thread(item.nowPlaying.getPP,(item.nowPlayingMap,item.id))
                                else:
                                    osuIRC.sendto(item.id,'!mp mods %s freemod'%osuCMD.chat[1])
                                    item.nowPlaying.DTHT=osuCMD.chat[1]
                                    _thread.start_new_thread(item.nowPlaying.getPP,(item.nowPlayingMap,item.id))
                            else:
                                osuIRC.sendto(item.id,"timemods available : None, DT, HT. example:  !timemods None  or:  !tm None")
                        else:
                            osuIRC.sendto(osuCMD.channel,"this command only available to room creator and moderator")
    def cmdForce():
        if (osuCMD.chat[0]==':!force'):
            for item in osuCMD.roomList:
                if item.id == osuCMD.channel:
                    if (item.creator==osuCMD.issuer) or (osuCMD.issuer in item.moderator):
                        if len(osuCMD.chat)==2:
                            if osuCMD.chat[1] == 'start':
                                osuIRC.sendto(item.id,'!mp start 5')
                            elif osuCMD.chat[1] == 'skip':
                                osuIRC.sendto(item.id,'force skipped by %s'%osuCMD.issuer)
                                item.next()
                            elif osuCMD.chat[1] == 'abort':
                                osuIRC.sendto(item.id,'!mp abort')
                            else:
                                osuIRC.sendto(item.id,'force command only have 3 available argumet:  !force start  |  !force skip  |  !force abort')
                        else:
                            osuIRC.sendto(item.id,'force command only have 3 available argumet:  !force start  |  !force skip  |  !force abort')
                    else:
                        osuIRC.sendto(item.id,'force command only available to room creator or moderator')



class osuAPI:
    MODE = {'std':'0','taiko':'1','ctb':'2','mania':'3'}
    MODEinv = ['std','taiko','ctb','mania']
    MODS = {'NoMod':'0','HD':'8','HR':'16','HDHR':'24'}
    playlist = []

    def dateNow():
        return time.localtime(time.time())

    def songAPI(since='',set='',map='',mode=''):
        since = '&since='+str(since) if since!='' else ''
        set = '&s='+str(set) if set!='' else ''
        map = '&b='+str(map) if map!='' else ''
        mode = '&m='+str(mode) if mode!='' else ''
        print("[GET] https://osu.ppy.sh/api/get_beatmaps?k=%s%s%s%s%s" %(KEY,since,set,map,mode))
        return requests.get("https://osu.ppy.sh/api/get_beatmaps?k=%s%s%s%s%s" %(KEY,since,set,map,mode)).json()

    def scoreAPI(map='',mods='',DTHT=''):
        if DTHT == 'DT':
            mods = int(osuAPI.MODS[mods])+64
            mods = str(mods)
        elif DTHT == 'HT':
            mods = int(osuAPI.MODS[mods])+256
            mods = str(mods)
        else:
            mods = osuAPI.MODS[mods]
        map = '&b='+str(map) if map!='' else ''
        mods = '&mods='+str(mods) if mods!='' else ''
        print("[GET] https://osu.ppy.sh/api/get_scores?k=%s%s%s&limit=20" %(KEY,map,mods))
        return requests.get("https://osu.ppy.sh/api/get_scores?k=%s%s%s&limit=20" %(KEY,map,mods)).json()

    def setRand(playMode='std',last=None):
        if last == None:
            temp = osuAPI.dateNow()
            date = (temp[0],temp[1],1)
        else:
            if last[1] > 1:
                date = (last[0],last[1]-1,1)
            else:
                if last[0] > 2014:
                    date = (last[0]-1,12,1)
                else:
                    temp = osuAPI.dateNow()
                    date = (temp[0],temp[1],1)
        data = osuAPI.songAPI(since='%d-%d-%d' %date, mode=osuAPI.MODE[playMode])
        setid=''
        pack=[]
        for song in data:
            if setid != song['beatmapset_id']:
                setid = song['beatmapset_id']
                pack.append(setid)
        return (date,pack)

    def mapFromSet(set,diff):
        print('[GET] MapFromSet')
        data = osuAPI.songAPI(set=set,mode='')
        for song in data:
            if(float(song['difficultyrating'])>=float(diff[0]) and float(song['difficultyrating'])<=float(diff[1])):
                return song['beatmap_id']

    def getMaxPP(map_id):
        mod_list = {'FC':'0','HD':'8','HR':'16','HRHD':'24'}
        PP = {}
        for name,mod in mod_list.items():
            print("GET: https://osu.ppy.sh/api/get_scores?k=%s&b=%s&mods=%s&limit=1" %(osuAPI.KEY,map_id,mod))
            data = requests.get("https://osu.ppy.sh/api/get_scores?k=%s&b=%s&mods=%s&limit=1" %(osuAPI.KEY,map_id,mod)).json()
            PP[name] = 'No'
            for map in data:
                PP[name] = map['pp']
        return PP

class Watchdog():
    def __init__(self, timeout, userHandler=None):  # timeout in seconds
        self.timeout = timeout
        self.handler = userHandler if userHandler is not None else self.defaultHandler
        self.timer = Timer(self.timeout, self.handler)
        self.timer.start()

    def reset(self):
        self.timer.cancel()
        self.timer = Timer(self.timeout, self.handler)
        self.timer.start()

    def stop(self):
        self.timer.cancel()

    def defaultHandler(self):
        raise RuntimeError

if __name__ == '__main__':
    osuIRC.begin()
