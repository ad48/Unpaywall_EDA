'''
Iterate over the snapshot file and retrieve summary data for each publisher
'''

import os
import json
import pandas as pd
import datetime
import gzip

from .PublisherNameConsolidator import PublisherNameConsolidator
from .PublisherCountsByType import PublisherCountsByType


class UnpaywallDataFrame:
    
    
    def __init__(self, snapshot_path, dataframe_path, allowed_months):
        self.snapshot_path = snapshot_path
        self.dataframe_path = dataframe_path
        self.allowed_months = allowed_months
    
    def build_load_dataframe(self):
        if not os.path.exists(self.dataframe_path):
            self.build_dataframe(self.snapshot_path)
        return pd.read_csv(self.dataframe_path)
    
    def build_dataframe(self, filepath):
        fail_yr_none = 0
        fail_type_none = 0
        yrmo_counts_dct = dict()
        publisher_name_consolidator = PublisherNameConsolidator().publisher_name_consolidator
        with gzip.open(filepath,'rb') as f:
            print('Building dataframe from file. This will take some time...')
            i = 0
            for line in f:
                try:
                    record = json.loads(line)
                    yrmo = self.get_yrmo(record)
                    article_type = self.get_article_type(record)

                    if any([x==None for x in[yrmo,article_type]]):
                        if yrmo==None:
                            fail_yr_none +=1
                        if article_type==None:
                            fail_type_none +=1
                        continue
                    
                    publisher = self.get_publisher(record,publisher_name_consolidator)
                    oa_type = self.get_principal_oa_type(record)
                    green_status = self.get_green_status(record)
                    yrmo_counts_dct = self.update_yrmo_counts_dct(yrmo_counts_dct, yrmo,publisher,oa_type, green_status)

                except Exception as e:
                    print(record)
                    print(e)
                    break
                i+=1
                if i%1e7==0 or i<=3:
                    print(datetime.datetime.now(), i, 'rows scanned')
                

        # make into rows
        rows = self.get_rows(yrmo_counts_dct)

        df = pd.DataFrame(rows)
        df = df.sort_values('month',ascending=True)
        df.to_csv(self.dataframe_path, index=False)
        print('DataFrame Created and written to file')
        print('Failures on year:', fail_yr_none)
        print('Failures on article_type:', fail_type_none)

    
    def get_article_type(self,record):
        article_type = record.get('genre',None)
        if article_type!='journal-article':
            article_type=None
        return article_type

    def get_yrmo(self,record):
        pubdate = record.get('published_date',None)
        if pubdate ==None:
            year = record.get('year',None)
            if year == None:
                yrmo = None
            else:
                yrmo = str(year)+'-01'
        else:
            yrmo = pubdate[:7]
        return yrmo

    def get_publisher(self,record,publisher_name_consolidator):
        publisher = record.get('publisher', None)
        if publisher in publisher_name_consolidator and publisher !=None:
            publisher = publisher_name_consolidator[publisher]
        else:
            pass
        return publisher


    def get_principal_oa_type(self,record):
        if record.get('oa_status',None)!=None:
            return record.get('oa_status',None)

    def get_green_status(self,record):
        green_status = False
        oa_locs = record.get('oa_locations',[])
        if type(oa_locs)==list and len(oa_locs)>0:
            for oa_loc in oa_locs:
                if oa_loc.get('host_type','')=='repository':
                    green_status = True
        return green_status


    def update_yrmo_counts_dct(self,yrmo_counts_dct, yrmo,publisher,oa_type,green_status):
        oa_type_names = {'subscription':'closed',
                             'hybrid':'hybrid',
                             'gold':'gold',
                             'bronze':'bronze',
                             'green':'green',}
        empty_record = {'count':1,
                        'subscription_count':0,
                        'hybrid_count':0,
                        'gold_count':0,
                        'bronze_count':0,
                       'green_count':0,
                       'bronze_green_count':0,
                       'gold_green_count':0,
                       'hybrid_green_count':0}
        allowed_months_set = set(self.allowed_months)
        if yrmo in allowed_months_set:
            if yrmo not in yrmo_counts_dct:
                yrmo_counts_dct[yrmo] = dict()
                yrmo_counts_dct[yrmo][publisher] = empty_record
            else:
                if publisher not in yrmo_counts_dct[yrmo]:
                    yrmo_counts_dct[yrmo][publisher] = empty_record
                else:
                    yrmo_counts_dct[yrmo][publisher]['count']+=1

            for oa_type_name in oa_type_names:
                if oa_type == oa_type_names[oa_type_name]:
                    yrmo_counts_dct[yrmo][publisher][oa_type_name+'_count'] += 1
                    if green_status == True and oa_type_name not in {'green','subscription'}:
                        yrmo_counts_dct[yrmo][publisher][oa_type_name+'_green_count'] += 1

        return yrmo_counts_dct

    def get_rows(self,yrmo_counts_dct):
        rows = []
        for yrmo in yrmo_counts_dct:
            for publisher in yrmo_counts_dct[yrmo]:
                row = yrmo_counts_dct[yrmo][publisher]
                row['publisher'] = publisher
                row['month'] = yrmo
                rows.append(row)
        return rows