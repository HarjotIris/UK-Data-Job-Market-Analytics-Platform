# UK Job Market Analytics Platform
End-to-End ETL Project that will collect job data from all major online job platforms in London, clean and transform this data to analyse trends and answer real-life business questions like :

- "What is the average salary for 'Data Analyst' ,'Data Scientist', and 'Data Engineer' roles in London?" 

- "What are the most in-demand tools and platforms (Tableau, Power BI, Snowflake, AWS, Azure)?" 

- "Which industries (Finance, Tech, Retail) are hiring the most data professionals?", etc etc.

So far I am collecting data from Reed UK and Indeed UK but I'm planning to add atleast 3 more sites to make the project more robust.

## ETL PIPELINE STRUCTURE
[Data Sources] → [Scrapers (Python)] → [Raw Storage] → [Cleaning & Transformation] → [Analytical DB] → [Analysis & Visualization]

Data extraction is being handled with Python using modules like 'requests', 'bs4' and 'selenium'. Eventually the scrapers will be automated to run independently using the 'subprocess' module. I know I can use GitHub actions, but I'd like do the data extraction just locally and then push it here. 

If you run the scripts, you will realize a lot of the cleaning is implicitly done, like - Salary Parsing, Text Standardization and Skills Extraction is already implemented. I have a couple excel formulas already written that I can simply add to compute average salaries after the data is extracted. The only major thing I have left out in terms of data cleaning is null values, which I am planning to deal with once the extraction part of the project is fully completed. 

I am yet to decide between mySQL and postgreSQL but I will get to it once the extraction is done and I have a tangible dataset that warrants to be loaded in such databases.

So:
## Tech Stack

- **Language:** Python  
- **Libraries:** requests, BeautifulSoup, Selenium, pandas, numpy  
- **Database (planned):** MySQL / PostgreSQL  
- **Visualization (planned):** Power BI / Tableau  
- **Version Control:** Git & GitHub

> *"Being built with <3 (and Python) by Harjot / Iris. Thank you for visiting."*
