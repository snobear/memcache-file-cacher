"""
Memcache file chunking+caching library
"""
import hashlib
from pymemcache.client import base
import re
import os

# max chunk size. Use a little less than 1B slab default max to allow room for overhead
# Suggested by Guido van Rossum - https://stackoverflow.com/a/9143912/193210
CHUNK_SIZE = 950000

class CacheFile(object):
    def __init__(self):
        """Connect to memcache"""
        # this should be in a config file
        self.client = base.Client(('localhost', 11211))

    def __set_value(self, key, chunk):
        """Write a value to memcache"""
        try:
            self.client.set(key, chunk)
        except Exception as e:
            print("set_value exception" % e)
            raise e

    def __get_file_id(self, fname):
        """
        Return sanitized filename.
        This is very basic and pretty restrictive. memcache allows more
        characters than this set, but just illustrates the need to sanitize user input.
        """
        return re.sub('[^a-zA-Z0-9-_]', '', fname)

    def __chunk_and_store(self, filename, file_path):
        """Read file from disk and store chunks in memcache. Return # of chunks stored"""
        chunk_count = 0
        file_hash = hashlib.md5()

        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if len(chunk) == 0:
                    break
                self.__set_value("%s_%d" % (filename, chunk_count), chunk)
                file_hash.update(chunk)
                chunk_count += 1   

        # delete temp file
        try:
            os.remove(file_path)
        except Exception as e:
            print("error removing temp file at %s" % file_path, e)
            pass

        return chunk_count, file_hash.hexdigest()

    def get_file(self, file_id, chunk_count):
        """Combine chunks from memcache and return entire file"""
        try:
            retrieved_file_hash = hashlib.md5()
            _file = b''
            # combine chunks
            for idx in range(0, int(chunk_count)):
                chunk = self.client.get("%s_%d" % (file_id, idx))
                retrieved_file_hash.update(chunk)
                _file = _file + chunk
    
        except Exception as e:
            print("error retrieving file:" % e)
            raise e
    
        return _file, retrieved_file_hash.hexdigest()
    #LEFTOFF: 
    # overwrite file if it exists and has different checksum
    def delete_file(self, file_id):
        """Remove a file from memcached - delete all chunks and metadata"""
        print("caching file at %s" % file_path)

    def is_valid_filesize(self, file_path, min_bytes = 0, max_bytes = 52428800):
        """Returns True if file is within size limit, otherwise False"""
        try:
            file_size_bytes = os.path.getsize(file_path)
        except Exception as e:
            raise e

        if (file_size_bytes <= min_bytes) or (file_size_bytes > max_bytes):
            return False
        
        return True

    def get_stored_file_meta(self, file_id):
        """
        If file exists, return chunk count and checksum for stored file.
        Returns False if file does not exist in memcached
        """
        chunk_count = self.client.get("%s_chunk_count" % file_id)
        if chunk_count is None:
            return False
    
        stored_checksum = self.client.get("%s_checksum" % file_id)
        if stored_checksum is None:
            return False

        return [chunk_count.decode("utf-8"), stored_checksum.decode("utf-8")]

    def cache_file(self, filename, file_path):
        """Takes a file upload object and chunks+stores in memcache"""
        print("caching file at %s" % file_path)
        file_id = None

        try:
            file_id = self.__get_file_id(filename)
            chunk_count, checksum = self.__chunk_and_store(file_id, file_path)
        except Exception as e:
            print("chunk and store error for file_id=%s" % file_id, e)
            return False, file_id

        # store file metadata
        try:
            self.__set_value("%s_checksum" % file_id, checksum)
            self.__set_value("%s_chunk_count" % file_id, chunk_count)
        except:
            print("error setting file metadata for file_id=%s" % file_id, e)
            return False, file_id
    
        return True, file_id