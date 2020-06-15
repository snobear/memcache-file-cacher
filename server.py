#!/usr/bin/env python
'''
NOTES:
- concurrency handling? - see cas
- free old cache when reaching mem limit of 1000MB
- Improvements that could be made:
  - larger file handling > 50MB: streamed upload, stream to disk, then stream to memcache
  - logging
  - doc generator-friendly comments (return types, etc...)
  - 
'''

from flask import Flask, jsonify, send_file, request
from io import BytesIO
import os, sys
from cflib.cachefile import CacheFile
app = Flask(__name__)

app.config['UPLOADED_FILES_DEST'] = 'uploads'
app.config['MIN_FILE_BYTES'] = 0
app.config['MAX_FILE_BYTES'] = 52428800 # 50MB

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

def invalid_file_size_response():
    print("invalid file size")
    resp = { 'msg': "error: file size must be between %d and %d bytes" % 
        (app.config['MIN_FILE_BYTES'], app.config['MAX_FILE_BYTES']) }
    return jsonify(resp), 400

@app.route("/upload", methods=["POST"])
def upload():
    """File upload endpoint"""
    print("received file uploaded request")

    # check file size per headers
    if not cf.is_valid_filesize_in_request(request, app.config['MIN_FILE_BYTES'], app.config['MAX_FILE_BYTES']):     
        return invalid_file_size_response()

    try:
        _file = request.files['file']
    except Exception as e:
        resp = { 'msg': 'error uploading file. file not present in request' }
        return jsonify(resp), 500

    # save file to disk
    try:
        file_path, uploaded_file_checksum = \
            cf.save_file_to_disk(app.config['UPLOADED_FILES_DEST'], _file)
    except Exception as e:
        print("error saving file to disk", e)
        resp = { 'msg': 'File upload error' }
        return jsonify(resp), 500

    # check the file size on disk
    if not cf.is_valid_filesize_on_disk(file_path, app.config['MIN_FILE_BYTES'],
            app.config['MAX_FILE_BYTES']):
        return invalid_file_size_response()

    try:
        result, file_id, cached_checksum = cf.cache_file(_file.filename, file_path)
    except Exception as e:
        print("error in cache_file:", e)
        resp = { 'msg': 'File upload error' }
        return jsonify(resp), 500

    if uploaded_file_checksum != cached_checksum:
        resp = { 'msg': 'error uploading file', 'id': file_id }
        return jsonify(resp), 500
    elif result:
        resp = { 'msg': 'File uploaded successfully', 'id': file_id }
        return jsonify(resp), 200
    else:
        resp = { 'msg': 'error uploading file', 'id': file_id }
        return jsonify(resp), 500

@app.route('/download', methods=['GET'])
def download():
    """Return file reconstructed from memcache chunked values"""
    file_not_found = False

    try:
        file_id = request.args.get('id')
        print("retrieving file_id=%s" % file_id)
        meta = cf.get_stored_file_meta(file_id)
        print("stored metadata for file_id=%s [chunks,checksum]" % file_id, meta)
    except Exception as e:
        print("error retrieving file:", e)
        resp = { 'msg': "error retrieving file", 'id': file_id }
        return jsonify(resp), 500

    if not meta:
        resp = { 'msg': "file does not exist in cache", 'id': file_id }
        return jsonify(resp), 404

    chunk_count = meta[0]
    stored_checksum = meta[1]
    result_file, retrieved_file_checksum, retrieved_chunk_count = cf.get_file(file_id, chunk_count)

    if not result_file:  # no file returned
        file_not_found = True
    elif stored_checksum != retrieved_file_checksum: # validation checksum
        if retrieved_chunk_count == chunk_count:
            print("error: checksums for file_id=%s do not match, but no keys appear to have been evicted." \
                  "This should be investigated." % file_id, stored_checksum, retrieved_file_checksum)
            resp = { 'msg': "server error encountered while retrieving file", 'id': file_id }
            return jsonify(resp), 500
        else:
            # this means keys were evicted. 
            file_not_found = True
            print("error: checksums for file_id=%s do not match. stored: %s, retrieved: %s" 
                % file_id, stored_checksum, retrieved_file_checksum)
            # file is no good with missing chunks, so clean it up
            self.delete_file(file_id, chunk_count)

    if file_not_found:
        resp = { 'msg': "file not found in cache", 'id': file_id }
        return jsonify(resp), 404

    return send_file(BytesIO(result_file), as_attachment=True, attachment_filename=file_id)

if __name__ == '__main__':
    startup_checks()
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 3000), debug=True)

# TODO same TTL, pep8, one test, specific edge cases should show in response