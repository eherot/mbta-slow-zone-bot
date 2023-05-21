import tweepy
import mastodon as mastodon
import requests
import logging
import argparse
from domains.mastodon import send_fixed_slow_zone_toots, send_new_slow_zone_toots
from domains.twitter import send_fixed_slow_zone_tweets, send_new_slow_zone_tweets
from domains.slack import send_slow_zone_slack
from utils import (
    generate_grouped_slow_zone_list,
    generate_post_text_map
)
import sys
import os

TWITTER_ACCESS_KEY = os.environ.get("ACCESS_KEY")
TWITTER_ACCESS_SECRET = os.environ.get("ACCESS_SECRET")
TWITTER_BEARER_TOKEN = os.environ.get("BEARER_TOKEN")
TWITTER_CONSUMER_KEY = os.environ.get("CONSUMER_KEY")
TWITTER_CONSUMER_SECRET = os.environ.get("CONSUMER_SECRET")
MASTODON_CLIENT_KEY = os.environ.get("MASTODON_CLIENT_KEY")
MASTODON_CLIENT_SECRET = os.environ.get("MASTODON_CLIENT_SECRET")
MASTODON_ACCESS_TOKEN = os.environ.get("MASTODON_ACCESS_TOKEN")

MAX_SLOWZONE_AGE = int(os.environ.get("MAX_SLOWZONE_AGE", 1))
DRY_RUN = False
DEBUG = False

twitter_client = api = tweepy.Client(
    bearer_token=TWITTER_BEARER_TOKEN,
    access_token=TWITTER_ACCESS_KEY,
    access_token_secret=TWITTER_ACCESS_SECRET,
    consumer_key=TWITTER_CONSUMER_KEY,
    consumer_secret=TWITTER_CONSUMER_SECRET,
)

mastodon_client = mastodon.Mastodon(
    api_base_url="https://better.boston",
    client_id=MASTODON_CLIENT_KEY,
    client_secret=MASTODON_CLIENT_SECRET,
    access_token=MASTODON_ACCESS_TOKEN,
)


def main():

    slow_zones = requests.get(
        "https://dashboard.transitmatters.org/static/slowzones/all_slow.json"
    )

    ended_slowzones = generate_grouped_slow_zone_list(
        # Slow zones are 1 day behind so we want to check if zones ended two days ago
        slow_zones.json(),
        "end",
        MAX_SLOWZONE_AGE,
        1
    )
    logging.info(f"ended_slowzones: {ended_slowzones}")

    new_slowzones = generate_grouped_slow_zone_list(
        # Slow zones take 4 days to be recognized
        slow_zones.json(),
        "start",
        MAX_SLOWZONE_AGE + 2,
        1
    )
    logging.info(f"new_slowzones: {new_slowzones}")

    if DEBUG:
        grouped_sz_today = generate_grouped_slow_zone_list(slow_zones.json(), "end", 0, 0)
        logging.debug(f"grouped_sz_today: {grouped_sz_today}")
        post_text_map = generate_post_text_map(grouped_sz_today)
        logging.debug(f"post_text_map: {post_text_map}")

    if not DRY_RUN:
        send_new_slow_zone_tweets(new_slowzones, twitter_client)
        send_new_slow_zone_toots(new_slowzones, mastodon_client)

        send_slow_zone_slack(new_slowzones, True)
        send_slow_zone_slack(ended_slowzones, False)

        send_fixed_slow_zone_tweets(ended_slowzones, twitter_client)
        send_fixed_slow_zone_toots(ended_slowzones, mastodon_client)

    # exit if no issues
    sys.exit(0)


if __name__ == "__main__":

    # argument parsing
    parser = argparse.ArgumentParser(description="MBTA Slow Zone Bot")
    parser.add_argument(
        "--dry-run", default=False, action="store_true", help="Runs bot without posting"
    )
    parser.add_argument(
        "--debug",
        default=False,
        action="store_true",
        help="Runs bot with debug logging",
    )
    args = parser.parse_args()
    DRY_RUN = args.dry_run
    DEBUG = args.debug

    # set logging config
    if DEBUG:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    # begin main program execution
    main()
