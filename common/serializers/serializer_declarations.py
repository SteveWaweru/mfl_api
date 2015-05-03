from rest_framework import serializers

from ..models import (
    Contact,
    PhysicalAddress,
    County,
    Ward,
    Constituency,
    ContactType,
    UserCounty,
    UserContact,
    Town
)
from .serializer_base import AbstractFieldsMixin


class UserContactSerializer(
        AbstractFieldsMixin, serializers.ModelSerializer):
    class Meta(object):
        model = UserContact


class ContactTypeSerializer(
        AbstractFieldsMixin, serializers.ModelSerializer):

    class Meta(object):
        model = ContactType


class ContactSerializer(
        AbstractFieldsMixin, serializers.ModelSerializer):

    class Meta(object):
        model = Contact


class PhysicalAddressSerializer(
        AbstractFieldsMixin, serializers.ModelSerializer):

    class Meta(object):
        model = PhysicalAddress


class CountySerializer(
        AbstractFieldsMixin, serializers.ModelSerializer):
    from mfl_gis.serializers import CountyBoundarySerializer

    county_boundary = CountyBoundarySerializer(
        source='countyboundary',
        read_only=True
    )

    class Meta(object):
        model = County


class TownSerializer(
        AbstractFieldsMixin, serializers.ModelSerializer):

    class Meta(object):
        model = Town


class WardSerializer(
        AbstractFieldsMixin, serializers.ModelSerializer):
    from mfl_gis.serializers import WardBoundarySerializer

    ward_boundary = WardBoundarySerializer(
        source='wardboundary',
        read_only=True
    )

    county = serializers.CharField(read_only=True)

    class Meta(object):
        model = Ward


class ConstituencySerializer(
        AbstractFieldsMixin, serializers.ModelSerializer):
    from mfl_gis.serializers import ConstituencyBoundarySerializer

    constituency_boundary = ConstituencyBoundarySerializer(
        source='constituencyboundary',
        read_only=True
    )

    class Meta(object):
        model = Constituency


class InchargeCountiesSerializer(
        AbstractFieldsMixin, serializers.ModelSerializer):
    class Meta(object):
        model = UserCounty
