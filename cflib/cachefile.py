"""
Memcache file chunking+caching library
"""
import hashlib
from pymemcache.client import base
import re
import os
from werkzeug.utils import secure_filename

# max chunk size
#CHUNK_SIZE = 999900
#CHUNK_SIZE = 262144
# note: I assumed max item size was 1MB, but it appears to be 512k?
# after testing and monitoring "stat slabs", this was the "winner" efficiency-wise
CHUNK_SIZE = 524288

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

    def __delete_temp_file(self, file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            print("error removing temp file at %s" % file_path, e)
            pass

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

        self.__delete_temp_file(file_path)

        return chunk_count, file_hash.hexdigest()
 
    """
    Public methods
    """
    def delete_file(self, file_id, chunk_count):
        """Remove a file from memcached - delete all chunks and metadata"""
        print("deleting file cache for file_id=%s" % file_id)

        # delete all file chunks
        for idx in range(0, int(chunk_count)):
            self.client.delete("%s_%d" % (file_id, idx), False)

        # delete file metadata
        self.client.delete("%s_chunk_count" % file_id, False)
        self.client.delete("%s_checksum" % file_id, False)

        return True

    def get_file(self, file_id, chunk_count):
        """
        Combine chunks from memcache.
        Returns the full file, the file's computed checksum, and chunk count
        """
        retrieved_chunk_count = 0
        try:
            retrieved_file_hash = hashlib.md5()
            _file = b''
            # combine chunks
            for idx in range(0, int(chunk_count)):
                chunk = self.client.get("%s_%d" % (file_id, idx))
                _file = _file + chunk
                retrieved_file_hash.update(chunk)
                retrieved_chunk_count += 1
        except Exception as e:
            # file cache has likely been evicted (we should catch specific exceptions here)
            _file = None
            print("error retrieving file", e)
            pass

        return _file, retrieved_file_hash.hexdigest(), retrieved_chunk_count

    def is_valid_filesize_in_request(self, request, min_bytes = 0, max_bytes = 52428800):
        """
        Check size of file in upload request
        """
        # allow for extra bytes added in request
        adjusted_max_bytes = max_bytes + 1000

        if not request.content_length:
            # we can't assume content-length will be set so don't fail
            return True
        else:
            file_size_bytes = request.content_length
            print("uploaded file content-length:", file_size_bytes)
            if (file_size_bytes > min_bytes) and (file_size_bytes <= adjusted_max_bytes):
                return True

        return False

    def is_valid_filesize_on_disk(self, file_path, min_bytes = 0, max_bytes = 52428800):
        """
        Check size of file on disk.
        This is used as a fallback if the safer is_valid_filesize() cannot be performed,
        or as an extra confirmation in case content-length is spoofed.
        Returns True if file is within size limit, otherwise False
        """
        try:
            file_size_bytes = os.path.getsize(file_path)
        except Exception as e:
            raise e

        if (file_size_bytes > min_bytes) and (file_size_bytes <= max_bytes):
            return True

        return False

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
        file_id = None

        # first delete existing file from cache
        try:
            file_id = self.__get_file_id(filename)
            print("deleting cached file_id=%s if it exists" % file_id)
            meta = self.get_stored_file_meta(file_id)
            if meta:
                self.delete_file(file_id, meta[0])
        except Exception as e:
            print("delete error for file_id=%s" % file_id, e)
            return False, file_id, None

        # chunk and store file
        try:
            print("caching file at %s" % file_path)
            chunk_count, checksum = self.__chunk_and_store(file_id, file_path)
        except Exception as e:
            print("chunk and store error for file_id=%s" % file_id, e)
            return False, file_id, None

        # store file metadata
        try:
            self.__set_value("%s_checksum" % file_id, checksum)
            self.__set_value("%s_chunk_count" % file_id, chunk_count)
        except Exception as e:
            print("error setting file metadata for file_id=%s" % file_id, e)
            # file cache is no good without metadata, so clean up keys if have the chunk count
            if chunk_count:
                self.delete_file(file_id, chunk_count)
            return False, file_id, None

        return True, file_id, checksum

    def save_file_to_disk(self, upload_dir, file_upload_object):
        """
        Save uploaded file to disk.
        Return file path and its checksum
        """ 
        try:
            raw_filename = file_upload_object.filename
            safe_filename = secure_filename(raw_filename)
            file_path = os.path.join(upload_dir, safe_filename)
            print("saving uploaded file to disk at %s" % file_path)
            file_upload_object.save(file_path)

            # stream from file to calculate checksum
            # safer/more efficient for larger file handling
            file_hash = hashlib.md5()
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(8192)
                    file_hash.update(chunk)
                    if len(chunk) == 0:
                        break
            checksum = file_hash.hexdigest()
        except Exception as e:
            print("error saving file to disk filename=%s" % raw_filename, e)
            self.__delete_temp_file(file_path)
            raise e

        return file_path, checksum
