import sys,socket,string,os,time,random,json
try:
    import requests
except ImportError:
    print('need requests dependency\ninstalling...')
    os.system('pip install requests')
    import requests

class osuRC:
    '''osu IRC class, dipakai untuk connect ke server irc, terima dan kirim data.'''
    host = "irc.ppy.sh"
    port = 6667
    realname = "Iam2Awesome"      #username
    password = "f0afe733"         #cari di osu.ppy.sh/p/irc
    realname = realname.lower()
    reconnect = 0           #case connection fail

    def conn():
        '''sambung ke server IRC osu!'''
        try:
            osuRC.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            osuRC.s.connect((osuRC.host, osuRC.port))
            osuRC.kirim("PASS %s" %osuRC.password)
            osuRC.kirim("NICK %s" %osuRC.realname)
            osuRC.kirim("USER %s %s bla :%s" % (osuRC.realname,osuRC.host,osuRC.realname))
            return True
        except:
            return False

    def kirim(x):
        '''mengirim ke IRC'''
        osuRC.s.send((x+"\r\n").encode())

    def terima(size=4096):
        '''menerima dari IRC, conver ke lower caps, decode utf-8 menjadi string'''
        return osuRC.s.recv(size).lower().decode()

    def cetak(file):
        '''cetak jika bukan baris kosong, notifikasi join atau notifikasi quit'''
        osuRC.kata = file.split(" ")
        if len(osuRC.kata) > 2:
            if osuRC.kata[1]!=("quit" or "join"):
                print(file)

    def disconnected():
        '''jancuk, disconnect :( ,,, oke kita sambungkan ulang....'''
        osuRC.s.shutdown(socket.SHUT_RDWR)
        osuRC.s.close()
        osuRC.conn()
        osuRC.kirim("JOIN "+osuHost.channel+"")
        osuRC.reconnect = 1

class osuHost:
    roomname = "random 4* - 5* ranked | !info"              #room name
    channel = "#indonesian"
    beatmap = 0             #beatmap going to !mp
    player = []             #people in room
    voterstart = []         #voter to start
    voterskip = []          #voter to skip\
    voterdiff = []          #voter to change difficulty
    mapqueue = []           #beatmap queue list

    def makeroom():
        ''' buat room '''
        osuRC.kirim("PRIVMSG banchobot !mp make "+osuHost.roomname+"")

    def getCreatedRoomID():
        ''' ambil id room yang dibuat '''
        if len(osuRC.kata) > 2:
            if osuRC.kata[0] == ":banchobot!cho@cho.ppy.sh" and osuRC.kata[1] == "mode":
                osuHost.channel = osuRC.kata[2]
                print(osuHost.channel)
                if osuRC.reconnect == 0:
                    osuRC.kirim("PRIVMSG "+osuHost.channel+" !mp password")
                    osuRC.kirim("PRIVMSG "+osuHost.channel+" !mp set 0 0 16")
                    osuRC.kirim("PRIVMSG "+osuHost.channel+" !mp mods freemod")

    def closeroom():
        ''' tutup room '''
        osuRC.kirim("PRIVMSG "+osuHost.channel+" !mp close")

    def startroom(time='5'):
        ''' mulai game'''
        osuRC.kirim("PRIVMSG "+osuHost.channel+" !mp start "+time+"")

    def changemap(mapID):
        ''' ganti beatmap '''
        osuRC.kirim("PRIVMSG "+osuHost.channel+" !mp map "+mapID+"")

    def nextmap():
        if len(osuHost.mapqueue) != 0:
            osuHost.beatmap = osuHost.mapqueue.pop(0)
            osuHost.changemap(osuHost.beatmap)
        else:
            if osuAPI.playlist == []:
#                osuAPI.getRand(diffb=osuAPI.diffb,difft=osuAPI.difft)
#            osuHost.beatmap = osuAPI.playlist.pop(0)
                osuAPI.getRand()
            mapsetpop = osuAPI.playlist.pop(0)
            mapsetsel = osuAPI.getmapbyset(set=mapsetpop,diffb=osuAPI.diffb,difft=osuAPI.difft)
            if mapsetsel != None:
                osuRC.kirim("PRIVMSG "+osuHost.channel+" no more queueing map, please add with !add <beatmaplink>. i'll choose random for now.")
                osuHost.beatmap = mapsetsel
                osuHost.changemap(osuHost.beatmap)
            else:
                print('diff not found')
                osuHost.nextmap()

    def getjoin():
        '''apakah ada yang join ke room?'''
        if osuRC.baris.find("joined in slot") != -1:
            lenlist = len(osuRC.kata)-4
            nama = '_'.join(osuRC.kata[3:lenlist])
            nama = nama.replace(':','')
            osuHost.player.append(nama)
            print(osuHost.player)

    def getquit():
        '''siapa yang keluar dibuang dari list'''
        if osuRC.baris.find("left the game.") != -1:
            lenlist = len(osuRC.kata)-3
            nama = '_'.join(osuRC.kata[3:lenlist])
            nama = nama.replace(':','')
            try:
                osuHost.player.remove(nama)
            except:
                pass
            print(osuHost.player)

    def isgamestart():
        '''cek apakah game sudah dimulai'''
        if osuRC.baris.find(":the match has started!") != -1:
            osuHost.voterstart = []
            osuHost.voterskip = []

    def isgamefinish():
        '''cek apakah game selesai?'''
        if osuRC.baris.find(":the match has finished!") != -1 or osuRC.baris.find(":aborted the match") != -1:
            osuHost.nextmap()

    def isclosed():
        '''cek apakah room ditutup pakai !mp closed?'''
        if osuRC.baris.find(":closed the match") != -1:
            osuHost.closeroom()
            quit()

    def isallready():
        '''apakah semua siap?'''
        if osuRC.baris.find(":all players are ready") != -1:
            osuHost.startroom()

    def getnama():
        nama = osuRC.kata[0].replace(':','')
        return nama.replace("!cho@ppy.sh","")

    def commandPing():
        if osuRC.kata[3] == ":!p" or osuRC.kata[3] == ":!hi":
            nama = osuHost.getnama()
            nama = nama.replace("_"," ")
            osuRC.kirim("PRIVMSG "+osuHost.channel+" hi "+nama+" -- automatic reply")

    def commandQueue():
        showlist = []
        if osuRC.kata[3] == ":!q" or osuRC.kata[3] == ":!queue" or osuRC.kata[3] == ":!list":
            if osuHost.mapqueue != []:
                for item in osuHost.mapqueue:
                    a = osuAPI.getName(item)
                    if a != None:
                        showlist.append(a)
                osuRC.kirim("PRIVMSG "+osuHost.channel+" Queue:"+str(len(showlist))+"  "+'  ||  '.join(showlist))
            else:
                osuRC.kirim("PRIVMSG "+osuHost.channel+" empty queue")

    def commandDiff():
        if osuRC.kata[3] == ":!d" or osuRC.kata[3] == ":!diff" or osuRC.kata[3] == ":!star":
            if len(osuRC.kata) == 6:
                try:
                    if float(osuRC.kata[4]) < float(osuRC.kata[5]):
                        osuAPI.diffb = osuRC.kata[4]
                        osuAPI.difft = osuRC.kata[5]
                        osuRC.kirim("PRIVMSG "+osuHost.channel+" set difficulty from "+str(osuAPI.diffb)+" to "+str(osuAPI.difft))
                    elif float(osuRC.kata[4]) > float(osuRC.kata[5]):
                        osuAPI.diffb = osuRC.kata[4]
                        osuAPI.difft = osuRC.kata[5]
                        osuRC.kirim("PRIVMSG "+osuHost.channel+" set difficulty from "+str(osuAPI.diffb)+" to "+str(osuAPI.difft))
                    else:
                        osuRC.kirim("PRIVMSG "+osuHost.channel+" wrong command. example: !star 4.5 5.2")
                except:
                    osuRC.kirim("PRIVMSG "+osuHost.channel+" wrong command. example: !star 4.5 5.2")
            else:
                osuRC.kirim("PRIVMSG "+osuHost.channel+" wrong command. example: !star 4.5 5.2")

    def commandInfo():
        '''kasih info'''
        if osuRC.kata[3] == ":!i" or osuRC.kata[3] == ":!info":
            nama = osuHost.getnama()
            namaclean = nama.replace("_"," ")
            osuRC.kirim("PRIVMSG "+osuHost.channel+" Autohost under developement. Made by [http://github.com/kron3 kron3], See all available command [https://github.com/kron3/osu-autohost/wiki/OSU-Autohost-Wiki here].")

    def commandReady():
        '''vote mulai'''
        if osuRC.kata[3] == ":!r" or osuRC.kata[3] == ":!ready" or osuRC.kata[3] == ":!go":
            nama = osuHost.getnama()
            namaclean = nama.replace("_"," ")
            if osuRC.kata[0] not in osuHost.voterstart:
                osuHost.voterstart.append(osuRC.kata[0])
                minimalstart = int(len(osuHost.player)*0.75)
                if minimalstart < 1:
                    minimalstart = 1
                osuRC.kirim("PRIVMSG "+osuHost.channel+" "+namaclean+" vote for start ("+str(len(osuHost.voterstart))+"/"+str(minimalstart)+")")
                if len(osuHost.voterstart) >= minimalstart:
                    osuHost.voterstart = []
                    osuHost.startroom()
            else:
                osuRC.kirim("PRIVMSG "+nama+" You already vote for start ...")

    def commandSkip():
        '''vote skip lagu saat ini'''
        if osuRC.kata[3] == ":!s" or osuRC.kata[3] == ":!skip" or osuRC.kata[3] == ":!pass":
            nama = osuHost.getnama()
            namaclean = nama.replace("_"," ")
            if osuRC.kata[0] not in osuHost.voterskip:
                osuHost.voterskip.append(osuRC.kata[0])
                minimalskip = int(len(osuHost.player)*0.5)
                if minimalskip < 1:
                    minimalskip = 1
                osuRC.kirim("PRIVMSG "+osuHost.channel+" "+namaclean+" vote for skip ("+str(len(osuHost.voterskip))+"/"+str(minimalskip)+")")
                if len(osuHost.voterskip) >= minimalskip:
                    osuHost.voterskip = []
                    osuHost.nextmap()
            else:
                osuRC.kirim("PRIVMSG "+nama+" You already vote for skip ...")

    def commandAdd():
        '''menambahkan lagu ke queue'''
        try:
            if osuRC.kata[3] == ":!add" or osuRC.kata[3] == ":+":
                if "osu.ppy.sh/b/" in osuRC.kata[4]:
                    getmap = osuRC.kata[4].replace("https://","")
                    getmap = getmap.replace("osu.ppy.sh/b/","")
                    getmap = getmap.split("&")
                    getmap = getmap[0]
                    getmap = getmap.split("?")
                    getmap = getmap[0]
                    osuHost.mapqueue.append(getmap)
                    judulmap = osuAPI.getName(map = getmap)
                    osuRC.kirim("PRIVMSG "+osuHost.channel+" "+judulmap+" added to queue ("+str(len(osuHost.mapqueue))+")")
                    print(osuHost.mapqueue)
                    if osuHost.beatmap == 0:
                        osuHost.nextmap()

                elif "osu.ppy.sh/s/" in osuRC.kata[4]:
                    getset = osuRC.kata[4].replace("https://","")
                    getset = getset.replace("osu.ppy.sh/s/","")
                    getmap = osuAPI.getmapbyset(set=getset,diffb=osuAPI.diffb,difft=osuAPI.difft)
                    getmap = str(getmap)
                    if getmap != 'None':
                        osuHost.mapqueue.append(getmap)
                    judulmap = osuAPI.getName(map = getmap)
                    judulmap = str(judulmap)
                    if judulmap == 'None':
                        osuRC.kirim("PRIVMSG "+osuHost.channel+" that beatmap list not have standarized difficulty! make sure it have ("+osuAPI.diffb+"*-"+osuAPI.difft+"*) difficulty.")
                    else:
                        osuRC.kirim("PRIVMSG "+osuHost.channel+" You input a beatmap set. i'll choose the difficulty for you ...")
                        osuRC.kirim("PRIVMSG "+osuHost.channel+" "+judulmap+" added to queue ("+str(len(osuHost.mapqueue))+")")
                        print(osuHost.mapqueue)
                        if osuHost.beatmap == 0:
                            osuHost.nextmap()

                elif "/beatmapsets/" in osuRC.kata[4]:
                    getmap = osuRC.kata[4].replace("https://","")
                    getmap = getmap.split("/")
                    getmap = getmap[len(getmap)-1]
                    if "#" in getmap:
                        getmap = osuAPI.getmapbyset(set=getmap,diffb=osuAPI.diffb,difft=osuAPI.difft)
                        getmap = str(getmap)
                        osuRC.kirim("PRIVMSG "+osuHost.channel+" You input a beatmap set. i'll choose the difficulty for you ...")
                    if getmap != 'None':
                        osuHost.mapqueue.append(getmap)
                    judulmap = osuAPI.getName(map = getmap)
                    osuRC.kirim("PRIVMSG "+osuHost.channel+" "+judulmap+" added to queue ("+str(len(osuHost.mapqueue))+")")
                    if osuHost.beatmap == 0:
                        osuHost.nextmap()
                else:
                    osuRC.kirim("PRIVMSG "+osuHost.channel+" wrong or unsupported beatmap link.")
        except:
            osuRC.kirim("PRIVMSG "+osuHost.channel+" unexpectedError on !add command - make sure the command is !add https://osu.ppy.sh/s/<beatmapset_id>.")


    def getnotif():
        '''just caller'''
        osuHost.getCreatedRoomID()
        osuHost.getjoin()
        osuHost.getquit()
        osuHost.isgamestart()
        osuHost.isgamefinish()
        osuHost.isallready()
        osuHost.isclosed()

    def getcommand():
        '''just caller'''
        if len(osuRC.kata) > 3:
            osuHost.commandPing()
            osuHost.commandQueue()
            osuHost.commandDiff()
            osuHost.commandInfo()
            osuHost.commandReady()
            osuHost.commandSkip()
            osuHost.commandAdd()

class osuAPI:
    '''untuk ambil beatmap name, dsb'''
    KEY = "ad8c161908bcf5bf8f595300537edbbecb7fc17b"         #cari di osu.ppy.sh/p/api
    playlist = []
    a = 0
    b = 0
    diffb = 4
    diffb = float(diffb)
    difft = 5
    difft = float(difft)
    def tglsekarang():
        '''get bulan untuk since'''
        return time.localtime(time.time())

    def connAPI(since=-1,set=-1,map=-1,mode=0):
        '''connect ke API osu'''
        osuAPI.KEY = str(osuAPI.KEY)
        since = str(since)
        set = str(set)
        map = str(map)
        mode = str(mode)
        if since != '-1':
            xsince = '&since='+since
        else:
            xsince = ''
        if set != '-1':
            xset = '&s='+set
        else:
            xset = ''
        if map != '-1':
            xmap = '&b='+map
        else:
            xmap = ''
#        print("https://osu.ppy.sh/api/get_beatmaps?k="+osuAPI.KEY+xsince+xset+xmap+"&limit=500&m="+mode)
        return requests.get("https://osu.ppy.sh/api/get_beatmaps?k="+osuAPI.KEY+xsince+xset+xmap+"&limit=500&m="+mode).json()

#    def getRand(diffb,difft):
    def getRand():
        '''get random set playlist. any ranked std map'''
        sekarang = osuAPI.tglsekarang()
        if osuAPI.a >= sekarang[1]:
            osuAPI.a = 0
            osuAPI.b += 1
        since = str(sekarang[0]-osuAPI.b)+'-'+str(sekarang[1]-osuAPI.a)+'-1'
        print(since)
        data = osuAPI.connAPI(since=since)
        setid = ''
        for song in data:
            if setid != song['beatmapset_id']:
                osuAPI.playlist.append(song['beatmapset_id'])
                setid = song['beatmapset_id']
#            if float(song['difficultyrating']) >= float(diffb) and float(song['difficultyrating']) < float(difft) and setid != song['beatmapset_id']:
#                osuAPI.playlist.append(song['beatmap_id'])
#                setid = song['beatmapset_id']
        osuAPI.a += 1
#        print(osuAPI.playlist)

    def getName(map):
        data = osuAPI.connAPI(map=map)
        for song in data:
            return song['artist']+' - '+song['title']+' ('+song['difficultyrating']+'*)'

    def getmapbyset(set,diffb,difft):
        data = osuAPI.connAPI(set=set)
        for song in data:
            if float(song['difficultyrating']) >= float(diffb) and float(song['difficultyrating']) < float(difft):
                return song['beatmap_id']

## Program start here
def main():
    '''main program'''
    connection = osuRC.conn()
    if connection != True:
        print(connection)
        quit()
    osuHost.roomname = input("Room Name: ")
    osuHost.makeroom()
    while 1:
        data = osuRC.terima().split("\n")
        if len(data)-1 == 0:
            osuRC.disconnected()
        for osuRC.baris in data:
            osuRC.kata = osuRC.baris.split(" ")
            osuRC.cetak(osuRC.baris)
            osuHost.getnotif()
            osuHost.getcommand()
    time.sleep(2)

main()
