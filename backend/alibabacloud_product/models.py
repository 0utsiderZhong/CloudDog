# ECS 实例

from django.utils import timezone
from django.db import models
from project.models import Project
from abc import abstractmethod
import logging

logger = logging.getLogger(__name__)


class ProductType(models.TextChoices):
    ECS = ('ecs', '服务器')
    WAF = ('waf', 'Web应用防火墙')

    class Meta:
        app_label = 'ProductType'


class InstanceBaseModel(models.Model):
    api_request_id = models.CharField(primary_key=True, default='', max_length=50, db_comment='API Request Id')
    instance_id = models.CharField(default='', max_length=30, verbose_name='InstanceId', db_comment='实例ID')
    request_time = models.DateTimeField(default=timezone.now, max_length=30, verbose_name='RequestTime', db_comment='API请求时间')
    product_type = models.CharField(default=ProductType.ECS, max_length=30, verbose_name='ProductName', db_comment='云产品类型', choices=ProductType.choices)
    project = models.ForeignKey(
        Project,
        # https://foofish.net/django-foreignkey-on-delete.html
        on_delete=models.DO_NOTHING,
        related_name='instance_object'
    )
    # 先拿一个project对象
    # project.instance_object.all()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    class Meta:
        abstract = True
        app_label = 'RequestBasicInfo'

    @abstractmethod
    def get_basic_info(self):
        pass


class EcsInstance(InstanceBaseModel):
    Status = (
        ('Pending', '创建中'),
        ('Running', '运行中'),
        ('Starting', '启动中'),
        ('Stopping', '停止中'),
        ('Stopped', '已停止'),
    )
    LockReason = (
        ('financial', '因欠费被锁定'),
        ('security', '因安全原因被锁定'),
        ('Recycling', '抢占式实例的待释放锁定状态'),
        ('dedicatedhostfinancial', '因为专有宿主机欠费导致ECS实例被锁定'),
        ('refunded', '因退款被锁定'),
    )
    InternetChargeType = (
        ('PayByBandwidth', '按固定带宽计费'),
        ('PayByTraffic', '按使用流量计费'),
    )
    InstanceChargeType = (
        ('PostPaid', '按量付费'),
        ('PrePaid', '包年包月')
    )
    StoppedMode = (
        ('KeepCharging', '停机后继续收费，为您继续保留库存资源'),
        ('StopCharging', '停机后不收费。停机后，我们释放实例对应的资源，例如vCPU、内存和公网IP等资源。重启是否成功依赖于当前地域中是否仍有资源库存'),
        ('Not-applicable', '本实例不支持停机不收费功能'),
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.DO_NOTHING,
        related_name='ecs_object'
    )
    product_type = ProductType.ECS

    """ ECS Instance Property """
    # API: DescribeInstanceAutoRenewAttribute
    auto_renew_enabled = models.BooleanField(default=False, verbose_name='AutoRenewEnabled', db_comment='是否已开启自动续费功能')
    renewal_status = models.CharField(default='', max_length=30, verbose_name='RenewalStatus', db_comment='实例的自动续费状态')
    period_init = models.CharField(default='', max_length=20, verbose_name='PeriodUnit', db_comment='自动续费时长的单位')
    duration = models.IntegerField(default=None, verbose_name='Duration', db_comment='自动续费时长')
    # API: DescribeInstances
    region_id = models.CharField(default='', max_length=30, verbose_name='RegionId', db_comment='实例地域')
    ecs_status = models.CharField(default='', max_length=20, verbose_name='EcsStatus', db_comment='实例状态', choices=Status)
    instance_charge_type = models.CharField(default='', max_length=30, verbose_name='InstanceChargeType', db_comment='实例付费类型', choices=InstanceChargeType)
    internet_charge_type = models.CharField(default='', max_length=30, verbose_name='InternetChargeType', db_comment='按固定带宽/使用流量计费', choices=InternetChargeType)
    expired_time = models.CharField(default='', max_length=30, verbose_name='ExpiredTime', db_comment='过期时间')
    stopped_mode = models.CharField(default='', max_length=30, verbose_name='StoppedMode', db_comment='实例停机后是否继续收费', choices=StoppedMode)
    start_time = models.CharField(default='', max_length=50, verbose_name='StartTime', db_comment='实例最近一次的启动时间')
    auto_release_time = models.CharField(default='', max_length=50, verbose_name='AutoReleaseTime', db_comment='按量付费实例的自动释放时间')
    lock_reason = models.CharField(default='', max_length=30, verbose_name='LockReason', db_comment='实例的锁定原因', choices=LockReason)

    def get_basic_info(self):
        to_string = 'ECS: Region {}, instance {} status is {}'.format(self.region_id, self.instance_id, self.ecs_status)
        return to_string

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'ecs_api_response'


class WafInstance(InstanceBaseModel):
    Status = (
        (0, '表示已过期'),
        (1, '表示未过期'),
    )
    Version = (
        ('version_3', '表示中国内地高级版'),
        ('version_4', '表示中国内地企业版'),
        ('version_5', '表示中国内地旗舰版'),
        ('version_exclusive_cluster', '表示中国内地虚拟独享集群版'),
        ('version_hybrid_cloud_standard', '表示中国内地混合云WAF版'),
        ('version_pro_asia', '表示非中国内地高级版'),
        ('version_business_asia', '表示非中国内地企业版'),
        ('version_enterprise_asia', '表示非中国内地旗舰版'),
        ('version_exclusive_cluster_asia', '表示非中国内地虚拟独享集群版'),
        ('version_hybrid_cloud_standard_asia', '表示非中国内地混合云WAF版'),
        ('version_elastic_bill', '表示按量计费版'),
        ('version_elastic_bill_new', '表示按量计费2.0版'),
    )
    Region = (
        ('cn', '表示中国内地'),
        ('cn-hongkong', '表示非中国内地'),
    )
    PayType = (
        (0, '表示当前阿里云账号未开通WAF实例'),
        (1, '表示当前阿里云账号已开通WAF包年包月实例'),
        (2, '表示当前阿里云账号已开通WAF按量计费实例'),
    )
    InDebt = (
        (0, '表示已欠费'),
        (1, '表示未欠费'),
    )
    SubscriptionType = (
        ('Subscription', '表示包年包月'),
        ('PayAsYouGo', '表示按量计费'),
    )
    Trial = (
        (0, '表示否'),
        (1, '表示是'),
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.DO_NOTHING,
        related_name='waf_object'
    )
    product_type = ProductType.WAF

    """ WAF Instance Property """
    waf_status = models.IntegerField(default=None, verbose_name='WafStatus', db_comment='WAF实例是否过期', choices=Status)
    end_date = models.IntegerField(default=None, verbose_name='EndDate', db_comment='WAF实例的到期时间')
    version = models.CharField(default='', max_length=40, verbose_name='Version', db_comment='WAF实例的版本', choices=Version)
    remain_day = models.IntegerField(default=None, verbose_name='RemainDay', db_comment='试用版WAF实例的剩余可用天数')
    region = models.CharField(default='', max_length=30, verbose_name='Region', db_comment='WAF实例的地域', choices=Region)
    pay_type = models.IntegerField(default=None, verbose_name='PayType', db_comment='WAF实例的开通状态', choices=PayType)
    in_debt = models.IntegerField(default=None, verbose_name='InDebt', db_comment='WAF实例是否存在欠费', choices=InDebt)
    subscription_type = models.CharField(default='', max_length=30, verbose_name='SubscriptionType', db_comment='WAF实例的计费方式', choices=SubscriptionType)
    trial = models.IntegerField(default=None, verbose_name='Trial', db_comment='当前阿里云账号是否开通了试用版WAF实例', choices=Trial)

    def get_basic_info(self):
        to_string = 'WAF: Region {}, instance {} status is {}'.format(self.region, self.instance_id, self.waf_status)
        return to_string

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    class Meta:
        db_table = 'waf_api_response'
