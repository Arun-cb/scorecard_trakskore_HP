from django.apps import AppConfig


class BaseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'base'

    def ready(self):
        from base.api import updater
        from base.api import smtp_mail
        to = 'arunravi1497@gmail.com'
        body = """<html>
            <style>
            table, th, td {
            color:green
            border:1px solid black;
            }
            </style>
            <body>

            <h2>A basic HTML table</h2>

            <table style="border:3px solid #BBBBBB; font-size:16px; font-family:Arial, Helvetica, sans-serif; margin:30px 0 30px 0;" bgcolor="#ffffff">
            <tr>
                <th style="border:2px solid #BBBBBB;">Company</th>
                <th style="border:2px solid #BBBBBB;">Contact</th>
                <th style="border:2px solid #BBBBBB;">Country</th>
            </tr>
            <tr>
                <td style="border:2px solid #BBBBBB; text-align:center;">Alfreds Futterkiste</td>
                <td style="border:2px solid #BBBBBB; text-align:center;">Maria Anders</td>
                <td style="border:2px solid #BBBBBB; text-align:center;">Germany</td>
            </tr>
            <tr>
                <td style="border:2px solid #BBBBBB; text-align:center;">Centro comercial Moctezuma</td>
                <td style="border:2px solid #BBBBBB; text-align:center;">Francisco Chang</td>
                <td style="border:2px solid #BBBBBB; text-align:center;">Mexico</td>
            </tr>
            </table>

            <p>To understand the example better, we have added borders to the table.</p>

            </body>
            </html>"""
        subject = "Demo mail"
        # attachment parts. if you want to send an attachment, should be given filename and filepath. If not to pass empty of those fields 
        attachments=True
        filename="Revenue per Employee (2).jpg"
        filepath='C:/Users/ArunR/Downloads/Revenue per Employee (2).jpg'
        updater.start()
        # smtp_mail.send_mail(to=to, body=body, subject=subject, type='html', attachments=attachments, filename=filename, filepath=filepath)

    