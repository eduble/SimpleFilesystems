#!/usr/bin/env python
"""
This file implements a FUSE-based filesystem related to 
an article published in GNU/Linux magazine.
I doubt it could ever be useful for anything else. :)
"""

from sys import argv, exit, path as sys_path
from os.path import dirname, join as path_join

top_dir = path_join(dirname(__file__), '..')
sys_path.append(path_join(top_dir, 'common'))

import filestat, tempfile, fuse, math, stat
from errno import *
from fuse import Fuse

# specify the expected FUSE API version
fuse.fuse_python_api = (0, 2)

FILES = [ "pose_renfort", "stock", "pieces_ok" ]
STOCK_INIT = 40000
READ_SIZE = 10 
READ_STRING_FORMAT = '%' + str(READ_SIZE) + 's'

class StockEngine(object):
	def __init__(self):
		self.stock = STOCK_INIT
		self.pieces_ok = 0
	
	def pose_renfort(self, x, y):
		if self.stock == 0:
			return False
		self.stock -= 1
		if math.sqrt(x*x+y*y) < 1:
			self.pieces_ok += 1
		return True

class CharpenteFS(Fuse):
	"""The FUSE main class of the CharpenteFS filesystem."""
	def __init__(self, *args, **kw):
		"""Constructor."""
		Fuse.__init__(self, *args, **kw)
		self.initSampleStatStructures()
		self.stock_engine = StockEngine()
	
	def initSampleStatStructures(self):
		"""
		Subroutine which prepares a sample 'stat' structure 
		(as returned by os.stat) for a readable file,
		a writable file and a directory.
		"""
		self.sample_dir_stat = filestat.generateSampleDirStat()
		self.sample_wr_only_stat = filestat.generateSampleFileStat(
			stat.S_IWUSR, # write-only
			0
		)
		self.sample_rd_only_stat = filestat.generateSampleFileStat(
			stat.S_IRUSR, # read-only
			READ_SIZE
		)
	
	def getattr(self, path):
		"""FUSE getattr() operation."""
		if path == '/':
			return self.sample_dir_stat
		if path.lstrip('/') not in FILES:
			return -ENOENT	# no such file or dir
		if path == '/pose_renfort':
			return self.sample_wr_only_stat
		else: # the 2 other files are read-only
			return self.sample_rd_only_stat
	
	def readdir(self, path, offset):
		"""FUSE readdir() operation."""
		for e in FILES:
			yield fuse.Direntry(e)
	
	def open(self, path, flags):
		return 0
	
	def read(self, path, size, offset):
		if path == '/pieces_ok':
			return self.read_from_int(
				self.stock_engine.pieces_ok, size, offset)
		else: 	# /stock
			return self.read_from_int(
				self.stock_engine.stock, size, offset)
	
	def read_from_int(self, int_value, size, offset):
		s = READ_STRING_FORMAT % (str(int_value) + '\n')
		if offset < len(s):
			if (offset + size) > len(s):
				size = len(s) - offset
			return s[offset:(offset + size)]
		else:
			return ''
	
	def release(self, path, flags):
		return 0
	
	def pose_renfort_input(self, buf):
		try:
			t = tuple(float(f) for f in buf.split())	
		except:
			return -EINVAL
		if len(t) != 2:
			return -EINVAL
		for x_or_y in t:
			if x_or_y > 1 or x_or_y < 0:
				return -EINVAL
		if self.stock_engine.pose_renfort(*t):
			return len(buf)  # ok
		else:
			return -EINVAL
	
	def write(self, path, buf, offset):
		return self.pose_renfort_input(buf)
	
	def utime(self, path, times):
		return 0
	
	def truncate(self, path, length):
		return 0

		

if __name__ == '__main__':
	usage = "CharpenteFS: le filesystem du charpentier.\n" + \
		argv[0] + " <mount_point>"
	
	if len(argv) < 2:
		print usage
		exit()
	
	mount_point = argv[1]
	
	server = CharpenteFS(usage=usage)
	server.fuse_args.mountpoint = mount_point
	server.multithreaded = False
	server.fuse_args.setmod('foreground')
	server.fuse_args.add('default_permissions')
	server.fuse_args.add('debug')
	server.main()

