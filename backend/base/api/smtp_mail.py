# from apscheduler.schedulers.background import BackgroundScheduler
# from base.api.views import check_kpi_pending
from .serializers import *
import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from rest_framework.response import Response
from rest_framework import generics, status, filters

def send_mail(to='', cc='', bcc= '', subject='', body='', type='', attachments=False, filename ='', filepath='', test=[]):
    if len(test) == 1:
        sender_email = test[0]['username']
        sender_password = test[0]['password']
        server_name = test[0]['server_name'] 
        port = test[0]['port'] 
        to = test[0]['username']
        message = MIMEText(body, 'html')
        message['Subject'] = subject
        message['From'] = sender_email
        message['To'] = to
        if test[0]['protocol'] == 'ssl':
            try:
                server = smtplib.SMTP_SSL(server_name, port)
            except Exception as e:
                return "false"
            try: 
                server.login(sender_email, sender_password)
            except Exception as e:
                return "false"
            try:
                server.sendmail(sender_email, to, message.as_string())
                server.quit()
                # print('Mail Sent')
                return "true"
            except Exception as e:
                return "false"
            
        elif test[0]['protocol'] == 'tls':
            try:
                server = smtplib.SMTP(server_name, port)
                server.set_debuglevel(0)
                server.starttls() #enable security
            except Exception as e:
                return "false"
            try:
                server.login(sender_email, sender_password) #login with mail_id and password
            except Exception as e:
                return "false"
            try:
                text = message.as_string()
                server.sendmail(sender_email, to, text)
                server.quit()
                return "true"
            except Exception as e:
                return "false"
    else:
        data = smtp_configure_serializer(smtp_configure.objects.filter(delete_flag='N'), many=True).data
        if len(data) == 1:
            sender_email = data[0]['username']
            sender_password = data[0]['password']
            server_name = data[0]['server_name'] 
            port = data[0]['port'] 
        if type == 'html':
            message = MIMEText(body, 'html')
        if attachments:
            with open(filepath, "rb") as attachment:
                # Add the attachment to the message
                part = MIMEBase("application", "octet-stream")
                part.set_payload((attachment).read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {os.path.basename(filename)}",
            )
            message = MIMEMultipart()
            message.attach(part)
        message['Subject'] = subject
        message['From'] = sender_email
        message['To'] = to
        # if attachments:
            # html_part = MIMEText(body)
            # message.attach(html_part)
            # message.attach(part)
        if cc != '':
            message['Cc'] = cc
        if bcc != '':
            message['Bcc'] = bcc
        if data[0]['protocol'] == 'ssl':
            server = smtplib.SMTP_SSL(server_name, port)
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to, message.as_string())
            server.quit()
            print('Mail Sent')
        elif data[0]['protocol'] == 'tls':
            server = smtplib.SMTP(server_name, port)
            server.set_debuglevel(0)
            server.starttls() #enable security
            server.login(sender_email, sender_password) #login with mail_id and password
            text = message.as_string()
            server.sendmail(sender_email, to, text)
            server.quit()
            print('Mail Sent')
    
