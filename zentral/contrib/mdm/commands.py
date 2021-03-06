import plistlib
import uuid
from django.http import HttpResponse
from django.urls import reverse
from zentral.conf import settings
from .payloads import build_payload, build_profile, get_payload_identifier


def build_command_response(request_type, content, command_uuid=None):
    if command_uuid is None:
        command_uuid = uuid.uuid4()
    content["RequestType"] = request_type
    command = {"CommandUUID": str(command_uuid),
               "Command": content}
    return HttpResponse(plistlib.dumps(command),
                        content_type="application/xml; charset=UTF-8")


DEVICE_INFORMATION_QUERIES = [
    # General
    "UDID",
    "Languages",
    "Locales",
    "DeviceID",
    "OrganizationInfo",
    "LastCloudBackupDate",
    "AwaitingConfiguration",
    "AutoSetupAdminAccounts",

    # iTunes - Needs Install Applications access right
    "iTunesStoreAccountIsActive",
    "iTunesStoreAccountHash",

    # Device Information
    "DeviceName",
    "OSVersion",
    "BuildVersion",
    "ModelName",
    "Model",
    "ProductName",
    "SerialNumber",
    "DeviceCapacity",
    "AvailableDeviceCapacity",
    "BatteryLevel",
    "CellularTechnology",
    "IMEI",
    "MEID",
    "ModemFirmwareVersion",
    "IsSupervised",
    "IsDeviceLocatorServiceEnabled",
    "IsActivationLockEnabled",
    "IsDoNotDisturbInEffect",
    "DeviceID",
    "EASDeviceIdentifier",
    "IsCloudBackupEnabled",
    "OSUpdateSettings",
    "LocalHostName",
    "HostName",
    "SystemIntegrityProtectionEnabled",
    "ActiveManagedUsers",
    "IsMDMLostModeEnabled",
    "MaximumResidentUsers",

    # OS update
    "CatalogURL",
    "IsDefaultCatalog",
    "PreviousScanDate",
    "PreviousScanResult",
    "PerformPeriodicCheck",
    "AutomaticCheckEnabled",
    "BackgroundDownloadEnabled",
    "AutomaticAppInstallationEnabled",
    "AutomaticOSInstallationEnabled",
    "AutomaticSecurityUpdatesEnabled"
]


def build_device_information_command_response():
    return build_command_response("DeviceInformation", {"Queries": DEVICE_INFORMATION_QUERIES})


def build_install_profile_command_response(artifact, command_uuid):
    artifact_suffix = artifact.get_configuration_profile_payload_identifier_suffix()
    payloads = []
    for idx, (payload_type, payload_name, payload_content) in enumerate(artifact.get_payloads()):
        payloads.append(build_payload(payload_type, payload_name,
                                      "{}.{}".format(artifact_suffix, idx + 1), payload_content,
                                      payload_version=artifact.version))
    command_payload = build_profile(str(artifact), artifact_suffix, payloads)
    return build_command_response("InstallProfile", {"Payload": command_payload}, command_uuid)


def build_remove_profile_command_response(artifact, command_uuid):
    artifact_suffix = artifact.get_configuration_profile_payload_identifier_suffix()
    identifier = get_payload_identifier(artifact_suffix)
    return build_command_response("RemoveProfile", {"Identifier": identifier}, command_uuid)


def build_install_application_command_response(command_uuid):
    manifest_url = "{}{}".format(settings["api"]["tls_hostname"],
                                 reverse("mdm:install_application_manifest", args=(str(command_uuid),)))
    return build_command_response("InstallApplication",
                                  {"ManifestURL": manifest_url,
                                   # Remove app when MDM profile is removed:
                                   # TODO: make it configurable ?
                                   "ManagementFlags": 1},
                                  command_uuid)
