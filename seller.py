import io
import logging.config
import os
import re
import zipfile
from environs import Env

import pandas as pd
import requests

logger = logging.getLogger(__file__)


def get_product_list(last_id: str, client_id: str, seller_token: str) -> dict:
    """Get the list of products from the Ozon store.

    Args:
        last_id (str): The ID of the last fetched product for pagination.
        client_id (str): The client ID for the Ozon API.
        seller_token (str): The API token for the Ozon seller account.

    Returns:
        dict: A dictionary containing product list information, including items and pagination details.

    Raises:
        requests.exceptions.RequestException: If the API request fails.

    Example:
        >>> get_product_list("", "client123", "token456")
        {"result": {...}}
     """
    url = "https://api-seller.ozon.ru/v2/product/list"
    headers = {
        "Client-Id": client_id,
        "Api-Key": seller_token,
    }
    payload = {
        "filter": {
            "visibility": "ALL",
        },
        "last_id": last_id,
        "limit": 1000,
    }
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    response_object = response.json()
    return response_object.get("result")


def get_offer_ids(client_id: str, seller_token: str) -> list:
    """Get all offer IDs from the Ozon store.

    Args:
        client_id (str): The client ID for the Ozon API.
        seller_token (str): The API token for the Ozon seller account.

    Returns:
        list: A list of offer IDs as strings.

    Example:
        >>> get_offer_ids("client123", "token456")
        ["offer123", "offer456", ...]
    """
    last_id = ""
    product_list = []
    while True:
        some_prod = get_product_list(last_id, client_id, seller_token)
        product_list.extend(some_prod.get("items"))
        total = some_prod.get("total")
        last_id = some_prod.get("last_id")
        if total == len(product_list):
            break
    offer_ids = []
    for product in product_list:
        offer_ids.append(product.get("offer_id"))
    return offer_ids


def update_price(prices: list, client_id: str, seller_token: str) -> dict:
    """Update product prices in the Ozon store.

    Args:
        prices (list): A list of dictionaries representing information about prices to update.
        client_id (str): The client ID for the Ozon API.
        seller_token (str): The API token for the Ozon seller account.

    Returns:
        dict: The API response containing information about updated prices.

    Raises:
        requests.exceptions.RequestException: If the API request fails.

    Example:
        >>> update_price(
        ...     [{"offer_id": "offer123", "price": "5990", "old_price": "6990", "currency_code": "RUB"}],
        ...     "client123", "token456"
        ... )
        {"result": [{"product_id": 456789, "offer_id": "offer123", "updated": True, "errors": []}]}
    """
    url = "https://api-seller.ozon.ru/v1/product/import/prices"
    headers = {
        "Client-Id": client_id,
        "Api-Key": seller_token,
    }
    payload = {"prices": prices}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def update_stocks(stocks: list, client_id: str, seller_token: str) -> dict:
    """Update product stock levels in the Ozon store.

    Args:
        stocks (list): A list of dictionaries representing stock levels to update.
        client_id (str): The client ID for the Ozon API.
        seller_token (str): The API token for the Ozon seller account.

    Returns:
        dict: A dictionary with the API response.

     Raises:
        requests.exceptions.RequestException: If the API request fails.

    Example:
        >>> update_stocks([{"offer_id": "PG-2404С1", "stock": 4}], "client123", "token456")
        {"result": [{"product_id": 55946, "offer_id": "PG-2404С1", "updated": True, "errors": []}]}
    """
    url = "https://api-seller.ozon.ru/v1/product/import/stocks"
    headers = {
        "Client-Id": client_id,
        "Api-Key": seller_token,
    }
    payload = {"stocks": stocks}
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


def download_stock() -> list:
    """
    Downloads and processes the stock file from the Casio website.

    Downloads a ZIP file containing an Excel sheet with stock data, extracts the file,
    processes the data into a list of dictionaries, and deletes the temporary file.

    Returns:
        list: A list of dictionaries representing stock data.

    Raises:
        requests.exceptions.RequestException: If the file download fails.

    Example:
        >>> download_stock()
        [{"Код": "123", "Количество": ">10", "Название": "Model 1"},
        {"Код": "456", "Количество": "5", "Название": "Model 2"}]
    """
    # Download remnants from the website
    casio_url = "https://timeworld.ru/upload/files/ostatki.zip"
    session = requests.Session()
    response = session.get(casio_url)
    response.raise_for_status()
    with response, zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        archive.extractall(".")
    # Creating a list of watches remnants:
    excel_file = "ostatki.xls"
    watch_remnants = pd.read_excel(
        io=excel_file,
        na_values=None,
        keep_default_na=False,
        header=17,
    ).to_dict(orient="records")
    os.remove("./ostatki.xls")  # Delete file
    return watch_remnants


def create_stocks(watch_remnants: list, offer_ids: list) -> list:
    """
    Generate stock data to update inventory levels in the Ozon store.

    Args:
        watch_remnants (list): A list of dictionaries containing stock data from the Casio file.
        offer_ids (list): A list of product offer IDs from the Ozon store.

    Returns:
        list: A list of dictionaries representing stock levels to update.

    Example:
        >>> watch_remnants = [{"Код": "123", "Количество": ">10"}, {"Код": "456", "Количество": "5"}]
        >>> offer_ids = ["123", "789"]
        >>> create_stocks(watch_remnants, offer_ids)
        [{"offer_id": "123", "stock": 100}, {"offer_id": "789", "stock": 0}]
    """
    stocks = []
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            count = str(watch.get("Количество"))
            if count == ">10":
                stock = 100
            elif count == "1":
                stock = 0
            else:
                stock = int(watch.get("Количество"))
            stocks.append({"offer_id": str(watch.get("Код")), "stock": stock})
            offer_ids.remove(str(watch.get("Код")))
    # Adding what is missing from the uploaded:
    for offer_id in offer_ids:
        stocks.append({"offer_id": offer_id, "stock": 0})
    return stocks


def create_prices(watch_remnants: list, offer_ids: list) -> list:
    """
    Generate price data to update product prices in the Ozon store.

    Args:
        watch_remnants (list): A list of dictionaries containing product data from the Casio file.
        offer_ids (list): A list of product offer IDs from the Ozon store.

    Returns:
        list: A list of dictionaries representing price data to update.

    Example:
        >>> watch_remnants = [{"Код": "123", "Цена": "5990"}, {"Код": "456", "Цена": "7990"}]
        >>> offer_ids = ["123", "789"]
        >>> create_prices(watch_remnants, offer_ids)
        [{"auto_action_enabled": "UNKNOWN", "currency_code": "RUB", "offer_id": "123", "old_price": "0", "price": "5990"}]
    """
    prices = []
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            price = {
                "auto_action_enabled": "UNKNOWN",
                "currency_code": "RUB",
                "offer_id": str(watch.get("Код")),
                "old_price": "0",
                "price": price_conversion(watch.get("Цена")),
            }
            prices.append(price)
    return prices


def price_conversion(price: str) -> str:
    """Convert a price string to a numeric string format.

    This function removes all non-numeric characters from the input price string
    and converts it to a plain number string without any symbols or formatting.

    Args:
        price (str): A string representing a price.
                     Example: "5'990.00 руб."

    Returns:
        str: A numeric string representing the price.
             Example: "5990"

    Examples:
        >>> price_conversion("5'990.00 руб.")
        '5990'
        >>> price_conversion("12.34$")
        '12'
        >>> price_conversion("abc")
        ''
    """
    return re.sub("[^0-9]", "", price.split(".")[0])


def divide(lst: list, n: int):
    """
    Splits a list into chunks of size n.

    Args:
        lst (list): The list to be divided into chunks.
        n (int): The size of each chunk.

    Yields:
        list: A chunk of the input list.

    Example:
        >>> list(divide([1, 2, 3, 4, 5, 6], 2))
        [[1, 2], [3, 4], [5, 6]]
    """
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


async def upload_prices(watch_remnants, client_id, seller_token):
    """
    Uploads the product price updates to the Ozon store.

    Args:
        watch_remnants (list): A list of dictionaries containing the product data.
        client_id (str): The client ID for the Ozon API.
        seller_token (str): The API token for the Ozon seller account.

    Returns:
        list: A list of dictionaries representing the prices updated on the Ozon store.

    Example:
        >>> await upload_prices(watch_remnants, "client123", "token456")
        [{"offer_id": "offer123", "price": "5990", ...}]
    """
    offer_ids = get_offer_ids(client_id, seller_token)
    prices = create_prices(watch_remnants, offer_ids)
    for some_price in list(divide(prices, 1000)):
        update_price(some_price, client_id, seller_token)
    return prices


async def upload_stocks(watch_remnants, client_id, seller_token):
    """
    Uploads the product stock updates to the Ozon store.

    Args:
        watch_remnants (list): A list of dictionaries containing the stock data.
        client_id (str): The client ID for the Ozon API.
        seller_token (str): The API token for the Ozon seller account.

    Returns:
        tuple: A tuple containing:
            - A list of dictionaries representing stocks with non-zero stock values.
            - The original list of stock updates.

    Example:
        >>> await upload_stocks(watch_remnants, "client123", "token456")
        ([{"offer_id": "offer123", "stock": 10}], [{"offer_id": "offer123", "stock": 10}])
    """
    offer_ids = get_offer_ids(client_id, seller_token)
    stocks = create_stocks(watch_remnants, offer_ids)
    for some_stock in list(divide(stocks, 100)):
        update_stocks(some_stock, client_id, seller_token)
    not_empty = list(filter(lambda stock: (stock.get("stock") != 0), stocks))
    return not_empty, stocks


def main():
    """Main function to update product stocks and prices on Ozon.

    This function fetches product offer IDs, downloads stock data,
    and updates both stocks and prices on Ozon.

    Returns:
        None
    """
    env = Env()
    seller_token = env.str("SELLER_TOKEN")
    client_id = env.str("CLIENT_ID")
    try:
        offer_ids = get_offer_ids(client_id, seller_token)
        watch_remnants = download_stock()
        # Update remnants
        stocks = create_stocks(watch_remnants, offer_ids)
        for some_stock in list(divide(stocks, 100)):
            update_stocks(some_stock, client_id, seller_token)
        # Change prices
        prices = create_prices(watch_remnants, offer_ids)
        for some_price in list(divide(prices, 900)):
            update_price(some_price, client_id, seller_token)
    except requests.exceptions.ReadTimeout:
        print("Превышено время ожидания...")
    except requests.exceptions.ConnectionError as error:
        print(error, "Ошибка соединения")
    except Exception as error:
        print(error, "ERROR_2")


if __name__ == "__main__":
    main()
