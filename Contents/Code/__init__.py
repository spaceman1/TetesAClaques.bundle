# -*- coding: utf-8 -*-
'''
Created on July 14, 2009

@summary: A Plex Media Server plugin that integrates movies from tetesaclaques.tv.
@version: 0.2
@author: Oncleben31
'''

import lxml, re, sys, locale

# Plugin parameters
PLUGIN_TITLE = "Têtes à Claques.TV"			# The plugin Title
PLUGIN_PREFIX = "/video/TAC.TV"				# The plugin's contextual path within Plex

# Plugin Icons
PLUGIN_ICON_DEFAULT = "icon-default.png"
FRENCH_SECTION_ICON = "frenchSpeaking.jpg"
ENGLISH_SECTION_ICON = "englishSpeaking.jpg"
VOTE_SECTION_ICON = "vote.png"
DATE_SECTION_ICON = "date.png"
SERIES_SECTION_ICON = "series.png"

# Plugin Artwork
PLUGIN_ARTWORK = "art-default.jpg"

#Some URLs for the script
PLUGIN_URL = "http://www.tetesaclaques.tv/"

####################################################################################################

def Start():
	#reload(sys)
	sys.setdefaultencoding("utf-8")
	
	# Register our plugins request handler
	Plugin.AddPrefixHandler(PLUGIN_PREFIX, MainMenu, PLUGIN_TITLE.decode('utf-8'), PLUGIN_ICON_DEFAULT, PLUGIN_ARTWORK)
	
	# Add in the views our plugin will support
	Plugin.AddViewGroup("Menu", viewMode="InfoList", mediaType="items")
	Plugin.AddViewGroup("ListeVideo", viewMode="List", mediaType="items")
	Plugin.AddViewGroup("ListeSerie", viewMode="Coverflow", mediaType="items")
	
	# Set up our plugin's container
	
	MediaContainer.title1 = PLUGIN_TITLE.decode('utf-8')
	MediaContainer.viewGroup = "Menu"
	MediaContainer.art = R(PLUGIN_ARTWORK)
	
####################################################################################################
# The plugin's main menu. 

def MainMenu():
	dir = MediaContainer(art = R(PLUGIN_ARTWORK), viewGroup = "Menu")
	dir.Append(Function(DirectoryItem(MenuLanguage, title=L("FRENCH_MENU"), thumb=R(FRENCH_SECTION_ICON), summary=L("FRENCH_MENU_SUMMARY")), langue="francais"))
	dir.Append(Function(DirectoryItem(MenuLanguage, title=L("ENGLISH_MENU"), thumb=R(ENGLISH_SECTION_ICON), summary=L("ENGLISH_MENU_SUMMARY")), langue="anglais"))
		 
	return dir

####################################################################################################
# Language choice for videos

def MenuLanguage(sender, langue):
	if langue == "francais":
		cookie = "LANGUEtac=fr"
		title2 = L("FRENCH_SECTION_TITLE")
	else :
	    cookie = "LANGUEtac=en"
	    title2 = L("ENGLISH_SECTION_TITLE")
	    
	dir = MediaContainer(art = R(PLUGIN_ARTWORK), viewGroup = "Menu", title2=title2)
	dir.Append(Function(DirectoryItem(RecupererListe, title=L("SORT_BY_DATE"), thumb=R(DATE_SECTION_ICON), summary=L("SORT_BY_DATE_SUMMARY")), classification="date", cookie=cookie))
	dir.Append(Function(DirectoryItem(RecupererListe, title=L("SORT_BY_VOTE"), thumb=R(VOTE_SECTION_ICON), summary=L("SORT_BY_VOTE_SUMMARY")), classification="vote", cookie=cookie))
	
	#Pas de mode série pour le moment en anglais
	if langue == "francais":
		dir.Append(Function(DirectoryItem(SerieListe, title=L("SORT_BY_SERIES"), thumb=R(SERIES_SECTION_ICON), summary=L("SORT_BY_SERIES_SUMMARY")), cookie=cookie))
	return dir

####################################################################################################
# Series List
	
def SerieListe(sender, cookie = None):
	dir = MediaContainer(art = R(PLUGIN_ARTWORK), viewGroup = "ListeSerie", title2 = L("SERIES_MENU_TITLE"))
	
	urldonneesHTML = PLUGIN_URL + "ajax/populerSliderIndex.php?serie=null&vid=null&vidToSlide=null&playOverlay=null&classification=date&selection=serie"
	Log("urldonneesHTML %s" % urldonneesHTML)
	
	donneesHTML = HTML.ElementFromURL(urldonneesHTML, encoding="utf-8", headers ={'cookie' : cookie})
	
	for c in donneesHTML.xpath("//div[@id='size']"):
		
		id = c.find("img").get("id").split("_")[0]
		Log("id %s" % (id))
		
		nom = c.find("img").get("alt")
		Log("nom %s" % (nom))
		
		shortThumb = c.find("img").get("src")
		thumb = "http://www.tetesaclaques.tv/" + shortThumb
		Log("thumb %s" % (thumb))
		
		infos = c.find("div").text
		
		dir.Append(Function(DirectoryItem(SerieEpisode, title=nom + " : " + infos, thumb=thumb), idserie=id, nom=nom, cookie=cookie))
	
	return dir

####################################################################################################
# videos' list of a serie

def SerieEpisode(sender, idserie=None, nom=None, cookie=None):
	dir = MediaContainer(art = R(PLUGIN_ARTWORK), viewGroup = "ListeVideo", title2 = nom)
	
	urldonneesHTML = PLUGIN_URL + "modules/populationSeries.php"
	donneesHTML = XML.ElementFromURL(urldonneesHTML, encoding="utf-8", headers ={'cookie' : cookie})
	listeID =[]
	for c in donneesHTML.xpath("//serie[idserie=" + idserie +"]//miniature"):
		listeID.append(int(c.find("idProduit").text))
		
	listeID.sort()
	
	for id in listeID:
		idProduit = str(id)
		Log("idProduit : %s" % idProduit)
		
		c = donneesHTML.xpath("//serie[idserie="+ idserie +"]//miniature[idProduit="+ idProduit +"]")[0]
		
		nom = c.find("titre").text
		Log("nom : %s" % nom)
		
		thumb = c.find("fichierMiniature").text
		Log("thumb : %s" % thumb)
		
		urlVideo = c.find("fichierVideo").text
		Log("urlVideo : %s" % urlVideo)
		
		dir.Append(VideoItem(urlVideo, title=nom, thumb=thumb)) 
		
	return dir

####################################################################################################
# videos sorted by vote or date

def RecupererListe(sender, classification=None, cookie = None) :
	if classification == "vote" :
		title2 = L("EPISODE_LIST_VOTE_TITLE")
	else :
		title2 = L("EPISODE_LIST_DATE_TITLE")
	
	dir = MediaContainer(art = R(PLUGIN_ARTWORK), viewGroup = "ListeVideo", title2 = title2)
	compteurVideo = 15
	section = 0
	
	# There are 15 videos by page
	while compteurVideo == 15 :
		compteurVideo = 0
		
		urldonneesHTML = PLUGIN_URL + "ajax/populerSliderIndex.php?serie=null&vid=null&vidToSlide="+ str(section*15) +"&playOverlay=null&classification=" + classification + "&selection=collection"
		donneesHTML = HTML.ElementFromURL(urldonneesHTML, encoding="utf-8", headers ={'cookie' : cookie})
		
		for c in donneesHTML.xpath("//div[@class='size some']"):
			id = c.find("span").get("id")
			Log("id %s" % (id))
			
			# Condition de detection de fin
			if id is None:
				break
			
			nom = c.find("span").text
			Log("nom %s" % (nom))
			
			thumbAndMore = c.find("img").get("style")
			thumb = thumbAndMore.rsplit("url(")[1].split(")")[0]
			
			# Patch pour bugs dans l'adresse des images
			if thumb[0:6] == "images" :
				urlImage = thumb.split("vignette/")[1]
				thumb = "http://image.tetesaclaques.tv/videos/"+urlImage
			Log("thumb %s" % (thumb))
			
			urlVideo = "http://video.tetesaclaques.tv/videos/" + thumb.split("/videos/")[1].rsplit(".jpg")[0] + ".flv"
			Log("urlVideo %s" % (urlVideo))
			
			dir.Append(VideoItem(urlVideo, title=nom, thumb=thumb)) 
			compteurVideo = compteurVideo + 1
			
		section = section + 1
		Log("###### nombre de video : %s" % compteurVideo)
		Log("###### section : %s" % section)
		
	return dir



