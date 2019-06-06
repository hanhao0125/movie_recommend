from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from settings import db
from models import User

u = Blueprint('user', __name__, template_folder='templates')


@u.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        account = request.form['account']
        password = request.form['password']
        user = User.query.filter(User.account == account).first()
        if user is not None:
            if user.is_freeze:
                return jsonify('账号被冻结，请联系管理员解封')
            if user.verify_password(password):
                login_user(user)
                return jsonify('success')
            else:
                return jsonify('密码不正确！')
        else:
            return jsonify('账号不存在')
    return render_template('login.html')


@u.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        account = request.form['account']
        password = request.form['password']
        user = User.query.filter(User.account == account).first()
        if user is not None:
            return jsonify('用户名已存在！')
        else:
            user = User(account)
            user.hash_password(password)
            db.session.add(user)
            db.session.commit()
        return jsonify('success')
    else:
        return render_template('register.html')


@u.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('user.login'))


@u.route('/user_info')
def user_info():
    return render_template('userInfo.html')


@u.route('/update_user_info', methods=['POST'])
@login_required
def uu_info():
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    phone = request.form['phone']
    user_id = current_user.id
    user = User.query.get(int(user_id))

    if password:
        user.password = user.hash_password(password)
    if username:
        user.username = username
    if email:
        user.email = email
    if phone:
        user.phone = phone
    db.session.commit()
    return jsonify('success')
