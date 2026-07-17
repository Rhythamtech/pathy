from tools.search import read_page


def extract_page_text(url: str, max_characters: int = 7000) -> str:
    return read_page(url=url, max_characters=max_characters)