import json
import math
import pickle
from operator import itemgetter
from re import search

import requests


def append_orders(otext, d):
    orders = json.loads(otext)["orders"]
    for i in orders:
        if "customer" in i:
            key = "{} - {}".format(i["order_number"], i["customer"]["default_address"]["company"])
            d[key] = i["id"]
        else:
            print("Wonky order: " + str(i))


def get_next_url(headers):
    link = headers["Link"]
    lsplit = link.split(",")
    links = list(filter(lambda l: "next" in l, lsplit))
    if links != []:
        link = links[0]

        url = search("<.*>", link)
        if url:
            cur_url = url[0][1:-1]
            cur_url = cur_url.replace("%2C", ",")
            url_start = len("https://southern-exposure-seed-exchange-wholesale.myshopify.com/admin/")
            return cur_url[url_start - 1:]
    else:
        return ""


class ShopifyConnector:

    def __init__(self, start_date, end_date, debug_orders=[]):
        self.SEASON_START_DATE = start_date
        self.SEASON_END_DATE = end_date
        self.SHOP_NAME = "southern-exposure-seed-exchange-wholesale"
        self.API_KEY = "bf8716619bdd3fd8ac76192f5d16743a"
        self.PASSWORD = "658887daedbca57500aae07056816039"
        self.API_URL = "https://{}.myshopify.com/admin/".format(self.SHOP_NAME)
        self.debug_orders = debug_orders

    def do_request(self, rest_string):
        return requests.get(self.API_URL + rest_string, auth=(self.API_KEY, self.PASSWORD))

    def get_orders_list(self):
        if self.debug_orders != []:
            return self.debug_orders
        # get all open (and ready-to-ship?) orders

        # Shopify updated the way this API works Jan 2020; you can't specify a limit now
        # If theres more results not included in the first response, there will be a 
        # Link embedded in the response.  See https://help.shopify.com/en/api/guides/paginated-rest-results
        # response = self.do_request("/api/2020-01/orders.json?limit=250&fields=id,customer,order_number")
        responses = []
        cur_url = "/api/2020-01/orders.json?limit=10&created_at_min=%sT16:15:47-04:00&created_at_max=%s" % (
            self.SEASON_START_DATE, self.SEASON_END_DATE)
        n = 0
        while (True):
            n += 1
            print("Loading order data, page %d" % n)
            response = self.do_request(cur_url)

            try:
                orders = json.loads(response.text)
            except:
                break

            responses.append(response)
            if "Link" in response.headers:
                cur_url = get_next_url(response.headers)
                if cur_url == "":
                    break
            else:
                break

        results = {}
        for r in responses:
            append_orders(r.text, results)

        pf = open("last_results.pickle", "wb")
        pickle.dump(results, pf)
        pf.close()
        return results

    def process_products_list(self, products, new_cards):
        # cards are: list of (item["title"], item["product_id"], item["variant_id"])
        # products are: list of {id, variant}
        # create products dict for easier lookup
        barcode_lookup = {}
        for product in products:
            barcode_lookup.setdefault(product["id"], {})
            for variant in product["variants"]:
                barcode_lookup[product["id"]].setdefault(variant["id"], variant["barcode"])
        results = []
        cards = sorted(new_cards, key=itemgetter(0))
        for card in cards:
            try:
                catnum, name = card[0].split(" - ", maxsplit=1)
                results.append((name, catnum, barcode_lookup[card[1]][card[2]]))
            except ValueError:
                title = card[0]
                results.append((title, title, barcode_lookup[card[1]][card[2]]))
            except KeyError:
                continue
        return results

    def get_all_products_old(self):
        results = None

        resp_count = self.do_request('products/count.json')
        if resp_count.ok:
            pages = math.ceil(json.loads(resp_count.text)["count"] / 250)
            cards = set()
            products = []
            curr_page = 1
            while curr_page <= pages:
                resp_get_prods = self.do_request(
                    "products.json?limit=250&page={}&fields=id,title,variants".format(curr_page))
                if resp_get_prods.ok:
                    curr_prods = json.loads(resp_get_prods.text)["products"]
                    for prod in curr_prods:
                        if prod["variants"] is not None and len(prod["variants"]) > 0:
                            cards.add((prod["title"], prod["id"], prod["variants"][0]["id"]))
                            products.append({"id": prod["id"], "variants": prod["variants"]})
                    curr_page += 1
                else:
                    print("get all products error")
                    print(resp_get_prods.text)
                    break
            results = self.process_products_list(products, cards)

        return results

    def get_all_products(self):
        results = None

        products = []
        cards = set()

        cur_url = "products.json?limit=250&fields=id,title,variants"
        n = 0
        while (True):
            n += 1
            print("Loading products data, page %d" % n)
            response = self.do_request(cur_url)

            if response.ok:
                curr_prods = json.loads(response.text)["products"]
                for prod in curr_prods:
                    if prod["variants"] is not None and len(prod["variants"]) > 0:
                        cards.add((prod["title"], prod["id"], prod["variants"][0]["id"]))
                        products.append({"id": prod["id"], "variants": prod["variants"]})
                    else:
                        break

            if "Link" in response.headers:
                cur_url = get_next_url(response.headers)
                if cur_url == "":
                    break
            else:
                break

        results = self.process_products_list(products, cards)
        return results

    def get_cards_needed_list(self, order_id):
        results = None
        new_cards = None
        current_products = set()
        past_products = set()

        resp_curr_order = self.do_request(
            "orders/{}.json?limit=250&fields=id,customer,order_number,line_items,created_at".format(order_id))
        if resp_curr_order.ok:
            # get order
            current_order = json.loads(resp_curr_order.text)["order"]
            for item in current_order["line_items"]:
                current_products.add((item["title"], item["product_id"], item["variant_id"]))
            # get customer from order
            customer_id = current_order["customer"]["id"]
            # use customer_id to get all customer's orders since season start until current order
            since = "created_at_min={}T00:00:00-00:00".format(self.SEASON_START_DATE)
            until = "created_at_max={}".format(current_order["created_at"])
            req_str = "orders.json?customer_id={}&{}&{}&limit=250&fields=id,customer,order_number,line_items,created_at".format(
                customer_id, since, until)
            resp_all_orders = self.do_request(req_str)
            if resp_all_orders.ok:
                # build list of current order prods and past order prods
                past_orders = json.loads(resp_all_orders.text)["orders"]
                for order in past_orders:
                    if order["order_number"] == current_order["order_number"]:
                        continue
                    for item in order["line_items"]:
                        past_products.add((item["title"], item["product_id"], item["variant_id"]))
                # get list of what is in current order and not in past orders
                get_id = lambda e: e[0].split(" ")[0]
                new_cards = current_products - past_products
        if new_cards:
            ids = [str(x[1]) for x in new_cards]
            resp_barcodes = self.do_request("products.json?ids={}&limit=250&fields=id,variants".format(",".join(ids)))
            if resp_barcodes.ok:
                products = json.loads(resp_barcodes.text)["products"]
                results = self.process_products_list(products, new_cards)
            else:
                print(resp_barcodes.status_code)
        return results
