# imports
import time
from bs4 import BeautifulSoup
import random
import numpy as np
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException

# initializing driver
driver = webdriver.Chrome()

# get url + initialize driver
url = "https://omero.mit.edu/webclient/?show=project-503"  # Replace with your desired URL
driver.get(url)

# random amount of time to sleep
sleep_time = random.randint(3, 7)
time.sleep(sleep_time)

htmls = []

# find subfolders of the main folders
subfolders = driver.find_elements(By.CLASS_NAME, "jstree-closed")

for i in range(len(subfolders)):
    driver.execute_script("arguments[0].scrollIntoView();", subfolders[i])
    print(subfolders[i].text)
    
    subfolders[i].click()
    
    click_time = random.randint(2, 6)
    time.sleep(click_time)
    
    htmls.append(driver.page_source)
    
    buttons = driver.find_elements(By.CLASS_NAME, "button_pagination")
    
    for i in range(len(buttons)):
        button = buttons[0]
        
        try:
            button.click()
            
            click_time = random.randint(2, 6)
            time.sleep(click_time)

            htmls.append(driver.page_source)
        
        except StaleElementReferenceException:
            # If a stale element exception occurs, re-fetch the buttons list
            buttons = driver.find_elements(By.CLASS_NAME, "button_pagination")
    
# quit driver
driver.quit()

soup_list = [BeautifulSoup(html, 'html.parser') for html in htmls]

# Initialize a variable to store the current parent ID
current_parent_id = None

# Lists to store data
parent_ids = []
parent_names = []
child_ids = []
child_names = []
child_parent_ids = []

# Find all the parent nodes (li elements with class 'jstree-node')
for soup in soup_list:
    parent_nodes = soup.find_all('li', class_='jstree-node')
    
    for parent_node in parent_nodes:
        child_nodes = parent_node.find_all('li', class_='jstree-node')
    
        # Check if the parent node has child nodes or lacks nested <ul> (like 'Cancer cell extravasation 7-20-22')
        if len(child_nodes) >= 1:
            # This is a parent node
            parent_id = parent_node.get('data-id')
            parent_name = parent_node.find('span', class_='jstree-anchor').text.strip()
            current_parent_id = parent_id  # Update the global current_parent_id
            parent_ids.append(parent_id)
            parent_names.append(parent_name)
        
            # Recursively process child nodes
            # for child_node in child_nodes:
            #    extract_nodes(child_node)
        
        else:
            # This is a child node
            child_id = parent_node.get('data-id')
            child_name = parent_node.find('span', class_='jstree-anchor').text.strip()
            child_ids.append(child_id)
            child_names.append(child_name)
            child_parent_ids.append(current_parent_id)
    
# data dictionary for the parent df
data_parent = {
    'Parent ID': parent_ids,
    'Parent File Name': parent_names
}

# making sure the arrays are the same size so the df gets created
child_links = np.zeros(len(child_parent_ids))

# data dictionary for the child df
data_child = {
    'Child ID': child_ids,
    'Child File Name': child_names,
    'Child Parent ID': child_parent_ids,
    'Child Links': child_links
}

# putting into dataframes
df_parent = pd.DataFrame(data_parent)
df_child = pd.DataFrame(data_child)

# extracting data and creating the links
for index, row in df_child.iterrows():
    child_id = row['Child ID']
    parent_id = row['Child Parent ID']
    df_child.loc[index, 'Child Links'] = f"https://omero.mit.edu/webclient/img_detail/{child_id}/?dataset={parent_id}"
    
# removing duplicates
df_parent.drop_duplicates(inplace=True)
df_child.drop_duplicates(inplace=True)

# Check if child IDs in df_child are in parent IDs in df_parent
df_child = df_child[~df_child['Child File Name'].isin(df_parent['Parent File Name'])]
df_child = df_child[df_child['Child ID'].notna()]

# Reset the index of df_child
df_child.reset_index(drop=True, inplace=True)

pd.set_option('display.max_rows', None)
print(df_parent)
print(df_child)

# output to excel
output_filename = 'filename_links.xlsx'

# Create a Pandas Excel writer using ExcelWriter
with pd.ExcelWriter(output_filename) as writer:
    df_parent.to_excel(writer, sheet_name='parent', index=False)
    df_child.to_excel(writer, sheet_name='child', index=False)
    
print("done")