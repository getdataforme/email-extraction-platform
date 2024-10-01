"""
This is the email parser module which helps us parse the email
from either text or from HTML content.
"""
from lxml import html
import re
import logging
from email_validator import validate_email, EmailNotValidError

logging.basicConfig(level=logging.INFO)

class EmailParser:
    def __init__(self, content="", content_type="text"):
        self.content = content
        self.content_type = content_type

    def get_email(self):
        EMAIL_REGEX = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')

        if self.content_type == "text":
            emails = EMAIL_REGEX.findall(self.content)
            if emails:
                logging.info(f"Found {len(emails)} emails in text.")
            return self._validate_emails(set(emails))

        elif self.content_type == 'html':
            try:
                tree = html.fromstring(self.content)
                text_content = tree.xpath('//text()')
                all_text = ' '.join(text_content)
                emails = EMAIL_REGEX.findall(all_text)
                if emails:
                    logging.info(f"Found {len(emails)} emails in HTML content.")
                return self._validate_emails(set(emails))
            except Exception as e:
                logging.error(f"Error parsing HTML content: {str(e)}")
                return set()

        else:
            logging.error("Unsupported content type. Use 'text' or 'html'.")
            return set()

    def _validate_emails(self, emails):
        """
        Validate extracted emails using email-validator.
        """
        valid_emails = set()
        for email in emails:
            try:
                v = validate_email(email)
                valid_emails.add(v.email)
                logging.info(f"Valid email: {v.email}")
            except EmailNotValidError as e:
                logging.warning(f"Invalid email {email}: {str(e)}")
        return valid_emails


if __name__ == '__main__':
    # Example usage
    text_content = "Contact us at kiran.sharma@gmail.com or info@example.com"
    html_content = "<html><body>Contact us at <a href='mailto:support@example.com'>support@example.com</a></body></html>"

    # Parse text content
    email_parser = EmailParser(content=text_content, content_type="text")
    emails_from_text = email_parser.get_email()
    print("Valid emails from text:", emails_from_text)

    # Parse HTML content
    email_parser = EmailParser(content=html_content, content_type="html")
    emails_from_html = email_parser.get_email()
    print("Valid emails from HTML:", emails_from_html)
