import numpy as np
from sklearn import linear_model
import pandas as pd
from scipy import signal
from datetime import timedelta



def impute_missing_recovered_data(pd_result_larg, 
                                  impute_start_date = pd.to_datetime("08-05-2021"), 
                                  look_back = 10,
                                  recovery_ratio_in_lookback = 0.95
                                 ):
    '''
    Impute the full data, for the recovered field
    '''
    for country in list(pd_result_larg.country.unique()):
        state_list = pd_result_larg[pd_result_larg['country'] == country].state.unique()
        for state in state_list:
            pd_sub = pd_result_larg[(pd_result_larg['country'] == country) & 
                                    (pd_result_larg['state'] == state)]
            d = pd_sub[pd.to_datetime(pd_sub.date) >= impute_start_date].deaths.reset_index(drop=True) - pd_sub[pd.to_datetime(pd_sub.date) >= impute_start_date - timedelta(days=1)].deaths.reset_index(drop=True)[0:-1]
            c = pd_sub.confirmed[-d.shape[0]-look_back:-look_back].reset_index(drop=True) - pd_sub.confirmed[-d.shape[0]-look_back-1:-look_back-1].reset_index(drop=True)
            r = pd_sub[pd.to_datetime(pd_sub.date) == impute_start_date - timedelta(days=1)].recovered.values[0]
            impute = r + ((recovery_ratio_in_lookback*c) - d).cumsum()
            pd_result_larg.loc[(pd_result_larg['country'] == country) & 
                               (pd_result_larg['state'] == state) &
                               (pd.to_datetime(pd_result_larg['date']) >= impute_start_date), 
                               'recovered'] = list(impute.fillna(0).astype(int))
                               
    return pd_result_larg



def savgol_filter(df_input, column='confirmed', window=5):
    ''' Savgol Filter which can be used in groupby apply function (data structure kept)

        parameters:
        ----------
        df_input : pandas.series
        column : str
        window : int
            used data points to calculate the filter result

        Returns:
        ----------
        df_result: pd.DataFrame
            the index of the df_input has to be preserved in result
    '''

    degree=1
    df_result=df_input

    filter_in=df_input[column].fillna(0) # attention with the neutral element here

    result=signal.savgol_filter(np.array(filter_in),
                           window, # window size used for filtering
                           1)
    df_result[str(column+'_filtered')]=result
    return df_result



def calc_filtered_data(df_input, filter_on='confirmed'):
    '''  Calculate savgol filter and return merged data frame

        Parameters:
        ----------
        df_input: pd.DataFrame
        filter_on: str
            defines the used column
        Returns:
        ----------
        df_output: pd.DataFrame
            the result will be joined as a new column on the input data frame
    '''

    must_contain=set(['state','country',filter_on])
    assert must_contain.issubset(set(df_input.columns)), 'Error in calc_filtered_data, not all columns in data frame'

    df_output=df_input.copy() # we need a copy here otherwise the filter_on column will be overwritten

    pd_filtered_result=df_output[['state','country',filter_on]].groupby(['state','country']).apply(savgol_filter)#.reset_index()

    #print('--+++ after group by apply')
    #print(pd_filtered_result[pd_filtered_result['country']=='Germany'].tail())

    #df_output=pd.merge(df_output,pd_filtered_result[['index',str(filter_on+'_filtered')]],on=['index'],how='left')
    df_output=pd.merge(df_output,pd_filtered_result[[str(filter_on+'_filtered')]],left_index=True,right_index=True,how='left')
    #print(df_output[df_output['country']=='Germany'].tail())
    return df_output



def get_daily_list(total_list):
    ''' Calculate Daily change in cases from the cummulative gathered list

        Parameters:
        ----------
        total_list: list
            A python list containing the cummulative cases
        
        Returns:
        ----------
        df_output: list
            the result will be a list containing daily change in values
    '''
    daily_list=[]
    daily_list.append(total_list.pop(0))
    for each in range(len(total_list)):
        if each == 0:
            daily_list.append(max(0, total_list[each] - total_list[0]))
        else:
            daily_list.append(max(0, total_list[each] - total_list[each-1]))
    
    return daily_list



def calc_daily_values_all_countries(pd_daily):
    ''' Calculate Daily cummulative cases for all countries

        Parameters:
        ----------
        all_countries: list
            A python list containing name of all countries
        
        Returns:
        ----------
        df_daily_all: pandas dataframe
            the result will be a list containing daily change in values
    '''
    all_countries = pd_daily['country'].unique()
    df_daily_all= pd.DataFrame()
    for each_country in all_countries:
        daily_list = get_daily_list(list(pd_daily[pd_daily['country'] == each_country]['confirmed']))
        df_daily = pd.DataFrame(np.array(daily_list))
        df_daily_death = np.array(get_daily_list(list(pd_daily[pd_daily['country'] == each_country]['deaths'])))
        df_daily_recov = np.array(get_daily_list(list(pd_daily[pd_daily['country'] == each_country]['recovered'])))
        
        df_daily = df_daily.rename(columns = {0:'daily_confirmed'})
        df_daily['daily_deaths'] = df_daily_death
        df_daily['daily_recovered'] = df_daily_recov
        df_daily['date'] = np.array(pd_daily[pd_daily['country'] == each_country]['date'])
        df_daily['country'] = np.array(pd_daily[pd_daily['country'] == each_country]['country'])
        df_daily_all = pd.concat([df_daily_all,df_daily])

    return df_daily_all



def build_features(impute_recovered = False):

    ##### Build the cumulative data
    
    pd_JH_data = pd.read_csv('../data/processed/COVID_relational_confirmed.csv',sep=';',parse_dates=[0])
    pd_JH_data = pd_JH_data.sort_values('date',ascending=True)
    
    pd_result_larg = calc_filtered_data(pd_JH_data)
    
    pd_JH_data_deaths = pd.read_csv('../data/processed/COVID_relational_deaths.csv',sep=';',parse_dates=[0])
    pd_JH_data_deaths = pd_JH_data_deaths.sort_values('date',ascending=True).reset_index(drop=True)
    pd_result_larg = pd.merge(pd_result_larg, pd_JH_data_deaths, on=['date', 'state', 'country'], how='left')
    
    pd_JH_data_recov = pd.read_csv('../data/processed/COVID_relational_recovered.csv',sep=';',parse_dates=[0])
    pd_JH_data_recov = pd_JH_data_recov.sort_values('date',ascending=True).reset_index(drop=True)
    pd_result_larg = pd.merge(pd_result_larg, pd_JH_data_recov, on=['date', 'state', 'country'], how='left')
    
    if impute_recovered:
        pd_result_larg = impute_missing_recovered_data(pd_result_larg)
    
    pd_result_larg.to_csv('../data/processed/COVID_final_set.csv',sep=';',index=False)
    
    ##### Build the daily data
    
    pd_daily = pd_result_larg[['date','state','country','confirmed','deaths','recovered']].groupby(['country','date']).agg(np.sum).reset_index()

    df_daily_all = calc_daily_values_all_countries(pd_daily)
    df_daily_all = df_daily_all.reset_index(drop=True)
    df_daily_all.daily_deaths = df_daily_all.daily_deaths.mask(df_daily_all.daily_deaths.lt(0), 0)
    df_daily_all.to_csv('../data/processed/COVID_final_daily_set.csv',sep=';',index=False)
    
    print("Processed data ready.")



def build_latest_global_statistics():
    
    # getting location information
    data_path = '../data/raw/COVID-19/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
    pd_loc = pd.read_csv(data_path)
    pd_loc = pd_loc.rename(columns = {'Country/Region':'country',
                                            'Province/State':'state'})
    pd_loc['state'] = pd_loc['state'].fillna('no')
    pd_loc = pd_loc[['country', 'Lat', 'Long']]
    pd_loc = pd_loc.groupby('country').mean().reset_index()
    
    # getting latest COVID data
    df_input_large = pd.read_csv('../data/processed/COVID_final_set.csv', sep=';')
    df_input_large['date'] = pd.to_datetime(df_input_large['date'])

    df_input_large = df_input_large[df_input_large['date'] == df_input_large['date'].max()].drop('confirmed_filtered', axis=1)
    year = str(df_input_large['date'].max().year-1)

    df_input_large = df_input_large.groupby(['country']).sum().reset_index()

    df_global_latest_stats = pd.merge(df_input_large, pd_loc, on=['country'], how='left')
    
    ## Get population data
    df_population_data = pd.read_csv('../data/processed/world_population_data.csv', sep=',')
    df_population_data = df_population_data[['Country Name', year]]
    df_population_data.columns = ['country', 'population']

    df_global_latest_stats = pd.merge(df_global_latest_stats, df_population_data, on='country', how='inner')
    df_global_latest_stats = df_global_latest_stats[df_global_latest_stats.population.notnull()]
    
    df_global_latest_stats['active'] = df_global_latest_stats['confirmed'] - (df_global_latest_stats['deaths'] + df_global_latest_stats['recovered'])
    df_global_latest_stats.loc[df_global_latest_stats['active'] < 0, 'active'] = 0
    
    # calculating the ratio to population
    for val in ['confirmed', 'deaths', 'recovered', 'active']:
        df_global_latest_stats['{}_ratio'.format(val)] = df_global_latest_stats[val]/df_global_latest_stats['population']
    
    df_global_latest_stats.to_csv('../data/processed/global_latest_stats.csv', sep=";", index=False)
    
    print("Global Statistics ready. No of records stored:", df_global_latest_stats.shape[0])