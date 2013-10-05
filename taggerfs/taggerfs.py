#!/usr/bin/env python
"""
This file implements a FUSE-based filesystem called TaggerFS.

TaggerFS allows you:
- to view a collection of mp3 files as an ID3-based tree.
- to update ID3 data by moving these files at their proper
  location in the tree.

"""

import os, sys, tempfile, fuse
from sys import argv
from errno import *
from os.path import basename
from id3library import ID3Library
from fuse import Fuse

# specify the expected FUSE API version
fuse.fuse_python_api = (0, 2)

class TaggerFS(Fuse):
	"""The FUSE main class of the TaggerFS filesystem."""
	def __init__(self, id3Library, *args, **kw):
		"""Constructor."""
		Fuse.__init__(self, *args, **kw)
		self.id3Library = id3Library
		self.initSampleStatStructures()
	
	def initSampleStatStructures(self):
		"""
		Subroutine which prepares a sample 'stat' structure 
		(as returned by os.stat) for a directory and for a symlink.
		"""
		# This filesystem only manages 2 kinds of files: 
		# directories and symlinks. 
		# We consider that all the directories will have
		# the same attributes, so we create a temporary
		# directory and record its stat structure. 
		# Same for the symlinks.
		# 1 - create a temp dir and a temp symlink
		tmpdir = tempfile.mkdtemp()
		tmplink = tmpdir + '/link'
		os.symlink(tmpdir, tmplink)
		# 2 - retrieve their attributes
		self.sample_dir_stat = os.lstat(tmpdir)	
		self.sample_link_stat = os.lstat(tmplink)	
		# 3 - clean up
		os.remove(tmplink)
		os.rmdir(tmpdir)
	
	def analysePath(self, path):
		"""
		Parse a path of the form: 
		/[<artist>[/<album>[/<basename>]]] 
		into a tuple (<artist>, <album>, <mp3_basename>)
		(some or all tuple entries may be 'None')
		"""
		if path == '/':
			return None, None, None
		tokens = path.split("/")[1:]
		while len(tokens) < 3:
			tokens.append(None)
		return tuple(tokens)	# (artist, album, mp3_basename)
	
	def getdircontents(self, path):
		"""
		Returns the list of entries in a given directory.
		"""
		artist, album, mp3_basename = self.analysePath(path)
		l = [ '.', '..' ]
		if artist == None:
			# list artists
			l.extend(self.id3Library.getArtists())
		elif album == None:
			# list albums of an artist
			l.extend(self.id3Library.getAlbums(artist))
		elif mp3_basename == None:
			# list songs of an album
			l.extend([basename(f) for f in \
				self.id3Library.getFiles(artist, album)])
		return l
	
	def getfullpath(self, artist, album, mp3_basename):
		"""
		Returns the full path of a given song.
		"""
		for f in self.id3Library.getFiles(artist, album):
			if basename(f) == mp3_basename:
				return f
	
	def getattr(self, path):
		"""FUSE getattr() operation."""
		if path.count('/') > 3:
			return -ENOENT	# no such file or dir
		artist, album, mp3_basename = self.analysePath(path)
		if artist != None and \
				artist not in self.getdircontents('/'):
			return -ENOENT	# no such file or dir
		if album != None and \
				album not in self.getdircontents('/' + artist):
			return -ENOENT	# no such file or dir
		if mp3_basename != None and \
				mp3_basename not in self.getdircontents(\
						'/' + artist + '/' + album):
			return -ENOENT	# no such file or dir
		if mp3_basename == None:
			# this is a directory
			return self.sample_dir_stat
		else:
			# this is a symlink
			return self.sample_link_stat

	def readlink(self, path):
		"""FUSE readlink() operation."""
		artist, album, mp3_basename = self.analysePath(path)
		return self.getfullpath(artist, album, mp3_basename)

	def readdir(self, path, offset):
		"""FUSE readdir() operation."""
		for e in self.getdircontents(path):
			yield fuse.Direntry(e)
	
	def rename(self, old_path, new_path):
		"""FUSE rename() operation."""
		old_artist, old_album, old_mp3_basename = self.analysePath(old_path)
		new_artist, new_album, new_mp3_basename = self.analysePath(new_path)
		if old_mp3_basename == None or new_mp3_basename == None or \
				old_mp3_basename != new_mp3_basename:
			# only moving a symlink is allowed
			return -EPERM
		fullpath = self.getfullpath(old_artist, old_album, old_mp3_basename)
		self.id3Library.update(fullpath, old_artist, old_album, 
				new_artist, new_album)

	def mkdir(self, path, mode):
		"""FUSE mkdir() operation."""
		artist, album, mp3_basename = self.analysePath(path)
		if artist == None:	# mkdir /<mount_point> ??
			return -EINVAL
		elif album == None:
			# register an artist
			if artist in self.id3Library.getArtists():
				return -EEXIST # artist already exists
			else:
				self.id3Library.registerArtist(artist)
		elif mp3_basename == None:
			# register an album
			if album in self.id3Library.getAlbums(artist):
				return -EEXIST # album already exists
			else:
				self.id3Library.registerAlbum(artist, album)
		else:
			return -EPERM


if __name__ == '__main__':
	usage = "TaggerFS: view and manage your mp3 collection as an ID3-based tree.\n" + \
		argv[0] + " <base_mp3_dir> <mount_point>"
	
	if len(sys.argv) < 3:
		print usage
		sys.exit()
	
	library_dir = sys.argv[1]
	mount_point = sys.argv[2]
	
	library = ID3Library()
	library.registerMP3FilesFromDir(library_dir)
	
	server = TaggerFS(library, usage=usage)
	server.fuse_args.mountpoint = mount_point
	server.multithreaded = False
	server.fuse_args.setmod('foreground')
	server.main()

