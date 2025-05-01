#!/usr/bin/python

import sys
import os
import random

version = "\nHubsan Bull-Shit decoder/encoder, ver 0.2\n"
err1 = "Cannot open the file\n"
err2 = "The file size is too small\n"
err3 = "The file data is wrong\n"

def decodeBytes(b):
    inlen = len(b)
    print "Encoded firmware size", inlen

    #offset to the encoded firmware header
    print "Header offset bytes:", ord(b[1]), ord(b[3])
    hdr_off = ord(b[1]) + ((~ord(b[3])) & 255)*256
    if inlen < hdr_off:
        print "inlen:",inlen," hdr_off:", hdr_off
        print err3
        return ""
    print "Header offset:", hdr_off
    #calculate firmware size (error if > 2080800)
    fwsize = ord(b[hdr_off + 5]) + (ord(b[hdr_off + 7]) << 8) + (ord(b[hdr_off + 9]) << 16)
    
    if inlen < hdr_off + 36 + fwsize:
        print err3
        print "inlen:",inlen, " hdr_off + 36 + fwsize:", hdr_off + 36 + fwsize
        return ""
    print "Decoded firmware size:", fwsize

    #Firmware checksum
    fw_sum = ord(b[hdr_off + 12]) + (ord(b[hdr_off + 13]) << 8)


    enc_table = [ord(b[hdr_off + 14]),\
    ord(b[hdr_off + 15]),\
    ord(b[hdr_off + 16]),\
    ord(b[hdr_off + 17]),\
    ord(b[hdr_off + 18]),\
    ord(b[hdr_off + 19]),\
    ord(b[hdr_off + 20])]

    i = 0
    enc_table_off = 0
    fw_off = hdr_off + 36

    fw = ""
    sum = 0
    while i < fwsize:
      b1 = ord(b[fw_off])
      b2 = ord(b[fw_off + 1])
      fw_off = fw_off + 2
      k = i & 3
      nb = 0
      if k == 0:
        nb = (((b1 & 0xF0) >> 4) | ((b2 & 0x0F) << 4)) ^ enc_table[enc_table_off]
      elif k == 1:
        nb = (((b1 & 0xF0) >> 4) | (b2 & 0xF0)) ^ enc_table[enc_table_off]
      elif k == 2:
        nb = ((b1 & 0x0F) | ((b2 & 0x0F) << 4)) ^ enc_table[enc_table_off]
      elif k == 3:
        nb = ((b1 & 0x0F) | (b2 & 0xF0)) ^ enc_table[enc_table_off]
      enc_table_off = enc_table_off + 1
      if enc_table_off >= 7:
        enc_table_off = 0
      i = i + 1
      nb = (~nb) &0xFF
      sum = (sum + nb) & 0xFFFF
      fw = fw + chr(nb)
    #
    if sum == fw_sum:
        print "Checksum Ok.", fw_sum
    else:
        print "Checksum error!", sum, fw_sum
        return ""
    if ord(fw[53]) == 17:
        print "This is Zino Pro firmware"
    else:
        print "This is original Zino firmware"
    return fw

def encodeBytes(b):
    #print "Encoding is not implemented yet :)"
    random.seed(117)
    hdr_off = int(4 + 255*random.random())
    enc_table = []
    for i in range(7):
        enc_table.append(int(256*random.random()) & 0xFF)
    fwsize = len(b);
    fw = []
    for i in range(hdr_off + 36 + 2*fwsize):
        fw.append(int(256*random.random()))
    fw_off = hdr_off + 36
    i = 0
    fw_sum = 0
    enc_table_off = 0
    while i < fwsize:
        cb = ord(b[i]) #current input byte
        fw_sum = (fw_sum + cb) & 0xFFFF
        cb = (~cb) & 0xFF
        cb = (cb ^ enc_table[enc_table_off]) & 0xFF
        k = i & 3
        #
        rb1 = fw[fw_off]
        rb2 = fw[fw_off + 1]
        #calc two output bytes for cb
        if k == 0:
          #nb = ((b1 & 0xF0) >> 4) | ((b2 & 0x0F) << 4)
          b1 = ((cb << 4) & 0xF0) | (rb1 & 0x0F)
          b2 = ((cb >> 4) & 0x0F) | (rb2 & 0xF0)
        elif k == 1:
          #nb = ((b1 & 0xF0) >> 4) | (b2 & 0xF0)
          b1 = ((cb << 4) & 0xF0) | (rb1 & 0x0F)
          b2 = (cb & 0xF0) | (rb2 & 0x0F)
        elif k == 2:
          #nb = (b1 & 0x0F) | ((b2 & 0x0F) << 4)
          b1 = (cb & 0x0F) | (rb1 & 0xF0)
          b2 = ((cb & 0xF0) >> 4) | (rb2 & 0xF0)
        elif k == 3:
          #nb = (b1 & 0x0F) | (b2 & 0xF0)
          b1 = (cb & 0x0F) | (rb1 & 0xF0)
          b2 = (cb & 0xF0) | (rb2 & 0x0F)
        #
        enc_table_off = enc_table_off + 1
        if enc_table_off >= 7:
          enc_table_off = 0
        fw[fw_off] = b1
        fw[fw_off + 1] = b2
        i = i + 1
        fw_off = fw_off + 2
    #save encode table
    for i in range(7):
        fw[hdr_off + 14 + i] = enc_table[i]
    #save checksum
    #fw_sum = ord(b[hdr_off + 12]) + (ord(b[hdr_off + 13]) << 8)
    print "Checksum: ", fw_sum
    fw[hdr_off + 12] = fw_sum & 0xFF
    fw[hdr_off + 13] = (fw_sum >> 8) & 0xFF
    #save firmware size
    #fwsize = ord(b[hdr_off + 5]) + (ord(b[hdr_off + 7]) << 8) + (ord(b[hdr_off + 9]) << 16)
    print "Encoded size:", hdr_off + 36 + 2*fwsize
    print "Header offset:", hdr_off
    fw[hdr_off + 5] = fwsize & 0xFF
    fw[hdr_off + 7] = (fwsize >> 8) & 0xFF
    fw[hdr_off + 9] = (fwsize >> 16) & 0xFF
    #save header offset
    #hdr_off = ord(b[1]) + ((~ord(b[3])) & 255)*256
    fw[1] = hdr_off & 0xFF
    fw[3] = (~(hdr_off >> 8)) & 0xFF
    print "Header offset bytes:", fw[1], fw[3]
    fws = ""
    for b in fw:
        fws = fws + chr(b)
    return fws

print version

if len(sys.argv) != 2:
    print "Usage:\n\npython hbsdec.py firmware.{hbs|bin}\n"
    exit(0)

ifn = sys.argv[1]
ext = ifn.split(".").pop()
print "Input file:", ifn

f = open(ifn)
if f == None:
    print err1
    exit(1)
b = f.read()
f.close()

if len(b) < 1024:
    print err2
    exit(2)

fw = []
if ext == "hbs" or ext == "gbl":
    ext = "bin"
    fw = decodeBytes(b)
elif ext == "bin":
    ext = "hbs"
    fw = encodeBytes(b)

if len(fw) > 0:
    a = ifn.split(".")
    a.pop()
    ofn_base = ".".join(a)
    ofn = ofn_base + "." + ext
    i = 1
    while os.path.exists(ofn):
        ofn = ofn_base + "("+str(i)+")" + "." + ext
    print "Output file:\n", ofn
    f = open(ofn, "wb")
    f.write(fw)
    f.close()
