from functools import wraps
from flask import (
    abort)
from flask_login import (
    current_user,
)
from application.settings import login_manager
from application.database import User


def admin_required():
    def decorator(_func):
        @wraps(_func)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.is_admin:
                return _func(*args, **kwargs)
            else:
                abort(403)

        return decorated_function

    return decorator


@login_manager.user_loader
def load_user(_id):
    try:
        return User.query.get(int(_id))
    except Exception:
        return None
