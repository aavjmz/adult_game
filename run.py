from app import create_app

app = create_app()

if __name__ == '__main__':
    # 使用127.0.0.1避免权限问题，使用8080端口避免冲突
    app.run(debug=True, host='127.0.0.1', port=8080)
