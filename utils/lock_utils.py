import fcntl
import threading

# ブラウザの初期化
LOCK_FILE = '/tmp/chrome-user-data.lock'
BROWSER_ACCESS_LOCK = threading.Lock()

def acquire_lock(lock_file):
    fd = open(lock_file, 'w')
    fcntl.flock(fd, fcntl.LOCK_EX)
    return fd

def release_lock(fd):
    fcntl.flock(fd, fcntl.LOCK_UN)
    fd.close()