if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
    os.makedirs(current_app.config['UPLOAD_FOLDER'])