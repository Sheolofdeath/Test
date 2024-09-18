import argparse
import os
import re
import shutil
import sys
import zipfile
import time
from multiprocessing.dummy import Pool as ThreadPool
from pathlib import Path
from random import randint

import requests
import tqdm
from bs4 import BeautifulSoup as bs
from bs4 import element
from google_trans_new import google_translator

tool_version = '1.0.2'
LINE_SIZE = 90
HEADERS = {
    'user-agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36')}

LANGUAGES = {
    'af': 'afrikaans',
    'sq': 'albanian',
    'am': 'amharic',
    'ar': 'arabic',
    'hy': 'armenian',
    'az': 'azerbaijani',
    'eu': 'basque',
    'be': 'belarusian',
    'bn': 'bengali',
    'bs': 'bosnian',
    'bg': 'bulgarian',
    'ca': 'catalan',
    'ceb': 'cebuano',
    'ny': 'chichewa',
    'zh-cn': 'chinese (simplified)',
    'zh-tw': 'chinese (traditional)',
    'co': 'corsican',
    'hr': 'croatian',
    'cs': 'czech',
    'da': 'danish',
    'nl': 'dutch',
    'en': 'english',
    'eo': 'esperanto',
    'et': 'estonian',
    'tl': 'filipino',
    'fi': 'finnish',
    'fr': 'french',
    'fy': 'frisian',
    'gl': 'galician',
    'ka': 'georgian',
    'de': 'german',
    'el': 'greek',
    'gu': 'gujarati',
    'ht': 'haitian creole',
    'ha': 'hausa',
    'haw': 'hawaiian',
    'iw': 'hebrew',
    'he': 'hebrew',
    'hi': 'hindi',
    'hmn': 'hmong',
    'hu': 'hungarian',
    'is': 'icelandic',
    'ig': 'igbo',
    'id': 'indonesian',
    'ga': 'irish',
    'it': 'italian',
    'ja': 'japanese',
    'jw': 'javanese',
    'kn': 'kannada',
    'kk': 'kazakh',
    'km': 'khmer',
    'ko': 'korean',
    'ku': 'kurdish (kurmanji)',
    'ky': 'kyrgyz',
    'lo': 'lao',
    'la': 'latin',
    'lv': 'latvian',
    'lt': 'lithuanian',
    'lb': 'luxembourgish',
    'mk': 'macedonian',
    'mg': 'malagasy',
    'ms': 'malay',
    'ml': 'malayalam',
    'mt': 'maltese',
    'mi': 'maori',
    'mr': 'marathi',
    'mn': 'mongolian',
    'my': 'myanmar (burmese)',
    'ne': 'nepali',
    'no': 'norwegian',
    'or': 'odia',
    'ps': 'pashto',
    'fa': 'persian',
    'pl': 'polish',
    'pt': 'portuguese',
    'pa': 'punjabi',
    'ro': 'romanian',
    'ru': 'russian',
    'sm': 'samoan',
    'gd': 'scots gaelic',
    'sr': 'serbian',
    'st': 'sesotho',
    'sn': 'shona',
    'sd': 'sindhi',
    'si': 'sinhala',
    'sk': 'slovak',
    'sl': 'slovenian',
    'so': 'somali',
    'es': 'spanish',
    'su': 'sundanese',
    'sw': 'swahili',
    'sv': 'swedish',
    'tg': 'tajik',
    'ta': 'tamil',
    'tt': 'tatar',
    'te': 'telugu',
    'th': 'thai',
    'tr': 'turkish',
    'tk': 'turkmen',
    'uk': 'ukrainian',
    'ur': 'urdu',
    'ug': 'uyghur',
    'uz': 'uzbek',
    'vi': 'vietnamese',
    'cy': 'welsh',
    'xh': 'xhosa',
    'yi': 'yiddish',
    'yo': 'yoruba',
    'zu': 'zulu',
}


class pcolors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    ORANGE = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def check_for_tool_updates():
    try:
        release_api = 'https://api.github.com/repos/quantrancse/epub-translator/releases/latest'
        response = requests.get(
            release_api, headers=HEADERS, timeout=5).json()
        latest_release = response['tag_name'][1:]
        if tool_version != latest_release:
            print(
                f'Current tool version: {pcolors.FAIL}{tool_version}{pcolors.ENDC}')
            print(
                f'Latest tool version: {pcolors.GREEN}{latest_release}{pcolors.ENDC}')
            print(
                f'Please upgrade the tool at: {pcolors.CYAN}https://github.com/quantrancse/epub-translator/releases{pcolors.ENDC}')
            print('-' * LINE_SIZE)
    except Exception:
        print('Something was wrong. Can not get the tool latest update!')


class TranslatorEngine():
    def __init__(self):
        self.dest_lang = 'vi'
        self.file_path = ''
        self.file_name = ''
        self.file_extracted_path = ''
        self.html_list_path = []
        self.translation_dict = {}
        self.translation_dict_file_path = ''
        self.dict_format = '^[^:]+:[^:]+$'
        self.max_trans_words = 5e3
        self.max_retries = 5  # Set the default max retries

    def get_epub_file_info(self, file_path):
        self.file_path = file_path
        self.file_name = os.path.splitext(os.path.basename(file_path))[0]
        self.file_extracted_path = os.path.join(os.path.abspath(
            os.path.join(file_path, os.pardir)), self.file_name + '_translated')

    def extract_epub(self):
        try:
            with zipfile.ZipFile(self.file_path, 'r') as zip:
                print('Extracting the epub file...', end='\r')
                zip.extractall(self.file_extracted_path)
                print(
                    f'Extracting the epub file: [{pcolors.GREEN} DONE {pcolors.ENDC}]')
            return True
        except Exception:
            print(
                f'Extracting the epub file: [{pcolors.FAIL} FAIL {pcolors.ENDC}]')
            return False

    def get_epub_html_path(self):
        for file_type in ['*.[hH][tT][mM][lL]', '*.[xX][hH][tT][mM][lL]', '*.[hH][tT][mM]']:
            self.html_list_path += [str(p.resolve())
                                    for p in list(Path(self.file_extracted_path).rglob(file_type))]

    def start(self, file_path):
    print(f"Starting translation process for {file_path}")
    self.get_epub_file_info(file_path)
    if self.extract_epub():
        print("EPUB extraction completed.")
        self.get_epub_html_path()
        print(f"Found {len(self.html_list_path)} HTML files to translate.")
        self.multithreads_html_translate()
        print("Translation completed.")
        self.zip_epub()
    
    def multithreads_html_translate(self):
        pool = ThreadPool(8)
        try:
            for _ in tqdm.tqdm(pool.imap_unordered(self.translate_html, self.html_list_path), total=len(self.html_list_path), desc='Translating'):
                pass
        except Exception:
            print(f'Translating epub: [{pcolors.FAIL} FAIL {pcolors.ENDC}]')
            raise
        pool.close()
        pool.join()

    def translate_html(self, html_file):
        with open(html_file, encoding='utf-8') as f:
            soup = bs(f, 'xml')

            epub_eles = list(soup.descendants)

            text_list = []
            for ele in epub_eles:
                if isinstance(ele, element.NavigableString) and str(ele).strip() not in ['', 'html']:
                    text_list.append(str(ele))

            translated_text = self.translate_tag(text_list)
            nextpos = -1

            for ele in epub_eles:
                if isinstance(ele, element.NavigableString) and str(ele).strip() not in ['', 'html']:
                    nextpos += 1
                    if nextpos < len(translated_text):
                        content = self.replace_translation_dict(
                            translated_text[nextpos])
