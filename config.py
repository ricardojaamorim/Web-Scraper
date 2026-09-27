BASE_URL = "https://www.pingodoce.pt"
USER_AGENT = "PriceTrackerBot/0.1 (personal project; contact: youremail@example.com)"
MIN_DELAY_SECONDS = 2.0  # Minimum delay between requests to avoid hammering the server
DB_PATH = "prices.db"

PRODUCT_SELECTORS = {
    "product_card": "div.product-tile-pd",
    "name": "div.product-name-link",
    "brand": "div.product-brand-name",
    "unit": "div.product-unit",
    "current_price_value": "span.sales.reduced-price span.value",
    "original_price_value": "span.strike-through.list span.value",
    "promo_message": "span.promo-message",
    "link": "a.product-tile-image-link",
}

CATEGORIES = [
    {"cgid": "ec_promos_1100000", "extra_params": {"pmin": "0.04"}},
    {"cgid": "ec_frutasevegetais_100", "extra_params": {"pmin": "0.04"}},
    {"cgid": "ec_talho_200", "extra_params": {"pmin": "0.04"}},
    {"cgid": "ec_peixaria_300", "extra_params": {"pmin": "0.04"}},
    {"cgid": "ec_padariaepastelaria_400", "extra_params": {"pmin": "0.04"}},
    {"cgid": "ec_charcutariaqueijos_500", "extra_params": {"pmin": "0.04"}},
    {"cgid": "ec_manteigasmargarinanatas_700", "extra_params": {"pmin": "0.04"}},
    {"cgid": "ec_animais_2300", "extra_params": {"pmin": "0.04"}},
    {"cgid": "ec_alternativasalimentares_2400", "extra_params": {"pmin": "0.04"}},
    {"cgid": "ec_parafarmacia_1800", "extra_params": {"pmin": "0.04"}},
    {"cgid": "ec_bebecrianca_2200", "extra_params": {"pmin": "0.04"}},
    {"cgid": "ec_higienepessoalbeleza_2100", "extra_params": {"pmin": "0.04"}},
    {"cgid": "ec_livrariapapelaria_2000", "extra_params": {"pmin": "0.04"}},
    {"cgid": "ec_casaeletrodomesticos_1900", "extra_params": {"pmin": "0.04"}},
    {"cgid": "ec_limpeza_1800", "extra_params": {"pmin": "0.04"}},
    {"cgid": "ec_vinhos_1700", "extra_params": {"pmin": "0.04"}},
    {"cgid": "ec_espirituosas_1600", "extra_params": {"pmin": "0.04"}},
    {"cgid": "ec_cervejassidras_1500", "extra_params": {"pmin": "0.04"}},
    {"cgid": "ec_aguassumosrefrigerantes_1400", "extra_params": {"pmin": "0.04"}},
    {"cgid": "ec_mercearia_1300", "extra_params": {"pmin": "0.04"}},
    {"cgid": "ec_bolachascereaisguloseimas_1200", "extra_params": {"pmin": "0.04"}},
    {"cgid": "ec_cafechaachocolatados_1100", "extra_params": {"pmin": "0.04"}},
    {"cgid": "ec_congelados_1000", "extra_params": {"pmin": "0.04"}},
    {"cgid": "ec_takeaway_2400", "extra_params": {"pmin": "0.04"}},
    {"cgid": "ec_leitebebidasvegetais_900", "extra_params": {"pmin": "0.04"}},
    {"cgid": "ec_iogurtessobremesas_800", "extra_params": {"pmin": "0.04"}},
    {"cgid": "ec_ovos_600", "extra_params": {"pmin": "0.04"}},
]
