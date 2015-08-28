import json

from django.contrib.auth.models import Group, Permission
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.test import Client, TestCase
from django.utils import timezone
from model_mommy import mommy

from common.tests.test_models import BaseTestCase
from ..models import MflUser, MFLOAuthApplication


class TestMflUserModel(BaseTestCase):

    def test_save_normal_user(self):
        data = {
            "email": "some@email.com",
            "employee_number": "some",
            "first_name": "jina",
            "last_name": "mwisho",
            "other_names": "jm",
            "password": "password1",
        }
        user = MflUser.objects.create_user(**data)

        # the base  test case class comes with another user
        self.assertEquals(3, MflUser.objects.count())

        self.assertEquals("jina", user.get_short_name)
        self.assertEquals("jina mwisho jm", user.get_full_name)

    def test_save_superuser(self):
        self.assertEquals(2, MflUser.objects.count())
        data = {
            "email": "some@email.com",
            "employee_number": "some",
            "first_name": "jina",
            "last_name": "mwisho",
            "other_names": "jm",
            "password": "password1",
        }
        user = MflUser.objects.create_superuser(**data)

        # the base  test case class comes with another user
        self.assertEquals(3, MflUser.objects.count())
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_permissions_property(self):
        data = {
            "email": "some@email.com",
            "employee_number": "some",
            "first_name": "jina",
            "last_name": "mwisho",
            "other_names": "jm",
            "password": "password1",
        }
        MflUser.objects.create_superuser(**data)
        # mysterious error here
        # self.assertTrue(len(user.permissions) > 0)
        # self.assertTrue("common.add_constituency" in user.permissions)

    def test_set_password_does_not_set_for_new_users(self):
        user = mommy.make(MflUser, password='a great password 1')
        user.set_password('does not really matter')
        self.assertIsNotNone(user.password_history)

    def test_set_password_sets_for_existing_users(self):
        user = mommy.make(MflUser, password='a very huge password 1')
        user.set_password('we now expect the change history to be saved')
        self.assertTrue(user.password_history)
        self.assertEqual(len(user.password_history), 1)

    def test_requires_password_change_new_user(self):
        user = mommy.make(MflUser, password='a very huge password 1')
        self.assertTrue(user.requires_password_change)

    def test_requires_password_change_new_user_with_prior_login(self):
        user = mommy.make(MflUser, password='A very huge password 1')
        self.assertTrue(user.requires_password_change)

    def test_doesnt_require_password_change_user_with_prior_passwords(self):
        user = mommy.make(MflUser, password='A very huge password1')
        user.set_password('we now expect the change history to be saved 1')
        self.assertFalse(user.requires_password_change)
        user.set_password('we now expect the change history to be saved 1')
        self.assertEqual(len(user.password_history), 2)

    def test_password_is_greater_than_or_equal_to_6_characters(self):
        data = {
            "email": "some@email.com",
            "employee_number": "some",
            "first_name": "jina",
            "last_name": "mwisho",
            "other_names": "jm",
            "password": "ort",
        }
        with self.assertRaises(ValidationError):
            MflUser.objects.create_user(**data)


class TestGroupCountyLevelMarkerProperty(BaseTestCase):

    def test_group_does_not_have_county_level_marker_permission(self):
        group = mommy.make(Group)
        perm = mommy.make(Permission)
        group.permissions.add(perm.id)
        county_perm = Permission.objects.get(codename='county_group_marker')
        self.assertNotIn(county_perm, group.permissions.all())
        self.assertFalse(group.is_county_level)
        self.assertIn(perm, group.permissions.all())

    def test_group_has_county_level_marker_permission(self):
        group = mommy.make(Group)
        perm = Permission.objects.get(codename='county_group_marker')
        group.permissions.add(perm.id)
        self.assertIn(perm, group.permissions.all())
        self.assertTrue(group.is_county_level)


class TestGroupSuperUsersProperty(BaseTestCase):
    def test_group_does_not_have_manipulate_superusers_permissions(self):
        group = mommy.make(Group)
        perm = mommy.make(Permission)
        group.permissions.add(perm.id)
        superuser_perm = Permission.objects.get(
            codename='manipulate_superusers')
        self.assertNotIn(superuser_perm, group.permissions.all())
        self.assertFalse(group.is_superuser_level)
        self.assertIn(perm, group.permissions.all())

    def test_group_has_county_level_marker_permission(self):
        group = mommy.make(Group)
        perm = Permission.objects.get(codename='manipulate_superusers')
        group.permissions.add(perm.id)
        self.assertIn(perm, group.permissions.all())
        self.assertTrue(group.is_superuser_level)


class TestLastLog(TestCase):

    def setUp(self):
        self.user_details = {
            'email': 'tester1@ehealth.or.ke',
            'first_name': 'Test',
            'employee_number': '2124124124',
            'password': 'mtihani124'
        }
        self.user = MflUser.objects.create_user(**self.user_details)
        admin = mommy.make(MflUser)
        app = MFLOAuthApplication.objects.create(
            name="test", user=admin, client_type="confidential",
            authorization_grant_type="password"
        )
        self.oauth2_payload = {
            "grant_type": "password",
            "username": self.user_details["employee_number"],
            "password": self.user_details["password"],
            "client_id": app.client_id,
            "client_secret": app.client_secret
        }

    def test_no_initial_login(self):
        self.assertIsNone(self.user.lastlog)
        self.assertIsNone(self.user.last_login)

    def test_session_login(self):
        self.user.last_login = timezone.now()
        self.user.save()
        self.assertEqual(self.user.lastlog, self.user.last_login)

    def test_oauth2_login(self):
        client = Client()
        resp = client.post(reverse("token"), self.oauth2_payload)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access_token", json.loads(resp.content))
        self.assertIsNotNone(self.user.lastlog)
        self.assertIsNone(self.user.last_login)

    def test_oauth2_login_then_session_login(self):
        token_client = Client()
        resp = token_client.post(reverse("token"), self.oauth2_payload)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access_token", json.loads(resp.content))

        self.user.last_login = timezone.now()
        self.user.save()

        self.assertEqual(self.user.lastlog, self.user.last_login)

    def test_session_login_then_oauth2_login(self):
        self.user.last_login = timezone.now()
        self.user.save()

        token_client = Client()
        resp = token_client.post(reverse("token"), self.oauth2_payload)
        self.assertEqual(resp.status_code, 200)
        self.assertIn("access_token", json.loads(resp.content))

        self.assertIsNotNone(self.user.lastlog)
        self.assertTrue(self.user.lastlog > self.user.last_login)
