"""
This simple class attempts to consolidate all the different names that appear for publishers in Unpaywall data
Consider that using member_ids in CrossRef data might be a smarter way to do this. 
"""

import pymongo

class PublisherNameConsolidator:
    
    def __init__(self):
        client = pymongo.MongoClient()
        db = client['unpaywall']
        coll = db['snapshot']
        publishers = list(coll.distinct('publisher'))
        self.publisher_dct = {
                    'CUP':[str(x) for x in publishers if x=='CUP' or 'Cambridge University Press' in str(x)],
                    'OUP': [str(x) for x in publishers if x=='OUP' or 'Oxford University Press' in str(x)],
                    'SAGE': [str(x) for x in publishers if 'SAGE' in str(x)],
                    'Elsevier': [str(x) for x in publishers if any(
                                                                            [y in str(x) ## Close matches
                                                                            for y in ['Harcourt','Morgan Kaufmann','Cell Press',
                                                                                      'Churchill Livingstone','Pergamon','B Saunders','B. Saunders']
                                                                           ] +
                                                                           [z == str(x) ## Exact matches
                                                                             for z in ['Butterworth-Heinemann Ltd.','Academic Press','Medicine Publishing']] +
                                                                            ['Elsevier' in str(x)] 

                                                                          ) and all(
                                                                            [a not in str(x) for a in ['V. Masson','G. Masson', 'V Masson', 'G Masson']]
                                                                            )],

                    'Springer' : [str(x) for x in publishers if any(
                                                                            [y in str(x) ## Close matches
                                                                            for y in ['Palgrave','Biomed Central','BioMed Central','MacMillan','Macmillan']
                                                                           ] +
                                                                           [z == str(x) ## Exact matches
                                                                             for z in ['Vogel ','Vogel,']] +
                                                                            ['Nature Publishing' in str(x) or 'Springer' in str(x)]
                                                                          )],
                    'Wiley': [str(x) for x in publishers if any([y in str(x) ## Close matches
                                                                            for y in ['Jossey-Bass','Wrox Press','Wrightbooks','Howell Book House','Audel','Capstone']
                                                                           ]
                                                                          + [z == str(x) ## Exact matches
                                                                             for z in ['Pfeiffer','Pfeiffer: A Wiley Imprint']]
                                                                           + ['Wiley' in str(x) or 'Blackwell' in str(x)]
                                                                          )],
                    'T+F' : [str(x) for x in publishers if any([y in str(x) ## Close matches
                                                                            for y in ['Informa ','F1000', 'Faculty of 1000','Cogent','Routledge','Garland Science','Spon Press']
                                                                           ]
                                                                          + [z == str(x) ## Exact matches
                                                                             for z in ['Psychology Press']]
                                                                           + ['Taylor' in str(x) and 'Francis' in str(x)]
                                                                          )],
                    'MDPI': ['MDPI', 'MDPI AG'],
                    }
        publisher_name_consolidator = dict()
        for key, value in self.publisher_dct.items():
            for string in value:
                publisher_name_consolidator.setdefault(string, key)
        self.publisher_name_consolidator = publisher_name_consolidator