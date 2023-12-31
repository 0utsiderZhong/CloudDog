import json
from abc import ABC

from alibabacloud_alb20200616 import models as alb_20200616_models
from alibabacloud_alb20200616.client import Client as AlbApiClient
from alibabacloud_cas20200630 import models as cas_20200630_models
from alibabacloud_cas20200630.client import Client as casApiClient
from alibabacloud_cloudfw20171207 import models as cloudfw_20171207_models
from alibabacloud_cloudfw20171207.client import Client as CfwApiClient
from alibabacloud_ecs20140526 import models as ecs_20140526_models
from alibabacloud_ecs20140526.client import Client as EcsApiClient
from alibabacloud_r_kvstore20150101 import models as r_kvstore_20150101_models
from alibabacloud_r_kvstore20150101.client import Client as R_kvstoreApiClient
from alibabacloud_rds20140815 import models as rds_20140815_models
from alibabacloud_rds20140815.client import Client as RdsApiClient
from alibabacloud_sas20181203 import models as sas_20181203_models
from alibabacloud_sas20181203.client import Client as CscApiClient
from alibabacloud_slb20140515 import models as slb_20140515_models
from alibabacloud_slb20140515.client import Client as SlbApiClient
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient
from alibabacloud_vpc20160428 import models as vpc_20160428_models
from alibabacloud_vpc20160428.client import Client as VpcApiClient
from alibabacloud_waf_openapi20211001 import models as waf_openapi_20211001_models
from alibabacloud_waf_openapi20211001.client import Client as WAFApiClient

from config import settings
from cron.base_cron.views import DjangoJobViewSet
from message.models import Event
from message.views import send_message
from product.alibabacloud_product.models import *
from project.models import Project
from utils import set_api_client_config

logger = logging.getLogger('clouddog')


# cron: sunday 01:10AM exec the job
# @register_job(scheduler, 'cron', day_of_week='sun', hour='1', minute='10', id='get_ali_ecs_api_response')
def get_ecs_api_response() -> None:
    project_list = (Project.objects.filter(status='Running',
                                           project_access_key__isnull=False,
                                           project_secret_key__isnull=False,
                                           cron_toggle=True).
                    values('project_access_key', 'project_secret_key', 'region', 'project_name', 'id'))
    runtime = util_models.RuntimeOptions()
    for project in project_list:
        client = EcsApiClient(set_api_client_config(project['project_access_key'],
                                                    project['project_secret_key'],
                                                    settings.ENDPOINT['ECS_ENDPOINT']['mainland']))
        for region in project['region']:
            describe_instances_request = ecs_20140526_models.DescribeInstancesRequest(region_id=region)
            try:
                # API Ref: https://next.api.aliyun.com/document/Ecs/2014-05-26/DescribeInstances
                describe_instance_response = client.describe_instances_with_options(describe_instances_request, runtime)
                describe_instance_response_to_str = UtilClient.to_jsonstring(describe_instance_response)
                describe_instance_response_json_obj = json.loads(describe_instance_response_to_str)
                instance_list = describe_instance_response_json_obj['body']['Instances']['Instance']
                for instance in instance_list:
                    describe_instance_auto_renew_attribute_request = ecs_20140526_models.DescribeInstanceAutoRenewAttributeRequest(region_id=region, instance_id=instance['InstanceId'])
                    # API Ref: https://next.api.aliyun.com/document/Ecs/2014-05-26/DescribeInstanceAutoRenewAttribute
                    describe_instance_auto_renew_attribute_response = client.describe_instance_auto_renew_attribute_with_options(describe_instance_auto_renew_attribute_request, runtime)
                    describe_instance_auto_renew_attribute_response_to_str = UtilClient.to_jsonstring(describe_instance_auto_renew_attribute_response)
                    describe_instance_auto_renew_attribute_response_json_obj = json.loads(describe_instance_auto_renew_attribute_response_to_str)
                    instance_auto_renew_info = describe_instance_auto_renew_attribute_response_json_obj['body']['InstanceRenewAttributes']['InstanceRenewAttribute'][0]
                    # request 2 API and get two request id, so the new request id is formed by combining two request id
                    request_id = describe_instance_response_json_obj['body']['RequestId'] + " " + describe_instance_auto_renew_attribute_response_json_obj['body']['RequestId']
                    ecs = AlibabacloudEcsApiResponse(api_request_id=request_id,
                                                     instance_id=instance['InstanceId'],
                                                     project_name=project['project_name'],
                                                     instance_name=instance['InstanceName'],
                                                     project_id=project['id'],
                                                     region_id=instance['RegionId'],
                                                     ecs_status=instance['Status'],
                                                     ram=instance['Memory'],
                                                     osname=instance['OSName'],
                                                     instance_type=instance['InstanceType'],
                                                     zone_id=instance['ZoneId'],
                                                     cpu=instance['Cpu'],
                                                     instance_charge_type=instance['InstanceChargeType'],
                                                     internet_charge_type=instance['InternetChargeType'],
                                                     expired_time=instance['ExpiredTime'],
                                                     stopped_mode=instance['StoppedMode'],
                                                     start_time=instance['StartTime'],
                                                     auto_release_time=instance['AutoReleaseTime'],
                                                     lock_reason=instance['OperationLocks']['LockReason'],
                                                     auto_renew_enabled=instance_auto_renew_info['AutoRenewEnabled'],
                                                     renewal_status=instance_auto_renew_info['RenewalStatus'],
                                                     period_init=instance_auto_renew_info['PeriodUnit'],
                                                     duration=instance_auto_renew_info['Duration'],
                                                     )
                    logger.info(ecs.get_basic_info())
                    ecs.save()
                    if ecs.ecs_status != "Running":
                        message = "project {} ecs {} status is no Running".format(project['project_name'], instance['InstanceId'])
                        event = Event(
                            project_name=project['project_name'],
                            event_type="exception",
                            instance_id=instance['InstanceId'],
                            product_type='ecs',
                            event_message=message)
                        event.save()
                        send_message(event)
                        logger.info(message)
            except Exception as error:
                UtilClient.assert_as_string(error)


# cron: sunday 01:20AM exec the job
# @register_job(scheduler, 'cron', day_of_week='sun', hour='1', minute='20', id='get_ali_waf_api_response')
def get_waf_api_response() -> None:
    project_list = (Project.objects.filter(status='Running',
                                           project_access_key__isnull=False,
                                           project_secret_key__isnull=False,
                                           cron_toggle=True).
                    values('project_access_key', 'project_secret_key', 'region', 'project_name', 'id'))
    runtime = util_models.RuntimeOptions()
    for project in project_list:
        for endpoint in settings.ENDPOINT['WAF_ENDPOINT']:
            client = WAFApiClient(set_api_client_config(project['project_access_key'],
                                                        project['project_secret_key'],
                                                        settings.ENDPOINT['WAF_ENDPOINT'][endpoint]))
            describe_instance_info_request = waf_openapi_20211001_models.DescribeInstanceRequest()
            try:
                # 复制代码运行请自行打印 API 的返回值
                res = client.describe_instance_with_options(describe_instance_info_request, runtime)
                describe_waf_attribute_response_to_str = UtilClient.to_jsonstring(res)
                describe_waf_attribute_response_json_obj = json.loads(describe_waf_attribute_response_to_str)
                waf_info = describe_waf_attribute_response_json_obj['body']
                waf = AlibabacloudWafApiResponse(api_request_id=waf_info['RequestId'],
                                                 instance_id=waf_info['InstanceId'],
                                                 project_name=project['project_name'],
                                                 project_id=project['id'],
                                                 waf_status=waf_info['Status'],
                                                 end_time=waf_info['EndTime'],
                                                 edition=waf_info['Edition'],
                                                 region=waf_info['RegionId'],
                                                 pay_type=waf_info['PayType'],
                                                 in_debt=waf_info['InDebt'],
                                                 start_time=waf_info['StartTime'],
                                                 )
                logger.info(waf.get_basic_info())
                waf.save()
                if waf.waf_status != 1:
                    message = "project {} waf {} status is no Running".format(project['project_name'], waf_info['Status'])
                    event = Event(
                        project_name=project['project_name'],
                        event_type="exception",
                        instance_id=waf_info['InstanceId'],
                        product_type='waf',
                        event_message=message)
                    event.save()
                    send_message(event)
                    logger.info(message)
            except Exception as error:
                UtilClient.assert_as_string(error)


# @register_job(scheduler, 'cron', day_of_week='sun', hour='1', minute='30', id='get_ali_slb_api_response')
def get_slb_api_response() -> None:
    project_list = (Project.objects.filter(status='Running',
                                           project_access_key__isnull=False,
                                           project_secret_key__isnull=False,
                                           cron_toggle=True).
                    values('project_access_key', 'project_secret_key', 'region', 'project_name', 'id'))
    runtime = util_models.RuntimeOptions()
    for project in project_list:
        client = SlbApiClient(set_api_client_config(project['project_access_key'],
                                                    project['project_secret_key'],
                                                    settings.ENDPOINT['SLB_ENDPOINT']['general']))
        for region in project['region']:
            describe_load_balancers_request = slb_20140515_models.DescribeLoadBalancersRequest(region_id=region)
            try:
                res = client.describe_load_balancers_with_options(describe_load_balancers_request, runtime)
                describe_slb_attribute_response_to_str = UtilClient.to_jsonstring(res)
                describe_slb_attribute_response_json_obj = json.loads(describe_slb_attribute_response_to_str)
                if describe_slb_attribute_response_json_obj['body']['TotalCount'] > 0:
                    slb_info = describe_slb_attribute_response_json_obj['body']['LoadBalancers']
                    for num, slb_instance in enumerate(slb_info):
                        describe_load_balancer_attribute_request = slb_20140515_models.DescribeLoadBalancerAttributeRequest(region_id=region, load_balancer_id=slb_instance['InstanceId'])
                        detail_res = client.describe_load_balancer_attribute_with_options(describe_load_balancer_attribute_request, runtime)
                        describe_slb_detail_attribute_response_to_str = UtilClient.to_jsonstring(detail_res)
                        describe_slb_detail_attribute_response_json_obj = json.loads(describe_slb_detail_attribute_response_to_str)
                        slb_instance_detail = describe_slb_detail_attribute_response_json_obj['body']
                        slb = AlibabacloudSLBApiResponse(api_request_id=(describe_slb_attribute_response_json_obj['body']['RequestId'] + str(num)),
                                                         instance_id=slb_instance['InstanceId'],
                                                         project_name=project['project_name'],
                                                         project_id=project['id'],
                                                         bandwidth=slb_instance_detail['Bandwidth'],
                                                         end_time_stamp=slb_instance_detail['EndTimeStamp'],
                                                         end_time=slb_instance_detail['EndTime'],
                                                         auto_release_time=slb_instance_detail['AutoReleaseTime'],
                                                         renewal_status=slb_instance_detail['RenewalStatus'],
                                                         renewal_duration=slb_instance_detail['RenewalDuration'],
                                                         renewal_cyc_unit=slb_instance_detail['RenewalCycUnit'],
                                                         create_time=slb_instance['CreateTime'],
                                                         pay_type=slb_instance['PayType'],
                                                         internet_charge_type=slb_instance['InternetChargeType'],
                                                         load_balancer_name=slb_instance['LoadBalancerName'],
                                                         address=slb_instance['Address'],
                                                         address_type=slb_instance['AddressType'],
                                                         address_ip_version=slb_instance['AddressIPVersion'],
                                                         region_id=slb_instance['RegionId'],
                                                         load_balancer_status=slb_instance['LoadBalancerStatus'],
                                                         load_balancer_spec=slb_instance['LoadBalancerSpec'],
                                                         instance_charge_type=slb_instance['InstanceChargeType'],
                                                         master_zone_id=slb_instance['MasterZoneId'],
                                                         slave_zone_id=slb_instance['SlaveZoneId'],
                                                         )
                        logger.info(slb.get_basic_info())
                        slb.save()
                        if slb.load_balancer_status != 'active':
                            message = "project {} slb {} status is no active".format(project['project_name'], slb_info['LoadBalancerStatus'])
                            event = Event(
                                project_name=project['project_name'],
                                event_type="exception",
                                instance_id=slb_info['InstanceId'],
                                product_type='slb',
                                event_message=message)
                            event.save()
                            send_message(event)
                            logger.info(message)
            except Exception as error:
                UtilClient.assert_as_string(error)


# @register_job(scheduler, 'cron', day_of_week='sun', hour='1', minute='40', id='get_ali_alb_api_response')
def get_alb_api_response() -> None:
    project_list = (Project.objects.filter(status='Running',
                                           project_access_key__isnull=False,
                                           project_secret_key__isnull=False,
                                           cron_toggle=True).
                    values('project_access_key', 'project_secret_key', 'region', 'project_name', 'id'))
    runtime = util_models.RuntimeOptions()
    for project in project_list:
        for region in project['region']:
            client = AlbApiClient(set_api_client_config(project['project_access_key'],
                                                        project['project_secret_key'],
                                                        settings.ENDPOINT['ALB_ENDPOINT'][region]))
            list_load_balancers_request = alb_20200616_models.ListLoadBalancersRequest()
            try:
                res = client.list_load_balancers_with_options(list_load_balancers_request, runtime)
                describe_alb_attribute_response_to_str = UtilClient.to_jsonstring(res)
                describe_alb_attribute_response_json_obj = json.loads(describe_alb_attribute_response_to_str)
                if describe_alb_attribute_response_json_obj['body']['TotalCount'] > 0:
                    alb_info = describe_alb_attribute_response_json_obj['body']['LoadBalancers']
                    alb = AlibabacloudALBApiResponse(api_request_id=describe_alb_attribute_response_json_obj['body']['RequestId'],
                                                     instance_id=alb_info['LoadBalancerId'],
                                                     project_name=project['project_name'],
                                                     project_id=project['id'],
                                                     create_time=alb_info['CreateTime'],
                                                     address_allocated_mode=alb_info['AddressAllocatedMode'],
                                                     address_type=alb_info['AddressType'],
                                                     dns_name=alb_info['DNSName'],
                                                     pay_type=alb_info['PayType'],
                                                     load_balancer_bussiness_status=alb_info['LoadBalancerBussinessStatus'],
                                                     load_balancer_edition=alb_info['LoadBalancerEdition'],
                                                     load_balancer_name=alb_info['LoadBalancerName'],
                                                     load_balancer_status=alb_info['LoadBalancerStatus'],
                                                     address_ip_version=alb_info['AddressIPVersion'],
                                                     ipv6_address_type=alb_info['Ipv6AddressType'],
                                                     )
                    logger.info(alb.get_basic_info())
                    alb.save()
                    if alb.load_balancer_status != 'Active':
                        message = "project {} alb {} status is no active".format(project['project_name'], alb_info['LoadBalancerStatus'])
                        event = Event(
                            project_name=project['project_name'],
                            event_type="exception",
                            instance_id=alb_info['InstanceId'],
                            product_type='alb',
                            event_message=message)
                        event.save()
                        send_message(event)
                        logger.info(message)
            except Exception as error:
                UtilClient.assert_as_string(error)


# @register_job(scheduler, 'cron', day_of_week='sun', hour='1', minute='50', id='get_ali_eip_api_response')
def get_eip_api_response() -> None:
    project_list = (Project.objects.filter(status='Running',
                                           project_access_key__isnull=False,
                                           project_secret_key__isnull=False,
                                           cron_toggle=True).
                    values('project_access_key', 'project_secret_key', 'region', 'project_name', 'id'))
    runtime = util_models.RuntimeOptions()
    for project in project_list:
        for region in project['region']:
            client = VpcApiClient(set_api_client_config(project['project_access_key'],
                                                        project['project_secret_key'],
                                                        settings.ENDPOINT['VPC_ENDPOINT'][region]))
            describe_eip_addresses_request = vpc_20160428_models.DescribeEipAddressesRequest(region_id=region)
            try:
                res = client.describe_eip_addresses_with_options(describe_eip_addresses_request, runtime)
                describe_eip_attribute_response_to_str = UtilClient.to_jsonstring(res)
                describe_eip_attribute_response_json_obj = json.loads(describe_eip_attribute_response_to_str)
                if describe_eip_attribute_response_json_obj['body']['TotalCount'] > 0:
                    eip_info = describe_eip_attribute_response_json_obj['body']['EipAddresses']
                    for num, eip_instance in enumerate(eip_info):
                        eip = AlibabacloudEIPApiResponse(api_request_id=(describe_eip_attribute_response_json_obj['body']['RequestId'] + str(num)),
                                                         instance_id=eip_instance['InstanceId'],
                                                         project_name=project['project_name'],
                                                         project_id=project['id'],
                                                         name=eip_instance['Name'],
                                                         region_id=eip_instance['RegionId'],
                                                         expired_time=eip_instance['ExpiredTime'],
                                                         allocation_id=eip_instance['AllocationId'],
                                                         instance_type=eip_instance['InstanceType'],
                                                         internet_charge_type=eip_instance['InternetChargeType'],
                                                         business_status=eip_instance['BusinessStatus'],
                                                         reservation_bandwidth=eip_instance['ReservationBandwidth'],
                                                         bandwidth=eip_instance['Bandwidth'],
                                                         ip_address=eip_instance['IpAddress'],
                                                         reservation_internet_charge_type=eip_instance['ReservationInternetChargeType'],
                                                         charge_type=eip_instance['ChargeType'],
                                                         net_mode=eip_instance['Netmode'],
                                                         allocation_time=eip_instance['AllocationTime'],
                                                         status=eip_instance['Status'],
                                                         reservation_active_time=eip_instance['ReservationActiveTime'],
                                                         )
                        logger.info(eip.get_basic_info())
                        eip.save()
                        if eip.status != 'Associating':
                            message = "project {} eip {} status is no Associating".format(project['project_name'], eip_instance['Status'])
                            event = Event(
                                project_name=project['project_name'],
                                event_type="exception",
                                instance_id=eip_instance['InstanceId'],
                                product_type='eip',
                                event_message=message)
                            event.save()
                            send_message(event)
                            logger.info(message)
            except Exception as error:
                UtilClient.assert_as_string(error)


# @register_job(scheduler, 'cron', day_of_week='sun', hour='1', minute='55', id='get_ali_ssl_api_response')
def get_ssl_api_response() -> None:
    project_list = (Project.objects.filter(status='Running',
                                           project_access_key__isnull=False,
                                           project_secret_key__isnull=False,
                                           cron_toggle=True).
                    values('project_access_key', 'project_secret_key', 'region', 'project_name', 'id'))
    runtime = util_models.RuntimeOptions()
    for project in project_list:
        for endpoint in settings.ENDPOINT['SSL_ENDPOINT']:
            client = casApiClient(set_api_client_config(project['project_access_key'],
                                                        project['project_secret_key'],
                                                        settings.ENDPOINT['SSL_ENDPOINT'][endpoint]))
            list_client_certificate_request = cas_20200630_models.ListClientCertificateRequest()
            try:
                res = client.list_client_certificate_with_options(list_client_certificate_request, runtime)
                describe_ssl_attribute_response_to_str = UtilClient.to_jsonstring(res)
                describe_ssl_attribute_response_json_obj = json.loads(describe_ssl_attribute_response_to_str)
                if describe_ssl_attribute_response_json_obj['body']['TotalCount'] > 0:
                    ssl_info = describe_ssl_attribute_response_json_obj['body']['CertificateList']
                    for num, ssl_instance in enumerate(ssl_info):
                        ssl = AlibabacloudSSLApiResponse(api_request_id=(describe_ssl_attribute_response_json_obj['body']['RequestId'] + str(num)),
                                                         instance_id=ssl_instance['Identifier'],
                                                         project_name=project['project_name'],
                                                         project_id=project['id'],
                                                         subject_dn=ssl_instance['SubjectDN'],
                                                         common_name=ssl_instance['CommonName'],
                                                         organization_unit=ssl_instance['OrganizationUnit'],
                                                         organization=ssl_instance['Organization'],
                                                         status=ssl_instance['Status'],
                                                         BeforeDate=ssl_instance['BeforeDate'],
                                                         AfterDate=ssl_instance['AfterDate'],
                                                         days=ssl_instance['Days'],
                                                         )
                        logger.info(ssl.get_basic_info())
                        ssl.save()
                        if ssl.status != 'ISSUE':
                            message = "project {} ssl certificate {} status is REVOKE".format(project['project_name'], ssl_instance['Status'])
                            event = Event(
                                project_name=project['project_name'],
                                event_type="exception",
                                instance_id=ssl_instance['Identifier'],
                                product_type='ssl',
                                event_message=message)
                            event.save()
                            send_message(event)
                            logger.info(message)
            except Exception as error:
                UtilClient.assert_as_string(error)


# @register_job(scheduler, 'cron', day_of_week='sun', hour='2', minute='00', id='get_ali_csc_api_response')
def get_csc_api_response() -> None:
    project_list = (Project.objects.filter(status='Running',
                                           project_access_key__isnull=False,
                                           project_secret_key__isnull=False,
                                           cron_toggle=True).
                    values('project_access_key', 'project_secret_key', 'region', 'project_name', 'id'))
    runtime = util_models.RuntimeOptions()
    for project in project_list:
        for endpoint in settings.ENDPOINT['CSC_ENDPOINT']:
            client = CscApiClient(set_api_client_config(project['project_access_key'],
                                                        project['project_secret_key'],
                                                        settings.ENDPOINT['CSC_ENDPOINT'][endpoint]))
            describe_version_config_request = sas_20181203_models.DescribeVersionConfigRequest()
            try:
                # https://next.api.aliyun.com/api/Sas/2018-12-03/DescribeVersionConfig
                res = client.describe_version_config_with_options(describe_version_config_request, runtime)
                describe_csc_attribute_response_to_str = UtilClient.to_jsonstring(res)
                describe_csc_attribute_response_json_obj = json.loads(describe_csc_attribute_response_to_str)
                csc_info = describe_csc_attribute_response_json_obj['body']
                csc = AlibabacloudSSLApiResponse(api_request_id=(describe_csc_attribute_response_json_obj['body']['RequestId']),
                                                 instance_id=csc_info['InstanceId'],
                                                 project_name=project['project_name'],
                                                 project_id=project['id'],
                                                 mv_auth_count=csc_info['MVAuthCount'],
                                                 sas_log=csc_info['SasLog'],
                                                 sas_screen=csc_info['SasScreen'],
                                                 honeypot_capacity=csc_info['HoneypotCapacity'],
                                                 mv_unused_auth_count=csc_info['MVUnusedAuthCount'],
                                                 web_lock=csc_info['WebLock'],
                                                 app_white_list_auth_count=csc_info['AppWhiteListAuthCount'],
                                                 last_trail_end_time=csc_info['LastTrailEndTime'],
                                                 version=csc_info['Version'],
                                                 web_lock_auth_count=csc_info['WebLockAuthCount'],
                                                 release_time=csc_info['ReleaseTime'],
                                                 highest_version=csc_info['HighestVersion'],
                                                 asset_level=csc_info['AssetLevel'],
                                                 is_over_balance=csc_info['IsOverBalance'],
                                                 sls_capacity=csc_info['SlsCapacity'],
                                                 vm_cores=csc_info['VmCores'],
                                                 allow_partial_buy=csc_info['AllowPartialBuy'],
                                                 app_white_list=csc_info['AppWhiteList'],
                                                 image_scan_capacity=csc_info['ImageScanCapacity'],
                                                 is_trial_version=csc_info['IsTrialVersion'],
                                                 user_defined_alarms=csc_info['UserDefinedAlarms'],
                                                 open_time=csc_info['OpenTime'],
                                                 is_new_container_version=csc_info['IsNewContainerVersion'],
                                                 is_new_multi_version=csc_info['IsNewMultiVersion'],
                                                 threat_analysis_capacity=csc_info['ThreatAnalysisCapacity'],
                                                 cspm_capacity=csc_info['CspmCapacity'],
                                                 vul_fix_capacity=csc_info['VulFixCapacity'],
                                                 )
                logger.info(csc.get_basic_info())
                csc.save()
            except Exception as error:
                UtilClient.assert_as_string(error)


# @register_job(scheduler, 'cron', day_of_week='sun', hour='2', minute='00', id='get_ali_rds_api_response')
def get_rds_api_response() -> None:
    project_list = (Project.objects.filter(status='Running',
                                           project_access_key__isnull=False,
                                           project_secret_key__isnull=False).
                    values('project_access_key', 'project_secret_key', 'region', 'project_name', 'id'))
    runtime = util_models.RuntimeOptions()
    rds_total_count = 0
    for project in project_list:
        for endpoint in settings.ENDPOINT['RDS_ENDPOINT']:
            client = RdsApiClient(set_api_client_config(project['project_access_key'],
                                                        project['project_secret_key'],
                                                        settings.ENDPOINT['RDS_ENDPOINT'][endpoint]))
            for region in project['region']:
                describe_db_instances_request = rds_20140815_models.DescribeDBInstancesRequest(region_id=region)
                try:
                    # https://next.api.aliyun.com/api/Rds/2014-08-15/DescribeDBInstances
                    db_list_res = client.describe_dbinstances_with_options(describe_db_instances_request, runtime)
                    describe_rds_attribute_response_to_str = UtilClient.to_jsonstring(db_list_res)
                    describe_rds_attribute_response_json_obj = json.loads(describe_rds_attribute_response_to_str)
                    rds_list = describe_rds_attribute_response_json_obj['Items']
                    rds_total_count += len(rds_list)
                    for rds_instance in rds_list:
                        # https://next.api.aliyun.com/api/Rds/2014-08-15/DescribeDBInstanceAttribute
                        describe_db_instance_detail = rds_20140815_models.DescribeDBInstanceAttributeRequest(dbinstance_id=rds_instance['DBInstanceId'])
                        db_instance_detail_res = client.describe_dbinstance_attribute_with_options(describe_db_instance_detail, runtime)
                        describe_rds_attribute_detail_response_to_str = UtilClient.to_jsonstring(db_instance_detail_res)
                        db_instance_detail = json.loads(describe_rds_attribute_detail_response_to_str)
                        request_id = describe_rds_attribute_response_json_obj['body']['RequestId'] + " " + db_instance_detail['body']['RequestId']
                        rds = AlibabacloudRDSApiResponse(api_request_id=request_id,
                                                         instance_id=rds_instance['InstanceId'],
                                                         project_name=project['project_name'],
                                                         project_id=project['id'],
                                                         master_instance_id=rds_instance['MasterInstanceId'],
                                                         guard_db_instance_id=rds_instance['GuardDBInstanceId'],
                                                         db_instance_description=rds_instance['DBInstanceDescription'],
                                                         engine=rds_instance['Engine'],
                                                         db_instance_status=rds_instance['DBInstanceStatus'],
                                                         db_instance_type=rds_instance['DBInstanceType'],
                                                         category=rds_instance['Category'],
                                                         db_instance_class_type=db_instance_detail['DBInstanceClassType'],  # detail
                                                         db_instance_storage=db_instance_detail['DBInstanceStorage'],  # detail
                                                         db_instance_memory=db_instance_detail['DBInstanceMemory'],  # detail
                                                         db_instance_cpu=db_instance_detail['DBInstanceCPU'],  # detail
                                                         region_id=rds_instance['RegionId'],
                                                         instance_network_type=rds_instance['InstanceNetworkType'],
                                                         db_instance_net_type=rds_instance['DBInstanceNetType'],
                                                         db_instance_class=rds_instance['DBInstanceClass'],
                                                         engine_version=rds_instance['EngineVersion'],
                                                         pay_type=rds_instance['PayType'],
                                                         connection_mode=rds_instance['ConnectionMode'],
                                                         connection_string=rds_instance['ConnectionString'],
                                                         create_time=rds_instance['CreateTime'],
                                                         expire_time=rds_instance['ExpireTime'],
                                                         destroy_time=rds_instance['DestroyTime'],
                                                         lock_mode=rds_instance['LockMode'],
                                                         lock_reason=rds_instance['LockReason'],
                                                         )
                        logger.info(rds.get_basic_info())
                        rds.save()
                except Exception as error:
                    UtilClient.assert_as_string(error)


# @register_job(scheduler, 'cron', day_of_week='sun', hour='2', minute='00', id='get_ali_redis_api_response')
def get_redis_api_response() -> None:
    project_list = (Project.objects.filter(status='Running',
                                           project_access_key__isnull=False,
                                           project_secret_key__isnull=False).
                    values('project_access_key', 'project_secret_key', 'region', 'project_name', 'id'))
    runtime = util_models.RuntimeOptions()
    redis_total_count = 0
    for project in project_list:
        for endpoint in settings.ENDPOINT['REDIS_ENDPOINT']:
            client = R_kvstoreApiClient(set_api_client_config(project['project_access_key'],
                                                              project['project_secret_key'],
                                                              settings.ENDPOINT['REDIS_ENDPOINT'][endpoint]))
            for region in project['region']:
                describe_instances_request = r_kvstore_20150101_models.DescribeInstancesRequest(region_id=region)
                try:
                    # https://next.api.aliyun.com/api/R-kvstore/2015-01-01/DescribeInstances
                    redis_list_res = client.describe_instances_with_options(describe_instances_request, runtime)
                    describe_redis_attribute_response_to_str = UtilClient.to_jsonstring(redis_list_res)
                    describe_redis_attribute_response_json_obj = json.loads(describe_redis_attribute_response_to_str)
                    redis_list = describe_redis_attribute_response_json_obj['body']['Instances']
                    redis_total_count += len(redis_list)
                    for num, redis_instance in enumerate(redis_list):
                        redis = AlibabacloudRedisApiResponse(api_request_id=(describe_redis_attribute_response_json_obj['body']['RequestId'] + str(num)),
                                                             instance_id=redis_instance['InstanceId'],
                                                             project_name=project['project_name'],
                                                             project_id=project['id'],
                                                             private_ip=redis_instance['PrivateIp'],
                                                             capacity=redis_instance['Capacity'],
                                                             architecture_type=redis_instance['ArchitectureType'],
                                                             network_type=redis_instance['NetworkType'],
                                                             bandwidth=redis_instance['Bandwidth'],
                                                             instance_name=redis_instance['InstanceName'],
                                                             shard_count=redis_instance['ShardCount'],
                                                             user_name=redis_instance['UserName'],
                                                             instance_class=redis_instance['InstanceClass'],
                                                             instance_type=redis_instance['InstanceType'],
                                                             instance_status=redis_instance['InstanceStatus'],
                                                             region_id=redis_instance['RegionId'],
                                                             engine_version=redis_instance['EngineVersion'],
                                                             charge_type=redis_instance['ChargeType'],
                                                             connection_mode=redis_instance['ConnectionMode'],
                                                             connection_domain=redis_instance['ConnectionDomain'],
                                                             create_time=redis_instance['CreateTime'],
                                                             expire_time=redis_instance['ExpireTime'],
                                                             destroy_time=redis_instance['DestroyTime'],
                                                             )
                        logger.info(redis.get_basic_info())
                        redis.save()
                except Exception as error:
                    UtilClient.assert_as_string(error)


# @register_job(scheduler, 'cron', day_of_week='sun', hour='2', minute='00', id='get_ali_cfw_api_response')
def get_cfw_api_response() -> None:
    project_list = (Project.objects.filter(status='Running',
                                           project_access_key__isnull=False,
                                           project_secret_key__isnull=False).
                    values('project_access_key', 'project_secret_key', 'region', 'project_name', 'id'))
    runtime = util_models.RuntimeOptions()
    cfw_total_count = 0
    for project in project_list:
        for endpoint in settings.ENDPOINT['CFW_ENDPOINT']:
            client = CfwApiClient(set_api_client_config(project['project_access_key'],
                                                        project['project_secret_key'],
                                                        settings.ENDPOINT['CFW_ENDPOINT'][endpoint]))
            describe_vpc_firewall_list_request = cloudfw_20171207_models.DescribeVpcFirewallListRequest()
            try:
                # https://next.api.aliyun.com/api/Cloudfw/2017-12-07/DescribeVpcFirewallList
                cfw_list_res = client.describe_vpc_firewall_list_with_options(describe_vpc_firewall_list_request, runtime)
                describe_redis_attribute_response_to_str = UtilClient.to_jsonstring(cfw_list_res)
                describe_redis_attribute_response_json_obj = json.loads(describe_redis_attribute_response_to_str)
                cfw_list = describe_redis_attribute_response_json_obj['body']['VpcFirewalls']
                cfw_total_count += describe_redis_attribute_response_json_obj['body']['TotalCount']
                if cfw_total_count > 0:
                    for num, cfw_instance in enumerate(cfw_list):
                        cfw = AlibabacloudCFWApiResponse(api_request_id=(describe_redis_attribute_response_json_obj['body']['RequestId'] + str(num)),
                                                         instance_id=cfw_instance['InstanceId'],
                                                         project_name=project['project_name'],
                                                         project_id=project['id'],
                                                         connect_type=cfw_instance['ConnectType'],
                                                         region_status=cfw_instance['RegionStatus'],
                                                         bandwidth=cfw_instance['Bandwidth'],
                                                         vpc_firewall_name=cfw_instance['VpcFirewallName'],
                                                         firewall_switch_status=cfw_instance['FirewallSwitchStatus'],
                                                         )
                        logger.info(cfw.get_basic_info())
                        cfw.save()
            except Exception as error:
                UtilClient.assert_as_string(error)


class AliECSDjangoJobViewSet(DjangoJobViewSet, ABC):
    def custom_job(self):
        get_ecs_api_response()


class AliWAFDjangoJobViewSet(DjangoJobViewSet, ABC):
    def custom_job(self):
        get_waf_api_response()


class AliSLBDjangoJobViewSet(DjangoJobViewSet, ABC):
    def custom_job(self):
        get_slb_api_response()


class AliALBDjangoJobViewSet(DjangoJobViewSet, ABC):
    def custom_job(self):
        get_alb_api_response()


class AliEIPDjangoJobViewSet(DjangoJobViewSet, ABC):
    def custom_job(self):
        get_eip_api_response()


class AliSSLDjangoJobViewSet(DjangoJobViewSet, ABC):
    def custom_job(self):
        get_ssl_api_response()


class AliCSCDjangoJobViewSet(DjangoJobViewSet, ABC):
    def custom_job(self):
        get_csc_api_response()


class AliRDSDjangoJobViewSet(DjangoJobViewSet, ABC):
    def custom_job(self):
        get_rds_api_response()


class AliRedisDjangoJobViewSet(DjangoJobViewSet, ABC):
    def custom_job(self):
        get_redis_api_response()


class AliCFWDjangoJobViewSet(DjangoJobViewSet, ABC):
    def custom_job(self):
        get_cfw_api_response()
