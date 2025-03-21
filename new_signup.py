from DrissionPage import ChromiumOptions, ChromiumPage
import time
import os
import signal
import random
from colorama import Fore, Style
import configparser
from pathlib import Path
import sys
from config import get_config 

# Add global variable at the beginning of the file
_translator = None

def cleanup_chrome_processes(translator=None):
    """Clean all Chrome related processes"""
    print("\nCleaning Chrome processes...")
    try:
        if os.name == 'nt':
            os.system('taskkill /F /IM chrome.exe /T 2>nul')
            os.system('taskkill /F /IM chromedriver.exe /T 2>nul')
        else:
            os.system('pkill -f chrome')
            os.system('pkill -f chromedriver')
    except Exception as e:
        if translator:
            print(f"{Fore.RED}❌ {translator.get('register.cleanup_error', error=str(e))}{Style.RESET_ALL}")
        else:
            print(f"清理进程时出错: {e}")

def signal_handler(signum, frame):
    """Handle Ctrl+C signal"""
    global _translator
    if _translator:
        print(f"{Fore.CYAN}{_translator.get('register.exit_signal')}{Style.RESET_ALL}")
    else:
        print("\n接收到退出信号，正在关闭...")
    cleanup_chrome_processes(_translator)
    os._exit(0)

def simulate_human_input(page, url, config, translator=None):
    """Visit URL"""
    if translator:
        print(f"{Fore.CYAN}🚀 {translator.get('register.visiting_url')}: {url}{Style.RESET_ALL}")
    
    # First visit blank page
    page.get('about:blank')
    time.sleep(get_random_wait_time(config, 'page_load_wait'))
    
    # Visit target page
    page.get(url)
    time.sleep(get_random_wait_time(config, 'page_load_wait'))

def fill_signup_form(page, first_name, last_name, email, config, translator=None):
    """Fill signup form"""
    try:
        if translator:
            print(f"{Fore.CYAN}📧 {translator.get('register.filling_form')}{Style.RESET_ALL}")
        else:
            print("\n正在填写注册表单...")
        
        # Fill first name
        first_name_input = page.ele("@name=first_name")
        if first_name_input:
            first_name_input.input(first_name)
            time.sleep(get_random_wait_time(config, 'input_wait'))
        
        # Fill last name
        last_name_input = page.ele("@name=last_name")
        if last_name_input:
            last_name_input.input(last_name)
            time.sleep(get_random_wait_time(config, 'input_wait'))
        
        # Fill email
        email_input = page.ele("@name=email")
        if email_input:
            email_input.input(email)
            time.sleep(get_random_wait_time(config, 'input_wait'))
        
        # Click submit button
        submit_button = page.ele("@type=submit")
        if submit_button:
            submit_button.click()
            time.sleep(get_random_wait_time(config, 'submit_wait'))
            
        if translator:
            print(f"{Fore.GREEN}✅ {translator.get('register.form_success')}{Style.RESET_ALL}")
        else:
            print("Form filled successfully")
        return True
        
    except Exception as e:
        if translator:
            print(f"{Fore.RED}❌ {translator.get('register.form_error', error=str(e))}{Style.RESET_ALL}")
        else:
            print(f"Error filling form: {e}")
        return False

# def get_default_chrome_path():
#     """Get default Chrome path"""
#     if sys.platform == "win32":
#         paths = [
#             os.path.join(os.environ.get('PROGRAMFILES', ''), 'Google/Chrome/Application/chrome.exe'),
#             os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Google/Chrome/Application/chrome.exe'),
#             os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google/Chrome/Application/chrome.exe')
#         ]
#     elif sys.platform == "darwin":
#         paths = [
#             "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
#         ]
#     else:  # Linux
#         paths = [
#             "/usr/bin/google-chrome",
#             "/usr/bin/google-chrome-stable"
#         ]

#     for path in paths:
#         if os.path.exists(path):
#             return path
#     return ""

def get_default_chrome_path():
    """Get the default Chrome executable path, with better error handling."""
    
    # Allow manual override
    chrome_env = os.environ.get("CHROME_PATH")
    if chrome_env and os.path.exists(chrome_env) and os.access(chrome_env, os.X_OK):
        return chrome_env

    if sys.platform == "win32":
        paths = [
            os.path.join(os.environ.get('PROGRAMFILES', ''), 'Google/Chrome/Application/chrome.exe'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), 'Google/Chrome/Application/chrome.exe'),
            os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Google/Chrome/Application/chrome.exe')
        ]
    elif sys.platform == "darwin":
        paths = ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    else:  # Linux
        paths = ["/usr/bin/google-chrome", "/usr/bin/google-chrome-stable"]

    for path in paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path

    raise FileNotFoundError("Chrome executable not found. Try setting CHROME_PATH manually.")

def get_user_documents_path():
    """Get user Documents folder path"""
    if sys.platform == "win32":
        return os.path.join(os.path.expanduser("~"), "Documents")
    elif sys.platform == "darwin":
        return os.path.join(os.path.expanduser("~"), "Documents")
    else:  # Linux
        # Get actual user's home directory
        sudo_user = os.environ.get('SUDO_USER')
        if sudo_user:
            return os.path.join("/home", sudo_user, "Documents")
        return os.path.join(os.path.expanduser("~"), "Documents")

def get_random_wait_time(config, timing_type='page_load_wait'):
    """
    Get random wait time from config
    Args:
        config: ConfigParser object
        timing_type: Type of timing to get (page_load_wait, input_wait, submit_wait)
    Returns:
        float: Random wait time or fixed time
    """
    try:
        if not config.has_section('Timing'):
            return random.uniform(0.1, 0.8)  # Default value
            
        if timing_type == 'random':
            min_time = float(config.get('Timing', 'min_random_time', fallback='0.1'))
            max_time = float(config.get('Timing', 'max_random_time', fallback='0.8'))
            return random.uniform(min_time, max_time)
            
        time_value = config.get('Timing', timing_type, fallback='0.1-0.8')
        
        # Check if it's a fixed time value
        if '-' not in time_value and ',' not in time_value:
            return float(time_value)  # Return fixed time
            
        # Process range time
        min_time, max_time = map(float, time_value.split('-' if '-' in time_value else ','))
        return random.uniform(min_time, max_time)
    except:
        return random.uniform(0.1, 0.8)  # Return default value when error

def setup_driver(translator=None):
    """Setup browser driver"""
    try:
        # Get config
        config = get_config(translator)
        
        # Get Chrome path
        chrome_path = config.get('Chrome', 'chromepath', fallback=get_default_chrome_path())
        
        if not chrome_path or not os.path.exists(chrome_path):
            if translator:
                print(f"{Fore.YELLOW}⚠️ {translator.get('register.chrome_path_invalid') if translator else 'Chrome路径无效，使用默认路径'}{Style.RESET_ALL}")
            chrome_path = get_default_chrome_path()

        # Set browser options
        co = ChromiumOptions()
        
        # Set Chrome path
        co.set_browser_path(chrome_path)
        
        # Use incognito mode
        co.set_argument("--incognito")

        # Set random port
        co.set_argument("--no-sandbox")
        
        # Set random port
        co.auto_port()
        
        # Use headless mode (must be set to False, simulate human operation)
        co.headless(False)
        
        try:
            # Load extension
            extension_path = os.path.join(os.getcwd(), "turnstilePatch")
            if os.path.exists(extension_path):
                co.set_argument("--allow-extensions-in-incognito")
                co.add_extension(extension_path)
        except Exception as e:
            if translator:
                print(f"{Fore.RED}❌ {translator.get('register.extension_load_error', error=str(e))}{Style.RESET_ALL}")
            else:
                print(f"Error loading extension: {e}")
        
        if translator:
            print(f"{Fore.CYAN}🚀 {translator.get('register.starting_browser')}{Style.RESET_ALL}")
        else:
            print("Starting browser...")
        
        page = ChromiumPage(co)
        return config, page

    except Exception as e:
        if translator:
            print(f"{Fore.RED}❌ {translator.get('register.browser_setup_error', error=str(e))}{Style.RESET_ALL}")
        else:
            print(f"Error setting up browser: {e}")
        raise

def handle_turnstile(page, config, translator=None):
    """Handle Turnstile verification"""
    try:
        if translator:
            print(f"{Fore.CYAN}🔄 {translator.get('register.handling_turnstile')}{Style.RESET_ALL}")
        else:
            print("\nHandling Turnstile verification...")
        
        # from config
        turnstile_time = float(config.get('Turnstile', 'handle_turnstile_time', fallback='2'))
        random_time_str = config.get('Turnstile', 'handle_turnstile_random_time', fallback='1-3')
        
        # Parse random time range
        try:
            min_time, max_time = map(float, random_time_str.split('-'))
        except:
            min_time, max_time = 1, 3  # Default value
        
        max_retries = 2
        retry_count = 0

        while retry_count < max_retries:
            retry_count += 1
            if translator:
                print(f"{Fore.CYAN}🔄 {translator.get('register.retry_verification', attempt=retry_count)}{Style.RESET_ALL}")
            else:
                print(f"Attempt {retry_count} of verification...")

            try:
                # Try to reset turnstile
                page.run_js("try { turnstile.reset() } catch(e) { }")
                time.sleep(turnstile_time)  # from config

                # Locate verification box element
                challenge_check = (
                    page.ele("@id=cf-turnstile", timeout=2)
                    .child()
                    .shadow_root.ele("tag:iframe")
                    .ele("tag:body")
                    .sr("tag:input")
                )

                if challenge_check:
                    if translator:
                        print(f"{Fore.CYAN}🔄 {translator.get('register.detect_turnstile')}{Style.RESET_ALL}")
                    else:
                        print("Detected verification box...")
                    
                    # from config
                    time.sleep(random.uniform(min_time, max_time))
                    challenge_check.click()
                    time.sleep(turnstile_time)  # from config

                    # check verification result
                    if check_verification_success(page, translator):
                        if translator:
                            print(f"{Fore.GREEN}✅ {translator.get('register.verification_success')}{Style.RESET_ALL}")
                        else:
                            print("Verification successful!")
                        return True

            except Exception as e:
                if translator:
                    print(f"{Fore.RED}❌ {translator.get('register.verification_failed')}{Style.RESET_ALL}")
                else:
                    print(f"Verification attempt failed: {e}")

            # Check if verification has been successful
            if check_verification_success(page, translator):
                if translator:
                    print(f"{Fore.GREEN}✅ {translator.get('register.verification_success')}{Style.RESET_ALL}")
                else:
                    print("Verification successful!")
                return True

            time.sleep(random.uniform(min_time, max_time))

        if translator:
            print(f"{Fore.RED}❌ {translator.get('register.verification_failed')}{Style.RESET_ALL}")
        else:
            print("Exceeded maximum retry attempts")
        return False

    except Exception as e:
        if translator:
            print(f"{Fore.RED}❌ {translator.get('register.verification_error', error=str(e))}{Style.RESET_ALL}")
        else:
            print(f"Error in verification process: {e}")
        return False

def check_verification_success(page, translator=None):
    """Check if verification is successful"""
    try:
        # Check if there is a subsequent form element, indicating verification has passed
        if (page.ele("@name=password", timeout=0.5) or 
            page.ele("@name=email", timeout=0.5) or
            page.ele("@data-index=0", timeout=0.5) or
            page.ele("Account Settings", timeout=0.5)):
            return True
        
        # Check if there is an error message
        error_messages = [
            'xpath://div[contains(text(), "Can\'t verify the user is human")]',
            'xpath://div[contains(text(), "Error: 600010")]',
            'xpath://div[contains(text(), "Please try again")]'
        ]
        
        for error_xpath in error_messages:
            if page.ele(error_xpath):
                return False
            
        return False
    except:
        return False

def generate_password(length=12):
    """Generate random password"""
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*"
    return ''.join(random.choices(chars, k=length))

def fill_password(page, password: str, config, translator=None):
    """
    Fill password form
    """
    try:
        print(f"{Fore.CYAN}🔑 {translator.get('register.setting_password') if translator else 'Setting password'}{Style.RESET_ALL}")
        
        # Fill password
        password_input = page.ele("@name=password")
        print(f"{Fore.CYAN}🔑 {translator.get('register.setting_on_password')}: {password}{Style.RESET_ALL}")
        if password_input:
            password_input.input(password)

        # Click submit button
        submit_button = page.ele("@type=submit")
        if submit_button:
            submit_button.click()
            time.sleep(get_random_wait_time(config, 'submit_wait'))
            
        print(f"{Fore.GREEN}✅ {translator.get('register.password_submitted') if translator else 'Password submitted'}{Style.RESET_ALL}")
        
        return True
        
    except Exception as e:
        print(f"{Fore.RED}❌ {translator.get('register.password_error', error=str(e)) if translator else f'Error setting password: {str(e)}'}{Style.RESET_ALL}")

        return False

def handle_verification_code(browser_tab, email_tab, controller, config, translator=None):
    """Handle verification code"""
    try:
        if translator:
            print(f"\n{Fore.CYAN}🔄 {translator.get('register.waiting_for_verification_code')}{Style.RESET_ALL}")
            
        # Check if using manual input verification code
        if hasattr(controller, 'get_verification_code') and email_tab is None:  # Manual mode
            verification_code = controller.get_verification_code()
            if verification_code:
                # Fill verification code in registration page
                for i, digit in enumerate(verification_code):
                    browser_tab.ele(f"@data-index={i}").input(digit)
                    time.sleep(get_random_wait_time(config, 'verification_code_input'))
                
                print(f"{translator.get('register.verification_success')}")
                time.sleep(get_random_wait_time(config, 'verification_success_wait'))
                
                # Handle last Turnstile verification
                if handle_turnstile(browser_tab, config, translator):
                    if translator:
                        print(f"{Fore.GREEN}✅ {translator.get('register.verification_success')}{Style.RESET_ALL}")
                    time.sleep(get_random_wait_time(config, 'verification_retry_wait'))
                    
                    # Visit settings page
                    print(f"{Fore.CYAN}🔑 {translator.get('register.visiting_url')}: https://www.cursor.com/settings{Style.RESET_ALL}")
                    browser_tab.get("https://www.cursor.com/settings")
                    time.sleep(get_random_wait_time(config, 'settings_page_load_wait'))
                    return True, browser_tab
                    
                return False, None
                
        # Automatic verification code logic
        elif email_tab:
            print(f"{Fore.CYAN}🔄 {translator.get('register.waiting_for_verification_code')}{Style.RESET_ALL}")
            time.sleep(get_random_wait_time(config, 'email_check_initial_wait'))

            # Use existing email_tab to refresh email
            email_tab.refresh_inbox()
            time.sleep(get_random_wait_time(config, 'email_refresh_wait'))

            # Check if there is a verification code email
            if email_tab.check_for_cursor_email():
                verification_code = email_tab.get_verification_code()
                if verification_code:
                    # Fill verification code in registration page
                    for i, digit in enumerate(verification_code):
                        browser_tab.ele(f"@data-index={i}").input(digit)
                        time.sleep(get_random_wait_time(config, 'verification_code_input'))
                    
                    if translator:
                        print(f"{Fore.GREEN}✅ {translator.get('register.verification_success')}{Style.RESET_ALL}")
                    time.sleep(get_random_wait_time(config, 'verification_success_wait'))
                    
                    # Handle last Turnstile verification
                    if handle_turnstile(browser_tab, config, translator):
                        if translator:
                            print(f"{Fore.GREEN}✅ {translator.get('register.verification_success')}{Style.RESET_ALL}")
                        time.sleep(get_random_wait_time(config, 'verification_retry_wait'))
                        
                        # Visit settings page
                        if translator:
                            print(f"{Fore.CYAN}🔑 {translator.get('register.visiting_url')}: https://www.cursor.com/settings{Style.RESET_ALL}")
                        browser_tab.get("https://www.cursor.com/settings")
                        time.sleep(get_random_wait_time(config, 'settings_page_load_wait'))
                        return True, browser_tab
                        
                    else:
                        if translator:
                            print(f"{Fore.RED}❌ {translator.get('register.verification_failed')}{Style.RESET_ALL}")
                        else:
                            print("最后一次验证失败")
                        return False, None
                        
            # Get verification code, set timeout
            verification_code = None
            max_attempts = 20
            retry_interval = get_random_wait_time(config, 'retry_interval')  # Use get_random_wait_time
            start_time = time.time()
            timeout = float(config.get('Timing', 'max_timeout', fallback='160'))  # This can be kept unchanged because it is a fixed value

            if translator:
                print(f"{Fore.CYAN}{translator.get('register.start_getting_verification_code')}{Style.RESET_ALL}")
            
            for attempt in range(max_attempts):
                # Check if timeout
                if time.time() - start_time > timeout:
                    if translator:
                        print(f"{Fore.RED}❌ {translator.get('register.verification_timeout')}{Style.RESET_ALL}")
                    break
                    
                verification_code = controller.get_verification_code()
                if verification_code:
                    if translator:
                        print(f"{Fore.GREEN}✅ {translator.get('register.verification_success')}{Style.RESET_ALL}")
                    break
                    
                remaining_time = int(timeout - (time.time() - start_time))
                if translator:
                    print(f"{Fore.CYAN}{translator.get('register.try_get_code', attempt=attempt + 1, time=remaining_time)}{Style.RESET_ALL}")
                
                # Refresh email
                email_tab.refresh_inbox()
                time.sleep(retry_interval)  # Use get_random_wait_time
            
            if verification_code:
                # Fill verification code in registration page
                for i, digit in enumerate(verification_code):
                    browser_tab.ele(f"@data-index={i}").input(digit)
                    time.sleep(get_random_wait_time(config, 'verification_code_input'))
                
                if translator:
                    print(f"{Fore.GREEN}✅ {translator.get('register.verification_success')}{Style.RESET_ALL}")
                time.sleep(get_random_wait_time(config, 'verification_success_wait'))
                
                # Handle last Turnstile verification
                if handle_turnstile(browser_tab, config, translator):
                    if translator:
                        print(f"{Fore.GREEN}✅ {translator.get('register.verification_success')}{Style.RESET_ALL}")
                    time.sleep(get_random_wait_time(config, 'verification_retry_wait'))
                    
                    # Visit settings page
                    if translator:
                        print(f"{Fore.CYAN}{translator.get('register.visiting_url')}: https://www.cursor.com/settings{Style.RESET_ALL}")
                    browser_tab.get("https://www.cursor.com/settings")
                    time.sleep(get_random_wait_time(config, 'settings_page_load_wait'))
                    
                    # Return success directly, let cursor_register.py handle account information acquisition
                    return True, browser_tab
                    
                else:
                    if translator:
                        print(f"{Fore.RED}❌ {translator.get('register.verification_failed')}{Style.RESET_ALL}")
                    return False, None
                
            return False, None
            
    except Exception as e:
        if translator:
            print(f"{Fore.RED}❌ {translator.get('register.verification_error', error=str(e))}{Style.RESET_ALL}")
        return False, None

def handle_sign_in(browser_tab, email, password, translator=None):
    """Handle login process"""
    try:
        # Check if on login page
        sign_in_header = browser_tab.ele('xpath://h1[contains(text(), "Sign in")]')
        if not sign_in_header:
            return True  # If not on login page, it means login is successful
            
        print(f"{Fore.CYAN}检测到登录页面，开始登录...{Style.RESET_ALL}")
        
        # Fill email
        email_input = browser_tab.ele('@name=email')
        if email_input:
            email_input.input(email)
            time.sleep(1)
            
            # Click Continue
            continue_button = browser_tab.ele('xpath://button[contains(@class, "BrandedButton") and text()="Continue"]')
            if continue_button:
                continue_button.click()
                time.sleep(2)
                
                # Handle Turnstile verification
                if handle_turnstile(browser_tab, translator):
                    # Fill password
                    password_input = browser_tab.ele('@name=password')
                    if password_input:
                        password_input.input(password)
                        time.sleep(1)
                        
                        # Click Sign in
                        sign_in_button = browser_tab.ele('xpath://button[@name="intent" and @value="password"]')
                        if sign_in_button:
                            sign_in_button.click()
                            time.sleep(2)
                            
                            # Handle last Turnstile verification
                            if handle_turnstile(browser_tab, translator):
                                print(f"{Fore.GREEN}Login successful!{Style.RESET_ALL}")
                                time.sleep(3)
                                return True
                                
        print(f"{Fore.RED}Login failed{Style.RESET_ALL}")
        return False
        
    except Exception as e:
        print(f"{Fore.RED}Login process error: {str(e)}{Style.RESET_ALL}")
        return False

def main(email=None, password=None, first_name=None, last_name=None, email_tab=None, controller=None, translator=None):
    """Main function, can receive account information, email tab, and translator"""
    global _translator
    _translator = translator  # Save to global variable
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    page = None
    success = False
    try:
        config, page = setup_driver(translator)
        if translator:
            print(f"{Fore.CYAN}🚀 {translator.get('register.browser_started')}{Style.RESET_ALL}")
        
        # Visit registration page
        url = "https://authenticator.cursor.sh/sign-up"
        
        # Visit page
        simulate_human_input(page, url, config, translator)
        if translator:
            print(f"{Fore.CYAN}🔄 {translator.get('register.waiting_for_page_load')}{Style.RESET_ALL}")
        time.sleep(get_random_wait_time(config, 'page_load_wait'))
        
        # If account information is not provided, generate random information
        if not all([email, password, first_name, last_name]):
            first_name = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=6)).capitalize()
            last_name = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=6)).capitalize()
            email = f"{first_name.lower()}{random.randint(100,999)}@example.com"
            password = generate_password()
            
            # Save account information
            with open('test_accounts.txt', 'a', encoding='utf-8') as f:
                f.write(f"\n{'='*50}\n")
                f.write(f"Email: {email}\n")
                f.write(f"Password: {password}\n")
                f.write(f"{'='*50}\n")
        
        # Fill form
        if fill_signup_form(page, first_name, last_name, email, config, translator):
            if translator:
                print(f"\n{Fore.GREEN}✅ {translator.get('register.form_submitted')}{Style.RESET_ALL}")
            
            # Handle first Turnstile verification
            if handle_turnstile(page, config, translator):
                if translator:
                    print(f"\n{Fore.GREEN}✅ {translator.get('register.first_verification_passed')}{Style.RESET_ALL}")
                
                # Fill password
                if fill_password(page, password, config, translator):
                    if translator:
                        print(f"\n{Fore.CYAN}🔄 {translator.get('register.waiting_for_second_verification')}{Style.RESET_ALL}")
                                        
                    # Handle second Turnstile verification
                    if handle_turnstile(page, config, translator):
                        if translator:
                            print(f"\n{Fore.CYAN}🔄 {translator.get('register.waiting_for_verification_code')}{Style.RESET_ALL}")
                        if handle_verification_code(page, email_tab, controller, config, translator):
                            success = True
                            return True, page
                        else:
                            print(f"\n{Fore.RED}❌ {translator.get('register.verification_code_processing_failed') if translator else 'Verification code processing failed'}{Style.RESET_ALL}")
                    else:
                        print(f"\n{Fore.RED}❌ {translator.get('register.second_verification_failed') if translator else 'Second verification failed'}{Style.RESET_ALL}")
                else:
                    print(f"\n{Fore.RED}❌ {translator.get('register.second_verification_failed') if translator else 'Second verification failed'}{Style.RESET_ALL}")
            else:
                print(f"\n{Fore.RED}❌ {translator.get('register.first_verification_failed') if translator else 'First verification failed'}{Style.RESET_ALL}")
        
        return False, None
        
    except Exception as e:
        print(f"发生错误: {e}")
        return False, None
    finally:
        if page and not success:  # Only clean up when failed
            try:
                page.quit()
            except:
                pass
            cleanup_chrome_processes(translator)

if __name__ == "__main__":
    main()  # Run without parameters, use randomly generated information 