# import csv
# import json
# from typing import Dict

# import jmespath
# from parsel import Selector
# from playwright.sync_api import sync_playwright
# from nested_lookup import nested_lookup

# # Note: we'll also be using parse_thread function we wrote earlier:
# from scrapethread import parse_thread


# def parse_profile(data: Dict) -> Dict:
#     """Parse Threads profile JSON dataset for the most important fields"""
#     result = jmespath.search(
#         """{
#         is_private: text_post_app_is_private,
#         is_verified: is_verified,
#         profile_pic: hd_profile_pic_versions[-1].url,
#         username: username,
#         full_name: full_name,
#         bio: biography,
#         bio_links: bio_links[].url,
#         followers: follower_count
#     }""",
#         data,
#     )
#     result["url"] = f"https://www.threads.net/@{result['username']}"
#     return result


# def scrape_profile(url: str) -> dict:
#     """Scrape Threads profile and their recent posts from a given URL"""
#     with sync_playwright() as pw:
#         # start Playwright browser
#         browser = pw.chromium.launch(headless=True)
#         context = browser.new_context(viewport={"width": 1920, "height": 1080})
#         page = context.new_page()

#         try:
#             page.goto(url, timeout=10000)  # Give it 10 seconds to load
#             # Check if profile exists by looking for a specific element
#             page.wait_for_selector("[data-pressable-container=true]", timeout=10000)
#         except Exception as e:
#             # If an error occurs (like timeout or element not found), handle it
#             print(f"Error: {e}")
#             # You can check if a common element that indicates a non-existing profile is visible
#             # try:
#             #     if page.locator('text="Page Not Found"').is_visible():
#             #         print("Profile not found!")
#             # except Exception:
#             #     return {}
#             return {}  # Return empty data in case of invalid profile

#         selector = Selector(page.content())
#     parsed = {
#         "user": {},
#         "threads": [],
#     }
#     # find all hidden datasets
#     hidden_datasets = selector.css('script[type="application/json"][data-sjs]::text').getall()
#     for hidden_dataset in hidden_datasets:
#         # skip loading datasets that clearly don't contain threads data
#         if '"ScheduledServerJS"' not in hidden_dataset:
#             continue
#         is_profile = 'follower_count' in hidden_dataset
#         is_threads = 'thread_items' in hidden_dataset
#         if not is_profile and not is_threads:
#             continue
#         data = json.loads(hidden_dataset)
#         if is_profile:
#             user_data = nested_lookup('user', data)
#             parsed['user'] = parse_profile(user_data[0])
#         if is_threads:
#             thread_items = nested_lookup('thread_items', data)
#             threads = [
#                 parse_thread(t) for thread in thread_items for t in thread
#             ]
#             parsed['threads'].extend(threads)
#     return parsed

# def read_csv_and_scrape_profiles(csv_file: str) -> Dict:
#     """
#     Reads the CSV file and loops through to get user data as JSON.
    
#     :param csv_file: The path to the CSV file containing user URLs.
#     :return: A dictionary containing scraped user data.
#     """
#     user_data = {}

#     # Open the CSV file and read it
#     with open(csv_file, mode='r', encoding='utf-8') as file:
#         reader = csv.reader(file)
#         next(reader)  # Skip the header row if it exists
#         for row in reader:
#             username = row[0]  # Assuming the username is in the first column
#             user_url = f"https://www.threads.net/@{username}"

#             # Scrape the profile data for this user
#             print(f"Scraping profile for: {username}")
#             profile_data = scrape_profile(user_url)
            
#             if profile_data:
#                 user_data[username] = profile_data
#             else:
#                 print(f"Failed to scrape profile for: {username}")

#     return user_data

# if __name__ == "__main__":
#     # Specify the path to your CSV file
#     csv_file_path = "test.csv"  # Adjust this path as needed
#     scraped_data = read_csv_and_scrape_profiles(csv_file_path)

#     # Print or save the scraped data
#     with open("scraped_user_data.json", "w", encoding="utf-8") as output_file:
#         json.dump(scraped_data, output_file, indent=4, ensure_ascii=False)
#     print("Scraped data saved to scraped_user_data.json")

import csv
import json
from typing import Dict

import jmespath
from parsel import Selector
from playwright.sync_api import sync_playwright
from nested_lookup import nested_lookup

from scrapethread import parse_thread


def parse_profile(data: Dict) -> Dict:
    """Parse Threads profile JSON dataset for the most important fields"""
    result = jmespath.search(
        """{
            is_private: text_post_app_is_private,
            is_verified: is_verified,
            profile_pic: hd_profile_pic_versions[-1].url,
            username: username,
            full_name: full_name,
            bio: biography,
            bio_links: bio_links[].url,
            followers: follower_count
        }""",
        data,
    )
    result["url"] = f"https://www.threads.net/@{result['username']}"
    return result


def scrape_profile(url: str) -> dict:
    """Scrape Threads profile and their recent posts from a given URL"""
    with sync_playwright() as pw:
        # start Playwright browser
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()

        try:
            page.goto(url, timeout=15000)  # Give it 10 seconds to load
            # Check if profile exists by looking for a specific element
            page.wait_for_selector("[data-pressable-container=true]", timeout=15000)
        except Exception as e:
            print(f"Error: {e}")
            return {}  # Return empty data in case of invalid profile

        selector = Selector(page.content())

    parsed = {
        "user": {},
        "threads": [],
    }
    # find all hidden datasets
    hidden_datasets = selector.css('script[type="application/json"][data-sjs]::text').getall()
    for hidden_dataset in hidden_datasets:
        # skip loading datasets that clearly don't contain threads data
        if '"ScheduledServerJS"' not in hidden_dataset:
            continue
        is_profile = 'follower_count' in hidden_dataset
        is_threads = 'thread_items' in hidden_dataset
        if not is_profile and not is_threads:
            continue
        data = json.loads(hidden_dataset)
        if is_profile:
            user_data = nested_lookup('user', data)
            if user_data:
                parsed['user'] = parse_profile(user_data[0])
        if is_threads:
            thread_items = nested_lookup('thread_items', data)
            threads = [
                parse_thread(t) for thread in thread_items for t in thread
            ]
            parsed['threads'].extend(threads)
    return parsed


def read_csv_and_scrape_profiles_in_batches(csv_file: str, batch_size: int = 50, output_file: str = "scraped_user_data.jsonl") -> None:
    """
    Reads the CSV file and processes user profiles in batches to prevent holding too much data in memory.
    Each scraped profile is written as a separate line in a JSON Lines file.
    
    :param csv_file: The path to the CSV file containing user URLs.
    :param batch_size: Number of profiles to scrape before writing them to disk.
    :param output_file: The output file path in JSON Lines format.
    """
    batch = {}
    with open(csv_file, mode='r', encoding='utf-8') as file, open(output_file, mode='w', encoding='utf-8') as out_f:
        reader = csv.reader(file)
        header = next(reader, None)  # Skip header row if it exists
        for count, row in enumerate(reader, start=1):
            # Assuming the username is in the first column
            username = row[0].strip()
            user_url = f"https://www.threads.net/@{username}"
            print(f"Scraping profile for: {username}")
            profile_data = scrape_profile(user_url)
            
            if profile_data:
                batch[username] = profile_data
            else:
                print(f"Failed to scrape profile for: {username}")

            # If the batch size is reached, write the batch to the file and reset the batch
            if count % batch_size == 0:
                for user, data in batch.items():
                    out_f.write(json.dumps({user: data}, ensure_ascii=False) + "\n")
                out_f.flush()  # Make sure to flush the file buffer
                print(f"Wrote batch of {batch_size} profiles to {output_file}")
                batch.clear()

        # Write any remaining profiles that didn't fill a complete batch
        if batch:
            for user, data in batch.items():
                out_f.write(json.dumps({user: data}, ensure_ascii=False) + "\n")
            out_f.flush()
            print(f"Wrote final batch of {len(batch)} profiles to {output_file}")


def convert_jsonl_to_json(jsonl_file: str, json_file: str) -> None:
    """
    Converts a JSON Lines (.jsonl) file to a standard JSON (.json) file.

    :param jsonl_file: Path to the input JSONL file.
    :param json_file: Path to the output JSON file.
    """
    data = []

    with open(jsonl_file, "r", encoding="utf-8") as infile:
        for line in infile:
            data.append(json.loads(line.strip()))  # Parse each line as JSON object

    with open(json_file, "w", encoding="utf-8") as outfile:
        json.dump(data, outfile, indent=2, ensure_ascii=False)  # Save as a pretty JSON file

    print(f"Converted {jsonl_file} to {json_file}")

if __name__ == "__main__":
    # Specify the path to your CSV file and the batch size
    csv_file_path = "usernames_crawl.csv"  # Adjust this path as needed
    output_file_path = "data.jsonl"  # Output file in JSON Lines format

    read_csv_and_scrape_profiles_in_batches(csv_file=csv_file_path, batch_size=500, output_file=output_file_path)
    print(f"Scraping complete. Data saved to {output_file_path}")

    convert_jsonl_to_json("data.jsonl", "data.json")
