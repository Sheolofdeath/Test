import argparse
from google_trans_new import google_translator
import os

def translate_file(input_file_path, target_language):
    # Initialize the translator
    translator = google_translator(timeout=10)

    try:
        # Read the content of the input file
        with open(input_file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Translate the content
        translated_content = translator.translate(content, lang_tgt=target_language)

        # Define the output file path
        base, _ = os.path.splitext(input_file_path)
        output_file_path = f"{base}_translated.txt"

        # Write the translated content to the output file
        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.write(translated_content)

        print(f"Translation completed and saved to {output_file_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Translate the contents of a text file to a specified language.')
    parser.add_argument('input_file', type=str, help='Path to the input text file')
    parser.add_argument('target_language', type=str, help='Target language code (e.g., "es" for Spanish)')

    args = parser.parse_args()

    translate_file(args.input_file, args.target_language)
