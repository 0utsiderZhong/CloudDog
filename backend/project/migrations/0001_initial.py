# Generated by Django 4.2.5 on 2023-09-11 07:49

import django.contrib.postgres.fields
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(db_comment='主键ID', primary_key=True, serialize=False)),
                ('cloud_platform', models.CharField(choices=[('Alibabacloud', '阿里云国际'), ('Aliyun', '阿里云中国'), ('AWS', '亚马逊云平台'), ('Azure', '微软云平台'), ('GCP', '谷歌云平台')], db_comment='云平台类型', default='AlibabaCloud', max_length=100, verbose_name='CloudPlatform')),
                ('account', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(), db_comment='项目RAM账号', default=list, size=None, verbose_name='Account')),
                ('region', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(), db_comment='地域', default=list, size=None, verbose_name='Region')),
                ('project_name', models.CharField(db_comment='项目名称', default='Sunway', max_length=500, unique=True, verbose_name='ProjectName')),
                ('project_access_key', models.CharField(db_comment='Access Key', default=None, max_length=100, verbose_name='AK')),
                ('project_secret_key', models.CharField(db_comment='Secret Key', default=None, max_length=100, verbose_name='SK')),
                ('cron_expression', django.contrib.postgres.fields.ArrayField(base_field=models.CharField(default=''), db_comment='Cron Expression', default=list, size=None, verbose_name='CronExpression')),
                ('cron_toggle', models.BooleanField(db_comment='Job Toggle', default=True, verbose_name='JobToggle')),
                ('key_authority', models.CharField(db_comment='Key的权限', default='ReadOnlyAccess', max_length=50, verbose_name='KeyAuthority')),
                ('status', models.CharField(choices=[('Running', '运行中'), ('Stopped', '已终止')], db_comment='项目状态', default='Running', max_length=30, verbose_name='ProjectStatus')),
                ('create_time', models.DateField(db_comment='账号创建时间', default=django.utils.timezone.now, verbose_name='CreateTime')),
            ],
            options={
                'db_table': 'project',
                'ordering': ['-id'],
            },
        ),
    ]
