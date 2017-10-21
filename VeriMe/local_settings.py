WAIT_IMAGES_TIME = 180
GET_MERCHANT_INFO_URL = "http://[YOUR_API_ADDRESS]/api/v1/get_merchant/?"
UPLOAD_PROFILE_URL = "http://[YOUR_API_ADDRESS]/api/v1/write_profile"
DOWNLOAD_IMAGES_URL = "http://api.verime.mobi/media/?img="
REQUESTID_EXPIRE_TIME = 3600
CONFIDENCE_THRESHOLD = 0.48
ACTION_CODE_FORMAT_2 = '^\d-\d$'
ACTION_CODE_FORMAT_3 = '^\d-\d-\d$'
SUCCESS_RESPONSE = {"error_code": "0", "error_desc": ""}
UNDEFINE_ERROR_RESPONSE = {"error_code": "100", "error_desc": "Undefined error!"}
REQUESTID_NOTFOUND_RESPONSE = {"error_code": "002", "error_desc": "RequestID not found!"}
REQUESTID_EXPRIE_RESPONSE = {"error_code": "003", "error_desc": "RequestID expired!"}
PERMISSION_DENIED_RESPONSE = {"error_code": "017", "error_desc": "This requestID does not belong your merchant!"}
