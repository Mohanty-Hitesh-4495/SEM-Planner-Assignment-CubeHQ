import yaml
import os
import csv
import time
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
from llm_agent import extract_form_data, get_llm

def fill_website_field(page, website_url, timeout=5000):
    """Fill the website/keyword input field"""
    print(f"Filling website field with: {website_url}")
    try:
        # Target the specific input field for website/keyword with multiple selectors
        website_selectors = [
            'input[name="websiteURLOrKeyword"]',  # Exact name match
            'input[data-testid="websiteURLOrKeyword"]',  # Data testid
            '.MuiInputBase-input',  # MUI input class
            'input[type="text"]'  # Generic text input
        ]
        
        website_input = None
        for selector in website_selectors:
            try:
                website_input = page.wait_for_selector(selector, timeout=2000, state="visible")
                if website_input:
                    print(f"Found website input with selector: {selector}")
                    break
            except:
                continue
        
        if not website_input:
            print("Could not find website input field with any selector")
            return False
        
        # Clear existing content and fill with new value
        website_input.click(force=True)
        page.wait_for_timeout(500)
        website_input.select_text()
        website_input.type(website_url, delay=100)
        page.wait_for_timeout(1000)
        
        print(f"Successfully filled website field")
        return True
        
    except Exception as e:
        print(f"Error filling website field: {str(e)}")
        return False

def fill_industry_dropdown(page, industry_value, timeout=5000):
    """Fill the industry dropdown"""
    if not industry_value or industry_value == "All Industries":
        print("Skipping industry selection - using default 'All Industries'")
        return True
        
    print(f"Trying to select industry: {industry_value}")
    try:
        # Find the industry dropdown using the MUI Select structure
        # First try to find the select div that acts as the combobox
        industry_selectors = [
            '[aria-label="industry"]',  # Direct aria-label match
            'div[role="combobox"] .MuiSelect-select',  # MUI Select element
            '.MuiSelect-select',  # Direct select class
            '.sc-jYGMYt.sc-igAlAF.eZHANI.kHFAsD.MuiSelect-select'  # Full class chain
        ]
        
        industry_dropdown = None
        for selector in industry_selectors:
            try:
                industry_dropdown = page.wait_for_selector(selector, timeout=2000, state="visible")
                if industry_dropdown:
                    print(f"Found industry dropdown with selector: {selector}")
                    break
            except:
                continue
        
        if not industry_dropdown:
            print("Could not find industry dropdown with any selector")
            return False
            
        # Click to open the dropdown
        industry_dropdown.click(force=True)
        page.wait_for_timeout(2000)
        
        # Wait for the dropdown menu to appear and look for the option
        try:
            # Look for menu items in the MUI dropdown
            menu_selectors = [
                f'li[role="option"]:has-text("{industry_value}")',  # MUI menu item
                f'.MuiMenuItem-root:has-text("{industry_value}")',  # MUI menu item class
                f'[role="option"]:has-text("{industry_value}")',  # Generic option role
                f'li:has-text("{industry_value}")'  # Generic li element
            ]
            
            option_found = False
            for menu_selector in menu_selectors:
                try:
                    industry_option = page.wait_for_selector(menu_selector, timeout=3000, state="visible")
                    if industry_option:
                        industry_option.click(force=True)
                        page.wait_for_timeout(1000)
                        print(f"Successfully selected industry: {industry_value} using selector: {menu_selector}")
                        option_found = True
                        break
                except:
                    continue
            
            if not option_found:
                print(f"Industry option '{industry_value}' not found in any dropdown menu")
                page.keyboard.press("Escape")
                return False
            
            return True
                
        except Exception as e:
            print(f"Error selecting industry option: {str(e)}")
            page.keyboard.press("Escape")
            return False
            
    except Exception as e:
        print(f"Error opening industry dropdown: {str(e)}")
        return False

def fill_location_autocomplete(page, location_value, timeout=5000):
    """Fill the location autocomplete field"""
    if not location_value:
        print("No location provided, skipping")
        return True
        
    print(f"Filling location field with: {location_value}")
    try:
        # Find the location autocomplete input using multiple selectors
        location_selectors = [
            '[aria-label="location"] input',  # Input within aria-labeled container
            'input[aria-autocomplete="list"]',  # Autocomplete input
            '.MuiAutocomplete-input',  # MUI Autocomplete input class
            'input[role="combobox"]',  # Input with combobox role
            'input[type="text"][autocomplete="off"]'  # Generic autocomplete input
        ]
        
        location_input = None
        for selector in location_selectors:
            try:
                location_input = page.wait_for_selector(selector, timeout=2000, state="visible")
                if location_input:
                    print(f"Found location input with selector: {selector}")
                    break
            except:
                continue
        
        if not location_input:
            print("Could not find location input field with any selector")
            return False
        
        # Clear existing content and focus the input
        location_input.click(force=True)
        page.wait_for_timeout(500)
        
        # Clear any existing value
        location_input.select_text()
        page.keyboard.press("Delete")
        page.wait_for_timeout(500)
        
        # Type the new location
        location_input.type(location_value, delay=100)
        page.wait_for_timeout(2000)
        
        # Wait for autocomplete suggestions and select the first matching one
        try:
            # Look for autocomplete popup options with various selectors
            autocomplete_selectors = [
                f'[role="option"]:has-text("{location_value}")',  # Exact match
                f'[role="option"]',  # Any option (will select first)
                f'.MuiAutocomplete-option:has-text("{location_value}")',  # MUI autocomplete option
                f'.MuiAutocomplete-option',  # Any MUI option
                f'li[role="option"]:has-text("{location_value}")',  # List item option
                f'li[role="option"]'  # Any list item option
            ]
            
            option_selected = False
            for selector in autocomplete_selectors:
                try:
                    # Wait for options to appear
                    autocomplete_option = page.wait_for_selector(selector, timeout=3000, state="visible")
                    
                    if autocomplete_option:
                        autocomplete_option.click(force=True)
                        page.wait_for_timeout(1000)
                        print(f"Successfully selected location from autocomplete using: {selector}")
                        option_selected = True
                        break
                except:
                    continue
            
            if not option_selected:
                print("No autocomplete options found or selected, keeping typed value")
                # Press Enter or Tab to confirm the typed value
                page.keyboard.press("Tab")
                page.wait_for_timeout(500)
                
            return True
                
        except Exception as e:
            print(f"No autocomplete suggestions appeared: {str(e)}")
            # Press Tab to move to next field and confirm the typed value
            page.keyboard.press("Tab")
            return True  # Still return True as the text was entered
            
    except Exception as e:
        print(f"Error filling location field: {str(e)}")
        return False

def click_continue_button(page, timeout=5000):
    """Click the Continue button to submit the form"""
    print("Looking for Continue button...")
    try:
        # Target the specific Continue button
        continue_button = page.wait_for_selector('button[data-testid="buttonContinue"]', timeout=timeout)
        
        if not continue_button:
            print("Could not find Continue button with data-testid")
            # Fallback: look for button with Continue text
            continue_button = page.wait_for_selector('button:has-text("Continue")', timeout=2000)
        
        if not continue_button:
            print("Could not find Continue button")
            return False
        
        # Ensure button is visible and enabled
        if not continue_button.is_visible() or not continue_button.is_enabled():
            print("Continue button is not visible or enabled")
            return False
        
        # Click the button
        continue_button.click(force=True)
        page.wait_for_timeout(2000)
        print("Successfully clicked Continue button")
        return True
        
    except Exception as e:
        print(f"Error clicking Continue button: {str(e)}")
        return False

def read_config(config_path):
    """Read configuration from YAML file"""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def clean_url(url):
    """Clean URL to extract domain for better keyword research"""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    parsed = urlparse(url)
    return parsed.netloc.replace('www.', '')

def collect_keywords(config, output_csv="data/wordstream_output.csv", timeout=60000):
    """Scrape keywords from WordStream using the brand website"""
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)

    # Debug: Print config contents
    print("Config contents:")
    print(config)

    # Get website URL from config
    brand_website = config.get("brand_website")
    if not brand_website:
        raise Exception("No brand_website found in config file")
    
    print(f"Using website URL: {brand_website}")
    
    # Clean the URL for better results
    clean_domain = clean_url(brand_website)
    print(f"Cleaned domain: {clean_domain}")

    with sync_playwright() as p:
        # Launch browser with more options for better compatibility
        browser = p.chromium.launch(
            headless=False,  # Set to True for headless mode
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--window-size=1920,1080'
            ]
        )
        
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        )
        
        page = context.new_page()
        
        try:
            # Navigate to the page
            print("Navigating to WordStream...")
            page.goto("https://tools.wordstream.com/fkt", timeout=timeout)
            
            # Wait for the page to load completely
            page.wait_for_load_state("networkidle", timeout=timeout)
            page.wait_for_timeout(3000)
            
            # Take screenshot for debugging
            page.screenshot(path="step1_loaded.png")
            
            # Handle any popups/modals first
            print("Checking for popups or modals...")
            try:
                # Look for common modal/popup close buttons
                close_selectors = [
                    'button[aria-label*="close"]',
                    'button[aria-label*="Close"]',
                    '.close',
                    '[data-testid*="close"]',
                    'button:has-text("×")',
                    'button:has-text("Close")',
                    'button:has-text("No thanks")',
                    'button:has-text("Skip")',
                    'button:has-text("Later")'
                ]
                
                for close_selector in close_selectors:
                    try:
                        close_button = page.query_selector(close_selector)
                        if close_button and close_button.is_visible():
                            print(f"Found and clicking close button: {close_selector}")
                            close_button.click(force=True)
                            page.wait_for_timeout(1000)
                            break
                    except:
                        continue
                
                # Try pressing Escape key to close any remaining modals
                page.keyboard.press('Escape')
                page.wait_for_timeout(1000)
                
            except Exception as e:
                print(f"Error handling popup: {str(e)}")
            
            # Take screenshot after handling popups
            page.screenshot(path="step1_after_popup.png")
            
            # Fill the website/keyword field using the improved function
            print("Filling website field...")
            success = fill_website_field(page, brand_website)
            if success:
                print("✅ Website field filled successfully")
                page.screenshot(path="step2_website_filled.png")
            else:
                print("❌ Failed to fill website field")
                raise Exception("Failed to fill website field")
            
            # Get form data using LLM
            llm = get_llm()
            form_data = extract_form_data(config, llm)
            print(f"Form data extracted: {form_data}")
            
            # Fill industry dropdown if available
            if form_data["industry"] and form_data["industry"] != "All Industries":
                industry_success = fill_industry_dropdown(page, form_data["industry"])
                if not industry_success:
                    print("Failed to fill industry, continuing with default")
            
            # Fill location autocomplete if available
            if form_data["location"]:
                location_success = fill_location_autocomplete(page, form_data["location"])
                if not location_success:
                    print("Failed to fill location, continuing without it")
            
            # Take screenshot after filling all fields
            page.screenshot(path="step2_filled.png")
            
            # Click the Continue button
            continue_success = click_continue_button(page)
            if not continue_success:
                raise Exception("Failed to click Continue button")
            
            # Wait for results to load
            print("Waiting for results to load...")
            page.wait_for_timeout(10000)  # Wait 10 seconds for initial load
            
            # Take screenshot of current state
            page.screenshot(path="step3_after_continue.png")
            print(f"Current URL after clicking continue: {page.url}")
            
            # Wait for loading to complete
            print("Checking for loading indicators...")
            loading_selectors = [
                '[data-testid*="loading"]',
                '.loading',
                '[class*="loading"]',
                '[role="progressbar"]',
                'text="Loading"',
                'text="Please wait"',
                'text="Analyzing"',
                'text="Processing"'
            ]
            
            # Wait for loading to finish
            max_wait_time = 120000  # 2 minutes max wait
            start_time = time.time() * 1000
            
            while True:
                current_time = time.time() * 1000
                if current_time - start_time > max_wait_time:
                    print("Maximum wait time exceeded")
                    break
                
                # Check if any loading indicators are still visible
                loading_visible = False
                for selector in loading_selectors:
                    try:
                        if selector.startswith('text='):
                            text_to_find = selector[5:]  # Remove 'text=' prefix
                            elements = page.query_selector_all(f'text="{text_to_find}"')
                        else:
                            elements = page.query_selector_all(selector)
                        
                        if any(el.is_visible() for el in elements):
                            loading_visible = True
                            break
                    except:
                        continue
                
                if not loading_visible:
                    print("Loading indicators have disappeared")
                    break
                    
                print("Still loading... waiting 3 more seconds")
                page.wait_for_timeout(3000)
            
            # Additional wait after loading disappears
            page.wait_for_timeout(5000)
            
            # Look for results
            print("Looking for results...")
            page.screenshot(path="step4_results.png")
            
            # Try to find results table or container
            results_selectors = [
                'table tbody tr',
                'table tr td',
                '[data-testid*="results"]',
                '.results',
                '[class*="result"]',
                '[class*="keyword"]',
                '.MuiTable-root',
                '.MuiDataGrid-root',
                '[role="grid"]',
                '[role="table"]'
            ]
            
            results_found = False
            keywords = []
            
            for selector in results_selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if len(elements) > 0:
                        print(f"Found {len(elements)} result elements with selector: {selector}")
                        results_found = True
                        
                        # Try to extract keyword data from tables
                        if 'table' in selector:
                            keywords = extract_keywords_from_table(page)
                        
                        break
                except:
                    continue
            
            if not results_found:
                page.screenshot(path="no_results_found.png")
                print("Could not find results. Check screenshots for debugging.")
                
                # Create empty results
                keywords = []
            
        except Exception as e:
            print(f"Error during automation: {str(e)}")
            page.screenshot(path="error_screenshot.png")
            raise
        finally:
            browser.close()

    # Save results to CSV
    if keywords:
        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["keyword", "monthly_volume", "cpc", "competition"])
            writer.writeheader()
            writer.writerows(keywords)
        
        print(f"✅ Successfully saved {len(keywords)} keywords to {output_csv}")
        
        # Display first few keywords
        print("\nFirst few keywords found:")
        for i, kw in enumerate(keywords[:5]):
            print(f"{i+1}. {kw['keyword']} - Volume: {kw['monthly_volume']}, CPC: {kw['cpc']}")
            
    else:
        print("⚠️ No keywords were extracted. Check the screenshots for debugging.")
        # Create empty CSV file
        with open(output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["keyword", "monthly_volume", "cpc", "competition"])
            writer.writeheader()

def extract_keywords_from_table(page):
    """Extract keywords from results table"""
    keywords = []
    
    try:
        # Look for tables on the page
        tables = page.query_selector_all("table")
        print(f"Found {len(tables)} tables on the page")
        
        for table_idx, table in enumerate(tables):
            print(f"\n--- Processing Table {table_idx + 1} ---")
            
            # Get all rows in this table
            rows = table.query_selector_all("tr")
            print(f"Table {table_idx + 1} has {len(rows)} rows")
            
            header_found = False
            
            for row_idx, row in enumerate(rows):
                cells = row.query_selector_all("td, th")
                if len(cells) == 0:
                    continue
                    
                cell_texts = [cell.inner_text().strip() for cell in cells]
                
                # Check if this is a header row
                if any(header in cell_texts[0].lower() for header in ['keyword', 'search term', 'phrase', 'query']):
                    header_found = True
                    print(f"Header row found: {cell_texts}")
                    continue
                
                # Skip empty rows
                if not any(cell_text.strip() and cell_text.strip() not in ['-', '–', '—', 'N/A'] for cell_text in cell_texts):
                    continue
                    
                # Process data rows
                if header_found and len(cell_texts) >= 2:
                    print(f"Data row {row_idx}: {cell_texts}")
                    
                    keyword_data = {
                        "keyword": cell_texts[0] if len(cell_texts) > 0 else "",
                        "monthly_volume": cell_texts[1] if len(cell_texts) > 1 else "N/A",
                        "cpc": cell_texts[2] if len(cell_texts) > 2 else "N/A",
                        "competition": cell_texts[3] if len(cell_texts) > 3 else "N/A"
                    }
                    
                    # Only add if we have a meaningful keyword
                    if (keyword_data["keyword"] and 
                        len(keyword_data["keyword"]) > 1 and 
                        keyword_data["keyword"].lower() not in ['keyword', 'search term', 'phrase']):
                        keywords.append(keyword_data)
                        print(f"Added keyword: {keyword_data['keyword']}")
        
        print(f"Total keywords extracted: {len(keywords)}")
        
    except Exception as e:
        print(f"Error extracting keywords from table: {str(e)}")
    
    return keywords

def main():
    """Main function to run the keyword scraper"""
    try:
        # Try different possible config paths
        config_paths = [
            "config/config.yml", 
            "config.yml", 
            "config/sem_config.yaml", 
            "sem_config.yaml"
        ]
        
        config = None
        config_path_used = None
        
        for path in config_paths:
            try:
                print(f"Trying to read config from: {path}")
                config = read_config(path)
                config_path_used = path
                print(f"✅ Successfully read config from: {path}")
                break
            except FileNotFoundError:
                print(f"❌ Config file not found: {path}")
                continue
        
        if not config:
            raise Exception("Could not find config file in any of these locations: " + ", ".join(config_paths))
        
        print(f"\nUsing config from: {config_path_used}")
        print(f"Brand website: {config.get('brand_website', 'Not found')}")
        
        # Run the keyword collection
        collect_keywords(config)
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()