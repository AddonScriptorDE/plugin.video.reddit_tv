#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import socket
import sys
import re
import os
import json
import sqlite3
import random
import datetime
import xbmcplugin
import xbmcgui
import xbmcaddon
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom


addon = xbmcaddon.Addon()
pluginhandle = int(sys.argv[1])
addonID = addon.getAddonInfo('id')
translation = addon.getLocalizedString
xbox = xbmc.getCondVisibility("System.Platform.xbox")
osWin = xbmc.getCondVisibility('system.platform.windows')
osOsx = xbmc.getCondVisibility('system.platform.osx')
osLinux = xbmc.getCondVisibility('system.platform.linux')

socket.setdefaulttimeout(30)
opener = urllib2.build_opener()
userAgent = "XBMC | "+addonID+" | "+addon.getAddonInfo('version')
opener.addheaders = [('User-Agent', userAgent)]
urlMain = "http://www.reddit.com"

cat_new = addon.getSetting("cat_new") == "true"
cat_hot_h = addon.getSetting("cat_hot_h") == "true"
cat_hot_d = addon.getSetting("cat_hot_d") == "true"
cat_hot_w = addon.getSetting("cat_hot_w") == "true"
cat_hot_m = addon.getSetting("cat_hot_m") == "true"
cat_top_d = addon.getSetting("cat_top_d") == "true"
cat_top_w = addon.getSetting("cat_top_w") == "true"
cat_top_m = addon.getSetting("cat_top_m") == "true"
cat_top_y = addon.getSetting("cat_top_y") == "true"
cat_top_a = addon.getSetting("cat_top_a") == "true"
cat_com_h = addon.getSetting("cat_com_h") == "true"
cat_com_d = addon.getSetting("cat_com_d") == "true"
cat_com_w = addon.getSetting("cat_com_w") == "true"
cat_com_m = addon.getSetting("cat_com_m") == "true"
cat_com_y = addon.getSetting("cat_com_y") == "true"
cat_com_a = addon.getSetting("cat_com_a") == "true"

filter = addon.getSetting("filter") == "true"
filterRating = int(addon.getSetting("filterRating"))
filterThreshold = int(addon.getSetting("filterThreshold"))
showNSFW = addon.getSetting("showNSFW") == "true"

showAll = addon.getSetting("showAll") == "true"
showUnwatched = addon.getSetting("showUnwatched") == "true"
showUnfinished = addon.getSetting("showUnfinished") == "true"
showAllNewest = addon.getSetting("showAllNewest") == "true"
showUnwatchedNewest = addon.getSetting("showUnwatchedNewest") == "true"
showUnfinishedNewest = addon.getSetting("showUnfinishedNewest") == "true"

forceViewMode = addon.getSetting("forceViewMode") == "true"
viewMode = str(addon.getSetting("viewMode"))

itemsPerPage = int(addon.getSetting("itemsPerPage"))
itemsPerPage = ["25", "50", "75", "100"][itemsPerPage]

searchSort = int(addon.getSetting("searchSort"))
searchSort = ["ask", "relevance", "new", "hot", "top", "comments"][searchSort]
searchTime = int(addon.getSetting("searchTime"))
searchTime = ["ask", "hour", "day", "week", "month", "year", "all"][searchTime]

showBrowser = addon.getSetting("showBrowser") == "true"
browser_win = int(addon.getSetting("browser_win"))
browser_wb_zoom = str(addon.getSetting("browser_wb_zoom"))

addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/"+addonID)
subredditsFile = xbmc.translatePath("special://profile/addon_data/"+addonID+"/subreddits")
if not os.path.isdir(addonUserDataFolder):
    os.mkdir(addonUserDataFolder)

allHosterQuery = urllib.quote_plus("site:youtu.be OR site:youtube.com OR site:vimeo.com OR site:liveleak.com OR site:dailymotion.com")
if showNSFW:
    nsfw = "nsfw:yes"
else:
    nsfw = "nsfw:no"


def getDbPath():
    path = xbmc.translatePath("special://userdata/Database")
    files = os.listdir(path)
    latest = ""
    for file in files:
        if file[:8] == 'MyVideos' and file[-3:] == '.db':
            if file > latest:
                latest = file
    return os.path.join(path, latest)


def getPlayCount(url):
    c.execute('SELECT playCount FROM files WHERE strFilename=?', [url])
    result = c.fetchone()
    if result:
        result = result[0]
        if result:
            return int(result)
        return 0
    return -1


def addSubreddit(subreddit):
    alreadyIn = False
    fh = open(subredditsFile, 'r')
    content = fh.readlines()
    fh.close()
    if subreddit:
        for line in content:
            if line.lower()==subreddit.lower():
                alreadyIn = True
        if not alreadyIn:
            fh = open(subredditsFile, 'a')
            fh.write(subreddit+'\n')
            fh.close()
    else:
        keyboard = xbmc.Keyboard('', translation(30001))
        keyboard.doModal()
        if keyboard.isConfirmed() and keyboard.getText():
            subreddit = keyboard.getText()
            for line in content:
                if line.lower()==subreddit.lower()+"\n":
                    alreadyIn = True
            if not alreadyIn:
                fh = open(subredditsFile, 'a')
                fh.write(subreddit+'\n')
                fh.close()


def removeSubreddit(subreddit):
    fh = open(subredditsFile, 'r')
    content = fh.readlines()
    fh.close()
    contentNew = ""
    for line in content:
        if line!=subreddit+'\n':
            contentNew+=line
    fh = open(subredditsFile, 'w')
    fh.write(contentNew)
    fh.close()
    xbmc.executebuiltin("Container.Refresh")


def index():
    content = ""
    if os.path.exists(subredditsFile):
        fh = open(subredditsFile, 'r')
        content = fh.read()
        fh.close()
    if "all\n" not in content:
        fh = open(subredditsFile, 'a')
        fh.write('all\n')
        fh.close()
    entries = []
    if os.path.exists(subredditsFile):
        fh = open(subredditsFile, 'r')
        content = fh.read()
        fh.close()
        spl = content.split('\n')
        for i in range(0, len(spl), 1):
            if spl[i]:
                subreddit = spl[i].strip()
                entries.append(subreddit.title())
    entries.sort()
    for entry in entries:
        if entry == "all":
            addDir(entry, entry.lower(), 'listSorting', "")
        else:
            addDirR(entry, entry.lower(), 'listSorting', "")
    addDir("[ Vimeo.com ]", "all", 'listSorting', "", "site:vimeo.com")
    addDir("[ Youtube.com ]", "all", 'listSorting', "", "site:youtu.be OR site:youtube.com")
    addDir("[ Liveleak.com ]", "all", 'listSorting', "", "site:liveleak.com")
    addDir("[ Dailymotion.com ]", "all", 'listSorting', "", "site:dailymotion.com")
    addDir("[B]- "+translation(30001)+"[/B]", "", 'addSubreddit', "")
    addDir("[B]- "+translation(30019)+"[/B]", "", 'searchReddits', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def listSorting(subreddit, hosterQuery):
    hosterQuery = urllib.quote_plus(hosterQuery)
    if not hosterQuery:
        hosterQuery = allHosterQuery
    if cat_new:
        addDir(translation(30003), urlMain+"/r/"+subreddit+"/search.json?q="+nsfw+"+"+hosterQuery+"&sort=new&restrict_sr=on&limit="+itemsPerPage, 'listVideos', "", subreddit)
    if cat_hot_h:
        addDir(translation(30002)+": "+translation(30006), urlMain+"/r/"+subreddit+"/search.json?q="+nsfw+"+"+hosterQuery+"&sort=hot&restrict_sr=on&limit="+itemsPerPage+"&t=hour", 'listVideos', "", subreddit)
    if cat_hot_d:
        addDir(translation(30002)+": "+translation(30007), urlMain+"/r/"+subreddit+"/search.json?q="+nsfw+"+"+hosterQuery+"&sort=hot&restrict_sr=on&limit="+itemsPerPage+"&t=day", 'listVideos', "", subreddit)
    if cat_hot_w:
        addDir(translation(30002)+": "+translation(30008), urlMain+"/r/"+subreddit+"/search.json?q="+nsfw+"+"+hosterQuery+"&sort=hot&restrict_sr=on&limit="+itemsPerPage+"&t=week", 'listVideos', "", subreddit)
    if cat_hot_m:
        addDir(translation(30002)+": "+translation(30009), urlMain+"/r/"+subreddit+"/search.json?q="+nsfw+"+"+hosterQuery+"&sort=hot&restrict_sr=on&limit="+itemsPerPage+"&t=month", 'listVideos', "", subreddit)
    if cat_top_d:
        addDir(translation(30004)+": "+translation(30007), urlMain+"/r/"+subreddit+"/search.json?q="+nsfw+"+"+hosterQuery+"&sort=top&restrict_sr=on&limit="+itemsPerPage+"&t=day", 'listVideos', "", subreddit)
    if cat_top_w:
        addDir(translation(30004)+": "+translation(30008), urlMain+"/r/"+subreddit+"/search.json?q="+nsfw+"+"+hosterQuery+"&sort=top&restrict_sr=on&limit="+itemsPerPage+"&t=week", 'listVideos', "", subreddit)
    if cat_top_m:
        addDir(translation(30004)+": "+translation(30009), urlMain+"/r/"+subreddit+"/search.json?q="+nsfw+"+"+hosterQuery+"&sort=top&restrict_sr=on&limit="+itemsPerPage+"&t=month", 'listVideos', "", subreddit)
    if cat_top_y:
        addDir(translation(30004)+": "+translation(30010), urlMain+"/r/"+subreddit+"/search.json?q="+nsfw+"+"+hosterQuery+"&sort=top&restrict_sr=on&limit="+itemsPerPage+"&t=year", 'listVideos', "", subreddit)
    if cat_top_a:
        addDir(translation(30004)+": "+translation(30011), urlMain+"/r/"+subreddit+"/search.json?q="+nsfw+"+"+hosterQuery+"&sort=top&restrict_sr=on&limit="+itemsPerPage+"&t=all", 'listVideos', "", subreddit)
    if cat_com_h:
        addDir(translation(30005)+": "+translation(30006), urlMain+"/r/"+subreddit+"/search.json?q="+nsfw+"+"+hosterQuery+"&sort=comments&restrict_sr=on&limit="+itemsPerPage+"&t=hour", 'listVideos', "", subreddit)
    if cat_com_d:
        addDir(translation(30005)+": "+translation(30007), urlMain+"/r/"+subreddit+"/search.json?q="+nsfw+"+"+hosterQuery+"&sort=comments&restrict_sr=on&limit="+itemsPerPage+"&t=day", 'listVideos', "", subreddit)
    if cat_com_w:
        addDir(translation(30005)+": "+translation(30008), urlMain+"/r/"+subreddit+"/search.json?q="+nsfw+"+"+hosterQuery+"&sort=comments&restrict_sr=on&limit="+itemsPerPage+"&t=week", 'listVideos', "", subreddit)
    if cat_com_m:
        addDir(translation(30005)+": "+translation(30009), urlMain+"/r/"+subreddit+"/search.json?q="+nsfw+"+"+hosterQuery+"&sort=comments&restrict_sr=on&limit="+itemsPerPage+"&t=month", 'listVideos', "", subreddit)
    if cat_com_y:
        addDir(translation(30005)+": "+translation(30010), urlMain+"/r/"+subreddit+"/search.json?q="+nsfw+"+"+hosterQuery+"&sort=comments&restrict_sr=on&limit="+itemsPerPage+"&t=year", 'listVideos', "", subreddit)
    if cat_com_a:
        addDir(translation(30005)+": "+translation(30011), urlMain+"/r/"+subreddit+"/search.json?q="+nsfw+"+"+hosterQuery+"&sort=comments&restrict_sr=on&limit="+itemsPerPage+"&t=all", 'listVideos', "", subreddit)
    addDir("[B]- "+translation(30023)+"[/B]", subreddit, "listFavourites", "")
    addDir("[B]- "+translation(30017)+"[/B]", subreddit, "searchVideos", "")
    xbmcplugin.endOfDirectory(pluginhandle)


def listVideos(url, subreddit):
    currentUrl = url
    xbmcplugin.setContent(pluginhandle, "episodes")
    if showAllNewest:
        addDir("[B]- "+translation(30166)+"[/B]", url, 'autoPlay', "", "ALL_NEW")
    if showUnwatchedNewest:
        addDir("[B]- "+translation(30167)+"[/B]", url, 'autoPlay', "", "UNWATCHED_NEW")
    if showUnfinishedNewest:
        addDir("[B]- "+translation(30168)+"[/B]", url, 'autoPlay', "", "UNFINISHED_NEW")
    if showAll:
        addDir("[B]- "+translation(30012)+"[/B]", url, 'autoPlay', "", "ALL_RANDOM")
    if showUnwatched:
        addDir("[B]- "+translation(30014)+"[/B]", url, 'autoPlay', "", "UNWATCHED_RANDOM")
    if showUnfinished:
        addDir("[B]- "+translation(30015)+"[/B]", url, 'autoPlay', "", "UNFINISHED_RANDOM")
    content = opener.open(url).read()
    content = json.loads(content.replace('\\"', '\''))
    count = 1
    for entry in content['data']['children']:
        try:
            title = cleanTitle(entry['data']['title'].encode('utf-8'))
            try:
                description = cleanTitle(entry['data']['media']['oembed']['description'].encode('utf-8'))
            except:
                description = ""
            commentsUrl = urlMain+entry['data']['permalink'].encode('utf-8')
            try:
                date = str(entry['data']['created_utc'])
                date = date.split(".")[0]
                dateTime = str(datetime.datetime.fromtimestamp(int(date)).strftime('%Y-%m-%d %H:%M'))
                date = dateTime.split(" ")[0]
            except:
                date = ""
                dateTime = ""
            ups = entry['data']['ups']
            downs = entry['data']['downs']
            rating = 100
            if ups+downs>0:
                rating = int(ups*100/(ups+downs))
            if filter and (ups+downs) > filterThreshold and rating < filterRating:
                continue
            comments = entry['data']['num_comments']
            description = dateTime+"  |  "+str(ups+downs)+" votes: "+str(rating)+"% Up  |  "+str(comments)+" comments\n"+description
            try:
                thumb = entry['data']['media']['oembed']['thumbnail_url'].encode('utf-8')
            except:
                thumb = entry['data']['thumbnail'].encode('utf-8')
            try:
                url = entry['data']['media']['oembed']['url']+'"'
            except:
                url = entry['data']['url']+'"'
            matchYoutube = re.compile('youtube.com/watch\\?v=(.+?)"', re.DOTALL).findall(url)
            matchVimeo = re.compile('vimeo.com/(.+?)"', re.DOTALL).findall(url)
            matchDailyMotion = re.compile('dailymotion.com/video/(.+?)_', re.DOTALL).findall(url)
            matchDailyMotion2 = re.compile('dailymotion.com/.+?video=(.+?)', re.DOTALL).findall(url)
            matchLiveLeak = re.compile('liveleak.com/view\\?i=(.+?)"', re.DOTALL).findall(url)
            url = ""
            if matchYoutube:
                url = getYoutubeUrl(matchYoutube[0])
            elif matchVimeo:
                url = getVimeoUrl(matchVimeo[0].replace("#", "").split("?")[0])
            elif matchDailyMotion:
                url = getDailyMotionUrl(matchDailyMotion[0])
            elif matchDailyMotion2:
                url = getDailyMotionUrl(matchDailyMotion2[0])
            elif matchLiveLeak:
                url = getLiveLeakUrl(matchLiveLeak[0])
            if url:
                addLink(title, url, 'playVideo', thumb, description, date, count, commentsUrl, subreddit)
                count+=1
        except:
            pass
    try:
        after = content['data']['after']
        if "&after=" in currentUrl:
            nextUrl = currentUrl[:currentUrl.find("&after=")]+"&after="+after
        else:
            nextUrl = currentUrl+"&after="+after
        addDir(translation(30016), nextUrl, 'listVideos', "", subreddit)
    except:
        pass
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')
    xbmcplugin.endOfDirectory(pluginhandle)


def listFavourites(subreddit):
    xbmcplugin.setContent(pluginhandle, "episodes")
    file = os.path.join(addonUserDataFolder, subreddit+".fav")
    xbmcplugin.addSortMethod(pluginhandle, xbmcplugin.SORT_METHOD_LABEL)
    if os.path.exists(file):
        fh = open(file, 'r')
        content = fh.read()
        fh.close()
        match = re.compile('<favourite name="(.+?)" url="(.+?)" description="(.+?)" thumb="(.+?)" date="(.+?)" site="(.+?)" />', re.DOTALL).findall(content)
        for name, url, desc, thumb, date, site in match:
            addFavLink(name, url, "playVideo", thumb, desc.replace("<br>","\n"), date, site, subreddit)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')
    xbmcplugin.endOfDirectory(pluginhandle)


def autoPlay(url, type):
    entries = []
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    content = opener.open(url).read()
    content = json.loads(content.replace('\\"', '\''))
    for entry in content['data']['children']:
        try:
            title = cleanTitle(entry['data']['media']['oembed']['title'].encode('utf-8'))
            ups = entry['data']['ups']
            downs = entry['data']['downs']
            rating = 100
            if ups+downs>0:
                rating = int(ups*100/(ups+downs))
            if filter and (ups+downs) > filterThreshold and rating < filterRating:
                continue
            try:
                url = entry['data']['media']['oembed']['url']+'"'
            except:
                url = entry['data']['url']+'"'
            matchYoutube = re.compile('youtube.com/watch\\?v=(.+?)"', re.DOTALL).findall(url)
            matchVimeo = re.compile('vimeo.com/(.+?)"', re.DOTALL).findall(url)
            matchDailyMotion = re.compile('dailymotion.com/video/(.+?)_', re.DOTALL).findall(url)
            matchDailyMotion2 = re.compile('dailymotion.com/.+?video=(.+?)', re.DOTALL).findall(url)
            matchLiveLeak = re.compile('liveleak.com/view\\?i=(.+?)"', re.DOTALL).findall(url)
            url = ""
            if matchYoutube:
                url = getYoutubeUrl(matchYoutube[0])
            elif matchVimeo:
                url = getVimeoUrl(matchVimeo[0].replace("#", "").split("?")[0])
            elif matchDailyMotion:
                url = getDailyMotionUrl(matchDailyMotion[0])
            elif matchDailyMotion2:
                url = getDailyMotionUrl(matchDailyMotion2[0])
            elif matchLiveLeak:
                url = getLiveLeakUrl(matchLiveLeak[0])
            if url:
                url = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode=playVideo"
                if type.startswith("ALL_"):
                    listitem = xbmcgui.ListItem(title)
                    entries.append([title, url])
                elif type.startswith("UNWATCHED_") and getPlayCount(url) < 0:
                    listitem = xbmcgui.ListItem(title)
                    entries.append([title, url])
                elif type.startswith("UNFINISHED_") and getPlayCount(url) == 0:
                    listitem = xbmcgui.ListItem(title)
                    entries.append([title, url])
        except:
            pass
    if type.endswith("_RANDOM"):
        random.shuffle(entries)
    for title, url in entries:
        listitem = xbmcgui.ListItem(title)
        playlist.add(url, listitem)
    xbmc.Player().play(playlist)


def getYoutubeUrl(id):
    if xbox:
        url = "plugin://video/YouTube/?path=/root/video&action=play_video&videoid=" + id
    else:
        url = "plugin://plugin.video.youtube/?path=/root/video&action=play_video&videoid=" + id
    return url


def getVimeoUrl(id):
    if xbox:
        url = "plugin://video/Vimeo/?path=/root/video&action=play_video&videoid=" + id
    else:
        url = "plugin://plugin.video.vimeo/?path=/root/video&action=play_video&videoid=" + id
    return url


def getDailyMotionUrl(id):
    if xbox:
        url = "plugin://video/DailyMotion.com/?url=" + id + "&mode=playVideo"
    else:
        url = "plugin://plugin.video.dailymotion_com/?url=" + id + "&mode=playVideo"
    return url


def getLiveLeakUrl(id):
    if xbox:
        url = "plugin://video/Reddit.com/?url=" + id + "&mode=playLiveLeakVideo"
    else:
        url = "plugin://plugin.video.reddit_tv/?url=" + id + "&mode=playLiveLeakVideo"
    return url


def playVideo(url):
    listitem = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def playLiveLeakVideo(id):
    content = opener.open("http://www.liveleak.com/view?i="+id).read()
    matchHD = re.compile('hd_file_url=(.+?)&', re.DOTALL).findall(content)
    matchSD = re.compile('file: "(.+?)"', re.DOTALL).findall(content)
    if matchHD:
        url = urllib.unquote_plus(matchHD[0])
    elif matchSD:
        url = matchSD[0]
    listitem = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def queueVideo(url, name):
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    listitem = xbmcgui.ListItem(name)
    playlist.add(url, listitem)


def addToFavs(url, subreddit):
    file = os.path.join(addonUserDataFolder, subreddit+".fav")
    if os.path.exists(file):
        fh = open(file, 'r')
        content = fh.read()
        fh.close()
        if url not in content:
            fh = open(file, 'w')
            fh.write(content.replace("</favourites>", "    "+url.replace("\n","<br>")+"\n</favourites>"))
            fh.close()
    else:
        fh = open(file, 'a')
        fh.write("<favourites>\n    "+url.replace("\n","<br>")+"\n</favourites>")
        fh.close()


def removeFromFavs(url, subreddit):
    file = os.path.join(addonUserDataFolder, subreddit+".fav")
    fh = open(file, 'r')
    content = fh.read()
    fh.close()
    fh = open(file, 'w')
    fh.write(content.replace("    "+url.replace("\n","<br>")+"\n", ""))
    fh.close()
    xbmc.executebuiltin("Container.Refresh")


def searchVideos(subreddit, hosterQuery):
    hosterQuery = urllib.quote_plus(hosterQuery)
    if not hosterQuery:
        hosterQuery = allHosterQuery
    keyboard = xbmc.Keyboard('', translation(30017))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText().replace(" ", "+")
        if searchSort == "ask":
            searchAskOne(urlMain+"/r/"+subreddit+"/search.json?q="+nsfw+"+"+hosterQuery+"%20"+search_string+"&restrict_sr=on&limit="+itemsPerPage+"&sort=", subreddit)
        else:
            if searchTime == "ask":
                searchAskTwo(urlMain+"/r/"+subreddit+"/search.json?q="+nsfw+"+"+hosterQuery+"%20"+search_string+"&restrict_sr=on&limit="+itemsPerPage+"&sort="+searchSort+"&t=", subreddit)
            else:
                listVideos(urlMain+"/r/"+subreddit+"/search.json?q="+nsfw+"+"+hosterQuery+"%20"+search_string+"&restrict_sr=on&limit="+itemsPerPage+"&sort="+searchSort+"&t="+searchTime, subreddit)


def searchReddits():
    keyboard = xbmc.Keyboard('', translation(30017))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        search_string = keyboard.getText().replace(" ", "+")
        content = opener.open(urlMain+'/r/all/search?q='+search_string+'+'+nsfw+"+"+allHosterQuery+'&restrict_sr=on&sort=new&t=all').read()
        match = re.compile('<li class="searchfacet reddit"><a class="facet title word" href=".+?">/r/(.+?)</a>&nbsp;<span class="facet count number">\\((.+?)\\)</span></li>', re.DOTALL).findall(content)
        for subreddit, count in match:
            title = subreddit.title() + " ("+count+" "+translation(30020)+")"
            addDirA(title, subreddit, "listSorting", "")
        xbmcplugin.endOfDirectory(pluginhandle)


def searchAskOne(url, subreddit):
    addDir(translation(30114), url+"relevance", 'searchAskTwo', "", subreddit)
    addDir(translation(30115), url+"new", 'searchAskTwo', "", subreddit)
    addDir(translation(30116), url+"hot", 'searchAskTwo', "", subreddit)
    addDir(translation(30117), url+"top", 'searchAskTwo', "", subreddit)
    addDir(translation(30118), url+"comments", 'searchAskTwo', "", subreddit)
    xbmcplugin.endOfDirectory(pluginhandle)


def searchAskTwo(url, subreddit):
    if searchTime == "ask":
        addDir(translation(30119), url+"&t=hour", 'listVideos', "", subreddit)
        addDir(translation(30120), url+"&t=day", 'listVideos', "", subreddit)
        addDir(translation(30121), url+"&t=week", 'listVideos', "", subreddit)
        addDir(translation(30122), url+"&t=month", 'listVideos', "", subreddit)
        addDir(translation(30123), url+"&t=year", 'listVideos', "", subreddit)
        addDir(translation(30124), url+"&t=all", 'listVideos', "", subreddit)
        xbmcplugin.endOfDirectory(pluginhandle)
    else:
        listVideos(url+"&t="+searchTime, subreddit)


def cleanTitle(title):
        title = title.replace("&lt;","<").replace("&gt;",">").replace("&amp;","&").replace("&#039;","'").replace("&quot;","\"")
        return title.strip()


def parameters_string_to_dict(parameters):
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


def addLink(name, url, mode, iconimage, description, date, nr, site, subreddit):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": description, "Aired": date, "Episode": nr})
    liz.setProperty('IsPlayable', 'true')
    entries = []
    entries.append((translation(30018), 'RunPlugin(plugin://'+addonID+'/?mode=queueVideo&url='+urllib.quote_plus(u)+'&name='+urllib.quote_plus(name)+')',))
    favEntry = '<favourite name="'+name+'" url="'+u+'" description="'+description+'" thumb="'+iconimage+'" date="'+date+'" site="'+site+'" />'
    entries.append((translation(30022), 'RunPlugin(plugin://'+addonID+'/?mode=addToFavs&url='+urllib.quote_plus(favEntry)+'&type='+urllib.quote_plus(subreddit)+')',))
    if showBrowser and (osWin or osOsx or osLinux):
        if osWin and browser_win==0:
            entries.append((translation(30021), 'RunPlugin(plugin://plugin.program.webbrowser/?url='+urllib.quote_plus(site)+'&mode=showSite&zoom='+browser_wb_zoom+'&stopPlayback=no&showPopups=no&showScrollbar=no)',))
        else:
            entries.append((translation(30021), 'RunPlugin(plugin://plugin.program.chrome.starter/?url='+urllib.quote_plus(site)+'&mode=showSite)',))
    liz.addContextMenuItems(entries)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addFavLink(name, url, mode, iconimage, description, date, site, subreddit):
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": description, "Aired": date})
    liz.setProperty('IsPlayable', 'true')
    entries = []
    entries.append((translation(30018), 'RunPlugin(plugin://'+addonID+'/?mode=queueVideo&url='+urllib.quote_plus(url)+'&name='+urllib.quote_plus(name)+')',))
    favEntry = '<favourite name="'+name+'" url="'+url+'" description="'+description+'" thumb="'+iconimage+'" date="'+date+'" site="'+site+'" />'
    entries.append((translation(30024), 'RunPlugin(plugin://'+addonID+'/?mode=removeFromFavs&url='+urllib.quote_plus(favEntry)+'&type='+urllib.quote_plus(subreddit)+')',))
    if showBrowser and (osWin or osOsx or osLinux):
        if osWin and browser_win==0:
            entries.append((translation(30021), 'RunPlugin(plugin://plugin.program.webbrowser/?url='+urllib.quote_plus(site)+'&mode=showSite&zoom='+browser_wb_zoom+'&stopPlayback=no&showPopups=no&showScrollbar=no)',))
        else:
            entries.append((translation(30021), 'RunPlugin(plugin://plugin.program.chrome.starter/?url='+urllib.quote_plus(site)+'&mode=showSite)',))
    liz.addContextMenuItems(entries)
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=liz)
    return ok


def addDir(name, url, mode, iconimage, type=""):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)+"&type="+str(type)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


def addDirA(name, url, mode, iconimage):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    liz.addContextMenuItems([(translation(30001), 'RunPlugin(plugin://'+addonID+'/?mode=addSubreddit&url='+urllib.quote_plus(url)+')',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


def addDirR(name, url, mode, iconimage):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
    liz.addContextMenuItems([(translation(30013), 'RunPlugin(plugin://'+addonID+'/?mode=removeSubreddit&url='+urllib.quote_plus(url)+')',)])
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok


dbPath = getDbPath()
conn = sqlite3.connect(dbPath)
c = conn.cursor()

params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))
type = urllib.unquote_plus(params.get('type', ''))
name = urllib.unquote_plus(params.get('name', ''))

if mode == 'listVideos':
    listVideos(url, type)
elif mode == 'listSorting':
    listSorting(url, type)
elif mode == 'listFavourites':
    listFavourites(url)
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'playLiveLeakVideo':
    playLiveLeakVideo(url)
elif mode == 'addSubreddit':
    addSubreddit(url)
elif mode == 'removeSubreddit':
    removeSubreddit(url)
elif mode == 'autoPlay':
    autoPlay(url, type)
elif mode == 'queueVideo':
    queueVideo(url, name)
elif mode == 'addToFavs':
    addToFavs(url, type)
elif mode == 'removeFromFavs':
    removeFromFavs(url, type)
elif mode == 'searchAskOne':
    searchAskOne(url, type)
elif mode == 'searchAskTwo':
    searchAskTwo(url, type)
elif mode == 'searchVideos':
    searchVideos(url, type)
elif mode == 'searchReddits':
    searchReddits()
else:
    index()
