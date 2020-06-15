#!/usr/bin/env bash
# rough script to generate a bunch of data files, upload, then download and verify checksum
# NOTEs:
# check slab alloc: 
#     echo "stats slabs" | nc localhost 11211 | egrep "chunk_size|chunks_per_page|total_pages|total_malloced"                                  (git)-[ingress01]
filecount=5
outdir=load_test
mb=10

rm -rf $outdir
mkdir -p $outdir

echo "generating data files"
for i in $(seq 1 ${filecount}); do
    dd if=/dev/urandom of=${outdir}/test${i}.dat bs=1048576 count=$mb
done

echo "uploading data files"
for i in $(seq 1 ${filecount}); do
    curl -X POST http://localhost:3000/upload -F file=@${outdir}/test${i}.dat;
done

echo "download cached files"
for i in $(seq 1 ${filecount}); do
    curl -XGET "http://localhost:3000/download?id=test${i}dat" --output ${outdir}/dl_test${i}.dat
done

echo "checking checksums of original vs downloaded files"
for i in $(seq 1 ${filecount}); do
    unset orig dl
    ofile=${outdir}/test${i}.dat
    dfile=${outdir}/dl_test${i}.dat

    orig=$(shasum ${ofile})
    dl=$(shasum ${dfile})

    if [[ "${orig}" != "${dl}" ]]; then
        echo "Original file ${outdir}/test${i}.dat and downloaded file ${outdir}/dl_test${i}.dat checksums do no match"
        echo original: $orig
        echo downlded: $dl
    fi
done

# cleanup
#rm -rf $outdir