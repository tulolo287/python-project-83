from urllib.parse import urlparse


def get_parsed_url(url):
    parsed_url = urlparse(url)
    return f"{parsed_url[0]}://{parsed_url[1]}"
    