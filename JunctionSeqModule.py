import sys, string
import os.path
import unique
import statistics
import copy
import time
import ExonModule

dirfile = unique

def read_directory(sub_dir):
    dir=os.path.dirname(dirfile.__file__)
    dir_list = os.listdir(dir + sub_dir)
    #add in code to prevent folder names from being included
    dir_list2 = [] 
    for entry in dir_list:
        if entry[-4:] == ".txt" or entry[-4:] == ".TXT" or entry[-3:] == ".fa":
            dir_list2.append(entry)
    return dir_list2

def filepath(filename):
    dir=os.path.dirname(dirfile.__file__)       #directory file is input as a variable under the main            
    fn=os.path.join(dir,filename)
    return fn

def eliminate_redundant_dict_values(database):
    db1={}
    for key in database:
        list = unique.unique(database[key])
        list.sort()
        db1[key] = list
    return db1

#################### Begin Analyzing Datasets #################### 
def importProbesetSeqeunces(filename,exon_db,species):
    print 'importing', filename
    fn=filepath(filename)
    probeset_seq_db={}; x = 0;count = 0
    for line in open(fn,'r').xreadlines():
        if x==0: x=1
        else:
            data, newline = string.split(line,'\n'); t = string.split(data,'\t')
            probeset = t[0]; sequence = t[-1]; sequence = string.upper(sequence)
            try:
                y = exon_db[probeset]; gene = y.GeneID(); y.SetExonSeq(sequence)
                try: probeset_seq_db[gene].append(y)
                except KeyError: probeset_seq_db[gene] = [y]
            except KeyError: null=[] ### Occurs if there is no Ensembl for the critical exon or the sequence is too short to analyze
    print len(probeset_seq_db), "length of gene - probeset sequence database"
    return probeset_seq_db
        
def importSplicingAnnotationDatabaseAndSequence(species,array_type,biotype):
    filename = 'input/'+species+'/'+array_type+'/'+array_type+'-Ensembl.txt'
    fn=filepath(filename); array_ens_db={}; x = 0
    for line in open(fn,'r').xreadlines():
        data, newline = string.split(line,'\n'); t = string.split(data,'\t')
        if x==0: x=1
        else: 
            array_gene,ens_gene = t
            try: array_ens_db[array_gene].append(ens_gene)
            except KeyError: array_ens_db[array_gene]=[ens_gene]

    filename = 'input/'+species+'/'+array_type+'/'+array_type+'_critical-junction-seq.txt'         
    fn=filepath(filename); probeset_seq_db={}; x = 0
    for line in open(fn,'r').xreadlines():
        data, newline = string.split(line,'\n'); t = string.split(data,'\t')
        if x==0: x=1
        else: 
            probeset,probeset_seq,junction_seq = t; junction_seq=string.replace(junction_seq,'|','')
            probeset_seq_db[probeset] = probeset_seq,junction_seq
            
    ###Import reciprocol junctions, so we can compare these directly instead of hits to nulls and combine with sequence data
    ###This short-cuts what we did in two function in ExonModule with exon level data
    filename = 'input/'+species+'/'+array_type+'/'+array_type+'_junction-comparisons.txt'
    fn=filepath(filename); probeset_gene_seq_db={}; x = 0
    for line in open(fn,'r').xreadlines():
        data, newline = string.split(line,'\n'); t = string.split(data,'\t')
        if x==0: x=1
        else: 
            array_gene,probeset1,probeset2,critical_exons = t #; critical_exons = string.split(critical_exons,'|')
            probesets = [probeset1,probeset2]
            if array_gene in array_ens_db:
                ensembl_gene_ids = array_ens_db[array_gene]
                for probeset_id in probesets:
                    if probeset_id in probeset_seq_db:
                        probeset_seq,junction_seq = probeset_seq_db[probeset_id]
                        if biotype == 'gene':
                            for ensembl_gene_id in ensembl_gene_ids:
                                probe_data = ExonModule.JunctionDataSimple(probeset_id,ensembl_gene_id,array_gene,probesets,critical_exons)
                                probe_data.SetExonSeq(probeset_seq)
                                probe_data.SetJunctionSeq(junction_seq)
                                try: probeset_gene_seq_db[ensembl_gene_id].append(probe_data)
                                except KeyError: probeset_gene_seq_db[ensembl_gene_id] = [probe_data]
                        else: ### Used for probeset annotations downstream of sequence alignment in LinkEST, analagous to exon_db for exon analyses
                            probe_data = ExonModule.JunctionDataSimple(probeset_id,ensembl_gene_ids,array_gene,probesets,critical_exons)
                            probe_data.SetExonSeq(probeset_seq)
                            probe_data.SetJunctionSeq(junction_seq)                            
                            probeset_gene_seq_db[probeset_id] = probe_data                
    print len(probeset_gene_seq_db),"genes with probeset sequence associated"
    return probeset_gene_seq_db

def getParametersAndExecute(probeset_seq_file,array_type,species,data_type):
    if data_type == 'critical-exons':
        probeset_annotations_file = "input/"+species+"/"+array_type+'/'+species+"_Ensembl_"+array_type+"_probesets.txt"
        ###Import probe-level associations
        exon_db = ExonModule.importSplicingAnnotationDatabase(probeset_annotations_file)
        start_time = time.time()
        probeset_seq_db = importProbesetSeqeunces(probeset_seq_file,exon_db,species)  ###Do this locally with a function that works on tab-delimited as opposed to fasta sequences (exon array)
        end_time = time.time(); time_diff = int(end_time-start_time)
    elif data_type == 'junctions':
        start_time = time.time(); biotype = 'gene' ### Indicates whether to store information at the level of genes or probesets
        probeset_seq_db = importSplicingAnnotationDatabaseAndSequence(species,array_type,biotype)
        end_time = time.time(); time_diff = int(end_time-start_time)
    print "Analyses finished in %d seconds" % time_diff
    return probeset_seq_db

if __name__ == '__main__':
    species = 'Mm'; array_type = 'exon'
    process_microRNA_predictions = 'yes'
    mir_source = 'multiple'
    array_type = 'AltMouse'
    
    print "******Analysis Stringency*******"
    print "1) Include probeset-miR overlaps with evidence from multiple predictive alogrithms (PicTar, miranda, sanger, TargetScan)"
    print "2) Include all probeset-miR overlaps"
    inp = sys.stdin.readline(); inp = inp.strip()
    if inp == '1': stringency = 'strict'
    if inp == '2': stringency = 'lax'
    
    import_dir = '/input'+'/'+species+'/'+array_type
    filedir = import_dir[1:]+'/'
    dir_list = read_directory(import_dir)  #send a sub_directory to a function to identify all files in a directory
    for input_file in dir_list:    #loop through each file in the directory to output results
        if 'critical-exon-seq' in input_file: probeset_seq_file = filedir+input_file
        
    data_type = 'critical-exons'
    splice_event_db = getParametersAndExecute(probeset_seq_file,array_type,species,data_type)

    if process_microRNA_predictions == 'yes':
        print 'stringency:',stringency 
        ensembl_mirna_db = ExonModule.importmiRNATargetPredictionsAdvanced(species)
        ExonModule.alignmiRNAData(mir_source,species,stringency,ensembl_mirna_db,splice_event_db)