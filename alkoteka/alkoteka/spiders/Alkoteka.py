import json
from datetime import datetime, UTC
from random import choice

import requests
from scrapy import Spider, Request, http
from fake_useragent import UserAgent
from urllib.parse import urlparse, urlsplit
from alkoteka.items import AlkotekaItem
from typing_extensions import deprecated


# uuid city_uuid=4a70f9e0-46ae-11e7-83ff-00155d026416 - Краснодар

# https://alkoteka.com/catalog/slaboalkogolnye-napitki-2
# https://alkoteka.com/web-api/v1/product?city_uuid=4a70f9e0-46ae-11e7-83ff-00155d026416&page=1&per_page=20&root_category_slug=slaboalkogolnye-napitki-2
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
    BASE_URL = 'https://alkoteka.com'
    STARTS_URL = (
        'https://alkoteka.com/catalog/vino',
        'https://alkoteka.com/catalog/krepkiy-alkogol',
        'https://alkoteka.com/catalog/slaboalkogolnye-napitki-2',

    )

    ROOT_CATEGORY_SLUGS = [
        # 'vino',
        # 'slaboalkogolnye-napitki-2',
        # 'bezalkogolnye-napitki-1'
    ]
    """
    Картеж категорий по слагам для сбора данных передается в API, 
    формируется из ссылок STARTS_URL при запуске паука.
    """

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
    """
    API для получения данных об определенном товаре
    """

    PROXY_FILEPATH = "proxy_pool.json"

    city_uuid = '4a70f9e0-46ae-11e7-83ff-00155d026416'
    """
    идентификатор Краснодара для API       
    """



    def __init__(self, from_file=False, file_path=None, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        # TODO доделать возможность загрузки урлов при старте парсера
        # if from_file:
        #     with open(file_path, 'r', encoding='utf-8') as f:
        #         print(f.readlines())
        #         # type(self).STARTS_URL = list(map(str.strip(f.readlines()))

        self.proxy_pool = type(self)._get_proxies()


    @classmethod
    def _get_proxies(cls):
        """
        Получение списка IP прокси по урлу.
        :return:
        """

        with open(cls.PROXY_FILEPATH) as f:
            proxies = json.load(f)

            return proxies


    @classmethod
    def _parse_input_url(cls, urls: list | tuple) -> list:
        """
        Для получения из списка урл STARTS_URL со слагами
        :param urls: список входных url
        :return: список слагов
        """
        return list(
            map(
                lambda url: cls._get_slug(url),
                urls
            )
        )

    @staticmethod
    def _get_slug(url: str) -> str:
        """
         заточен на определенный формат ссылки https://alkoteka.com/catalog/vino
            - первая часть https://alkoteka.com/catalog/
            - обязательно наличие слага, пример /vino
        :param url:
        :return: slug который нужен для подстановки в API
        """
        path = urlparse(url).path.rsplit('/', 1)

        return path[-1]

    @staticmethod
    def _get_title(name: str, description_blocks: list):
        """
        Для получения полного заголовка с учетом цвета
        :param name:
        :param description_blocks:
        :return:
        """

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
    def _get_marketing_tags(marketing_tags: list) -> list | None:
        """
        Получение маркетинговых тэгов
        :param marketing_tags:
        :return:
        """
        if not marketing_tags:
            return
        return tuple(map(lambda tag: tag.get("title"), marketing_tags))

    @staticmethod
    def _get_brand(description_blocks: list) -> str:
        """
        Получение информации о брендах
        :param description_blocks:
        :return:
        """
        if not description_blocks:
            return ""

        for item in description_blocks:
            if item.get('code') == "brend":
                return ' '.join(
                    map(
                        lambda value: str(_a) if (_a := value.get("name", "")) and isinstance(_a, int | float) else _a,
                        item.get("values", tuple())

                    )
                )

    @staticmethod
    def _get_section(category: dict) -> list:
        """
        Рекурсивно собирает все 'name' от корневой категории до текущей.
        Порядок: от верхнего уровня к нижнему (например: ['Вино', 'Вино тихое'])
        :param category:
        :return:
        """
        names = []

        def get_name_recursive(cat):
            if not cat:
                return

            parent = cat.get("parent")

            if parent:
                get_name_recursive(parent)
            name = cat.get("name")
            if name:
                names.append(name)

        get_name_recursive(category)
        return names

    # TODO пересмотреть метод по подсчету variants ERRORS
    @staticmethod
    def _get_variants_count(filters: list) -> int:
        """
         Считает количество вариантов товара по признакам:
        - цвет (code == 'cvet')
        - объём/масса (code == 'obem' или 'massa')

        Если таких фильтров нет — возвращает 1.
        Если есть несколько — перемножает количество значений.
        :param filters:
        :return:
        """
        import math
        print("="*10)
        print("="*10)
        print(int(datetime.now(UTC).timestamp()))
        print("="*10)
        print(filters)
        print("=" * 10)
        VARIANT_CODES = {'cvet', 'obem', 'massa'}

        total_variants = 1
        for filter_item in filters:
            code = filter_item.get("code")
            if code not in VARIANT_CODES:
                continue

            if filter_item.get("type") == "select":  # на тот случай, если где-то объем указан списком значений
                values = filter_item.get("values", [])
                count = len([v for v in values if v.get("enabled", False)])
                if count > 0:
                    total_variants *= count

            elif filter_item.get("type") == "range":

                min_val = filter_item.get("min")
                max_val = filter_item.get("max")
                if min_val is not None and max_val is not None:
                    if math.isclose(min_val, max_val, abs_tol=1e-9):
                        count = 1
                    else:
                        count = 1
                    total_variants *= count

        return total_variants if total_variants >= 1 else 1

    @staticmethod
    def _get_sale_tag(price, prev_price=None) -> str:
        """
        Подсчет процента скидки
        :param price: обычная цена если не указано prev_price, цена со скидкой еслил указана prev_price
        :param prev_price: обычная цена если есть скидка.
        :return:
        """
        if not prev_price:
            return ""
        price = float(price)
        prev_price = float(prev_price)
        discount_persent = 100 - price * 100 / prev_price
        return f"Скидка {discount_persent}%"

    @deprecated("Метод не используется. Вместо него используется получение общего количества товаров через JSON ответа.")
    @staticmethod
    def _get_count_item(stores: list | int) -> int:
        """
        Используется для получения общего количества товаров
        через весь список магазинов
        :param stores:
        :return:
        """
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
        """
        Получение общего описания после совмещения всех текстовых блоков
        :param text_blocks:
        :return:
        """

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
        """
        Получение всех характеристик товара
        :param description_blocks:
        :return:
        """
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
                            values
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

        if type(self).STARTS_URL:
            type(self).ROOT_CATEGORY_SLUGS.extend(
                type(self)._parse_input_url(type(self).STARTS_URL)
            )

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
                        # 'proxy': choice(self.proxy_pool)
                    }

                )

    def parse(self, response: http.JsonResponse) -> dict:
        """Обработка JSON-ответа общая"""
        try:
            data = response.json()

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
                            # 'proxy': choice(self.proxy_pool)
                        }

                    )

                # break


        except Exception as e:
            self.logger.error(f"Failed to parse JSON on {response.url}: {e}")
            return

    def parse_items(self, response: http.JsonResponse) -> dict:
        """
        Обработка ответа на запрос по определенной позиции
        :param response:
        :return:
        """
        try:
            data_response = response.json()
            # self.logger.debug(f"Response from {response.meta.get("product_url")}")
            if (data := data_response.get('results')):
                alkoteka_item = AlkotekaItem()
                alkoteka_item["timestamp"] = int(datetime.now(UTC).timestamp())
                alkoteka_item["RPC"] = data.get("uuid")
                alkoteka_item["url"] = response.meta.get("product_url")
                alkoteka_item["title"] = type(self)._get_title(name=data.get("name"),
                                                               description_blocks=data.get("description_blocks"))
                alkoteka_item["marketing_tags"] = type(self)._get_marketing_tags(data.get("filter_labels"))
                alkoteka_item["brand"] = type(self)._get_brand(data.get("description_blocks"))
                alkoteka_item["section"] = type(self)._get_section(data.get("category"))
                alkoteka_item["price_data"] = {
                    "current": prev_price if (prev_price := data.get("prev_price")) else data.get("price"),
                    "original": data.get("price"),
                    "sale_gate": type(self)._get_sale_tag(data.get("price"), data.get("prev_price"))
                }
                alkoteka_item["stock"] = {
                    "in_stock": data.get("available", False),
                    # "count": type(self)._get_count_item(data.get("availability", {}).get("stores", 0)) # Подсчет через список магазинов
                    "count": data.get("quantity_total", 0),
                }

                alkoteka_item["metadata"] = {
                    "__description": type(self)._get_description(data.get("text_blocks")),
                    "Артикул": data.get("vendor_code"),
                    **type(self)._get_all_characteristics(data.get("description_blocks"))
                }
                alkoteka_item["variants"] = type(self)._get_variants_count(data.get("description_blocks"))
                self.logger.info(f"{alkoteka_item}")
                yield alkoteka_item



        except Exception as e:
            self.logger.error(f"[ PARSE_ITEMS ] Failed to parse JSON on {response.url}: {e.args}")
            self.logger.error(f"[ PARSE_ITEMS ] {'='*20}")
            self.logger.error(f"[ PARSE_ITEMS ] {data.get('description_blocks') }")
            self.logger.error(f"[ PARSE_ITEMS ] {'=' * 20}")
            return


if __name__ == '__main__':
    alkoteka = Alkoteka()
