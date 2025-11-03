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

class LinkedInScraper:
    def __init__(self, output_filename = 'jobs_indeed', format = 'all'):
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
        #self.clear_data()  # ADD THIS LINE
        seen_jobs = set()
        browser = webdriver.Firefox(options=options)
        # geoId is fixed here for london area, can change for other places
        url = f'https://www.linkedin.com/jobs/search/?geoId=90009496&keywords={job_keyword}&originalSubdomain=uk&refresh=true&start=0'


        browser.get(url)

        # job title, url, company, location
        time.sleep(np.random.uniform(3, 5))

        # getting rid of pop ups
        for i in range(2):
            browser.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(np.random.uniform(3, 5))

        # refreshing to load the full page
        browser.refresh()

        # scroll function to load all jobs
        def scroll_until_button_visible(browser, max_scrolls=50):
            """Scroll down until 'See more jobs' button is visible"""
            for i in range(max_scrolls):
                try:
                    # Try to find the button
                    button = browser.find_element(By.CSS_SELECTOR, "button[aria-label='See more jobs']")
                    
                    # Check if button is visible
                    if button.is_displayed():
                        print(f"Button found after {i} scrolls")
                        return button
                except NoSuchElementException:
                    pass
                
                # Scroll down
                browser.execute_script("window.scrollBy(0, 1000);")
                time.sleep(np.random.uniform(0.5, 1.5))  # Random delay to appear human-like
            
            print("Max scrolls reached, button not found")
            return None
        
        # Scroll until button is visible
        see_more_button = scroll_until_button_visible(browser)

        for i in range(10): # can do more than 10 if you want more jobs, this was approx 180 jobs, there were 9k total and we will get there, believe
            if see_more_button:
                # Click the button if you want to load more jobs
                see_more_button.click()
                time.sleep(2)

        try:
            textelem = browser.find_elements(By.CSS_SELECTOR, 'h3.base-search-card__title')

            for elem in textelem:
                self.titles.append(elem.text)
        except:
            textelem = []

        try:
            companyelem = browser.find_elements(By.CSS_SELECTOR, 'h4.base-search-card__subtitle')

            for elem in companyelem:
                self.companies.append(elem.text)
        except:
            companyelem = []

        try:
            locaelem = browser.find_elements(By.CSS_SELECTOR, 'span.job-search-card__location')

            for elem in locaelem:
                self.locations.append(elem.text)
        except:
            locaelem = []

        try:
            urlelem = browser.find_elements(By.CSS_SELECTOR, 'a.base-card__full-link')

            for u in urlelem:
                self.urls.append(u.get_attribute('href'))
        except:
            urlelem = []

        unique_jobs = []
        for t, c, u, l in zip(self.titles, self.companies, self.urls, self.locations):
            job_id = f"{self.normalize(t)}_{self.normalize(c)}_{self.normalize(l)}"
            if job_id not in seen_jobs:
                seen_jobs.add(job_id)
                unique_jobs.append((t, c, l, u))

            # Update lists with unique jobs only
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
                for i in range(2):
                    browser.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                # we have to click show more to load the full description
                def scroll_and_click_show_more(browser, max_scrolls=50):
                        """Scroll down until 'Show more' button is visible and click it"""
                        for i in range(max_scrolls):
                                try:
                                # Try to find the button
                                        button = browser.find_element(By.CSS_SELECTOR, "button[data-tracking-control-name='public_jobs_show-more-html-btn']")
                                            
                                # Check if button is visible
                                        if button.is_displayed():
                                                print(f"'Show more' button found after {i} scrolls")
                                                
                                # Scroll to the button to ensure it's in view
                                        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                                        time.sleep(0.5)
                                                
                                # Click the button
                                        button.click()
                                        print("'Show more' button clicked")
                                        time.sleep(1)
                                        return True
                                                
                                except NoSuchElementException:
                                        pass
                                        
                                # Scroll down
                                browser.execute_script("window.scrollBy(0, 800);")
                                time.sleep(np.random.uniform(0.3, 0.8))

                                
                                    
                                print("Max scrolls reached, 'Show more' button not found")
                                return False
                scroll_and_click_show_more(browser)
                descelem = browser.find_elements(By.CSS_SELECTOR, 'div.show-more-less-html__markup.relative.overflow-hidden')
                cleaned_desc = self.clean_text(descelem[0].text)
                self.job_description.append(cleaned_desc)
                
            except:
                print(f"Failed to load job description for {u}")
                self.job_description.append("Description not available")
                self.job_skills.append("N/A")

        browser.quit()

        
if __name__ == '__main__':
    scraper = LinkedInScraper()
    job_keyword = 'data analyst'
    scraper.scrape_jobs(job_keyword=job_keyword)

    print(len(scraper.titles))
    print(len(scraper.companies))
    print(len(scraper.locations))
    print(len(scraper.urls))

    scraper.jd_extraction()
    print(len(scraper.job_description))


# <div class="show-more-less-html__markup relative overflow-hidden">