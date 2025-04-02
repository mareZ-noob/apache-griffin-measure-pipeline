import asyncio
import csv
import json
import os
import random
import re
import time
from typing import List, Set, Tuple

from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from parsel import Selector
from playwright.sync_api import sync_playwright
from playwright.async_api import async_playwright


def is_valid_username(username: str) -> bool:
    """
    Validate username according to common social media username rules.
    Returns True if username is valid, False otherwise.
    """
    if not username:
        return False
        
    username_pattern = r'^(?![0-9])[a-zA-Z0-9_]{1,30}$'
    return bool(re.match(username_pattern, username))


def load_existing_usernames(csv_filename: str) -> Set[str]:
    """Load existing usernames from the CSV file."""
    existing_usernames = set()

    if os.path.exists(csv_filename):
        with open(csv_filename, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            next(reader, None)
            for row in reader:
                if row and is_valid_username(row[0]):
                    existing_usernames.add(row[0])

    return existing_usernames


def save_usernames_to_csv(usernames: List[str], csv_filename: str) -> None:
    """Save the new usernames to a CSV file in append mode with a header if the file is empty."""
    file_exists = os.path.exists(csv_filename)

    with open(csv_filename, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)

        if not file_exists:
            writer.writerow(["Username"])

        for username in usernames:
            if is_valid_username(username):
                writer.writerow([username])


def extract_username_from_href(href: str) -> Tuple[str, bool]:
    """
    Extract and validate username from href.
    Returns tuple of (username, is_valid).
    """
    if not href:
        return "", False

    match = re.search(r'\/@([a-zA-Z0-9_]+)', href)
    if not match:
        return "", False
    
    username = match.group(1)
    return username, is_valid_username(username)


SCRAPEOPS_API_KEY = '2c9624d3-827d-4df7-9efa-135863f594f4'


def get_user_agent_list():
  response = requests.get('http://headers.scrapeops.io/v1/user-agents?api_key=' + SCRAPEOPS_API_KEY)
  json_response = response.json()
  return json_response.get('result', [])


def get_random_user_agent(user_agent_list):
  random_index = random.randint(0, len(user_agent_list) - 1)
  return user_agent_list[random_index]


USER_AGENTS = get_user_agent_list()


def randomize_headers():
    """Randomize headers, including User-Agent and Accept-Language."""
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept-Language': random.choice(['en-US,en;q=0.9', 'es-ES,es;q=0.9', 'de-DE,de;q=0.9'])
    }


def scrape_usernames_from_page(url: str, start_scroll: int) -> List[str]:
    """Scrape usernames from a specific part of the page, starting from a specific scroll position."""
    valid_usernames = []
    
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            context = browser.new_context(viewport={"width": 1920, "height": 1080})
            page = context.new_page()
            headers = randomize_headers()
            # page.set_extra_http_headers(headers)

            try:
                page.goto(url, timeout=50000)
                page.evaluate(f"window.scrollTo(0, {start_scroll});")
                time.sleep(10)

                selector = Selector(page.content())
                divs = selector.css('div[aria-describedby]')

                for div in divs:
                    href = div.css('a::attr(href)').get()
                    username, is_valid = extract_username_from_href(href)
                    
                    if is_valid:
                        valid_usernames.append(username)
                    
            except Exception as e:
                print(f"Error during page navigation: {str(e)}")
            
            finally:
                browser.close()
                
    except Exception as e:
        print(f"Error in browser session: {str(e)}")

    return valid_usernames


def scrape_usernames(url: str, csv_filename: str, max_threads: int = 5) -> List[str]:
    """Scrape all usernames using multithreading for concurrent scraping and save to a CSV file."""
    existing_usernames = load_existing_usernames(csv_filename)
    all_usernames = []

    with ThreadPoolExecutor(max_threads) as executor:
        future_to_scroll = {
            executor.submit(scrape_usernames_from_page, url, i * 1000): i * 1000
            for i in range(1000)
        }

        for future in as_completed(future_to_scroll):
            try:
                usernames = future.result()
                all_usernames.extend(usernames)
                
            except Exception as e:
                print(f"Error processing results: {str(e)}")

    # Check for duplicates before saving
    unique_usernames = list(set(all_usernames) - existing_usernames)
    
    if unique_usernames:
        save_usernames_to_csv(unique_usernames, csv_filename)

    return unique_usernames


if __name__ == "__main__":
    url = "https://www.threads.net/@zuck/post/DFNf73PJxOQ"
    """
    https://www.threads.net/@zuck/post/DEntxehTGSl
    https://www.threads.net/@zuck/post/DEhgYx4JbEG 
    """
    csv_filename = "usernames.csv"
    
    try:
        usernames = scrape_usernames(url, csv_filename)
        print(f"Scraped {len(usernames)} new valid usernames.")
    except Exception as e:
        print(f"Error during scraping: {str(e)}")
