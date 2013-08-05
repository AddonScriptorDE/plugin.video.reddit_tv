#!/usr/bin/python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import socket
import sys
import re
import os
import random
import datetime
import xbmcplugin
import xbmcgui
import xbmcaddon

addon = xbmcaddon.Addon()
addonID = 'plugin.video.reddit_tv'
socket.setdefaulttimeout(30)
pluginhandle = int(sys.argv[1])
addonUserDataFolder = xbmc.translatePath("special://profile/addon_data/"+addonID)
subredditsFile = xbmc.translatePath("special://profile/addon_data/"+addonID+"/subreddits")
xbox = xbmc.getCondVisibility("System.Platform.xbox")
forceViewMode = addon.getSetting("forceViewMode") == "true"
viewMode = str(addon.getSetting("viewMode"))
filter = addon.getSetting("filter") == "true"
filterRating=int(addon.getSetting("filterRating"))
filterVoteThreshold=int(addon.getSetting("filterVoteThreshold")) 
translation = addon.getLocalizedString
urlMain = "http://www.reddit.com"
userAgent = "Mozilla/5.0 (Windows NT 6.2; WOW64; rv:22.0) Gecko/20100101 Firefox/22.0"
opener = urllib2.build_opener()
opener.addheaders = [('User-Agent', userAgent)]
if not os.path.isdir(addonUserDataFolder):
  os.mkdir(addonUserDataFolder)


def index():
    entries = []
    entries.append("videos")
    if os.path.exists(subredditsFile):
        fh = open(subredditsFile, 'r')
        content = fh.read()
        fh.close()
        spl = content.split('\n')
        for i in range(0, len(spl), 1):
            if spl[i]:
                subreddit = spl[i]
                entries.append(subreddit)
    entries.sort()
    for entry in entries:
        if entry=="videos":
            addDir(entry.title(), entry, 'listSorting', "")
        else:
            addDirR(entry.title(), entry, 'listSorting', "")
    addDir("- "+translation(30001), "", 'addSubreddit', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def addSubreddit():
    keyboard = xbmc.Keyboard('', translation(30001))
    keyboard.doModal()
    if keyboard.isConfirmed() and keyboard.getText():
        subreddit = keyboard.getText()
        fh = open(subredditsFile, 'a')
        fh.write(subreddit+'\n')
        fh.close()


def removeSubreddit(subreddit):
    fh = open(subredditsFile, 'r')
    content = fh.read()
    fh.close()
    fh = open(subredditsFile, 'w')
    fh.write(content.replace(subreddit+'\n', ''))
    fh.close()
    xbmc.executebuiltin("Container.Refresh")


def listSorting(subreddit):
    addDir(translation(30002), urlMain+"/r/"+subreddit+"/hot/.json?limit=100", 'listVideos', "")
    addDir(translation(30003), urlMain+"/r/"+subreddit+"/new/.json?limit=100", 'listVideos', "")
    addDir(translation(30004)+": "+translation(30007), urlMain+"/r/"+subreddit+"/top/.json?limit=100&t=day", 'listVideos', "")
    addDir(translation(30004)+": "+translation(30008), urlMain+"/r/"+subreddit+"/top/.json?limit=100&t=week", 'listVideos', "")
    addDir(translation(30004)+": "+translation(30009), urlMain+"/r/"+subreddit+"/top/.json?limit=100&t=month", 'listVideos', "")
    addDir(translation(30004)+": "+translation(30010), urlMain+"/r/"+subreddit+"/top/.json?limit=100&t=year", 'listVideos', "")
    addDir(translation(30004)+": "+translation(30011), urlMain+"/r/"+subreddit+"/top/.json?limit=100&t=all", 'listVideos', "")
    addDir(translation(30005)+": "+translation(30006), urlMain+"/r/"+subreddit+"/controversial/.json?limit=100&t=hour", 'listVideos', "")
    addDir(translation(30005)+": "+translation(30007), urlMain+"/r/"+subreddit+"/controversial/.json?limit=100&t=day", 'listVideos', "")
    addDir(translation(30005)+": "+translation(30008), urlMain+"/r/"+subreddit+"/controversial/.json?limit=100&t=week", 'listVideos', "")
    addDir(translation(30005)+": "+translation(30009), urlMain+"/r/"+subreddit+"/controversial/.json?limit=100&t=month", 'listVideos', "")
    addDir(translation(30005)+": "+translation(30010), urlMain+"/r/"+subreddit+"/controversial/.json?limit=100&t=year", 'listVideos', "")
    addDir(translation(30005)+": "+translation(30011), urlMain+"/r/"+subreddit+"/controversial/.json?limit=100&t=all", 'listVideos', "")
    xbmcplugin.endOfDirectory(pluginhandle)


def listVideos(url):
    xbmcplugin.setContent(pluginhandle, "episodes")
    addDir("- "+translation(30012), url, 'playRandomly', "")
    content = opener.open(url).read()
    spl = content.split('"content"')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        try:
            match = re.compile('"title": "(.+?)"', re.DOTALL).findall(entry)
            title = match[0].replace("&amp;","&")
            match = re.compile('"description": "(.+?)"', re.DOTALL).findall(entry)
            description = match[0]
            match = re.compile('"created_utc": (.+?),', re.DOTALL).findall(entry)
            date = match[0].split(".")[0]
            dateTime = str(datetime.datetime.fromtimestamp(int(date)).strftime('%Y-%m-%d %H:%M'))
            date = dateTime.split(" ")[0]
            match = re.compile('"ups": (.+?),', re.DOTALL).findall(entry)
            ups = int(match[0])
            match = re.compile('"downs": (.+?),', re.DOTALL).findall(entry)
            downs = int(match[0])
            rating = int(ups*100/(ups+downs))
            if filter and (ups+downs)>filterVoteThreshold and rating<filterRating:
                continue
            title = title+" ("+str(rating)+"%)"
            match = re.compile('"num_comments": (.+?),', re.DOTALL).findall(entry)
            comments = match[0]
            description = dateTime+"  |  "+str(ups+downs)+" votes: "+str(rating)+"% Up  |  "+comments+" comments\n"+description
            match = re.compile('"thumbnail_url": "(.+?)"', re.DOTALL).findall(entry)
            thumb = match[0]
            matchYoutube = re.compile('"url": "http://www.youtube.com/watch\\?v=(.+?)"', re.DOTALL).findall(entry)
            matchVimeo = re.compile('"url": "http://vimeo.com/(.+?)"', re.DOTALL).findall(entry)
            url = ""
            if matchYoutube:
                url = getYoutubeUrl(matchYoutube[0])
            elif matchVimeo:
                url = getVimeoUrl(matchVimeo[0].replace("#", ""))
            if url:
                addLink(title, url, 'playVideo', thumb, description, date)
        except:
            pass
    xbmcplugin.endOfDirectory(pluginhandle)
    if forceViewMode:
        xbmc.executebuiltin('Container.SetViewMode('+viewMode+')')


def playRandomly(url):
    entries = []
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    content = opener.open(url).read()
    spl = content.split('"content"')
    for i in range(1, len(spl), 1):
        entry = spl[i]
        try:
            match = re.compile('"title": "(.+?)"', re.DOTALL).findall(entry)
            title = match[0].replace("&amp;","&")
            match = re.compile('"ups": (.+?),', re.DOTALL).findall(entry)
            ups = int(match[0])
            match = re.compile('"downs": (.+?),', re.DOTALL).findall(entry)
            downs = int(match[0])
            rating = int(ups*100/(ups+downs))
            if filter and (ups+downs)>filterVoteThreshold and rating<filterRating:
                continue
            matchYoutube = re.compile('"url": "http://www.youtube.com/watch\\?v=(.+?)"', re.DOTALL).findall(entry)
            matchVimeo = re.compile('"url": "http://vimeo.com/(.+?)"', re.DOTALL).findall(entry)
            url = ""
            if matchYoutube:
                url = getYoutubeUrl(matchYoutube[0])
            elif matchVimeo:
                url = getVimeoUrl(matchVimeo[0].replace("#", ""))
            if url:
                listitem = xbmcgui.ListItem(title)
                entries.append([title, url])
        except:
            pass
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


def playVideo(url):
    listitem = xbmcgui.ListItem(path=url)
    xbmcplugin.setResolvedUrl(pluginhandle, True, listitem)


def parameters_string_to_dict(parameters):
    ''' Convert parameters encoded in a URL to a dict. '''
    paramDict = {}
    if parameters:
        paramPairs = parameters[1:].split("&")
        for paramsPair in paramPairs:
            paramSplits = paramsPair.split('=')
            if (len(paramSplits)) == 2:
                paramDict[paramSplits[0]] = paramSplits[1]
    return paramDict


def addLink(name, url, mode, iconimage, description, date):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultVideo.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name, "Plot": description, "Aired": date})
    liz.setProperty('IsPlayable', 'true')
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz)
    return ok


def addDir(name, url, mode, iconimage):
    u = sys.argv[0]+"?url="+urllib.quote_plus(url)+"&mode="+str(mode)
    ok = True
    liz = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=iconimage)
    liz.setInfo(type="Video", infoLabels={"Title": name})
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

params = parameters_string_to_dict(sys.argv[2])
mode = urllib.unquote_plus(params.get('mode', ''))
url = urllib.unquote_plus(params.get('url', ''))

if mode == 'listVideos':
    listVideos(url)
elif mode == 'listSorting':
    listSorting(url)
elif mode == 'playVideo':
    playVideo(url)
elif mode == 'addSubreddit':
    addSubreddit()
elif mode == 'removeSubreddit':
    removeSubreddit(url)
elif mode == 'playRandomly':
    playRandomly(url)
else:
    index()
