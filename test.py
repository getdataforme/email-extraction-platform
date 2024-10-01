
import requests
from lxml import html, etree
import logging
import time
import signal
import sys
import asyncio
import aiohttp
import tiktok_crawler
from email_parser import EmailParser
from playwright.async_api import async_playwright
from undetected_playwright import Tarnished

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}
# # Regular expression for finding emails
# EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
search_keywords = ["contact", "contacto", "discover"]
search_keywords2 = ["/contact", "/contacto", "/discover", "/contact.html", "/contacto.php", "/contacto.html"]
# Define the extensions and keywords that need to be skipped
SKIPPED_EXTENSIONS = {'.js', '.png', '.jpg', '.webp', '.css', '.jpeg'}
SKIPPED_KEYWORDS = {'javascript:', '#', 'mailto:'}

# Function to filter out unwanted links (extensions and keywords)
def process_links(link):
    # Skip links that contain unwanted keywords or file extensions
    if any(link.endswith(ext) for ext in SKIPPED_EXTENSIONS):
        return True
    if any(kw in link for kw in SKIPPED_KEYWORDS):
        return True
    return False

# Find all unique pages from the base page
def find_all_pages(base_url, base_content):
    tree = html.fromstring(base_content)
    links = tree.xpath('//a/@href')
    all_pages = []
    for link in links:
        if process_links(link):
            continue
        # Convert relative links to full URLs
        full_url = str(requests.compat.urljoin(base_url, link))
        # Ensure the full URL starts with http and is not already added
        if full_url not in all_pages:
            all_pages.append(full_url)
    return all_pages

# Process individual page
def process_page(url):
    logger.info(f"Processing {url}")
    try:
        page_content, status_code = fetch_page(url)
        if page_content:
            try:
                emails = EmailParser(page_content)
                if emails:
                    logger.info(f"Found emails on {url}: {emails}")
                    return emails, status_code
            except etree.XMLSyntaxError as e:
                if 'Document is empty' in str(e):
                    logger.warning(f"Skipping {url}: Document is empty.")
                else:
                    logger.error(f"XML error processing {url}: {e}")
        elif status_code == 404:
            logger.error(f"Page not found (404) at {url}")
            return None, 404
        elif status_code == 403:
            return None, 403
        else:
            logger.error(f"Error processing {url} with status code {status_code}")
            return None, status_code
    except Exception as e:
        logger.error(f"Unexpected error while processing {url}: {e}")
    return None, status_code
def fetch_page(url, retries=3):
    delay = 1
    for attempt in range(1, retries + 3):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            if response.status_code == 429:
                if attempt == retries:
                    logger.error(f"Too many requests (429) for {url}, max retries reached.")
                    return None, 429
                retry_after = int(response.headers.get("Retry-After", delay))
                logger.warning(f"429 Too Many Requests for {url}. Retrying in {retry_after} seconds (Attempt {attempt}/{retries})")
                time.sleep(retry_after)
                delay *= 2  # Exponential backoff
                continue
            response.raise_for_status()
            return response.content.decode('utf-8'), response.status_code
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None, "NaN"
# # Extract emails from page content
# def extract_emails(page_content):
#     if page_content:
#         tree = html.fromstring(page_content)
#         text_content = tree.xpath('//text()')
#         all_text = ' '.join(text_content)
#         emails = set(EMAIL_REGEX.findall(all_text))  # Use set to remove duplicates
#         valid_emails = set()
#         for email in emails:
#             try:
#                 v= validate_email(email)
#                 valid_emails.add(v.email)
#             except EmailNotValidError as e:
#                     print(f"Invalid email {email}: {str(e)}")
#         return valid_emails
            
#     return set()

# Asynchronous crawler 2 email extraction part
async def make_requests(url):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=HEADERS) as response:
                return await response.text(), url
        except aiohttp.ClientError as e:
            print(f"Request failed for {url}: {e}")
            return None, url
        except:
            return None, None
# async def email_extractor(html):
#     emails = EMAIL_REGEX.findall(html)
#     return emails

# Modify the playwright_email_extractor to include stealth functionality
async def playwright_email_extractor(url):
    print("here2")
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = await browser.new_context()
        
        # Apply stealth manually by injecting evasion JavaScript
        # You can include some stealth scripts, e.g., navigator.webdriver or other obfuscation scripts
        stealth_js = """
        // Sample stealth evasion JavaScript code
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        """
        await context.add_init_script(stealth_js)  
        
       
        page = await context.new_page()
        response = await page.goto(url)
        status = response.status
        emails = []
        if 200 <= status < 404:
            await page.wait_for_load_state('networkidle')
            content = await page.content()
            emails1 =EmailParser(content=content)
            emails = emails1.get_email()
            if not emails:
                content = page.locator('a')
                count = await content.count()
                hrefs = []
                for i in range(count):
                    href = await content.nth(i).get_attribute('href')
                    text = await content.nth(i).inner_text()
                    if text.lower() in search_keywords or href in search_keywords2:
                        try:
                            if not href.startswith('http'):
                                current_url = page.url
                                base_url = "/".join(current_url.split("/")[:3])
                                await page.goto(base_url + href)
                                await page.wait_for_load_state('networkidle')
                                contents = await page.content()
                                emails1 = EmailParser(contents)
                                emails=emails1.get_email()
                                if emails:
                                    break
                            else:
                                hrefs.append(href)
                        except Exception as e:
                            logger.error(f"Error following link {href}: {e}")
                    else:
                        hrefs.append(href)
                if not emails:
                    for href in hrefs:
                        try:
                            if not href.startswith('http'):
                                current_url = page.url
                                base_url = "/".join(current_url.split("/")[:3])
                                await page.goto(base_url + href)
                                await page.wait_for_load_state('networkidle')
                                contents = await page.content()
                                emails1 = EmailParser(contents)
                                emails=emails1.get_email()
                                if emails:
                                    break
                            else:
                                await page.goto(href)
                                await page.wait_for_load_state('networkidle')
                                contents = await page.content()
                                emails1 = EmailParser(contents)
                                emails=emails1.get_email()
                                if emails:
                                    break
                        except Exception as e:
                            logger.error(f"Error following link {href}: {e}")
        await browser.close()
        return emails
    
async def crawler2(url, status):
    tasks = []
    if status != '404':
        tasks.append(make_requests(url))

    results = await asyncio.gather(*tasks)
    for result, url in results:
        if result is not None:
            emails1 = EmailParser(result)
            emails=emails1.get_email()
            print("here1")
            # breakpoint()
            if not emails:
                emails_list = await playwright_email_extractor(url)
                if emails_list:
                    return emails_list
            else:
                return emails
    return []

def main(url):
    # url = "https://safalpun.com.np/"
    logger.info(f"Processing {url}")
    page_content, status_code = fetch_page(url)
    if url.startswith('https://www.tiktok.com'):
        tiktok_crawler.main2(url)

 
 
    if page_content:
            # emails = EmailParser(page_content)
            # # emails=emails.get_email()
            all_pages = find_all_pages(url, page_content)
            logger.info(f"Found {len(all_pages)} pages from {url}. Processing each page for emails...")

            for page_url in all_pages:
                logger.info(f"Processing page: {page_url}")
                # Fetch and extract emails from each found page
                page_content, status_code = fetch_page(page_url)
                if page_content:
                    emails = EmailParser(page_content)
                    emails=emails.get_email()
                    print('emails',emails)
                    if emails:
                        logger.info(f"Found1 emails on {page_url}: {emails}")
                        break
                else:
                    logger.error(f"Failed to fetch the page {page_url} with status code {status_code}")
            # If no emails were found on the base page or extracted pages, move to crawler2
            if not emails:
                logger.info(f"No emails found even with extracted pages. Moving to crawler2...")
                loop = asyncio.get_event_loop()
                emails = loop.run_until_complete(crawler2(url, status_code))

                # breakpoint()
                # newresult =set(emails)
                if emails:
                    logger.info(f"Found emails using crawler2: {emails}")
                    print(emails)
                else:
                    logger.info(f"No emails found even with crawler2 for {url}")
                    print("No emails found with crawler2")
    else:
        logger.error(f"Failed to fetch the page {url} with status code {status_code}")
        print(f"Error fetching {url}: {status_code}")
# Handle interruptions
def handle_interrupt(signal, frame):
    logger.info("Interrupt received. Exiting...")
    sys.exit(0)
if __name__ == "__main__":
    signal.signal(signal.SIGINT, handle_interrupt)
    main("https://tamangsurendra.com.np/")
    #https://tamangsurendra.com.np/