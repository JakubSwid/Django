import csv
import os
import tempfile
from datetime import datetime, date
from django.core.exceptions import ValidationError
from django.core.files import File
from django.conf import settings
from .models import Obiekt, Foto
from PIL import Image
import io


def save_foto_with_compression(foto_instance, uploaded_file):
    """
    Save both original and compressed versions of an uploaded photo.
    
    Args:
        foto_instance: Foto model instance
        uploaded_file: Uploaded file from form
    """
    # Reset file position to beginning
    uploaded_file.seek(0)
    
    # Save original image
    foto_instance.plik_oryginalny.save(uploaded_file.name, uploaded_file, save=False)
    
    # Reset file position again for compression
    uploaded_file.seek(0)
    
    # Create temporary file for compression
    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
        temp_path = temp_file.name
        
        # Create compressed version
        try:
            with Image.open(uploaded_file) as img:
                # Convert to RGB if necessary (for JPEG compatibility)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Calculate new size maintaining aspect ratio
                img.thumbnail((1200, 800), Image.Resampling.LANCZOS)
                
                # Save compressed image
                img.save(temp_path, 'JPEG', quality=85, optimize=True)
        
            # Save compressed image to model
            with open(temp_path, 'rb') as compressed_file:
                name, ext = os.path.splitext(uploaded_file.name)
                compressed_filename = f"{name}_compressed.jpg"
                foto_instance.plik.save(compressed_filename, File(compressed_file), save=False)
                
        finally:
            # Clean up temporary file
            try:
                os.remove(temp_path)
            except OSError:
                pass
    
    foto_instance.save()


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


def optimize_image(image_path, max_width=1200, max_height=800, quality=85):
    """
    Optimize image by resizing and compressing it.

    Args:
        image_path (str): Path to the image file
        max_width (int): Maximum width in pixels
        max_height (int): Maximum height in pixels
        quality (int): JPEG quality (1-100)

    Returns:
        str: Path to optimized image (temporary file)
    """
    try:
        with Image.open(image_path) as img:
            # Convert to RGB if necessary (for JPEG compatibility)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            # Calculate new size maintaining aspect ratio
            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            # Create temporary file for optimized image
            temp_dir = tempfile.mkdtemp()
            filename = os.path.basename(image_path)
            name, ext = os.path.splitext(filename)

            # Force JPEG extension for better compression
            optimized_path = os.path.join(temp_dir, f"{name}_optimized.jpg")

            # Save optimized image
            img.save(optimized_path, 'JPEG', quality=quality, optimize=True)

            # Check file size reduction
            original_size = os.path.getsize(image_path)
            optimized_size = os.path.getsize(optimized_path)
            reduction_percent = ((original_size - optimized_size) / original_size) * 100

            print(f"Image optimized: {filename}")
            print(f"  Original: {original_size / 1024 / 1024:.2f} MB")
            print(f"  Optimized: {optimized_size / 1024 / 1024:.2f} MB")
            print(f"  Reduction: {reduction_percent:.1f}%")

            return optimized_path

    except Exception as e:
        print(f"Error optimizing image {image_path}: {e}")
        return image_path  # Return original if optimization fails


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


def parse_date_field(date_value):
    """
    Parse date from various formats.

    Args:
        date_value (str): Date string to parse

    Returns:
        date or None: Parsed date object or None if parsing fails
    """
    if not date_value:
        return None

    # Try different date formats
    date_formats = [
        '%Y-%m-%d',  # 2024-01-15
        '%d.%m.%Y',  # 15.01.2024
        '%d/%m/%Y',  # 15/01/2024
        '%d-%m-%Y',  # 15-01-2024
        '%Y/%m/%d',  # 2024/01/15
        '%Y.%m.%d',  # 2024.01.15
    ]

    for date_format in date_formats:
        try:
            return datetime.strptime(date_value, date_format).date()
        except ValueError:
            continue

    return None


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

    # Get current date for default values
    current_date = date.today()

    try:
        # Detect the best encoding for the file
        encoding = detect_encoding(file_path)

        with open(file_path, 'r', encoding=encoding, newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')

            for row in reader:
                try:
                    # Convert empty strings to None for nullable fields, safely handle None
                    row = {k: v if v and v.strip() else None for k, v in row.items()}

                    # Parse date fields with fallback to current date
                    data_wpisu = parse_date_field(row.get('data_wpisu'))
                    if not data_wpisu:
                        data_wpisu = current_date
                        print(f"No 'data_wpisu' found in row {reader.line_num}, using current date: {current_date}")

                    data_korekty_1 = parse_date_field(row.get('data_korekty_1'))
                    data_korekty_2 = parse_date_field(row.get('data_korekty_2'))

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
                        'data_wpisu': data_wpisu,  # Always has a value (current date if not provided)
                        'korekta_nr_1_autor': row.get('korekta_nr_1_autor', ''),
                        'data_korekty_1': data_korekty_1,  # Can be None
                        'korekta_nr_2_autor': row.get('korekta_nr_2_autor', ''),
                        'data_korekty_2': data_korekty_2,  # Can be None
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

                            # SAVE BOTH ORIGINAL AND COMPRESSED IMAGES
                            optimized_photo_path = optimize_image(photo_path)
                            
                            foto = Foto(obiekt=obiekt)
                            filename = os.path.basename(photo_path)
                            name, ext = os.path.splitext(filename)
                            
                            # Save original image
                            with open(photo_path, 'rb') as original_file:
                                original_filename = f"{name}_original{ext}"
                                foto.plik_oryginalny.save(original_filename, File(original_file), save=False)
                            
                            # Save compressed image
                            with open(optimized_photo_path, 'rb') as photo_file:
                                # Change extension to .jpg for optimized images
                                optimized_filename = f"{name}.jpg"
                                foto.plik.save(optimized_filename, File(photo_file), save=False)
                            
                            # Save the Foto instance
                            foto.save()

                            # Clean up temporary optimized file
                            if optimized_photo_path != photo_path:
                                try:
                                    os.remove(optimized_photo_path)
                                    # Also remove the temporary directory if empty
                                    temp_dir = os.path.dirname(optimized_photo_path)
                                    if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                                        os.rmdir(temp_dir)
                                except OSError:
                                    pass

                        except Exception as e:
                            error_count += 1
                            error_messages.append(f"Błąd przy dodawaniu zdjęcia {photo_name} dla {obiekt}: {str(e)}")
                            continue

                    success_count += 1

                except (ValueError, ValidationError, KeyError) as e:
                    error_count += 1
                    error_messages.append(f"Błąd w rzędzie {reader.line_num}: {str(e)}")

    except FileNotFoundError:
        error_messages.append(f"Plik nie znaleziony: {file_path}")
        error_count += 1
    except UnicodeDecodeError as e:
        error_messages.append(
            f"Unicode decode error: {str(e)}. File may contain characters that cannot be decoded with any supported encoding.")
        error_count += 1
    except Exception as e:
        error_messages.append(f"Unexpected error: {str(e)}")
        error_count += 1

    return success_count, error_count, error_messages