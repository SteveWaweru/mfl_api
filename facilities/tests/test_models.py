from django.utils import timezone

from model_mommy import mommy

from common.tests.test_models import BaseTestCase
from common.models import Contact, Ward, PhysicalAddress

from ..models import (
    OwnerType, Owner, JobTitle, OfficerIncharge,
    OfficerInchargeContact, FacilityStatus, FacilityType,
    RegulatingBody, RegulationStatus, Facility,
    FacilityRegulationStatus, GeoCodeSource,
    GeoCodeMethod, FacilityCoordinates,
    FacilityContact, FacilityUnit)


class TestOwnerTypes(BaseTestCase):
    def test_save(self):
        data = {
            "name": "FBO",
            "description": "The the faith based organisation owners"
        }
        data = self.inject_audit_fields(data)
        owner_type = OwnerType.objects.create(**data)
        self.assertEquals(1, OwnerType.objects.count())

        # test unicode
        self.assertEquals("FBO", owner_type.__unicode__())


class TestOwnerModel(BaseTestCase):
    def test_save(self):
        owner_type = mommy.make(OwnerType, name="FBO")
        data = {
            "owner_type": owner_type,
            "name": "CHAK",
            "description": "this is some description",
            "abbreviation": "CHAK"
        }
        data = self.inject_audit_fields(data)
        owner = Owner.objects.create(**data)
        self.assertEquals(1, Owner.objects.count())

        owner_with_no_code = mommy.make(Owner, code=None)
        self.assertTrue(owner_with_no_code.code >= 1)

        owner_with_code = mommy.make(Owner, code=679879)
        self.assertTrue(owner_with_code.code >= 1)

        # test unicode
        self.assertEquals("CHAK", owner.__unicode__())
        self.assertIsNotNone(owner.code)

    def test_owner_code_sequence(self):
        # make code none so that mommy does not supply it
        owner_1 = mommy.make(Owner, code=None)
        owner_2 = mommy.make(Owner, code=None)
        owner_2_code = int(owner_1.code) + 1
        self.assertEquals(owner_2.code, owner_2_code)


class TestJobTitleModel(BaseTestCase):
    def test_save(self):
        data = {
            "name": "Nurse officer incharge",
            "description": "some good description"
        }
        data = self.inject_audit_fields(data)
        jt = JobTitle.objects.create(**data)
        self.assertEquals(1, JobTitle.objects.count())

        # test unicode
        self.assertEquals("Nurse officer incharge", jt.__unicode__())


class TestOfficerIncharge(BaseTestCase):
    def test_save(self):
        jt = mommy.make(JobTitle)
        data = {
            "name": "Kimani Maruge",
            "registration_number": "78736790",
            "job_title": jt
        }
        data = self.inject_audit_fields(data)
        officer = OfficerIncharge.objects.create(**data)
        self.assertEquals(1, OfficerIncharge.objects.count())

        # test unicode
        self.assertEquals("Kimani Maruge", officer.__unicode__())


class TestOfficerInchargeContactModel(BaseTestCase):
    def test_save(self):
        officer = mommy.make(OfficerIncharge, name='Maruge')
        contact = mommy.make(Contact, contact='maruge@gmail.com')
        data = {
            "officer": officer,
            "contact": contact
        }
        data = self.inject_audit_fields(data)
        contact = OfficerInchargeContact.objects.create(**data)
        self.assertEquals(1, OfficerInchargeContact.objects.count())

        # test unicode
        expected = "Maruge: maruge@gmail.com"
        self.assertEquals(expected, contact.__unicode__())


class TestFacilityStatusModel(BaseTestCase):
    def test_save(self):
        data = {
            "name": "OPERATIONAL",
            "description": "The Facility is operating normally"
        }
        data = self.inject_audit_fields(data)
        fs = FacilityStatus.objects.create(**data)

        # test unicode
        self.assertEquals('OPERATIONAL', fs.__unicode__())


class TestFacilityTypeModel(BaseTestCase):
    def test_save(self):
        data = {
            "name": "Hospital",
            "sub_division": "District Hospital"
        }
        data = self.inject_audit_fields(data)
        facility_type = FacilityType.objects.create(**data)
        self.assertEquals(1, FacilityType.objects.count())

        # test unicode
        self.assertEquals("Hospital", facility_type.__unicode__())


class TestRegulatingBodyModel(BaseTestCase):
    def test_save(self):
        data = {
            "name": "Director of Medical Services",
            "abbreviation": "DMS"
        }
        data = self.inject_audit_fields(data)
        regulating_body = RegulatingBody.objects.create(**data)
        self.assertEquals(1, RegulatingBody.objects.count())

        # test unicode
        self.assertEquals(
            "Director of Medical Services",
            regulating_body.__unicode__())


class TestFacility(BaseTestCase):
    def test_save(self):
        facility_type = mommy.make(FacilityType, name="DISPENSARY")
        operation_status = mommy.make(FacilityStatus, name="OPERATIONAL")
        officer_in_charge = mommy.make(OfficerIncharge)
        regulating_body = mommy.make(RegulatingBody)
        owner = mommy.make(Owner, name="MOH")
        ward = mommy.make(Ward)
        address = mommy.make(PhysicalAddress)
        data = {
            "name": "Forces Memorial",
            "description": "Hospital for the armed forces",
            "facility_type": facility_type,
            "number_of_beds": 100,
            "number_of_cots": 1,
            "open_whole_day": True,
            "open_whole_week": True,
            "operation_status": operation_status,
            "ward": ward,
            "owner": owner,
            "location_desc": "it is located along Moi Avenue Nairobi",
            "officer_in_charge": officer_in_charge,
            "physical_address": address
        }
        data = self.inject_audit_fields(data)
        facility = Facility.objects.create(**data)
        facility_reg_status = mommy.make(
            FacilityRegulationStatus, facility=facility,
            regulating_body=regulating_body)
        self.assertEquals(1, Facility.objects.count())

        # Bloody branch misses
        mommy.make(Facility, code=89778)
        mommy.make(Facility, code=None)

        #  test unicode
        self.assertEquals("Forces Memorial", facility.__unicode__())
        self.assertIsNotNone(facility.code)
        self.assertEquals(
            facility_reg_status.regulation_status,
            facility.current_regulatory_status)

    def test_working_of_facility_code_sequence(self):
        # make code none so that mommy does not supply it
        facility_1 = mommy.make(Facility, code=None)
        facility_2 = mommy.make(Facility, code=None)
        facility_2_code = int(facility_1.code) + 1
        self.assertEquals(int(facility_2.code), facility_2_code)


class TestGeoCodeSourceModel(BaseTestCase):
    def test_save(self):
        data = {
            "name": "Kenya Medical Research Institute",
            "description": "",
            "abbreviation": "KEMRI"
        }
        data = self.inject_audit_fields(data)
        source = GeoCodeSource.objects.create(**data)
        self.assertEquals(1, GeoCodeSource.objects.count())

        # test unicode
        self.assertEquals(
            "Kenya Medical Research Institute",
            source.__unicode__())


class TesGeoCodeMethodModel(BaseTestCase):
    def test_save(self):
        data = {
            "name": "Taken with GPS device",
            "description": "GPS device was used to get the geo codes"
        }
        data = self.inject_audit_fields(data)
        method = GeoCodeMethod.objects.create(**data)
        self.assertEquals(1, GeoCodeMethod.objects.count())

        # test unicode
        self.assertEquals("Taken with GPS device", method.__unicode__())


class TestFacilityCoordinatesModel(BaseTestCase):
    def test_save(self):
        facility = mommy.make(Facility, name="Nairobi Hospital")
        method = mommy.make(GeoCodeMethod)
        source = mommy.make(GeoCodeSource)
        data = {
            "facility": facility,
            "latitude": "78.99",
            "longitude": "67.54",
            "method": method,
            "source": source,
            "collection_date": timezone.now()
        }
        data = self.inject_audit_fields(data)
        facility_gps = FacilityCoordinates.objects.create(**data)
        self.assertEquals(1, FacilityCoordinates.objects.count())

        # test unicode
        self.assertEquals("Nairobi Hospital", facility_gps.__unicode__())


class TestFacilityContact(BaseTestCase):
    def test_save(self):
        facility = mommy.make(Facility, name="Nairobi Hospital")
        contact = mommy.make(Contact, contact="075689267")
        data = {
            "facility": facility,
            "contact": contact
        }
        data = self.inject_audit_fields(data)
        facility_contact = FacilityContact.objects.create(**data)

        # test unicode
        expected = "Nairobi Hospital: 075689267"
        self.assertEquals(expected, facility_contact.__unicode__())


class TestRegulationStatus(BaseTestCase):
    def test_save(self):
        data = {
            "name": "OPERATIONAL",
            "description": "The facility is operating normally."
        }
        data = self.inject_audit_fields(data)
        regulation_status = RegulationStatus.objects.create(**data)
        self.assertEquals(1, RegulationStatus.objects.count())

        # test unicode
        self.assertEquals("OPERATIONAL", regulation_status.__unicode__())


class TestFacilityRegulationStatus(BaseTestCase):
    def test_save(self):
        facility = mommy.make(Facility, name="Nairobi Hospital")
        status = mommy.make(RegulationStatus, name="SUSPENDED")
        regulator = mommy.make(RegulatingBody)
        data = {
            "facility": facility,
            "regulation_status": status,
            "reason": "Reports of misconduct by the doctor",
            "regulating_body": regulator
        }
        data = self.inject_audit_fields(data)
        facility_reg_status = FacilityRegulationStatus.objects.create(**data)
        self.assertEquals(1, FacilityRegulationStatus.objects.count())

        #  test unicode
        expected = "Nairobi Hospital: SUSPENDED"
        self.assertEquals(expected, facility_reg_status.__unicode__())


class TestFacilityUnitModel(BaseTestCase):

    def test_string_representation(self):
        facility = mommy.make(Facility, name='AKUH')
        data = {
            "facility": facility,
            "name": "Pharmacy",
            "description": "This is the AKUH Pharmacy section."
        }
        data = self.inject_audit_fields(data)
        facility_unit = FacilityUnit.objects.create(**data)
        self.assertEquals(1, FacilityUnit.objects.count())
        self.assertEquals(str(facility_unit), 'AKUH: Pharmacy')