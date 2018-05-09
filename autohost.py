import sys,socket,string,os,time,random,json,_thread
try:
    import requests
except ImportError:
    print('need requests dependency\ninstalling...')
    os.system('pip install requests')
    import requests

class osuIRC:
    '''osu IRC class, dipakai untuk connect ke server irc, terima dan kirim data.'''
    host = "irc.ppy.sh"
    port = 6667
    UID = "Iam2Awesome".lower()
    KEY = "f0afe733".lower()

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

    def recv(size=4096):
        '''menerima dari IRC, convert ke lower caps, decode utf-8 menjadi string'''
        return osuIRC.IRC.recv(size).decode().lower()

    def show(file):
        '''cetak jika bukan baris kosong, notifikasi join atau notifikasi quit'''
        osuIRC.kata = file.split(" ")
        if len(osuIRC.kata)>2 :
            if osuIRC.kata[1] != ("quit" or "join"):
                print(file)

    def DC():
        '''case disconnected'''
        osuIRC.IRC.shutdown(socket.SHUT_RDWR)
        osuIRC.IRC.close()
        osuIRC.connect()
        for room in osuCMD.roomList:
            osuIRC.send("JOIN %s" %room.id)


class osuRoom:
    def __init__(self,maker,name="",id=""):
        self.maker = maker
        self.nowBM = '0'
        self.player = []
        self.start = []
        self.skip = []
        self.queue = []
        self.lastRand = None
        self.setRand = []
        self.roomNumber = 0
        self.difficulty = ['3','4']
        if(name=="" and id!=""):
            self.id = id
            self.getPlayerList = True
            self.name = "INVITED ROOM "+str(time.time())
            _thread.start_new_thread(self.getPlayer,())
            print('thread started succesfully')
        elif(name!="" and id==""):
            self.name = name
            self.getID = True
            self.getNumber = True
            osuIRC.send("PRIVMSG banchobot !mp make %s | !info" %self.name)
            _thread.start_new_thread(self.getRoomID,())
            _thread.start_new_thread(self.getRoomNumber,())
            print('thread started succesfully')
        _thread.start_new_thread(self.watchdog,())

    def watchdog(self):
        time.sleep(120)
        if self.player == []:
            self.close()
            print('watchdog bite')
        else:
            self.watchdog()

    def getPlayer(self):
        print('getting player...')
        now = time.time()
        begin = now
        while(self.getPlayerList and now-begin<20):
            if len(osuIRC.kata) > 2:
                if(osuIRC.kata[1] == "353" and osuIRC.kata[5] == ":@banchobot"):
                    player = osuIRC.kata[6:]
                    try:
                        player.remove("+"+osuIRC.UID)
                        player.remove("\r")
                    except:
                        print('cannot remove autohost id from player')
                    self.player.extend(player)
                    self.getPlayerList = False
                    osuIRC.send("PRIVMSG "+self.maker+" Joined the room")
                    print(self.player)

    def getRoomNumber(self):
        print('getting room number...')
        now = time.time()
        begin = now
        while(self.getID and self.getNumber and now-begin<20):
            if len(osuIRC.kata) > 2:
                if osuIRC.kata[1] == "332":
                    self.number = osuIRC.kata[len(osuIRC.kata)-1].replace("#","")
                    osuIRC.send("PRIVMSG "+self.maker+" room created [osump://%s/ JOIN HERE]" %self.number)
                    self.getNumber = False
            now = time.time()
        if now-begin > 20:
            print('cannot obtain number')

    def getRoomID(self):
        print('getting room id...')
        now = time.time()
        begin = now
        while(self.getID and self.getNumber and now-begin<20):
            if len(osuIRC.kata) > 2:
                if osuIRC.kata[1] == "mode":
                    self.id = osuIRC.kata[2]
                    osuIRC.send("PRIVMSG "+self.id+" !mp password")
                    osuIRC.send("PRIVMSG "+self.id+" !mp set 0 0 16")
                    osuIRC.send("PRIVMSG "+self.id+" !mp mods freemod")
                    self.getID = False
                    self.next()
            now = time.time()
        if now-begin > 20:
            print('cannot obtain id')

    def close(self):
        osuIRC.send("PRIVMSG "+self.id+" !mp close")

    def begin(self,time=5):
        osuIRC.send("PRIVMSG "+self.id+" !mp start %s" %str(time))
        self.start = []
        self.skip = []

    def change(self,mapID):
        osuIRC.send("PRIVMSG "+self.id+" !mp map %s" %str(mapID))

    def next(self):
        print("\ngetting next song\n")
        if len(self.queue) != 0:
            print('get from queue')
            self.nowBM = self.queue.pop(0)
            PP = osuAPI.getMaxPP(self.nowBM)
            mods = ['FC','HD','HR','HRHD']
            for mod in mods:
                if PP[mod] == 'None':
                    PP[mod] == '0'
            self.change(self.nowBM)
            osuIRC.send("PRIVMSG "+self.id+" "+osuAPI.songName(self.nowBM)+" ||   FC: %s pp   HD: %s pp   HR: %s pp   HRHD: %s pp" %(PP['FC'],PP['HD'],PP['HR'],PP['HRHD']))
            self.start = []
            self.skip = []
        else:
            print("get random")
            if self.setRand == []:
                print('empty set random')
                self.lastRand,self.setRand = osuAPI.setRand(self.lastRand)
            getmap = osuAPI.mapFromSet(self.setRand.pop(0),self.difficulty)
            print(getmap)
            if getmap != None:
                osuIRC.send("PRIVMSG "+self.id+" no more queueing map, please add with !add <beatmaplink>. i'll choose random for now.")
                self.nowBM = getmap
                PP = osuAPI.getMaxPP(self.nowBM)
                mods = ['FC','HD','HR','HRHD']
                for mod in mods:
                    if PP[mod] == 'None':
                        PP[mod] == '0'
                self.change(self.nowBM)
                osuIRC.send("PRIVMSG "+self.id+" "+osuAPI.songName(self.nowBM)+" ||   FC: %s pp   HD: %s pp   HR: %s pp   HRHD: %s pp" %(PP['FC'],PP['HD'],PP['HR'],PP['HRHD']))
                self.start = []
                self.skip = []
            else:
                self.next()

    def join(self,name):
        self.player.append(name)
        print(self.name,self.player)

    def quit(self,name):
        try:
            self.player.remove(name)
        except:
            print('cannot find that player')
        print(self.name,self.player)

class osuCMD:
    roomList = []
    last_makename = ''

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
            roomname = ' '.join(osuCMD.chat[1:])
            if roomname != osuCMD.last_makename:
                osuCMD.roomList.append(osuRoom(name=roomname,maker=osuCMD.issuer))
                osuCMD.last_makename = roomname
            else:
                print('double detected')

    def getInvite():
        if(osuCMD.channel == osuIRC.UID and osuCMD.chat[0] == ":!invite"):
            roomid = osuCMD.chat[1]
            isduplicate = False
            for item in osuCMD.roomList:
                if item.id == roomid:
                    isduplicate = True
            if isduplicate == False:
                osuCMD.roomList.append(osuRoom(id=roomid,maker=osuCMD.issuer))
                osuIRC.send("JOIN "+roomid)
            else:
                osuIRC.send("PRIVMSG "+osuCMD.issuer+" "+roomid+" already registered in our database!")


    def getClose():
        if (osuCMD.chat[0] == ":!cya"):
            for item in osuCMD.roomList:
                if item.maker == osuCMD.issuer:
                    if item.id == osuCMD.channel:
                        item.close()
                        osuCMD.roomList.remove(item)

    def getJoin():
        if osuIRC.baris.find("joined in slot") != -1:
            if osuCMD.issuer == 'banchobot':
                lenlist = len(osuIRC.kata)-4
                name = '_'.join(osuIRC.kata[3:lenlist])
                name = name.replace(':','')
                for item in osuCMD.roomList:
                    if item.id == osuCMD.channel:
                        item.join(name)

    def getQuit():
        if osuIRC.baris.find("left the game") != -1:
            if osuCMD.issuer == 'banchobot':
                lenlist = len(osuIRC.kata)-3
                name = '_'.join(osuIRC.kata[3:lenlist])
                name = name.replace(':','')
                for item in osuCMD.roomList:
                    if item.id == osuCMD.channel:
                        item.quit(name)

    def getGameStart():
        if osuIRC.baris.find(":the match has started!") != -1:
            if osuCMD.issuer == 'banchobot':
                for item in osuCMD.roomList:
                    if item.id == osuCMD.channel:
                        item.start = []
                        item.skip = []

    def getGameFinish():
        if osuIRC.baris.find(":the match has finished!") != -1 or osuIRC.baris.find(":aborted the match") != -1:
            if osuCMD.issuer == 'banchobot':
                for item in osuCMD.roomList:
                    if item.id == osuCMD.channel:
                        item.start = []
                        item.skip = []
                        item.next()

    def getAllReady():
        if osuIRC.baris.find(":all players are ready") != -1:
            if osuCMD.issuer == 'banchobot':
                for item in osuCMD.roomList:
                    if item.id == osuCMD.channel:
                        item.begin()

    def cmdQueue():
        showlist = []
        if(osuCMD.chat[0] == ':!q' or osuCMD.chat[0] == ':!queue'):
            for item in osuCMD.roomList:
                if item.id == osuCMD.channel:
                    if item.queue != []:
                        for que in item.queue:
                            name = osuAPI.songName(map=que)
                            if name != None:
                                showlist.append(name)
                        osuIRC.send("PRIVMSG "+item.id+" Queue:"+str(len(showlist))+"  ||  "+'  ||  '.join(showlist))
                    else:
                        osuIRC.send("PRIVMSG "+item.id+" Empty Queue :(")

    def cmdDiff():
        if(osuCMD.chat[0] == ':!diff' or osuCMD.chat[0] == ':!d'):
            for item in osuCMD.roomList:
                if item.id == osuCMD.channel:
                    if len(osuCMD.chat) == 3:
                        try:
                            if float(osuCMD.chat[1]) < float(osuCMD.chat[2]):
                                item.difficulty = [osuCMD.chat[1],osuCMD.chat[2]]
                                osuIRC.send("PRIVMSG "+item.id+" Set difficulty from "+item.difficulty[0]+"★ to "+item.difficulty[1]+"★.")
                            elif float(osuCMD.chat[1]) > float(osuCMD.chat[2]):
                                item.difficulty = [osuCMD.chat[2],osuCMD.chat[1]]
                            else:
                                osuIRC.send("PRIVMSG "+item.id+" wrong command. example: !diff 4.5 5.2")
                        except:
                            osuIRC.send("PRIVMSG "+item.id+" wrong command. example: !diff 4.5 5.2")
                    else:
                        osuIRC.send("PRIVMSG "+item.id+" wrong command. example: !diff 4.5 5.2")

    def cmdInfo():
        if(osuCMD.chat[0] == ':!i' or osuCMD.chat[0] == ':!info'):
            osuIRC.send("PRIVMSG "+osuCMD.channel+" Autohost under developement. Made by [http://github.com/kron3 kron3], See all available command [https://github.com/kron3/osu-autohost/wiki/OSU-Autohost-Wiki here].")

    def cmdReady():
        if(osuCMD.chat[0] == ':!r' or osuCMD.chat[0] == ':!ready'):
            for item in osuCMD.roomList:
                if item.id == osuCMD.channel:
                    if osuCMD.issuer not in item.start:
                        item.start.append(osuCMD.issuer)
                        minimalstart = int(len(item.player)*0.7)
                        if minimalstart<1:
                            minimalstart = 1
                        osuIRC.send("PRIVMSG "+item.id+" "+osuCMD.issuer+" vote for start ("+str(len(item.start))+"/"+str(minimalstart)+")")
                        if len(item.start) >= minimalstart:
                            item.begin()
                    else:
                        osuIRC.send("PRIVMSG "+osuCMD.issuer+" You already vote for start ...")

    def cmdRef():
        if(osuCMD.chat[0] == ':!ref' or osuCMD.chat[0] == ':!f'):
            for item in osuCMD.roomList:
                if item.id == osuCMD.channel:
                    if osuCMD.issuer == item.maker:
                        if(len(osuCMD.chat)>1):
                            people = " ".join(osuCMD.chat[1:])
                            if people in item.player:
                                osuIRC.send("PRIVMSG "+item.id+" !mp addref "+people)
                            else:
                                osuIRC.send("PRIVMSG "+item.id+" "+people+" not exist in this room!")
                        else:
                            osuIRC.send("PRIVMSG "+item.id+" !mp addref "+osuCMD.issuer)
                    else:
                        osuIRC.send("PRIVMSG "+item.id+" this command only available to room creator ("+item.maker+"). Ask "+item.maker+" to add you as !ref or make your own room like this by PM me: !make <room_name>")

    def cmdSkip():
        if(osuCMD.chat[0] == ':!s' or osuCMD.chat[0] == ':!skip'):
            for item in osuCMD.roomList:
                if item.id == osuCMD.channel:
                    if osuCMD.issuer not in item.skip:
                        item.skip.append(osuCMD.issuer)
                        minimalskip = int(len(item.player)*0.7)
                        if minimalskip<1:
                            minimalskip = 1
                        osuIRC.send("PRIVMSG "+item.id+" "+osuCMD.issuer+" vote for skip ("+str(len(item.skip))+"/"+str(minimalskip)+")")
                        if len(item.skip) >= minimalskip:
                            item.next()
                    else:
                        osuIRC.send("PRIVMSG "+osuCMD.issuer+" You already vote for skip ...")

    def cmdAdd():
        if(osuCMD.chat[0] == ':+' or osuCMD.chat[0] == ':!add'):
            for item in osuCMD.roomList:
                if item.id == osuCMD.channel:
                    if(len(osuCMD.chat) == 2):
                        if('osu.ppy.sh/b/' in osuCMD.chat[1]):
                            getmap = osuCMD.chat[1].replace("https://","").replace("http://","").replace("osu.ppy.sh/b/","")
                            getmap = getmap.split("&")
                            getmap = getmap[0]
                            getmap = getmap.split("?")
                            getmap = getmap[0]
                            judul = osuAPI.songName(map=getmap)
                            inRange,inRangeSet = osuAPI.diffInRange(map=getmap,diff=item.difficulty)
                            if inRange == False:
                                osuIRC.send("PRIVMSG "+item.id+" added beatmap not in difficulty range! i'll choose one with difficulty in range.")
                                getmap = osuAPI.mapFromSet(set=inRangeSet,diff=item.difficulty)
                            if getmap not in item.queue:
                                item.queue.append(getmap)
                                osuIRC.send("PRIVMSG "+item.id+" "+judul+" added to queue ("+str(len(item.queue))+")")
                                if item.nowBM == '0':
                                    item.next()
                            else:
                                osuIRC.send("PRIVMSG "+item.id+" "+judul+" already exist in queue!")
                        elif('osu.ppy.sh/s/' in osuCMD.chat[1]):
                            getset = osuCMD.chat[1].replace("https://","").replace("http://","").replace("osu.ppy.sh/s/","")
                            getmap = osuAPI.mapFromSet(set=getset,diff=item.difficulty)
                            if getmap != None:
                                judul = osuAPI.songName(map=getmap)
                                if getmap not in item.queue:
                                    item.queue.append(getmap)
                                    osuIRC.send("PRIVMSG "+item.id+" You input a beatmap set. i'll choose the beatmap for you ...")
                                    osuIRC.send("PRIVMSG "+item.id+" "+judul+" added to queue ("+str(len(item.queue))+")")
                                    if item.nowBM == '0':
                                        item.next()
                                else:
                                    osuIRC.send("PRIVMSG "+item.id+" "+judul+" already exist in queue!")
                            else:
                                osuIRC.send("PRIVMSG "+item.id+" that beatmap list not have standarized difficulty! make sure it have "+item.difficulty[0]+"-"+item.difficulty[1]+"★ difficulty.")
                        elif '/beatmapsets/' in osuCMD.chat[1]:
                            getmap = osuCMD.chat[1].replace("https://","").replace("http://","")
                            getmap = getmap.split("/")
                            getmap = getmap[len(getmap)-1]
                            if "#" in getmap:
                                getmap = getmap.split("#")
                                getmap = getmap[0]
                                getmap = osuAPI.mapFromSet(set=getmap,diff=item.difficulty)
                                osuIRC.send("PRIVMSG "+item.id+"  You input a beatmap set. i'll choose the difficulty for you ...")
                            if getmap != None:
                                inRange,inRangeSet = osuAPI.diffInRange(map=getmap,diff=item.difficulty)
                                if inRange == False:
                                    osuIRC.send("PRIVMSG "+item.id+" added beatmap not in difficulty range! i'll choose one with difficulty in range.")
                                    getmap = osuAPI.mapFromSet(set=inRangeSet,diff=item.difficulty)
                                judul = osuAPI.songName(map=getmap)
                                if getmap not in item.queue:
                                    item.queue.append(getmap)
                                    osuIRC.send("PRIVMSG "+item.id+" "+judul+" added to queue ("+str(len(item.queue))+")")
                                    if item.nowBM == '0':
                                        item.next()
                                else:
                                    osuIRC.send("PRIVMSG "+item.id+" "+judul+" already exist in queue!")
                            else:
                                osuIRC.send("PRIVMSG "+item.id+" that beatmap list not have standarized difficulty! make sure it have "+item.difficulty[0]+"-"+item.difficulty[1]+"★ difficulty.")
                        else:
                            osuIRC.send("PRIVMSG "+item.id+" wrong or unsupported beatmap link.")
                    else:
                        osuIRC.send("PRIVMSG "+item.id+" wrong or unsupported beatmap link.")


class osuAPI:
    KEY = "ad8c161908bcf5bf8f595300537edbbecb7fc17b"
    playlist = []

    def dateNow():
        return time.localtime(time.time())

    def songAPI(since='',set='',map='',mode=0):
        since = '&since='+str(since) if since!='' else ''
        set = '&s='+str(set) if set!='' else ''
        map = '&b='+str(map) if map!='' else ''
        mode = '&m='+str(mode) if mode!='' else ''
        print("https://osu.ppy.sh/api/get_beatmaps?k=%s%s%s%s%s" %(osuAPI.KEY,since,set,map,mode))
        return requests.get("https://osu.ppy.sh/api/get_beatmaps?k=%s%s%s%s%s" %(osuAPI.KEY,since,set,map,mode)).json()

    def setRand(last=None):
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
        data = osuAPI.songAPI(since='%d-%d-%d' %date)
        setid=''
        pack=[]
        for song in data:
            if setid != song['beatmapset_id']:
                setid = song['beatmapset_id']
                pack.append(setid)
        return (date,pack)

    def songName(map='',set=''):
        if(map=='' and set==''):
            raise Exception('need to define at least map or set!')
        else:
            data = osuAPI.songAPI(map=map,set=set,mode='')
            for song in data:
                return "[%s %s - %s (%.2f★)]" %("https://osu.ppy.sh/b/"+map,song['artist'],song['title'],float(song['difficultyrating']))

    def mapFromSet(set,diff):
        data = osuAPI.songAPI(set=set,mode='')
        for song in data:
            if(float(song['difficultyrating'])>=float(diff[0]) and float(song['difficultyrating'])<=float(diff[1])):
                return song['beatmap_id']

    def diffInRange(map,diff):
        data = osuAPI.songAPI(map=map)
        for song in data:
            if(float(song['difficultyrating'])>float(diff[0]) and float(song['difficultyrating'])<float(diff[1])):
                return True,song['beatmapset_id']
            else:
                return False,song['beatmapset_id']

    def getMaxPP(map_id):
        mod_list = {'FC':'0','HD':'8','HR':'16','HRHD':'24'}
        PP = {}
        for name,mod in mod_list.items():
            print("GET: https://osu.ppy.sh/api/get_scores?k=%s&b=%s&mods=%s&limit=1" %(osuAPI.KEY,map_id,mod))
            data = requests.get("https://osu.ppy.sh/api/get_scores?k=%s&b=%s&mods=%s&limit=1" %(osuAPI.KEY,map_id,mod)).json()
            PP[name] = '0'
            for map in data:
                PP[name] = map['pp']
        return PP


def main():
    connect = osuIRC.connect()
    print('connect ok')
    if connect == False:
        print(connect)
        quit()
    while 1:
        raw = osuIRC.recv()
        if raw.find('ping cho.ppy.sh') != -1:
            osuIRC.send('PONG')
            print('PONG')
        data = raw.split("\n")
        if len(data)-1 == 0:
            osuIRC.DC()
        for osuIRC.baris in data:
            osuIRC.kata = osuIRC.baris.split(" ")
            osuIRC.show(osuIRC.baris)
            osuCMD.getBasic()
            if osuCMD.chat != None:
                osuCMD.getMake()
                osuCMD.getInvite()
                osuCMD.getClose()
                osuCMD.getJoin()
                osuCMD.getQuit()
                osuCMD.getGameStart()
                osuCMD.getGameFinish()
                osuCMD.getAllReady()
                osuCMD.cmdQueue()
                osuCMD.cmdDiff()
                osuCMD.cmdInfo()
                osuCMD.cmdReady()
                osuCMD.cmdSkip()
                osuCMD.cmdAdd()
                osuCMD.cmdRef()
                osuCMD.issuer = None
                osuCMD.type = None
                osuCMD.channel = None
                osuCMD.chat = None
    time.sleep(2)

if __name__ == '__main__':
    main()
