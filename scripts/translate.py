from googletrans import Translator
import polib
import os
import shutil

# need to install:
#  pip install googletrans==4.0.0-rc1
#  pip install poli


def translate_po_to_spanish(input_path):
    # Load the original .po file
    po = polib.pofile(input_path)

    # Initialize the Google Translator
    translator = Translator()
    new_translations = 0
    failed = 0
    # Translate messages to Spanish and update the .po object
    for entry in po:
        if entry.msgstr:
            continue  # Skip entries that already have translations
        # print(entry.msgid)
        try:
            translated_text = translator.translate(
                entry.msgid, src='en', dest='es').text
            entry.msgstr = translated_text
            new_translations += 1
        except:   # noqa: E722
            failed += 1

    # Save the translated .po file
    po.save(input_path)
    print(f"Translation complete. new {new_translations} failed {failed}")


if __name__ == "__main__":
    #  Replace with your input .po file path
    input_po_file = "locale/es/LC_MESSAGES/django.po"
    # Replace with the desired output .po file path
    copy_file = input_po_file + '.copy'
    if os.path.exists(input_po_file):
        shutil.copy(input_po_file, copy_file)
        translate_po_to_spanish(input_po_file)
    else:
        print(f"{input_po_file} File does not exist.")
