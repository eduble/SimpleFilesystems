import os, tempfile

def generateSampleDirStat():
	"""
	Subroutine which prepares a sample 'stat' structure 
	(as returned by os.stat) for a directory.
	"""
	tmpdir = tempfile.mkdtemp()
	stat_info = os.stat(tmpdir)
	os.rmdir(tmpdir)
	return stat_info
	
def generateSampleFileStat(mode, size):
	"""
	Subroutine which returns a sample 'stat' structure 
	(as returned by os.stat) for a regular file.
	"""
	fd, tmpfile = tempfile.mkstemp()
	if size > 0:
		os.write(fd, '-' * size);
	os.close(fd)
	os.chmod(tmpfile, mode)
	stat_info = os.stat(tmpfile)
	os.remove(tmpfile)
	return stat_info
	
def generateSampleSymlinkStat():
	"""
	Subroutine which returns a sample 'stat' structure 
	(as returned by os.stat) for a symlink.
	"""
	tmpdir = tempfile.mkdtemp()
	tmplink = tmpdir + '/link'
	os.symlink(tmpdir, tmplink)
	stat_info = os.lstat(tmplink)	
	os.remove(tmplink)
	os.rmdir(tmpdir)
	return stat_info
