"""
Class to build a dataframe for analysis out of MongoDB
- This is useful for picking out data for 1 or 2 publishers, but when we get up to a large number, it's faster to iterate over the whole snapshot.
- The 'build_allowed_months' function here gets used in the repo a little bit, otherwise, the functions are not used.
- Due to the inconsistencies in publisher names, this is esecially slow to run when publishers have a lot of aliases.
"""

import pandas as pd
import pymongo
import datetime

class PublisherCountsByType:
    
    def __init__(self):
        # initialise client class for interacting with db
        client = pymongo.MongoClient()
        # create or open database
        db = client['unpaywall']
        # create or open collection (table) within database
        self.coll = db['snapshot']
        
    
    def build_df(self, publisher_dct, start_month, end_month):
        df = pd.DataFrame()
        for publisher in publisher_dct:
            print(datetime.datetime.now(), '| Building dataframe for ', publisher)
            publisher_name_ls = publisher_dct[publisher]
            sub_df = self.build_publisher_df(publisher_name_ls,start_month,end_month)
            sub_df['publisher'] = publisher
            df = pd.concat([df,sub_df])
            print(datetime.datetime.now(), '| Found ', sub_df.shape)
        print('DataFrame built:', df.shape)
        return df
    
    def build_allowed_months(self,  start_month, end_month):
        """
        Ad hoc function to build a list of months like '2014-01', '2014-02' etc
        we will use this as labels for the time-periods we are looking at.
        """

        start_y, start_m = tuple([int(x) for x in start_month.split('-')])
        end_y, end_m = tuple([int(x) for x in end_month.split('-')])
        
        year_range = list(range(start_y, end_y+1))

        # if start_y != end_y, then we take everything after the start_month 
        # in the first year and everything before the end month in the end year
        month_range_y1 = range(start_m,12+1)
        month_range_end_y = range(1,end_m+1)

        # if start_y==end_y, this is the month range
        month_range_if_1y = range(start_m, end_m+1)

        allowed_months= list()
        for i,year in enumerate(year_range):
            y = str(year)
            if len(year_range)==1:
                month_range=month_range_if_1y   
            elif i==0:
                month_range = month_range_y1
            elif i == len(year_range)-1:
                month_range = month_range_end_y
            else:
                month_range = range(1,12+1)
            for month in month_range:
                str_m = "{0:0=2d}".format(month)
                yrmo = y + '-' +str_m
                allowed_months.append(yrmo)
        return allowed_months
    
    
    def build_publisher_df(self, publisher_name_ls, start_month,end_month):
        """
        Builds a dataframe of Unpaywall data from a MongoDB query
        Input is just a list of publisher names (many publishers have >1 name in the data).
        """
        data =[]
        allowed_cols = ['doi','genre','has_repository_copy','published_date',
                       'oa_status','is_oa','oa_locations','year']

        start_year = int(start_month[:4])
        end_year = int(end_month[:4])
        years = list(range(start_year,end_year+1))
        
        cur = self.coll.find({'publisher': {'$in':publisher_name_ls},
#                          'genre':'journal-article',
                        'year': {'$in':years}
                             })
        for i,x in enumerate(cur):
            x = {key : x[key] 
                 if key in x
                 else ''
                 for key in allowed_cols}
            data.append(x)
        
        # filter
        df = pd.DataFrame(data)
        df = df[df['genre']=='journal-article']
        df['published_month'] = df['published_date'].map(lambda x: str(x)[:7])
        allowed_months_set = set(self.build_allowed_months(start_month,end_month))
        
        df = df[[x in allowed_months_set for x in df['published_month']]]
        
        
        return df