import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib3.exceptions import InsecureRequestWarning

def get_element_by_css_selector(url, selector, rawdata=False):
    try:
        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
        resp = requests.get(url, verify=False)
        print(url)
        html = resp.text
        soup = BeautifulSoup(html, "html5lib")
        tag = soup.select(selector)[0]

        if rawdata:
            return tag.text
        else:
            if tag.text is not None:
                return float(tag.text.replace(",", ""))
            else:
                return 0
    except AttributeError as e:
        print(e)
        return None


def get_elements_by_css_selector(url, selector):
    try:
        requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
        resp = requests.get(url)
        html = resp.text
        soup = BeautifulSoup(html, "html5lib")
        tags = soup.select(selector)
        return tags
    except:
        return None


def get_code_list_by_market(market=1):
    """
    get listed company information such as code and name
    :param market: 1: all, 2: kospi, 3: kosdaq
    :return: DataFrame
    """
    url = f"http://comp.fnguide.com/SVO2/common/lookup_data.asp?mkt_gb={market}&comp_gb=1"
    requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)
    resp = requests.get(url)
    data = resp.json()
    df = pd.DataFrame(data)
    df = df.set_index(['cd', 'nm'])
    return df







if __name__ == "__main__":
    df = get_code_list_by_market(market=3)
    print(df.head())
