# In this way you can run the [crawler python3 tiktok1.py elonmusk]
import re
import argparse
from playwright.sync_api import sync_playwright
from undetected_playwright import Tarnished
from email_parser import EmailParser





# EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')


# def save_to_json(output_file, data):
#     """
#     Save data to the JSON file, ensuring no duplicate URLs are added.
#     """
#     try:
#         with open(output_file, "r+") as file:
#             try:
#                 file_data = json.load(file)
#             except json.JSONDecodeError:
#                 file_data = []

#             # Check for duplicate URLs before adding
#             existing_urls = {entry['url'] for entry in file_data}
#             new_data = [entry for entry in data if entry['url'] not in existing_urls]

#             if new_data:
#                 file_data.extend(new_data)
#                 file.seek(0)
#                 json.dump(file_data, file, indent=4)

    # except FileNotFoundError:
    #     with open(output_file, "w") as file:
    #         json.dump(data, file, indent=4)



def scroll_page(page, max_scrolls=10, scroll_pause_time=2000):
    """
    Scrolls the page until new content stops loading or max scroll limit is reached.
    """
    previous_height = page.evaluate("document.body.scrollHeight")
    scrolls = 0

    while scrolls < max_scrolls:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(scroll_pause_time)  
        new_height = page.evaluate("document.body.scrollHeight")

        if new_height == previous_height:
            break  
        previous_height = new_height
        scrolls += 1

    print(f"Scrolled {scrolls} times.")


def main1(keyword):
    # result_data = []
    # output_file = "tiktok_result.json"
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(locale="en-US")

        Tarnished.apply_stealth(context)
        page = context.new_page()

        search_url = f"https://www.tiktok.com/search/user?q={keyword}"
        page.goto(search_url, wait_until="networkidle")
        page.wait_for_timeout(5000)

        elements = page.query_selector_all("//a[@data-e2e='search-user-avatar']")

        base_url = "https://www.tiktok.com"
        full_urls = [base_url + element.get_attribute("href") for element in elements]

        # Process each URL
        for url in full_urls:
            print(f"Visiting: {url}")
            page.goto(url, wait_until="networkidle")
            page.wait_for_timeout(5000)

            content = page.content()
            email_parser = EmailParser(content=content)
            emails = email_parser.get_email()

            # result_data.append({
            #     "url": url,
            #     "emails": emails
            # })

            
            # save_to_json(output_file, result_data)

            if len(emails)>0:
                print(f"Found emails at {url}: {', '.join(emails)}")
            else:
                print(f"No emails found at {url}")

        browser.close()

    # print(f"Results saved to {output_file}")

def main2(url):
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(locale="en-US")

        Tarnished.apply_stealth(context)
        page = context.new_page()

        # search_url = url
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(5000)

        # Process each URL
        
        print(f"Visiting: {url}")
        page.goto(url, wait_until="networkidle")
        page.wait_for_timeout(5000)

        content = page.content()
        # breakpoint()
        email_parser = EmailParser(content=content)
        emails = email_parser.get_email()

        if len(emails)>0:
            print(f"Found emails at {url}: {', '.join(emails)}")
        else:
            print(f"No emails found at {url}")

    browser.close()
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search for users on TikTok and extract emails.")
    parser.add_argument("keyword", type=str, help="Keyword to search for TikTok users.")
    
    args = parser.parse_args()
    main1(args.keyword)
