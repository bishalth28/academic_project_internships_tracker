

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, List
from dotenv import load_dotenv

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Set up logging
log_file = f"scheduler_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AutomatedTracker:
    """
    Automated internship tracker that runs without user intervention.
    
    Features:
    - Reads search configurations from config file
    - Runs multiple searches automatically
    - Saves results to CSV
    - Logs all activities
    - Handles errors gracefully
    """
    
    def __init__(self):
        """Initialize the automated tracker."""
        self.config_file = 'search_config.json'
        self.config = self.load_config()
        logger.info("🤖 Automated Tracker initialized")
    
    def load_config(self) -> Dict:
        """
        Load search configuration from JSON file.
        
        Config format:
        {
            "searches": [
                {
                    "major": "Computer Science",
                    "location": "Remote",
                    "max_pages": 2
                },
                {
                    "major": "Software Engineering",
                    "location": "Ohio",
                    "max_pages": 3
                }
            ],
            "max_jobs_per_search": 10,
            "output_format": "csv"
        }
        """
        if not os.path.exists(self.config_file):
            # Create default config
            default_config = {
                "searches": [
                    {
                        "major": "Computer Science",
                        "location": "Remote",
                        "max_pages": 2
                    }
                ],
                "max_jobs_per_search": 10,
                "output_format": "csv"
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            logger.info(f"✅ Created default config: {self.config_file}")
            return default_config
        
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            logger.info(f"✅ Loaded config: {self.config_file}")
            return config
        except Exception as e:
            logger.error(f"❌ Error loading config: {e}")
            return {"searches": [], "max_jobs_per_search": 10, "output_format": "csv"}
    
    def run_automated_search(self):
        """
        Run all configured searches automatically.
        
        This is the main function called by the scheduler.
        """
        logger.info("="*70)
        logger.info("🤖 STARTING AUTOMATED INTERNSHIP SEARCH")
        logger.info("="*70)
        
        start_time = datetime.now()
        
        # Import tracker
        try:
            from internship_tracker import InternshipTracker
        except ImportError:
            logger.error("❌ Cannot import InternshipTracker. Make sure internship_tracker.py exists!")
            return False
        
        # Check credentials
        email = os.getenv('WRIGHT_STATE_EMAIL')
        username = os.getenv('WRIGHT_STATE_USERNAME')
        password = os.getenv('WRIGHT_STATE_PASSWORD')
        
        if not all([email, username, password]):
            logger.error("❌ Missing credentials in .env file!")
            logger.error("   Please set WRIGHT_STATE_EMAIL, WRIGHT_STATE_USERNAME, WRIGHT_STATE_PASSWORD")
            return False
        
        # Initialize tracker in headless mode
        tracker = InternshipTracker(
            email=email,
            username=username,
            password=password,
            headless=True
        )
        
        try:
            # Login
            logger.info("🔐 Logging in...")
            if not tracker.login():
                logger.error("❌ Login failed")
                return False
            
            logger.info("✅ Login successful")
            
            # Run each search
            searches = self.config.get('searches', [])
            max_jobs = self.config.get('max_jobs_per_search', 10)
            output_format = self.config.get('output_format', 'csv')
            
            total_jobs_found = 0
            
            for i, search in enumerate(searches, 1):
                logger.info(f"\n{'='*70}")
                logger.info(f"🔍 SEARCH {i}/{len(searches)}")
                logger.info(f"{'='*70}")
                
                major = search.get('major', '')
                location = search.get('location', '')
                max_pages = search.get('max_pages', 2)
                
                logger.info(f"   Major: {major}")
                logger.info(f"   Location: {location}")
                logger.info(f"   Pages: {max_pages}")
                
                # Search
                job_urls = tracker.search_jobs(major, location, max_pages)
                
                if not job_urls:
                    logger.warning(f"⚠️  No jobs found for search {i}")
                    continue
                
                logger.info(f"✅ Found {len(job_urls)} jobs")
                
                # Scrape details
                jobs_to_scrape = min(len(job_urls), max_jobs)
                logger.info(f"📋 Scraping {jobs_to_scrape} jobs...")
                
                jobs = []
                for j, url in enumerate(job_urls[:jobs_to_scrape], 1):
                    logger.info(f"   [{j}/{jobs_to_scrape}] Scraping job...")
                    job = tracker.scrape_job_details(url)
                    jobs.append(job)
                
                # Save
                filename = f"auto_{major.replace(' ', '_')}_{location.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                tracker.save_to_file(jobs, filename, output_format)
                
                total_jobs_found += len(jobs)
                
                logger.info(f"✅ Saved {len(jobs)} jobs")
            
            # Summary
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds() / 60
            
            logger.info("\n" + "="*70)
            logger.info("🎉 AUTOMATED SEARCH COMPLETED")
            logger.info("="*70)
            logger.info(f"   Searches run: {len(searches)}")
            logger.info(f"   Total jobs found: {total_jobs_found}")
            logger.info(f"   Duration: {duration:.1f} minutes")
            logger.info(f"   Time saved vs manual: ~{(37.5 - duration):.1f} minutes")
            logger.info("="*70)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error during automated search: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
            
        finally:
            tracker.close()
    
    def run_scheduled(self):
        """
        Run the tracker and handle scheduling logic.
        
        This function:
        1. Checks if it should run (based on last run time)
        2. Runs the search
        3. Updates last run time
        """
        last_run_file = 'last_run.txt'
        
        # Check last run time
        if os.path.exists(last_run_file):
            with open(last_run_file, 'r') as f:
                last_run = f.read().strip()
            logger.info(f"Last run: {last_run}")
        
        # Run the search
        success = self.run_automated_search()
        
        # Update last run time
        if success:
            with open(last_run_file, 'w') as f:
                f.write(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            logger.info("✅ Last run time updated")
        
        return success


def main():
    """
    Main function for scheduled execution.
    """
    print("\n" + "="*70)
    print("  AUTOMATED INTERNSHIP TRACKER SCHEDULER")
    print("="*70 + "\n")
    
    try:
        tracker = AutomatedTracker()
        success = tracker.run_scheduled()
        
        if success:
            print("\n✅ Automated search completed successfully!")
            print("💡 Check internships.csv for results")
            print("💡 Run 'streamlit run dashboard.py' to view dashboard")
        else:
            print("\n❌ Automated search failed. Check logs for details.")
        
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())


if __name__ == "__main__":
    main()