import pandas as pd
import numpy as np
from datetime import datetime
import shutil
import glob
import os



def store_relational_JH_data_type(case_type):
    ''' Transformes the COVID data into a relational data set
    '''

    data_path = '../data/raw/COVID-19/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_{}_global.csv'.format(case_type)
    pd_raw = pd.read_csv(data_path)

    pd_data_base = pd_raw.rename(columns = {'Country/Region':'country',
                                            'Province/State':'state'})

    pd_data_base['state'] = pd_data_base['state'].fillna('no')

    pd_data_base = pd_data_base.drop(['Lat','Long'],axis=1)


    pd_relational_model = pd_data_base.set_index(['state','country']) \
                                .T                              \
                                .stack(level=[0,1])             \
                                .reset_index()                  \
                                .rename(columns={'level_0':'date',
                                                 0:case_type},
                                       )

    pd_relational_model['date'] = pd_relational_model.date.astype('datetime64[ns]')

    pd_relational_model.to_csv('../data/processed/COVID_relational_{}.csv'.format(case_type),sep=';',index=False)
    print('{} cases processed. Number of rows stored: '.format(case_type) + str(pd_relational_model.shape[0]))
    


def store_relational_JH_data():
    ''' Transformes the COVID data into a relational data set, for confirmed, deaths and recovered
    '''
    store_relational_JH_data_type("confirmed")
    store_relational_JH_data_type("deaths")
    store_relational_JH_data_type("recovered")
    
    
    
def process_world_population_data():
    filename = "../data/raw/global_population_data.zip"
    dir_name = '../data/raw/global_population_data/'
    
    shutil.unpack_archive(filename, dir_name)
    
    list_of_files = filter( os.path.isfile,
                            glob.glob(  dir_name + '*') )
    max_file = max( list_of_files,
                    key =  lambda x: os.stat(x).st_size)
    max_filename = os.path.split(max_file)[-1]
    
    file = "../data/raw/global_population_data/{}".format(max_filename)
    
    with open(file, 'r') as file_r_obj:
        lines = file_r_obj.readlines()
        
    write_file = "../data/processed/world_population_data.csv"
        
    with open(write_file, 'w') as file_w_obj:
        for i in range(4, len(lines)):
            file_w_obj.write(lines[i])
    
    df_population_data = pd.read_csv('../data/processed/world_population_data.csv', sep=',')
    df_population_data.loc[df_population_data['Country Code']=='USA', 'Country Name'] = 'US'
    df_population_data.to_csv('../data/processed/world_population_data.csv', sep=',', index=False)

    print("World propulation data CSV prepared. Number of records stored:", df_population_data.shape[0])


def store_confirmed_data_for_sir():
    data_path = '../data/raw/COVID-19/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
    pd_raw = pd.read_csv(data_path)
    pd_raw = pd_raw.drop(['Lat','Long','Province/State'],axis=1)
    pd_raw = pd_raw.rename(columns={'Country/Region':'country'})
    pd_flat_table = pd_raw.set_index('country') \
                    .T \
                    .stack(level=[0]) \
                    .reset_index() \
                    .rename(columns={'level_0':'date',
                                    0:'confirmed'}
                                    )
    pd_flat_table['date'] = pd_flat_table.date.astype('datetime64[ns]')
    pd_flat_table = pd.pivot_table(pd_flat_table, values='confirmed', index='date', columns='country', aggfunc=np.sum, fill_value=0).reset_index()
    pd_flat_table.to_csv('../data/processed/COVID_full_flat_table.csv',sep=';',index = False)
    #print(pd_flat_table.tail())
    print('Data processed for SIR modelling. Number of rows stored in Full Flat Table: '+str(pd_flat_table.shape[0]))
    


