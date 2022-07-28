import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
from scipy import optimize
from scipy import integrate

'''
Default paramter initializations
'''
N0 = 0
I0 = 100        # Initial Infected population
S0 = 0          # Initial Suspected population
R0 = 0          # Initial Recovered population
beta = 0.5      # Initial Rate of infection
gamma = 0.1     # Initial Rate of recovery
t = 0

def Handle_SIR_Modelling(ydata):
    global t
    t = np.arange(len(ydata))
    
    global I0
    I0 = ydata[0]   #Infected population
    popt, pcov = optimize.curve_fit(fit_odeint, t, ydata, maxfev=10000)
    fitted = fit_odeint(t, *popt)
    return t, ydata, fitted

def SIR_model_fit(SIR, time, beta, gamma):
    '''
    Simple SIR model implementation.
    S: Suspected population
    I: Infected population
    R: Recovered population
    beta: rate of infection
    gamma: rate of recovery
    time: for integral as define in odeint function of scipy.integrate
    as per slides: ds+dI+dR = 0 and S+R+I=N (total population)

    Make a note tht in this model a recovered person can not get infected again.
    '''

    S,I,R = SIR
    dS_dt = -beta*S*I/N0
    dI_dt = beta*S*I/N0 - gamma*I
    dR_dt = gamma*I

    return dS_dt, dI_dt, dR_dt

def fit_odeint(x, beta, gamma):
    ''' To call integrate funtion of scipy'''
    return integrate.odeint(SIR_model_fit, (S0, I0, R0), t, args=(beta, gamma))[:,1]  #we are only fetching dI

def exec_SIR_modelling():
    print('SIR Modelling Started.')
    df_analyse = pd.read_csv('../data/processed/COVID_full_flat_table.csv', sep=';')
    df_analyse.sort_values('date', ascending=True)
    
    year = str(pd.to_datetime(df_analyse['date']).dt.year.min())
    
    df_analyse = df_analyse.drop(['date'],axis=1)
    df_SIR_model = pd.DataFrame()
    
    df_population_data = pd.read_csv('../data/processed/world_population_data.csv', sep=',')

    for each_country in df_analyse:
        if each_country in list(df_population_data['Country Name']):
            global N0
            global S0
            global I0
            N0 = df_population_data[df_population_data['Country Name'] == each_country][year].values[0]
            S0 = N0 - I0
            ydata = np.array(df_analyse[each_country][35:150])
            t, ydata, fitted = Handle_SIR_Modelling(ydata)
            df_SIR_model[each_country] = fitted
        
    df_SIR_model.to_csv('../data/processed/COVID_SIR_Model_Data.csv',sep=';', index = False)
    print(df_SIR_model.shape[0],'rows generated for', df_SIR_model.shape[1], 'countries.')
    print('SIR Modelling Completed.')