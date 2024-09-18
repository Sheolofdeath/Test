import argparse
import os
import re
import shutil
import sys
import zipfile
from multiprocessing.dummy import Pool as ThreadPool
from pathlib import Path

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
    # ... [same LANGUAGES dictionary]
}

class pcolors:
    # ... [same pcolors class]

def check_for_tool_updates():
    # ... [same function]

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
                print(f'Extracting the epub file: [{pcolors.GREEN} DONE {pcolors.ENDC}]')
            return True
        except Exception:
            print(f'Extracting the epub file: [{pcolors.FAIL} FAIL {pcolors.ENDC}]')
            return False

    def get_epub_html_path(self):
        for file_type in ['*.[hH][tT][mM][lL]', '*.[xX][hH][tT][mM]', '*.[hH][tT][mM]']:
            self.html_list_path += [str(p.resolve())
                                    for p in list(Path(self.file_extracted_path).rglob(file_type))]

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
                        ele.replace_with(element.NavigableString(content))

            with open(html_file, "w", encoding="utf-8") as w:
                w.write(str(soup))

    def replace_translation_dict(self, text):
        if self.translation_dict:
            for replace_text in self.translation_dict.keys():
                if replace_text in text:
                    text = text.replace(
                        replace_text, self.translation_dict[replace_text])
        return text

    def get_translation_dict_contents(self):
        if os.path.isfile(self.translation_dict_file_path) and self.translation_dict_file_path.endswith('.txt'):
            print('Translation dictionary detected.')
            with open(self.translation_dict_file_path, encoding='utf-8') as f:
                for line in f.readlines():
                    if re.match(self.dict_format, line):
                        split = line.rstrip().split(':')
                        self.translation_dict[split[0]] = split[1]
                    else:
                        print(f'Translation dictionary is not in correct format: {line}')
                        return False
            return True
        else:
            print('Translation dictionary file path is incorrect!')
            return False

    def translate_tag(self, text_list):
        combined_contents = self.combine_words(text_list)
        translated_contents = self.multithreads_translate(combined_contents)
        extracted_contents = self.extract_words(translated_contents)

        return extracted_contents

    def translate_text(self, text):
        translator = google_translator(timeout=5)
        if type(text) is not str:
            translate_text = ''
            for substr in text:
                translate_substr = translator.translate(substr, self.dest_lang)
                translate_text += translate_substr
        else:
            translate_text = translator.translate(text, self.dest_lang)
        return translate_text

    def multithreads_translate(self, text_list):
        results = []
        pool = ThreadPool(8)
        try:
            results = pool.map(self.translate_text, text_list)
        except Exception:
            print(f'Translating epub: [{pcolors.FAIL} FAIL {pcolors.ENDC}]')
            raise
        pool.close()
        pool.join()
        return results

    def combine_words(self, text_list):
        combined_text = []
        combined_single = ''
        for text in text_list:
            combined_single_prev = combined_single
            if combined_single:
                combined_single += '\n-----\n' + text
            else:
                combined_single = text
            if len(combined_single) >= self.max_trans_words:
                combined_text.append(combined_single_prev)
                combined_single = '\n-----\n' + text
        combined_text.append(combined_single)
        return combined_text

    def extract_words(self, text_list):
        extracted_text = []
        for text in text_list:
            extract = text.split('-----')
            extracted_text += extract
        return extracted_text

    def zip_epub(self):
        print('Making the translated epub file...', end='\r')
        try:
            filename = f"{self.file_extracted_path}.epub"
            file_extracted_absolute_path = Path(self.file_extracted_path)

            with open(str(file_extracted_absolute_path / 'mimetype'), 'w') as file:
                file.write('application/epub+zip')
            with zipfile.ZipFile(filename, 'w') as archive:
                archive.write(
                    str(file_extracted_absolute_path / 'mimetype'), 'mimetype',
                    compress_type=zipfile.ZIP_STORED)
                for file in file_extracted_absolute_path.rglob('*.*'):
                    archive.write(
                        str(file), str(file.relative_to(
                            file_extracted_absolute_path)),
                        compress_type=zipfile.ZIP_DEFLATED)

            shutil.rmtree(self.file_extracted_path)
            print(f'Making the translated epub file: [{pcolors.GREEN} DONE {pcolors.ENDC}]')
        except Exception as e:
            print(e)
            print(f'Making the translated epub file: [{pcolors.FAIL} FAIL {pcolors.ENDC}]')

    def start(self, dir_path):
        for epub_file in Path(dir_path).glob('*.epub'):
            self.get_epub_file_info(str(epub_file))
            if self.extract_epub():
                self.get_epub_html_path()
                self.multithreads_html_translate()
                self.zip_epub()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='A tool for translating all epub files in a folder to different languages using Google Translate, with support for custom dictionaries.')
    parser.add_argument('-v', '--version', action='version',
                        version='epub-translator v%s' % tool_version)
    parser.add_argument('directory', type=str,
                        help='path to the directory containing epub files')  # Specify directory
    parser.add_argument('-l', '--lang', type=str, metavar='dest_lang',
                        help='destination language')
    parser.add_argument('-d', '--dict', type=str, metavar='dict_path',
                        help='path to the translation dictionary')
    args = parser.parse_args()

    engine = TranslatorEngine()

    check_for_tool_updates()

    if args.lang and args.lang not in LANGUAGES.keys():
        print('Cannot find destination language: ' + args.lang)
        sys.exit()
    elif args.lang:
        engine.dest_lang = args.lang

    if args.dict:
        translation_dict_file_path = args.dict.replace(
            '&', '').replace('\'', '').replace('\"', '').strip()
        engine.translation_dict_file_path = os.path.abspath(
            translation_dict_file_path)
        if not engine.get_translation_dict_contents():
            sys.exit()

    # Process all EPUB files in the specified directory
    dir_path = args.directory.replace('&', '').replace('\'', '').replace('\"', '').strip()
    
    if os.path.isdir(dir_path):
        engine.start(dir_path)
    else:
        print(f'The specified path is not a valid directory: {dir_path}')
        sys.exit()
                  
