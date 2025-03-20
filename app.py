import os
import logging
import traceback
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from scraper import scrape_job_posting
from text_processor import extract_job_details

# Configure logging
logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s %(levelname)s:%(name)s: %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

logger.info("Starting application...")

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

@app.route('/', methods=['GET'])
def index():
    """Render the main page with the scraper form."""
    logger.info("Index route accessed")
    return render_template('index.html')

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    logger.info("Health check endpoint accessed")
    return jsonify({"status": "ok", "message": "Application is running"})

@app.route('/scrape', methods=['POST'])
def scrape():
    """Handle the job URL submission and scraping process."""
    url = request.form.get('job_url')
    
    if not url:
        flash('Please enter a valid URL', 'danger')
        return redirect(url_for('index'))
    
    try:
        # Scrape the job posting
        logger.debug(f"Scraping URL: {url}")
        html_content = scrape_job_posting(url)
        
        if not html_content:
            flash('Failed to retrieve content from the provided URL', 'danger')
            return redirect(url_for('index'))
        
        # Extract job details from the content
        job_details = extract_job_details(html_content, url)
        
        # Store the results in session for display
        session['job_details'] = job_details
        session['source_url'] = url
        
        return redirect(url_for('results'))
    
    except Exception as e:
        logger.error(f"Error during scraping: {str(e)}")
        flash(f'Error during scraping: {str(e)}', 'danger')
        return redirect(url_for('index'))

@app.route('/results')
def results():
    """Display the scraped job details."""
    job_details = session.get('job_details')
    source_url = session.get('source_url')
    
    if not job_details:
        flash('No job details found. Please try scraping again.', 'warning')
        return redirect(url_for('index'))
    
    return render_template('results.html', job_details=job_details, source_url=source_url)

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('index.html', error="Page not found"), 404

@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    return render_template('index.html', error="Server error, please try again later"), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
