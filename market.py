import datetime
import logging.config
from environs import Env
from seller import download_stock

import requests

from seller import divide, price_conversion

logger = logging.getLogger(__file__)


def get_product_list(page, campaign_id, access_token):
    """
        Retrieves a list of products from the specified page of a Yandex.Market.

        This function sends a GET request to the Yandex.Market API to fetch a list of
        products associated with the specified campaign.

        Args:
            page (str): The page token to fetch data from. Use an empty string for the first page.
            campaign_id (str): The unique identifier of the Yandex.Market.
            access_token (str): The access token for API authentication.

        Returns:
            dict: A result containing the list of products and additional pagination information.

        Raises:
            requests.exceptions.RequestException: If the API request fails due to an HTTP error, connection issue, or timeout.

        Example:
            >>> get_product_list("", "123456", "valid_token")
                {'paging': {'nextPageToken': 'token2'}, 'offerMappingEntries': [...]}
        """
    endpoint_url = "https://api.partner.market.yandex.ru/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Host": "api.partner.market.yandex.ru",
    }
    payload = {
        "page_token": page,
        "limit": 200,
    }
    url = endpoint_url + f"campaigns/{campaign_id}/offer-mapping-entries"
    response = requests.get(url, headers=headers, params=payload)
    response.raise_for_status()
    response_object = response.json()
    return response_object.get("result")


def update_stocks(stocks, campaign_id, access_token):
    """
    Updates product stock levels in a Yandex.Market campaign.

    Sends a PUT request to the Yandex.Market API to update stock information for up to 2000 products.

    Args:
        stocks (list): A list of dictionaries with stock details, including SKU, warehouse ID, and stock count.
        campaign_id (str): The ID of the Yandex.Market campaign.
        access_token (str): The access token for API authentication.

    Returns:
        dict: The API response with a "status" field ("OK" for success, "ERROR" for failure).

    Raises:
        requests.exceptions.RequestException: If the API request fails due to an HTTP error, connection issue, or timeout.

    Example:
        >>> update_stocks(stocks, "123456", "valid_token")
        {'status': 'OK'}
    """
    endpoint_url = "https://api.partner.market.yandex.ru/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Host": "api.partner.market.yandex.ru",
    }
    payload = {"skus": stocks}
    url = endpoint_url + f"campaigns/{campaign_id}/offers/stocks"
    response = requests.put(url, headers=headers, json=payload)
    response.raise_for_status()
    response_object = response.json()
    return response_object


def update_price(prices, campaign_id, access_token):
    """
    Updates product prices in a Yandex.Market campaign.

    Sends a POST request to the Yandex.Market API to update prices for up to 2000 products.

    Args:
        prices (list): A list of dictionaries with price details, including SKU, price value, currency, and VAT.
        campaign_id (str): The ID of the Yandex.Market campaign.
        access_token (str): The access token for API authentication.

    Returns:
        dict: The API response with a "status" field ("OK" for success, "ERROR" for failure).

    Raises:
        requests.exceptions.RequestException: If the API request fails due to an HTTP error, connection issue, or timeout.

    Example:
        >>> update_price(prices, "123456", "valid_token")
        {'status': 'OK'}
    """
    endpoint_url = "https://api.partner.market.yandex.ru/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
        "Host": "api.partner.market.yandex.ru",
    }
    payload = {"offers": prices}
    url = endpoint_url + f"campaigns/{campaign_id}/offer-prices/updates"
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    response_object = response.json()
    return response_object


def get_offer_ids(campaign_id, market_token):
    """
        Retrieves product SKUs (offer IDs) from a Yandex.Market campaign.

        Makes multiple requests to the Yandex.Market API to fetch all offer SKUs associated with the campaign.

        Args:
            campaign_id (str): The ID of the Yandex.Market campaign.
            market_token (str): The access token for API authentication.

        Returns:
            list: A list of SKUs (offer IDs) for the products in the specified campaign.

        Example:
            >>> get_offer_ids("123456", "valid_token")
            ["sku1", "sku2", "sku3"]
        """
    page = ""
    product_list = []
    while True:
        some_prod = get_product_list(page, campaign_id, market_token)
        product_list.extend(some_prod.get("offerMappingEntries"))
        page = some_prod.get("paging").get("nextPageToken")
        if not page:
            break
    offer_ids = []
    for product in product_list:
        offer_ids.append(product.get("offer").get("shopSku"))
    return offer_ids


def create_stocks(watch_remnants, offer_ids, warehouse_id):
    """
        Generates stock data for offers based on remnants and warehouse information.

        Args:
            watch_remnants (list): List of products with "Код" (SKU) and "Количество" (stock).
            offer_ids (list): List of SKUs to update.
            warehouse_id (int): Warehouse ID.

        Returns:
            list: Stock data formatted for the Yandex.Market API.

        Example:
            >>> watch_remnants = [{"Код": "sku1", "Количество": ">10"}]
            >>> offer_ids = ["sku1", "sku2"]
            >>> create_stocks(watch_remnants, offer_ids, 12345)
            [
                {"sku": "sku1", "warehouseId": 12345, "items": [{"count": 100, "type": "FIT", "updatedAt": "2025-01-18T00:00:00Z"}]},
                {"sku": "sku2", "warehouseId": 12345, "items": [{"count": 0, "type": "FIT", "updatedAt": "2025-01-18T00:00:00Z"}]}
            ]
        """
    stocks = list()
    date = str(datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z")
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            count = str(watch.get("Количество"))
            if count == ">10":
                stock = 100
            elif count == "1":
                stock = 0
            else:
                stock = int(watch.get("Количество"))
            stocks.append(
                {
                    "sku": str(watch.get("Код")),
                    "warehouseId": warehouse_id,
                    "items": [
                        {
                            "count": stock,
                            "type": "FIT",
                            "updatedAt": date,
                        }
                    ],
                }
            )
            offer_ids.remove(str(watch.get("Код")))
    # Adding the missing from the uploaded:
    for offer_id in offer_ids:
        stocks.append(
            {
                "sku": offer_id,
                "warehouseId": warehouse_id,
                "items": [
                    {
                        "count": 0,
                        "type": "FIT",
                        "updatedAt": date,
                    }
                ],
            }
        )
    return stocks


def create_prices(watch_remnants, offer_ids):
    """
        Generates price data for offers based on remnants.

        Args:
            watch_remnants (list): List of products with "Код" (SKU) and "Цена".
            offer_ids (list): List of SKUs to update.

        Returns:
            list: Price data formatted for the Yandex.Market API.

        Example:
            >>> watch_remnants = [{"Код": "sku1", "Цена": "1000"}]
            >>> offer_ids = ["sku1", "sku2"]
            >>> create_prices(watch_remnants, offer_ids)
            [
                {
                    "id": "sku1",
                    "price": {
                        "value": 1000,
                        "currencyId": "RUR"
                    }
                }
            ]
        """
    prices = []
    for watch in watch_remnants:
        if str(watch.get("Код")) in offer_ids:
            price = {
                "id": str(watch.get("Код")),
                # "feed": {"id": 0},
                "price": {
                    "value": int(price_conversion(watch.get("Цена"))),
                    # "discountBase": 0,
                    "currencyId": "RUR",
                    # "vat": 0,
                },
                # "marketSku": 0,
                # "shopSku": "string",
            }
            prices.append(price)
    return prices


async def upload_prices(watch_remnants, campaign_id, market_token):
    """
        Uploads price data to Yandex.Market for the specified campaign.

        Args:
            watch_remnants (list): List of products with "Код" (SKU) and "Цена".
            campaign_id (int): ID of the Yandex.Market campaign.
            market_token (str): Access token for Yandex.Market API.

        Returns:
            list: All price data successfully prepared and uploaded.

        Example:
            >>> await upload_prices(watch_remnants, 12345, "your_market_token")
        """
    offer_ids = get_offer_ids(campaign_id, market_token)
    prices = create_prices(watch_remnants, offer_ids)
    for some_prices in list(divide(prices, 500)):
        update_price(some_prices, campaign_id, market_token)
    return prices


async def upload_stocks(watch_remnants, campaign_id, market_token, warehouse_id):
    """
        Uploads stock data to Yandex.Market for the specified campaign and warehouse.

        Args:
            watch_remnants (list): List of products with "Код" (SKU) and "Количество".
            campaign_id (int): ID of the Yandex.Market campaign.
            market_token (str): Access token for Yandex.Market API.
            warehouse_id (int): ID of the warehouse for stock updates.

        Returns:
            tuple:
                - list: Stock data with non-zero counts that were uploaded.
                - list: All stock data prepared and uploaded.

        Example:
            >>> await upload_stocks(watch_remnants, 12345, "your_market_token", 6789)
        """
    offer_ids = get_offer_ids(campaign_id, market_token)
    stocks = create_stocks(watch_remnants, offer_ids, warehouse_id)
    for some_stock in list(divide(stocks, 2000)):
        update_stocks(some_stock, campaign_id, market_token)
    not_empty = list(
        filter(lambda stock: (stock.get("items")[0].get("count") != 0), stocks)
    )
    return not_empty, stocks


def main():
    """
        Main function to synchronize stock and price data with the Yandex Market API.

        Exceptions:
            requests.exceptions.ReadTimeout: Raised if an API request times out.
            requests.exceptions.ConnectionError: Raised if there is a connection error to the API.
            Exception: Logs any other unexpected error during execution.

        Returns:
            None
        """
    env = Env()
    market_token = env.str("MARKET_TOKEN")
    campaign_fbs_id = env.str("FBS_ID")
    campaign_dbs_id = env.str("DBS_ID")
    warehouse_fbs_id = env.str("WAREHOUSE_FBS_ID")
    warehouse_dbs_id = env.str("WAREHOUSE_DBS_ID")

    watch_remnants = download_stock()
    try:
        # FBS
        offer_ids = get_offer_ids(campaign_fbs_id, market_token)
        # Update the remaining FBS
        stocks = create_stocks(watch_remnants, offer_ids, warehouse_fbs_id)
        for some_stock in list(divide(stocks, 2000)):
            update_stocks(some_stock, campaign_fbs_id, market_token)
        # Change FBS prices
        upload_prices(watch_remnants, campaign_fbs_id, market_token)

        # DBS
        offer_ids = get_offer_ids(campaign_dbs_id, market_token)
        # # Update the remaining DBS
        stocks = create_stocks(watch_remnants, offer_ids, warehouse_dbs_id)
        for some_stock in list(divide(stocks, 2000)):
            update_stocks(some_stock, campaign_dbs_id, market_token)
        # Change DBS prices
        upload_prices(watch_remnants, campaign_dbs_id, market_token)
    except requests.exceptions.ReadTimeout:
        print("Превышено время ожидания...")
    except requests.exceptions.ConnectionError as error:
        print(error, "Ошибка соединения")
    except Exception as error:
        print(error, "ERROR_2")


if __name__ == "__main__":
    main()
