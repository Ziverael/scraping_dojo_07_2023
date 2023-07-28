###IMPORTS###
from bs4 import BeautifulSoup as bsp
import os
import sys
import jsonlines
from dotenv import load_dotenv
import requests #Communicatrion with web
from selenium import webdriver # Dynamic scraping for JS websites
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import re


###CLASSES###
class Scraper():
    def __init__(self, page, timeout, proxy = None):
        """
        ARGS
        ----
        page    [str]   URL of the page for scraping
        timeout [int]   posiive integer representing max timeout for page content in seconds
        """
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        if proxy:
            options.add_argument('--proxy-server={}'.format(proxy))
        self.driver = webdriver.Chrome(options = options) 
        self.url = page
        self.page_src = ""
        self.page_bsp = None
        self.timeout = timeout
    
    def get_page(self):
        """Get HTML from URL"""
        self.driver.get(self.url)
        return self.driver.page_source

    def set_page_src(self, page_src):
        """Set page for scraping with bsp"""
        self.page_src = page_src
        self.page_bsp = bsp(page_src, 'html.parser')
    
    def get_page_src(self):
        return self.page_src
    
    def chage_url(self, page):
        """Change URL for scraping"""
        self.url = page
    
    def wait_for_elem(self, class_, verbose = False):
        """Wait for element with provided class name and then load page_src."""
        if verbose:
            print("Waiting for element {}...".format(class_))
        WebDriverWait(self.driver, timeout = self.timeout).until(lambda x: x.find_element(By.CLASS_NAME, class_))
        self.set_page_src(self.driver.page_source)

    def scrape(self, tag, class_ = None, id_ = None, all_results = True, parent = None, get_text = True):
        """
        Scrape matching tags
        ARGS
        ----
        tag [str]   tag type
        class_  [str]   tag class
        all_results [bool]  return all results or first results
        parent [object]    if provided, then search only childs of given element
        get_text    [bool]  if True return text from tag. Otherwise return tag
        
        RETURN
        ------
        if all_results is True then return list of tags. Otherwise return single object.
        If attribute page_src is empty then return -1.
        """
        if not self.page_bsp:
            return -1
        if all_results:
            if parent:
                if get_text:
                    return [i.get_text() for i in parent.findChildren(tag, {'class' : class_, 'id' : id_})]
                else:
                    return [i for i in parent.findChildren(tag, {'class' : class_, 'id' : id_})]
            else:
                if get_text:
                    return [i.get_text() for i in self.page_bsp.find_all(tag, {'class' : class_, 'id' : id_})]
                else:
                    return [i for i in self.page_bsp.find_all(tag, {'class' : class_, 'id' : id_})]

        else:
            if parent:
                if get_text:
                    return parent.findChildren(tag.get_text(), {'class' : class_, 'id' : id_})[0]
                else:
                    return parent.findChildren(tag, {'class' : class_, 'id' : id_})[0]
            else:
                if get_text:
                    return self.page_bsp.find(tag, {'class' : class_, 'id' : id_}).get_text()
                else:
                    return self.page_bsp.find(tag, {'class' : class_, 'id' : id_})
        
    def quit(self):
        """Close driver"""
        self.driver.close()
        self.driver.quit()

            

class JSONLWriter():
    def __init__(self, output_):
        self.output = output_
    
    def overwrite(self, input_):
        """Write to file. If flie already exists, then overwrite it."""
        with open(self.output, 'w') as f:
            writer = jsonlines.Writer(f)
            if isinstance(input_, dict):
                writer.write(input_)
            elif isinstance(input_, list):
                for line in input_:
                    writer.write(line)
            else:
                raise Exception("Expected dictionary or list of dictionaries.")


    def write(self, input_):
        """Write to file. If flie already exists, then append content."""
        with open(self.output, 'a') as f:
            writer = jsonlines.Writer(f)
            if isinstance(input_, dict):
                writer.write(input_)
            elif isinstance(input_, list):
                for line in input_:
                    writer.write(line)
            else:
                raise Exception("Expected dictionary or list of dictionaries.")


###MAIN###
if __name__ == "__main__":
    print("Load variables...")
    #Read enviromental variables
    load_dotenv()

    ###VARIABLES###
    URL = os.getenv('INPUT_URL')
    OUTPUT = os.getenv('OUTPUT_FILE')
    PROXY = os.getenv('PROXY')
    MAX_TIMEOUT = 600
    print("Done!")
    print("Start scraping...")
    try:
        #Objects initialization
        scr = Scraper(URL, MAX_TIMEOUT)
        scr.set_page_src(scr.get_page())

        #Wait for elements
        scr.wait_for_elem('quote', verbose = True)
        
        #Start scraping
        quotes_div = scr.scrape('div', id_ = 'quotesPlaceholder', all_results = False, get_text = False)
        quotes = scr.scrape('span', class_ = 'text', parent = quotes_div)
        authors = scr.scrape('small', class_ = 'author', parent = quotes_div)
        tags = scr.scrape('div', class_ ='quote', get_text = False, parent = quotes_div)
        tags = [scr.scrape('a', class_ ='tag', get_text = True, parent = qu) for qu in tags]
    except Exception as e:
        print("Problem during scraping!")
        print(e)
        print("Program terminated!")
        sys.exit(1)
    finally:
        scr.quit()
    
    print("Done!")
    print("Prepare data...")
    #Prepare output file
    data = []
    for i in range(len(quotes)):
        data.append(
            {
                'text' : quotes[i],
                'by' : authors[i],
                'tags' : tags[i]
            }
        )
    
    print("Done!")
    print("Save data to output file...")
    #Write to jsonl
    out = JSONLWriter(OUTPUT)
    out.overwrite(data)
    print("Done!")

