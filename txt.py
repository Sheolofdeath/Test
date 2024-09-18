from google_trans_new import google_translator

def translate_file(input_file_path, output_file_path, target_language):
    # Initialize the translator
    translator = google_translator(timeout=10)

    try:
        # Read the content of the input file
        with open(input_file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        # Translate the content
        translated_content = translator.translate(content, lang_tgt=target_language)

        # Write the translated content to the output file
        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.write(translated_content)

        print(f"Translation completed and saved to {output_file_path}")

    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage:
input_file_path = 'input.txt'  # Path to your input text file
output_file_path = 'translated_output.txt'  # Path to save the translated text
target_language = 'en'  # Translate to Spanish; you can change the target language code

translate_file(input_file_path, output_file_path, target_language)
