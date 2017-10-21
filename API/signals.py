from django.dispatch import Signal

callback_merchant = Signal(providing_args=['requestID', 'userID'])
