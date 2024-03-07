from rest_framework import serializers
from base.models import *
from django.contrib.auth.models import User, Group
from rest_framework.validators import UniqueValidator
from django.contrib.auth.password_validation import validate_password


class ChangePasswordSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    old_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('old_password', 'password', 'password2')

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."})

        return attrs

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError(
                {"old_password": "Old password is not correct"})
        return value

    def update(self, instance, validated_data):

        instance.set_password(validated_data['password'])
        instance.save()

        return instance


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all())]
    )

    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'password2',
                  'email', 'first_name', 'last_name', 'is_active')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError(
                {"password": "Password fields didn't match."})

        return attrs

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            is_active=validated_data['is_active']
        )

        user.set_password(validated_data['password'])
        user.save()

        return user


class UpdateActiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('is_active',)

    def update(self, instance, validated_data):
        instance.is_active = validated_data['is_active']
        instance.save()

        return instance


# Auth Group Serializer


class auth_group_serializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name')


# Navigation Menu Serializer


class navigation_menu_details_serializer(serializers.ModelSerializer):
    class Meta:
        model = navigation_menu_details
        fields = ('menu_id', 'menu_name', 'parent_menu_id',
                  'url', 'page_number', 'created_by', 'last_updated_by')


# Group Access Definition Serializer


class group_access_definition_serializer(serializers.ModelSerializer):
    class Meta:
        model = group_access_definition
        fields = ('menu_id', 'group_id', 'add', 'edit', 'view',
                  'delete', 'created_by', 'last_updated_by')


# User Serialzer


class user_serializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email',
                  'first_name', 'last_name', 'is_active')


# Group Serialzer


class group_serializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ('id', 'name')


# Join Group and Group Access Definition Serializer


class group_group_access_serializer(serializers.ModelSerializer):
    group_id = group_serializer(read_only=True)

    class Meta:
        model = group_access_definition
        fields = ['group_id', 'menu_id', 'group_id', 'add', 'view',
                  'edit', 'delete', 'created_by', 'last_updated_by']


# User Settings Serializer


class settings_serializer(serializers.ModelSerializer):
    class Meta:
        model = settings
        fields = ('variable_name', 'value', 'user_id',
                  'created_by', 'last_updated_by')


# User Serializer


class CheckAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'is_superuser', 'is_staff', 'is_active',)


# User License Serializer


class user_license_serializer(serializers.ModelSerializer):
    class Meta:
        model = user_license
        fields = ('id', 'license_key', 'user_id',
                  'created_by', 'last_updated_by')


# Session Serializer


class session_serializer(serializers.ModelSerializer):
    class Meta:
        model = session
        fields = '__all__'


# Session Configuration Serializer


class session_configuration_serializer(serializers.ModelSerializer):
    class Meta:
        model = session_configuration
        fields = '__all__'


# Single Sign On (SSO) Configuration Serializer


class sso_configure_serializer(serializers.ModelSerializer):
    class Meta:
        model = sso_configure
        fields = ('id', 'app_id', 'tenant_id', 'created_by', 'last_updated_by')


# SMTP Mail Serializer


class smtp_configure_serializer(serializers.ModelSerializer):
    class Meta:
        model = smtp_configure
        fields = ('id', 'user_id', 'server_name', 'username', 'password',
                  'protocol', 'port', 'created_by', 'last_updated_by')


# Global Helper Serializer


class helper_serializer(serializers.ModelSerializer):
    class Meta:
        model = helper
        fields = ('id', 'page_no', 'label', 'help_context',
                  'context_order', 'created_by', 'last_updated_by')


# Validation Warnings Serializer


class warnings_serializer(serializers.ModelSerializer):
    class Meta:
        model = warnings
        fields = ('id', 'error_code', 'error_msg', 'error_category',
                  'error_from', 'error_no', 'created_by', 'last_updated_by')


class qb_defnition_serializer(serializers.ModelSerializer):
    class Meta:
        model = query_definition
        fields = '__all__'


class shared_query_definition_serializer(serializers.ModelSerializer):
    class Meta:
        model = shared_query_definition
        fields = '__all__'


class qb_table_serializer(serializers.ModelSerializer):
    class Meta:
        model = query_builder_table
        fields = '__all__'


class qb_table_columns_serializers(serializers.ModelSerializer):
    class Meta:
        model = query_builder_table_columns
        fields = '__all__'


class qb_table_joins_serializers(serializers.ModelSerializer):
    class Meta:
        model = query_builder_table_joins
        fields = '__all__'


class qb_table_alias_serializers(serializers.ModelSerializer):
    class Meta:
        model = query_builder_table_alias
        fields = '__all__'


class qb_table_column_filter_serializers(serializers.ModelSerializer):
    class Meta:
        model = query_builder_table_column_filter
        fields = '__all__'


class qb_table_groupBy_serializers(serializers.ModelSerializer):
    class Meta:
        model = query_builder_table_groupBy
        fields = '__all__'


class qb_table_aggergate_serializers(serializers.ModelSerializer):
    class Meta:
        model = query_builder_aggeration_function_table
        fields = '__all__'

# User pProfile


class user_profile_serializer(serializers.ModelSerializer):
    class Meta:
        model = user_profile
        fields = ('id', 'user_id', 'profile_pic', 'username',
                  'first_name', 'last_name', 'email', 'temporary_address', 'permanent_address', 'contact', 'user_group', 'user_status', 'created_by', 'last_updated_by')

# DB Connect


class rb_connect_definition_table_serializer(serializers.ModelSerializer):
    class Meta:
        model = rb_connect_definition_table
        fields = ('id', 'connection_name', 'schema_name', 'database_name', 'connection_type', 'user_name',
                  'password', 'host_id', 'port', 'service_name_or_SID', 'account_id', 'warehouse_id', 'role', 'auth_type', 'body', 'auth_url', 'user_id',
                  'data_enpoint_url', 'method', 'created_by', 'last_updated_by')
        # '__all__'
        

class metrics_serilizer(serializers.ModelSerializer):
    class Meta:
        model = metrics
        fields = ('id','QUERY_ID','QUERY_NAME','COLUMN_NAME','COLUMN_DATATYPE','TOTAL_COUNT','NOT_NULL_COUNT','NULL_COUNT','BLANK_COUNT','DISTINCT_VALUES_COUNT','MAX_LENGTH','MIN_LENGTH','MAX_VALUE','MIN_VALUE','NUMERIC_ONLY_VALUES_COUNT','ALPHABETS_ONLY_VALUES_COUNT','ALPHANUMERIC_ONLY_VALUES_COUNT','CONTAINS_SPECIAL_CHAR_COUNT','TOP_TEN_DISTINCT_VALUES','TOP_TEN_DISTRIBUTED_VALUES','OUTLIERS','DUPLICATE','REFERAL_INTEGRITY','RUN_DATE')

class meta_metrics_serilizer(serializers.ModelSerializer):
    class Meta:
        model = meta_metrics
        fields = ('__all__')

# Restful Connect
# class rb_rest_connect_table_Serializer(serializers.ModelSerializer):
#     class Meta:
#         model = rb_rest_connect_table
#         fields = ('id', 'connection_name', 'connection_type', 'auth_type', 'body', 'auth_url', 'user_id',
#                   'password', 'data_enpoint_url', 'method', 'created_by', 'last_updated_by')

