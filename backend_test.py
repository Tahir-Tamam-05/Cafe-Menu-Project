import requests
import sys
import json
import time
from datetime import datetime

class CafeMenuAPITester:
    def __init__(self, base_url="https://cafedash-2.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.admin_email = "sana.shaikh0056714@gmail.com"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        
        result = f"{status} - {name}"
        if details:
            result += f" | {details}"
        
        print(result)
        self.test_results.append({
            "name": name,
            "success": success,
            "details": details
        })
        return success

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        
        if headers:
            test_headers.update(headers)
        
        if self.token and 'Authorization' not in test_headers:
            test_headers['Authorization'] = f'Bearer {self.token}'

        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            
            if success:
                details = f"Status: {response.status_code}"
                try:
                    response_data = response.json()
                    if isinstance(response_data, list):
                        details += f" | Items: {len(response_data)}"
                    elif isinstance(response_data, dict) and 'message' in response_data:
                        details += f" | {response_data['message']}"
                except:
                    pass
            else:
                details = f"Expected {expected_status}, got {response.status_code}"
                try:
                    error_data = response.json()
                    if 'detail' in error_data:
                        details += f" | Error: {error_data['detail']}"
                except:
                    details += f" | Response: {response.text[:100]}"

            self.log_test(name, success, details)
            return success, response.json() if success else {}

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_public_endpoints(self):
        """Test all public endpoints"""
        print("\n" + "="*60)
        print("🌐 TESTING PUBLIC ENDPOINTS")
        print("="*60)
        
        # Test get menu
        success, menu_data = self.run_test(
            "Get Public Menu",
            "GET",
            "menu",
            200
        )
        
        if success and menu_data:
            available_items = len(menu_data)
            print(f"   📊 Found {available_items} available menu items")
            
            # Check if we have the expected 114 items (some might be unavailable)
            if available_items > 100:
                self.log_test("Menu Items Count Check", True, f"Found {available_items} items (expected ~114)")
            else:
                self.log_test("Menu Items Count Check", False, f"Only {available_items} items found, expected ~114")
        
        # Test get categories
        success, categories_data = self.run_test(
            "Get Categories",
            "GET",
            "menu/categories",
            200
        )
        
        if success and categories_data:
            categories = categories_data.get('categories', [])
            print(f"   📊 Found {len(categories)} categories: {categories[:5]}...")
            
            # Check for expected categories
            expected_categories = ['Lassi', 'Falooda', 'Milk Shakes', 'Ice Creams', 'Fresh Juices']
            found_expected = [cat for cat in expected_categories if cat in categories]
            if len(found_expected) >= 3:
                self.log_test("Categories Check", True, f"Found {len(found_expected)}/{len(expected_categories)} expected categories")
            else:
                self.log_test("Categories Check", False, f"Only found {len(found_expected)} expected categories")
        
        # Test get specials
        success, specials_data = self.run_test(
            "Get Today's Specials",
            "GET",
            "menu/specials",
            200
        )
        
        if success:
            specials_count = len(specials_data)
            print(f"   📊 Found {specials_count} special items")

    def test_auth_flow(self):
        """Test authentication flow"""
        print("\n" + "="*60)
        print("🔐 TESTING AUTHENTICATION FLOW")
        print("="*60)
        
        # Test send OTP
        success, otp_response = self.run_test(
            "Send OTP",
            "POST",
            "auth/send-otp",
            200,
            data={"email": self.admin_email}
        )
        
        if not success:
            print("❌ Cannot proceed with auth tests - OTP sending failed")
            return False
        
        # Wait a moment for OTP to be generated
        print("⏳ Waiting 3 seconds for OTP to be logged...")
        time.sleep(3)
        
        # Try to get OTP from backend logs
        otp = self.get_otp_from_logs()
        
        if not otp:
            print("❌ Could not retrieve OTP from logs")
            self.log_test("Get OTP from Logs", False, "OTP not found in backend logs")
            return False
        
        self.log_test("Get OTP from Logs", True, f"Found OTP: {otp}")
        
        # Test verify OTP
        success, verify_response = self.run_test(
            "Verify OTP",
            "POST",
            "auth/verify-otp",
            200,
            data={"email": self.admin_email, "otp": otp}
        )
        
        if success and 'token' in verify_response:
            self.token = verify_response['token']
            self.log_test("JWT Token Generation", True, "Token received and stored")
            return True
        else:
            self.log_test("JWT Token Generation", False, "No token in response")
            return False

    def get_otp_from_logs(self):
        """Try to get OTP from backend logs"""
        try:
            import subprocess
            result = subprocess.run(
                ["tail", "-n", "30", "/var/log/supervisor/backend.err.log"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            lines = result.stdout.split('\n')
            for line in reversed(lines):  # Check from newest to oldest
                if f"OTP FOR {self.admin_email}" in line:
                    # Extract OTP from line like "🔐 OTP FOR email: 123456"
                    parts = line.split(':')
                    if len(parts) >= 2:
                        otp = parts[-1].strip()
                        if otp.isdigit() and len(otp) == 6:
                            return otp
            
            # Also check stdout log
            result = subprocess.run(
                ["tail", "-n", "30", "/var/log/supervisor/backend.out.log"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            lines = result.stdout.split('\n')
            for line in reversed(lines):
                if f"OTP FOR {self.admin_email}" in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        otp = parts[-1].strip()
                        if otp.isdigit() and len(otp) == 6:
                            return otp
                            
        except Exception as e:
            print(f"Error reading logs: {e}")
        
        return None

    def test_admin_endpoints(self):
        """Test admin endpoints (requires authentication)"""
        if not self.token:
            print("❌ No auth token available - skipping admin tests")
            return
        
        print("\n" + "="*60)
        print("👑 TESTING ADMIN ENDPOINTS")
        print("="*60)
        
        # Test get all menu items (admin)
        success, admin_menu_data = self.run_test(
            "Get All Menu Items (Admin)",
            "GET",
            "admin/menu",
            200
        )
        
        if success and admin_menu_data:
            total_items = len(admin_menu_data)
            available_items = len([item for item in admin_menu_data if item.get('available', True)])
            unavailable_items = total_items - available_items
            
            print(f"   📊 Total items: {total_items}")
            print(f"   📊 Available: {available_items}")
            print(f"   📊 Unavailable: {unavailable_items}")
            
            if total_items >= 114:
                self.log_test("Total Items Count (Admin)", True, f"Found {total_items} items (expected 114)")
            else:
                self.log_test("Total Items Count (Admin)", False, f"Only {total_items} items, expected 114")
        
        # Test create new menu item
        test_item = {
            "name": "Test Lassi",
            "category": "Lassi",
            "price": 50.0,
            "description": "Test item for API testing",
            "is_special": True,
            "available": True
        }
        
        success, create_response = self.run_test(
            "Create New Menu Item",
            "POST",
            "admin/menu",
            200,
            data=test_item
        )
        
        created_item_id = None
        if success and 'id' in create_response:
            created_item_id = create_response['id']
            self.log_test("Item Creation Response", True, f"Item ID: {created_item_id}")
        
        # Test update menu item
        if created_item_id:
            update_data = {
                "name": "Updated Test Lassi",
                "price": 60.0,
                "description": "Updated test item"
            }
            
            success, update_response = self.run_test(
                "Update Menu Item",
                "PUT",
                f"admin/menu/{created_item_id}",
                200,
                data=update_data
            )
            
            # Test toggle special status
            success, toggle_response = self.run_test(
                "Toggle Special Status",
                "PUT",
                f"admin/menu/{created_item_id}/toggle-special",
                200
            )
            
            # Test toggle availability
            success, toggle_response = self.run_test(
                "Toggle Availability",
                "PUT",
                f"admin/menu/{created_item_id}/toggle-available",
                200
            )
            
            # Test delete menu item
            success, delete_response = self.run_test(
                "Delete Menu Item",
                "DELETE",
                f"admin/menu/{created_item_id}",
                200
            )

    def test_error_cases(self):
        """Test error handling"""
        print("\n" + "="*60)
        print("⚠️  TESTING ERROR CASES")
        print("="*60)
        
        # Test unauthorized access to admin endpoints
        temp_token = self.token
        self.token = None  # Remove token temporarily
        
        success, _ = self.run_test(
            "Unauthorized Admin Access",
            "GET",
            "admin/menu",
            403
        )
        
        self.token = temp_token  # Restore token
        
        # Test invalid OTP
        success, _ = self.run_test(
            "Invalid OTP Verification",
            "POST",
            "auth/verify-otp",
            400,
            data={"email": self.admin_email, "otp": "000000"}
        )
        
        # Test invalid email for OTP
        success, _ = self.run_test(
            "Invalid Email for OTP",
            "POST",
            "auth/send-otp",
            403,
            data={"email": "invalid@example.com"}
        )

    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.tests_run - self.tests_passed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   • {result['name']}: {result['details']}")
        
        return success_rate >= 80  # Consider 80%+ as overall success

def main():
    print("🧪 Starting Café Menu API Tests")
    print("=" * 60)
    
    tester = CafeMenuAPITester()
    
    # Run all test suites
    tester.test_public_endpoints()
    
    auth_success = tester.test_auth_flow()
    
    if auth_success:
        tester.test_admin_endpoints()
    else:
        print("⚠️  Skipping admin tests due to authentication failure")
    
    tester.test_error_cases()
    
    # Print final summary
    overall_success = tester.print_summary()
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(main())