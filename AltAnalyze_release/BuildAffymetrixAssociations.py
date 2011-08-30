###BuildAffymetrixAssociations
#Copyright 2005-2008 J. David Gladstone Institutes, San Francisco California
#Author Nathan Salomonis - nsalomonis@gmail.com

#Permission is hereby granted, free of charge, to any person obtaining a copy 
#of this software and associated documentation files (the "Software"), to deal 
#in the Software without restriction, including without limitation the rights 
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
#copies of the Software, and to permit persons to whom the Software is furnished 
#to do so, subject to the following conditions:

#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
#INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
#PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
#HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION 
#OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE 
#SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""This module contains methods for reading Affymetrix formatted CSV annotations files
from http://www.affymetrix.com, extracting out various direct and inferred gene relationships,
downloading, integrating and inferring WikiPathway gene relationships and downloading and
extracting EntrezGene-Gene Ontology relationships from NCBI."""

import sys, string
import os.path
import unique
import datetime
import export
import update
################# Parse directory files

def filepath(filename):
    fn = unique.filepath(filename)
    return fn

def read_directory(sub_dir):
    try:
        dir_list = unique.read_directory(sub_dir)
        #add in code to prevent folder names from being included
        dir_list2 = [] 
        for entry in dir_list:
            if entry[-4:] == ".txt" or entry[-4:] == ".csv" or entry[-4:] == ".TXT" or entry[-4:] == ".tab" or '.zip' in entry:
                dir_list2.append(entry)
    except Exception:
        print sub_dir, "NOT FOUND!!!!"
        dir_list2=[]
    return dir_list2

def returnDirectories(sub_dir):
    dir_list = unique.returnDirectories(sub_dir)
    ###Below code used to prevent folder names from being included
    dir_list2 = []
    for i in dir_list:
        if "." not in i: dir_list2.append(i)
    return dir_list2

def cleanUpLine(line):
    data = string.replace(line,'\n','')
    data = string.replace(data,'\c','')
    data = string.replace(data,'\r','')
    data = string.replace(data,'"','')
    return data

class GrabFiles:
    def setdirectory(self,value): self.data = value
    def display(self): print self.data
    def searchdirectory(self,search_term):
        #self is an instance while self.data is the value of the instance
        file = getDirectoryFiles(self.data,str(search_term))
        if len(file)<1: print search_term,'not found'
        return file
    def returndirectory(self):
        dir_list = read_directory(self.data)
        return dir_list
    
def getDirectoryFiles(import_dir, search_term):
    exact_file = ''
    dir_list = read_directory(import_dir)  #send a sub_directory to a function to identify all files in a directory
    for data in dir_list:    #loop through each file in the directory to output results
        affy_data_dir = import_dir[1:]+'/'+data
        if search_term in affy_data_dir: exact_file = affy_data_dir
    return exact_file

################# Import and Annotate Data
class AffymetrixInformation:
    def __init__(self,probeset,symbol,ensembl,entrez,unigene,uniprot,description,goids,go_names,pathways):
        self._probeset = probeset; self._ensembl = ensembl; self._uniprot = uniprot; self._description = description
        self._entrez = entrez; self._symbol = symbol; self._unigene = unigene
        self._goids = goids; self._go_names = go_names; self._pathways = pathways
    def ArrayID(self): return self._probeset
    def Description(self): return self._description
    def Symbol(self): return self._symbol
    def Ensembl(self): return self._ensembl
    def EnsemblString(self):
        ens_str = string.join(self._ensembl,'|')
        return ens_str
    def Entrez(self): return self._entrez
    def EntrezString(self):
        entrez_str = string.join(self._entrez,'|')
        return entrez_str
    def Unigene(self): return self._unigene
    def UnigeneString(self):
        unigene_str = string.join(self._unigene,'|')
        return unigene_str
    def Uniprot(self): return self._uniprot
    def GOIDs(self): return self._goids
    def GOProcessIDs(self): return self._goids[0]
    def GOComponentIDs(self): return self._goids[1]
    def GOFunctionIDs(self): return self._goids[2]
    def GONameLists(self): return self._go_names
    def GOProcessNames(self):
        go_names = string.join(self._go_names[0],' // ')
        return go_names
    def GOComponentNames(self):
        go_names = string.join(self._go_names[1],' // ')
        return go_names
    def GOFunctionNames(self):
        go_names = string.join(self._go_names[2],' // ')
        return go_names
    def GONames(self):
        go_names = self._go_names[0]+self._go_names[1]+self._go_names[2]
        return go_names
    def Pathways(self): return self._pathways
    def PathwayInfo(self):
        pathway_str = string.join(self.Pathways(),' // ')
        return pathway_str
    def GOPathwayInfo(self):
        pathway_str = string.join(self.GONames() + self.Pathways(),' // ')
        return pathway_str
    def resetEnsembl(self,ensembl): self._ensembl = ensembl
    def resetEntrez(self,entrez): self._entrez = entrez
    def ArrayValues(self):
        output = self.Symbol()+'|'+self.ArrayID()
        return output
    def __repr__(self): return self.ArrayValues()

class InferredEntrezInformation:
    def __init__(self,symbol,entrez,description):
        self._entrez = entrez; self._symbol = symbol; self._description = description
    def Entrez(self): return self._entrez
    def Symbol(self): return self._symbol
    def Description(self): return self._description
    def DataValues(self):
        output = self.Symbol()+'|'+self.Entrez()
        return output
    def __repr__(self): return self.DataValues()
    
def eliminate_redundant_dict_values(database):
    db1={}
    for key in database: list = unique.unique(database[key]); list.sort(); db1[key] = list
    return db1

def buildMODDbase():
    mod_db={}
    mod_db['Dr'] = 'FlyBase'
    mod_db['Ce'] = 'WormBase'
    mod_db['Mm'] = 'MGI Name'
    mod_db['Rn'] = 'RGD Name'
    mod_db['Sc'] = 'SGD accession number'
    mod_db['At'] = 'AGI'
    return mod_db

def verifyFile(filename):
    fn=filepath(filename); file_found = 'yes'
    try:
        for line in open(fn,'rU').xreadlines():break
    except Exception: file_found = 'no'
    return file_found

######### Import New Data ##########
def parse_affymetrix_annotations(filename,species):
    ###Import an Affymetrix array annotation file (from http://www.affymetrix.com) and parse out annotations
    temp_affy_db = {}; x=0; y=0

    if process_go == 'yes':
        eg_go_found = verifyFile('Databases/'+species+'/gene-go/EntrezGene-GeneOntology.txt')
        ens_go_found = verifyFile('Databases/'+species+'/gene-go/Ensembl-GeneOntology.txt')
        if eg_go_found == 'no' or ens_go_found == 'no': process_go_var = 'yes'
    else: process_go_var = 'yes'

    fn=filepath(filename); mod_db = buildMODDbase()
    for line in open(fn,'r').readlines():             
        probeset_data = string.replace(line,'\n','')  #remove endline
        probeset_data = string.replace(probeset_data,'---','')
        affy_data = string.split(probeset_data[1:-1],'","')  #remove endline
        try: mod_name = mod_db[species]
        except KeyError: mod_name = 'YYYYYY' ###Something that should not be found
        if x==0 and line[0]!='#':
            x=1; affy_headers = affy_data
            for header in affy_headers:
                y = 0
                while y < len(affy_headers):
                    if 'Probe Set ID' in affy_headers[y] or 'probeset_id' in affy_headers[y]: ps = y
                    if 'transcript_cluster_id' in affy_headers[y]: tc = y
                    if 'Gene Symbol' in affy_headers[y]: gs = y
                    if 'Ensembl' in affy_headers[y]: ens = y
                    if ('nigene' in affy_headers[y] or 'UniGene' in affy_headers[y]) and 'Cluster' not in affy_headers[y]: ug = y
                    if 'mrna_assignment' in affy_headers[y]: ma = y
                    if 'gene_assignment' in affy_headers[y]: ga = y
                    if 'Entrez' in affy_headers[y] or 'LocusLink' in affy_headers[y]: ll = y
                    if 'SwissProt' in affy_headers[y] or 'swissprot' in affy_headers[y]: sp = y
                    if 'Gene Title' in affy_headers[y]: gt = y
                    if 'rocess' in affy_headers[y]: bp = y
                    if 'omponent' in affy_headers[y]: cc = y
                    if 'unction' in affy_headers[y]: mf = y
                    if 'RefSeq Protein' in affy_headers[y]: rp = y
                    if 'RefSeq Transcript' in affy_headers[y]: rt = y
                    if 'athway' in affy_headers[y]: gp = y
                    if mod_name in affy_headers[y]: mn = y
                    y += 1
        elif x == 1:
            ###If using the Affy 2.0 Annotation file structure, both probeset and transcript cluster IDs are present
            ###If transcript_cluster centric file (gene's only no probesets), then probeset = transcript_cluster
            try: 
                transcript_cluster = affy_data[tc]  ###Affy's unique Gene-ID
                probeset = affy_data[ps]
                if probeset != transcript_cluster: ###Occurs for transcript_cluster ID centered files
                    probesets = [probeset,transcript_cluster]
                else: probesets = [probeset]
                ps = tc; version = 2 ### Used to define where the non-UID data exists
            except UnboundLocalError: probesets = [affy_data[ps]]; version = 1
            
            try: uniprot = affy_data[sp]; unigene = affy_data[ug]; uniprot_list = string.split(uniprot,' /// ')
            except IndexError: uniprot=''; unigene=''; uniprot_list=[] ### This occurs due to a random python error, typically once twice in the file
            symbol = ''; description = ''
            try: pathway_data = affy_data[gp]
            except IndexError: pathway_data='' ### This occurs due to a random python error, typically once twice in the file
            for probeset in probesets:
                if version == 1: ###Applies to 3' biased arrays only (Conventional Format)
                    description = affy_data[gt]; symbol = affy_data[gs]; goa=''; entrez = affy_data[ll]
                    ensembl_list = []; ensembl = affy_data[ens]; ensembl_list = string.split(ensembl,' /// ')
                    entrez_list = string.split(entrez,' /// '); unigene_list = string.split(unigene,' /// ')
                    uniprot_list = string.split(uniprot,' /// '); symbol_list = string.split(symbol,' /// ')
                    try: mod = affy_data[mn]; mod_list = string.split(mod,' /// ')
                    except UnboundLocalError: mod = ''; mod_list = []
                    if len(symbol)<1 and len(mod)>0: symbol = mod ### For example, for At, use Tair if no symbol present
                    ref_prot = affy_data[rp]; ref_prot_list = string.split(ref_prot,' /// ')
                    ref_tran = affy_data[rt]; ref_tran_list = string.split(ref_tran,' /// ')
                    ###Process GO information if desired
                    if process_go_var == 'yes':
                        process = affy_data[bp]; component = affy_data[cc]; function = affy_data[mf]
                        process_goids, process_names = extractPathwayData(process,'GO',version)
                        component_goids, component_names = extractPathwayData(component,'GO',version)
                        function_goids, function_names = extractPathwayData(function,'GO',version)
                        goids = [process_goids,component_goids,function_goids]
                        go_names = [process_names,component_names,function_names]
                    else: goids=[]; go_names=[]
                    if extract_pathway_names == 'yes': null, pathways = extractPathwayData(pathway_data,'pathway',version)
                    else: pathways = []

                    ai = AffymetrixInformation(probeset, symbol, ensembl_list, entrez_list, unigene_list, uniprot_list, description, goids, go_names, pathways)
                    if len(entrez_list)<5: affy_annotation_db[probeset] = ai
                    if parse_wikipathways == 'yes':
                        if (len(entrez_list)<4 and len(entrez_list)>0) or (len(ensembl_list)<4 and len(ensembl_list)>0):
                            primary_list = entrez_list+ensembl_list
                            for primary in primary_list:
                                if len(primary)>0:
                                    for gene in ensembl_list:
                                        if len(gene)>1: meta[primary,gene]=[]
                                    for gene in ref_prot_list:
                                        gene_data = string.split(gene,'.'); gene = gene_data[0]
                                        if len(gene)>1: meta[primary,gene]=[] 
                                    for gene in ref_tran_list:
                                        if len(gene)>1: meta[primary,gene]=[]
                                    for gene in unigene_list:
                                        if len(gene)>1: meta[primary,gene]=[]
                                    for gene in mod_list:
                                        if len(gene)>1: meta[primary,'mod:'+gene]=[]
                                    for gene in symbol_list:
                                        if len(gene)>1: meta[primary,gene]=[]
                                    for gene in uniprot_list:
                                        if len(gene)>1: meta[primary,gene]=[]
                                    for gene in entrez_list:
                                        if len(gene)>1: meta[primary,gene]=[]
                    #symbol_list = string.split(symbol,' /// '); description_list = string.split(description,' /// ')
                    if len(entrez_list)<2: ###Only store annotations for EntrezGene if there is only one listed ID, since the symbol, description and Entrez Gene are sorted alphabetically, not organized relative to each other (stupid)
                        iter = 0
                        for entrez in entrez_list:
                            #symbol = symbol_list[iter]; description = description_list[iter] ###grab the symbol that matches the EntrezGene entry
                            z = InferredEntrezInformation(symbol,entrez,description)
                            try: gene_annotation_db[entrez] = z
                            except NameError: null=[]
                            iter += 1
                    if len(ensembl_list)<2: ###Only store annotations for EntrezGene if there is only one listed ID, since the symbol, description and Entrez Gene are sorted alphabetically, not organized relative to each other (stupid)
                        for ensembl in ensembl_list:
                            z = InferredEntrezInformation(symbol,ensembl,description)
                            try: gene_annotation_db['ENS:'+ensembl] = z
                            except NameError: null=[]
                else: ### Applies to Exon, Transcript, whole geneome Gene arrays.
                    uniprot_list2 = []
                    for uniprot_id in uniprot_list:
                        if len(uniprot_id)>0:
                            try: a = int(uniprot_id[1]); uniprot_list2.append(uniprot_id)
                            except ValueError: null = []
                    uniprot_list = uniprot_list2
                    ensembl_list=[]; descriptions=[]; refseq_list=[]; symbol_list=[]
                    try: mrna_associations = affy_data[ma]
                    except IndexError: mrna_associations=''; 
                    ensembl_data = string.split(mrna_associations,' /// ')
                    for entry in ensembl_data:
                        annotations = string.split(entry,' // ')
                        #if probeset == '8148358': print annotations
                        for i in annotations:
                            if 'gene:ENS' in i:
                                ensembl_id_data = string.split(i,'gene:ENS')
                                ensembl_ids = ensembl_id_data[1:]; description = ensembl_id_data[0] ###There can be multiple IDs
                                descriptions.append((len(description),description))
                                for ensembl_id in ensembl_ids:
                                    ensembl_id = string.split(ensembl_id,' ')
                                    ensembl_id = 'ENS'+ensembl_id[0]; ensembl_list.append(ensembl_id)
                            if 'NM_' in i:
                                refseq_id = string.replace(i,' ','')
                                refseq_list.append(refseq_id)
                                
                    #if probeset == '8148358': print ensembl_list; kill
                    try: gene_assocs = affy_data[ga]; entrez_list=[]
                    except IndexError: gene_assocs=''; entrez_list=[]
                    entrez_data = string.split(gene_assocs,' /// ')
                    for entry in entrez_data:
                        try:
                            if len(entry)>0:
                                annotations = string.split(entry,' // ')
                                entrez_gene = int(annotations[-1]); entrez_list.append(str(entrez_gene))
                                symbol = annotations[1]; description = annotations[2]; descriptions.append((len(description),description))
                                symbol_list.append(symbol)
                                #print entrez_gene,symbol, descriptions;kill
                                z = InferredEntrezInformation(symbol,entrez_gene,description)
                                try: gene_annotation_db[str(entrez_gene)] = z ###create an inferred Entrez gene database
                                except NameError: null = []
                        except ValueError: null = []
                        
                    if len(symbol_list) == 1 and len(ensembl_list)>0:
                        symbol = symbol_list[0]
                        for ensembl in ensembl_list:
                            z = InferredEntrezInformation(symbol,ensembl,description)
                            try: gene_annotation_db['ENS:'+ensembl] = z ###create an inferred Entrez gene database
                            except NameError: null = []
                    gene_assocs = string.replace(gene_assocs,'---','')
                    unigene_data = string.split(unigene,' /// '); unigene_list = []
                    for entry in unigene_data:
                        if len(entry)>0:
                            annotations = string.split(entry,' // ')
                            try: null = int(annotations[-2][3:]); unigene_list.append(annotations[-2])
                            except Exception: null = []
                    ###Only applies to optional GOID inclusion
                    if parse_wikipathways == 'yes':
                        if (len(entrez_list)<4 and len(entrez_list)>0) or (len(ensembl_list)<4 and len(ensembl_list)>0):
                            primary_list = entrez_list+ensembl_list
                            for primary in primary_list:
                                if len(primary)>0:
                                    for gene in ensembl_list:
                                        if len(gene)>1: meta[primary,gene]=[]
                                    for gene in refseq_list:
                                        gene_data = string.split(gene,'.'); gene = gene_data[0]
                                        if len(gene)>1: meta[primary,gene]=[]
                                    for gene in unigene_list:
                                        if len(gene)>1: meta[primary,gene]=[]
                                    for gene in symbol_list:
                                        if len(gene)>1: meta[primary,gene]=[]
                                    for gene in uniprot_list:
                                        if len(gene)>1: meta[primary,gene]=[]
                                    for gene in entrez_list:
                                        if len(gene)>1: meta[primary,gene]=[]
                    if process_go_var == 'yes':
                        try: process = affy_data[bp]; component = affy_data[cc]; function = affy_data[mf]
                        except IndexError: process = ''; component=''; function=''### This occurs due to a random python error, typically once twice in the file
                        process_goids, process_names = extractPathwayData(process,'GO',version)
                        component_goids, component_names = extractPathwayData(component,'GO',version)
                        function_goids, function_names = extractPathwayData(function,'GO',version)
                        goids = [process_goids,component_goids,function_goids]
                        go_names = [process_names,component_names,function_names]
                    else: goids=[]; go_names=[]
                    if extract_pathway_names == 'yes': null, pathways = extractPathwayData(pathway_data,[],version)
                    else: pathways = []
                    entrez_list=unique.unique(entrez_list); unigene_list=unique.unique(unigene_list); uniprot_list=unique.unique(uniprot_list); ensembl_list=unique.unique(ensembl_list)
                    descriptions2=[]
                    for i in descriptions: 
                        if 'cdna:known' not in i: descriptions2.append(i)
                    descriptions = descriptions2
                    if len(descriptions)>0:
                        descriptions.sort(); description = descriptions[-1][1]
                        if description[0] == ' ': description = description[1:] ### some entries begin with a blank
                    ai = AffymetrixInformation(probeset,symbol,ensembl_list,entrez_list,unigene_list,uniprot_list,description,goids,go_names,pathways)
                    if len(entrez_list)<5 and len(ensembl_list)<5: affy_annotation_db[probeset] = ai
    print 'Affymetrix CSV annotations imported..'
    
def getArrayAnnotationsFromGOElite(conventional_array_db,species_code,vendor,use_go):
    import gene_associations; import time
    start_time = time.time()
    ### Get Gene Ontology gene associations
    try: gene_to_mapp_ens = gene_associations.importGeneMAPPData(species_code,'Ensembl')
    except Exception: gene_to_mapp_ens = {}
    try: gene_to_mapp_eg = gene_associations.importGeneMAPPData(species_code,'EntrezGene')
    except Exception: gene_to_mapp_eg = {}
    if vendor == 'Affymetrix': ### Remove exon associations which decrease run efficency and are superfulous
        try: ens_to_array = gene_associations.getGeneToUidNoExon(species_code,'Ensembl-'+vendor); print 'Ensembl-'+vendor,'relationships imported'
        except Exception: ens_to_array={}
        try: eg_to_array = gene_associations.getGeneToUidNoExon(species_code,'EntrezGene-'+vendor); print 'EntrezGene-'+vendor,'relationships imported'
        except Exception: eg_to_array={}
        print '* *',
    else:
        try: ens_to_array = gene_associations.getGeneToUid(species_code,'Ensembl-'+vendor)
        except Exception: ens_to_array = {}
        try: eg_to_array = gene_associations.getGeneToUid(species_code,'EntrezGene-'+vendor)
        except Exception: eg_to_array = {}
    print '* *',
    try: ens_annotations = gene_associations.importGeneData(species_code,'Ensembl')
    except Exception: ens_annotations = {}
    try: eg_annotations = gene_associations.importGeneData(species_code,'EntrezGene')
    except Exception: eg_annotations = {}
    
    if use_go == 'yes':
        import OBO_import
        go_annotations = OBO_import.importPreviousGOAnnotations()

        try: gene_to_go_ens = gene_associations.importGeneGOData(species_code,'Ensembl','null')
        except Exception: gene_to_go_ens = {}
        print '* *',
        try: gene_to_go_eg = gene_associations.importGeneGOData(species_code,'EntrezGene','null')
        except Exception: gene_to_go_eg = {}
        print '* *',
        component_db,process_db,function_db = annotateGOElitePathways('GO',go_annotations,gene_to_go_ens,ens_to_array)
        print '* *',
        component_eg_db,process_eg_db,function_eg_db = annotateGOElitePathways('GO',go_annotations,gene_to_go_eg,eg_to_array)
        print '* *',
        component_db = combineDBs(component_eg_db,component_db)
        print '* *',
        process_db = combineDBs(process_eg_db,process_db)
        print '* *',
        function_db = combineDBs(function_eg_db,function_db)
        print '* *',
    else: print '* * * * * * * * * *',
    unique_arrayids={} ### Get all unique probesets
    for gene in ens_to_array:
        for uid in ens_to_array[gene]: unique_arrayids[uid]=[]
    for gene in eg_to_array:
        for uid in eg_to_array[gene]: unique_arrayids[uid]=[]
    
    array_ens_mapp_db = annotateGOElitePathways('MAPP','',gene_to_mapp_ens,ens_to_array)
    array_eg_mapp_db = annotateGOElitePathways('MAPP','',gene_to_mapp_eg,eg_to_array)
    array_mapp_db = combineDBs(array_ens_mapp_db,array_eg_mapp_db)
    print '* *',
    array_to_ens = swapKeyValues(ens_to_array)
    array_to_eg = swapKeyValues(eg_to_array)
    
    global array_symbols; global array_descriptions; array_symbols={}; array_descriptions={}
    getArrayIDAnnotations(ens_to_array,ens_annotations)
    getArrayIDAnnotations(eg_to_array,eg_annotations)
    print '* *',
    for arrayid in unique_arrayids:
        try: component_names = component_db[arrayid]
        except Exception: component_names=[]
        try: process_names = process_db[arrayid]
        except Exception: process_names=[]
        try: function_names = function_db[arrayid]
        except Exception: function_names=[]
        try: wp_names = array_mapp_db[arrayid]
        except Exception: wp_names=[]
        try: ensembls = array_to_ens[arrayid]
        except Exception: ensembls=[]
        try: entrezs = array_to_eg[arrayid]
        except Exception: entrezs=[]
        try: symbol = array_symbols[arrayid]
        except Exception: symbol=''
        try: description = array_descriptions[arrayid]
        except Exception: description=''
        #if len(wp_names)>0:
            #print arrayid, component_names, process_names, function_names, wp_names, ensembls, entrezs, symbol, description;kill
        
        try:
            ca = conventional_array_db[arrayid]
            definition = ca.Description()
            symbol = ca.Symbol()
            ens = ca.Ensembl()
            entrez = ca.Entrez()
            pathways = ca.Pathways()
            process, component, function = ca.GONameLists()
            ensembls+=ens; entrezs+=entrez; wp_names+=pathways
            component_names+=component; process_names+=process; function_names+=function
            ensembls=unique.unique(ensembls); entrezs=unique.unique(entrezs); wp_names=unique.unique(wp_names)
            component_names=unique.unique(component_names); process_names=unique.unique(process_names); function_names=unique.unique(function_names)
        except Exception: null=[]
        go_names = process_names,component_names,function_names
        ai = AffymetrixInformation(arrayid,symbol,ensembls,entrezs,[],[],description,[],go_names,wp_names)
        conventional_array_db[arrayid] = ai
    #print len(conventional_array_db),'ArrayIDs with annotations.'
    end_time = time.time(); time_diff = int(end_time-start_time)
    print 'ArrayID annotations imported in',time_diff, 'seconds'
    return conventional_array_db

class PathwayInformation:
    def __init__(self,component_list,function_list,process_list,pathway_list):
        self.component_list = component_list; self.function_list = function_list
        self.process_list = process_list; self.pathway_list = pathway_list
    def Component(self): return self.Format(self.component_list)
    def Process(self): return self.Format(self.process_list)
    def Function(self): return self.Format(self.function_list)
    def Pathway(self): return self.Format(self.pathway_list)
    def Combined(self): return self.Format(self.pathway_list+self.process_list+self.function_list+self.component_list)
    def Format(self,terms):
        return string.join(terms,' // ')
    
def getHousekeepingGenes(species_code):
    vendor = 'Affymetrix'
    exclude = ['ENSG00000256901'] ### Incorrect homology with housekeeping
    import gene_associations
    try: ens_to_array = gene_associations.getGeneToUidNoExon(species_code,'Ensembl-'+vendor); print 'Ensembl-'+vendor,'relationships imported'
    except Exception: ens_to_array={}
    housekeeping_genes={}
    for gene in ens_to_array:
        for uid in ens_to_array[gene]:
            if 'AFFX' in uid:
                if gene not in exclude: housekeeping_genes[gene]=[]
    return housekeeping_genes

def getEnsemblAnnotationsFromGOElite(species_code):
    import gene_associations; import time
    start_time = time.time()
    ### Get Gene Ontology gene associations
    try: gene_to_mapp_ens = gene_associations.importGeneMAPPData(species_code,'Ensembl')
    except Exception: gene_to_mapp_ens = {}

    import OBO_import
    go_annotations = OBO_import.importPreviousGOAnnotations()

    try: gene_to_go_ens = gene_associations.importGeneGOData(species_code,'Ensembl','null')
    except Exception: gene_to_go_ens = {}

    component_db={}; process_db={}; function_db={}; all_genes={}
    for gene in gene_to_go_ens:
        all_genes[gene]=[]
        for goid in gene_to_go_ens[gene]:
            if goid in go_annotations:
                s = go_annotations[goid]
                go_name = string.replace(s.GOName(),'\\','')
                gotype = s.GOType()
                if gotype == 'C':
                    try: component_db[gene].append(go_name)
                    except KeyError: component_db[gene] = [go_name]
                if gotype == 'P':
                    try: process_db[gene].append(go_name)
                    except KeyError: process_db[gene] = [go_name]
                if gotype == 'F':
                    try: function_db[gene].append(go_name)
                    except KeyError: function_db[gene] = [go_name]
                    
    for gene in gene_to_mapp_ens: all_genes[gene]=[]

    for gene in all_genes:
        component_go=[]; process_go=[]; function_go=[]; pathways=[]
        if gene in component_db: component_go = component_db[gene]
        if gene in function_db: function_go = function_db[gene]
        if gene in process_db: process_go = process_db[gene]
        if gene in gene_to_mapp_ens: pathways = gene_to_mapp_ens[gene]
        pi=PathwayInformation(component_go,function_go,process_go,pathways)
        all_genes[gene]=pi
        
    end_time = time.time(); time_diff = int(end_time-start_time)
    print len(all_genes),'Ensembl GO/pathway annotations imported in',time_diff, 'seconds'
    return all_genes

def getArrayIDAnnotations(gene_to_uid,gene_annotations):
    for gene in gene_annotations:
        if gene in gene_to_uid:
            uids = gene_to_uid[gene]
            s = gene_annotations[gene]
            if len(s.Symbol()) > 0:
                for uid in uids:
                    array_symbols[uid] = s.Symbol()
                    array_descriptions[uid] = s.Description()
                
def combineDBs(db1,db2):
    for i in db1:
        try: db1[i]+=db2[i]
        except Exception: null=[]
    for i in db2:
        try: db2[i]+=db1[i]
        except Exception: db1[i]=db2[i]
    db1 = eliminate_redundant_dict_values(db1)
    return db1

def annotateGOElitePathways(pathway_type,go_annotations,gene_to_pathway,gene_to_uid):
    array_pathway_db={}
    for gene in gene_to_uid:
        try:
            pathways = gene_to_pathway[gene]
            for pathway in pathways:
                for arrayid in gene_to_uid[gene]:           
                    if pathway_type == 'GO':
                        s = go_annotations[pathway]
                        go_name = string.replace(s.GOName(),'\\','')
                        try: array_pathway_db[arrayid,s.GOType()].append(go_name)
                        except Exception: array_pathway_db[arrayid,s.GOType()] = [go_name]
                    else:
                        try: array_pathway_db[arrayid].append(pathway + '(WikiPathways)')
                        except Exception: array_pathway_db[arrayid] = [pathway + '(WikiPathways)']
        except Exception: null=[]
                                    
    array_pathway_db = eliminate_redundant_dict_values(array_pathway_db)
    if pathway_type == 'GO':
        component_db={}; process_db={}; function_db={}
        for (arrayid,gotype) in array_pathway_db:
            if gotype == 'C': component_db[arrayid] = array_pathway_db[(arrayid,gotype)]
            if gotype == 'P': process_db[arrayid] = array_pathway_db[(arrayid,gotype)]
            if gotype == 'F': function_db[arrayid] = array_pathway_db[(arrayid,gotype)]
        return component_db,process_db,function_db
    else: return array_pathway_db

def extractPathwayData(terms,type,version):
    goids = []; go_names = []
    buffer = ' /// '; small_buffer = ' // '
    go_entries = string.split(terms,buffer)
    for go_entry in go_entries:
        go_entry_info = string.split(go_entry,small_buffer)
        try:
            if len(go_entry_info)>1:
                if version == 1:
                    if type == 'GO': ### 6310 // DNA recombination // inferred from electronic annotation ///
                        goid, go_name, source = go_entry_info
                        while len(goid)< 7: goid = '0'+goid
                        goid = 'GO:'+goid
                    else: ### Calcium signaling pathway // KEGG ///
                        go_name, source = go_entry_info; goid = ''
                        if len(go_name)>1: go_name = source+'-'+go_name
                        else: go_name = ''
                if version == 2:
                    if type == 'GO': ### NM_153254 // GO:0006464 // protein modification process // inferred from electronic annotation /// 
                        try: accession, goid, go_name, source = go_entry_info
                        except ValueError: accession = go_entry_info[0]; goid = go_entry_info[1]; go_name = ''; source = ''
                    else: ### AF057061 // GenMAPP // Matrix_Metalloproteinases
                        accession, go_name, source = go_entry_info; goid = ''
                        if len(go_name)>1: go_name = source+'-'+go_name
                        else: go_name = ''
                goids.append(goid); go_names.append(go_name)
        except IndexError: goids = goids
    if extract_go_names != 'yes': go_names = [] ### Then don't store (save memory)
    goids = unique.unique(goids); go_names = unique.unique(go_names)
    return goids, go_names
          
def exportResultsSummary(dir_list,species,type):
    program_type,database_dir = unique.whatProgramIsThis()
    if program_type == 'AltAnalyze': parent_dir = 'AltDatabase/goelite'
    else: parent_dir = 'Databases'
    
    if overwrite_previous == 'over-write previous':
        if program_type != 'AltAnalyze': import OBO_import; OBO_import.exportVersionData(0,'0/0/0','/'+species+'/nested/')  ### Erase the existing file so that the database is re-remade
    else: parent_dir = 'NewDatabases'

    new_file = parent_dir+'/'+species+'/'+type+'_files_summarized.txt'
    today = str(datetime.date.today()); today = string.split(today,'-'); today = today[1]+'/'+today[2]+'/'+today[0]
    fn=filepath(new_file); data = open(fn,'w')
    for filename in dir_list: data.write(filename+'\t'+today+'\n')
    try:
        if parse_wikipathways == 'yes': data.write(wikipathways_file+'\t'+today+'\n')
    except Exception: null=[]
    data.close()

def exportMetaGeneData(species):
    program_type,database_dir = unique.whatProgramIsThis()
    if program_type == 'AltAnalyze': parent_dir = 'AltDatabase/goelite'
    else: parent_dir = 'Databases'
    
    if overwrite_previous == 'over-write previous':
        if program_type != 'AltAnalyze':
            null = None
            #import OBO_import; OBO_import.exportVersionData(0,'0/0/0','/'+species+'/nested/')  ### Erase the existing file so that the database is re-remade
    else: parent_dir = 'NewDatabases'
    
    new_file = parent_dir+'/'+species+'/uid-gene/Ensembl_EntrezGene-meta.txt'
    data = export.ExportFile(new_file)

    for (primary,gene) in meta: data.write(primary+'\t'+gene+'\n')
    data.close()

def importMetaGeneData(species):
    program_type,database_dir = unique.whatProgramIsThis()
    if program_type == 'AltAnalyze': parent_dir = 'AltDatabase/goelite'
    else: parent_dir = 'Databases'
    filename = parent_dir+'/'+species+'/uid-gene/Ensembl_EntrezGene-meta.txt'
    fn=filepath(filename)
    for line in open(fn,'rU').readlines():             
        data = cleanUpLine(line)
        primary,gene = string.split(data,'\t')
        meta[primary,gene]=[]
    
def exportRelationshipDBs(species):
    program_type,database_dir = unique.whatProgramIsThis()
    if program_type == 'AltAnalyze': parent_dir = 'AltDatabase/goelite'
    else: parent_dir = 'Databases'
    
    if overwrite_previous == 'over-write previous':
        if program_type != 'AltAnalyze': import OBO_import; OBO_import.exportVersionData(0,'0/0/0','/'+species+'/nested/')  ### Erase the existing file so that the database is re-remade
    else: parent_dir = 'NewDatabases'
  
    x1=0; x2=0; x3=0; x4=0; x5=0; x6=0
    today = str(datetime.date.today()); today = string.split(today,'-'); today = today[1]+'/'+today[2]+'/'+today[0]
    import UI; header = 'GeneID'+'\t'+'GOID'+'\n'
    ens_annotations_found = verifyFile('Databases/'+species+'/gene/Ensembl.txt')
        
    if process_go == 'yes': ens_process_go = 'yes'; eg_process_go = 'yes'
    else:
        ens_process_go = 'no'; eg_process_go = 'no'
        eg_go_found = verifyFile('Databases/'+species+'/gene-go/EntrezGene-GeneOntology.txt')
        ens_go_found = verifyFile('Databases/'+species+'/gene-go/Ensembl-GeneOntology.txt')
        if eg_go_found == 'no': eg_process_go = 'yes'
        if ens_go_found == 'no': ens_process_go = 'yes'

    for probeset in affy_annotation_db:
        ai = affy_annotation_db[probeset]
        ensembls = unique.unique(ai.Ensembl()); entrezs = unique.unique(ai.Entrez())
        for ensembl in ensembls:
            if len(ensembl)>0:
                if x1 == 0: ### prevents the file from being written if no data present
                    new_file1 = parent_dir+'/'+species+'/uid-gene/Ensembl-Affymetrix.txt'
                    data1 = export.ExportFile(new_file1); x1=1
                data1.write(ensembl+'\t'+probeset+'\n')
                if ens_process_go == 'yes':
                    goids = unique.unique(ai.GOIDs())
                    for goid_ls in goids:
                        for goid in goid_ls:
                            if len(goid)>0:
                                if x4==0:
                                    new_file4 = parent_dir+'/'+species+'/gene-go/Ensembl-GeneOntology.txt'
                                    data4 = export.ExportFile(new_file4); data4.write(header); x4=1
                                data4.write(ensembl+'\t'+goid+'\n')
        for entrez in entrezs:
            if len(entrez)>0:
                if x2 == 0:
                    new_file2 = parent_dir+'/'+species+'/uid-gene/EntrezGene-Affymetrix.txt'
                    data2 = export.ExportFile(new_file2); x2=1
                data2.write(entrez+'\t'+probeset+'\n')
                if eg_process_go == 'yes':
                    goids = unique.unique(ai.GOIDs())
                    for goid_ls in goids:
                        for goid in goid_ls:
                            if len(goid)>0:
                                if x5==0:
                                    new_file5 = parent_dir+'/'+species+'/gene-go/EntrezGene-GeneOntology.txt'
                                    data5 = export.ExportFile(new_file5); data5.write(header); x5=1
                                data5.write(entrez+'\t'+goid+'\n')
    for geneid in gene_annotation_db:
        ea = gene_annotation_db[geneid]
        if len(geneid)>0 and 'ENS:' not in geneid:
            if x3 == 0:
                new_file3 = parent_dir+'/'+species+'/gene/EntrezGene.txt'
                data3 = export.ExportFile(new_file3); x3=1
                data3.write('ID'+'\t'+'Symbol'+'\t'+'Name'+'\t'+'Species'+'\t'+'Date'+'\t'+'Remarks'+'\n')
            data3.write(geneid+'\t'+ea.Symbol()+'\t'+ea.Description()+'\t'+species+'\t'+today+'\t'+''+'\n')
        elif ens_annotations_found == 'no' and 'ENS:' in geneid:
            geneid = string.replace(geneid,'ENS:','')
            if x6 == 0:
                new_file6 = parent_dir+'/'+species+'/gene/EntrezGene.txt'
                data6 = export.ExportFile(new_file6); x6=1
                data6.write('ID'+'\t'+'Symbol'+'\t'+'Name'+'\n')
            data6.write(geneid+'\t'+ea.Symbol()+'\t'+ea.Description()+'\n')
            
    if x1==1: data1.close()
    if x2==1: data2.close()
    if x3==1: data3.close()
    if x4==1: data4.close()
    if x5==1: data5.close()
    if x6==1: data6.close()
    
def swapKeyValues(db):
    swapped={}
    for key in db:
        values = list(db[key]) ###If the value is not a list, make a list
        for value in values:
            try: swapped[value].append(key)
            except KeyError: swapped[value] = [key]
    swapped = eliminate_redundant_dict_values(swapped)
    return swapped

def integratePreviousAssociations():
    print 'Integrating associations from previous databases...'
    #print len(entrez_annotations),len(ens_to_uid), len(entrez_to_uid)
    for gene in entrez_annotations:
        if gene not in gene_annotation_db:
            ### Add previous gene information to the new database
            y = entrez_annotations[gene]
            z = InferredEntrezInformation(y.Symbol(),gene,y.Description())
            gene_annotation_db[gene] = z
    uid_to_ens = swapKeyValues(ens_to_uid); uid_to_entrez = swapKeyValues(entrez_to_uid)

    ###Add prior missing gene relationships for all probesets in the new database and that are missing
    for uid in uid_to_ens:
        if uid in affy_annotation_db:
            y = affy_annotation_db[uid]
            ensembl_ids = uid_to_ens[uid]
            if y.Ensembl() == ['']: y.resetEnsembl(ensembl_ids)
            else:
                ensembl_ids = unique.unique(y.Ensembl()+ensembl_ids)
                y.resetEnsembl(ensembl_ids)
        else:
            ensembl_ids = uid_to_ens[uid]; entrez_ids = []
            if uid in uid_to_entrez: entrez_ids = uid_to_entrez[uid]
            ai = AffymetrixInformation(uid, '', ensembl_ids, entrez_ids, [], [], '',[],[],[])
            affy_annotation_db[uid] = ai
    for uid in uid_to_entrez:
        if uid in affy_annotation_db:
            y = affy_annotation_db[uid]
            entrez_ids = uid_to_entrez[uid]
            if y.Entrez() == ['']: y.resetEntrez(entrez_ids)
        else:
            entrez_ids = uid_to_entrez[uid]; ensembl_ids = []
            if uid in uid_to_ens: ensembl_ids = uid_to_ens[uid]
            ai = AffymetrixInformation(uid, '', ensembl_ids, entrez_ids, [], [], '',[],[],[])
            affy_annotation_db[uid] = ai

def parseGene2GO(tax_id,species,overwrite_prev,rewrite_existing):
    global overwrite_previous; overwrite_previous = overwrite_prev; status = 'run'
    program_type,database_dir = unique.whatProgramIsThis()
    if program_type == 'AltAnalyze': database_dir = '/AltDatabase'
    else: database_dir = '/BuildDBs'
    import_dir = database_dir+'/Entrez/Gene2GO'
    g = GrabFiles(); g.setdirectory(import_dir)
    filename = g.searchdirectory('gene2go') ###Identify gene files corresponding to a particular MOD
    if len(filename)>1:
        fn=filepath(filename); gene_go=[]; x = 0
        for line in open(fn,'rU').readlines():             
            data = cleanUpLine(line)
            t = string.split(data,'\t')
            if x == 0: x = 1 ###skip the first line
            else:
                taxid=t[0];entrez=t[1];goid=t[2]
                if taxid == tax_id: gene_go.append([entrez,goid])
    else: status = 'not run'        
    if len(gene_go)>0:
        program_type,database_dir = unique.whatProgramIsThis()
        if program_type == 'AltAnalyze': parent_dir = 'AltDatabase/goelite'
        else: parent_dir = 'Databases'
        
        if overwrite_previous == 'over-write previous':
            if program_type != 'AltAnalyze': import OBO_import; OBO_import.exportVersionData(0,'0/0/0','/'+species+'/nested/')  ### Erase the existing file so that the database is re-remade
        else: parent_dir = 'NewDatabases'
        new_file = parent_dir+'/'+species+'/gene-go/EntrezGene-GeneOntology.txt'
        today = str(datetime.date.today()); today = string.split(today,'-'); today = today[1]+'/'+today[2]+'/'+today[0]

        import EnsemblSQL
        headers = ['EntrezGene ID','GO ID']
        EnsemblSQL.exportListstoFiles(gene_go,headers,new_file,rewrite_existing)

        print 'Exported',len(gene_go),'gene-GO relationships for species:',species
        exportResultsSummary(['Gene2GO.zip'],species,'EntrezGene_GO')  
    else: print 'No NCBI Gene Ontology support for this species'
    return 'run'

def importWikipathways(system_codes,incorporate_previous_associations,process_go,species_full,species,integrate_affy_associations,overwrite_affycsv):
    global wikipathways_file; global overwrite_previous
    overwrite_previous = overwrite_affycsv
    program_type,database_dir = unique.whatProgramIsThis()
    if program_type == 'AltAnalyze': database_dir = '/AltDatabase'
    else: database_dir = '/BuildDBs'
    import_dir = database_dir+'/wikipathways'
    g = GrabFiles(); g.setdirectory(import_dir); wikipathway_gene_db={}; eg_wikipathway_db={}; ens_wikipathway_db={}
    filename = g.searchdirectory('wikipathways') ###Identify gene files corresponding to a particular MOD
    print "Parsing",filename; wikipathways_file = string.split(filename,'/')[-1]
    print "Extracting data for species:",species_full,species
    if len(filename)>1:
        fn=filepath(filename); gene_go={}; x = 0
        for line in open(fn,'rU').readlines():             
            data = cleanUpLine(line)
            data = string.replace(data,'MGI:','')
            t = string.split(data,'\t')
            if x == 0:
                x = 1; y = 0
                while y < len(t):
                    if 'Ensembl' in t[y]: ens = y
                    if 'UniGene' in t[y]: ug = y
                    if 'Entrez' in t[y]: ll = y
                    if 'SwissProt' in t[y]: sp = y
                    if 'RefSeq' in t[y]: rt = y
                    if 'MOD' in t[y]: md= y
                    if 'Pathway Name' in t[y]: pn = y
                    if 'Organism' in t[y]: og= y
                    if 'Url to WikiPathways' in t[y]: ur= y
                    y += 1
            else:
                ensembl = t[ens]; unigene = t[ug]; uniprot = t[sp]; refseq = t[rt]; mod = t[md]; entrez = t[ll]
                ensembl = splitEntry(ensembl); unigene = splitEntry(unigene); uniprot = splitEntry(uniprot)
                pathway_name = t[pn]; organism = t[og]; wikipathways_url = t[ur]; entrez = splitEntry(entrez);
                refseq = splitEntry(refseq); mod = splitEntry(mod); mod2 = []
                for m in mod: mod2.append('mod:'+m); mod = mod2
                gene_ids = mod+ensembl+unigene+uniprot+refseq+entrez
                if organism == species_full:
                    for gene_id in gene_ids:
                        if len(gene_id)>1:
                            try: wikipathway_gene_db[gene_id].append(pathway_name)
                            except KeyError: wikipathway_gene_db[gene_id] = [pathway_name]
                    for gene_id in ensembl:
                        if len(gene_id)>1:
                            try: ens_wikipathway_db[pathway_name].append(gene_id)
                            except KeyError: ens_wikipathway_db[pathway_name] = [gene_id]
                    for gene_id in entrez:
                        if len(gene_id)>1:
                            try: eg_wikipathway_db[pathway_name].append(gene_id)
                            except KeyError: eg_wikipathway_db[pathway_name] = [gene_id]
                        
        print "Number of unique gene IDs linked to Wikipathways for species:",len(wikipathway_gene_db)
        parse_wikipathways = 'yes'
        buildAffymetrixCSVAnnotations(species,incorporate_previous_associations,process_go,parse_wikipathways,integrate_affy_associations,overwrite_affycsv)
        """global affy_annotation_db; affy_annotation_db={}; global gene_annotation_db; gene_annotation_db = {}
        global ens_to_uid; global entrez_to_uid; global entrez_annotations; global parse_wikipathways

        parse_wikipathways = 'yes'        
        import_dir = '/BuildDBs/Affymetrix/'+species
        dir_list = read_directory(import_dir)  #send a sub_directory to a function to identify all files in a directory
        for affy_data in dir_list:    #loop through each file in the directory to output results
            affy_data_dir = 'BuildDBs/Affymetrix/'+species+'/'+affy_data
            parse_affymetrix_annotations(affy_data_dir,species)"""
        #if len(affy_annotation_db)>0 or len(meta)>0:
        try:
            print len(meta), "gene relationships imported"
            print len(wikipathway_gene_db), "gene IDs extracted from Wikipathway pathways"
            """for (primary,gene_id) in meta:
                if gene_id == 'NP_598767': print wikipathway_gene_db[gene_id];kill"""
            ### Since relationships are inferred in new versions of the WikiPathways tables, we don't require meta
            for (primary,gene_id) in meta:
                try:
                    pathway_names = wikipathway_gene_db[gene_id]
                    for pathway in pathway_names:
                        if 'ENS' in primary:
                            try: ens_wikipathway_db[pathway].append(primary)
                            except KeyError: ens_wikipathway_db[pathway] = [primary]
                        else:
                            try:
                                check = int(primary) ### Ensure this is numeric - thus EntrezGene
                                try: eg_wikipathway_db[pathway].append(primary)
                                except KeyError: eg_wikipathway_db[pathway] = [primary]
                            except Exception: null = []
                except KeyError: null=[]
            #print len(eg_wikipathway_db), len(ens_wikipathway_db)
            #print system_codes
            ad = system_codes['EntrezGene']
            system_code = ad.SystemCode()
            if len(eg_wikipathway_db)>0:
                exportGeneToMAPPs(species,'EntrezGene',system_code,eg_wikipathway_db)
            ad = system_codes['Ensembl']
            system_code = ad.SystemCode()
            if len(ens_wikipathway_db)>0:
                exportGeneToMAPPs(species,'Ensembl',system_code,ens_wikipathway_db)
            return len(meta)
        except ValueError: return 'ValueError'
    else: return 'not run'

def splitEntry(str_value):
    str_list = string.split(str_value,',')
    return str_list

def exportGeneToMAPPs(species,system_name,system_code,wikipathway_db):
    program_type,database_dir = unique.whatProgramIsThis()
    if program_type == 'AltAnalyze': parent_dir = 'AltDatabase/goelite'
    else: parent_dir = 'Databases'
    
    if overwrite_previous == 'over-write previous':
        if program_type != 'AltAnalyze':
            #import OBO_import; OBO_import.exportVersionData(0,'0/0/0','/'+species+'/nested/')  ### Erase the existing file so that the database is re-remade
            null = None
    else: parent_dir = 'NewDatabases'
    
    new_file = parent_dir+'/'+species+'/gene-mapp/'+system_name+'-MAPP.txt'
    print "Exporting",new_file
    today = str(datetime.date.today()); today = string.split(today,'-'); today = today[1]+'/'+today[2]+'/'+today[0]
    y=0
    data1 = export.ExportFile(new_file)
    data1.write('ID'+'\t'+'SystemCode'+'\t'+'MAPP'+'\n')
    #print len(wikipathway_db)
    for pathway in wikipathway_db:
        gene_ids = unique.unique(wikipathway_db[pathway])
        #print gene_ids;kill
        for gene_id in gene_ids: data1.write(gene_id+'\t'+system_code+'\t'+pathway+'\n'); y+=1
    data1.close()
    print 'Exported',y,'gene-MAPP relationships for species:',species
    
def extractAndIntegrateAffyData(species,integrate_affy_associations,Parse_wikipathways):
    global affy_annotation_db; affy_annotation_db={}; global gene_annotation_db; gene_annotation_db = {}
    global parse_wikipathways; global meta; meta = {}
    parse_wikipathways = Parse_wikipathways
    if parse_wikipathways == 'yes':
        try: importMetaGeneData(species) ### If meta gene relationships previously built (then don't need Affy files)
        except Exception: null=[]
    
    program_type,database_dir = unique.whatProgramIsThis()
    if program_type == 'AltAnalyze': database_dir = '/AltDatabase/affymetrix'
    else: database_dir = '/BuildDBs/Affymetrix'
    import_dir = database_dir+'/'+species
    dir_list = read_directory(import_dir)  #send a sub_directory to a function to identify all files in a directory
    for affy_data in dir_list:    #loop through each file in the directory to output results
        affy_data_dir = database_dir[1:]+'/'+species+'/'+affy_data
        if '.csv' in affy_data_dir:
            if '.zip' in affy_data_dir:
                ### unzip the file
                print "Extracting the zip file:",filepath(affy_data_dir)
                update.unzipFiles(affy_data,filepath(database_dir[1:]+'/'+species+'/'))
                try:
                    print "Removing the zip file:",filepath(affy_data_dir)
                    os.remove(filepath(affy_data_dir)); status = 'removed'
                except Exception: null=[] ### Not sure why this error occurs since the file is not open
                affy_data_dir = string.replace(affy_data_dir,'.zip','')
            parse_affymetrix_annotations(affy_data_dir,species)
    if len(affy_annotation_db)>0 and integrate_affy_associations == 'yes': exportAffymetrixCSVAnnotations(species,dir_list)
    if parse_wikipathways == 'yes':
        try: exportMetaGeneData(species)
        except Exception: null=[]

def exportAffymetrixCSVAnnotations(species,dir_list):
    import gene_associations; global entrez_annotations
    global ens_to_uid; global entrez_to_uid
    if incorporate_previous_associations == 'yes':    
        ###dictionary gene to unique array ID
        mod_source1 = 'Ensembl'+'-'+'Affymetrix'; mod_source2 = 'EntrezGene'+'-'+'Affymetrix'
        try: ens_to_uid = gene_associations.getGeneToUid(species,mod_source1)
        except Exception: ens_to_uid = {}
        try: entrez_to_uid = gene_associations.getGeneToUid(species,mod_source2)
        except Exception: entrez_to_uid = {}
        ### Gene IDs with annotation information    
        try: entrez_annotations = gene_associations.importGeneData(species,'EntrezGene')
        except Exception: entrez_annotations = {}
        ### If we wish to combine old and new GO relationships - Unclear if this is a good idea
        """if process_go == 'yes':
            entrez_to_go = gene_associations.importGeneGOData(species,'EntrezGene','null')
            ens_to_go = gene_associations.importGeneGOData(species,'Ensembl','null')"""
        integratePreviousAssociations()
    if len(gene_annotation_db)>1:
        exportRelationshipDBs(species)
        exportResultsSummary(dir_list,species,'Affymetrix')

def importAffymetrixAnnotations(dir,Species,Process_go,Extract_go_names,Extract_pathway_names):
    global species; global process_go; global extract_go_names; global extract_pathway_names
    global affy_annotation_db; affy_annotation_db={}; global parse_wikipathways

    parse_wikipathways = 'no'
    species = Species; process_go = Process_go; extract_go_names = Extract_go_names; extract_pathway_names = Extract_pathway_names

    import_dir = '/'+dir+'/'+species
    dir_list = read_directory(import_dir)  #send a sub_directory to a function to identify all files in a directory
    print 'Parsing Affymetrix Annotation files...'
    for affy_data in dir_list:    #loop through each file in the directory to output results
        affy_data_dir = dir+'/'+species+'/'+affy_data
        if '.csv' in affy_data_dir: parse_affymetrix_annotations(affy_data_dir,species)
    return affy_annotation_db

def buildAffymetrixCSVAnnotations(Species,Incorporate_previous_associations,Process_go,parse_wikipathways,integrate_affy_associations,overwrite_affycsv):
    global incorporate_previous_associations; global process_go; global species; global extract_go_names
    global wikipathways_file; global overwrite_previous; overwrite_previous = overwrite_affycsv
    global extract_pathway_names; extract_go_names = 'no'; extract_pathway_names = 'no'
    process_go = Process_go; incorporate_previous_associations = Incorporate_previous_associations; species = Species
    extractAndIntegrateAffyData(species,integrate_affy_associations,parse_wikipathways)
    
def importSystemInfo():
    import UI
    filename = 'Config/source_data.txt'; x=0
    fn=filepath(filename); global system_list; system_list=[]; global system_codes; system_codes={}; mod_list=[]
    for line in open(fn,'rU').readlines():             
        data = cleanUpLine(line)
        t = string.split(data,'\t')
        sysname=t[0];syscode=t[1]
        try: mod = t[2]
        except KeyError: mod = ''
        if x==0: x=1
        else:
            system_list.append(sysname)
            ad = UI.SystemData(syscode,sysname,mod)
            if len(mod)>1: mod_list.append(sysname)
            system_codes[sysname] = ad
    return system_codes

def TimeStamp():
    import time
    time_stamp = time.localtime()
    year = str(time_stamp[0]); month = str(time_stamp[1]); day = str(time_stamp[2])
    if len(month)<2: month = '0'+month
    if len(day)<2: day = '0'+day
    return year+month+day

if __name__ == '__main__':
    getEnsemblAnnotationsFromGOElite('Hs');sys.exit()
    Species_full = 'Rattus norvegicus'; Species_code = 'Rn'; tax_id = '10090'; overwrite_affycsv = 'yes'
    System_codes = importSystemInfo(); process_go = 'yes'; incorporate_previous_associations = 'yes'
    import update; overwrite = 'over-write previous'
    import time; start_time = time.time()
    getArrayAnnotationsFromGOElite({},'Hs','Agilent','yes')
    end_time = time.time(); time_diff = int(end_time-start_time); print time_diff, 'seconds'; kill
    #buildAffymetrixCSVAnnotations(Species_code,incorporate_previous_associations,process_go,'no',integrate_affy_associations,overwrite);kill   
    species_code = Species_code; parseGene2GO(tax_id,species_code,overwrite,'no');kill

    date = TimeStamp(); file_type = ('wikipathways_'+date+'.tab','.txt')
    fln,status = update.download('http://www.wikipathways.org/wpi/pathway_content_flatfile.php?output=tab','BuildDBs/wikipathways/',file_type)
    status = ''
    if 'Internet' not in status:
        importWikipathways(System_codes,incorporate_previous_associations,process_go,Species_full,Species_code,'no',overwrite)