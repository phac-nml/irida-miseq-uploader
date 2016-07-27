import gzip
import sys
import wx
from wx.lib.pubsub import pub

def parse_fastq(filename):
    fastq_file = gzip.open(filename)
    for i, line in enumerate(fastq_file):
        if i % 4 == 1:
            yield line.rstrip('\n')

def fastq_stats(filename, event_name=None):
    total_bases = 0
    total_reads = 0
    for sequence in parse_fastq(filename):
        total_reads += 1
        total_bases += len(sequence)
    if event_name:
        wx.CallAfter(pub.sendMessage, event_name, fastq_stats=(total_reads, total_bases))
    return (total_reads, total_bases)

if __name__ == "__main__":
    filename = sys.argv[1]
    (reads, bases) = fastq_stats(filename)
    print "Total reads: [{}], total bases: [{}].".format(reads, bases)
