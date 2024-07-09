from flask_uploads import UploadSet, IMAGES

photos = UploadSet('photos', IMAGES)
attachments = UploadSet('attachments', extensions=('pdf', 'doc', 'docx', 'xls', 'xlsx'))
