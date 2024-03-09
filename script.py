"""
Scrapes a headline from The Daily Pennsylvanian website and saves it to a 
JSON file that tracks featured headlines over time.
"""

import os
import sys

import daily_event_monitor

import bs4
import requests
import loguru

def check_row_featured(row: bs4.Tag) -> bool:
    inner_div = row.find("div")
    if inner_div == None:
        return False
    heading = inner_div.find("h3")
    if heading == None:
        return False
    return heading.text == "Featured"

def scrape_data_point():
    """
    Scrapes the featured article titles/links from The Daily Pennsylvanian home page.

    Returns:
        list[dict]: A list of key-value pairs for each article, storing the link and title
    """
    req = requests.get("https://www.thedp.com/")
    loguru.logger.info(f"Request URL: {req.url}")
    loguru.logger.info(f"Request status code: {req.status_code}")

    if req.ok:
        soup = bs4.BeautifulSoup(req.text, "html.parser")
        # Get all featured headlines of the day
        all_rows = soup.find_all("div", class_="row")
        selected_row = None
        for row in all_rows:
            if check_row_featured(row):
                selected_row = row
                break
        featured_article_metadata = []
        if selected_row:
            for article_div in selected_row.find("div").find("div").find_all("div"):
                link = article_div.find("a", class_ = 'frontpage-link standard-link')
                if not link:
                    continue
                featured_article_metadata.append({'title': link.text, 'link': link['href']})
        loguru.logger.info(f"Data points: {featured_article_metadata}")
        return featured_article_metadata


if __name__ == "__main__":

    # Setup logger to track runtime
    loguru.logger.add("scrape.log", rotation="1 day")

    # Create data dir if needed
    loguru.logger.info("Creating data directory if it does not exist")
    try:
        os.makedirs("data", exist_ok=True)
    except Exception as e:
        loguru.logger.error(f"Failed to create data directory: {e}")
        sys.exit(1)

    # Load daily event monitor
    loguru.logger.info("Loading daily event monitor")
    dem = daily_event_monitor.DailyEventMonitor(
        "data/daily_pennsylvanian_headlines.json"
    )

    # Run scrape
    loguru.logger.info("Starting scrape")
    try:
        data_point = scrape_data_point()
    except Exception as e:
        loguru.logger.error(f"Failed to scrape data point: {e}")
        data_point = None

    # Save data
    if data_point is not None:
        dem.add_today(data_point)
        dem.save()
        loguru.logger.info("Saved daily event monitor")

    def print_tree(directory, ignore_dirs=[".git", "__pycache__"]):
        loguru.logger.info(f"Printing tree of files/dirs at {directory}")
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            level = root.replace(directory, "").count(os.sep)
            indent = " " * 4 * (level)
            loguru.logger.info(f"{indent}+--{os.path.basename(root)}/")
            sub_indent = " " * 4 * (level + 1)
            for file in files:
                loguru.logger.info(f"{sub_indent}+--{file}")

    print_tree(os.getcwd())

    loguru.logger.info("Printing contents of data file {}".format(dem.file_path))
    with open(dem.file_path, "r") as f:
        loguru.logger.info(f.read())

    # Finish
    loguru.logger.info("Scrape complete")
    loguru.logger.info("Exiting")
