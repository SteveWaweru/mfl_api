import logging
import uuid
import pytz

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.conf import settings

from .fields import SequenceField
from .utilities.sequence_helper import SequenceGenerator

LOGGER = logging.getLogger(__file__)


def get_utc_localized_datetime(datetime_instance):
    """
    Converts a naive datetime to a UTC localized datetime.

    :datetime_instance datetime A naive datetime instance.
    """
    current_timezone = pytz.timezone(settings.TIME_ZONE)
    localized_datetime = current_timezone.localize(datetime_instance)
    return localized_datetime.astimezone(pytz.utc)


def get_default_system_user_id():
    """
    Ensure that there is a default system user, unknown password
    """
    try:
        return get_user_model().objects.get(
            email='system@ehealth.or.ke',
            first_name='System',
            username='system'
        ).pk
    except get_user_model().DoesNotExist:
        return get_user_model().objects.create(
            email='system@ehealth.or.ke',
            first_name='System',
            username='system'
        ).pk


class CustomDefaultManager(models.Manager):
    def get_queryset(self):
        return super(
            CustomDefaultManager, self).get_queryset().filter(deleted=False)


class AbstractBase(models.Model):
    """
    Provides auditing attributes to a model.

    It will provide audit fields that will keep track of when a model
    is created or updated and by who.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, default=get_default_system_user_id,
        on_delete=models.PROTECT, related_name='+')
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, default=get_default_system_user_id,
        on_delete=models.PROTECT, related_name='+')
    deleted = models.BooleanField(default=False)
    active = models.BooleanField(
        default=True,
        help_text="Indicates whether the record has been retired?")

    objects = CustomDefaultManager()
    everything = models.Manager()

    def validate_updated_date_greater_than_created(self):
        if timezone.is_naive(self.updated):
            self.updated = get_utc_localized_datetime(self.updated)

        if self.updated < self.created:
            raise ValidationError(
                'The updated date cannot be less than the created date')

    def preserve_created_and_created_by(self):
        """
        Ensures that in subsequent times created and created_by fields
        values are not overriden.
        """
        try:
            original = self.__class__.objects.get(pk=self.pk)
            self.created = original.created
            self.created_by = original.created_by
        except self.__class__.DoesNotExist:
            LOGGER.info(
                'preserve_created_and_created_by '
                'Could not find an instance of {} with pk {} hence treating '
                'this as a new record.'.format(self.__class__, self.pk))

    def save(self, *args, **kwargs):
        self.full_clean(exclude=None)
        self.preserve_created_and_created_by()
        self.validate_updated_date_greater_than_created()
        super(AbstractBase, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Mark the field model deleted
        self.deleted = True
        self.save()

    class Meta:
        abstract = True


class SequenceMixin(object):
    """
    Intended to be mixed into models with a `code` `SequenceField`
    """

    def generate_next_code_sequence(self):
        """
        Relies upon the predictability of Django sequence naming
        ( convention )
        """
        return SequenceGenerator(
            app_label=self._meta.app_label,
            model_name=self._meta.model_name
        ).next()


class ContactType(AbstractBase):
    """
    Captures the different types of contacts that we have in the real world.

    The most common contacts are email, phone numbers, landline etc.
    """
    name = models.CharField(
        max_length=100, unique=True,
        help_text="A short name, preferrably 6 characters long, representing a"
        "certain type of contact e.g EMAIL")
    description = models.TextField(help_text='A brief desx')

    def __unicode__(self):
        return self.name


class Contact(AbstractBase):
    """
    Holds ways in which entities can communicate.

    The commincation ways are not limited provided that all parties
    willing to communicate will be able to do so. The commucation
    ways may include emails, phone numbers, landlines etc.
    """
    contact = models.CharField(
        max_length=100,
        help_text="The actual contact of the person e.g test@mail.com,"
        " 07XXYYYZZZ")
    contact_type = models.ForeignKey(
        ContactType,
        help_text="The type of contact that the given contact is e.g email"
        " or phone number",
        on_delete=models.PROTECT)

    def __unicode__(self):
        return "{}::{}".format(self.contact_type.name, self.contact)


class PhysicalAddress(AbstractBase):
    """
    The physical properties of a facility.

    These are physical properties of the facility and included is the
    plot number and nearest landmark. This information in conjunction with
    GPS codes is useful in locating the facility.
    """
    town = models.CharField(
        max_length=100, null=True, blank=True,
        help_text="The town where the entity is located e.g Nakuru")
    postal_code = models.CharField(
        max_length=100,
        help_text="The 5 digit number for the post office address. e.g 00900")
    address = models.CharField(
        max_length=100,
        help_text="This is the actual post office number of the entity. "
        "e.g 6790")
    nearest_landmark = models.CharField(
        max_length=100, null=True, blank=True,
        help_text="well-known physical features /structure that can be used to"
        " simplify directions to a given place. e.g town market or village ")
    plot_number = models.CharField(
        max_length=100, null=True, blank=True,
        help_text="This is the same number found on the title deeds of the"
        "piece of land on which this facility is located")

    def __unicode__(self):
        return "{}: {}".format(self.postal_code, self.address)


class RegionAbstractBase(AbstractBase, SequenceMixin):
    """
    Model to supply the common attributes of a region.

    A  region is an Administrative/political hierarchy and includes the
    following levels:
        1. County,
        2. Constituency,
        3. Sub-county,
        4. ward
    """
    name = models.CharField(
        max_length=100, unique=True,
        help_text="Name og the region may it be e.g Nairobi")
    code = SequenceField(
        unique=True,
        help_text="A unique_code 4 digit number representing the region.")

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_next_code_sequence()
        super(RegionAbstractBase, self).save(*args, **kwargs)

    class Meta:
        abstract = True


class County(RegionAbstractBase):
    """
    This is the largest administrative/political division in Kenya.

    Kenya is divided in 47 different counties.

    Code generation is handled by the custom save method in RegionAbstractBase
    """
    pass  # Everything, including __unicode__ is handled by the abstract model


class Constituency(RegionAbstractBase):
    """
    Counties in Kenya are divided into constituencies.

    A Constituency is a political sub division of a county.
    There are 290 constituencies in total.
    In most cases they coincide with sub counties.

    Code generation is handled by the custom save method in RegionAbstractBase
    """

    county = models.ForeignKey(
        County,
        help_text="Name of the county where the constituency is located",
        on_delete=models.PROTECT)


class Ward(RegionAbstractBase):
    """
    The Kenyan counties are sub divided into wards.

    This is an administrative sub-division of the counties.
    A constituency can have one or more wards.
    In most cases the sub county is also the constituency.

    Code generation is handled by the custom save method in RegionAbstractBase
    """
    constituency = models.ForeignKey(
        Constituency,
        help_text="The constituency where the ward is located.",
        on_delete=models.PROTECT)

    @property
    def county(self):
        return self.constituency.county


class UserCounties(AbstractBase):
    """
    Will store a record of the counties that a user has been incharge of.

    A user can only be incharge of only one county at a time.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='user_counties',
        on_delete=models.PROTECT)
    county = models.ForeignKey(County, on_delete=models.PROTECT)
    is_active = models.BooleanField(
        default=True,
        help_text="Is the user currently incharge of the county?")

    def __unicode__(self):
        return "{}: {}".format(self.user.email, self.county.name)

    def validate_only_one_county_active(self):
        """
        A user can be incharge of only one county at the a time.
        """
        counties = self.__class__.objects.filter(
            user=self.user, is_active=True)
        if counties.count() > 0:
            raise ValidationError(
                "A user can only be active in one county at a time")

    def save(self, *args, **kwargs):
        self.validate_only_one_county_active()
        super(UserCounties, self).save(*args, **kwargs)


class UserResidence(AbstractBase):
    """
    Stores the wards in which the user resides in.
    If a user moves to another ward the current ward is deactivated by setting
    active to False
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='user_residence')
    ward = models.ForeignKey(Ward, on_delete=models.PROTECT)

    def __unicode__(self):
        return self.user.email + ": " + self.ward.name

    def validate_user_residing_in_one_place_at_a_time(self):
        user_wards = self.__class__.objects.filter(user=self.user, active=True)
        if user_wards.count() > 0:
            raise ValidationError(
                "User can only reside in one ward at a a time")

    def save(self, *args, **kwargs):
        self.validate_user_residing_in_one_place_at_a_time()
        super(UserResidence, self).save(*args, **kwargs)


class UserContact(AbstractBase):
    """
    Stores a user's contacts.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='user_contacts', on_delete=models.PROTECT)
    contact = models.ForeignKey(Contact)

    def __unicode__(self):
        return "{}: {}".format(self.user.get_full_name, self.contact.contact)
