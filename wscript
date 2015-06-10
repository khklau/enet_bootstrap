import fnmatch
import hashlib
import os
import shutil
import stat
import subprocess
import tarfile
import urllib
import zipfile
from waflib import Logs
from waflib.extras.preparation import PreparationContext
from waflib.extras.build_status import BuildStatus
from waflib.extras.filesystem_utils import removeSubdir
from waflib.extras.mirror import MirroredTarFile

__downloadUrl = 'http://enet.bespin.org/download/%s'
__srcFile = 'enet-1.3.13.tar.gz'
__srcSha256Checksum = '\xe3\x60\x72\x02\x1f\xaa\x28\x73\x1b\x08\xc1\x5b\x1c\x3b\x5b\x91\xb9\x11\xba\xf5\xf6\xab\xcc\x7f\xe4\xa6\xd4\x25\xab\xad\xa3\x5c'
__srcDir = 'src'

def options(optCtx):
    optCtx.load('dep_resolver')

def prepare(prepCtx):
    prepCtx.options.dep_base_dir = prepCtx.srcnode.find_dir('..').abspath()
    prepCtx.load('dep_resolver')
    status = BuildStatus.init(prepCtx.path.abspath())
    if status.isSuccess():
	prepCtx.msg('Preparation already complete', 'skipping')
	return
    srcPath = os.path.join(prepCtx.path.abspath(), __srcDir)
    file = MirroredTarFile(
	    __srcSha256Checksum,
	    __downloadUrl % __srcFile,
	    os.path.join(prepCtx.path.abspath(), __srcFile))
    prepCtx.msg('Synchronising', file.getSrcUrl())
    if file.sync(10):
	prepCtx.msg('Saved to', file.getTgtPath())
    else:
	prepCtx.fatal('Synchronisation failed')
    extractDir = 'enet-1.3.13'
    removeSubdir(prepCtx.path.abspath(), __srcDir, extractDir, 'lib', 'include')
    prepCtx.start_msg('Extracting files to')
    file.extract(prepCtx.path.abspath())
    os.rename(extractDir, __srcDir)
    prepCtx.end_msg(srcPath)
    for dirPath, subDirList, fileList in os.walk(os.path.join(srcPath, 'scripts')):
	for file in fileList:
	    os.chmod(os.path.join(dirPath, file), stat.S_IXUSR | stat.S_IRUSR | stat.S_IWUSR)

def configure(confCtx):
    confCtx.load('dep_resolver')
    status = BuildStatus.init(confCtx.path.abspath())
    if status.isSuccess():
	confCtx.msg('Configuration already complete', 'skipping')
	return
    srcPath = os.path.join(confCtx.path.abspath(), __srcDir)
    os.chdir(srcPath)
    if os.name == 'posix':
	returnCode = subprocess.call([
		'sh',
		os.path.join(srcPath, 'configure'),
		'--prefix=%s' % confCtx.srcnode.abspath()])
	if returnCode != 0:
	    confCtx.fatal('Configure failed: %d' % returnCode)
    elif os.name == 'nt':
	# Nothing to do, just use the provided VS solution
	return
    else:
	confCtx.fatal('Unsupported OS %s' % os.name)

def build(buildCtx):
    status = BuildStatus.load(buildCtx.path.abspath())
    if status.isSuccess():
	Logs.pprint('NORMAL', 'Build already complete                   :', sep='')
	Logs.pprint('GREEN', 'skipping')
	return
    srcPath = os.path.join(buildCtx.path.abspath(), __srcDir)
    os.chdir(srcPath)
    if os.name == 'posix':
	returnCode = subprocess.call([
		'make',
		'install'])
    elif os.name == 'nt':
	returnCode = subprocess.call([
		'devenv.com',
		os.path.join(srcPath, 'enet.dsp')])
    else:
	confCtx.fatal('Unsupported OS %s' % os.name)
    if returnCode != 0:
	buildCtx.fatal('Build failed: %d' % returnCode)
    status.setSuccess()
