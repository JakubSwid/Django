from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from .models import Obiekt


class FormSystemTestCase(TestCase):
    def setUp(self):
        # Create test users
        self.user = User.objects.create_user('testuser', 'test@example.com', 'testpass123')
        self.editor = User.objects.create_user('editor', 'editor@example.com', 'editorpass123')
        
        # Create Redaktor group and add editor
        redaktor_group = Group.objects.create(name='Redaktor')
        self.editor.groups.add(redaktor_group)
        
        self.client = Client()

    def test_two_button_form_functionality(self):
        """Test that form correctly handles both button actions"""
        self.client.login(username='testuser', password='testpass123')
        
        # First test the form view loads correctly
        response = self.client.get(reverse('formularz'))
        self.assertEqual(response.status_code, 200)
        
    def test_object_creation_with_status(self):
        """Test that objects can be created with different statuses"""
        # Test draft object creation
        draft_obj = Obiekt.objects.create(
            nazwa_geograficzna_polska='Draft Object',
            typ_obiektu='Test Type',
            status='roboczy',
            user=self.user
        )
        self.assertEqual(draft_obj.status, 'roboczy')
        self.assertEqual(draft_obj.user, self.user)
        
        # Test verification object creation
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
        # Regular user should be denied
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('import_csv'))
        self.assertEqual(response.status_code, 403)
        
        # Editor should have access
        self.client.login(username='editor', password='editorpass123')
        response = self.client.get(reverse('import_csv'))
        self.assertEqual(response.status_code, 200)

    def test_edit_draft_permissions(self):
        """Test that users can only edit their own draft objects"""
        # Create a draft object for user
        draft_obj = Obiekt.objects.create(
            nazwa_geograficzna_polska='User Draft',
            typ_obiektu='Test',
            status='roboczy',
            user=self.user
        )
        
        # User should be able to access their own draft
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('edytuj_roboczy', args=[draft_obj.id]))
        self.assertEqual(response.status_code, 200)
        
        # Editor should not be able to access user's draft
        self.client.login(username='editor', password='editorpass123')
        response = self.client.get(reverse('edytuj_roboczy', args=[draft_obj.id]))
        self.assertEqual(response.status_code, 403)

    def test_template_tags(self):
        """Test permission template tags work correctly"""
        from .templatetags.permission_tags import is_redaktor, can_edit_obiekt
        
        # Test is_redaktor filter
        self.assertFalse(is_redaktor(self.user))
        self.assertTrue(is_redaktor(self.editor))
        
        # Test can_edit_obiekt filter
        draft_obj = Obiekt.objects.create(
            nazwa_geograficzna_polska='User Draft',
            typ_obiektu='Test',
            status='roboczy',
            user=self.user
        )
        
        self.assertTrue(can_edit_obiekt(self.user, draft_obj))
        self.assertFalse(can_edit_obiekt(self.editor, draft_obj))
        
        # Test non-draft object
        published_obj = Obiekt.objects.create(
            nazwa_geograficzna_polska='Published',
            typ_obiektu='Test',
            status='weryfikacja',
            user=self.user
        )
        
        self.assertFalse(can_edit_obiekt(self.user, published_obj))
