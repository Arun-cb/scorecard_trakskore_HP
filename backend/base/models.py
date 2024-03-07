from django.db import models
from django.contrib.auth.models import User, Group


# Navigation Menu Model

class navigation_menu_details(models.Model):
    menu_id = models.AutoField(primary_key=True)
    menu_name = models.CharField(
        max_length=300, null=False, blank=False, unique=True)
    parent_menu_id = models.IntegerField(null=False, blank=False)
    url = models.CharField(max_length=300, null=False, blank=False)
    page_number = models.IntegerField(null=False, blank=False)
    created_by = models.IntegerField(null=False, blank=False)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated_by = models.IntegerField(null=False, blank=False)
    last_updated_date = models.DateTimeField(auto_now=True)
    delete_flag = models.CharField(
        max_length=1, null=False, blank=False, default='N')

    class Meta:
        db_table = "tb_sc_navigation_menu_details"


# Group Access Model


class group_access_definition(models.Model):
    menu_id = models.ForeignKey(
        navigation_menu_details, max_length=5, null=False, blank=False, db_column='menu_id', on_delete=models.CASCADE)
    group_id = models.ForeignKey(
        Group, related_name='group', null=False, blank=False, db_column='group_id', on_delete=models.CASCADE)
    add = models.CharField(max_length=1, null=False, blank=False, default='N')
    edit = models.CharField(max_length=1, null=False, blank=False, default='N')
    view = models.CharField(max_length=1, null=False, blank=False, default='N')
    delete = models.CharField(max_length=1, null=False,
                              blank=False, default='N')
    created_by = models.IntegerField(null=False, blank=False)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated_by = models.IntegerField(null=False, blank=False)
    last_updated_date = models.DateTimeField(auto_now=True)
    delete_flag = models.CharField(
        max_length=1, null=False, blank=False, default='N')

    class Meta:
        db_table = "tb_sc_group_access_definition"


# User Settings Model


class settings(models.Model):
    variable_name = models.CharField(max_length=300, null=False, blank=False)
    value = models.CharField(max_length=300, null=False, blank=False)
    user_id = models.IntegerField(null=False, blank=False)
    created_by = models.IntegerField(null=False, blank=False)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated_by = models.IntegerField(null=False, blank=False)
    last_updated_date = models.DateTimeField(auto_now=True)
    delete_flag = models.CharField(
        max_length=1, null=False, blank=False, default='N')

    class Meta:
        db_table = "tb_sc_settings"


# User Profile Logo Path Function


def profile_pic_upload_path(instance, filename):
    obj = user_profile.objects.all().last()
    ext = filename.split('.')
    if obj == None:
        file_name = "user_profile_%s.%s" % (1, ext[1])
    elif instance.id == None:
        file_name = "user_profile_%s.%s" % (obj.id+1, ext[1])
    else:
        file_name = "user_profile_%s_upd.%s" % (instance.id, ext[1])
    # print(file_name)
    return file_name
    # '/'.join([file_name])


# User Profile Model


class user_profile(models.Model):
    user_id = models.ForeignKey(
        User, null=False, blank=False, db_column='user_id', on_delete=models.CASCADE)
    profile_pic = models.ImageField(
        null=True, blank=True, upload_to=profile_pic_upload_path)
    username = models.CharField(max_length=100, null=False, blank=False)
    first_name = models.CharField(max_length=100, null=True, blank=True)
    last_name = models.CharField(max_length=100, null=True, blank=True)
    email = models.CharField(max_length=100, null=False, blank=False)
    temporary_address = models.CharField(max_length=100, null=True, blank=True)
    permanent_address = models.CharField(max_length=100, null=True, blank=True)
    contact = models.CharField(max_length=10, null=True, blank=True)
    user_group = models.CharField(max_length=100, null=False, blank=False)
    user_status = models.BooleanField(default=False)
    created_by = models.IntegerField(null=False, blank=False)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated_by = models.IntegerField(null=False, blank=False)
    last_updated_date = models.DateTimeField(auto_now=True)
    delete_flag = models.CharField(
        max_length=1, null=False, blank=False, default='N')

    class Meta:
        db_table = "tb_sc_user_profile"


# SMTP Mail Model


class smtp_configure(models.Model):
    user_id = models.IntegerField(null=False, blank=False)
    server_name = models.CharField(max_length=300, null=False, blank=False)
    username = models.CharField(max_length=300, null=False, blank=False)
    password = models.CharField(max_length=300, null=False, blank=False)
    protocol = models.CharField(max_length=300, null=False, blank=False)
    port = models.IntegerField(null=False, blank=False)
    created_by = models.IntegerField(null=False, blank=False)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated_by = models.IntegerField(null=False, blank=False)
    last_updated_date = models.DateTimeField(auto_now=True)
    delete_flag = models.CharField(
        max_length=1, null=False, blank=False, default='N')

    class Meta:
        db_table = "tb_sc_smtp_configure"


# Helper Tooltip Model


class helper(models.Model):
    page_no = models.ForeignKey(navigation_menu_details, null=False,
                                blank=False, db_column='page_no', on_delete=models.CASCADE)
    label = models.CharField(max_length=500, null=False, blank=False)
    help_context = models.CharField(max_length=500, null=False, blank=False)
    context_order = models.IntegerField()
    created_by = models.IntegerField(null=False, blank=False)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated_by = models.IntegerField(null=False, blank=False)
    last_updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tb_sc_helper"


# Validation Warnings Model


class warnings(models.Model):
    error_code = models.CharField(max_length=50, null=False, blank=False)
    error_msg = models.CharField(max_length=500, null=False, blank=False)
    error_category = models.CharField(max_length=50, null=False, blank=False)
    error_from = models.CharField(max_length=50, null=False, blank=False)
    error_no = models.IntegerField(null=True, blank=False)
    created_by = models.IntegerField(null=False, blank=False)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated_by = models.IntegerField(null=False, blank=False)
    last_updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tb_sc_warnings"


# User License Model


class user_license(models.Model):
    license_key = models.CharField(max_length=50, null=False, blank=False)
    user_id = models.IntegerField(null=True, blank=False)
    created_by = models.IntegerField(null=False, blank=False)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated_by = models.IntegerField(null=False, blank=False)
    last_updated_date = models.DateTimeField(auto_now=True)
    delete_flag = models.CharField(
        max_length=1, null=False, blank=False, default='N')

    class Meta:
        db_table = "tb_sc_user_license"


# Session Maintainance Model


class session(models.Model):
    id = models.AutoField(primary_key=True)
    uid = models.IntegerField(null=False, blank=False)
    sid = models.CharField(max_length=455, null=False, blank=False)
    logintime = models.CharField(max_length=20, null=True, blank=True)
    lasttime = models.CharField(max_length=20, null=True, blank=True)
    expired = models.CharField(max_length=20, null=False, blank=False)
    status = models.IntegerField(null=False, blank=False)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated_date = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tb_sc_session"


# Session Configuration Model


class session_configuration(models.Model):
    idle_time = models.IntegerField(null=False, blank=False)
    session_time = models.IntegerField(null=False, blank=False)
    created_by = models.IntegerField(null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated_by = models.IntegerField(null=True, blank=True)
    last_updated_date = models.DateTimeField(auto_now=True)
    delete_flag = models.CharField(
        max_length=1, null=False, blank=False, default='N')

    class Meta:
        db_table = "tb_sc_session_configuration"


# Single Sign On (SSO) Configuration Model


class sso_configure(models.Model):

    app_id = models.CharField(max_length=300, null=False, blank=False)
    tenant_id = models.CharField(max_length=300, null=False, blank=False)
    created_by = models.IntegerField(null=False, blank=False)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated_by = models.IntegerField(null=False, blank=False)
    last_updated_date = models.DateTimeField(auto_now=True)
    delete_flag = models.CharField(
        max_length=1, null=False, blank=False, default='N')

    class Meta:
        db_table = "tb_sc_sso_configure"


# Query Builder Database Connection Model


class rb_connect_definition_table(models.Model):
    id = models.AutoField(primary_key=True)
    connection_name = models.CharField(max_length=255, null=False, blank=False)
    schema_name = models.CharField(max_length=255, null=True, blank=True)
    database_name = models.CharField(max_length=255, null=True, blank=True)
    connection_type = models.CharField(max_length=255, null=False, blank=False)
    user_name = models.CharField(max_length=50, null=True, blank=True)
    password = models.CharField(max_length=50, null=True, blank=True)
    host_id = models.CharField(max_length=20, null=True, blank=True)
    port = models.IntegerField(null=True, blank=True)
    service_name_or_SID = models.CharField(max_length=30, null=True, blank=True)
    account_id = models.CharField(max_length=255, null=True, blank=True)
    warehouse_id = models.CharField(max_length=255, null=True, blank=True)
    role = models.CharField(max_length=255, null=True, blank=True)

    auth_type = models.CharField(max_length=255, null=True, blank=True)
    auth_url = models.CharField(max_length=255, null=True, blank=True)
    body = models.CharField(max_length=255, null=True, blank=True)
    user_id = models.CharField(max_length=500, null=True, blank=True)
    # password = models.CharField(max_length=500, null=True, blank=True)
    data_enpoint_url = models.CharField(max_length=2000, null=True, blank=True)
    method = models.CharField(max_length=50, null=True, blank=True)
    
    created_by = models.IntegerField(null=False, blank=False)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated_by = models.IntegerField(null=False, blank=False)
    last_updated_date = models.DateTimeField(auto_now=True)
    delete_flag = models.CharField(
        max_length=1, null=False, blank=False, default='N')

    class Meta:
        db_table = "rb_connect_definition_table"


# Query Builder Definition Model


class query_definition(models.Model):
    id = models.AutoField(primary_key=True)
    query_name = models.CharField(max_length=255, null=False, blank=False)
    connection_id = models.ForeignKey(
        rb_connect_definition_table, null=False, blank=False, db_column="connection_id", on_delete=models.CASCADE)
    query_text = models.TextField(null=True, blank=True)
    created_user = models.CharField(max_length=255, null=False, blank=False)
    created_by = models.IntegerField(null=False, blank=False)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated_by = models.IntegerField(null=False, blank=False)
    last_updated_date = models.DateTimeField(auto_now=True)
    delete_flag = models.CharField(
        max_length=1, null=False, blank=False, default='N')
    query_status = models.BooleanField(default=False)
    query_type = models.BooleanField(default=False)

    class Meta:
        db_table = "tb_sqb_query_definition"


# Shared Query Definition Model


class shared_query_definition(models.Model):
    id = models.AutoField(primary_key=True)
    permission_to = models.CharField(max_length=255, null=False, blank=False)
    permission_by = models.CharField(max_length=255, null=False, blank=False)
    permission_type = models.CharField(max_length=255, null=False, blank=False)
    query_id = models.IntegerField(null=False, blank=False)
    created_by = models.IntegerField(null=False, blank=False)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated_by = models.IntegerField(null=False, blank=False)
    last_updated_date = models.DateTimeField(auto_now=True)
    delete_flag = models.CharField(
        max_length=1, null=False, blank=False, default='N')

    class Meta:
        db_table = "tb_sqb_shared_query_definition"


# Query Builder Table Model


class query_builder_table(models.Model):
    id = models.AutoField(primary_key=True)
    table_name = models.CharField(max_length=255, null=False, blank=False)
    table_id = models.CharField(max_length=255, null=False, blank=False)
    query_id = models.ForeignKey(query_definition, null=False,
                                 blank=False, db_column='query_id', on_delete=models.CASCADE)
    created_by = models.IntegerField(null=False, blank=False)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated_by = models.IntegerField(null=False, blank=False)
    last_updated_date = models.DateTimeField(auto_now=True)
    delete_flag = models.CharField(
        max_length=1, null=False, blank=False, default='N')

    class Meta:
        db_table = "tb_sqb_query_builder_table"


# Query Builder Columns Model


class query_builder_table_columns(models.Model):
    id = models.AutoField(primary_key=True)
    column_name = models.CharField(max_length=255, null=True, blank=False)
    column_data_type = models.CharField(max_length=255, null=True, blank=False)
    alias_name = models.CharField(max_length=255, null=True, blank=False)
    sort_type = models.CharField(max_length=255, null=True, blank=True)
    sort_order = models.IntegerField(null=True, blank=True)
    sort_column = models.CharField(max_length=255, null=True, blank=True)
    group_by = models.CharField(max_length=255, null=True, blank=True)
    col_function = models.CharField(max_length=255, null=True, blank=True)
    column_display_order = models.IntegerField(null=True, blank=True)
    column_display_ind = models.CharField(
        max_length=255, null=True, blank=True)
    created_by = models.IntegerField(null=False, blank=False)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated_by = models.IntegerField(null=False, blank=False)
    last_updated_date = models.DateTimeField(auto_now=True)
    delete_flag = models.CharField(
        max_length=1, null=False, blank=False, default='N')
    table_column_table_id = models.ForeignKey(
        query_builder_table, null=False, blank=False, db_column='table_column_table_id', on_delete=models.CASCADE)
    table_column_query_id = models.ForeignKey(
        query_definition, null=False, blank=False, db_column='table_column_query_id', on_delete=models.CASCADE)

    class Meta:
        db_table = "tb_sqb_query_builder_table_columns"


# Query Builder Joins Model


class query_builder_table_joins(models.Model):
    id = models.AutoField(primary_key=True)
    tab_join_table_id_one = models.ForeignKey(
        query_builder_table,
        related_name='tab_join_table_one',
        null=False, blank=False,
        db_column='tab_join_table_id_one',
        on_delete=models.CASCADE
    )
    tab_join_table_id_two = models.ForeignKey(
        query_builder_table,
        related_name='tab_join_table_id_two',
        null=False, blank=False,
        db_column='tab_join_table_id_two',
        on_delete=models.CASCADE
    )
    tab_join_query_id = models.ForeignKey(
        query_definition,
        null=False, blank=False,
        db_column='tab_join_query_id',
        on_delete=models.CASCADE
    )
    join_type = models.CharField(max_length=255, null=True, blank=False)
    join_column_name1 = models.CharField(
        max_length=255, null=True, blank=False)
    join_column_name2 = models.CharField(
        max_length=255, null=True, blank=False)
    created_by = models.IntegerField(null=False, blank=False)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated_by = models.IntegerField(null=False, blank=False)
    last_updated_date = models.DateTimeField(auto_now=True)
    delete_flag = models.CharField(
        max_length=1, null=False, blank=False, default='N')

    class Meta:
        db_table = "tb_sqb_query_builder_table_joins"


# Query Builder Alias Model


class query_builder_table_alias(models.Model):
    id = models.AutoField(primary_key=True)
    col_alias_table_id = models.ForeignKey(
        query_builder_table, null=False, blank=False, db_column='col_alias_table_id', on_delete=models.CASCADE)
    col_alias_query_id = models.ForeignKey(
        query_definition, null=False, blank=False, db_column='col_alias_query_id', on_delete=models.CASCADE)
    col_alias_column_id = models.ForeignKey(
        query_builder_table_columns, null=False, blank=False, db_column='col_alias_column_id', on_delete=models.CASCADE)
    alias_name = models.CharField(max_length=255, null=True, blank=True)
    created_by = models.IntegerField(null=False, blank=False)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated_by = models.IntegerField(null=False, blank=False)
    last_updated_date = models.DateTimeField(auto_now=True)
    delete_flag = models.CharField(
        max_length=1, null=False, blank=False, default='N')

    class Meta:
        db_table = "tb_sqb_query_builder_table_alias"


# Query Builder Filter Model


class query_builder_table_column_filter(models.Model):
    id = models.AutoField(primary_key=True)
    column_name = models.CharField(max_length=255, null=False, blank=False)
    column_filter = models.CharField(max_length=255, null=False, blank=False)
    column_value = models.CharField(max_length=255, null=False, blank=False)
    tab_filter_tale_id = models.ForeignKey(
        query_builder_table, null=False, blank=False, db_column='tab_filter_tale_id', on_delete=models.CASCADE)
    tab_filter_query_id = models.ForeignKey(
        query_definition, null=False, blank=False, db_column='tab_filter_query_id', on_delete=models.CASCADE)
    created_by = models.IntegerField(null=False, blank=False)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated_by = models.IntegerField(null=False, blank=False)
    last_updated_date = models.DateTimeField(auto_now=True)
    delete_flag = models.CharField(
        max_length=1, null=False, blank=False, default='N')

    class Meta:
        db_table = "tb_sqb_query_builder_table_column_filter"


# Query Builder GroupBy Model


class query_builder_table_groupBy(models.Model):
    id = models.AutoField(primary_key=True)
    table_grp_table_id = models.ForeignKey(
        query_builder_table, null=False, blank=False, db_column='table_grp_table_id', on_delete=models.CASCADE)
    table_grp_query_id = models.ForeignKey(
        query_definition, null=False, blank=False, db_column='table_grp_query_id', on_delete=models.CASCADE)
    table_grp_column_id = models.ForeignKey(
        query_builder_table_columns, null=False, blank=False, db_column='table_grp_column_id', on_delete=models.CASCADE)
    groupbyFunction = models.CharField(max_length=255, null=True, blank=False)
    having_filter_ind = models.CharField(max_length=1, null=True, blank=False)
    having_filter_operator = models.CharField(
        max_length=255, null=True, blank=False)
    having_filter_value = models.IntegerField(null=True, blank=False)
    created_by = models.IntegerField(null=False, blank=False)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated_by = models.IntegerField(null=False, blank=False)
    last_updated_date = models.DateTimeField(auto_now=True)
    delete_flag = models.CharField(
        max_length=1, null=False, blank=False, default='N')

    class Meta:
        db_table = "tb_sqb_query_builder_table_groupBy"


# Query Builder Aggeration Model


class query_builder_aggeration_function_table(models.Model):
    id = models.AutoField(primary_key=True)
    agg_fun_name = models.CharField(max_length=255, null=True, blank=False)

    table_aggragate_query_id = models.ForeignKey(
        query_definition, null=False, blank=False, db_column='table_aggragate_query_id', on_delete=models.CASCADE)

    table_aggregate_table_id = models.ForeignKey(
        query_builder_table, null=False, blank=False, db_column='table_aggregate_table_id', on_delete=models.CASCADE)

    table_aggregate_column_id = models.ForeignKey(
        query_builder_table_columns, null=False, blank=False, db_column='table_aggregate_column_id', on_delete=models.CASCADE)

    created_by = models.IntegerField(null=False, blank=False)
    created_date = models.DateTimeField(auto_now_add=True)
    last_updated_by = models.IntegerField(null=False, blank=False)
    last_updated_date = models.DateTimeField(auto_now=True)
    delete_flag = models.CharField(
        max_length=1, null=False, blank=False, default='N')

    class Meta:
        db_table = "tb_sqb_query_builder_aggreation_table"
        
        

class metrics(models.Model):
    id = models.AutoField(primary_key=True),
    QUERY_ID = models.CharField(max_length=100, null=True, blank=False)
    QUERY_NAME = models.CharField(max_length=255, null=True, blank=False)
    COLUMN_NAME = models.CharField(max_length=255, null=True, blank=False)
    COLUMN_DATATYPE = models.CharField(max_length=255, null=True, blank=False)
    TOTAL_COUNT = models.IntegerField(null=False, blank=False)
    NOT_NULL_COUNT = models.IntegerField(null=False, blank=False)
    NULL_COUNT = models.IntegerField(null=False, blank=False)
    BLANK_COUNT = models.IntegerField(null=False, blank=False)
    DISTINCT_VALUES_COUNT = models.IntegerField(null=False, blank=False)
    MAX_LENGTH = models.CharField(max_length=255, null=True, blank=False)
    MIN_LENGTH = models.CharField(max_length=255, null=True, blank=False)
    MAX_VALUE = models.CharField(max_length=255, null=True, blank=False)
    MIN_VALUE = models.CharField(max_length=255, null=True, blank=False)
    NUMERIC_ONLY_VALUES_COUNT = models.IntegerField(null=False, blank=False)
    ALPHABETS_ONLY_VALUES_COUNT = models.IntegerField(null=False, blank=False)
    ALPHANUMERIC_ONLY_VALUES_COUNT = models.IntegerField(null=False, blank=False)
    CONTAINS_SPECIAL_CHAR_COUNT = models.IntegerField(null=False, blank=False)
    TOP_TEN_DISTINCT_VALUES = models.TextField(null=True, blank=False)
    TOP_TEN_DISTRIBUTED_VALUES = models.CharField(max_length=255, null=True, blank=False)
    OUTLIERS = models.CharField(max_length=255, null=True, blank=False)
    DUPLICATE = models.CharField(max_length=255, null=True, blank=False)
    REFERAL_INTEGRITY = models.CharField(max_length=255, null=True, blank=False)
    RUN_DATE = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table ='metrics'



# Restful connection table
# class rb_rest_connect_table(models.Model):
#     id = models.AutoField(primary_key=True)
#     connection_name = models.CharField(max_length=255,null=False,blank=False)
#     connection_type = models.CharField(max_length=255,null=False,blank=False)
#     auth_type = models.CharField(max_length=255, null=False, blank=False)
#     # connection_url = models.CharField(max_length=2000,null=True,blank=True)
#     auth_url = models.CharField(max_length=255, null=True, blank=True)
#     body = models.CharField(max_length=255, null=True, blank=True)
#     user_id = models.CharField(max_length=500, null=True, blank=True)
#     password = models.CharField(max_length=500, null=True, blank=True)
#     data_enpoint_url = models.CharField(max_length=2000, null=False, blank=False)
#     method = models.CharField(max_length=50, null=False, blank=False)
#     # client_id = models.CharField(max_length=500, null=True, blank=True)
#     # secret_code = models.CharField(max_length=500, null=True, blank=True)
#     created_by = models.IntegerField(null=False, blank=False)
#     created_date = models.DateTimeField(auto_now_add=True)
#     last_updated_by = models.IntegerField(null=False, blank=False)
#     last_updated_date = models.DateTimeField(auto_now=True)
#     delete_flag = models.CharField(max_length=1, null=False, blank=False, default='N')

#     class Meta:
#         db_table = "rb_rest_connect_table"



