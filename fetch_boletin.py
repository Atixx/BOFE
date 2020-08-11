import argparse
import urllib.parse
from bs4 import BeautifulSoup
from requests import request, utils
from collections import namedtuple
from json import dumps
from datetime import date

BASE_URL = 'https://www.boletinoficial.gob.ar'

class BoletinFetcher:
    def __init__(self, search_string, input_date):
        input_date = input_date or date.today().isoformat()
        search_string = search_string or "Policia Seguridad Aeroportuaria"
        self.search_string = search_string.replace(' ', '+')
        self.date_from = date.fromisoformat(input_date)
        self.date_until = date.fromisoformat(input_date)
        self.url = 'https://www.boletinoficial.gob.ar/busquedaAvanzada/realizarBusqueda'

    Response = namedtuple('Response', ['code', 'html', 'count'])

    headers = {
        **utils.default_headers(),
        **{
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
        }
    }

    def format_date(self, date: date):
        return date.strftime('%d/%m/%Y')

    def format_searchstring(self):
        return self.search_string

    def payload(self):
        obj = {
            "busquedaRubro": False,
            "hayMasResultadosBusqueda": True,
            "ejecutandoLlamadaAsincronicaBusqueda": False,
            "ultimaSeccion": "",
            "filtroPorRubrosSeccion": False,
            "filtroPorRubroBusqueda": False,
            "filtroPorSeccionBusqueda": False,
            "busquedaOriginal": True,
            "ordenamientoSegunda": False,
            "seccionesOriginales": [1, 2, 3],
            "ultimoItemExterno": None,
            "ultimoItemInterno": None,
            "texto": self.format_searchstring(),
            "rubros": [],
            "nroNorma": "",
            "anioNorma": "",
            "denominacion": "",
            "tipoContratacion": "",
            "anioContratacion": "",
            "nroContratacion": "",
            "fechaDesde": self.format_date(self.date_from),
            "fechaHasta": self.format_date(self.date_until),
            "todasLasPalabras": True,
            "comienzaDenominacion": True,
            "seccion": [1, 2, 3],
            "tipoBusqueda": "Avanzada",
            "numeroPagina": 1,
            "ultimoRubro": ""
        }
        return f'params={dumps(obj).strip()}&array_volver=[]'

    def parse_response(self, raw_response):
        content = raw_response.json()['content']
        return self.Response(code=raw_response.status_code,
                        html=content['html'],
                        count=content['cantidad_result_seccion'])

    def find_sections(self, soup):
        soup.findAll('h5', {'class': 'seccion-rubro'})

    def clean_text(self, text):
        return text.strip().replace(u'\xa0', u' ')

    def run(self):
        response = self.parse_response(
            request("POST", self.url, headers=self.headers, data=self.payload()))
        soup = BeautifulSoup(response.html, 'html.parser')

        articles = soup.findAll('p', {'class': 'item'})

        for article in articles:
            print(f'Title: {self.clean_text(article.text)}')
            print(f"Link: {BASE_URL+article.find_parent('a').get('href')}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--search', help='Search string in quotes, defaults to "Policia Seguridad Aeroportuaria"')
    parser.add_argument('-d', '--date', help='Date to search in iso format, yyyy-mm-dd, defaults to today\'s date')
    args = parser.parse_args()
    command = BoletinFetcher(search_string=args.search, input_date=args.date)
    command.run()