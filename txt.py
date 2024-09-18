import argparse
from google_trans_new import google_translator
import os

def split_text(text, max_length=5000):
    """Split text into chunks of max_length characters."""
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]

def translate_file(input_file_path, target_language):
    # Initialize the translator
    translator = google_translator(timeout=10)

    try:
        # Try reading the file with different encodings
        encodings = ['utf-8', 'ISO-8859-1', 'windows-1252']
        content = ""
        
        for encoding in encodings:
            try:
                with open(input_file_path, 'r', encoding=encoding) as file:
                    content = file.read()
                break  # Exit loop if read is successful
            except UnicodeDecodeError:
                continue  # Try next encoding if error occurs

        if not content:
            raise ValueError("Unable to decode the file with supported encodings.")

        # Split content into chunks and translate
        chunks = split_text(content)
        translated_chunks = []

        for chunk in chunks:
            translated_chunk = translator.translate(chunk, lang_tgt=target_language)
            translated_chunks.append(translated_chunk)
        
        # Join translated chunks
        translated_content = ''.join(translated_chunks)

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
    
