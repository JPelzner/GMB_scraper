import time
import numpy as np
import pandas as pd
import os
from pathlib import Path
from datetime import datetime, date

from selenium import webdriver
import chromedriver_autoinstaller
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
# from webdriver_manager.core.utils import read_version_from_cmd, PATTERN
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC


class GMB_scraper():
    def __init__(self, chrome_options):
        self.client_code = input("Please enter the client code\n\n*")
        self.cutoff_code = input(
            """Please enter a number to specify the time intervals
            1y - ["a year"]
            2y - ["2 years"]
            3y - ["3 years"]
            1-3y - ["a year", "2 years", "3 years"]
            1m - ["a month"]
            6m - ["6 months"]
            1 - ["a month", "3 months", "a year"]
            2 - ["a month", "2 months", "3 months"]
            3 - ["a month", "2 months", "3 months", "4 months", "5 months"]
            4 - ["3 months", "6 months"]
            5 - ["a month", "3 months", "6 months", "a year"]
            6 - multiple intervals (breakdown by month over past n months)
            7 - one interval (n months)
            * """
        )
        self.chrome_options = chrome_options

    # load files containing the list of competitors for a certain client and city
    def load_indivual_files(self, client_code):
        """Return list of filepath(s)
        Each entry in the list is a tuple
        The first value in the tuple is the type of file
        The second is the actual filename"""
        print("LOAD FILE(S)")
        filepaths = []
        for p in Path("./inputs").glob("*.csv"):
            detail1 = (
                str(p).split(".csv")[0].split("inputs\\")[1].split("__")[0]
            )  # for all locations
            print(f"~~{detail1}")
            if client_code in detail1:  # for all client locations
                print(str(p))
                filename = str(p).split("inputs\\")[-1]
                # detail = str(p).split("_competitor")[0].split("inputs\\")[1]
                filepaths.append((client_code, filename))
                return filepaths

    def load_master_competitor_file(self):
        """Return list of filepath(s)
        Each entry in the list is a tuple
        The first value in the tuple is the type of file
        The second is the actual filename"""
        print("LOAD MASTER FILE")
        filepath = ()
        for p in Path("./inputs").glob("*.xlsx"):
            detail1 = (
                str(p).split(".csv")[0].split("inputs\\")[1].split("__")[0]
            )  # for all locations
            # print(f"~~{detail1}")
            if 'master_competitor_doc' in detail1:  # for all client locations
                print(str(p))
                filename = str(p)
                # detail = str(p).split("_competitor")[0].split("inputs\\")[1]
                filepath = ('ALL_CLIENTS', filename)
                return filepath

    def find_target_review_tags(self, driver, pane, total_review_count, cutoff_date):
        """Scroll down on the page to add more reviews.
        Stop scrolling in one of two cases:
        1) We see the end date for our collection period on a review date
        --save all loaded reviews to a variable
        --look at date tag for each review
        --if our time period input is in the date tag
            --stop scrolling
        2) We have reached the end of the review list
        --total reviews loaded from last scroll
        equals amount of reviews loaded from this scroll"""
        print(f"CUTOFF DATE: {cutoff_date}")
        if "year" in cutoff_date:
            if cutoff_date == "a year":
                cutoff_int = 1
            else:
                cutoff_int = int(cutoff_date.split(" years")[0])
        elif "month" in cutoff_date:
            if cutoff_date == "a month":
                cutoff_int = 1
            else:
                cutoff_int = int(cutoff_date.split(" months")[0])
        elif "week" in cutoff_date:
            if cutoff_date == "a week":
                cutoff_int = 1
            else:
                cutoff_int = int(cutoff_date.split(" weeks")[0])
        # print(f"CUTOFF INT: {cutoff_int}")
        scroll_count = 0
        # review_date_tags = driver.find_elements(
        #     By.CSS_SELECTOR, "div[class*='ODSEW'] > span[aria-label*='star'] + span"
        # )
        review_date_tags = driver.find_elements(
            By.CSS_SELECTOR, "div[class*='GHT2ce'] span[aria-label*='star'] + span"
        )

        # time.sleep(30)
        # print(review_date_tags)

        # print(f" # REVIEW DATE TAGS: \n{len(review_date_tags)}")
        review_rating_tags = driver.find_elements(
            By.CSS_SELECTOR, "div[class*='GHT2ce'] span[aria-label*='star']"
        )
        # review_text_tags = driver.find_elements(
        #     By.CSS_SELECTOR, "div[class*='GHT2ce'] div[tabindex='-1']"
        # )
        review_text_tags = driver.find_elements(
            By.CSS_SELECTOR, "div[class='GHT2ce']")
        print(
            f"\nSCROLL COUNT: {scroll_count}\n NUMBER OF REVIEWS LOADED: {len(review_date_tags)}"
        )
        if len(review_text_tags) == 0:
            print(f"*** REVIEW DATES NOT LOADED")
            time.sleep(2)
            review_text_tags = driver.find_elements(
                By.CSS_SELECTOR, "div[class='GHT2ce']")
            print(
                f"\nSCROLL COUNT: {scroll_count}\n NUMBER OF REVIEWS LOADED: {len(review_date_tags)}"
            )
        num_review_text_tags = 0
        buffer_count = 0
        print(f"TOTAL REVIEW COUNT: {total_review_count}")
        print(f"TOTAL REVIEW DATE TAGS: {len(review_date_tags)}")
        review_end = False
        if total_review_count == len(review_date_tags):
            print("REACHED END OF REVIEWS")
            review_end = True
            if "year" in cutoff_date:
                review_date_ints = [
                    span.text.split(" year")[0]
                    for span in review_date_tags
                    if "year" in span.text
                ]
            elif "month" in cutoff_date:
                review_date_ints = [
                    span.text.split(" month")[0]
                    for span in review_date_tags
                    if "month" in span.text
                ]
            elif "week" in cutoff_date:
                review_date_ints = [
                    span.text.split(" week")[0]
                    for span in review_date_tags
                    if "week" in span.text
                ]

            if len(review_date_ints) == 0:
                max_review_date_int = 0
            else:
                review_date_ints = [
                    1 if entry == "a" else int(entry) for entry in review_date_ints
                ]
                max_review_date_int = max(review_date_ints)
            # print(f"(1) MAX REVIEW DATE INT: {max_review_date_int}")
            # the loop will stop if we reach our cut off date in the current scroll
            # if any([cutoff_date in span.text for span in review_date_tags]):
            #     print("CUT OFF DATE REACHED")
            #     return review_date_tags, review_rating_tags, review_text_tags

            if max_review_date_int == 0 or max_review_date_int >= cutoff_int:
                print("CUT OFF DATE REACHED")
            else:
                print("NOT PAST CUT OFF DATE")

        while total_review_count != len(
            review_date_tags
        ):  # this loop will end if we hit the bottom of the page
            time.sleep(1.2)
            if len(review_date_tags) > 25:
                recent_review_date_tags = review_date_tags[-20:]
            else:
                recent_review_date_tags = review_date_tags
            if "year" in cutoff_date:
                review_date_ints = [
                    span.text.split(" year")[0]
                    for span in recent_review_date_tags
                    if "year" in span.text
                ]
            elif "month" in cutoff_date:
                review_date_ints = [
                    span.text.split(" month")[0]
                    for span in recent_review_date_tags
                    if "month" in span.text
                ]
            elif "week" in cutoff_date:
                review_date_ints = [
                    span.text.split(" week")[0]
                    for span in recent_review_date_tags
                    if "week" in span.text
                ]

            if len(review_date_ints) == 0:
                max_review_date_int = 0
            else:
                review_date_ints = [
                    1 if entry == "a" else int(entry) for entry in review_date_ints
                ]
                max_review_date_int = max(review_date_ints)
            # print(f"(2) MAX REVIEW DATE INT: {max_review_date_int}")
            # the loop will stop if we reach our cut off date in the current scroll
            # if any([cutoff_date in span.text for span in review_date_tags]):
            #     print("CUT OFF DATE REACHED")
            #     return review_date_tags, review_rating_tags, review_text_tags

            if max_review_date_int >= cutoff_int:
                print("CUT OFF DATE REACHED !!")
                return (
                    review_date_tags,
                    review_rating_tags,
                    review_text_tags,
                    review_end,
                )

            # but if we do not, we will scroll again and check our logic once more
            else:
                # print("KEEP SCROLLING")
                print("SCROLL BLOCK")
                pane.send_keys(Keys.END)
                review_date_tags = driver.find_elements(
                    By.CSS_SELECTOR,
                    "div[class*='GHT2ce'] span[aria-label*='star'] + span",
                )
                review_rating_tags = driver.find_elements(
                    By.CSS_SELECTOR, "div[class*='GHT2ce'] span[aria-label*='star']"
                )
                review_text_tags = driver.find_elements(
                    By.CSS_SELECTOR, "div[class='GHT2ce']"
                )
                scroll_count += 1
                if scroll_count % 5 == 0:
                    print(
                        f"\nSCROLL COUNT: {scroll_count}\n NUMBER OF REVIEWS LOADED: {len(review_date_tags)}"
                    )
                    print(
                        f"NUMBER OF REVIEW TAGS FOR TEXT ANALYSIS: {len(review_text_tags)}"
                    )
                    print(f"NUM REVIEW TEXT TAGS: {num_review_text_tags}")
                    print(
                        f"LEN REVIEW TEXT TAGS LIST: {len(review_text_tags)}")

                    if num_review_text_tags == len(review_text_tags):
                        print("*BUFFERING")
                        time.sleep(3)
                        buffer_count += 1
                        if buffer_count == 3:
                            print("!! REVIEWS NOT LOADING")
                        #         return (
                        #             review_date_tags,
                        #             review_rating_tags,
                        #             review_text_tags,
                        #         )
                        # else:
                        print("MORE REVIEWS LOADING")
                        num_review_text_tags = len(review_text_tags)

        return review_date_tags, review_rating_tags, review_text_tags, review_end

    def pull_data_from_review_tags(
            self, cutoff_date, review_date_tags, review_rating_tags, review_text_tags):
        """
        Iterating through the review tags, populate an output dictionary

        Returns:
            dict: _description_
        """

        if "year" in cutoff_date:
            if cutoff_date == "a year":
                cutoff_int = 1
            else:
                cutoff_int = int(cutoff_date.split(" years")[0])
        elif "month" in cutoff_date:
            if cutoff_date == "a month":
                cutoff_int = 1
            else:
                cutoff_int = int(cutoff_date.split(" months")[0])
        elif "week" in cutoff_date:
            if cutoff_date == "a week":
                cutoff_int = 1
            else:
                cutoff_int = int(cutoff_date.split(" weeks")[0])
        # determine the relative dates of these reviews
        # if they are within the time period specified above,
        # add the reviews to the count
        target_review_count = 0
        invisalign_review_count = None
        target_review_rating_lst = []
        target_review_blank_pct = None
        # target_review_blank_pct = []
        target_review_char_count_avg = None
        # target_review_char_count_avg = []

        # if review_date_tags is None:
        #     target_review_rating_avg = None
        #     target_review_blank_pct = None
        #     target_review_char_count_avg = None
        #     return target_review_count, target_review_rating_avg, target_review_blank_pct, target_review_char_count_avg

        # else:
        # target_review_count
        end_index = None
        for review_index, review in enumerate(review_date_tags):
            review_date = review.text
            # print(f"---REVIEW DATE: {review_date}")
            if "year" in cutoff_date:
                if "year" in review_date:
                    review_date_year = review_date.split(" year")[0]
                    if review_date_year == "a":
                        review_date_year = 1
                    else:
                        review_date_year = int(review_date_year)
                    if review_date_year < cutoff_int:
                        target_review_count += 1
                        saved_index = review_index
                    else:
                        end_index = review_index
                        break
                else:
                    target_review_count += 1
            elif "month" in cutoff_date:
                if "month" in review_date:
                    review_date_month = review_date.split(" month")[0]
                    if review_date_month == "a":
                        review_date_month = 1
                    else:
                        review_date_month = int(review_date_month)
                    if review_date_month < cutoff_int:
                        target_review_count += 1
                    else:
                        end_index = review_index
                        break
                elif "year" in review_date:  # we are out of bounds
                    end_index = review_index
                    break
                else:  # 'weeks', 'days', 'hours'
                    target_review_count += 1
            elif "week" in cutoff_date:
                if "week" in review_date:
                    review_date_month = review_date.split(" week")[0]
                    if review_date_month == "a":
                        review_date_month = 1
                    else:
                        review_date_month = int(review_date_month)
                    if review_date_month < cutoff_int:
                        target_review_count += 1
                    else:
                        end_index = review_index
                        break
                elif "year" in review_date:  # we are out of bounds
                    end_index = review_index
                    break
                elif "month" in review_date:  # we are also out of bounds
                    end_index = review_index
                    break
                else:  # 'days', 'hours'
                    target_review_count += 1
        print(f"END INDEX: {end_index}")
        print(f"~~~ TARGET REVIEW COUNT: {target_review_count}")
        if end_index is None:
            target_review_rating_lst = [
                int(span.get_attribute("aria-label").strip(" ").split(" ")[0])
                for span in review_rating_tags
            ]
            print("***B2")
        else:
            target_review_rating_lst = [
                int(span.get_attribute("aria-label").strip(" ").split(" ")[0])
                for span in review_rating_tags[:end_index]
            ]
            print("***B1")
            if end_index == 0:
                target_review_rating_lst = []
            else:
                target_review_rating_lst = target_review_rating_lst[:end_index]
                review_text_tags = review_text_tags[:end_index]

            # target_review_rating_lst = []
        print(
            f"~~~ TARGET RATING COUNT: {len(target_review_rating_lst)} \n {target_review_rating_lst}"
        )
        sub_5_review_count = len(
            [i for i in target_review_rating_lst if int(i) in [1, 2, 3, 4]]
        )
        review_count_1star = target_review_rating_lst.count(1)
        if len(target_review_rating_lst) != 0:
            target_review_rating_avg = np.mean(target_review_rating_lst)
        else:
            target_review_rating_avg = None
        print(f"~~~ TARGET RATING AVERAGE: {target_review_rating_avg}")

        # analyze the actual content of the review
        # print(f"REVIEW TEXT TAGS: {review_text_tags}")
        target_review_text_lst = []
        target_response_text_lst = []
        for tag_index, outer_tag in enumerate(review_text_tags[:end_index]):
            try:
                inner_tag = outer_tag.find_element(
                    By.CSS_SELECTOR, "div[class*='MyEned'] span[class*='wiI7pd']"
                )
                review_text = inner_tag.text
            except Exception as e:
                # print(f"ERROR:  {e}")
                # print(f"\n ({tag_index})  -- NO REVIEW TEXT TAG")
                review_text = ""
            # print(f"\n ({tag_index}) {review_text}")
            target_review_text_lst.append(review_text)

            response_tag_lst = outer_tag.find_elements(
                By.CSS_SELECTOR, "div[class='CDe7pd'] div[class*='wiI']"
            )
            if len(response_tag_lst) > 0:
                response_text = response_tag_lst[0].text
                target_response_text_lst.append(response_text)

        # target_review_non_blank_pct
        # if end_index is None:
        #     target_review_blank_pct = None
        # else:
        if len(target_review_text_lst) != 0:
            num_blank_reviews = len(
                [review for review in target_review_text_lst if len(
                    review) == 0]
            )
            target_review_blank_pct = num_blank_reviews / \
                len(target_review_text_lst)
            # target_review_content_pct = 1 - target_review_blank_pct
            target_review_content_count = len(
                target_review_text_lst) - num_blank_reviews
        else:
            target_review_blank_pct = None
            target_review_content_count = None
            # target_review_content_pct = 1

        # target_review_char_count_avg
        print("AVG. CHARACTER COUNT")
        # print(target_review_text_lst)
        # if end_index is None:
        #     target_review_char_count_avg = None
        #     target_review_response_pct = None
        # else:
        if len(target_review_text_lst) != 0:
            target_review_char_count_avg = np.mean(
                [len(review)
                 for review in target_review_text_lst if len(review) != 0]
            )
            # response count
            target_review_response_count = len(target_response_text_lst)
            target_review_response_pct = target_review_response_count / len(
                target_review_text_lst
            )
        else:
            target_review_char_count_avg = None
            target_review_response_pct = None

        # 'invisalign' review count ***only for use in 'invisalign' specific analyses***
        # if "invisalign" in file_detail:
        #     invisalign_review_count = len(
        #         [
        #             review
        #             for review in target_review_text_lst
        #             if "invisalign" in review or "Invisalign" in review
        #         ]
        #     )

        # keyword review count
        keyword_review_count = 0
        keyword_lst = ["oral surgeon", "oral surgery",
                       "dental implants", "wisdom tooth", "wisdom teeth"]

        for review in target_review_text_lst:
            if any([i in review.lower() for i in keyword_lst]):
                keyword_review_count += 1

        return (
            target_review_count,
            target_review_rating_avg,
            target_review_content_count,
            target_review_blank_pct,
            target_review_char_count_avg,
            target_review_response_pct,
            keyword_review_count,
            invisalign_review_count,
            sub_5_review_count,
            review_count_1star,
        )

    def pull_competitor_review_stats(
        self, cutoff_date_lst, practice_name, practice_url=None
    ):
        """Pull competitor review stats"""

        # driver = webdriver.Chrome(
        #     ChromeDriverManager("114.0.5735.90").install())

        # version = read_version_from_cmd("/usr/bin/chrome-bin --version", PATTERN["chrome"])
        # driver = webdriver.Chrome(
        #     ChromeDriverManager(version=version).install(), chrome_options=self.chrome_options
        # )

        chromedriver_autoinstaller.install()
        # driver = webdriver.Chrome()
        driver = webdriver.Chrome(self.chrome_options)

        # determine if the URL reflects the 'place' or the 'search' URL
        location_url_lst = []
        location_review_dict = {}

        if practice_url is None:
            # set up the initial Google Maps search for that practice
            practice_name_lst = practice_name.split(" ")
            url = f"https://www.google.com/maps/search/{'+'.join(practice_name_lst)}"
            driver.get(url)
            time.sleep(5)  # let the results load
            current_url = driver.current_url
            print(f"CURRENT GMB: {practice_name}")
            # print(f"CURRENT URL: {current_url}")

            if ".com/maps/search/" in current_url:
                # if the practice entry has multiple results,
                # add each URL into 'location_url_lst'
                all_results = driver.find_elements(
                    By.CSS_SELECTOR, f"a[aria-label='{practice_name}']"
                )
                print(f"ALL RESULTS: {all_results}")
                for result in all_results:
                    location_url_lst.append(result.get_attribute("href"))
            else:
                # if the entry redirects to a place page,
                # add that URL into 'location_url_lst'
                location_url_lst.append(current_url)
            #     pass

        # then the practice URL will be included
        else:
            print(f"CURRENT GMB: {practice_name}")
            print(f"\nPRACTICE URL: {practice_url}")
            # location_url_lst.append(practice_url)

        # for loc_url in location_url_lst:
        #     # navigate to the location specific URL
        #     print(f"\nLOC URL: {loc_url}")
            # driver.get(loc_url)
            driver.get(practice_url)
            time.sleep(2)

            # find the city of this location
            address_element = None
            try:
                address_element = driver.find_element(
                    By.CSS_SELECTOR, "button[aria-label*='Address']"
                )
            except Exception as e:
                print(f'ADDRESS BLOCK ERROR')
                time.sleep(0.6)
                try:
                    address_element = driver.find_element(
                        By.CSS_SELECTOR, "button[aria-label*='Address']"
                    )
                except:
                    pass
            if address_element is not None:
                address = address_element.get_attribute(
                    "aria-label").split(": ")[1]
                print(f"ADDRESS: {address}")
                address_zip = str(address.split(", ")[-1].split(" ")[1])

            else:
                address_zip = '1'

            location_review_dict[address_zip] = {}
            # add_location_key(driver, location_review_dict)

            # select the review list of that GMB page
            try:
                # review_rating_element = driver.find_element(
                #     By.CSS_SELECTOR, "ol[aria-label*='stars']"
                # )
                # avg_review_rating = (
                #     review_rating_element.get_attribute(
                #         "aria-label").strip().split(" ")[0]
                # )
                avg_review_rating = driver.find_element(
                    By.CSS_SELECTOR, "div[class*='F7nice'] span[aria-hidden='true']").text
                print(f"AVG REVIEW RATING: {avg_review_rating}")
            except Exception as e:
                print(f"EXCEPTION:  {e}")
                avg_review_rating = None
            try:
                # review_button = driver.find_elements(
                #     By.CSS_SELECTOR, "button[aria-label*='review']"
                # )
                # print(f"REVIEW BUTTON: {review_button}")
                # total_review_count_raw = review_button.get_attribute("aria-label").split(
                #     " "
                # )[0]
                review_text = driver.find_element(
                    By.CSS_SELECTOR,
                    "span[aria-label*='reviews']",
                )
                total_review_count_raw = review_text.get_attribute("aria-label").split(" ")[
                    0
                ]
                print(f"REVIEW COUNT TEXT: '{total_review_count_raw}'")
                if "," in total_review_count_raw:
                    total_review_count = int(
                        "".join(total_review_count_raw.split(",")))
                else:
                    total_review_count = int(total_review_count_raw)
                print(f"CUMULATIVE REVIEW COUNT: {total_review_count}")

            except Exception as e:
                print(f"EXCEPTION:  {e}")
                total_review_count = 0

            try:
                # review_button = driver.find_element(
                #     By.CSS_SELECTOR,
                #     "button[jsaction*='reviewChart']",
                # )
                review_button = driver.find_element(
                    By.CSS_SELECTOR,
                    "button[jsaction*='pane'][aria-label*='More reviews']",
                )
                print(f"(1) REVIEW BUTTON: {review_button}")
                # driver.implicitly_wait(4)
                time.sleep(1.5)
                ActionChains(driver).move_to_element(review_button).click(
                    review_button
                ).perform()
                # review_button.click()
                time.sleep(2.5)
            except Exception as e:
                print(f"EXCEPTION:  {e}")
                print(" (2) REVIEW BUTTON")
                review_button = driver.find_element(
                    By.CSS_SELECTOR,
                    "button[jsaction*='pane'][aria-label*='review']",
                )
                print(f"REVIEW BUTTON: {review_button}")
                # driver.implicitly_wait(4)
                time.sleep(2)
                ActionChains(driver).move_to_element(review_button).click(
                    review_button
                ).perform()
                # review_button.click()
                time.sleep(2.5)

            try:
                # sort the reviews by newest first
                sort_button = driver.find_element(
                    By.CSS_SELECTOR, "button[aria-label='Sort reviews']"
                )
                sort_button.click()
                time.sleep(1)
            except Exception as e:
                print(f"**ERROR: {e}")
                print("SORT BUTTON")
            try:
                newest_button = driver.find_element(
                    By.CSS_SELECTOR, "div[id='action-menu'] div[data-index='1']"
                )
                time.sleep(1.5)
                newest_button.click()
            except Exception as e:
                print(f"**ERROR:  {e}")
                print('"NEWEST" BUTTON')

            time.sleep(1.5)
            # exit scope if no reviews present
            if total_review_count == 0:
                location_review_dict[address_zip].update(
                    {
                        'current': {
                            "Cumulative Reviews": total_review_count,
                            "Avg Review Rating": None,
                            "Interval Review Count": None,
                            "Interval Sub-5 Count": None,
                            "Interval 1-Star Count": None,
                            "Interval Review Rating": None,
                            "% Content Reviews": None,
                            "Intveral Content Reviews": None,
                            "Avg Char Count": None,
                            "Kwd Review Count": None,
                            "Review Responses": None,
                            "% Review Responses": None,
                            "Invisalign Review Count": None,
                        }
                    }
                )
                for c_idx, cutoff_date in enumerate(cutoff_date_lst):
                    location_review_dict[address_zip].update(
                        {
                            cutoff_date: {
                                "Cumulative Reviews": total_review_count,
                                "Avg Review Rating": None,
                                "Interval Review Count": None,
                                "Interval Sub-5 Count": None,
                                "Interval 1-Star Count": None,
                                "Interval Review Rating": None,
                                "% Content Reviews": None,
                                "Intveral Content Reviews": None,
                                "Avg Char Count": None,
                                "Kwd Review Count": None,
                                "Review Responses": None,
                                "% Review Responses": None,
                                "Invisalign Review Count": None,
                            }
                        }
                    )

            else:
                # scroll down to load more reviews
                # until either the end of the time period for collection is reached
                # or until the last (oldest) review is reached
                # this one has been depricated
                # pane = driver.find_element(
                #     By.CSS_SELECTOR, "div[class*='section-scrollbox']"
                # )
                # i did not get this one to work
                # pane = driver.find_elements(
                #     By.CSS_SELECTOR, "div[data-review-id*='ChZ'] span[class*='wiI']"
                # )[0]
                pane = driver.find_elements(
                    By.CSS_SELECTOR, "div[tabindex='-1'][class*='m6QErb D']"
                )[0]
                print("PANE LOCATED")
                # print(pane)

                # first_review_txt = pane.get_attribute('innerHTML')
                # print(f"FIRST REVIEW TEXT: {first_review_txt}")

                # element = pane.find_element(
                #     By.CSS_SELECTOR, "div[aria-label*=' ']"
                # )
                # print(f'PANE ELEMENT TEXT: {element.get_attribute("aria-label")}')

                print(f"CUTOFF DATE LIST:  {cutoff_date_lst}")
                location_review_dict[address_zip].update(
                    {
                        'current': {
                            "Cumulative Reviews": total_review_count,
                            "Avg Review Rating": avg_review_rating,
                            "Interval Review Count": None,
                            "Interval Sub-5 Count": None,
                            "Interval 1-Star Count": None,
                            "Interval Review Rating": None,
                            "Content Reviews": None,
                            "% Content Reviews": None,
                            "Avg Char Count": None,
                            "Kwd Review Count": None,
                            "% Review Responses": None,
                            "Invisalign Review Count": None,
                        }
                    }
                )
                for c_idx, cutoff_date in enumerate(cutoff_date_lst):
                    print(f"\nCURRENT CUTOFF DATE: {cutoff_date}")
                    (
                        total_date_tags,
                        total_rating_tags,
                        total_text_tags,
                        review_end,
                    ) = self.find_target_review_tags(
                        driver, pane, total_review_count, cutoff_date
                    )  # run the function
                    print(f"TARGET REVIEW TAGS LOADED")
                    (
                        target_review_count,
                        target_review_rating_avg,
                        target_review_content_count,
                        target_review_blank_pct,
                        target_review_char_count_avg,
                        target_review_response_pct,
                        keyword_review_count,
                        invisalign_review_count,
                        sub_5_star_review_count,
                        review_count_1_star,
                    ) = self.pull_data_from_review_tags(
                        cutoff_date,
                        total_date_tags,
                        total_rating_tags,
                        total_text_tags,
                    )
                    print(f"REVIEW TAG DATA PULLED")
                    print(f"REVIEW COUNT: {target_review_count}")
                    if target_review_rating_avg is not None:
                        target_review_rating_avg = round(
                            target_review_rating_avg, 3)
                    print(f"AVERAGE REVIEW RATING: {target_review_rating_avg}")
                    if target_review_blank_pct is not None:
                        target_review_blank_pct = round(
                            target_review_blank_pct * 100, 1)
                        target_review_content_pct = 100 - target_review_blank_pct
                    else:
                        target_review_content_pct = None
                    print(
                        f"PCT NON-BLANK REVIEWS: {target_review_content_pct}")
                    if target_review_char_count_avg is not None:
                        target_review_char_count_avg = round(
                            target_review_char_count_avg, 0
                        )
                    print(
                        f"AVG CHARACTER COUNT OF NON-BLANK REVIEWS: {target_review_char_count_avg}"
                    )
                    print(
                        f"PCT REVIEWS RESPONDED TO: {target_review_response_pct}")
                    print(
                        f"INVISALIGN REVIEW COUNT: {invisalign_review_count}")
                    location_review_dict[address_zip].update(
                        {
                            cutoff_date: {
                                "Cumulative Reviews": total_review_count,
                                "Avg Review Rating": avg_review_rating,
                                "Interval Review Count": target_review_count,
                                "Interval Sub-5 Count": sub_5_star_review_count,
                                "Interval 1-Star Count": review_count_1_star,
                                "Interval Review Rating": target_review_rating_avg,
                                "Content Reviews": target_review_content_count,
                                "% Content Reviews": target_review_content_pct,
                                "Avg Char Count": target_review_char_count_avg,
                                "Kwd Review Count": keyword_review_count,
                                "% Review Responses": target_review_response_pct,
                                "Invisalign Review Count": invisalign_review_count,
                            }
                        }
                    )
                    time.sleep(2)
        driver.close()
        return location_review_dict

    def produce_output_df(self, output_df, location_review_dict, competitor):
        data_lst = []
        for zipcode, interval_dict in location_review_dict.items():
            print(f"ZIP: {zipcode}")
            print(f"INNER DICT: {interval_dict}")
            for cutoff_date, review_dict in interval_dict.items():
                entry_dict = {
                    "comp": competitor,
                    "loc_zip": str(zipcode),
                    "interval": cutoff_date,
                }
                for review_key, review_val in review_dict.items():
                    # print(f"REVIEW KEY: {review_key}")
                    if review_key == "Cumulative Reviews":
                        entry_dict.update(
                            {"cumulative_reviews": review_val})
                    elif review_key == "Avg Review Rating":
                        entry_dict.update({"total_avg_rating": review_val})
                    elif review_key == "Interval Review Count":
                        entry_dict.update(
                            {"interval_review_count": review_val})
                    elif review_key == "Interval Sub-5 Count":
                        entry_dict.update(
                            {"interval_sub5star_count": review_val})
                    elif review_key == "Interval 1-Star Count":
                        entry_dict.update(
                            {"interval_1star_count": review_val})
                    elif review_key == "Interval Review Rating":
                        entry_dict.update(
                            {"interval_avg_rating": review_val})
                    elif review_key == "% Content Reviews":
                        entry_dict.update(
                            {"content_review_pct": review_val})
                    elif review_key == "Avg Char Count":
                        entry_dict.update({"avg_char_count": review_val})
                    elif review_key == "Kwd Review Count":
                        entry_dict.update({"keyword_count": review_val})
                    elif review_key == "% Review Responses":
                        entry_dict.update(
                            {"review_response_pct": review_val})
                    # elif review_key == "Invisalign Review Count":
                    #         entry_dict.update(
                    #             {"invis_review_count": review_val})
                    else:
                        pass
                data_lst.append(entry_dict)

        print(data_lst)
        current_df = pd.DataFrame(data_lst)
        if output_df is None:
            output_df = current_df.copy()
        else:
            output_df = output_df.append(current_df, ignore_index=True)

        return output_df

    def save_monthly_gains_file(self, df, report_date, client_sheet):
        num_comps = len(df) // 13
        start_date = pd.to_datetime(date.today())
        try:
            start_date = start_date.replace(
                year=start_date.year-1, month=start_date.month-2)
        except Exception as e:
            print(f"EXCEPTION LINE 897  :  {e}")
            start_month = start_date.month-2
            if start_month == -1:
                start_month = 11
            elif start_month == 0:
                start_month = 12

            start_date = start_date.replace(
                year=start_date.year-2, month=start_month, day=28)
        end_date = pd.to_datetime(date.today())
        try:
            end_date = end_date.replace(month=end_date.month-1)
        except:
            print(f"ERROR  :  {e}")
            end_date = end_date.replace(year=start_date.year-1, month=12)
        date_arr = pd.date_range(
            end_date, start_date, freq='-1MS')[:-1] + pd.DateOffset(days=start_date.day-1)
        cum_reviews = []
        for ind, row in df.iterrows():
            if row['interval'] == 'current':
                cum_reviews.append(row['cumulative_reviews'])
            else:
                try:
                    cum_reviews.append(
                        row['cumulative_reviews'] - row['interval_review_count'])
                except:
                    cum_reviews.append(0)
        df['cumulative_reviews'] = cum_reviews
        month_col = []
        for i in range(num_comps):
            for j in date_arr:
                month_col.append(j)
        df['month'] = month_col

        file_str = f'./outputs/{client_sheet}_market_GMB_results_{report_date}.csv'
        df.to_csv(file_str, index=False)
        print(f"FILE SAVED :\n{file_str}")
        return

############ IMPLEMENT THE FUNCTION ON ALL COMPETITORS FOR COMPILED CLIENT LOCATIONS ############
# have the user input the client code that we are analyzing

# set the list of cutoff dates to scrape reviews for
# cutoff_date_lst = ["a year", "2 years", "3 years"]
# cutoff_date_lst = ["3 months", "6 months", "a year"]


def main(headless=True, GPU_blocklist=False):
    chrome_options = Options()
    # chrome_options.add_argument("--disable-extensions")
    # chrome_options.add_argument("--lang=en-US")
    chrome_options.add_argument("--lang=en-GB")
    # chrome_options.add_experimental_option('prefs', {'intl.accept_languages': 'en,en_US'})
    if headless == 1:
        chrome_options.add_argument("--headless")

    if GPU_blocklist == 0:
        chrome_options.add_argument("--ignore-gpu-blocklist")

    scraper = GMB_scraper(chrome_options)
    client_code = scraper.client_code
    cutoff_code = scraper.cutoff_code

    yr_check = 0
    if cutoff_code == "1y":
        cutoff_date_lst = ["a year"]
    elif cutoff_code == "2y":
        cutoff_date_lst = ["2 years"]
    elif cutoff_code == "3y":
        cutoff_date_lst = ["3 years"]
    elif cutoff_code == "1-3y":
        cutoff_date_lst = ["a year", "2 years", "3 years"]
    elif cutoff_code == "1m":
        cutoff_date_lst = ["a month"]
    elif cutoff_code == "6m":
        cutoff_date_lst = ["6 months"]
    elif cutoff_code == "1":
        cutoff_date_lst = ["a month", "3 months", "a year"]
    elif cutoff_code == "2":
        cutoff_date_lst = ["a month", "2 months", "3 months"]
    elif cutoff_code == "3":
        cutoff_date_lst = ["a month", "2 months",
                           "3 months", "4 months", "5 months"]
    elif cutoff_code == "4":
        cutoff_date_lst = ["3 months", "6 months"]
    elif cutoff_code == "5":
        cutoff_date_lst = ["a month", "3 months", "6 months", "a year"]
    elif cutoff_code == "6":
        cutoff_date_lst = ["a month"]
        mo_range = int(
            input("Enter number of months back to collect review volume for   *")
        )
        if 12 <= mo_range < 24:
            yr_check = True
            mo_range = 11
        for num in range(2, mo_range + 1):
            int_str = f"{num} months"
            cutoff_date_lst.append(int_str)
        if yr_check == 1:
            cutoff_date_lst.append("a year")
    elif cutoff_code == "7":
        n = int(input("Enter an integer greater than 1 and less than 12   * "))
        cutoff_date_lst = [f"{n} months"]
    else:
        raise Exception("pick a valid identifier as presented")

    filepath = scraper.load_master_competitor_file()
    print(f"FILEPATH: {filepath}")

    # for each location with a competitor list
    # process that file,
    file = filepath[1]
    # file_detail, file = filepath[0], filepath[1]
    master_wb = pd.ExcelFile(file, engine='openpyxl')
    client_sheet = None
    sheet_names = master_wb.sheet_names
    for sheet in sheet_names:
        if client_code in str(sheet):
            client_sheet = sheet
            print(client_sheet)
            break

    try:
        comp_list_df = master_wb.parse(client_sheet)
    except Exception as e:
        print(f"***ERROR: {e} -- CLIENT CODE:  {client_code}")
        print("UNABLE TO LOAD AN INPUT SHEET FROM MASTER FILE")
        return

    if 'client' in comp_list_df.columns:
        clientonly_flag = input("ENTER (1) for 'CLIENT-ONLY' scope  \n* ")
        if clientonly_flag == '1':
            comp_list_df = comp_list_df[comp_list_df['client'] == 1].reset_index(
            )
    elif 'OMS' in comp_list_df.columns:
        clientonly_flag = input("ENTER (1) for 'OMS' competitors only  \n* ")
        if clientonly_flag == '1':
            comp_list_df = comp_list_df[comp_list_df['OMS'] == 1].reset_index()
    elif 'prospect' in comp_list_df.columns:
        clientonly_flag = input(
            "ENTER (1) for 'prospect' locations only  \n* ")
        if clientonly_flag == '1':
            comp_list_df = comp_list_df[comp_list_df['prospect'] == 1].reset_index(
            )

    comp_lst = comp_list_df["Business"]
    comp_url_lst = comp_list_df["Google URL"]
    print(f"BUSINESSES: \n{comp_lst}")

    output_df = None
    start = time.time()
    for index, competitor in enumerate(comp_lst):
        if index % 10 == 0:
            print(f"\n**{index}")
            print(f"{round(index/len(comp_lst)*100)}%")
            current = time.time()
            elapsed = round(current - start, 0)
            avg_per_row = round(elapsed / (index + 1), 2)
            print(f"{elapsed} seconds total")
            print(f"{avg_per_row} seconds per geo")
            total_time_sec = round(avg_per_row * len(comp_lst))
            print(f"TOTAL TIME ESTIMATE: {total_time_sec/60} minutes")
            print(
                f"TOTAL TIME REMAINING: {round((total_time_sec-elapsed)/60, 1)} minutes"
            )
        # try:
        competitor_url = comp_url_lst[index]
        # skip entries without a valid URL
        if str(competitor_url) == "nan":
            continue
        location_review_dict = scraper.pull_competitor_review_stats(
            cutoff_date_lst, competitor, competitor_url
        )
        output_df = scraper.produce_output_df(
            output_df, location_review_dict, competitor)

    report_date = datetime.strftime(pd.to_datetime(date.today()), "%m%d%y")
    # output_df.to_csv(
    #     f"./outputs/{file_detail}_competitor_review_stats.csv", index=False
    # )
    cutoff_date_savestr = "(" + "_".join(cutoff_date_lst) + ")"
    if cutoff_code == '6':
        cutoff_date_savestr = "(" + cutoff_date_lst[-1] + ")_MONTHLY"
    file_savestr = f"./outputs/{client_code}_{cutoff_date_savestr}_results_{report_date}.csv"
    if clientonly_flag == '1':
        file_savestr = file_savestr.split('.csv')[0]+"_CLIENTONLY.csv"
    output_df.to_csv(
        file_savestr, index=False)
    print(f"FILE SAVED: {file_savestr}")

    if 'MONTHLY' in cutoff_date_savestr:
        scraper.save_monthly_gains_file(
            output_df, report_date, client_sheet)
    return


if __name__ == "__main__":
    # run engine if file used directly from command line
    main(headless=True)
