"""Celery tasks related to maintenance functions around AWS."""
import json
import logging

import boto3
from django.db import IntegrityError, transaction
from django.utils.translation import gettext as _

from api.clouds.aws.models import AwsEC2InstanceDefinition
from util.celery import retriable_shared_task

logger = logging.getLogger(__name__)


@retriable_shared_task(name="api.clouds.aws.tasks.repopulate_ec2_instance_mapping")
def repopulate_ec2_instance_mapping():
    """
    Use the Boto3 pricing client to update the EC2 instancetype lookup table.

    Returns:
        None: Run as an asynchronous Celery task.

    """
    definitions = _fetch_ec2_instance_type_definitions()
    with transaction.atomic():
        try:
            _save_ec2_instance_type_definitions(definitions)
        except Exception as e:
            logger.exception(
                _("Failed to save EC2 instance definitions; rolling back.")
            )
            raise e
    logger.info(_("Finished saving AWS EC2 instance type definitions."))


def _fetch_ec2_instance_type_definitions():
    """
    Fetch EC2 instance type definitions from AWS Pricing API.

    Returns:
        dict: definitions dict of dicts where the outer key is the instance
        type name and the inner dict has keys memory and vcpu. For example:
        {'r5.large': {'memory': 24.0, 'vcpu': 1}}

    """
    client = boto3.client("pricing")
    paginator = client.get_paginator("get_products")
    page_iterator = paginator.paginate(
        ServiceCode="AmazonEC2",
        Filters=[
            {
                "Type": "TERM_MATCH",
                "Field": "productFamily",
                "Value": "Compute Instance",
            },
        ],
    )
    logger.info(_("Getting AWS EC2 instance type information."))
    instances = {}
    for page in page_iterator:
        for instance in page["PriceList"]:
            try:
                instance_attr = json.loads(instance)["product"]["attributes"]

                # memory comes in formatted like: 1,952.00 GiB
                memory = float(instance_attr.get("memory", 0)[:-4].replace(",", ""))
                vcpu = int(instance_attr.get("vcpu", 0))

                instances[instance_attr["instanceType"]] = {
                    "memory": memory,
                    "vcpu": vcpu,
                }
            except ValueError:
                logger.error(
                    _(
                        "Could not fetch EC2 definition for instance-type "
                        "%(instance_type)s, memory %(memory)s, vcpu %(vcpu)s."
                    ),
                    {
                        "instance_type": instance_attr["instanceType"],
                        "memory": instance_attr.get("memory", 0),
                        "vcpu": instance_attr.get("vcpu", 0),
                    },
                )
    return instances


def _save_ec2_instance_type_definitions(definitions):
    """
    Save AWS EC2 instance type definitions to our database.

    Note:
        If an instance type name already exists in the DB, do NOT overwrite it.

    Args:
        definitions (dict): dict of dicts where the outer key is the instance
            type name and the inner dict has keys memory and vcpu. For example:
            {'r5.large': {'memory': 24.0, 'vcpu': 1}}

    Returns:
        None

    """
    for name, attributes in definitions.items():
        try:
            obj, created = AwsEC2InstanceDefinition.objects.get_or_create(
                instance_type=name,
                defaults={"memory": attributes["memory"], "vcpu": attributes["vcpu"]},
            )
            if created:
                logger.info(_("Saving new instance type %s"), obj.instance_type)
            else:
                logger.info(_("Instance type %s already exists."), obj.instance_type)
        except IntegrityError as e:
            logger.exception(
                _(
                    "Failed to get_or_create an AwsEC2InstanceDefinition("
                    'name="%(name)s", memory=%(memory)s, vcpu=%(vcpu)s'
                    "); this should never happen."
                ),
                {
                    "name": name,
                    "memory": attributes["memory"],
                    "vcpu": attributes["vcpu"],
                },
            )
            raise e
