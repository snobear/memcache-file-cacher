#!/usr/bin/env python
'''
NOTES:
- 0 byte file
- test for < 0 or > 50MB
- concurrency handling? - see cas
- free old cache when reaching mem limit of 1000MB
- NICETOHAVE:
  - larger file handling: stream to disk, then stream to memcache
  - logging
'''

from flask import Flask, jsonify, send_file, request
from werkzeug.utils import secure_filename
from io import BytesIO
import os, sys
from cflib.cachefile import CacheFile
app = Flask(__name__)

app.config['UPLOADED_FILES_DEST'] = 'uploads'
app.config['MIN_FILE_BYTES'] = 0
app.config['MAX_FILE_BYTES'] = 52428800

cf = CacheFile()

def startup_checks():
    """
    Run some pre-start checks:
    - uploads directory exists and is writeable by flask
    """
    if not os.path.exists(app.config['UPLOADED_FILES_DEST']):
        print("error: uploads directory %s does not exist." % app.config['UPLOADED_FILES_DEST'])
        sys.exit(1)

    if not os.access(app.config['UPLOADED_FILES_DEST'], os.R_OK | os.W_OK | os.X_OK):
        print("error: uploads directory %s is not writeable by web server." % app.config['UPLOADED_FILES_DEST'])
        sys.exit(1)

@app.route("/upload", methods=["POST"])
def upload():
    """File upload endpoint"""
    try:
        _file = request.files['file']
    except Exception as e:
        resp = { 'msg': 'error uploading file. file not present in request' }
        return jsonify(resp), 500

    # save file to disk
    try:
        raw_filename = _file.filename
        safe_filename = secure_filename(raw_filename)
        file_path = os.path.join(app.config['UPLOADED_FILES_DEST'], safe_filename)
        _file.save(file_path)
    except Exception as e:
        print("error saving file", e)
        resp = { 'msg': 'File upload error' }
        return jsonify(resp), 500

    # ensure file is within size limits
    if not cf.is_valid_filesize(file_path, app.config['MIN_FILE_BYTES'], app.config['MAX_FILE_BYTES']):
        resp = { 'msg': "error: file size must be between %d and %d bytes" % 
            (app.config['MIN_FILE_BYTES'], app.config['MAX_FILE_BYTES']) }
        return jsonify(resp), 400

    try:
        result, file_id = cf.cache_file(raw_filename, file_path)
    except Exception as e:
        print("error in cache_file:", e)
        resp = { 'msg': 'File upload error' }
        return jsonify(resp), 500

    if result:
        resp = { 'msg': 'File uploaded successfully', 'id': file_id }
        return jsonify(resp), 200
    else:
        resp = { 'msg': 'error uploading file', 'id': file_id }
        return jsonify(resp), 500

@app.route('/download', methods=['GET'])
def download():
    """Return file reconstructed from memcache chunked values"""
    try:
        file_id = request.args.get('id')
        print("retrieving file_id=%s" % file_id)
        meta = cf.get_stored_file_meta(file_id)
    except Exception as e:
        print("error retrieving file:", e)
        resp = { 'msg': "error retrieving file with id %s" % file_id }
        return jsonify(resp), 500

    if not meta:
        resp = { 'msg': "file with id %s not found" % file_id }
        return jsonify(resp), 404

    chunk_count = meta[0]
    stored_checksum = meta[1]
    result_file, retrieved_file_checksum = cf.get_file(file_id, chunk_count)

    if stored_checksum != retrieved_file_checksum:
        # this situation is a critical issue that would essentially be a bug
        print("error: checksums don't match:", stored_checksum, retrieved_file_checksum)
        resp = { 'msg': "server error retrieving file with id %s" % file_id }
        return jsonify(resp), 500

    return send_file(BytesIO(result_file), as_attachment=True, attachment_filename=file_id)

if __name__ == '__main__':
    startup_checks()
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 3000), debug=True)
