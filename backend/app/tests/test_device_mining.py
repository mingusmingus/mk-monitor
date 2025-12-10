import unittest
from unittest.mock import MagicMock, patch
from app.services.device_mining import DeviceMiner

class TestDeviceMiner(unittest.TestCase):
    def setUp(self):
        # Create a mock for the Device object
        self.mock_device = MagicMock()
        self.mock_device.id = 1
        self.mock_device.ip_address = "192.168.1.1"
        self.mock_device.username_encrypted = "enc_user"
        self.mock_device.password_encrypted = "enc_pass"
        self.mock_device.port = 8728
        self.mock_device.ros_api_port = 8728

    @patch('app.services.device_mining.decrypt_secret')
    @patch('app.services.device_mining.RouterOsApiPool')
    def test_collect_data_v6(self, MockRouterOsApiPool, mock_decrypt):
        mock_decrypt.return_value = "secret"

        # Setup mock API
        mock_pool_instance = MockRouterOsApiPool.return_value
        mock_api_instance = mock_pool_instance.get_api.return_value

        # Mock responses for various commands
        def get_resource_side_effect(path):
            resource = MagicMock()
            if path == '/system/package':
                resource.get.return_value = [{'name': 'routeros-mipsbe', 'version': '6.48.6', 'disabled': 'false'}]
            elif path == '/system/identity':
                resource.get.return_value = [{'name': 'MikroTik-Router'}]
            elif path == '/system/resource':
                resource.get.return_value = [{'uptime': '1w', 'cpu-load': '10', 'free-memory': '50000', 'total-memory': '60000', 'version': '6.48.6'}]
            elif path == '/system/routerboard':
                resource.get.return_value = [{'model': 'RB750Gr3', 'serial-number': '12345'}]
            elif path == '/system/health':
                resource.get.return_value = [{'name': 'voltage', 'value': '24.1'}, {'name': 'temperature', 'value': '30'}]
            elif path == '/interface':
                 resource.get.return_value = [{'name': 'ether1', 'type': 'ether', 'running': 'true'}, {'name': 'ether2', 'type': 'ether', 'running': 'true'}]
            elif path == '/interface/ethernet':
                resource.get.return_value = [{'name': 'ether1', 'auto-negotiation': 'yes', 'speed': '1Gbps'}, {'name': 'ether2'}]
            elif path == '/ip/address':
                resource.get.return_value = [{'address': '192.168.88.1/24', 'interface': 'ether1'}]
            elif path == '/ip/neighbor':
                resource.get.return_value = [{'interface': 'ether1', 'identity': 'Switch-Core', 'address': '192.168.88.2'}]
            elif path == '/ip/route':
                 resource.call.return_value = [{'ret': 10}] # Mock count
            elif path == '/ip/firewall/filter':
                resource.get.return_value = [{'chain': 'input', 'action': 'drop', 'bytes': '1024', 'packets': '50'}]
            # v6 wireless
            elif path == '/interface/wireless/registration-table':
                resource.get.return_value = [{'mac-address': '00:11:22:33:44:55', 'signal-strength': '-50'}]
            else:
                resource.get.return_value = []
                resource.call.return_value = []
            return resource

        mock_api_instance.get_resource.side_effect = get_resource_side_effect

        # Instantiate Miner
        miner = DeviceMiner(self.mock_device)

        data = miner.mine()

        self.assertIsNotNone(data)
        self.assertNotIn("error", data, f"Mining failed with error: {data.get('error')}")

        # Verify Context
        self.assertEqual(data['context']['identity'], 'MikroTik-Router')
        self.assertEqual(miner.ros_version_major, 6)

        # Verify Health
        self.assertEqual(data['health']['voltage'], '24.1')

        # Verify Security
        self.assertEqual(data['security']['total_fw_drop_packets'], 50)

    @patch('app.services.device_mining.decrypt_secret')
    @patch('app.services.device_mining.RouterOsApiPool')
    def test_collect_data_v7(self, MockRouterOsApiPool, mock_decrypt):
        mock_decrypt.return_value = "secret"

        # Setup mock API
        mock_pool_instance = MockRouterOsApiPool.return_value
        mock_api_instance = mock_pool_instance.get_api.return_value

        def get_resource_side_effect(path):
            resource = MagicMock()
            if path == '/system/package':
                # Return empty list for package to simulate checking version from resource or other means if needed,
                # or just valid v7 package. The code checks data["context"]["version"] which comes from /system/resource
                resource.get.return_value = []
            elif path == '/system/resource':
                resource.get.return_value = [{'uptime': '1w', 'version': '7.12', 'board-name': 'CCR'}]
            elif path == '/system/identity':
                resource.get.return_value = [{'name': 'MikroTik-v7'}]
            # ... returns empty or valid data for others
            elif path == '/interface/wifiwave2/registration-table': # v7 check
                resource.get.return_value = [{'mac-address': 'AA:BB:CC:DD:EE:FF'}]
            elif path == '/interface/wifi/registration-table': # v7 fallback
                resource.get.return_value = []
            else:
                resource.get.return_value = []
                resource.call.return_value = []
            return resource

        mock_api_instance.get_resource.side_effect = get_resource_side_effect

        miner = DeviceMiner(self.mock_device)
        data = miner.mine()

        self.assertEqual(miner.ros_version_major, 7)
        self.assertEqual(data['context']['version'], '7.12')
