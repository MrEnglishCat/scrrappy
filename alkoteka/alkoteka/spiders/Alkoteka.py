import json
from datetime import datetime, UTC

from scrapy import Spider, Request, http
from fake_useragent import UserAgent

# from alkoteka.alkoteka.items import AlkotekaItem
from alkoteka.items import AlkotekaItem


# uuid city_uuid=4a70f9e0-46ae-11e7-83ff-00155d026416 - Краснодар


# TODO не забыть про бесплатные прокси

def get_random_headers() -> dict:
    """
    Используется для получения динамического header в части user-agent
    :return:
    """
    user_agent = UserAgent().random

    return {
        'Accept': '*/*',
        'User-Agent': user_agent,
        'Content-Type': 'application/json',
        'Accept-Language': 'ru,en-US;q=0.9,en;q=0.8,ky;q=0.7',
    }


class Alkoteka(Spider):
    name = 'alkoteka'
    starts_url = (
        'https://alkoteka.com/catalog/vino',
        'https://alkoteka.com/catalog/krepkiy-alkogol',
        'https://alkoteka.com/catalog/slaboalkogolnye-napitki-2',

    )

    allowed_domains = ["alkoteka.com"]

    # ALKOTEKA_API_CATALOG = 'https://alkoteka.com/web-api/v1/product?city_uuid=4a70f9e0-46ae-11e7-83ff-00155d026416&page={page}&per_page=20&root_category_slug={root_category_slug}'
    ALKOTEKA_API_CATALOG = 'https://alkoteka.com/web-api/v1/product?city_uuid=4a70f9e0-46ae-11e7-83ff-00155d026416&page={page}&per_page={per_page}&root_category_slug={root_category_slug}'
    """
    в meta "has_more_pages": false, - можно определить  последняя ли это страница
    """

    ALKOTEKA_API_CITY_SEARCH = 'https://alkoteka.com/web-api/v1/city?city_uuid=4a70f9e0-46ae-11e7-83ff-00155d026416&search={city_name}'
    """
    API для поиска города, передается в параметр search
    """

    ALKOTEKA_API_ALL_CITY = 'https://alkoteka.com/web-api/v1/city?city_uuid=4a70f9e0-46ae-11e7-83ff-00155d026416&page={page}'  # всего 3 страницы, 59 городов
    """
    Можно получить все доступные города, ответ по страницам. 
    """

    ALKOTEKA_API_ITEM_URL = 'https://alkoteka.com/web-api/v1/product/{item_slug}?city_uuid=4a70f9e0-46ae-11e7-83ff-00155d026416'

    ROOT_CATEGORY_SLUGS = (
        'vino',
        # 'slaboalkogolnye-napitki-2',
        # 'bezalkogolnye-napitki-1'
    )
    """
    Картеж категорий по слагам для сбора данных
    """

    city_uuid = '4a70f9e0-46ae-11e7-83ff-00155d026416'

    @staticmethod
    def _get_title(name: str, description_blocks: list):

        for block in description_blocks:
            match block.get("code"):
                case "cvet":
                    name += " " + ' '.join(
                        filter(
                            lambda name_: name_ not in name,
                            map(
                                lambda value: value.get("name"),
                                block.get("values")
                            )
                        )
                    )
                case "krepost" | "ves":
                    name += " " + f"{block.get("max")} {block.get('unit')}"


        return name

    @staticmethod
    def _get_marketing_tags(marketing_tags: list)->list|None:
        if not marketing_tags:
            return
        return tuple(map(lambda tag: tag.get("title"), marketing_tags))


    @staticmethod
    def _get_brand(description_blocks: list) -> str:
        if not description_blocks:
            return ""

        for item in description_blocks:
            if item.get('code') == "brend":
                return ' '.join(
                    map(
                        lambda value: value.get("name", ""),
                        item.get("values", tuple())

                    )
                )

    @staticmethod
    def _get_sale_tag(price, prev_price=None) -> str:

        if not prev_price:
            return ""
        price = float(price)
        prev_price = float(prev_price)
        discount_persent = 100 - price * 100 / prev_price
        return f"Скидка {discount_persent}%"

        # price - х% - соскидкой
        # prev_price - 100%  - без скидки

    @staticmethod
    def _get_count_item(stores: list | int) -> int:

        if not stores:
            return stores

        return sum(
            map(
                lambda store: int(store.get("quantity").split()[0]),
                stores
            )
        )

    @staticmethod
    def _get_description(text_blocks: list) -> str:

        if not text_blocks:
            return ""

        return ' '.join(
            map(
                lambda block: f"{block.get("title", "")}\n{block.get("content", "")}",
                text_blocks
            )
        )

    @staticmethod
    def _get_all_characteristics(description_blocks: list) -> dict:
        if not description_blocks:
            return {}

        result = {}
        for block in description_blocks:
            title = block.get("title")
            if (values := block.get("values")):
                result.setdefault(
                    title,
                    ' '.join(
                        map(
                            lambda value: value.get("name"),
                            block.get("values", {})
                        )
                    )
                )
            else:
                result.setdefault(
                    title,
                    f"{block.get("max")} {block.get("unit")}"
                )

        return result

    def start_requests(self):
        for slug in type(self).ROOT_CATEGORY_SLUGS:
            # for page in range(1, 10):
            for page in range(1, 2):
                url = type(self).ALKOTEKA_API_CATALOG.format(
                    page=page,
                    per_page=200,
                    root_category_slug=slug
                )
                payload = {
                    'city_uuid': type(self).city_uuid,
                    'page': page,
                    'root_category_slug': slug,
                    'per_page': 200,
                }
                yield Request(
                    url=url,
                    headers=get_random_headers(),
                    body=json.dumps(payload),
                    callback=self.parse,
                    meta={
                        'page': page,
                        'root_category_slug': slug,
                    }

                )

    def parse(self, response: http.JsonResponse) -> dict:
        """Обработка JSON-ответа"""
        try:
            data = response.json()
            item_slugs_for_api = []

            # with open(f"{response.meta['root_category_slug']}.json", 'w', encoding='utf-8') as f:
            #     json.dump(data, f, ensure_ascii=False, indent=4)

            for item in data.get('results', []):
                if (item_slug := item.get("slug")):
                    url = type(self).ALKOTEKA_API_ITEM_URL.format(item_slug=item_slug)
                    payload = {
                        'city_uuid': type(self).city_uuid,
                    }
                    yield Request(
                        url=url,
                        headers=get_random_headers(),
                        body=json.dumps(payload),
                        callback=self.parse_items,
                        meta={
                            'item_slug': item_slug,
                            'product_url': item.get("product_url"),
                        }

                    )

                break


        except Exception as e:
            self.logger.error(f"Failed to parse JSON on {response.url}: {e}")
            return

    def parse_items(self, response: http.JsonResponse) -> dict:
        try:
            data_response = response.json()
            if (data := data_response.get('results')):
                alkoteka_item = AlkotekaItem()
                alkoteka_item["timestamp"] = int(datetime.now(UTC).timestamp())
                alkoteka_item["RPC"] = data.get("uuid")
                alkoteka_item["url"] = response.meta.get("product_url")
                alkoteka_item["title"] = type(self)._get_title(name=data.get("name"),
                                                               description_blocks=data.get("description_blocks"))
                alkoteka_item["marketing_tags"] = type(self)._get_marketing_tags(data.get("filter_labels"))
                alkoteka_item["brand"] = type(self)._get_brand(data.get("description_blocks"))
                alkoteka_item["price_data"] = {
                    "current": prev_price if (prev_price := data.get("prev_price")) else data.get("price"),
                    "original": data.get("price"),
                    "sale_gate": type(self)._get_sale_tag(data.get("price"), data.get("prev_price"))
                }
                alkoteka_item["stock"] = {
                    "in_stock": data.get("available", False),
                    "count": type(self)._get_count_item(data.get("availability", {}).get("stores", 0))
                }

                alkoteka_item["metadata"] = {
                    "__description": type(self)._get_description(data.get("text_blocks")),
                    "Артикул": data.get("vendor_code"),
                    **type(self)._get_all_characteristics(data.get("description_blocks"))
                }

                yield alkoteka_item



        except Exception as e:
            self.logger.error(f"Failed to parse JSON on {response.url}: {e}")
            return


if __name__ == '__main__':
    alkoteka = Alkoteka()
