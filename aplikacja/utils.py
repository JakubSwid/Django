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
    Zapisuje oryginalną i skompresowaną wersję przesłanego zdjęcia.

    Args:
        foto_instance: Instancja modelu Foto
        uploaded_file: Przesłany plik z formularza
    """
    uploaded_file.seek(0)

    foto_instance.plik_oryginalny.save(uploaded_file.name, uploaded_file, save=False)

    uploaded_file.seek(0)

    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
        temp_path = temp_file.name

        try:
            with Image.open(uploaded_file) as img:
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')

                img.thumbnail((1200, 800), Image.Resampling.LANCZOS)

                img.save(temp_path, 'JPEG', quality=85, optimize=True)

            with open(temp_path, 'rb') as compressed_file:
                name, ext = os.path.splitext(uploaded_file.name)
                compressed_filename = f"{name}_skompresowany.jpg"
                foto_instance.plik.save(compressed_filename, File(compressed_file), save=False)

        finally:
            try:
                os.remove(temp_path)
            except OSError:
                pass

    foto_instance.save()


def save_uploaded_photos(uploaded_files):
    """
    Zapisuje przesłane zdjęcia do katalogu tymczasowego i zwraca ścieżkę.

    Args:
        uploaded_files: Lista przesłanych plików zdjęć

    Returns:
        str: Ścieżka do katalogu tymczasowego zawierającego zdjęcia
    """
    if not uploaded_files:
        return None

    temp_dir = tempfile.mkdtemp(prefix='import_photos_')

    for uploaded_file in uploaded_files:
        file_path = os.path.join(temp_dir, uploaded_file.name)

        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, 'wb') as f:
            for chunk in uploaded_file.chunks():
                f.write(chunk)

    return temp_dir


def find_photo_file(photo_name, photos_base_dir):
    """
    Znajduje plik zdjęcia w katalogu zdjęć (wyszukiwanie rekurencyjne).

    Args:
        photo_name (str): Nazwa pliku zdjęcia
        photos_base_dir (str): Katalog bazowy do przeszukania

    Returns:
        str or None: Pełna ścieżka do pliku zdjęcia jeśli znaleziony, None w przeciwnym razie
    """
    if not photos_base_dir or not os.path.exists(photos_base_dir):
        return None

    photo_filename = os.path.basename(photo_name)

    for root, dirs, files in os.walk(photos_base_dir):
        if photo_filename in files:
            return os.path.join(root, photo_filename)

    return None


def optimize_image(image_path, max_width=1200, max_height=800, quality=85):
    """
    Optymalizuje obraz poprzez zmianę rozmiaru i kompresję.

    Args:
        image_path (str): Ścieżka do pliku obrazu
        max_width (int): Maksymalna szerokość w pikselach
        max_height (int): Maksymalna wysokość w pikselach
        quality (int): Jakość JPEG (1-100)

    Returns:
        str: Ścieżka do zoptymalizowanego obrazu (plik tymczasowy)
    """
    try:
        with Image.open(image_path) as img:
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            temp_dir = tempfile.mkdtemp()
            filename = os.path.basename(image_path)
            name, ext = os.path.splitext(filename)

            optimized_path = os.path.join(temp_dir, f"{name}_skompresowany.jpg")

            img.save(optimized_path, 'JPEG', quality=quality, optimize=True)

            original_size = os.path.getsize(image_path)
            optimized_size = os.path.getsize(optimized_path)
            reduction_percent = ((original_size - optimized_size) / original_size) * 100

            print(f"Obraz zoptymalizowany: {filename}")
            print(f"  Oryginalny: {original_size / 1024 / 1024:.2f} MB")
            print(f"  Zoptymalizowany: {optimized_size / 1024 / 1024:.2f} MB")
            print(f"  Redukcja: {reduction_percent:.1f}%")

            return optimized_path

    except Exception as e:
        print(f"Błąd optymalizacji obrazu {image_path}: {e}")
        return image_path


def detect_encoding(file_path):
    """
    Wykrywa najlepsze kodowanie do odczytu pliku CSV z polskimi znakami.

    Args:
        file_path (str): Ścieżka do pliku CSV

    Returns:
        str: Najlepsze kodowanie do użycia
    """
    encodings_to_try = [
        'utf-8-sig',
        'utf-8',
        'cp1250',
        'iso-8859-2',
        'windows-1252'
    ]

    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding, newline='') as test_file:
                for _ in range(5):
                    line = test_file.readline()
                    if not line:
                        break
                return encoding
        except (UnicodeDecodeError, UnicodeError):
            continue

    return 'utf-8'


def parse_date_field(date_value):
    """
    Parsuje datę z różnych formatów.

    Args:
        date_value (str): Ciąg znaków daty do sparsowania

    Returns:
        date or None: Sparsowany obiekt daty lub None jeśli parsowanie nie powiedzie się
    """
    if not date_value:
        return None

    date_formats = [
        '%Y-%m-%d',
        '%d.%m.%Y',
        '%d/%m/%Y',
        '%d-%m-%Y',
        '%Y/%m/%d',
        '%Y.%m.%d',
    ]

    for date_format in date_formats:
        try:
            return datetime.strptime(date_value, date_format).date()
        except ValueError:
            continue

    return None


def import_objects_from_csv(file_path, photos_base_dir=None):
    """
    Importuje dane Obiekt i powiązane zdjęcia z pliku CSV z wartościami oddzielonymi przecinkami.

    Args:
        file_path (str): Ścieżka do pliku CSV
        photos_base_dir (str): Katalog bazowy zawierający zdjęcia (opcjonalny)

    Returns:
        tuple: (liczba_sukcesów, liczba_błędów, komunikaty_błędów)
    """
    success_count = 0
    error_count = 0
    error_messages = []

    current_date = date.today()

    try:
        encoding = detect_encoding(file_path)

        with open(file_path, 'r', encoding=encoding, newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=',')

            for row in reader:
                try:
                    row = {k: v if v and v.strip() else None for k, v in row.items()}

                    data_wpisu = parse_date_field(row.get('data_wpisu'))
                    if not data_wpisu:
                        data_wpisu = current_date
                        print(f"Brak 'data_wpisu' w rzędzie {reader.line_num}, używam bieżącej daty: {current_date}")

                    data_korekty_1 = parse_date_field(row.get('data_korekty_1'))
                    data_korekty_2 = parse_date_field(row.get('data_korekty_2'))

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
                        'data_wpisu': data_wpisu,
                        'korekta_nr_1_autor': row.get('korekta_nr_1_autor', ''),
                        'data_korekty_1': data_korekty_1,
                        'korekta_nr_2_autor': row.get('korekta_nr_2_autor', ''),
                        'data_korekty_2': data_korekty_2,
                        'imie_nazwisko_osoby_upamietnionej': row.get('imie_nazwisko_osoby_upamietnionej', ''),
                        'skan_3d': row.get('skan_3d', ''),
                        'status': row.get('status', 'opublikowany')
                    }

                    obiekt = Obiekt(**obiekt_data)
                    obiekt.full_clean()
                    obiekt.save()

                    photo_list = []
                    for key in row:
                        if key.startswith('zdjecie'):
                            value = row[key]
                            if isinstance(value, str) and value.strip():
                                photo_list.append(value.strip())

                    if len(photo_list) > 10:
                        raise ValidationError(f"Obiekt może mieć maksymalnie 10 zdjęć. Znaleziono {len(photo_list)}.")

                    for photo_name in photo_list:
                        try:
                            photo_path = None

                            if photos_base_dir:
                                photo_path = find_photo_file(photo_name, photos_base_dir)

                            if not photo_path:
                                if os.path.isabs(photo_name):
                                    photo_path = photo_name
                                else:
                                    default_photo_dir = os.path.join(settings.MEDIA_ROOT, 'zdjecia')
                                    potential_path = os.path.join(default_photo_dir, photo_name)
                                    if os.path.exists(potential_path):
                                        photo_path = potential_path

                            if not photo_path or not os.path.exists(photo_path):
                                error_messages.append(
                                    f"Nie znaleziono pliku zdjęcia: {photo_name} dla obiektu {obiekt}")
                                continue

                            optimized_photo_path = optimize_image(photo_path)

                            foto = Foto(obiekt=obiekt)
                            filename = os.path.basename(photo_path)
                            name, ext = os.path.splitext(filename)

                            with open(photo_path, 'rb') as original_file:
                                original_filename = f"{name}{ext}"
                                foto.plik_oryginalny.save(original_filename, File(original_file), save=False)

                            with open(optimized_photo_path, 'rb') as photo_file:
                                optimized_filename = f"{name}_skompresowany.jpg"
                                foto.plik.save(optimized_filename, File(photo_file), save=False)

                            foto.save()

                            if optimized_photo_path != photo_path:
                                try:
                                    os.remove(optimized_photo_path)
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
            f"Błąd dekodowania Unicode: {str(e)}. Plik może zawierać znaki, które nie mogą być zdekodowane żadnym obsługiwanym kodowaniem.")
        error_count += 1
    except Exception as e:
        error_messages.append(f"Nieoczekiwany błąd: {str(e)}")
        error_count += 1

    return success_count, error_count, error_messages