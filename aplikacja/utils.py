import csv
import os
import tempfile
from datetime import datetime
from django.core.exceptions import ValidationError
from django.core.files import File
from django.conf import settings
from .models import Obiekt, Foto


def save_uploaded_photos(uploaded_files):
    """
    Save uploaded photos to a temporary directory and return the path.

    Args:
        uploaded_files: List of uploaded photo files

    Returns:
        str: Path to temporary directory containing photos
    """
    if not uploaded_files:
        return None

    # Create temporary directory for photos
    temp_dir = tempfile.mkdtemp(prefix='import_photos_')

    for uploaded_file in uploaded_files:
        # Get the relative path from the uploaded file
        # webkitdirectory preserves folder structure in file.name
        file_path = os.path.join(temp_dir, uploaded_file.name)

        # Create directories if they don't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Save the file
        with open(file_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

    return temp_dir


def find_photo_file(photo_name, photos_base_dir):
    """
    Find a photo file in the photos directory (recursive search).

    Args:
        photo_name (str): Name of the photo file
        photos_base_dir (str): Base directory to search in

    Returns:
        str or None: Full path to photo file if found, None otherwise
    """
    if not photos_base_dir or not os.path.exists(photos_base_dir):
        return None

    # Remove any path separators from photo_name, we only want the filename
    photo_filename = os.path.basename(photo_name)

    # Search recursively in the photos directory
    for root, dirs, files in os.walk(photos_base_dir):
        if photo_filename in files:
            return os.path.join(root, photo_filename)

    return None


def detect_encoding(file_path):
    """
    Detect the best encoding for reading the CSV file with Polish characters.

    Args:
        file_path (str): Path to the CSV file

    Returns:
        str: Best encoding to use
    """
    # List of encodings commonly used for Polish text
    encodings_to_try = [
        'utf-8-sig',  # UTF-8 with BOM (Excel often saves with this)
        'utf-8',  # Standard UTF-8
        'cp1250',  # Windows Central European
        'iso-8859-2',  # Latin-2 Central European
        'windows-1252'  # Windows Western European (fallback)
    ]

    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding, newline='') as test_file:
                # Try to read first few lines to test encoding
                for _ in range(5):
                    line = test_file.readline()
                    if not line:
                        break
                # If we got here without error, this encoding works
                return encoding
        except (UnicodeDecodeError, UnicodeError):
            continue

    # If all encodings fail, default to utf-8 and let it raise an error
    return 'utf-8'


def import_objects_from_csv(file_path, photos_base_dir=None):
    """
    Import Obiekt data and associated photos from a CSV file with comma-separated values.

    Args:
        file_path (str): Path to the CSV file
        photos_base_dir (str): Base directory containing photos (optional)

    Returns:
        tuple: (success_count, error_count, error_messages)
    """
    success_count = 0
    error_count = 0
    error_messages = []

    try:
        # Detect the best encoding for the file
        encoding = detect_encoding(file_path)

        with open(file_path, 'r', encoding=encoding, newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')

            for row in reader:
                try:
                    # Convert empty strings to None for nullable fields, safely handle None
                    row = {k: v if v and v.strip() else None for k, v in row.items()}

                    # Prepare data for Obiekt creation
                    obiekt_data = {
                        'polozenie_szerokosc': float(row['polozenie_szerokosc'].replace(',', '.')) if row.get(
                            'polozenie_szerokosc') else None,
                        'polozenie_dlugosc': float(row['polozenie_dlugosc'].replace(',', '.')) if row.get(
                            'polozenie_dlugosc') else None,
                        'obiekt': row.get('obiekt', ''),
                        'nazwa_geograficzna_polska': row['nazwa_geograficzna_polska'],
                        'nazwa_geograficzna_obca': row.get('nazwa_geograficzna_obca', ''),
                        'wojewodztwo': row.get('wojewodztwo', ''),
                        'powiat': row.get('powiat', ''),
                        'lokalizacja': row.get('lokalizacja', ''),
                        'typ_obiektu': row['typ_obiektu'],
                        'material': row.get('material', ''),
                        'wysokosc': float(row['wysokosc'].replace(',', '.')) if row.get('wysokosc') else None,
                        'szerokosc': float(row['szerokosc'].replace(',', '.')) if row.get('szerokosc') else None,
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
                                photo_list.append(value.strip())

                    # Limit to 10 photos
                    if len(photo_list) > 10:
                        raise ValidationError(f"Obiekt może mieć maksymalnie 10 zdjęć. Znaleziono {len(photo_list)}.")

                    # Process photos
                    for photo_name in photo_list:
                        try:
                            photo_path = None

                            # If photos_base_dir is provided, search for the photo
                            if photos_base_dir:
                                photo_path = find_photo_file(photo_name, photos_base_dir)

                            # If not found in uploaded folder, try the old method (absolute/relative path)
                            if not photo_path:
                                if os.path.isabs(photo_name):
                                    photo_path = photo_name
                                else:
                                    # Try in default MEDIA_ROOT/zdjecia directory
                                    default_photo_dir = os.path.join(settings.MEDIA_ROOT, 'zdjecia')
                                    potential_path = os.path.join(default_photo_dir, photo_name)
                                    if os.path.exists(potential_path):
                                        photo_path = potential_path

                            if not photo_path or not os.path.exists(photo_path):
                                error_messages.append(f"Photo file not found: {photo_name} for object {obiekt}")
                                continue

                            with open(photo_path, 'rb') as photo_file:
                                foto = Foto(obiekt=obiekt)
                                filename = os.path.basename(photo_path)
                                foto.plik.save(filename, File(photo_file), save=True)

                        except Exception as e:
                            error_count += 1
                            error_messages.append(f"Error adding photo {photo_name} for {obiekt}: {str(e)}")
                            continue

                    success_count += 1

                except (ValueError, ValidationError, KeyError) as e:
                    error_count += 1
                    error_messages.append(f"Error in row {reader.line_num}: {str(e)}")

    except FileNotFoundError:
        error_messages.append(f"File not found: {file_path}")
        error_count += 1
    except UnicodeDecodeError as e:
        error_messages.append(
            f"Unicode decode error: {str(e)}. File may contain characters that cannot be decoded with any supported encoding.")
        error_count += 1
    except Exception as e:
        error_messages.append(f"Unexpected error: {str(e)}")
        error_count += 1

    return success_count, error_count, error_messages