from pathlib import Path
from django.core.exceptions import ValidationError


ALLOWED_EXTENSIONS = {
    '.pdf',
    '.png',
    '.jpg',
    '.jpeg',
    '.doc',
    '.docx',
    '.xls',
    '.xlsx',
    '.txt'
}

MAX_FILE_SIZE = 10 * 1024 * 1024


def validate_project_attachments(files):

    for uploaded_file in files:

        extension = Path(uploaded_file.name).suffix.lower()

        if extension not in ALLOWED_EXTENSIONS:
            raise ValidationError(
                'One or more files have an unsupported format.'
            )

        if uploaded_file.size > MAX_FILE_SIZE:
            raise ValidationError(
                'Each attachment must be smaller than 10 MB.'
            )