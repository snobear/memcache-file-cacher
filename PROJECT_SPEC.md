# Zapier SRE Skills Interview

## Project Details

Please consider this document as a set of requirements, and deliver the code necessary to fulfill these requirements. If a requirement seems ambiguous, state your understanding of the requirements in a readme or inline comments along with your solution.

## Scenario

Your mission is to write library that will accept a large file (somewhere between 5MB and 50MB) as an input and store it in Memcache. Once stored, the library will then be used to retrieve the file from Memcache and return it.

Once your library for storing and retrieving files is written, you will then write a small HTTP API (REST, JSON, etc) to accept and store files posted from an HTTP Client (browser, curl). Once stored, the HTTP API will then be used to retrieve the files with a followup request.

---

You might be asking "what's the catch?" 

Well, using the default slab size, Memcached can only store up to 1MB per key. That means you'll have to implement some means of chunking the file to store it in Memcache.

Further, Memcache can evict keys when it runs out of memory. A complete solution should detect these cases and handle them appropriately.

## Deliverables

There are three deliverables for this project:

1. A small library to store and retrieve large files in Memcache
2. An HTTP API that can be used to interact with the library 

## Specs

### Library:

* Your library should be small and self contained.
* Your library should use a similar memcache client and any other libraries required.
* Your library should accept any file size from 0 to 50MB. Files larger than 50MB should be rejected.
* Your library should accept a file, chunk it, and store as bytes in Memcache with a minimum amount of overhead. 
* Your library should retreive a file's chunks from Memcache and return a single stream of bytes. 
* Your library may chunk the file in any way appropriate.
* Your library can key the chunks in any way appropriate.
* Your library should check for file consistency to ensure the data retrieved is the same as the original data stored.
* Your library should handle edge cases appropriately by raising an Exception or similar. Some examples of edge cases may include: trying to store a file that already exists, trying to retrieve a file that does not exist, or when a file retrieved is inconsistent/corrupt. 
* Your library should have at least one test.

**NOTE:** you can use this command to generate a 50MB file of random data if needed:

```bash
dd if=/dev/urandom of=bigoldfile.dat bs=1048576 count=50
```

### API:

* You may use a framework for implementing your API (`django`, `flask`, etc)
* Your API should accept a POST request with file contents in the payload and store it using your library. It may be convenient to return an identifier used for retrieval at a later time.
* Your API should accept a GET request with a file name / identifier and retrieve it using your library. The file contents should be retured in the response. 
* Your API should handle edge cases appropriately (return an error response, etc) when a file does not exist or is not consistent.
* Your API should have at least one test.


## How we'll review your code:

We did this project ourselves so we should have a good time comparing versions. Once complete, we'll be reviewing your code for:

* **Completeness** - Did you complete an implementation that meets the requirements?
* **Correctness** - Does your solution perform the correct functionality? (i.e., Does it work when we run it?)
* **Clarity** - Can we understand your code and the decisions you made in the implementation?
* **Code Quality** - Is your code well structured and clean? Does it use common idioms? Does it adhere to PEP8?

 
## Project time limit:

This project will have no time limit, however we ask that you don't spend an excessive amount of time on it. We're not looking for a perfect solution but rather a rough representation of what you can do on a short time frame. 

## Once finished

* To deliver your project, simply commit your final work and push to the `project` branch of the private Github repo provided by Zapier. 

* Open a pull request to merge your `project` branch to `master`.

  * Make sure to add a description to your pull request with any details you want to provide.

  * At the very least, It is useful to provide a description of how to deploy / run your project.

* If you finish early and want to submit unfinished ideas, please add those to other branches. 

