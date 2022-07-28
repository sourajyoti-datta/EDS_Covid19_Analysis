import subprocess
import os
import pandas as pd
import numpy as np
from datetime import datetime
import requests
import json
import git


    
def get_johns_hopkins():
    ''' Get data by a git pull request, the source code has to be pulled first
        Result is stored in the predifined csv structure
    '''
    # git_pull = subprocess.Popen( "/usr/bin/git pull" ,
    #                      cwd = os.path.dirname( 'data/raw/COVID-19/' ),
    #                      shell = True,
    #                      stdout = subprocess.PIPE,
    #                      stderr = subprocess.PIPE )
    # (out, error) = git_pull.communicate()


    # print("Error : " + str(error))
    # print("out : " + str(out))
    
    git_url = "https://github.com/CSSEGISandData/COVID-19.git"
    repo_dir = "../data/raw/COVID-19"
    branch = "master"

    try:
        g = git.cmd.Git(repo_dir)
        msg = g.pull()
        print(msg)
    except:
        git.Repo.clone_from(git_url, repo_dir, branch=branch, single_branch=True, depth=1)



def get_current_data_germany():
    ''' Get current data from germany, attention API endpoint not too stable
        Result data frame is stored as pd.DataFrame
    '''
    # 400 regions / Landkreise
    data = requests.get('https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_Landkreisdaten/FeatureServer/0/query?where=1%3D1&outFields=*&outSR=4326&f=json')

    json_object = json.loads(data.content)
    full_list = []
    for pos,each_dict in enumerate (json_object['features'][:]):
        full_list.append(each_dict['attributes'])

    pd_full_list = pd.DataFrame(full_list)
    pd_full_list.to_csv('../data/raw/NPGEO/GER_state_data.csv',sep=';')
    print(' Number of regions rows: ' + str(pd_full_list.shape[0]))
    
    
    
def get_world_population_data():
    url = 'https://api.worldbank.org/v2/en/indicator/SP.POP.TOTL?downloadformat=csv'

    # Downloading the file by sending the request to the URL
    req = requests.get(url)
     
    # Split URL to get the file name
    filename = "../data/raw/global_population_data.zip"
     
    # Writing the file to the local file system
    with open(filename,'wb') as output_file:
        output_file.write(req.content)
        
    print("World propulation raw ZIP data downloaded.")


    