from flask import render_template
from hris import app

# checks if the app.py file has executed directly and not imported
if __name__ == '__main__':
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(413)
    def request_entity_too_large(error):
        return render_template('413.html'), 413
    
    app.run(debug=True, threaded=True) 
    