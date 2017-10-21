def check_password(environ, user, password):
    if user == 'spy':
        if password == 'secret':
            return True
        return False
    return None
