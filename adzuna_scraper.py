from selenium import webdriver
import re, unicodedata, json, pandas as pd, os
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException
import time
import numpy as np
from functools import wraps
from collections import defaultdict
from datetime import datetime, timedelta
import argparse
from selenium.webdriver.common.keys import Keys
options = Options()
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
class AdzunaScraper:
    def __init__(self, output_filename = 'linkedIn_jobs', format = 'all'):
        self.titles = []
        self.companies = []
        self.urls = []
        self.job_description= []
        self.job_skills = []
        self.output_filename = output_filename
        #self.json_filename = ''
        self.format = format.lower()
        self.job_title_short = []
        self.locations = []
        self.salary = []
        self.degree = []
        self.health_insurance = []
        self.work_from_home = []
        self.schedule = []
        self.salary_rate = []

    def scrape_jobs(self, job_keyword, n_pages):

        url = f'https://www.adzuna.co.uk/jobs/search?loc=86384&q={job_keyword}&p={n_pages}'
        browser = webdriver.Firefox(options=options)
        browser.get(url)

        titleelem_list = browser.find_elements(By.CSS_SELECTOR, 'a[data-js="jobLink"]')

        for title in titleelem_list:
            if title.text:
                self.titles.append(title.text)

        companyelem_list = browser.find_elements(By.CSS_SELECTOR, 'div.ui-company')

        for company in companyelem_list:
            self.companies.append(company.text)

        sal_list = browser.find_elements(By.CSS_SELECTOR, 'div.ui-salary')

        for sal in sal_list:
            match = re.search(r'(£[\d,]+)', sal.text)
            if match:
                value = match.group(1)
                self.salary.append(value)

        locaelem_list = browser.find_elements(By.CSS_SELECTOR, 'div.ui-location')
        for loca in locaelem_list:
            temp = loca.text
            res = ''
            for i in range(len(temp)):
                if temp[i] == ' ' and i > 0 and temp[i-1] == ' ' or temp[i] == '+':
                    break
                else:
                    res += temp[i]
            if res:
                cleaned = re.sub(r'[\r\n]+', '', res)
                self.locations.append(cleaned.rstrip(','))

        urlelem_list = browser.find_elements(By.CSS_SELECTOR, 'a[data-js="jobLink"]')
        for u in urlelem_list:
            
            temp = u.get_attribute('href')
            if self.urls and temp != self.urls[-1]:
                self.urls.append(temp)
            elif not self.urls:
                self.urls.append(temp)
            else:
                continue
        for title, company, loca, u, sal in zip(self.titles, self.companies, self.locations, self.urls, self.salary):
            print(title)
            print(company)
            print(loca)
            print(u)
            print(sal)
            print("="*50)

if __name__ == '__main__':
    scraper = AdzunaScraper()
    job_keyword = "Data Analyst"
    page_number = 2
    scraper.scrape_jobs(job_keyword, page_number)