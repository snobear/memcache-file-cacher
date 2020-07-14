# File Cache API

A REST API that allows a user to:

- upload a file that is then chunked and cached in memcache
- retrieve/download a cached file

All py source files are pep8 compliant per `pycodestyle`.

## Build and run

From the top level repo directory, run:

```
docker-compose up --build
```

This will fire up containers for:
- memcache
- the api service
- tests (two functional tests are auto run against the api)

## Usage

### Upload a file to be cached

```
curl -X POST http://localhost:3000/upload -F file=@somefile.dat
```

This calls returns the file `id` which can be used in subsequent calls to download the file. 

### Download a file

```
curl -XGET "http://localhost:3000/download?id=testdat" --output downloadtest.dat
```

The library handles checksum validation, but for a self sanity check:

```
shasum somefile.dat downloadtest.dat
```

### Improvements
Ideas on various improvements to make

- more testing of chunk sizes to find the most efficient
- disable CAS if it's not a requirement to shave a few bytes off each item
- more efficient file handling: streamed upload, stream to disk, then stream to memcache instead of reading into memory.
- doc generator-friendly comments (return types, etc...)
- re: API responses, how abstracted should the user be? For example, should we respond with "file not found in cache" or "file chunks evicted from cache". Depends on who the user is.
