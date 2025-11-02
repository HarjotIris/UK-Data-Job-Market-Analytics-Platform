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
options = Options()
options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

class IndeedScraper:
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
    
    def _extract_degree(self, job_description):
        degree_list = ['bachelor\'s', 'master\'s', 'bachelors', 'masters']
        vague_list = ['relevant degree', 'degree']
        jd_lower = job_description.lower()
        
        for degree in degree_list:
            if degree in jd_lower:
                return degree
        for val in vague_list:
            if val in jd_lower:
                return 'degree mentioned vaguely'
        return 'No degree mentioned'
    
    def _extract_job_health_insurance_info(self, job_description):
        jd_lower = job_description.lower()
        
        return 'True' if 'health insurance' in jd_lower else 'False'
    
    def _extract_job_work_from_home(self, job_description):
        jd_lower = job_description.lower()
        
        return 'True' if 'remote' in jd_lower or 'hybrid' in jd_lower else 'False'
    
    def _salary_rate(self, salary):
            if 'annum' in salary or 'year' in salary:
                return 'yearly'
            elif 'hour' in salary or 'hourly' in salary:
                return 'hourly'
            else:
                return 'Not applicable'

    def _extract_skills(self, job_description):
        """Extract common skills from job description"""
        skills_list = [
            'python', 'java', 'javascript', 'sql', 'c++', 'c#', 'php', 'ruby', 'swift',
            'excel', 'powerbi', 'tableau', 'power bi', 'looker', 'qlik',
            'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'keras',
            'machine learning', 'deep learning', 'data analysis', 'data analytics', 
            'statistical analysis', 'data visualization', 'data mining',
            'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes',
            'spark', 'hadoop', 'hive', 'kafka', 'airflow',
            'git', 'github', 'gitlab', 'jira', 'agile', 'scrum',
            'etl', 'data warehousing', 'data modeling', 'database',
            'mysql', 'postgresql', 'mongodb', 'oracle', 'sql server',
            'api', 'rest', 'json', 'xml', 'html', 'css',
            'communication', 'teamwork', 'problem solving', 'analytical'
        ]
        
        found_skills = []
        jd_lower = job_description.lower()
        
        for skill in skills_list:
            if skill in jd_lower:
                found_skills.append(skill)
        
        return ', '.join(found_skills) if found_skills else 'N/A'
    
    def _categorize_job_title(self, job_title):
        """
        Categorize job title into standardized short titles
        Uses keyword matching with priority order (specific → general → catch-all)
        """
        title_lower = job_title.lower()
        
        # Define categories with their keywords (order matters - check specific first!)
        categories = [
            # ========== SENIOR POSITIONS (Most Specific First) ==========
            
            # Senior Machine Learning
            ('Senior Machine Learning Engineer', ['senior', 'machine learning', 'engineer']),
            ('Senior Machine Learning Engineer', ['senior', 'ml', 'engineer']),
            ('Senior Machine Learning Engineer', ['senior', 'machine learning', 'scientist']),
            ('Senior Machine Learning Engineer', ['senior', 'mlops']),
            
            # Senior Data Science
            ('Senior Data Scientist', ['senior', 'data scientist']),
            ('Senior Data Scientist', ['senior', 'data science']),
            ('Senior Data Scientist', ['senior', 'applied', 'scientist']),
            ('Senior Data Scientist', ['senior', 'research', 'data']),
            
            # Senior Data Engineering
            ('Senior Data Engineer', ['senior', 'data engineer']),
            ('Senior Data Engineer', ['senior', 'data engineering']),
            ('Senior Data Engineer', ['senior', 'analytics', 'engineer']),
            ('Senior Data Engineer', ['senior', 'etl', 'engineer']),
            ('Senior Data Engineer', ['senior', 'data platform', 'engineer']),
            ('Senior Data Engineer', ['senior', 'data pipeline', 'engineer']),
            
            # Senior Data Analyst - ALL VARIATIONS
            ('Senior Data Analyst', ['senior', 'data analyst']),
            ('Senior Data Analyst', ['senior', 'data quality', 'analyst']),
            ('Senior Data Analyst', ['senior', 'data governance', 'analyst']),
            ('Senior Data Analyst', ['senior', 'category data', 'analyst']),
            ('Senior Data Analyst', ['senior', 'data strategy', 'analyst']),
            ('Senior Data Analyst', ['senior', 'analytics', 'analyst']),
            ('Senior Data Analyst', ['senior', 'data insights', 'analyst']),
            ('Senior Data Analyst', ['senior', 'data operations', 'analyst']),
            ('Senior Data Analyst', ['senior', 'marketing', 'data', 'analyst']),
            ('Senior Data Analyst', ['senior', 'financial', 'data', 'analyst']),
            ('Senior Data Analyst', ['senior', 'product', 'data', 'analyst']),
            ('Senior Data Analyst', ['senior', 'customer', 'data', 'analyst']),
            ('Senior Data Analyst', ['senior', 'sales', 'data', 'analyst']),
            ('Senior Data Analyst', ['senior', 'business', 'data', 'analyst']),
            ('Senior Data Analyst', ['senior', 'data reporting', 'analyst']),
            ('Senior Data Analyst', ['senior', 'data visualization', 'analyst']),
            
            # Senior Business Intelligence
            ('Senior Business Analyst', ['senior', 'business intelligence', 'analyst']),
            ('Senior Business Analyst', ['senior', 'bi analyst']),
            ('Senior Business Analyst', ['senior', 'business analyst']),
            ('Senior Business Analyst', ['senior', 'business systems', 'analyst']),
            
            # Senior Software Engineering
            ('Senior Software Engineer', ['senior', 'software', 'engineer']),
            ('Senior Software Engineer', ['senior', 'software', 'developer']),
            ('Senior Software Engineer', ['senior', 'backend', 'engineer']),
            ('Senior Software Engineer', ['senior', 'frontend', 'engineer']),
            ('Senior Software Engineer', ['senior', 'full stack']),
            ('Senior Software Engineer', ['senior', 'developer']),
            
            # ========== LEAD/PRINCIPAL/STAFF POSITIONS ==========
            
            ('Lead Data Scientist', ['lead', 'data scientist']),
            ('Lead Data Scientist', ['staff', 'data scientist']),
            ('Lead Data Engineer', ['lead', 'data engineer']),
            ('Lead Data Engineer', ['staff', 'data engineer']),
            ('Principal Data Scientist', ['principal', 'data scientist']),
            ('Principal Data Scientist', ['principal', 'scientist']),
            ('Lead Machine Learning Engineer', ['lead', 'machine learning']),
            ('Lead Machine Learning Engineer', ['lead', 'ml', 'engineer']),
            
            # ========== MACHINE LEARNING ROLES ==========
            
            ('Machine Learning Engineer', ['machine learning', 'engineer']),
            ('Machine Learning Engineer', ['ml', 'engineer']),
            ('Machine Learning Engineer', ['machine learning', 'scientist']),
            ('Machine Learning Engineer', ['mlops', 'engineer']),
            ('Machine Learning Engineer', ['deep learning', 'engineer']),
            ('AI Engineer', ['ai', 'engineer']),
            ('AI Engineer', ['artificial intelligence', 'engineer']),
            ('AI Engineer', ['ai/ml']),
            
            # ========== DATA SCIENCE ROLES ==========
            
            ('Data Scientist', ['data scientist']),
            ('Data Scientist', ['data science']),
            ('Data Scientist', ['applied', 'scientist']),
            ('Research Scientist', ['research', 'scientist']),
            ('Research Scientist', ['research', 'data']),
            
            # ========== DATA ENGINEERING ROLES ==========
            
            ('Data Engineer', ['data engineer']),
            ('Data Engineer', ['data engineering']),
            ('Data Engineer', ['etl', 'engineer']),
            ('Data Engineer', ['data platform', 'engineer']),
            ('Data Engineer', ['data pipeline', 'engineer']),
            ('Data Engineer', ['data warehouse', 'engineer']),
            ('Analytics Engineer', ['analytics', 'engineer']),
            ('Analytics Engineer', ['analytics engineering']),
            
            # ========== DATA ANALYSIS ROLES - ALL VARIATIONS ==========
            
            ('Data Analyst', ['data analyst']),
            ('Data Analyst', ['data quality', 'analyst']),
            ('Data Analyst', ['data governance', 'analyst']),
            ('Data Analyst', ['category data', 'analyst']),
            ('Data Analyst', ['data strategy', 'analyst']),
            ('Data Analyst', ['analytics', 'analyst']),
            ('Data Analyst', ['data insights', 'analyst']),
            ('Data Analyst', ['data operations', 'analyst']),
            ('Data Analyst', ['marketing', 'data', 'analyst']),
            ('Data Analyst', ['financial', 'data', 'analyst']),
            ('Data Analyst', ['product', 'data', 'analyst']),
            ('Data Analyst', ['customer', 'data', 'analyst']),
            ('Data Analyst', ['sales', 'data', 'analyst']),
            ('Data Analyst', ['business', 'data', 'analyst']),
            ('Data Analyst', ['data reporting', 'analyst']),
            ('Data Analyst', ['data visualization', 'analyst']),
            ('Data Analyst', ['data analytics']),
            
            # Business Intelligence
            ('Business Intelligence Analyst', ['business intelligence', 'analyst']),
            ('Business Intelligence Analyst', ['bi analyst']),
            ('Business Intelligence Analyst', ['business intelligence']),
            ('Business Intelligence Analyst', ['bi developer']),
            
            # ========== BUSINESS ANALYST ROLES ==========
            
            ('Business Analyst', ['business analyst']),
            ('Business Analyst', ['business systems', 'analyst']),
            ('Business Analyst', ['functional', 'analyst']),
            ('Business Analyst', ['process', 'analyst']),
            
            # ========== QUANTITATIVE ROLES ==========
            
            ('Quantitative Analyst', ['quantitative', 'analyst']),
            ('Quantitative Analyst', ['quant', 'analyst']),
            ('Quantitative Analyst', ['quantitative', 'researcher']),
            ('Quantitative Analyst', ['quant', 'developer']),
            
            # ========== SOFTWARE ENGINEERING ROLES ==========
            
            ('Software Engineer', ['software', 'engineer']),
            ('Software Engineer', ['software', 'developer']),
            ('Backend Engineer', ['backend', 'engineer']),
            ('Backend Engineer', ['back-end', 'engineer']),
            ('Frontend Engineer', ['frontend', 'engineer']),
            ('Frontend Engineer', ['front-end', 'engineer']),
            ('Full Stack Engineer', ['full stack']),
            ('Full Stack Engineer', ['fullstack']),
            ('DevOps Engineer', ['devops']),
            ('DevOps Engineer', ['dev ops']),
            ('DevOps Engineer', ['site reliability', 'engineer']),
            ('DevOps Engineer', ['sre']),
            
            # ========== CLOUD ROLES ==========
            
            ('Cloud Engineer', ['cloud', 'engineer']),
            ('Cloud Engineer', ['cloud', 'developer']),
            ('Cloud Architect', ['cloud', 'architect']),
            ('Cloud Architect', ['solutions', 'architect', 'cloud']),
            
            # ========== ARCHITECT ROLES ==========
            
            ('Data Architect', ['data', 'architect']),
            ('Solutions Architect', ['solutions', 'architect']),
            ('Enterprise Architect', ['enterprise', 'architect']),
            
            # ========== CATCH-ALL PATTERNS (Ordered by Priority) ==========
            # These catch anything we missed with specific patterns
            
            # Catch any Senior + Data + Analyst combination
            ('Senior Data Analyst', ['senior', 'data', 'analyst']),
            
            # Catch any Senior + Data + Engineer combination
            ('Senior Data Engineer', ['senior', 'data', 'engineer']),
            
            # Catch any Senior + Data + Scientist combination
            ('Senior Data Scientist', ['senior', 'data', 'scientist']),
            
            # Catch any Senior + ML/Machine Learning combination
            ('Senior Machine Learning Engineer', ['senior', 'machine', 'learning']),
            ('Senior Machine Learning Engineer', ['senior', 'ml']),
            
            # Catch any Senior + Software/Developer combination
            ('Senior Software Engineer', ['senior', 'software']),
            ('Senior Software Engineer', ['senior', 'engineer']),
            

            # ========== OTHER ANALYST TYPES (Add before final catch-all) ==========

            ('Financial Analyst', ['financial', 'analyst']),
            ('Financial Analyst', ['finance', 'analyst']),
            ('Risk Analyst', ['risk', 'analyst']),
            ('Operations Analyst', ['operations', 'analyst']),
            ('Junior Analyst', ['junior', 'analyst']),

            # Catch any Data + Analyst combination (non-senior)
            ('Data Analyst', ['data', 'analyst']),

            # Generic analyst (for anything that doesn't fit above)
            ('Analyst', ['analyst']),
            
            # Catch any Data + Engineer combination (non-senior)
            ('Data Engineer', ['data', 'engineer']),
            
            # Catch any Data + Scientist combination (non-senior)
            ('Data Scientist', ['data', 'scientist']),
            
            # Catch any ML/Machine Learning Engineer (non-senior)
            ('Machine Learning Engineer', ['machine', 'learning']),
            ('Machine Learning Engineer', ['ml']),
            
            # Catch any AI-related roles
            ('AI Engineer', ['ai']),
            ('AI Engineer', ['artificial', 'intelligence']),
            
            # Catch any Business Analyst variations
            ('Business Analyst', ['business', 'analyst']),
            
            # Catch any Software Engineer variations
            ('Software Engineer', ['software']),
            ('Software Engineer', ['developer']),
            ('Software Engineer', ['engineer']),
        ]
        
        # Check each category
        for category_name, keywords in categories:
            # Check if ALL keywords are in the title
            if all(keyword in title_lower for keyword in keywords):
                return category_name
        
        # If no match found, return "Other"
        return 'Other'

    def clear_data(self):
        self.titles = []
        self.companies = []
        self.urls = []
        self.job_description = []
        self.job_skills = []
        self.job_title_short = []
        self.locations = []
        self.salary = []
        self.schedule = []
        self.salary_rate = []


    def scrape_jobs(self, location, page_no, job_keyword):
        self.clear_data()  # ADD THIS LINE
        seen_jobs = set()
        browser = webdriver.Firefox(options=options)
        job_keyword = job_keyword.strip().replace(' ', '+').lower()
        try:
            for page in range(1, page_no+1):
                retry_count = 0
                max_retries = 3

                while retry_count < max_retries:
                    try:
                        url = f'https://uk.indeed.com/jobs?q={job_keyword}&l={location}&start={(page - 1)*10}'

                        browser.get(url)
                        time.sleep(np.random.uniform(3, 5))
                        try:
                            textElems = browser.find_elements(By.CSS_SELECTOR, '.jcs-JobTitle.css-1baag51.eu4oa1w0')
                        except:
                            textElems = []

                        try:
                            companyElems = browser.find_elements(By.CSS_SELECTOR, '.css-1afmp4o.e37uo190')
                        except:
                            companyElems = []

                        
                        for elem in textElems:
                            try:
                                href_val = elem.get_attribute('href')
                                if href_val and elem.text:
                                    self.titles.append(elem.text)
                                    self.job_title_short.append(self._categorize_job_title(elem.text))
                                    self.urls.append(href_val)
                            except:
                                continue


                        for elem in companyElems[1:]:
                            try:
                                if elem.text:
                                    self.companies.append(elem.text)
                            except:
                                continue

                        break
                        #print(len(titles))
                        #print(len(url))
                        #print(len(companies))
                    except Exception as e:
                        retry_count += 1
                        print(f"Error loading page {page}, attempt {retry_count}: {e}")
                        if retry_count < max_retries:
                            time.sleep(np.random.uniform(5, 8))
                        else:
                            print(f"Failed to load page {page} after {max_retries} attempts")
            

            
        # After the page loop, before finally block
        # Check for duplicates
            unique_jobs = []
            for t, c, u in zip(self.titles, self.companies, self.urls):
                job_id = f"{self.normalize(t)}_{self.normalize(c)}"
                if job_id not in seen_jobs:
                    seen_jobs.add(job_id)
                    unique_jobs.append((t, c, u))

            # Update lists with unique jobs only
            self.titles = [job[0] for job in unique_jobs]
            self.companies = [job[1] for job in unique_jobs]
            self.urls = [job[2] for job in unique_jobs]
        except Exception as e:
            print(f'Major error during scraping : {e}')
            
        finally:
            
            browser.quit()
            return f'Successfully scraped {len(self.titles)} unique jobs. Saved to {self.output_filename}'
        
    

    def jd_extraction(self):
        browser = webdriver.Firefox(options=options)
        for u in self.urls:
            retry_count = 0
            max_retries = 3

            while retry_count < max_retries:
                try:
                    
                    browser.get(u)
                    time.sleep(np.random.uniform(3, 5))

                    try:
                        loc = browser.find_element(By.CSS_SELECTOR, '[data-testid="inlineHeader-companyLocation"]')
                        self.locations.append(loc.text)

                        try:
                            sal = browser.find_element(By.CSS_SELECTOR, '.css-1oc7tea.eu4oa1w0')
                            sal_text = sal.text
                            self.salary.append(sal_text)
                            s_rate = self._salary_rate(sal_text)
                            self.salary_rate.append(s_rate)

                        except:
                            self.salary.append("Competitive Salary")
                            self.salary_rate.append("Not applicable")

                        try:
                            schedule = browser.find_element(By.CSS_SELECTOR, '.css-1u1g3ig.eu4oa1w0')
                            schedule_text = schedule.text
                            if schedule_text.startswith('- '):
                                schedule_text = schedule_text[2:]
                            self.schedule.append(schedule_text)

                        except:
                            self.schedule.append("Schedule not found")

                        elem = browser.find_element(By.CSS_SELECTOR, '.jobsearch-JobComponent-description')

                        s = elem.text
                        start = s.find('Full job description')
                        end = s.find('About you')
                        required = s[start:end]
                        required = required.replace('Full job description', 'Full job description : ')
                        cleaned_desc = self.clean_text(required)

                        degree = self._extract_degree(cleaned_desc)
                        self.degree.append(degree)

                        health_ins = self._extract_job_health_insurance_info(cleaned_desc)
                        self.health_insurance.append(health_ins)
                        self.job_description.append(cleaned_desc)

                        remote = self._extract_job_work_from_home(cleaned_desc)
                        self.work_from_home.append(remote)

                        skills = self._extract_skills(cleaned_desc)
                        self.job_skills.append(skills)
                        break

                    except NoSuchElementException:
                        print(f"Job description not found for URL: {u}")
                        self.job_description.append("Description not available")
                        self.job_skills.append("N/A")
                        break
                except Exception as e:
                    retry_count += 1
                    print(f"Error loading job description for {u}, attempt {retry_count}: {e}")
                    if retry_count < max_retries:
                        time.sleep(np.random.uniform(5, 8))
                    else:
                        print(f"Failed to load job description for {u} after {max_retries} attempts")
                        self.job_description.append("Description not available")
                        self.job_skills.append("N/A")
        browser.quit()



    def _save_to_csv(self):
        import csv
        try:
            with open(self.output_filename + '.csv', 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                writer.writerow(['Title', 'Title_Short' 'Company', 'Location', 'URL', 'Job Description', 'Skills', 'Salary', 'Job_Health_Insurance', 'Degree', 'Remote Work', 'Job_via', 'Job_Schedule', 'Salary_rate', 'City'])
                for title, title_short, company, loca, u, desc, skills, salary, hinsurance, degree, remote, schedule, rate in zip(self.titles, self.job_title_short, self.companies, self.locations, self.urls, self.job_description, self.job_skills, self.salary, self.health_insurance, self.degree, self.work_from_home, self.schedule, self.salary_rate):
                    writer.writerow([
                        title.strip(),
                        title_short.strip(),
                        company.strip(),
                        loca.strip(),
                        u.strip(),
                        desc.strip(),
                        skills.strip(),
                        salary.strip(),
                        hinsurance.strip(),
                        degree.strip(),
                        remote.strip(),
                        'Indeed',
                        schedule.strip(),
                        rate.strip(),
                        'London'
                    ])
            print(f"Saved to {self.output_filename}")
        except Exception as e:
            print(f'Error saving to csv: {e}')

    def _save_to_json(self):
        data = []
        json_filename = self.output_filename + '.json'
        for title, title_short, company, loca, u, desc, skills, salary, hinsurance, degree, remote, schedule, rate in zip(self.titles, self.job_title_short, self.companies, self.locations, self.urls, self.job_description, self.job_skills, self.salary, self.health_insurance, self.degree, self.work_from_home, self.schedule, self.salary_rate):
            data.append({
                'title': title.strip(),
                'title_short': title_short.strip(),
                'company': company.strip(),
                'locations': loca.strip(),
                'job_url': u.strip(),
                'job_description': desc.strip(),
                'skills': skills.strip(),
                'salary': salary.strip(),
                'health_insurancce': hinsurance.strip(),
                'degree': degree.strip(),
                'work_from_home': remote.strip(),
                'job_via': 'Indeed',
                'schedule': schedule.strip(),
                'salary_rate': rate.strip(),
                'city': 'London'
                
            })
        
        with open(json_filename, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Saved to {json_filename}")

    def _save_to_excel(self):
        excel_filename = self.output_filename + '.xlsx'
        
        new_df = pd.DataFrame({
            'Title': [title.strip() for title in self.titles],
            'Title_Short':[st.strip() for st in self.job_title_short],
            'Company': [company.strip() for company in self.companies],
            'Location': [loca.strip() for loca in self.locations],
            'URL': [url.strip() for url in self.urls],
            'Job Description': [desc.strip() for desc in self.job_description],
            'Skills': [skills.strip() for skills in self.job_skills],
            'Salary': [sal.strip() for sal in self.salary],
            'Job_Health_Insurance': [j.strip() for j in self.health_insurance],
            'Degree': [d.strip() for d in self.degree],
            'Remote Work': [r.strip() for r in self.work_from_home],
            'Job_via': 'Indeed',
            'Job_Schedule': [js.strip() for js in self.schedule],
            'Salary_rate': [rate.strip() for rate in self.salary_rate],
            'City': 'London'
        })
        
        if os.path.exists(excel_filename):
            existing_df = pd.read_excel(excel_filename, engine='openpyxl')
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=['Title', 'Company'], keep='first')
            combined_df.to_excel(excel_filename, index=False, engine='openpyxl')
            print(f'Appended to {excel_filename}. Total jobs: {len(combined_df)}')
        else:
            new_df.to_excel(excel_filename, index=False, engine='openpyxl')
            print(f'Created {excel_filename} with {len(new_df)} jobs')
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Scraper CLI')

    parser.add_argument('--filename', default='jobs', help='Name of the output file without any extensions')
    parser.add_argument('--job_keyword', nargs='+', required=True, help='Enter the job keyword you want to search within quotes')
    parser.add_argument('--number_of_pages', type=int, default=1, help='Enter the number of pages you want to scrape')
    parser.add_argument('--format', choices=['csv', 'json', 'excel', 'pandas', 'all'], default='all', help='Output format')
    parser.add_argument('--location', help='Enter the location', default='London')

    args = parser.parse_args()

    scraper = IndeedScraper(output_filename=args.filename, format=args.format)
    job_keyword = ' '.join(args.job_keyword)
    
    # Scrape the jobs
    scraper.scrape_jobs(args.location, args.number_of_pages, job_keyword)
    
    
    print(f"\nScraping complete! Found {len(scraper.titles)} jobs.")

    print(f'Total titles - {len(scraper.titles)}')
    print(f'Total company - {len(scraper.companies)}')
    print(f'Total job urls - {len(scraper.urls)}')

    # Extract job descriptions
    scraper.jd_extraction()

    # ADD THIS BLOCK
    if args.format == 'csv':
        scraper._save_to_csv()
    elif args.format == 'json':
        scraper._save_to_json()
    elif args.format == 'excel':
        scraper._save_to_excel()
    elif args.format == 'pandas':
        scraper._save_to_csv()
        scraper._save_to_json()
    else:  # 'all'
        scraper._save_to_csv()
        scraper._save_to_json()
        scraper._save_to_excel()

    print(f"\nScraping complete! Found {len(scraper.titles)} jobs.")
    print(f'Total job descriptions - {len(scraper.job_description)}, Jobs : {scraper.job_description}')