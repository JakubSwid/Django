import csv
from datetime import datetime
from django.core.exceptions import ValidationError
from django.core.files import File
import os
from django.conf import settings  # Import settings for MEDIA_ROOT
from .models import Obiekt, Foto


def import_objects_from_csv(file_path):
    """
    Import Obiekt data and associated photos from a CSV file with comma-separated values.

    Args:
        file_path (str): Path to the CSV file

    Returns:
        tuple: (success_count, error_count, error_messages)
    """
    success_count = 0
    error_count = 0
    error_messages = []

    # Define the base directory for photos (e.g., MEDIA_ROOT/photos)
    PHOTO_BASE_DIR = os.path.join(settings.MEDIA_ROOT, 'zdjecia')  # Adjust as needed

    try:
        with open(file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')

            for row in reader:
                try:
                    # Convert empty strings to None for nullable fields, safely handle None
                    row = {k: v if v and v.strip() else None for k, v in row.items()}

                    # Prepare data for Obiekt creation
                    obiekt_data = {
                        'polozenie_szerokosc': float(row['polozenie_szerokosc']) if row.get(
                            'polozenie_szerokosc') else None,
                        'polozenie_dlugosc': float(row['polozenie_dlugosc']) if row.get('polozenie_dlugosc') else None,
                        'obiekt': row.get('obiekt', ''),
                        'nazwa_geograficzna_polska': row['nazwa_geograficzna_polska'],
                        'nazwa_geograficzna_obca': row.get('nazwa_geograficzna_obca', ''),
                        'wojewodztwo': row.get('wojewodztwo', ''),
                        'powiat': row['powiat'],
                        'lokalizacja': row.get('lokalizacja', ''),
                        'typ_obiektu': row['typ_obiektu'],
                        'material': row.get('material', ''),
                        'wysokosc': float(row['wysokosc']) if row.get('wysokosc') else None,
                        'szerokosc': float(row['szerokosc']) if row.get('szerokosc') else None,
                        'opis': row.get('opis', ''),
                        'inskrypcja': row.get('inskrypcja', ''),
                        'typ_pisma': row.get('typ_pisma', ''),
                        'tlumaczenie': row.get('tlumaczenie', ''),
                        'herby': row.get('herby', ''),
                        'genealogia': row.get('genealogia', ''),
                        'bibliografia': row.get('bibliografia', ''),
                        'odsylacze_do_zrodla': row.get('odsylacze_do_zrodla', ''),
                        'autorzy_wpisu': row.get('autorzy_wpisu', ''),
                        'data_wpisu': datetime.strptime(row['data_wpisu'], '%Y-%m-%d').date() if row.get(
                            'data_wpisu') else None,
                        'korekta_nr_1_autor': row.get('korekta_nr_1_autor', ''),
                        'data_korekty_1': datetime.strptime(row['data_korekty_1'], '%Y-%m-%d').date() if row.get(
                            'data_korekty_1') else None,
                        'korekta_nr_2_autor': row.get('korekta_nr_2_autor', ''),
                        'data_korekty_2': datetime.strptime(row['data_korekty_2'], '%Y-%m-%d').date() if row.get(
                            'data_korekty_2') else None,
                        'imie_nazwisko_osoby_upamietnionej': row.get('imie_nazwisko_osoby_upamietnionej', ''),
                        'skan_3d': row.get('skan_3d', ''),
                        'status': row.get('status', 'opublikowany')
                    }

                    # Create and save Obiekt instance
                    obiekt = Obiekt(**obiekt_data)
                    obiekt.full_clean()  # Validate the model
                    obiekt.save()

                    # Handle photo imports from additional columns
                    photo_list = []
                    for key in row:
                        if key.startswith('zdjecie'):
                            value = row[key]
                            if isinstance(value, str) and value.strip():
                                # Prepend base directory if path is relative
                                full_path = value if os.path.isabs(value) else os.path.join(PHOTO_BASE_DIR, value)
                                photo_list.append(full_path)
                            elif value:
                                error_messages.append(f"Invalid photo value in {key} for {obiekt}: {value}")

                    # Limit to 10 photos
                    if len(photo_list) > 10:
                        raise ValidationError(f"Obiekt może mieć maksymalnie 10 zdjęć. Znaleziono {len(photo_list)}.")

                    for path in photo_list:
                        try:
                            if not os.path.exists(path):
                                raise FileNotFoundError(f"Photo file not found: {path}")

                            with open(path, 'rb') as photo_file:
                                foto = Foto(obiekt=obiekt)
                                filename = os.path.basename(path)
                                foto.plik.save(filename, File(photo_file), save=True)
                        except (FileNotFoundError, Exception) as e:
                            error_count += 1
                            error_messages.append(f"Error adding photo {path} for {obiekt}: {str(e)}")
                            continue

                    success_count += 1

                except (ValueError, ValidationError, KeyError) as e:
                    error_count += 1
                    error_messages.append(f"Error in row {reader.line_num}: {str(e)}")

    except FileNotFoundError:
        error_messages.append(f"File not found: {file_path}")
        error_count += 1
    except Exception as e:
        error_messages.append(f"Unexpected error: {str(e)}")
        error_count += 1

    return success_count, error_count, error_messages