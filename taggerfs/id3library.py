#!/usr/bin/env python
"""
This module implements a management library for your
collection of ID3-tagged mp3 files.
"""
import os
from os.path import join
from mutagen.easyid3 import EasyID3

class ID3Library:
	"""Library of ID3-tagged mp3 files."""
	def __init__(self):
		"""Constructor."""
		self._data = {}
	
	def getTagElement(self, tag, elem):
		"""Sub-routine to get one element of an ID3 tag (i.e. artist, album, ...)."""
		value = None
		if elem in tag:
			value = tag[elem][0].encode('utf8').strip()
			if value == '':
				value = None
		return value
	
	def registerMP3File(self, path):
		"""Registers the ID3 tag of a given mp3 file into the library."""
		tag = EasyID3(path)
		artist = self.getTagElement(tag,'artist')
		album = self.getTagElement(tag,'album')
		if artist == None:
			artist = 'UnknownArtist'
		if album == None:
			album = 'UnknownAlbum'
		if artist not in self._data:
			self._data[artist] = {}
		allAlbumsOfArtist = self._data[artist]
		if album not in allAlbumsOfArtist:
			allAlbumsOfArtist[album] = set({})
		allTracksOfAlbum = allAlbumsOfArtist[album]
		allTracksOfAlbum.add(path)

	def registerMP3FilesFromDir(self, d):
		"""Registers all files in a given directory (including files in sub-directories)."""
		for dirname, dirnames, filenames in os.walk(d):
			for filename in filenames:
				if filename.endswith('.mp3'):
					print 'adding file:', filename
					path = join(dirname, filename)
					self.registerMP3File(path)
	
	def getArtists(self):
		"""Outputs the list of artists the library knows about."""
		return self._data.keys()
	
	def getAlbums(self, artist):
		"""Outputs the list of albums the library knows about for a given artist."""
		return self._data[artist].keys()
	
	def getFiles(self, artist, album):
		"""Outputs the list of files the library knows about for a given album."""
		return self._data[artist][album]
	
	def registerArtist(self, artist):
		"""Registers an artist into the library."""
		self._data[artist] = {}
	
	def registerAlbum(self, artist, album):
		"""Registers an album into the library."""
		self._data[artist][album] = set({})
	
	def update(self, fullpath, old_artist, old_album, 
				new_artist, new_album):
		"""
		Updates the data (artist & album) about a given song.
  		In-memory and in-file (i.e. the ID3 tag) data will both be updated.
		"""
		# update current hierarchy
		self._data[new_artist][new_album].add(fullpath)
		self._data[old_artist][old_album].remove(fullpath)
		# update ID3 tag
		tag = EasyID3(fullpath)
		tag['artist'] = new_artist
		tag['album'] = new_album
		tag.save()
	

