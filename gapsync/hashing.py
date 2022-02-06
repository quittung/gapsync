import os, hashlib

def hash_file(filename: str, buffer: int = 1024 * 1024) -> str:
    hash = hashlib.sha256()
    with open(filename, 'rb') as f:
        while True:
            data = f.read(buffer)
            if not data:
                break
            hash.update(data)

    return hash.hexdigest()

class HashFileSingleParam(object):
    """enables usage of hash file with a single parameter"""
    def __init__(self, buffer_size: int = 1024 * 1024, verbose: bool = False) -> None:
        self.buffer_size = buffer_size
        self.verbose = verbose 
    
    def __call__(self, filename: str) -> str:
        hash = hash_file(filename, self.buffer_size)
        if self.verbose: print("{} - {}\n".format(hash, filename), end="")
        
        return hash

def hash_folder(top_dir: str, pool = None, verbose: bool = False) -> dict:
    file_dict = {}
    top_dir = os.path.normpath(top_dir)
    
    files = [os.path.join(root, file) for root, dirs, files in os.walk(top_dir) for file in files]

    
    hash_file_sp = HashFileSingleParam(verbose)
    if pool: 
        hashes = pool.map(hash_file_sp, files)
    else:
        hashes = list(map(hash_file_sp, files))

    files = [file[len(top_dir):] for file in files]
    files = [file.replace("\\", "/") for file in files]
    files = [file[1:] if file[0] == "/" else file for file in files]
    file_dict = dict(zip(files, hashes))
    
    return file_dict
