import os
import resend

resend.api_key = "re_7ssjF9cG_9Lb8P6RJ4uwrRzr7eLPqvHDQ"

params: resend.Emails.SendParams = {
    "from": "LinguaFlex <services@linguaflex.com>",
    "to": ["fejibo4756@cronack.com"],
    "subject": "hello world",
    "html": "<strong>it works!</strong>",
}

email = resend.Emails.send(params)
print(email)