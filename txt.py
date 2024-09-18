import argparse
import time
from google_trans_new import google_translator
from tqdm import tqdm
import chardet

def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        raw_data = f.read(10000)  # Read the first 10000 bytes
        result = chardet.detect(raw_data)
        return result['encoding']

def translate_text(text, translator, retries=3):
    for attempt in range(retries):
        try:
            return translator.translate(text)
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
            time.sleep(5)  # Wait before retrying
    raise Exception("Failed to connect after several attempts")

def translate_file(input_file, output_file):
    translator = google_translator(timeout=10)

    # Detect file encoding
    encoding = detect_encoding(input_file)
    
    # Read the content from the input file
    with open(input_file, 'r', encoding=encoding) as f:
        text = f.read()

    # Show progress bar for translation
    print("Translating...")
    translated_text = ""

    # Simulate progress for large text
    for _ in tqdm(range(1), desc="Progress"):
        translated_text = translate_text(text, translator)

    # Write the translated content to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(translated_text)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Translate all text inside a txt file using Google Translate.")
    parser.add_argument('input_file', type=str, help='Path to the input text file')
    parser.add_argument('output_file', type=str, help='Path to the output translated text file')
    
    args = parser.parse_args()
    
    translate_file(args.input_file, args.output_file)
