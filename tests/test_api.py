#!/usr/bin/env python
# functional tests for the file caching api
import requests
import json
import subprocess
import re
import unittest
import os

# API_HOST='http://localhost'
API_HOST = 'http://api'  # when run via docker compose
API_PORT = 3000


class CacheTest(unittest.TestCase):
    def get_file_id(self, fname):
        """file id format in cachefile lib"""
        return re.sub('[^a-zA-Z0-9-_]', '', fname)

    def generate_random_data_file(self, size_mb):
        FNULL = open(os.devnull, 'w')
        fname = "test_%dmb.dat" % size_mb
        cmd_list = ['dd', 'if=/dev/random', "of=%s" %
                    fname, 'bs=1048576', "count=%d" % size_mb]
        a = subprocess.Popen(cmd_list, stdout=FNULL, stderr=subprocess.STDOUT)
        a.communicate()
        FNULL.close()
        return fname

    def test_upload_valid_size_file(self):
        fname = self.generate_random_data_file(25)
        file_id = self.get_file_id(fname)
        f = open(fname, 'rb')
        files = {'file': f}
        url = "%s:%d/upload" % (API_HOST, API_PORT)
        r = requests.post(url, files=files)
        f.close()

        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json(),
                         {"id": file_id, "msg": "File uploaded successfully"})

    def test_upload_toosmall_file(self):
        fname = self.generate_random_data_file(0)
        file_id = self.get_file_id(fname)
        f = open(fname, 'rb')
        files = {'file': f}
        url = "%s:%d/upload" % (API_HOST, API_PORT)
        r = requests.post(url, files=files)
        f.close()

        r_json = r.json()
        self.assertEqual(r.status_code, 400)
        self.assertIn("file size must be between", r_json['msg'])


if __name__ == '__main__':
    unittest.main()
