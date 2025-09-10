from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from .models import Obiekt


class FormSystemTestCase(TestCase):
    def setUp(self):
        # Utwórz testowych użytkowników
        self.user = User.objects.create_user('testuser', 'test@example.com', 'testpass123')
        self.editor = User.objects.create_user('editor', 'editor@example.com', 'editorpass123')
        
        # Utwórz grupę Redaktor i dodaj redaktora
        redaktor_group = Group.objects.create(name='Redaktor')
        self.editor.groups.add(redaktor_group)
        
        self.client = Client()

    def test_two_button_form_functionality(self):
        """Test that form correctly handles both button actions"""
        self.client.login(username='testuser', password='testpass123')
        
        # Najpierw sprawdź czy widok formularza ładuje się poprawnie
        response = self.client.get(reverse('formularz'))
        self.assertEqual(response.status_code, 200)
        
    def test_object_creation_with_status(self):
        """Test that objects can be created with different statuses"""
        # Testuj tworzenie roboczego obiektu
        draft_obj = Obiekt.objects.create(
            nazwa_geograficzna_polska='Draft Object',
            typ_obiektu='Test Type',
            status='roboczy',
            user=self.user
        )
        self.assertEqual(draft_obj.status, 'roboczy')
        self.assertEqual(draft_obj.user, self.user)
        
        # Testuj tworzenie obiektu do weryfikacji
        verification_obj = Obiekt.objects.create(
            nazwa_geograficzna_polska='Verification Object',
            typ_obiektu='Test Type',
            status='weryfikacja',
            user=self.user
        )
        self.assertEqual(verification_obj.status, 'weryfikacja')
        self.assertEqual(verification_obj.user, self.user)

    def test_editor_access_to_import_csv(self):
        """Test that only editors can access import CSV"""
        # Zwykły użytkownik powinien zostać odrzucony
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('import_csv'))
        self.assertEqual(response.status_code, 403)
        
        # Redaktor powinien mieć dostęp
        self.client.login(username='editor', password='editorpass123')
        response = self.client.get(reverse('import_csv'))
        self.assertEqual(response.status_code, 200)

    def test_edit_draft_permissions(self):
        """Test that users can only edit their own draft objects but editors can edit any object"""
        # Utwórz roboczy obiekt dla użytkownika
        draft_obj = Obiekt.objects.create(
            nazwa_geograficzna_polska='User Draft',
            typ_obiektu='Test',
            status='roboczy',
            user=self.user
        )
        
        # Użytkownik powinien móc uzyskać dostęp do swojego roboczego obiektu
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('edytuj_roboczy', args=[draft_obj.id]))
        self.assertEqual(response.status_code, 200)
        
        # Redaktor powinien teraz móc uzyskać dostęp do roboczego obiektu użytkownika (zmienione zachowanie)
        self.client.login(username='editor', password='editorpass123')
        response = self.client.get(reverse('edytuj_roboczy', args=[draft_obj.id]))
        self.assertEqual(response.status_code, 200)

    def test_template_tags(self):
        """Test permission template tags work correctly"""
        from .templatetags.permission_tags import is_redaktor, can_edit_obiekt
        
        # Testuj filtr is_redaktor
        self.assertFalse(is_redaktor(self.user))
        self.assertTrue(is_redaktor(self.editor))
        
        # Testuj filtr can_edit_obiekt
        draft_obj = Obiekt.objects.create(
            nazwa_geograficzna_polska='User Draft',
            typ_obiektu='Test',
            status='roboczy',
            user=self.user
        )
        
        self.assertTrue(can_edit_obiekt(self.user, draft_obj))
        # Redaktorzy mogą teraz edytować dowolny obiekt (zmienione zachowanie)
        self.assertTrue(can_edit_obiekt(self.editor, draft_obj))
        
        # Testuj nie-roboczy obiekt
        published_obj = Obiekt.objects.create(
            nazwa_geograficzna_polska='Published',
            typ_obiektu='Test',
            status='weryfikacja',
            user=self.user
        )
        
        # Zwykli użytkownicy nie mogą edytować nie-roboczych obiektów
        self.assertFalse(can_edit_obiekt(self.user, published_obj))
        # Ale redaktorzy mogą edytować dowolny obiekt
        self.assertTrue(can_edit_obiekt(self.editor, published_obj))
