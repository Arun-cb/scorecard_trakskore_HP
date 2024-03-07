from django.urls import path
from . import rb_views
from . import views
from rest_framework_simplejwt.views import ( TokenRefreshView )


urlpatterns = [
    path("", views.getRoutes),
    path("token/", views.MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path(
        "change_password/<int:pk>/",
        views.ChangePasswordView.as_view(),
        name="auth_change_password",
    ),
    path("getempregdetails", views.getEmpRegDetails),
    path(
        "update_profile/<int:pk>/",
        views.UpdateActiveView.as_view(),
        name="auth_update_profile",
    ),
    path("createuser", views.save_users),


    # For SSO Users insert at auth_group
    path("createmsuser", views.ms_save_users),
    path("get_auth_group", views.get_auth_group),
    path("get_user_groups", views.get_user_groups),
    path("get_range_user_groups/<int:start>/<int:end>/",
         views.get_range_user_groups),
    path("get_user_groups/<int:id>/", views.get_user_groups),
    path("ins_user_groups", views.ins_user_groups),


    # For SSO Users insert at user_group
    path("ms_ins_user_groups", views.ms_ins_user_groups),
    path("upd_user_groups", views.upd_user_groups),


    # navigation_menu_details
    path("get_navigation_menu_details", views.get_navigation_menu_details),
    path("get_navigation_menu_details/<int:id>/",
         views.get_navigation_menu_details),
    path("get_single_navigation_menu_details/<int:id>/",
         views.get_single_navigation_menu_details),
    path("ins_navigation_menu_details", views.ins_navigation_menu_details),


    # group_access_definition
    path("ins_group_access", views.ins_group_access),
    path("get_group_access_definition", views.get_group_access_definition),
    path("get_group_access_definition/<int:id>/",
         views.get_group_access_definition),
    path("upd_group_access_definition", views.upd_group_access_definition),
    path("upd_group_access_definition/<int:id>/",
         views.upd_group_access_definition),

    path("get_user_details", views.get_user_details),


    # join group and group_access_definition
    path("join_user_group_access", views.group_group_access),
    path("join_user_group_access/<int:id>/", views.group_group_access),
    path("join_user_group_access/<int:id>/<int:menu_id>/",
         views.group_group_access),


    # settings
    path("get_settings", views.get_settings),
    path("get_settings/<int:id>/", views.get_settings),
    path("upd_settings", views.upd_settings),
    path("upd_settings/<int:id>/", views.upd_settings),


    # Csv uplode
    path("csv_insert/<int:id>/", views.Csv_insert),


    #  smtp
    # path("get_smtp", views.get_smtp),
    # path("ins_upt_smtp", views.ins_upt_smtp),


    #  Forgot Password
    path("forgot_password", views.forgot_password),
    # path("get_kpi_actuals_monthly_score", views.get_kpi_actuals_monthly_score),


    # Global helper
    path("get_helper/<int:id>/", views.get_helper),
    path("get_helper", views.get_helper),


    # Global Error Message
    path("get_warnings", views.get_warnings),


    path("get_license", views.get_license),
    path("ins_upd_license/<int:id>/", views.ins_upd_license),

#     path("upd_order_no", views.update_order_no),
    path("updatesession/<int:uid>/", views.updatesession),
    path("updatesession/<int:uid>/<str:update>/", views.updatesession),
    path("deletesession/<int:uid>/", views.deletesession),

    # session Configuration
    path("getsessionconfig", views.get_session_configuration),
    path("ins_upd_session_config/<int:id>/", views.ins_upd_session_configuration),

    # #
    # path("ins_sso", views.ins_sso),
    # path("get_sso", views.get_sso),
    # !path("upd_sso/<int:id>/", views.upd_sso),

    # User Profile URLS
    path("ins_user_profile", views.ins_user_profile),
    path("get_user_profile", views.get_user_profile),
    path("get_user_profile/<int:id>/", views.get_user_profile),
    path("upd_user_profile/<int:id>/", views.upd_user_profile),
    path("del_user_profile/<int:id>/", views.del_user_profile),

    path("get_rb_connect_definition_table", views.get_rb_connect_definition_table),
    path("get_rb_table", views.get_rb_table),
    path("get_rb_connect_definition_table/<int:id>/", views.get_rb_connect_definition_table),
    path("get_range_rb_connect_definition_table/<int:start>/<int:end>/",
         views.get_range_rb_connect_definition_table),
    path("ins_rb_connect_definition_table", views.ins_rb_connect_definition_table),
    path("rb_test_db_connection", views.rb_test_db_connection),
    path("upd_rb_connect_definition_table/<int:id>/", views.upd_rb_connect_definition_table),
    path("del_rb_connect_definition_table/<int:id>/", views.del_rb_connect_definition_table),


    # path("rb_get_conn_str",rb_views.rb_get_conn_str),
    path("set_db_sql_connection", rb_views.set_db_sql_connection),
    path("set_db_oracle_connection", rb_views.set_db_oracle_connection),
    path("get_connected_tables", rb_views.fnGetTableData),
    path("display_columns", rb_views.rb_sql_show_columns),
    path("ins_save_connection_data", rb_views.fnStoreQueryNameConnectionData),
    path("upd_connection_data/<int:id>/",
         rb_views.fnUpdateQueryNameConnectionData),
    path("get_connection_data", rb_views.fnGetQueryDefinition),
    path("get_connection_data/<int:id>/", rb_views.fnGetQueryDefinition),
    path("get_range_query_definition/<int:start>/<int:end>/<str:created_user>/<str:sortcolumn>/",
         rb_views.get_range_query_definition),
    path("get_range_query_definition/<int:start>/<int:end>/<str:created_by>/<str:sortcolumn>/<str:search>/",
         rb_views.get_range_query_definition),

    # ? Shared Query URLS
    path("ins_shared_query_definition", rb_views.ins_shared_query_definition),
    path("upd_shared_query_definition/<int:id>/",
         rb_views.upd_shared_query_definition),
    path("get_shared_query_definition", rb_views.get_shared_query_definition),
    path("get_shared_query_definition/<int:id>/",
         rb_views.get_shared_query_definition),
    path("get_range_shared_query_definition/<int:start>/<int:end>/<str:permission_to>/<str:sortcolumn>/",
         rb_views.get_range_shared_query_definition),
    path("get_range_shared_query_definition/<int:start>/<int:end>/<str:permission_to>/<str:sortcolumn>/<str:search>/",
         rb_views.get_range_shared_query_definition),


    path("ins_save_table_data", rb_views.fnsaveSelectedTables),
    path("get_save_table_data", rb_views.fnGetQueryBuilderTable),
    path("get_save_table_data/<int:id>/", rb_views.fnGetQueryBuilderTable),

    path("ins_save_column_data", rb_views.fnsaveSelectedColumn),
    path("get_save_column_data", rb_views.fngetsavedcolumns),
    path("get_save_column_data/<int:id>/", rb_views.fngetsavedcolumns),


    path("ins_alias_table_data", rb_views.fn_ins_column_alias),
    path("get_alias_table_data", rb_views.fn_get_column_alias),


    path("ins_aggregate_table_data", rb_views.fn_ins_column_aggregate),
    path("get_aggregate_table_data", rb_views.fn_get_column_aggregate),
    path("get_aggregate_table_data/<int:id>/",
         rb_views.fn_get_column_aggregate),

    path("ins_save_join_table_data", rb_views.fninsjointablesave),
    path("get_join_table_data", rb_views.fnGetJoinTableColumnData),
    path("get_join_table_data/<int:id>/", rb_views.fnGetJoinTableColumnData),
    
    path("ins_filter_column_data",rb_views.fn_ins_column_filter_data),

    path("ins_filter_column_data",rb_views.fn_ins_column_filter_data),

    path("get_execute_query_data", rb_views.fnpostquerytoexecute),


    path("ins_query_column_data", rb_views.fn_ins_query_column_data),

    path("get_query_result", rb_views.fnGetQueryResult),
    path("load_data", rb_views.load_data),

    path("get_ydata_profiling_report", views.get_ydata_profiling_report),
    path("get_data_quality_report", views.get_data_quality_report),
    path("get_json_report", views.get_json_report),

     # path("get_rb_connect_definition_table", views.get_rb_rest_connect_table),
     # path("get_rb_connect_definition_table/<int:id>/", views.get_rb_rest_connect_table),
     # path("get_range_rb_connect_definition_table/<int:start>/<int:end>/", views.get_range_rb_rest_connect_table),
     # path("ins_rb_connect_definition_table",views.ins_rb_rest_connect_table),
     # # path("rb_test_db_connection",views.rb_test_db_connection),
     # path("upd_rb_db_connect_definition_table/<int:id>/", views.upd_rb_db_connect_definition_table),
     # path("del_rb_connect_definition_table/<int:id>/", views.del_rb_rest_connect_table),
     
     path("ins_and_upd_connection_data", rb_views.ins_and_upd_connection_data),
     
     path("transform_data",rb_views.fn_data_to_transform),
     path('datainsertdestination',rb_views.fn_ins_data_to_source),
     path('datatocomapre',rb_views.dataprofileCompare),     
     path('dataquality',rb_views.fn_data_quality),
     path('ins_profiler_data',rb_views.ins_data_quality_metrics),
     path("get_metrics/<int:id>/", rb_views.get_metrics_data),

     # Meta_Metrics
     path('ins_data_quality_meta_metrics',rb_views.ins_data_quality_meta_metrics),


]
