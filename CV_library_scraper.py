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

class CVScraper:
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

    def normalize(self, text):
        return re.sub(r'[^a-z0-9]', '', text.lower().strip())
    
    def clean_text(self, text):
        """Clean text of problematic characters and encoding issues"""
        if not text:
            return ""
        
        text = unicodedata.normalize('NFKD', text)
        text = text.replace('\u00a0', ' ')
        text = text.replace('\u2013', '-')
        text = text.replace('\u2014', '-')
        text = text.replace('\u2018', "'")
        text = text.replace('\u2019', "'")
        text = text.replace('\u201c', '"')
        text = text.replace('\u201d', '"')
        text = text.replace('\u00e9', 'e')
        text = text.replace('\u00f1', 'n')
        text = ''.join(char for char in text if char.isprintable() or char in ['\n', '\t'])
        
        return text.strip()

    def scrape_jobs(self, job_keyword):
        seen_jobs = set()
        page = 1
        url = f'https://www.cv-library.co.uk/{job_keyword}-jobs-in-london?page={page}&us=1'
        browser = webdriver.Firefox(options=options)
        browser.get(url)

        try:
            textelem = browser.find_elements(By.CSS_SELECTOR, 'h2.job__title')
            for elem in textelem:
                self.titles.append(elem.text)
        except:
            textelem = []
        #print(len(self.titles))
        try:
            companyelem = browser.find_elements(By.CSS_SELECTOR, 'a.job__company-link')
            #count = 0
            totalelems = []
            for elem in companyelem:
                if elem.text:
                    totalelems.append(elem.text)
            for i in range(len(totalelems)):
                if (i >= 2 and i <= 4) or (i >= 7 and i <= 9):
                    continue
                self.companies.append(totalelems[i])
            #print(count)
        except:
            companyelem = []

        try:
            locaelem = browser.find_elements(By.CSS_SELECTOR, 'span.job__details-location')
            for elem in locaelem:
                self.locations.append(elem.text)
        except:
            locaelem = []

        try:
            urlelem = browser.find_elements(By.CSS_SELECTOR, 'h2.job__title a')

            for u in urlelem:
                self.urls.append(u.get_attribute('href'))
            print(len(self.urls))
        except:
            urlelem = []
        
        

        unique_jobs = []
        for t, c, u, l in zip(self.titles, self.companies, self.urls, self.locations):
            job_id = f"{self.normalize(t)}_{self.normalize(c)}_{self.normalize(l)}"
            if job_id not in seen_jobs:
                seen_jobs.add(job_id)
                unique_jobs.append((t, c, l, u))

        self.titles = [job[0] for job in unique_jobs]
        self.companies = [job[1] for job in unique_jobs]
        self.locations = [job[2] for job in unique_jobs]
        self.urls = [job[3] for job in unique_jobs]

    def jd_extraction(self):
        browser = webdriver.Firefox(options=options)
        for u in self.urls:
            try:
                browser.get(u)
                time.sleep(np.random.uniform(3, 5))
                try:
                    premiumdescelem = browser.find_elements(By.CSS_SELECTOR, 'div.premium-description')
                    if premiumdescelem:
                        cleaned_desc = self.clean_text(premiumdescelem[0].text)
                        self.job_description.append(cleaned_desc)
                        continue
                except:
                    premiumdescelem = []

                normaldescelem = browser.find_elements(By.CSS_SELECTOR, 'div.job__description')
                cleaned_desc = self.clean_text(normaldescelem[0].text)
                self.job_description.append(cleaned_desc)

            except:
                print(f"Failed to load job description for {u}")
                self.job_description.append("Description not available")
                self.job_skills.append("N/A")
        

if __name__ == '__main__':
    scraper = CVScraper(output_filename="cv_scraper")
    job_keyword = "Data Analyst"
    converted = job_keyword.lower().replace(" ", "-")
    scraper.scrape_jobs(converted)

    
    scraper.jd_extraction()


    print(len(scraper.titles))
    print(len(scraper.companies))
    print(len(scraper.locations))
    print(len(scraper.urls))
    print(len(scraper.job_description))

    for desc in scraper.job_description:
        print(desc)
    